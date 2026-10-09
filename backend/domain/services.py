import math
from datetime import datetime, timezone
from typing import Optional, Tuple, List
from backend.domain.models import HeatSeverity, Task, TaskStatus, Escalation, Priority, EscalationStatus


def calculate_heat_index(temperature_c: float, humidity: float) -> float:
    """
    Calculate Heat Index using Rothfusz regression equation.
    Input temperature in Celsius, humidity in %.
    Returns Heat Index in Celsius rounded to 1 decimal place.
    """
    # Convert Celsius to Fahrenheit
    T = (temperature_c * 9 / 5) + 32
    RH = humidity

    # Simple formula first
    hi = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (RH * 0.094))

    if hi >= 80:
        # Full Rothfusz regression
        hi = (
            -42.379
            + 2.04901523 * T
            + 10.14333127 * RH
            - 0.22475541 * T * RH
            - 0.00683783 * T * T
            - 0.05481717 * RH * RH
            + 0.00122874 * T * T * RH
            + 0.00085282 * T * RH * RH
            - 0.00000199 * T * T * RH * RH
        )

        # Adjustments
        if RH < 13 and 80 <= T <= 112:
            adjustment = ((13 - RH) / 4) * math.sqrt((17 - abs(T - 95.0)) / 17)
            hi -= adjustment
        elif RH > 85 and 80 <= T <= 87:
            adjustment = ((RH - 85) / 10) * ((87 - T) / 5)
            hi += adjustment

    # Convert back to Celsius
    hi_c = (hi - 32) * 5 / 9
    return round(hi_c, 1)


def calculate_heat_risk(
    temperature_c: float,
    humidity: float,
    duration_hours: int = 4,
    location_thresholds: Optional[dict] = None
) -> Tuple[HeatSeverity, float]:
    """
    Deterministic calculation of heat severity.
    Returns tuple of (HeatSeverity, heat_index_c).
    """
    heat_index_c = calculate_heat_index(temperature_c, humidity)

    # Use location specific thresholds if provided, else standard thresholds
    if location_thresholds:
        crit_hi = location_thresholds.get("critical_heat_index", 50.0)
        high_hi = location_thresholds.get("high_heat_index", 41.0)
        mod_hi = location_thresholds.get("moderate_heat_index", 32.0)
    else:
        crit_hi = 50.0
        high_hi = 41.0
        mod_hi = 32.0

    # Deterministic severity evaluation
    if heat_index_c >= crit_hi or temperature_c >= 44.0:
        severity = HeatSeverity.CRITICAL
    elif heat_index_c >= high_hi or temperature_c >= 40.0:
        severity = HeatSeverity.HIGH
    elif heat_index_c >= mod_hi or temperature_c >= 36.0:
        severity = HeatSeverity.MODERATE
    else:
        severity = HeatSeverity.LOW

    return severity, heat_index_c


class TaskLifecycleService:
    """Service to handle task transitions, overdue detection, and escalation."""

    @staticmethod
    def transition_status(task: Task, new_status: TaskStatus) -> Task:
        allowed_transitions = {
            TaskStatus.PENDING: [TaskStatus.NOTIFIED],
            TaskStatus.NOTIFIED: [TaskStatus.ACKNOWLEDGED, TaskStatus.OVERDUE, TaskStatus.ESCALATED],
            TaskStatus.ACKNOWLEDGED: [TaskStatus.NOTIFIED, TaskStatus.IN_PROGRESS, TaskStatus.OVERDUE, TaskStatus.ESCALATED],
            TaskStatus.IN_PROGRESS: [TaskStatus.NOTIFIED, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.OVERDUE, TaskStatus.ESCALATED],
            TaskStatus.OVERDUE: [TaskStatus.NOTIFIED, TaskStatus.ESCALATED, TaskStatus.COMPLETED, TaskStatus.FAILED],
            TaskStatus.ESCALATED: [TaskStatus.NOTIFIED, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.FAILED],
            TaskStatus.FAILED: [TaskStatus.NOTIFIED],
            TaskStatus.COMPLETED: [],
        }

        if new_status not in allowed_transitions.get(task.status, []):
            raise ValueError(f"Invalid task status transition from {task.status} to {new_status}")

        task.status = new_status
        task.updated_at = datetime.now(timezone.utc)
        if new_status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc)
            task.failure_reason = None
        elif new_status != TaskStatus.FAILED:
            task.failure_reason = None
        return task

    @staticmethod
    def check_and_escalate_task(task: Task, current_time: Optional[datetime] = None) -> Tuple[Task, Optional[Escalation]]:
        """
        Detect if a task is overdue and generate an Escalation record if needed.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Ensure task.deadline has timezone info if needed
        deadline = task.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        escalation_record = None

        active_statuses = (
            TaskStatus.NOTIFIED,
            TaskStatus.ACKNOWLEDGED,
            TaskStatus.IN_PROGRESS,
        )
        if current_time > deadline and task.status in active_statuses:
            task.status = TaskStatus.OVERDUE

            task.status = TaskStatus.ESCALATED
            task.escalation_status = EscalationStatus.ESCALATED
            task.updated_at = current_time
            task.updated_by = "HeatOps System"

            escalation_record = Escalation(
                escalation_id=f"esc_{task.task_id}_{int(current_time.timestamp())}",
                task_id=task.task_id,
                reason=f"Task '{task.action}' assigned to {task.responsible_team} missed deadline ({task.deadline.isoformat()}).",
                created_at=current_time,
                severity=task.priority,
                status="OPEN"
            )

        return task, escalation_record
