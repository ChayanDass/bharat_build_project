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
    ):
        self.provider = provider
        self.model_id = model_id
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        self.region_name = region_name

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

        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=tools or [],
        )
        try:
            result = agent(prompt)
        except Exception as exc:
            return {
                "text": "",
                "tool_calls": [],
                "error": f"Strands {self.provider} invocation failed: {exc}",
            }
        return {"text": str(result), "tool_calls": []}
