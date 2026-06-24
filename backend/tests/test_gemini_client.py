import json

import pytest

from app.services.gemini_client import (
    GeminiClient,
    GeminiConfigurationError,
    GeminiResponseError,
)


def test_gemini_client_requires_api_key():
    with pytest.raises(GeminiConfigurationError):
        GeminiClient(api_key="")


def test_parse_match_result_from_json():
    client = GeminiClient(api_key="test-key", generate_fn=lambda _: "")
    raw = json.dumps(
        {
            "is_match": True,
            "confidence": 0.92,
            "normalized_title": "Nike Air Max 90",
            "reasoning": "Same model",
        }
    )
    result = client._parse_match_result(raw)
    assert result.is_match is True
    assert result.confidence == 0.92
    assert result.normalized_title == "Nike Air Max 90"


def test_parse_match_result_from_markdown_block():
    client = GeminiClient(api_key="test-key", generate_fn=lambda _: "")
    raw = """```json
{"is_match": false, "confidence": 0.2, "normalized_title": "", "reasoning": "Different"}
```"""
    result = client._parse_match_result(raw)
    assert result.is_match is False


def test_match_listings_uses_injected_generate_fn():
    def fake_generate(_: str) -> str:
        return json.dumps(
            {
                "is_match": True,
                "confidence": 0.85,
                "normalized_title": "Adidas Samba",
                "reasoning": "Match",
            }
        )

    client = GeminiClient(api_key="test-key", generate_fn=fake_generate)
    result = client.match_listings("Adidas Samba OG", "good", ["Adidas Samba OG 42"])
    assert result.is_match is True
    assert result.confidence == 0.85


def test_call_model_retries_and_raises():
    attempts = {"count": 0}

    def failing_generate(_: str) -> str:
        attempts["count"] += 1
        raise TimeoutError("timeout")

    client = GeminiClient(api_key="test-key", generate_fn=failing_generate, max_retries=2)
    with pytest.raises(GeminiResponseError):
        client._call_model("prompt")
    assert attempts["count"] == 2
