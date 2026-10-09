import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file
load_dotenv(override=True)


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LLM_PROVIDER: str = "gemini"
    DATABASE_PROVIDER: str = "sqlite"
    SCHEDULER_PROVIDER: str = "local"
    NOTIFICATION_PROVIDER: str = "console"
    AUTHORIZATION_PROVIDER: str = "cedar"

    GEMINI_API_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    SQLITE_DB_PATH: str = "heatops_dev.db"
    CEDAR_POLICY_PATH: Optional[str] = None
    SNS_TOPIC_ARN: Optional[str] = None
    LOCALSTACK_ENDPOINT_URL: str = "http://localhost:4566"
    LOCALSTACK_SNS_TOPIC_NAME: str = "heatops-notifications"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


class Container:
    """Dependency Injection Container."""
    def __init__(self, cfg: Settings = settings):
        self.cfg = cfg
        self._init_infrastructure()

    def _init_infrastructure(self):
        # Database & Repositories
        if self.cfg.DATABASE_PROVIDER == "sqlite":
            from backend.infrastructure.sqlite_repository import (
                SQLiteDatabase, SQLiteWardRepository, SQLiteVulnerabilityRepository,
                SQLiteResourceRepository, SQLiteHeatEventRepository, SQLiteActionPlanRepository,
                SQLiteTaskRepository, SQLiteEscalationRepository
            )
            self.db = SQLiteDatabase(self.cfg.SQLITE_DB_PATH)
            self.ward_repo = SQLiteWardRepository(self.db)
            self.vulnerability_repo = SQLiteVulnerabilityRepository(self.db)
            self.resource_repo = SQLiteResourceRepository(self.db)
            self.event_repo = SQLiteHeatEventRepository(self.db)
            self.action_plan_repo = SQLiteActionPlanRepository(self.db)
            self.task_repo = SQLiteTaskRepository(self.db)
            self.escalation_repo = SQLiteEscalationRepository(self.db)
        else:
            from backend.infrastructure.dynamodb_repository import (
                DynamoDBWardRepository, DynamoDBVulnerabilityRepository,
                DynamoDBResourceRepository, DynamoDBHeatEventRepository,
                DynamoDBActionPlanRepository, DynamoDBTaskRepository,
                DynamoDBEscalationRepository
            )
            self.ward_repo = DynamoDBWardRepository(region_name=self.cfg.AWS_REGION)
            self.vulnerability_repo = DynamoDBVulnerabilityRepository(region_name=self.cfg.AWS_REGION)
            self.resource_repo = DynamoDBResourceRepository(region_name=self.cfg.AWS_REGION)
            self.event_repo = DynamoDBHeatEventRepository(region_name=self.cfg.AWS_REGION)
            self.action_plan_repo = DynamoDBActionPlanRepository(region_name=self.cfg.AWS_REGION)
            self.task_repo = DynamoDBTaskRepository(region_name=self.cfg.AWS_REGION)
            self.escalation_repo = DynamoDBEscalationRepository(region_name=self.cfg.AWS_REGION)

        # Model Provider
        if self.cfg.LLM_PROVIDER == "gemini":
            from backend.infrastructure.gemini_provider import GeminiModelProvider
            self.model_provider = GeminiModelProvider(api_key=self.cfg.GEMINI_API_KEY)
        elif self.cfg.LLM_PROVIDER == "bedrock":
            from backend.infrastructure.bedrock_provider import BedrockModelProvider
            self.model_provider = BedrockModelProvider(region_name=self.cfg.AWS_REGION)
        else:
            from backend.infrastructure.mock_provider import MockModelProvider
            self.model_provider = MockModelProvider()

        # Scheduler Provider
        if self.cfg.SCHEDULER_PROVIDER == "local":
            from backend.infrastructure.local_scheduler import LocalSchedulerProvider
            self.scheduler_provider = LocalSchedulerProvider()
        else:
            from backend.infrastructure.local_scheduler import EventBridgeSchedulerProvider
            self.scheduler_provider = EventBridgeSchedulerProvider()

        # Notification Provider
        if self.cfg.NOTIFICATION_PROVIDER == "console":
            from backend.infrastructure.console_notification import ConsoleNotificationProvider
            self.notification_provider = ConsoleNotificationProvider()
        elif self.cfg.NOTIFICATION_PROVIDER == "sns":
            from backend.infrastructure.console_notification import SNSNotificationProvider
            if not self.cfg.SNS_TOPIC_ARN:
                raise ValueError("SNS_TOPIC_ARN is required when NOTIFICATION_PROVIDER=sns.")
            self.notification_provider = SNSNotificationProvider(
                topic_arn=self.cfg.SNS_TOPIC_ARN,
                region_name=self.cfg.AWS_REGION,
            )
        elif self.cfg.NOTIFICATION_PROVIDER == "localstack_sns":
            from backend.infrastructure.console_notification import SNSNotificationProvider
            self.notification_provider = SNSNotificationProvider(
                endpoint_url=self.cfg.LOCALSTACK_ENDPOINT_URL,
                topic_name=self.cfg.LOCALSTACK_SNS_TOPIC_NAME,
                region_name=self.cfg.AWS_REGION,
                use_localstack_credentials=True,
            )
        else:
            raise ValueError(
                f"Unsupported NOTIFICATION_PROVIDER: {self.cfg.NOTIFICATION_PROVIDER}"
            )

        if self.cfg.AUTHORIZATION_PROVIDER != "cedar":
            raise ValueError(
                f"Unsupported AUTHORIZATION_PROVIDER: {self.cfg.AUTHORIZATION_PROVIDER}"
            )
        from backend.security.cedar_authorizer import CedarAuthorizer
        self.task_authorizer = CedarAuthorizer(self.cfg.CEDAR_POLICY_PATH)


# Global container instance
container = Container()
