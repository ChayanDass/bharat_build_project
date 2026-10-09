import json
from queue import Queue
from threading import Thread
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from backend.config import container
from backend.domain.models import TaskStatus, EscalationStatus, HeatEvent
from backend.domain.services import TaskLifecycleService, calculate_heat_risk
from backend.agent.heatops_agent import HeatOpsAgent
from backend.agent.llm_planner import LLMPlanningError
from data.demo.seed_data import seed_demo_data

router = APIRouter(prefix="/api")
agent = HeatOpsAgent()


class CentralAssignmentBody(BaseModel):
    responsible_team: str
    assigned_by: str = "Central HeatOps Operator"


class DepartmentStatusBody(BaseModel):
    status: TaskStatus
    updated_by: str
    failure_reason: Optional[str] = None


class QueryBody(BaseModel):
    question: str
    ward_id: Optional[str] = "ward_12"


class EscalateBody(BaseModel):
    reason: str


class WeatherScenarioBody(BaseModel):
    scenario: str


def require_task_permission(
    *,
    role: str,
    action: str,
    task_id: str,
    department: Optional[str],
    task_department: str,
) -> None:
    if not container.task_authorizer.is_allowed(
        role=role,
        action=action,
        department=department,
        task_id=task_id,
        task_department=task_department,
    ):
        raise HTTPException(status_code=403, detail="Cedar policy denied this task operation.")


@router.get("/wards")
def list_wards():
    wards = container.ward_repo.list_wards()
    res = []
    for w in wards:
        vuln = container.vulnerability_repo.get_vulnerability(w.ward_id)
        res.append({
            "ward": w.model_dump(),
            "vulnerability": vuln.model_dump() if vuln else None
        })
    return res


@router.get("/events")
def list_events():
    events = container.event_repo.get_active_events()
    res = []
    for ev in events:
        ward = container.ward_repo.get_ward(ev.ward_id)
        res.append({
            "event": ev.model_dump(),
            "ward_name": ward.name if ward else ev.ward_id
        })
    return res


@router.get("/events/{ward_id}")
def get_event_detail(
    ward_id: str,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="view_ward",
        task_id=f"ward:{ward_id}",
        department=actor_department,
        task_department="",
    )
    events = container.event_repo.list_events_by_ward(ward_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"No event found for ward {ward_id}")
    event = events[0]
    ward = container.ward_repo.get_ward(ward_id)
    vuln = container.vulnerability_repo.get_vulnerability(ward_id)
    resources = container.resource_repo.get_resources_by_ward(ward_id)
    plan = container.action_plan_repo.get_plan_by_event(event.event_id)
    tasks = container.task_repo.list_tasks_by_plan(plan.plan_id) if plan else []
    previous_completed_tasks = []
    current_plan_id = plan.plan_id if plan else None
    for task in container.task_repo.list_all_tasks():
        task_plan = container.action_plan_repo.get_plan(task.plan_id)
        if (
            task_plan
            and task_plan.event_id == event.event_id
            and task.plan_id != current_plan_id
            and task.status == TaskStatus.COMPLETED
        ):
            previous_completed_tasks.append(task)

    return {
        "event": event.model_dump(),
        "ward": ward.model_dump() if ward else None,
        "vulnerability": vuln.model_dump() if vuln else None,
        "resources": [r.model_dump() for r in resources],
        "action_plan": plan.model_dump() if plan else None,
        "tasks": [t.model_dump() for t in tasks],
        "previous_completed_tasks": [t.model_dump() for t in previous_completed_tasks],
    }


@router.get("/tasks")
def list_tasks(
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="list_tasks",
        task_id="all-tasks",
        department=actor_department,
        task_department="",
    )
    now = datetime.now(timezone.utc)
    tasks = container.task_repo.list_all_tasks()
    updated = []
    for t in tasks:
        up_t, esc = TaskLifecycleService.check_and_escalate_task(t, now)
        if esc:
            container.task_repo.save_task(up_t)
            container.escalation_repo.save_escalation(esc)
        updated.append(up_t.model_dump())
    return updated


