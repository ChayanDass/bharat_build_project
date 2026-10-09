from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HeatSeverity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    NOTIFIED = "NOTIFIED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    OVERDUE = "OVERDUE"
    ESCALATED = "ESCALATED"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EscalationStatus(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"


class Ward(BaseModel):
    ward_id: str
    name: str
    city: str
    population: int
    risk_metadata: Dict[str, Any] = Field(default_factory=dict)


class VulnerabilityProfile(BaseModel):
    ward_id: str
    elderly_count: int
    children_count: int
    outdoor_worker_count: int
    high_risk_population: int
    vulnerability_score: float


class Resource(BaseModel):
    resource_id: str
    ward_id: str
    type: str  # e.g., "cooling_centre", "water_point", "health_centre", "water_tanker"
    name: str
    capacity: int
    availability: int
    contact_owner: str


class HeatEvent(BaseModel):
    event_id: str
    ward_id: str
    timestamp: datetime
    temperature: float  # in Celsius
    humidity: float     # percentage
    heat_index: float   # calculated in Celsius
    severity: HeatSeverity
    duration: int       # hours


class ActionPlan(BaseModel):
    plan_id: str
    event_id: str
    created_at: datetime
    priority: Priority
    status: str = "ACTIVE"
    summary: Optional[str] = None


class Task(BaseModel):
    task_id: str
    plan_id: str
    action: str
    responsible_team: str  # e.g., "Health Dept", "Water Dept", "Labour Dept", "Ward Officers"
    priority: Priority
    deadline: datetime
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime
    completed_at: Optional[datetime] = None
    escalation_status: EscalationStatus = EscalationStatus.NONE
    recommendation_reason: Optional[str] = None
    assigned_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    failure_reason: Optional[str] = None


class Escalation(BaseModel):
    escalation_id: str
    task_id: str
    reason: str
    created_at: datetime
    severity: Priority = Priority.CRITICAL
    status: str = "OPEN"  # OPEN, RESOLVED
