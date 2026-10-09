import pytest
from datetime import datetime, timezone, timedelta
from backend.domain.models import Task, TaskStatus, Priority, EscalationStatus
from backend.domain.services import TaskLifecycleService


def test_task_lifecycle_happy_path():
    now = datetime.now(timezone.utc)
    task = Task(
        task_id="t_life",
        plan_id="p_life",
        action="Deploy cooling tents",
        responsible_team="Ward Officers",
        priority=Priority.HIGH,
        deadline=now + timedelta(hours=1),
        status=TaskStatus.PENDING,
        created_at=now,
        escalation_status=EscalationStatus.NONE
    )

    notified = TaskLifecycleService.transition_status(task, TaskStatus.NOTIFIED)
    assert notified.status == TaskStatus.NOTIFIED

    t1 = TaskLifecycleService.transition_status(notified, TaskStatus.ACKNOWLEDGED)
    assert t1.status == TaskStatus.ACKNOWLEDGED

    t2 = TaskLifecycleService.transition_status(t1, TaskStatus.IN_PROGRESS)
    assert t2.status == TaskStatus.IN_PROGRESS

    t3 = TaskLifecycleService.transition_status(t2, TaskStatus.COMPLETED)
    assert t3.status == TaskStatus.COMPLETED
    assert t3.completed_at is not None


def test_task_lifecycle_overdue_and_escalation():
    now = datetime.now(timezone.utc)
    expired_task = Task(
        task_id="t_overdue",
        plan_id="p_life",
        action="Request additional water supply",
        responsible_team="Water Dept",
        priority=Priority.CRITICAL,
        deadline=now - timedelta(minutes=15),
        status=TaskStatus.NOTIFIED,
        created_at=now - timedelta(hours=1),
        escalation_status=EscalationStatus.NONE
    )

    updated_task, esc = TaskLifecycleService.check_and_escalate_task(expired_task, current_time=now)
    assert updated_task.status == TaskStatus.ESCALATED
    assert updated_task.escalation_status == EscalationStatus.ESCALATED
    assert updated_task.updated_by == "HeatOps System"
    assert esc is not None
    assert "missed deadline" in esc.reason


def test_department_can_report_failure_and_operator_can_retry():
    now = datetime.now(timezone.utc)
    task = Task(
        task_id="t_failed",
        plan_id="p_life",
        action="Inspect water pumps",
        responsible_team="Water Dept",
        priority=Priority.HIGH,
        deadline=now + timedelta(hours=1),
        status=TaskStatus.NOTIFIED,
        created_at=now,
        escalation_status=EscalationStatus.NONE,
    )

    acknowledged = TaskLifecycleService.transition_status(task, TaskStatus.ACKNOWLEDGED)
    in_progress = TaskLifecycleService.transition_status(acknowledged, TaskStatus.IN_PROGRESS)
    failed = TaskLifecycleService.transition_status(in_progress, TaskStatus.FAILED)
    assert failed.status == TaskStatus.FAILED

    retried = TaskLifecycleService.transition_status(failed, TaskStatus.NOTIFIED)

    assert retried.status == TaskStatus.NOTIFIED
    assert retried.completed_at is None


def test_pending_recommendation_does_not_auto_escalate():
    now = datetime.now(timezone.utc)
    pending_task = Task(
        task_id="t_pending",
        plan_id="p_life",
        action="Review heat safety plan",
        responsible_team="Ward Officers",
        priority=Priority.HIGH,
        deadline=now - timedelta(minutes=15),
        status=TaskStatus.PENDING,
        created_at=now - timedelta(hours=1),
        escalation_status=EscalationStatus.NONE,
    )

    updated_task, escalation = TaskLifecycleService.check_and_escalate_task(pending_task, now)

    assert updated_task.status == TaskStatus.PENDING
    assert escalation is None
