import os
import json
import logging
from typing import List, Optional, Dict, Any
from backend.domain.interfaces import ModelProvider

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

logger = logging.getLogger("HeatOps.Gemini")


class GeminiModelProvider(ModelProvider):
    """
    Hosted Google Gemini API ModelProvider implementation.
    Reads GEMINI_API_KEY from environment variables.
    Never exposes or hardcodes API key.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        self.client = None
        if genai and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")

    def invoke(self, prompt: str, system_prompt: Optional[str] = None, tools: Optional[List[Any]] = None) -> Dict[str, Any]:
        if not self.client:
            return {
                "text": "",
                "tool_calls": [],
                "error": "Gemini client is not initialized. Check GEMINI_API_KEY and google-genai installation."
            }

        config = types.GenerateContentConfig(
            system_instruction=system_prompt if system_prompt else None,
            temperature=0.2,
        )

        # Try configured model first, then currently available Flash aliases.
        models_to_try = [
            self.model_name,
            "gemini-flash-latest",
            "gemini-3-flash-preview",
            "gemini-flash-lite-latest",
        ]

        for m_name in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=m_name,
                    contents=prompt,
                    config=config,
                )

                tool_calls = []
                if hasattr(response, "function_calls") and response.function_calls:
                    for fc in response.function_calls:
                        tool_calls.append({
                            "name": fc.name,
                            "args": fc.args
                        })

                if response.text and not response.text.startswith("Gemini API Error"):
                    return {
                        "text": response.text,
                        "tool_calls": tool_calls,
                        "raw_response": response
                    }
            except Exception as e:
                logger.warning(f"Gemini call failed with model {m_name}: {e}")

        return {
            "text": "",
            "tool_calls": [],
            "error": "All configured Gemini model calls failed."
        }