@router.post("/tasks/{task_id}/assign")
def assign_task_to_department(
    task_id: str,
    body: CentralAssignmentBody,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    task = container.task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    require_task_permission(
        role=actor_role,
        action="assign_task",
        task_id=task.task_id,
        department=actor_department,
        task_department=task.responsible_team,
    )
    try:
        updated_task = TaskLifecycleService.transition_status(task, TaskStatus.NOTIFIED)
        response_window = task.deadline - task.created_at
        updated_task.deadline = datetime.now(timezone.utc) + response_window
        updated_task.responsible_team = body.responsible_team
        updated_task.assigned_by = body.assigned_by
        updated_task.updated_by = body.assigned_by
        container.task_repo.save_task(updated_task)
        container.notification_provider.send_notification(
            recipient=updated_task.responsible_team,
            message=(
                f"New HeatOps task assigned by {body.assigned_by}: {updated_task.action} "
                f"(priority {updated_task.priority.value}, deadline {updated_task.deadline.isoformat()})."
            ),
            topic="HEATOPS_TASK_ASSIGNMENT",
        )
        return updated_task.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/tasks/{task_id}")
def get_task_status(
    task_id: str,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    task = container.task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    require_task_permission(
        role=actor_role,
        action="refresh_task",
        task_id=task.task_id,
        department=actor_department,
        task_department=task.responsible_team,
    )
    return task.model_dump()


@router.get("/department/tasks")
def list_department_tasks(
    department: str,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="view_task",
        task_id=f"inbox:{department}",
        department=actor_department,
        task_department=department,
    )
    return [
        task.model_dump()
        for task in container.task_repo.list_all_tasks()
        if task.responsible_team == department and task.status != TaskStatus.PENDING
    ]


@router.post("/department/{department}/tasks/{task_id}/status")
def update_department_task_status(
    department: str,
    task_id: str,
    body: DepartmentStatusBody,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    if body.status not in (
        TaskStatus.ACKNOWLEDGED,
        TaskStatus.IN_PROGRESS,
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
    ):
        raise HTTPException(
            status_code=400,
            detail="Unsupported department task status.",
        )
    task = container.task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.responsible_team != department:
        raise HTTPException(status_code=404, detail="Task is not assigned to this department")
    require_task_permission(
        role=actor_role,
        action="update_task",
        task_id=task.task_id,
        department=actor_department,
        task_department=task.responsible_team,
    )
    if body.status == TaskStatus.FAILED and not (body.failure_reason or "").strip():
        raise HTTPException(status_code=400, detail="A failure reason is required.")
    try:
        updated_task = TaskLifecycleService.transition_status(task, body.status)
        updated_task.updated_by = body.updated_by
        updated_task.failure_reason = (
            body.failure_reason.strip()
            if body.status == TaskStatus.FAILED and body.failure_reason
            else None
        )
        container.task_repo.save_task(updated_task)
        container.notification_provider.send_notification(
            recipient="HEATOPS_COMMAND_CENTER",
            message=(
                f"{updated_task.responsible_team} updated task '{updated_task.action}' "
                f"to {updated_task.status.value}."
            ),
            topic="HEATOPS_TASK_STATUS_UPDATE",
        )
        return updated_task.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/tasks/{task_id}/retry")
def retry_task_dispatch(
    task_id: str,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    task = container.task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    require_task_permission(
        role=actor_role,
        action="retry_task",
        task_id=task.task_id,
        department=actor_department,
        task_department=task.responsible_team,
    )
    if task.status not in (
        TaskStatus.FAILED,
        TaskStatus.OVERDUE,
        TaskStatus.ESCALATED,
        TaskStatus.ACKNOWLEDGED,
        TaskStatus.IN_PROGRESS,
    ):
        raise HTTPException(
            status_code=400,
            detail="Only acknowledged, active, failed, or escalated tasks can be retried.",
        )
    try:
        updated_task = TaskLifecycleService.transition_status(task, TaskStatus.NOTIFIED)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    updated_task.deadline = datetime.now(timezone.utc) + timedelta(minutes=60)
    if updated_task.escalation_status == EscalationStatus.ESCALATED:
        updated_task.escalation_status = EscalationStatus.RESOLVED
    updated_task.assigned_by = "Central HeatOps Operator"
    updated_task.updated_by = "Central HeatOps Operator"
    container.task_repo.save_task(updated_task)
    container.notification_provider.send_notification(
        recipient=updated_task.responsible_team,
        message=f"Retry requested for HeatOps task: {updated_task.action}. Please resume and report status.",
        topic="HEATOPS_TASK_RETRY",
    )
    return updated_task.model_dump()


@router.post("/tasks/{task_id}/escalate")
def escalate_task_endpoint(
    task_id: str,
    body: EscalateBody,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    task = container.task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    require_task_permission(
        role=actor_role,
        action="escalate_task",
        task_id=task.task_id,
        department=actor_department,
        task_department=task.responsible_team,
    )
    from backend.agent.tools import escalate_task
    res = escalate_task(task_id=task_id, reason=body.reason)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/escalations")
def list_escalations(
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="list_escalations",
        task_id="all-escalations",
        department=actor_department,
        task_department="",
    )
    escalations = container.escalation_repo.list_all_escalations()
    return [e.model_dump() for e in escalations]


@router.post("/agent/coordinate/{ward_id}")
def trigger_agent_coordination(
    ward_id: str,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="coordinate_response",
        task_id=f"ward:{ward_id}",
        department=actor_department,
        task_department="",
    )
    try:
        return agent.analyze_and_coordinate(ward_id)
    except LLMPlanningError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/agent/coordinate/{ward_id}/stream")
def trigger_agent_coordination_stream(
    ward_id: str,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="coordinate_response",
        task_id=f"ward:{ward_id}",
        department=actor_department,
        task_department="",
    )
    events: Queue = Queue()
    sentinel = object()

    def run_coordination():
        try:
            result = agent.analyze_and_coordinate(
                ward_id,
                on_trace=lambda step: events.put({"type": "step", "step": step}),
            )
            events.put({"type": "complete", "result": result})
        except Exception as exc:
            events.put({"type": "error", "message": str(exc)})
        finally:
            events.put(sentinel)

    Thread(target=run_coordination, daemon=True).start()

    def stream_events():
        while True:
            event = events.get()
            if event is sentinel:
                break
            yield f"data: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/agent/query")
def query_agent(
    body: QueryBody,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="query_agent",
        task_id=f"ward:{body.ward_id or 'ward_12'}",
        department=actor_department,
        task_department="",
    )
    try:
        answer = agent.query(body.question, context_ward_id=body.ward_id or "ward_12")
        return {"question": body.question, "answer": answer}
    except LLMPlanningError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/simulate/overdue/{task_id}")
def simulate_task_overdue(
    task_id: str,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    task = container.task_repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    require_task_permission(
        role=actor_role,
        action="simulate_overdue",
        task_id=task.task_id,
        department=actor_department,
        task_department=task.responsible_team,
    )
    if task.status not in (
        TaskStatus.NOTIFIED,
        TaskStatus.ACKNOWLEDGED,
        TaskStatus.IN_PROGRESS,
    ):
        raise HTTPException(
            status_code=400,
            detail="Only notified or active department tasks can be simulated as overdue.",
        )

    task.deadline = datetime.now(timezone.utc) - timedelta(minutes=10)

    up_t, esc = TaskLifecycleService.check_and_escalate_task(task)
    container.task_repo.save_task(up_t)
    if esc:
        container.escalation_repo.save_escalation(esc)
        container.notification_provider.send_notification(
            recipient=f"EMERGENCY_COMMAND_{up_t.responsible_team}",
            message=f"CRITICAL ESCALATION (Simulated Overdue): Task '{up_t.action}' is ESCALATED.",
            topic="CRITICAL_HEAT_ESCALATION"
        )

    return {
        "message": f"Task {task_id} simulated as overdue and escalated successfully.",
        "task": up_t.model_dump(),
        "escalation": esc.model_dump() if esc else None
    }


@router.post("/simulate/weather/{ward_id}")
def simulate_weather_change(
    ward_id: str,
    body: WeatherScenarioBody,
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="simulate_weather",
        task_id=f"ward:{ward_id}",
        department=actor_department,
        task_department="",
    )
    events = container.event_repo.list_events_by_ward(ward_id)
    if not events:
        raise HTTPException(status_code=404, detail=f"No event found for ward {ward_id}")

    latest = events[0]
    scenarios = {
        "afternoon_relief": {
            "temperature": 38.0,
            "humidity": 34.0,
            "duration": 2,
            "label": "Afternoon relief: heat intensity reduced after field response and weather shift.",
        },
        "renewed_heat_spike": {
            "temperature": 45.0,
            "humidity": 54.0,
            "duration": 5,
            "label": "Renewed heat spike: conditions worsened and require re-planning.",
        },
    }
    if body.scenario not in scenarios:
        raise HTTPException(status_code=400, detail="Unknown weather scenario")

    scenario = scenarios[body.scenario]
    severity, heat_index = calculate_heat_risk(
        scenario["temperature"],
        scenario["humidity"],
        scenario["duration"],
    )
    updated = HeatEvent(
        event_id=latest.event_id,
        ward_id=latest.ward_id,
        timestamp=datetime.now(timezone.utc),
        temperature=scenario["temperature"],
        humidity=scenario["humidity"],
        heat_index=heat_index,
        severity=severity,
        duration=scenario["duration"],
    )
    container.event_repo.save_event(updated)
    return {
        "message": scenario["label"],
        "event": updated.model_dump(),
    }


@router.post("/demo/reset")
def reset_demo_data(
    actor_role: str = Header(alias="X-HeatOps-Role"),
    actor_department: Optional[str] = Header(default=None, alias="X-HeatOps-Department"),
):
    require_task_permission(
        role=actor_role,
        action="reset_demo",
        task_id="demo-data",
        department=actor_department,
        task_department="",
    )
    seed_demo_data(reset=True)
    return {"status": "success", "message": "Demo database reset cleanly."}
