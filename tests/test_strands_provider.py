import sys
import types

from backend.infrastructure.strands_provider import StrandsModelProvider


def _install_fake_strands(monkeypatch, responses):
    attempts = []

    class FakeAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __call__(self, prompt):
            attempts.append(prompt)
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

    strands = types.ModuleType("strands")
    strands.Agent = FakeAgent
    models = types.ModuleType("strands.models")
    gemini = types.ModuleType("strands.models.gemini")
    gemini.GeminiModel = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "strands", strands)
    monkeypatch.setitem(sys.modules, "strands.models", models)
    monkeypatch.setitem(sys.modules, "strands.models.gemini", gemini)
    return attempts


def test_gemini_retries_transient_service_errors(monkeypatch):
    attempts = _install_fake_strands(
        monkeypatch,
        [RuntimeError("503 UNAVAILABLE"), "valid planner response"],
    )
    delays = []
    monkeypatch.setattr(
        "backend.infrastructure.strands_provider.time.sleep",
        delays.append,
    )
    provider = StrandsModelProvider(
        provider="gemini",
        model_id="unused-for-gemini",
        gemini_api_key="test-key",
        gemini_model="gemini-flash-latest",
        region_name="us-east-1",
        gemini_retry_attempts=3,
        gemini_retry_delay_seconds=0.25,
    )

    result = provider.invoke("plan", system_prompt="select known SOP ids only")

    assert result["text"] == "valid planner response"
    assert "error" not in result
    assert len(attempts) == 2
    assert delays == [0.25]


def test_gemini_returns_explicit_error_after_retry_limit(monkeypatch):
    attempts = _install_fake_strands(
        monkeypatch,
        [RuntimeError("503 UNAVAILABLE")] * 3,
    )
    delays = []
    monkeypatch.setattr(
        "backend.infrastructure.strands_provider.time.sleep",
        delays.append,
    )
    provider = StrandsModelProvider(
        provider="gemini",
        model_id="unused-for-gemini",
        gemini_api_key="test-key",
        gemini_model="gemini-flash-latest",
        region_name="us-east-1",
        gemini_retry_attempts=3,
        gemini_retry_delay_seconds=0.5,
    )

    result = provider.invoke("plan")

    assert result["text"] == ""
    assert "503 UNAVAILABLE" in result["error"]
    assert len(attempts) == 3
    assert delays == [0.5, 1.0]


def test_gemini_does_not_retry_non_transient_errors(monkeypatch):
    attempts = _install_fake_strands(
        monkeypatch,
        [RuntimeError("invalid API key")],
    )
    delays = []
    monkeypatch.setattr(
        "backend.infrastructure.strands_provider.time.sleep",
        delays.append,
    )
    provider = StrandsModelProvider(
        provider="gemini",
        model_id="unused-for-gemini",
        gemini_api_key="test-key",
        gemini_model="gemini-flash-latest",
        region_name="us-east-1",
        gemini_retry_attempts=3,
        gemini_retry_delay_seconds=0.5,
    )

    result = provider.invoke("plan")

    assert "invalid API key" in result["error"]
    assert len(attempts) == 1
    assert delays == []
