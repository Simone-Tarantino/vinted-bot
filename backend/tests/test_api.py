import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.gemini_client import GeminiClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.api import searches as searches_module

    searches_module._session_factory = None

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_health_requires_gemini_key(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["gemini_configured"] is True
    assert payload["status"] == "ok"


def test_health_degraded_without_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("DISABLE_SCHEDULER", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.api import searches as searches_module

    searches_module._session_factory = None
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"
    get_settings.cache_clear()


def test_create_and_list_search(client):
    create_response = client.post(
        "/searches",
        json={
            "query": "nike air max 90",
            "brand": "Nike",
            "max_price": 80,
            "discount_threshold_percent": 25,
        },
    )
    assert create_response.status_code == 201
    search_id = create_response.json()["id"]

    list_response = client.get("/searches")
    assert list_response.status_code == 200
    assert any(item["id"] == search_id for item in list_response.json())


def test_ai_matcher_integration():
    def fake_generate(_: str) -> str:
        return json.dumps(
            {
                "is_match": True,
                "confidence": 0.9,
                "normalized_title": "Nike Air Max 90",
                "reasoning": "same",
            }
        )

    from app.services.ai_matcher import AIMatcher

    gemini = GeminiClient(api_key="test", generate_fn=fake_generate)
    matcher = AIMatcher(gemini_client=gemini)
    valid, discount, confidence, _ = matcher.evaluate(
        vinted_title="Nike Air Max 90",
        vinted_price=40,
        vinted_condition="good",
        benchmark_price=100,
        discount_threshold_percent=20,
        reference_titles=["Nike Air Max 90 white"],
    )
    assert valid is True
    assert discount == 60.0
    assert confidence == 0.9
