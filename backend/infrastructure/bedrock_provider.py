import os
import json
from typing import List, Optional, Dict, Any
from backend.domain.interfaces import ModelProvider

try:
    import boto3
except ImportError:
    boto3 = None


class BedrockModelProvider(ModelProvider):
    """
    Amazon Bedrock ModelProvider implementation for Production environment.
    Uses AWS IAM credentials / boto3 bedrock runtime.
    """

    def __init__(self, model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0", region_name: str = "us-east-1"):
        self.model_id = model_id
        self.region_name = region_name
        self.client = None
        if boto3:
            self.client = boto3.client("bedrock-runtime", region_name=region_name)

    def invoke(self, prompt: str, system_prompt: Optional[str] = None, tools: Optional[List[Any]] = None) -> Dict[str, Any]:
        if not self.client:
            return {
                "text": f"[Bedrock Client Not Configured] Response for: {prompt}",
                "tool_calls": []
            }

        messages = [{"role": "user", "content": prompt}]
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "temperature": 0.2,
            "messages": messages,
        }
        if system_prompt:
            body["system"] = system_prompt

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            response_body = json.loads(response.get("body").read())
            text_content = ""
            for item in response_body.get("content", []):
                if item.get("type") == "text":
                    text_content += item.get("text", "")

            return {
                "text": text_content,
                "tool_calls": [],
                "raw_response": response_body
            }
        except Exception as e:
            return {
                "text": f"Bedrock API Error: {str(e)}",
                "tool_calls": [],
                "error": str(e)
            }
