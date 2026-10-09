import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.config import container
from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.tools import (
    HEATOPS_TOOLS,
    get_weather,
    calculate_heat_risk,
    get_vulnerability,
    get_resources,
    create_action_plan,
    assign_task,
    check_task_status,
    escalate_task
)
from backend.agent.sop_catalog import format_action, select_sops
from backend.agent.llm_planner import LLMPlanningError, plan_sops_with_llm

logger = logging.getLogger("HeatOps.Agent")


class HeatOpsAgent:
    """
    HeatOps AI Agent — Sense → Assess → Prioritize → Plan → Act → Monitor → Escalate

    Tasks are DYNAMIC: determined by severity level, detected resource gaps,
    and vulnerable population counts. Not hardcoded.
    """

    def __init__(self):
        self.model_provider = container.model_provider
        self.tools = HEATOPS_TOOLS

    def analyze_and_coordinate(self, ward_id: str, on_trace=None) -> Dict[str, Any]:
        """
        Execute full agentic workflow for a ward.
        Returns real trace_steps showing every decision the agent made.
        """
        logger.info(f"HeatOpsAgent: Starting dynamic coordination for {ward_id}")
        trace_steps: List[Dict[str, Any]] = []
        step_num = 0

        def trace(tool: str, desc: str, input_args: str, result_summary: str, decision: str = ""):
            nonlocal step_num
            step_num += 1
            entry = {
                "step": step_num,
                "tool": tool,
                "description": desc,
                "input": input_args,
                "result": result_summary,
                "decision": decision,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            trace_steps.append(entry)
            logger.info(f"[Step {step_num}] {tool}: {result_summary}")
            if on_trace:
                on_trace(entry)
            return entry

        # ── Step 1: Sense weather ─────────────────────────────────────────────
        weather = get_weather(ward_id)
        trace(
            tool="get_weather",
            desc=f"Retrieving current weather for ward {ward_id}",
            input_args=f'ward_id="{ward_id}"',
            result_summary=(
                f"Temp: {weather['temperature']}°C | "
                f"Humidity: {weather['humidity']}% | "
                f"Heat Index: {weather.get('heat_index', 'N/A')}°C | "
                f"Duration: {weather.get('duration_hours', 4)}h"
            ),
        )

        # ── Step 2: Calculate risk ────────────────────────────────────────────
        risk = calculate_heat_risk(
            weather["temperature"], weather["humidity"], weather.get("duration_hours", 4)
        )
        severity = risk["severity"]
        trace(
            tool="calculate_heat_risk",
            desc="Running NOAA Rothfusz heat risk formula to assess severity",
            input_args=f"temp={weather['temperature']}, humidity={weather['humidity']}, duration={weather.get('duration_hours', 4)}h",
            result_summary=(
                f"Severity: {severity} | "
                f"Heat Index: {risk['heat_index']}°C | "
                f"Critical threshold exceeded: {risk.get('is_critical', False)}"
            ),
            decision=f"Severity classified as {severity} — proceeding to vulnerability assessment",
        )

        # ── Step 3: Vulnerability profile ─────────────────────────────────────
        vuln = get_vulnerability(ward_id)
        outdoor_workers = vuln.get("outdoor_workers", 0)
        elderly = vuln.get("elderly", 0)
        children = vuln.get("children", 0)
        high_risk = vuln.get("high_risk_population", outdoor_workers + elderly)
        vuln_score = vuln.get("vulnerability_score", 0)
        trace(
            tool="get_vulnerability",
            desc="Fetching vulnerable population profile for targeted interventions",
            input_args=f'ward_id="{ward_id}"',
            result_summary=(
                f"Outdoor workers: {outdoor_workers:,} | "
                f"Elderly: {elderly:,} | "
                f"Children: {children:,} | "
                f"Vulnerability score: {vuln_score:.1f}/10"
            ),
            decision=(
                f"{'HIGH' if outdoor_workers > 500 else 'STANDARD'} outdoor worker risk. "
                f"{'ELDERLY ALERT required.' if elderly > 1000 else 'Elderly population manageable.'}"
            ),
        )

        # ── Step 4: Resource audit ────────────────────────────────────────────
        resources = get_resources(ward_id)
        resource_gaps = resources.get("resource_gaps", [])
        has_gaps = resources.get("has_gaps", False)
        has_water_gap = any("water" in gap.lower() for gap in resource_gaps)
        has_cooling_gap = any("cooling" in gap.lower() for gap in resource_gaps)
        total_resources = resources.get("total_resources", 0)
        trace(
            tool="get_resources",
            desc="Auditing available cooling centres, water points, and health facilities",
            input_args=f'ward_id="{ward_id}"',
            result_summary=(
                f"Total resources: {total_resources} | "
                f"Gaps detected: {len(resource_gaps)} | "
                f"{'; '.join(resource_gaps) if resource_gaps else 'No critical gaps'}"
            ),
            decision=(
                f"{'Resource gaps detected - selecting matching SOP interventions.' if has_gaps else 'Resources adequate - selecting standard SOP interventions.'}"
            ),
        )

        # ── Step 5: Find active event ─────────────────────────────────────────
        events = container.event_repo.list_events_by_ward(ward_id)
        event_id = events[0].event_id if events else f"evt_{ward_id}_manual"
        previous_plan = container.action_plan_repo.get_plan_by_event(event_id)
        previous_tasks = []
        for task in container.task_repo.list_all_tasks():
            task_plan = container.action_plan_repo.get_plan(task.plan_id)
            if task_plan and task_plan.event_id == event_id:
                previous_tasks.append(task)
        previous_completed_tasks = [
            task for task in previous_tasks
            if str(task.status.value if hasattr(task.status, "value") else task.status) == "COMPLETED"
        ]
        completed_action_history = []
        for task in previous_completed_tasks:
            task_plan = container.action_plan_repo.get_plan(task.plan_id)
            completed_action_history.append({
                "action": task.action,
                "team": task.responsible_team,
                "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "plan_id": task.plan_id,
                "environmental_conditions": task_plan.summary if task_plan else None,
            })
        active_previous_tasks = [
            task for task in previous_tasks if task not in previous_completed_tasks
        ]
        completed_actions = {t.action for t in previous_completed_tasks}

        if previous_plan:
            trace(
                tool="plan_memory",
                desc="Loading previous response state before replanning",
                input_args=f'event_id="{event_id}", previous_plan="{previous_plan.plan_id}"',
                result_summary=(
                    f"{len(previous_completed_tasks)} completed previous actions | "
                    f"{len(active_previous_tasks)} active/unfinished previous actions"
                ),
                decision="Completed actions will be preserved as previous work and not duplicated in the new plan.",
            )

        # ── Step 6: Candidate SOP filter ──────────────────────────────────────
        # Backend creates the allowed action menu. The LLM can choose from this
        # menu, but cannot invent actions or departments.
        candidate_sops = select_sops(
            severity=severity,
            outdoor_workers=outdoor_workers,
            elderly=elderly,
            children=children,
            vulnerability_score=vuln_score,
            has_water_gap=has_water_gap,
            has_cooling_gap=has_cooling_gap,
        )
        skipped_completed_sops = [
            sop for sop in candidate_sops
            if format_action(sop, outdoor_workers=outdoor_workers, elderly=elderly) in completed_actions
        ]
        candidate_sops = [
            sop for sop in candidate_sops
            if format_action(sop, outdoor_workers=outdoor_workers, elderly=elderly) not in completed_actions
        ]
        trace(
            tool="candidate_sops",
            desc="Generating eligible SOP menu from severity, gaps, and population thresholds",
            input_args=(
                f'severity="{severity}", outdoor_workers={outdoor_workers}, '
                f"elderly={elderly}, children={children}, vulnerability_score={vuln_score}, "
                f"has_water_gap={has_water_gap}, has_cooling_gap={has_cooling_gap}"
            ),
            result_summary=(
                f"{len(candidate_sops)} eligible SOP candidates: "
                f"{', '.join(sop['sop_id'] for sop in candidate_sops) if candidate_sops else 'none'}"
            ),
            decision=(
                "Backend filtered out impossible SOPs before the LLM planner saw the menu. "
                f"Skipped completed SOPs from prior plans: {[s['sop_id'] for s in skipped_completed_sops] or 'none'}. "
                "Uncompleted tasks from the previous plan may be replaced by this replanned response."
            ),
        )

        # ── Step 7: LLM operational planner + backend validation ──────────────
        ward_facts = {
            "ward_id": ward_id,
            "severity": severity,
            "heat_index": risk["heat_index"],
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "duration_hours": weather.get("duration_hours", 4),
            "outdoor_workers": outdoor_workers,
            "elderly": elderly,
            "children": children,
            "high_risk_population": high_risk,
            "vulnerability_score": vuln_score,
            "resource_gaps": resource_gaps,
            "has_water_gap": has_water_gap,
            "has_cooling_gap": has_cooling_gap,
            "previous_completed_actions": completed_action_history,
            "active_previous_actions": [
                {
                    "action": task.action,
                    "team": task.responsible_team,
                    "status": task.status.value if hasattr(task.status, "value") else task.status,
                    "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
                    "deadline": task.deadline.isoformat(),
                    "plan_id": task.plan_id,
                }
                for task in active_previous_tasks
            ],
        }
        selected_sops, planner_output = plan_sops_with_llm(
            self.model_provider,
            ward_id=ward_id,
            ward_facts=ward_facts,
            candidate_sops=candidate_sops,
            max_tasks=12,
        )
        trace(
            tool="llm_operational_planner",
            desc="Configured language model selects SOP IDs from the backend-approved candidate menu",
            input_args=f"{len(candidate_sops)} candidate SOPs, max_tasks=12",
            result_summary=(
                f"{len(selected_sops)} validated SOPs selected: "
                f"{', '.join(planner_output['selected_sop_ids']) if selected_sops else 'none'}"
            ),
            decision=(
                f"Planning mode: {planner_output['planning_mode']}. "
                f"Validation notes: {planner_output['validation_notes'] or 'none'}"
            ),
        )

        ai_summary = planner_output["executive_summary"]
        trace(
            tool="llm_synthesis",
            desc="Preparing executive summary from the validated planning response",
            input_args="severity, vulnerability, resource gaps, validated SOP selection",
            result_summary="AI executive summary generated with the SOP plan.",
            decision=ai_summary,
        )

        # ── Step 8: Create action plan ────────────────────────────────────────
        plan_summary = (
            f"Heat Action Plan for {ward_id} ({severity} Severity, "
            f"Temperature: {weather['temperature']}°C, Humidity: {weather['humidity']}%, "
            f"Heat Index: {risk['heat_index']}°C, Duration: {weather.get('duration_hours', 4)}h). "
            f"Vulnerability: {outdoor_workers} outdoor workers, {elderly} elderly, {children} children. "
            f"Resource gaps: {resource_gaps if resource_gaps else 'none'}. "
            f"LLM planner selected {len(selected_sops)} of {len(candidate_sops)} eligible SOPs. "
            f"Previous completed actions preserved: {len(previous_completed_tasks)}."
        )
        plan = create_action_plan(event_id=event_id, priority=severity, summary=plan_summary)
        plan_id = plan["plan_id"]
        trace(
            tool="create_action_plan",
            desc="Creating validated response workflow after LLM planning",
            input_args=f'event_id="{event_id}", priority="{severity}"',
            result_summary=f"Plan created: {plan_id}",
            decision="Plan record is created only after SOP IDs pass backend validation.",
        )

        # ── Step 9: Task assignment from validated SOPs ───────────────────────
        assigned_tasks = []
        for sop in selected_sops:
            action = format_action(sop, outdoor_workers=outdoor_workers, elderly=elderly)
            sop_reason = planner_output.get("selection_reasoning", {}).get(sop["sop_id"], sop["description"])
            task = assign_task(
                plan_id=plan_id,
                action=action,
                responsible_team=sop["team"],
                priority=sop["priority"],
                deadline_minutes=sop["deadline_min"],
                recommendation_reason=sop_reason,
            )
            assigned_tasks.append(task)
            trace(
                tool="assign_task",
                desc=f"Assigned SOP {sop['sop_id']} to {sop['team']}",
                input_args=(
                    f'sop_id="{sop["sop_id"]}", team="{sop["team"]}", '
                    f'deadline={sop["deadline_min"]}min, priority="{sop["priority"]}"'
                ),
                result_summary=f"Task {task['task_id']}: {action} -> {sop['team']}",
                decision=sop_reason,
            )

        return {
            "ward_id": ward_id,
            "event_id": event_id,
            "weather": weather,
            "risk_assessment": risk,
            "vulnerability_profile": vuln,
            "resources": resources,
            "action_plan": plan,
            "assigned_tasks": assigned_tasks,
            "agent_explanation": ai_summary,
            "candidate_sops": candidate_sops,
            "planner_output": planner_output,
            "previous_completed_tasks": [t.model_dump() for t in previous_completed_tasks],
            "carried_over_tasks": [t.model_dump() for t in active_previous_tasks],
            "trace_steps": trace_steps,  # ← real reasoning trace for frontend
            "severity_decision": severity,
            "tasks_rationale": f"{len(assigned_tasks)} tasks selected via {planner_output['planning_mode']} based on {severity} severity level" + (
                f" and {len(resource_gaps)} resource gap(s)" if resource_gaps else ""
            ),
        }

    def query(self, user_question: str, context_ward_id: Optional[str] = "ward_12") -> str:
        """
        Answer questions using real database facts.
        """
        ward = container.ward_repo.get_ward(context_ward_id)
        events = container.event_repo.list_events_by_ward(context_ward_id)
        vuln = container.vulnerability_repo.get_vulnerability(context_ward_id)
        tasks = container.task_repo.list_all_tasks()
        escalations = container.escalation_repo.list_all_escalations()
        active_event = events[0] if events else None

        fact_context = f"""
AUTHORITATIVE DATABASE STATE FOR CONTEXT:
- Target Ward: {ward.name if ward else context_ward_id} (Population: {ward.population if ward else 'Unknown'})
- Current Heat Event: Temp {active_event.temperature}°C, Humidity {active_event.humidity}%, Heat Index {active_event.heat_index}°C, Severity {active_event.severity.value if active_event else 'N/A'}
- Vulnerable Population: {vuln.outdoor_worker_count if vuln else 0} outdoor workers, {vuln.elderly_count if vuln else 0} elderly, {vuln.children_count if vuln else 0} children
- Total Tasks in System: {len(tasks)}
- Tasks Detail: {[t.model_dump() for t in tasks]}
- Active Escalations: {[e.model_dump() for e in escalations]}
"""
        full_prompt = f"{fact_context}\n\nUSER QUESTION: {user_question}"
        res = self.model_provider.invoke(prompt=full_prompt, system_prompt=SYSTEM_PROMPT)
        if res.get("error"):
            raise LLMPlanningError(f"Gemini query failed: {res['error']}")
        if not res.get("text"):
            raise LLMPlanningError("Gemini query returned an empty response.")
        return res["text"]
