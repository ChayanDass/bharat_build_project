from typing import List, Optional
from backend.domain.models import Ward, VulnerabilityProfile, Resource, HeatEvent, ActionPlan, Task, Escalation, TaskStatus
from backend.domain.interfaces import (
    WardRepository, VulnerabilityRepository, ResourceRepository,
    HeatEventRepository, ActionPlanRepository, TaskRepository, EscalationRepository
)

try:
    import boto3
    from boto3.dynamodb.conditions import Key
except ImportError:
    boto3 = None


class DynamoDBWardRepository(WardRepository):
    def __init__(self, table_name: str = "heatops_wards", region_name: str = "us-east-1"):
        self.table_name = table_name
        self.region_name = region_name
        if boto3:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        else:
            self.table = None

    def get_ward(self, ward_id: str) -> Optional[Ward]:
        if not self.table:
            return None
        res = self.table.get_item(Key={"ward_id": ward_id})
        item = res.get("Item")
        return Ward(**item) if item else None

    def list_wards(self) -> List[Ward]:
        if not self.table:
            return []
        res = self.table.scan()
        return [Ward(**item) for item in res.get("Items", [])]

    def save_ward(self, ward: Ward) -> Ward:
        if self.table:
            self.table.put_item(Item=ward.model_dump())
        return ward


class DynamoDBVulnerabilityRepository(VulnerabilityRepository):
    def __init__(self, table_name: str = "heatops_vulnerabilities", region_name: str = "us-east-1"):
        self.table_name = table_name
        if boto3:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        else:
            self.table = None

    def get_vulnerability(self, ward_id: str) -> Optional[VulnerabilityProfile]:
        if not self.table:
            return None
        res = self.table.get_item(Key={"ward_id": ward_id})
        item = res.get("Item")
        return VulnerabilityProfile(**item) if item else None

    def save_vulnerability(self, profile: VulnerabilityProfile) -> VulnerabilityProfile:
        if self.table:
            self.table.put_item(Item=profile.model_dump())
        return profile


class DynamoDBResourceRepository(ResourceRepository):
    def __init__(self, table_name: str = "heatops_resources", region_name: str = "us-east-1"):
        self.table_name = table_name
        if boto3:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        else:
            self.table = None

    def get_resources_by_ward(self, ward_id: str) -> List[Resource]:
        if not self.table:
            return []
        res = self.table.query(KeyConditionExpression=Key("ward_id").eq(ward_id))
        return [Resource(**item) for item in res.get("Items", [])]

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        if not self.table:
            return None
        res = self.table.get_item(Key={"resource_id": resource_id})
        item = res.get("Item")
        return Resource(**item) if item else None

    def save_resource(self, resource: Resource) -> Resource:
        if self.table:
            self.table.put_item(Item=resource.model_dump())
        return resource


class DynamoDBHeatEventRepository(HeatEventRepository):
    def __init__(self, table_name: str = "heatops_events", region_name: str = "us-east-1"):
        self.table_name = table_name
        if boto3:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        else:
            self.table = None

    def get_event(self, event_id: str) -> Optional[HeatEvent]:
        if not self.table:
            return None
        res = self.table.get_item(Key={"event_id": event_id})
        item = res.get("Item")
        return HeatEvent(**item) if item else None

    def get_active_events(self) -> List[HeatEvent]:
        if not self.table:
            return []
        res = self.table.scan()
        return [HeatEvent(**item) for item in res.get("Items", [])]

    def list_events_by_ward(self, ward_id: str) -> List[HeatEvent]:
        if not self.table:
            return []
        res = self.table.scan(FilterExpression=Key("ward_id").eq(ward_id))
        return [HeatEvent(**item) for item in res.get("Items", [])]

    def save_event(self, event: HeatEvent) -> HeatEvent:
        if self.table:
            data = event.model_dump()
            data["timestamp"] = event.timestamp.isoformat()
            self.table.put_item(Item=data)
        return event


class DynamoDBActionPlanRepository(ActionPlanRepository):
    def __init__(self, table_name: str = "heatops_action_plans", region_name: str = "us-east-1"):
        self.table_name = table_name
        if boto3:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        else:
            self.table = None

    def get_plan(self, plan_id: str) -> Optional[ActionPlan]:
        if not self.table:
            return None
        res = self.table.get_item(Key={"plan_id": plan_id})
        item = res.get("Item")
        return ActionPlan(**item) if item else None

    def get_plan_by_event(self, event_id: str) -> Optional[ActionPlan]:
        if not self.table:
            return None
        scan_args = {"FilterExpression": Key("event_id").eq(event_id)}
        items = []
        while True:
            res = self.table.scan(**scan_args)
            items.extend(res.get("Items", []))
            last_key = res.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_args["ExclusiveStartKey"] = last_key
        if not items:
            return None
        latest = max(
            items,
            key=lambda item: (item.get("created_at", ""), item.get("plan_id", "")),
        )
        return ActionPlan(**latest)

    def save_plan(self, plan: ActionPlan) -> ActionPlan:
        if self.table:
            data = plan.model_dump()
            data["created_at"] = plan.created_at.isoformat()
            self.table.put_item(Item=data)
        return plan


class DynamoDBTaskRepository(TaskRepository):
    def __init__(self, table_name: str = "heatops_tasks", region_name: str = "us-east-1"):
        self.table_name = table_name
        if boto3:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        else:
            self.table = None

    def get_task(self, task_id: str) -> Optional[Task]:
        if not self.table:
            return None
        res = self.table.get_item(Key={"task_id": task_id})
        item = res.get("Item")
        return Task(**item) if item else None

    def list_tasks_by_plan(self, plan_id: str) -> List[Task]:
        if not self.table:
            return []
        res = self.table.scan(FilterExpression=Key("plan_id").eq(plan_id))
        return [Task(**item) for item in res.get("Items", [])]

    def list_all_tasks(self) -> List[Task]:
        if not self.table:
            return []
        res = self.table.scan()
        return [Task(**item) for item in res.get("Items", [])]

    def save_task(self, task: Task) -> Task:
        if self.table:
            data = task.model_dump()
            data["deadline"] = task.deadline.isoformat()
            data["created_at"] = task.created_at.isoformat()
            if task.completed_at:
                data["completed_at"] = task.completed_at.isoformat()
            if task.updated_at:
                data["updated_at"] = task.updated_at.isoformat()
            self.table.put_item(Item=data)
        return task

    def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
        task.status = status
        return self.save_task(task)


class DynamoDBEscalationRepository(EscalationRepository):
    def __init__(self, table_name: str = "heatops_escalations", region_name: str = "us-east-1"):
        self.table_name = table_name
        if boto3:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        else:
            self.table = None

    def get_escalation(self, escalation_id: str) -> Optional[Escalation]:
        if not self.table:
            return None
        res = self.table.get_item(Key={"escalation_id": escalation_id})
        item = res.get("Item")
        return Escalation(**item) if item else None

    def list_escalations_by_task(self, task_id: str) -> List[Escalation]:
        if not self.table:
            return []
        res = self.table.scan(FilterExpression=Key("task_id").eq(task_id))
        return [Escalation(**item) for item in res.get("Items", [])]

    def list_all_escalations(self) -> List[Escalation]:
        if not self.table:
            return []
        res = self.table.scan()
        return [Escalation(**item) for item in res.get("Items", [])]

    def save_escalation(self, escalation: Escalation) -> Escalation:
        if self.table:
            data = escalation.model_dump()
            data["created_at"] = escalation.created_at.isoformat()
            self.table.put_item(Item=data)
        return escalation
