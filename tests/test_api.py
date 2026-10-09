import pytest
from fastapi.testclient import TestClient
from backend.main import app
from data.demo.seed_data import seed_demo_data

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    seed_demo_data()


def test_health_check():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["system"] == "HeatOps Command Centre"


def test_list_wards():
    res = client.get("/api/wards")
    assert res.status_code == 200
    wards = res.json()
    assert len(wards) >= 4


def test_list_events():
    res = client.get("/api/events")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 4


def test_low_severity_demo_ward_exists():
    res = client.get("/api/events/ward_31", headers={"X-HeatOps-Role": "central"})
    assert res.status_code == 200
    detail = res.json()
    assert detail["event"]["severity"] == "LOW"
    assert detail["event"]["temperature"] == 31.0


def test_get_event_detail():
    res = client.get("/api/events/ward_12", headers={"X-HeatOps-Role": "central"})
    assert res.status_code == 200
    detail = res.json()
    assert detail["event"]["severity"] == "CRITICAL"
    assert detail["vulnerability"]["outdoor_worker_count"] == 1200


def test_trigger_agent_coordination():
    res = client.post(
        "/api/agent/coordinate/ward_12",
        headers={"X-HeatOps-Role": "central"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ward_id"] == "ward_12"
    assert len(data["assigned_tasks"]) >= 4
    assert any(step["tool"] == "candidate_sops" for step in data["trace_steps"])
    assert any(step["tool"] == "llm_operational_planner" for step in data["trace_steps"])
    assert "planner_output" in data

    teams_by_action = {task["action"]: task["responsible_team"] for task in data["assigned_tasks"]}
    assert teams_by_action["Dispatch emergency water tanker to high-stress water point"] == "Water Dept"
    assert teams_by_action["Activate Cooling Centre B & open it as 24-hour heat refuge"] == "Ward Officers"
    assert teams_by_action["Enforce mandatory rest breaks for outdoor workers (no outdoor work 12 PM–4 PM)"] == "Labour Dept"


def test_simulate_overdue():
    # First coordinate ward 12 to create tasks
    coord_res = client.post(
        "/api/agent/coordinate/ward_12",
        headers={"X-HeatOps-Role": "central"},
    )
    tasks = coord_res.json()["assigned_tasks"]
    water_task = [t for t in tasks if "water" in t["action"].lower()][0]

    assign_res = client.post(
        f"/api/tasks/{water_task['task_id']}/assign",
        json={"responsible_team": "Water Dept"},
        headers={"X-HeatOps-Role": "central"},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "NOTIFIED"

    # Simulate overdue
    sim_res = client.post(
        f"/api/simulate/overdue/{water_task['task_id']}",
        headers={"X-HeatOps-Role": "central"},
    )
    assert sim_res.status_code == 200
    data = sim_res.json()
    assert data["task"]["status"] == "ESCALATED"
    assert data["escalation"] is not None


def test_department_status_is_scoped_and_persisted():
    coord_res = client.post(
        "/api/agent/coordinate/ward_12",
        headers={"X-HeatOps-Role": "central"},
    )
    task = coord_res.json()["assigned_tasks"][0]
    department = task["responsible_team"]

    assigned = client.post(
        f"/api/tasks/{task['task_id']}/assign",
        json={"responsible_team": department},
        headers={"X-HeatOps-Role": "central"},
    )
    assert assigned.status_code == 200

    department_headers = {
        "X-HeatOps-Role": "department",
        "X-HeatOps-Department": department,
    }
    inbox = client.get(
        "/api/department/tasks",
        params={"department": department},
        headers=department_headers,
    )
    assert inbox.status_code == 200
    assert task["task_id"] in {item["task_id"] for item in inbox.json()}
    other_inbox = client.get(
        "/api/department/tasks",
        params={"department": "Other Dept"},
        headers=department_headers,
    )
    assert other_inbox.status_code == 403

    acknowledged = client.post(
        f"/api/department/{department}/tasks/{task['task_id']}/status",
        json={"status": "ACKNOWLEDGED", "updated_by": f"{department} Operator"},
        headers=department_headers,
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["updated_at"] is not None
    assert acknowledged.json()["updated_by"] == f"{department} Operator"

    initiated = client.post(
        f"/api/department/{department}/tasks/{task['task_id']}/status",
        json={"status": "IN_PROGRESS", "updated_by": f"{department} Operator"},
        headers=department_headers,
    )
    assert initiated.status_code == 200
    stored = client.get(
        f"/api/tasks/{task['task_id']}",
        headers={"X-HeatOps-Role": "central"},
    )
    assert stored.json()["status"] == "IN_PROGRESS"
