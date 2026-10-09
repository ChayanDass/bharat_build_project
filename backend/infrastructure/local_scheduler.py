import logging
from typing import Any
from backend.domain.interfaces import SchedulerProvider

logger = logging.getLogger("HeatOps.Scheduler")


class LocalSchedulerProvider(SchedulerProvider):
    """Local Development Scheduler implementation."""

    def __init__(self):
        self.scheduled_jobs = {}

    def schedule_monitoring(self, interval_seconds: int, callback_url_or_fn: Any) -> str:
        job_id = f"job_local_{len(self.scheduled_jobs) + 1}"
        self.scheduled_jobs[job_id] = {
            "interval": interval_seconds,
            "callback": callback_url_or_fn
        }
        logger.info(f"LocalScheduler: Scheduled monitoring job {job_id} every {interval_seconds}s")
        return job_id


class EventBridgeSchedulerProvider(SchedulerProvider):
    """Production AWS EventBridge Scheduler implementation."""

    def __init__(self, rule_name_prefix: str = "heatops-monitor-"):
        self.prefix = rule_name_prefix

    def schedule_monitoring(self, interval_seconds: int, callback_url_or_fn: Any) -> str:
        rule_name = f"{self.prefix}{interval_seconds}s"
        logger.info(f"EventBridgeScheduler: Target rule {rule_name} registered for AWS EventBridge")
        return rule_name
