import re
import time
from typing import Any, Dict, List, Optional

from backend.domain.interfaces import ModelProvider


class StrandsModelProvider(ModelProvider):
    """Run bounded HeatOps planning through Strands with Gemini or Bedrock."""

    def __init__(
        self,
        provider: str,
        model_id: str,
        gemini_api_key: Optional[str],
        gemini_model: str,
        region_name: str,
        gemini_retry_attempts: int = 3,
        gemini_retry_delay_seconds: float = 1.0,
    ):
        self.provider = provider
        self.model_id = model_id
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        self.region_name = region_name
        self.gemini_retry_attempts = max(1, gemini_retry_attempts)
        self.gemini_retry_delay_seconds = max(0.0, gemini_retry_delay_seconds)

    @staticmethod
    def _is_transient_gemini_error(error: Exception) -> bool:
        status = getattr(error, "status", None)
        status_code = getattr(status, "code", status)
        if isinstance(status_code, int) and (
            status_code == 429 or 500 <= status_code <= 599
        ):
            return True

        message = str(error)
        return bool(
            re.search(r"\b(429|500|502|503|504)\b", message)
            or any(
                marker in message.upper()
                for marker in (
                    "RESOURCE_EXHAUSTED",
                    "UNAVAILABLE",
                    "INTERNAL",
                    "DEADLINE_EXCEEDED",
                )
            )
        )

    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        try:
            from strands import Agent
            if self.provider == "bedrock":
                import boto3
                from strands.models import BedrockModel

                model = BedrockModel(
                    model_id=self.model_id,
                    boto_session=boto3.Session(region_name=self.region_name),
                )
            elif self.provider == "gemini":
                if not self.gemini_api_key:
                    raise RuntimeError(
                        "GEMINI_API_KEY is required when LLM_PROVIDER=gemini "
                        "and AGENT_RUNTIME=strands."
                    )
                from strands.models.gemini import GeminiModel

                model = GeminiModel(
                    client_args={"api_key": self.gemini_api_key},
                    model_id=self.gemini_model,
                    params={"temperature": 0.2},
                )
            else:
                raise ValueError(
                    f"Strands does not have a configured model for provider '{self.provider}'."
                )
        except ImportError as exc:
            raise RuntimeError(
                "AGENT_RUNTIME=strands requires the strands-agents dependency "
                "and its selected model-provider extra."
            ) from exc

        for attempt in range(self.gemini_retry_attempts if self.provider == "gemini" else 1):
            try:
                agent = Agent(
                    model=model,
                    system_prompt=system_prompt,
                    tools=tools or [],
                )
                result = agent(prompt)
                return {"text": str(result), "tool_calls": []}
            except Exception as exc:
                if (
                    self.provider != "gemini"
                    or not self._is_transient_gemini_error(exc)
                    or attempt + 1 >= self.gemini_retry_attempts
                ):
                    return {
                        "text": "",
                        "tool_calls": [],
                        "error": f"Strands {self.provider} invocation failed: {exc}",
                    }
                time.sleep(self.gemini_retry_delay_seconds * (2 ** attempt))

        return {
            "text": "",
            "tool_calls": [],
            "error": f"Strands {self.provider} invocation failed after retries.",
        }
