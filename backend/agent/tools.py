import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from backend.config import container
from backend.domain.models import (
    ActionPlan, Task, Escalation, Priority, TaskStatus, EscalationStatus
)
from backend.domain.services import calculate_heat_risk as calc_heat_risk_svc, TaskLifecycleService


def get_weather(location_or_ward_id: str) -> Dict[str, Any]:
    """
    Tool 1: get_weather
    Retrieve current weather & heat parameters for a ward.
    """
    event_repo = container.event_repo
    events = event_repo.list_events_by_ward(location_or_ward_id)
    if events:
        latest = events[0]
        return {
            "ward_id": location_or_ward_id,
            "temperature": latest.temperature,
            "humidity": latest.humidity,
            "heat_index": latest.heat_index,
            "severity": latest.severity.value,
            "duration_hours": latest.duration,
            "timestamp": latest.timestamp.isoformat(),
            "forecast": f"High temperature event continuing for {latest.duration} hours with humidity {latest.humidity}%."
        }

    raise LookupError(
        f"No heat event data is available for ward '{location_or_ward_id}'. "
        "Load a current heat event before generating a response plan."
    )


def calculate_heat_risk(temperature: float, humidity: float, duration_hours: int = 4) -> Dict[str, Any]:
    """
    Tool 2: calculate_heat_risk
    Calculates severity deterministically using temperature and humidity.
    """
    severity, heat_index = calc_heat_risk_svc(temperature, humidity, duration_hours)
    return {
        "temperature": temperature,
        "humidity": humidity,
        "heat_index": heat_index,
        "severity": severity.value,
        "duration_hours": duration_hours,
        "is_critical": severity.value == "CRITICAL"
    }


def get_vulnerability(ward_id: str) -> Dict[str, Any]:
    """
    Tool 3: get_vulnerability
    Retrieve vulnerability details for a ward.
    """
    profile = container.vulnerability_repo.get_vulnerability(ward_id)
    ward = container.ward_repo.get_ward(ward_id)
    if not profile:
        raise LookupError(
            f"No vulnerability profile is available for ward '{ward_id}'. "
            "Load a vulnerability profile before generating a response plan."
        )
    return {
        "ward_id": ward_id,
        "ward_name": ward.name if ward else ward_id,
        "population": ward.population if ward else 0,
        "outdoor_workers": profile.outdoor_worker_count,
        "elderly": profile.elderly_count,
        "children": profile.children_count,
        "high_risk_population": profile.high_risk_population,
        "vulnerability_score": profile.vulnerability_score
    }


def get_resources(ward_id: str) -> Dict[str, Any]:
    """
    Tool 4: get_resources
    Retrieve available response resources & identify resource gaps for a ward.
    """
    resources = container.resource_repo.get_resources_by_ward(ward_id)
    vuln = container.vulnerability_repo.get_vulnerability(ward_id)

    resource_list = [r.model_dump() for r in resources]

    # Calculate resource gaps
    cooling_capacity = sum(r.capacity for r in resources if r.type == "cooling_centre")
    water_points = [r for r in resources if "water" in r.type.lower()]

    gaps = []
    if vuln:
        if cooling_capacity < vuln.outdoor_worker_count:
            gaps.append(f"Cooling center capacity ({cooling_capacity}) insufficient for {vuln.outdoor_worker_count} outdoor workers.")
        if len(water_points) < 2:
            gaps.append(f"Water supply points ({len(water_points)}) below minimum requirement (2) for high heat index.")

    return {
        "ward_id": ward_id,
        "resources": resource_list,
        "total_resources": len(resources),
        "resource_gaps": gaps,
        "has_gaps": len(gaps) > 0
    }


def create_action_plan(event_id: str, priority: str = "CRITICAL", summary: str = "") -> Dict[str, Any]:
    """
    Tool 5: create_action_plan
    Creates a new action plan for a heat event.
    """
    now = datetime.now(timezone.utc)
    plan_id = f"plan_{event_id}_{uuid.uuid4().hex}"

    try:
        p_enum = Priority(priority.upper())
    except ValueError:
        p_enum = Priority.CRITICAL

    plan = ActionPlan(
        plan_id=plan_id,
        event_id=event_id,
        created_at=now,
        priority=p_enum,
        status="ACTIVE",
        summary=summary or f"Heat response action plan for event {event_id}"
    )
    saved_plan = container.action_plan_repo.save_plan(plan)
    return saved_plan.model_dump()


