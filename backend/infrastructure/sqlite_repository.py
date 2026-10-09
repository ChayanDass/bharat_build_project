import sqlite3
import json
from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.domain.models import (
    Ward,
    VulnerabilityProfile,
    Resource,
    HeatEvent,
    ActionPlan,
    Task,
    Escalation,
    HeatSeverity,
    TaskStatus,
    Priority,
    EscalationStatus,
)
from backend.domain.interfaces import (
    WardRepository,
    VulnerabilityRepository,
    ResourceRepository,
    HeatEventRepository,
    ActionPlanRepository,
    TaskRepository,
    EscalationRepository,
)


def datetime_to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def iso_to_datetime(s: str) -> datetime:
    return datetime.fromisoformat(s)


class SQLiteDatabase:
    """Manages SQLite connection and schema creation."""

    def __init__(self, db_path: str = "heatops_dev.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS wards (
                ward_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                population INTEGER NOT NULL,
                risk_metadata TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerability_profiles (
                ward_id TEXT PRIMARY KEY,
                elderly_count INTEGER NOT NULL,
                children_count INTEGER NOT NULL,
                outdoor_worker_count INTEGER NOT NULL,
                high_risk_population INTEGER NOT NULL,
                vulnerability_score REAL NOT NULL,
                FOREIGN KEY (ward_id) REFERENCES wards(ward_id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                resource_id TEXT PRIMARY KEY,
                ward_id TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                availability INTEGER NOT NULL,
                contact_owner TEXT NOT NULL,
                FOREIGN KEY (ward_id) REFERENCES wards(ward_id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS heat_events (
                event_id TEXT PRIMARY KEY,
                ward_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                heat_index REAL NOT NULL,
                severity TEXT NOT NULL,
                duration INTEGER NOT NULL,
                FOREIGN KEY (ward_id) REFERENCES wards(ward_id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_plans (
                plan_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT,
                FOREIGN KEY (event_id) REFERENCES heat_events(event_id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                action TEXT NOT NULL,
                responsible_team TEXT NOT NULL,
                priority TEXT NOT NULL,
                deadline TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                escalation_status TEXT NOT NULL,
                recommendation_reason TEXT,
                assigned_by TEXT,
                updated_at TEXT,
                updated_by TEXT,
                failure_reason TEXT,
                FOREIGN KEY (plan_id) REFERENCES action_plans(plan_id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                escalation_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            );
            """)
            task_columns = {
                row["name"]
                for row in cursor.execute("PRAGMA table_info(tasks)").fetchall()
            }
            for column, column_type in (
                ("assigned_by", "TEXT"),
                ("updated_at", "TEXT"),
                ("updated_by", "TEXT"),
                ("failure_reason", "TEXT"),
                ("recommendation_reason", "TEXT"),
            ):
                if column not in task_columns:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {column} {column_type}")
            conn.commit()


class SQLiteWardRepository(WardRepository):
    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def get_ward(self, ward_id: str) -> Optional[Ward]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM wards WHERE ward_id = ?", (ward_id,)).fetchone()
            if not row:
                return None
            return Ward(
                ward_id=row["ward_id"],
                name=row["name"],
                city=row["city"],
                population=row["population"],
                risk_metadata=json.loads(row["risk_metadata"]) if row["risk_metadata"] else {}
            )

    def list_wards(self) -> List[Ward]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM wards").fetchall()
            return [
                Ward(
                    ward_id=row["ward_id"],
                    name=row["name"],
                    city=row["city"],
                    population=row["population"],
                    risk_metadata=json.loads(row["risk_metadata"]) if row["risk_metadata"] else {}
                ) for row in rows
            ]

    def save_ward(self, ward: Ward) -> Ward:
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO wards (ward_id, name, city, population, risk_metadata) VALUES (?, ?, ?, ?, ?)",
                (ward.ward_id, ward.name, ward.city, ward.population, json.dumps(ward.risk_metadata))
            )
            conn.commit()
        return ward


class SQLiteVulnerabilityRepository(VulnerabilityRepository):
    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def get_vulnerability(self, ward_id: str) -> Optional[VulnerabilityProfile]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM vulnerability_profiles WHERE ward_id = ?", (ward_id,)).fetchone()
            if not row:
                return None
            return VulnerabilityProfile(
                ward_id=row["ward_id"],
                elderly_count=row["elderly_count"],
                children_count=row["children_count"],
                outdoor_worker_count=row["outdoor_worker_count"],
                high_risk_population=row["high_risk_population"],
                vulnerability_score=row["vulnerability_score"]
            )

    def save_vulnerability(self, profile: VulnerabilityProfile) -> VulnerabilityProfile:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO vulnerability_profiles
                (ward_id, elderly_count, children_count, outdoor_worker_count, high_risk_population, vulnerability_score)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (profile.ward_id, profile.elderly_count, profile.children_count, profile.outdoor_worker_count, profile.high_risk_population, profile.vulnerability_score)
            )
            conn.commit()
        return profile


class SQLiteResourceRepository(ResourceRepository):
    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def get_resources_by_ward(self, ward_id: str) -> List[Resource]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM resources WHERE ward_id = ?", (ward_id,)).fetchall()
            return [
                Resource(
                    resource_id=row["resource_id"],
                    ward_id=row["ward_id"],
                    type=row["type"],
                    name=row["name"],
                    capacity=row["capacity"],
                    availability=row["availability"],
                    contact_owner=row["contact_owner"]
                ) for row in rows
            ]

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM resources WHERE resource_id = ?", (resource_id,)).fetchone()
            if not row:
                return None
            return Resource(
                resource_id=row["resource_id"],
                ward_id=row["ward_id"],
                type=row["type"],
                name=row["name"],
                capacity=row["capacity"],
                availability=row["availability"],
                contact_owner=row["contact_owner"]
            )

    def save_resource(self, resource: Resource) -> Resource:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO resources
                (resource_id, ward_id, type, name, capacity, availability, contact_owner)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (resource.resource_id, resource.ward_id, resource.type, resource.name, resource.capacity, resource.availability, resource.contact_owner)
            )
            conn.commit()
        return resource


class SQLiteHeatEventRepository(HeatEventRepository):
    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def get_event(self, event_id: str) -> Optional[HeatEvent]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM heat_events WHERE event_id = ?", (event_id,)).fetchone()
            if not row:
                return None
            return HeatEvent(
                event_id=row["event_id"],
                ward_id=row["ward_id"],
                timestamp=iso_to_datetime(row["timestamp"]),
                temperature=row["temperature"],
                humidity=row["humidity"],
                heat_index=row["heat_index"],
                severity=HeatSeverity(row["severity"]),
                duration=row["duration"]
            )

    def get_active_events(self) -> List[HeatEvent]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM heat_events ORDER BY timestamp DESC").fetchall()
            return [
                HeatEvent(
                    event_id=row["event_id"],
                    ward_id=row["ward_id"],
                    timestamp=iso_to_datetime(row["timestamp"]),
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                    heat_index=row["heat_index"],
                    severity=HeatSeverity(row["severity"]),
                    duration=row["duration"]
                ) for row in rows
            ]

    def list_events_by_ward(self, ward_id: str) -> List[HeatEvent]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM heat_events WHERE ward_id = ? ORDER BY timestamp DESC", (ward_id,)).fetchall()
            return [
                HeatEvent(
                    event_id=row["event_id"],
                    ward_id=row["ward_id"],
                    timestamp=iso_to_datetime(row["timestamp"]),
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                    heat_index=row["heat_index"],
                    severity=HeatSeverity(row["severity"]),
                    duration=row["duration"]
                ) for row in rows
            ]

    def save_event(self, event: HeatEvent) -> HeatEvent:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO heat_events
                (event_id, ward_id, timestamp, temperature, humidity, heat_index, severity, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id,
                    event.ward_id,
                    datetime_to_iso(event.timestamp),
                    event.temperature,
                    event.humidity,
                    event.heat_index,
                    event.severity.value if isinstance(event.severity, Enum) else event.severity,
                    event.duration,
                )
            )
            conn.commit()
        return event


class SQLiteActionPlanRepository(ActionPlanRepository):
    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def get_plan(self, plan_id: str) -> Optional[ActionPlan]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM action_plans WHERE plan_id = ?", (plan_id,)).fetchone()
            if not row:
                return None
            return ActionPlan(
                plan_id=row["plan_id"],
                event_id=row["event_id"],
                created_at=iso_to_datetime(row["created_at"]),
                priority=Priority(row["priority"]),
                status=row["status"],
                summary=row["summary"]
            )

    def get_plan_by_event(self, event_id: str) -> Optional[ActionPlan]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM action_plans WHERE event_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1", (event_id,)).fetchone()
            if not row:
                return None
            return ActionPlan(
                plan_id=row["plan_id"],
                event_id=row["event_id"],
                created_at=iso_to_datetime(row["created_at"]),
                priority=Priority(row["priority"]),
                status=row["status"],
                summary=row["summary"]
            )

    def save_plan(self, plan: ActionPlan) -> ActionPlan:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO action_plans
                (plan_id, event_id, created_at, priority, status, summary)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    plan.plan_id,
                    plan.event_id,
                    datetime_to_iso(plan.created_at),
                    plan.priority.value if isinstance(plan.priority, Enum) else plan.priority,
                    plan.status,
                    plan.summary
                )
            )
            conn.commit()
        return plan


class SQLiteTaskRepository(TaskRepository):
    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def get_task(self, task_id: str) -> Optional[Task]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if not row:
                return None
            return Task(
                task_id=row["task_id"],
                plan_id=row["plan_id"],
                action=row["action"],
                responsible_team=row["responsible_team"],
                priority=Priority(row["priority"]),
                deadline=iso_to_datetime(row["deadline"]),
                status=TaskStatus(row["status"]),
                created_at=iso_to_datetime(row["created_at"]),
                completed_at=iso_to_datetime(row["completed_at"]) if row["completed_at"] else None,
                escalation_status=EscalationStatus(row["escalation_status"]),
                recommendation_reason=row["recommendation_reason"],
                assigned_by=row["assigned_by"],
                updated_at=iso_to_datetime(row["updated_at"]) if row["updated_at"] else None,
                updated_by=row["updated_by"],
                failure_reason=row["failure_reason"],
            )

    def list_tasks_by_plan(self, plan_id: str) -> List[Task]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM tasks WHERE plan_id = ? ORDER BY deadline ASC", (plan_id,)).fetchall()
            return [
                Task(
                    task_id=row["task_id"],
                    plan_id=row["plan_id"],
                    action=row["action"],
                    responsible_team=row["responsible_team"],
                    priority=Priority(row["priority"]),
                    deadline=iso_to_datetime(row["deadline"]),
                    status=TaskStatus(row["status"]),
                    created_at=iso_to_datetime(row["created_at"]),
                    completed_at=iso_to_datetime(row["completed_at"]) if row["completed_at"] else None,
                    escalation_status=EscalationStatus(row["escalation_status"]),
                    recommendation_reason=row["recommendation_reason"],
                    assigned_by=row["assigned_by"],
                    updated_at=iso_to_datetime(row["updated_at"]) if row["updated_at"] else None,
                    updated_by=row["updated_by"],
                    failure_reason=row["failure_reason"],
                ) for row in rows
            ]

    def list_all_tasks(self) -> List[Task]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY deadline ASC").fetchall()
            return [
                Task(
                    task_id=row["task_id"],
                    plan_id=row["plan_id"],
                    action=row["action"],
                    responsible_team=row["responsible_team"],
                    priority=Priority(row["priority"]),
                    deadline=iso_to_datetime(row["deadline"]),
                    status=TaskStatus(row["status"]),
                    created_at=iso_to_datetime(row["created_at"]),
                    completed_at=iso_to_datetime(row["completed_at"]) if row["completed_at"] else None,
                    escalation_status=EscalationStatus(row["escalation_status"]),
                    recommendation_reason=row["recommendation_reason"],
                    assigned_by=row["assigned_by"],
                    updated_at=iso_to_datetime(row["updated_at"]) if row["updated_at"] else None,
                    updated_by=row["updated_by"],
                    failure_reason=row["failure_reason"],
                ) for row in rows
            ]

    def save_task(self, task: Task) -> Task:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO tasks
                (task_id, plan_id, action, responsible_team, priority, deadline, status, created_at, completed_at, escalation_status, recommendation_reason, assigned_by, updated_at, updated_by, failure_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.task_id,
                    task.plan_id,
                    task.action,
                    task.responsible_team,
                    task.priority.value if isinstance(task.priority, Enum) else task.priority,
                    datetime_to_iso(task.deadline),
                    task.status.value if isinstance(task.status, Enum) else task.status,
                    datetime_to_iso(task.created_at),
                    datetime_to_iso(task.completed_at) if task.completed_at else None,
                    task.escalation_status.value if isinstance(task.escalation_status, Enum) else task.escalation_status,
                    task.recommendation_reason,
                    task.assigned_by,
                    datetime_to_iso(task.updated_at) if task.updated_at else None,
                    task.updated_by,
                    task.failure_reason,
                )
            )
            conn.commit()
        return task

    def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
        task.status = status
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc)
        return self.save_task(task)


class SQLiteEscalationRepository(EscalationRepository):
    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def get_escalation(self, escalation_id: str) -> Optional[Escalation]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM escalations WHERE escalation_id = ?", (escalation_id,)).fetchone()
            if not row:
                return None
            return Escalation(
                escalation_id=row["escalation_id"],
                task_id=row["task_id"],
                reason=row["reason"],
                created_at=iso_to_datetime(row["created_at"]),
                severity=Priority(row["severity"]),
                status=row["status"]
            )

    def list_escalations_by_task(self, task_id: str) -> List[Escalation]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM escalations WHERE task_id = ? ORDER BY created_at DESC", (task_id,)).fetchall()
            return [
                Escalation(
                    escalation_id=row["escalation_id"],
                    task_id=row["task_id"],
                    reason=row["reason"],
                    created_at=iso_to_datetime(row["created_at"]),
                    severity=Priority(row["severity"]),
                    status=row["status"]
                ) for row in rows
            ]

    def list_all_escalations(self) -> List[Escalation]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC").fetchall()
            return [
                Escalation(
                    escalation_id=row["escalation_id"],
                    task_id=row["task_id"],
                    reason=row["reason"],
                    created_at=iso_to_datetime(row["created_at"]),
                    severity=Priority(row["severity"]),
                    status=row["status"]
                ) for row in rows
            ]

    def save_escalation(self, escalation: Escalation) -> Escalation:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO escalations
                (escalation_id, task_id, reason, created_at, severity, status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    escalation.escalation_id,
                    escalation.task_id,
                    escalation.reason,
                    datetime_to_iso(escalation.created_at),
                    escalation.severity.value if isinstance(escalation.severity, Enum) else escalation.severity,
                    escalation.status
                )
            )
            conn.commit()
        return escalation
