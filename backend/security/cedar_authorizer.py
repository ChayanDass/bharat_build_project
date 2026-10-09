from pathlib import Path
from typing import Optional

from cedarpy import is_authorized


class CedarAuthorizer:
    """Evaluate HeatOps task permissions with the Cedar policy engine."""

    def __init__(self, policy_path: Optional[str] = None):
        default_policy = Path(__file__).with_name("policies") / "heatops.cedar"
        self.policies = Path(policy_path or default_policy).read_text(encoding="utf-8")

    def is_allowed(
        self,
        *,
        role: str,
        action: str,
        department: Optional[str],
        task_id: str,
        task_department: str,
    ) -> bool:
        principal = {
            "uid": {"type": "HeatOps::Operator", "id": f"{role}:{department or 'central'}"},
            "attrs": {
                "role": role,
                "department": department or "",
            },
            "parents": [],
        }
        resource = {
            "uid": {"type": "HeatOps::Task", "id": task_id},
            "attrs": {"department": task_department},
            "parents": [],
        }
        result = is_authorized(
            {
                "principal": f'HeatOps::Operator::"{principal["uid"]["id"]}"',
                "action": f'HeatOps::Action::"{action}"',
                "resource": f'HeatOps::Task::"{task_id}"',
                "context": {},
            },
            self.policies,
            [principal, resource],
        )
        return bool(result.allowed)
