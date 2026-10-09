from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from backend.domain.models import (
    Ward,
    VulnerabilityProfile,
    Resource,
    HeatEvent,
    ActionPlan,
    Task,
    Escalation,
    TaskStatus,
)


class WardRepository(ABC):
    @abstractmethod
    def get_ward(self, ward_id: str) -> Optional[Ward]:
        pass

    @abstractmethod
    def list_wards(self) -> List[Ward]:
        pass

    @abstractmethod
    def save_ward(self, ward: Ward) -> Ward:
        pass


class VulnerabilityRepository(ABC):
    @abstractmethod
    def get_vulnerability(self, ward_id: str) -> Optional[VulnerabilityProfile]:
        pass

    @abstractmethod
    def save_vulnerability(self, profile: VulnerabilityProfile) -> VulnerabilityProfile:
        pass


class ResourceRepository(ABC):
    @abstractmethod
    def get_resources_by_ward(self, ward_id: str) -> List[Resource]:
        pass

    @abstractmethod
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        pass

    @abstractmethod
    def save_resource(self, resource: Resource) -> Resource:
        pass


class HeatEventRepository(ABC):
    @abstractmethod
    def get_event(self, event_id: str) -> Optional[HeatEvent]:
        pass

    @abstractmethod
    def get_active_events(self) -> List[HeatEvent]:
        pass

    @abstractmethod
    def list_events_by_ward(self, ward_id: str) -> List[HeatEvent]:
        pass

    @abstractmethod
    def save_event(self, event: HeatEvent) -> HeatEvent:
        pass


class ActionPlanRepository(ABC):
    @abstractmethod
    def get_plan(self, plan_id: str) -> Optional[ActionPlan]:
        pass

    @abstractmethod
    def get_plan_by_event(self, event_id: str) -> Optional[ActionPlan]:
        pass

    @abstractmethod
    def save_plan(self, plan: ActionPlan) -> ActionPlan:
        pass


class TaskRepository(ABC):
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Task]:
        pass

    @abstractmethod
    def list_tasks_by_plan(self, plan_id: str) -> List[Task]:
        pass

    @abstractmethod
    def list_all_tasks(self) -> List[Task]:
        pass

    @abstractmethod
    def save_task(self, task: Task) -> Task:
        pass

    @abstractmethod
    def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        pass


class EscalationRepository(ABC):
    @abstractmethod
    def get_escalation(self, escalation_id: str) -> Optional[Escalation]:
        pass

    @abstractmethod
    def list_escalations_by_task(self, task_id: str) -> List[Escalation]:
        pass

    @abstractmethod
    def list_all_escalations(self) -> List[Escalation]:
        pass

    @abstractmethod
    def save_escalation(self, escalation: Escalation) -> Escalation:
        pass


class ModelProvider(ABC):
    @abstractmethod
    def invoke(self, prompt: str, system_prompt: Optional[str] = None, tools: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Invoke the model provider with prompt and tools."""
        pass


class SchedulerProvider(ABC):
    @abstractmethod
    def schedule_monitoring(self, interval_seconds: int, callback_url_or_fn: Any) -> str:
        """Schedule periodic monitoring check."""
        pass


class NotificationProvider(ABC):
    @abstractmethod
    def send_notification(self, recipient: str, message: str, topic: Optional[str] = None) -> bool:
        """Send notification to stakeholder/team."""
        pass
