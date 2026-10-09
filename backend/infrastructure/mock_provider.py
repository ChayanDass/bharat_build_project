from typing import List, Optional, Dict, Any
from backend.domain.interfaces import ModelProvider


class MockModelProvider(ModelProvider):
    """
    Mock ModelProvider for deterministic automated testing.
    """

    def __init__(self, preset_response: Optional[str] = None):
        self.preset_response = preset_response

    def invoke(self, prompt: str, system_prompt: Optional[str] = None, tools: Optional[List[Any]] = None) -> Dict[str, Any]:
        if self.preset_response:
            return {"text": self.preset_response, "tool_calls": []}

        if "Ward 12" in prompt or "critical" in prompt.lower():
            return {
                "text": "Ward 12 is classified as critical because the heat index is 52°C, the ward has a high concentration of outdoor workers (1,200) and vulnerable residents (3,400 elderly, 5,100 children), and current water resources are insufficient.",
                "tool_calls": []
            }

        return {
            "text": f"Mock analysis completed for query: {prompt}",
            "tool_calls": []
        }
