import json

import pytest
import respx
import httpx

from backend.services.ai_service import AIService, AIServiceError
from backend.services.cache_service import cache, make_summary_cache_key
from backend.config import settings


def _service_with_key(key: str = "test-groq-key") -> AIService:
    svc = AIService()
    svc._api_key = key
    return svc


def _groq_success_payload(summary_text: str = "A short summary.") -> dict:
    body = {
        "summary": summary_text,
        "what_happened": "Something happened.",
        "why_it_matters": "It matters because of X.",
        "key_terms": [{"term": "Inflation", "meaning": "Rising prices over time."}],
        "key_takeaways": ["Takeaway one.", "Takeaway two."],
        "beginner_explanation": "In simple terms, this is what occurred.",
    }
    return {"choices": [{"message": {"content": json.dumps(body)}}]}


@pytest.mark.asyncio
async def test_demo_mode_when_no_key_configured():
    svc = _service_with_key(key="")
    result = await svc.summarize(
        title="Test", description="desc", content="content", url="https://example.com/a"
    )

    assert result["demo_mode"] is True
    assert result["cached"] is False
    assert "summary" in result


@pytest.mark.asyncio
@respx.mock
async def test_summarize_returns_structured_json():
    svc = _service_with_key()
    respx.post(settings.groq_api_url).mock(
        return_value=httpx.Response(200, json=_groq_success_payload())
    )

    result = await svc.summarize(
        title="Fed holds rates",
        description="desc",
        content="content",
        url="https://example.com/fed-holds-rates",
    )

    assert result["summary"] == "A short summary."
    assert result["key_terms"][0]["term"] == "Inflation"
    assert result["cached"] is False
    assert result["demo_mode"] is False


@pytest.mark.asyncio
@respx.mock
async def test_summarize_handles_groq_failure_gracefully():
    svc = _service_with_key()
    respx.post(settings.groq_api_url).mock(return_value=httpx.Response(503, json={"error": "down"}))
    respx.post(settings.groq_api_url).mock(return_value=httpx.Response(503, json={"error": "down"}))

    with pytest.raises(AIServiceError):
        await svc.summarize(
            title="Test", description="desc", content="content", url="https://example.com/b"
        )


@pytest.mark.asyncio
@respx.mock
async def test_cache_hit_returns_same_result_without_calling_groq_again():
    svc = _service_with_key()
    route = respx.post(settings.groq_api_url).mock(
        return_value=httpx.Response(200, json=_groq_success_payload("Cached-worthy summary."))
    )

    url = "https://example.com/cache-me"
    first = await svc.summarize(title="T", description="d", content="c", url=url)
    second = await svc.summarize(title="T", description="d", content="c", url=url)

    assert route.call_count == 1  # Groq was only called once
    assert first["summary"] == second["summary"] == "Cached-worthy summary."
    assert first["cached"] is False
    assert second["cached"] is True

    # And the cache key itself is the documented hash(url + "summary") shape
    assert cache.get(make_summary_cache_key(url)) is not None