def assign_task(
    plan_id: str,
    action: str,
    responsible_team: str,
    priority: str = "HIGH",
    deadline_minutes: int = 60,
    recommendation_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tool 6: assign_task
    Creates and assigns a response task to a responsible team with a deadline.
    """
    now = datetime.now(timezone.utc)
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    deadline = now + timedelta(minutes=deadline_minutes)

    try:
        p_enum = Priority(priority.upper())
    except ValueError:
        p_enum = Priority.HIGH

    task = Task(
        task_id=task_id,
        plan_id=plan_id,
        action=action,
        responsible_team=responsible_team,
        priority=p_enum,
        deadline=deadline,
        status=TaskStatus.PENDING,
        created_at=now,
        escalation_status=EscalationStatus.NONE,
        recommendation_reason=recommendation_reason,
    )
    saved_task = container.task_repo.save_task(task)
    return saved_task.model_dump()


def check_task_status(plan_id_or_task_id: str) -> Dict[str, Any]:
    """
    Tool 7: check_task_status
    Checks status of task(s) for a given plan or task ID. Updates overdue status automatically.
    """
    task_repo = container.task_repo
    now = datetime.now(timezone.utc)

    # Check if input is a task_id
    single_task = task_repo.get_task(plan_id_or_task_id)
    if single_task:
        updated_task, esc = TaskLifecycleService.check_and_escalate_task(single_task, now)
        if esc:
            task_repo.save_task(updated_task)
            container.escalation_repo.save_escalation(esc)
        return {"tasks": [updated_task.model_dump()]}

    # Else treat as plan_id
    tasks = task_repo.list_tasks_by_plan(plan_id_or_task_id)
    updated_tasks = []
    for t in tasks:
        up_t, esc = TaskLifecycleService.check_and_escalate_task(t, now)
        if esc:
            task_repo.save_task(up_t)
            container.escalation_repo.save_escalation(esc)
        updated_tasks.append(up_t.model_dump())

    return {
        "plan_id": plan_id_or_task_id,
        "tasks": updated_tasks,
        "total_tasks": len(updated_tasks)
    }


def escalate_task(task_id: str, reason: str, severity: str = "CRITICAL") -> Dict[str, Any]:
    """
    Tool 8: escalate_task
    Escalates a critical overdue/failed intervention.
    """
    task_repo = container.task_repo
    esc_repo = container.escalation_repo

    task = task_repo.get_task(task_id)
    if not task:
        return {"error": f"Task '{task_id}' not found."}
    if task.status in (TaskStatus.PENDING, TaskStatus.COMPLETED):
        return {"error": f"Task '{task_id}' cannot be escalated in its current status ({task.status.value})."}

    now = datetime.now(timezone.utc)

    try:
        sev_enum = Priority(severity.upper())
    except ValueError:
        sev_enum = Priority.CRITICAL

    task.status = TaskStatus.ESCALATED
    task.escalation_status = EscalationStatus.ESCALATED
    task.updated_at = now
    task.updated_by = "HeatOps System"
    task_repo.save_task(task)

    escalation = Escalation(
        escalation_id=f"esc_{task_id}_{int(now.timestamp())}",
        task_id=task_id,
        reason=reason,
        created_at=now,
        severity=sev_enum,
        status="OPEN"
    )
    saved_esc = esc_repo.save_escalation(escalation)

    # Dispatch high priority notification
    container.notification_provider.send_notification(
        recipient=f"EMERGENCY_COMMAND_{task.responsible_team}",
        message=f"CRITICAL ESCALATION: Task '{task.action}' is ESCALATED. Reason: {reason}",
        topic="CRITICAL_HEAT_ESCALATION"
    )

    return {
        "task_id": task_id,
        "status": "ESCALATED",
        "escalation": saved_esc.model_dump()
    }


# Map of all 8 tools
HEATOPS_TOOLS = {
    "get_weather": get_weather,
    "calculate_heat_risk": calculate_heat_risk,
    "get_vulnerability": get_vulnerability,
    "get_resources": get_resources,
    "create_action_plan": create_action_plan,
    "assign_task": assign_task,
    "check_task_status": check_task_status,
    "escalate_task": escalate_task,
}
