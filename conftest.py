"""
Shared fixtures.

All external APIs are mocked (via `respx`, which patches httpx at the
transport level) — no real network calls happen and no real API keys are
required to run this suite.
"""

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.services.cache_service import cache


@pytest.fixture(autouse=True)
def _reset_cache():
    """Every test starts with an empty summary cache."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def live_mode(monkeypatch):
    """Point the app's singleton services at fake-but-present API keys, so
    routes take the "real API" code path instead of falling back to Demo
    Mode. Combine with respx mocks for the actual HTTP calls."""
    monkeypatch.setattr(main.news_service, "_api_key", "test-news-key")
    monkeypatch.setattr(main.ai_service, "_api_key", "test-groq-key")
    yield
