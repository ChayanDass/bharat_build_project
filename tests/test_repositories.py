import pytest
from datetime import datetime, timezone
from backend.infrastructure.sqlite_repository import (
    SQLiteDatabase, SQLiteWardRepository, SQLiteHeatEventRepository, SQLiteTaskRepository
)
from backend.domain.models import Ward, HeatEvent, HeatSeverity, Task, TaskStatus, Priority, EscalationStatus


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_heatops.db"
    return SQLiteDatabase(str(db_file))


def test_ward_repository(test_db):
    repo = SQLiteWardRepository(test_db)
    ward = Ward(ward_id="w_test", name="Test Ward", city="Test City", population=10000)
    repo.save_ward(ward)

    fetched = repo.get_ward("w_test")
    assert fetched is not None
    assert fetched.name == "Test Ward"
    assert fetched.population == 10000


def test_event_repository(test_db):
    repo = SQLiteHeatEventRepository(test_db)
    event = HeatEvent(
        event_id="evt_test",
        ward_id="w_test",
        timestamp=datetime.now(timezone.utc),
        temperature=44.0,
        humidity=50.0,
        heat_index=51.0,
        severity=HeatSeverity.CRITICAL,
        duration=4
    )
    repo.save_event(event)

    fetched = repo.get_event("evt_test")
    assert fetched is not None
    assert fetched.severity == HeatSeverity.CRITICAL
    assert fetched.temperature == 44.0


def test_task_repository(test_db):
    repo = SQLiteTaskRepository(test_db)
    task = Task(
        task_id="t_test",
        plan_id="p_test",
        action="Water Supply Alert",
        responsible_team="Water Dept",
        priority=Priority.CRITICAL,
        deadline=datetime.now(timezone.utc),
        status=TaskStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        escalation_status=EscalationStatus.NONE
    )
    repo.save_task(task)

    fetched = repo.get_task("t_test")
    assert fetched is not None
    assert fetched.status == TaskStatus.PENDING

    repo.update_task_status("t_test", TaskStatus.COMPLETED)
    updated = repo.get_task("t_test")
    assert updated.status == TaskStatus.COMPLETED
    assert updated.completed_at is not None
