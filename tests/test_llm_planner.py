import json

import pytest

from backend.agent.llm_planner import LLMPlanningError, plan_sops_with_llm


class StaticProvider:
    def __init__(self, text):
        self.text = text

    def invoke(self, prompt, system_prompt=None, tools=None):
        return {"text": self.text, "tool_calls": []}


def _candidate(sop_id, team="Ward Officers"):
    return {
        "sop_id": sop_id,
        "team": team,
        "action": f"Action {sop_id}",
        "priority": "HIGH",
        "deadline_min": 30,
        "conditions": ["always"],
        "description": f"Description {sop_id}",
    }


def test_llm_planner_validates_ids_without_inserting_required_sops():
    provider = StaticProvider(json.dumps({
        "selected_sop_ids": ["WO-01", "FAKE-99", "WO-01"],
        "priority_order": ["WO-01", "FAKE-99", "WO-01"],
        "selection_reasoning": {"WO-01": "Cooling refuge is required."},
        "rejected_sop_ids": {},
        "confidence": 0.8,
        "missing_information": [],
        "executive_summary": "These interventions address the ward's immediate heat risks.",
    }))
    candidates = [
        _candidate("WD-01", "Water Dept"),
        _candidate("LD-01", "Labour Dept"),
        _candidate("WO-01", "Ward Officers"),
        _candidate("HD-01", "Health Dept"),
    ]

    selected, output = plan_sops_with_llm(
        provider,
        ward_id="ward_12",
        ward_facts={"severity": "CRITICAL"},
        candidate_sops=candidates,
    )

    assert [sop["sop_id"] for sop in selected] == ["WO-01"]
    assert any("Rejected invalid" in note for note in output["validation_notes"])


def test_llm_planner_fails_when_json_is_invalid():
    provider = StaticProvider("not json")
    candidates = [_candidate("WO-05"), _candidate("WD-05", "Water Dept")]

    with pytest.raises(LLMPlanningError, match="invalid JSON"):
        plan_sops_with_llm(
            provider,
            ward_id="ward_31",
            ward_facts={"severity": "LOW"},
            candidate_sops=candidates,
        )
