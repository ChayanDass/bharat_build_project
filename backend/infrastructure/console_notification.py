import logging
import json
from typing import Optional
import boto3
from backend.domain.interfaces import NotificationProvider

logger = logging.getLogger("HeatOps.Notification")


class ConsoleNotificationProvider(NotificationProvider):
    """Console/UI simulation notification provider for local development."""

    def __init__(self):
        self.sent_notifications = []

    def send_notification(self, recipient: str, message: str, topic: Optional[str] = None) -> bool:
        record = {
            "recipient": recipient,
            "message": message,
            "topic": topic or "HEAT_OPS_ALERT"
        }
        self.sent_notifications.append(record)
        logger.info(f"📢 [CONSOLE NOTIFICATION] To: {recipient} | Topic: {topic} | Message: {message}")
        print(f"📢 [HEAT OPS ALERT] To: {recipient} -> {message}")
        return True


class SNSNotificationProvider(NotificationProvider):
    """Publish task notifications through AWS SNS or an SNS-compatible endpoint."""

    def __init__(
        self,
        topic_arn: Optional[str] = None,
        region_name: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        topic_name: Optional[str] = None,
        use_localstack_credentials: bool = False,
    ):
        client_options = {"region_name": region_name}
        if endpoint_url:
            client_options["endpoint_url"] = endpoint_url
        if use_localstack_credentials:
            client_options.update(
                aws_access_key_id="test",
                aws_secret_access_key="test",
            )
        self.client = boto3.client("sns", **client_options)
        if topic_arn:
            self.topic_arn = topic_arn
        elif topic_name:
            self.topic_arn = self.client.create_topic(Name=topic_name)["TopicArn"]
        else:
            raise ValueError("Provide either topic_arn or topic_name for SNS notifications.")

    def send_notification(self, recipient: str, message: str, topic: Optional[str] = None) -> bool:
        self.client.publish(
            TopicArn=self.topic_arn,
            Subject=(topic or "HEAT_OPS_ALERT")[:100],
            Message=json.dumps({"recipient": recipient, "topic": topic, "message": message}),
            MessageAttributes={
                "recipient": {"DataType": "String", "StringValue": recipient},
                "topic": {
                    "DataType": "String",
                    "StringValue": topic or "HEAT_OPS_ALERT",
                },
            },
        )
        logger.info("Published HeatOps notification to SNS recipient=%s topic=%s", recipient, topic)
        return True
