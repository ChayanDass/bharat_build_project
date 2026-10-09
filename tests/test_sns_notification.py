from backend.infrastructure.console_notification import SNSNotificationProvider


class FakeSNSClient:
    def __init__(self):
        self.published = []

    def create_topic(self, *, Name):
        return {"TopicArn": f"arn:aws:sns:local:000000000000:{Name}"}

    def publish(self, **kwargs):
        self.published.append(kwargs)
        return {"MessageId": "local-message-id"}


def test_localstack_provider_creates_topic_and_publishes_recipient(monkeypatch):
    import backend.infrastructure.console_notification as notifications

    client = FakeSNSClient()
    captured = {}

    def create_client(service_name, **kwargs):
        captured.update(service=service_name, **kwargs)
        return client

    monkeypatch.setattr(notifications.boto3, "client", create_client)

    provider = SNSNotificationProvider(
        endpoint_url="http://localhost:4566",
        topic_name="heatops-test",
        use_localstack_credentials=True,
    )
    assert provider.send_notification("Water Dept", "Dispatch a tanker", "TASK")

    assert captured["service"] == "sns"
    assert captured["endpoint_url"] == "http://localhost:4566"
    assert captured["aws_access_key_id"] == "test"
    assert client.published[0]["MessageAttributes"]["recipient"]["StringValue"] == "Water Dept"
