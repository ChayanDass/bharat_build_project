import json
import re
from typing import Any, Dict, List, Tuple


REQUIRED_BY_SEVERITY = {
    "CRITICAL": {"WD-01", "LD-01", "WO-01", "HD-01"},
    "HIGH": {"LD-02", "WO-02", "HD-03"},
    "MODERATE": {"WO-04", "WO-05", "HD-03"},
    "LOW": {"WO-05"},
}

class LLMPlanningError(RuntimeError):
    """Raised when the configured language-model provider cannot produce a valid plan."""


def _candidate_payload(candidate_sops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "sop_id": sop["sop_id"],
            "team": sop["team"],
            "action": sop["action"],
            "priority": sop["priority"],
            "deadline_min": sop["deadline_min"],
            "conditions": sop["conditions"],
            "description": sop["description"],
        }
        for sop in candidate_sops
    ]


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def plan_sops_with_llm(
    model_provider: Any,
    ward_id: str,
    ward_facts: Dict[str, Any],
    candidate_sops: List[Dict[str, Any]],
    max_tasks: int = 12,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Ask the LLM to choose SOP IDs from already-eligible candidates, then validate.
    The model never creates tasks directly; backend validation owns execution.
    """
    candidate_by_id = {sop["sop_id"]: sop for sop in candidate_sops}
    candidate_ids = set(candidate_by_id)
    severity = str(ward_facts.get("severity", "")).upper()
    required_ids = REQUIRED_BY_SEVERITY.get(severity, set()) & candidate_ids

    prompt = f"""
You are HeatOps Operational Planner, a bounded municipal emergency-response agent.

You MUST choose only SOP IDs from candidate_sops. Do not invent actions, teams, deadlines, or departments.
Prefer the smallest high-impact plan that covers life safety, water, cooling, health, and field enforcement.
Use previous_completed_actions as historical context; each entry includes the environmental conditions when that action was planned. Do not treat those historical conditions as current.
Use active_previous_actions as the current work queue; each entry includes its latest status and deadline. Avoid duplicating an active assignment unless changed conditions require a replacement, and explain any replacement in selection_reasoning.
Required SOPs for this severity must be included unless impossible: {sorted(required_ids)}
Maximum preferred task count: {max_tasks}

Return ONLY valid JSON with this schema:
{{
  "selected_sop_ids": ["SOP-ID"],
  "priority_order": ["SOP-ID"],
  "selection_reasoning": {{"SOP-ID": "short operational reason"}},
  "rejected_sop_ids": {{"SOP-ID": "why not selected"}},
  "confidence": 0.0,
  "missing_information": ["item"],
  "executive_summary": "Concise factual explanation of the selected interventions."
}}

ward_id: {ward_id}
ward_facts:
{json.dumps(ward_facts, indent=2)}

candidate_sops:
{json.dumps(_candidate_payload(candidate_sops), indent=2)}
"""

    response = model_provider.invoke(
        prompt=prompt,
        system_prompt=(
            "You are a strict JSON planning engine. Select only provided SOP IDs. "
            "Never create new interventions."
        ),
    )
    if response.get("error"):
        raise LLMPlanningError(f"Configured planner failed: {response['error']}")

    raw_text = response.get("text", "")
    try:
        plan = _extract_json(raw_text)
    except Exception as exc:
        raise LLMPlanningError(
            f"Gemini planner returned invalid JSON. Raw response: {raw_text[:300]}"
        ) from exc

    if not isinstance(plan, dict):
        raise LLMPlanningError("Gemini planner JSON was not an object.")
    executive_summary = plan.get("executive_summary")
    if not isinstance(executive_summary, str) or not executive_summary.strip():
        raise LLMPlanningError("Gemini planner did not return an executive summary.")

    selected_ids = plan.get("priority_order") or plan.get("selected_sop_ids") or []
    if not isinstance(selected_ids, list):
        raise LLMPlanningError("Gemini planner did not return a valid SOP ID list.")
    validation_notes = []
    valid_ids = []
    for sop_id in selected_ids:
        if sop_id in candidate_ids and sop_id not in valid_ids:
            valid_ids.append(sop_id)
        else:
            validation_notes.append(f"Rejected invalid or duplicate SOP ID from LLM: {sop_id}")

    if candidate_sops and not valid_ids:
        raise LLMPlanningError("Gemini planner returned no valid candidate SOP IDs.")

    selected_sops = [candidate_by_id[sop_id] for sop_id in valid_ids]
    rejected_ids = sorted(candidate_ids - set(valid_ids))
    rejected_from_plan = plan.get("rejected_sop_ids") if isinstance(plan.get("rejected_sop_ids"), dict) else {}

    planner_output = {
        "selected_sop_ids": valid_ids,
        "priority_order": valid_ids,
        "selection_reasoning": plan.get("selection_reasoning", {}),
        "rejected_sop_ids": {
            sop_id: rejected_from_plan.get(sop_id, "Not selected after LLM prioritization and backend validation.")
            for sop_id in rejected_ids
        },
        "confidence": plan.get("confidence", 0.0),
        "missing_information": plan.get("missing_information", []),
        "validation_notes": validation_notes,
        "planning_mode": "llm_planned",
        "executive_summary": executive_summary.strip(),
        "raw_llm_text": raw_text[:2000],
    }
    return selected_sops, planner_output
