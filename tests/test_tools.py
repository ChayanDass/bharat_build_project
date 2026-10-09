import pytest
from backend.agent.tools import (
    get_weather, calculate_heat_risk, get_vulnerability, get_resources,
    create_action_plan, assign_task, check_task_status, escalate_task
)
from backend.config import container
from data.demo.seed_data import seed_demo_data


@pytest.fixture(autouse=True)
def setup_demo_data():
    seed_demo_data()


def test_tool_get_weather():
    w = get_weather("ward_12")
    assert w["temperature"] == 44.0
    assert w["severity"] == "CRITICAL"


def test_tool_calculate_heat_risk():
    r = calculate_heat_risk(44.0, 58.0)
    assert r["severity"] == "CRITICAL"
    assert r["is_critical"] is True


def test_tool_get_vulnerability():
    v = get_vulnerability("ward_12")
    assert v["outdoor_workers"] == 1200
    assert v["elderly"] == 3400


def test_tool_get_resources():
    res = get_resources("ward_12")
    assert res["total_resources"] >= 4


def test_tool_create_action_plan():
    plan = create_action_plan("evt_w12_001", priority="CRITICAL", summary="Test plan")
    assert plan["plan_id"].startswith("plan_evt_w12_001_")


def test_tool_assign_task():
    plan = create_action_plan("evt_w12_001")
    task = assign_task(plan["plan_id"], "Request water tanker", "Water Dept", priority="CRITICAL", deadline_minutes=30)
    assert task["action"] == "Request water tanker"
    assert task["responsible_team"] == "Water Dept"


def test_tool_check_task_status():
    plan = create_action_plan("evt_w12_001")
    task = assign_task(plan["plan_id"], "Deploy hydration station", "Ward Officers", priority="HIGH")
    status = check_task_status(plan["plan_id"])
    assert status["total_tasks"] >= 1


def test_tool_escalate_task():
    plan = create_action_plan("evt_w12_001")
    task = assign_task(plan["plan_id"], "Critical water supply", "Water Dept", priority="CRITICAL")
    res = escalate_task(task["task_id"], reason="Water tanker breakdown")
    assert res["status"] == "ESCALATED"
    assert res["escalation"]["reason"] == "Water tanker breakdown"
