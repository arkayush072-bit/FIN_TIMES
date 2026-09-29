import pytest
import respx
import httpx

from backend.services.news_service import NewsService
from backend.config import settings


def _service_with_key(key: str = "test-news-key") -> NewsService:
    svc = NewsService()
    svc._api_key = key
    return svc


@pytest.mark.asyncio
async def test_demo_mode_when_no_key_configured():
    svc = _service_with_key(key="")
    result = await svc.get_news(category="business")

    assert result["demo_mode"] is True
    assert result["error"] is None
    assert len(result["articles"]) > 0


@pytest.mark.asyncio
@respx.mock
async def test_get_news_success():
    svc = _service_with_key()
    route = respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "ok",
                "totalResults": 1,
                "articles": [
                    {
                        "title": "Markets rise on earnings",
                        "description": "A short description.",
                        "content": "Full content here.",
                        "url": "https://example.com/article-1",
                        "urlToImage": "https://example.com/image.jpg",
                        "source": {"name": "Example News"},
                        "publishedAt": "2026-09-28T10:00:00Z",
                    }
                ],
            },
        )
    )

    result = await svc.get_news(category="business")

    assert route.called
    assert result["demo_mode"] is False
    assert result["error"] is None
    assert len(result["articles"]) == 1
    assert result["articles"][0]["title"] == "Markets rise on earnings"
    assert result["articles"][0]["source"] == "Example News"


@pytest.mark.asyncio
@respx.mock
async def test_get_news_handles_provider_error_gracefully():
    svc = _service_with_key()
    respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(500, json={"status": "error", "message": "boom"})
    )

    result = await svc.get_news(category="business")

    assert result["articles"] == []
    assert result["error"] is not None
    assert "stack" not in result["error"].lower()


@pytest.mark.asyncio
@respx.mock
async def test_get_news_handles_rate_limit():
    svc = _service_with_key()
    respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(429, json={"status": "error"})
    )

    result = await svc.get_news(category="business")

    assert result["articles"] == []
    assert "try again" in result["error"].lower()


@pytest.mark.asyncio
@respx.mock
async def test_get_news_empty_results_returns_empty_array_not_error():
    svc = _service_with_key()
    respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(200, json={"status": "ok", "totalResults": 0, "articles": []})
    )

    result = await svc.get_news(category="business")

    assert result["error"] is None
    assert result["articles"] == []


@pytest.mark.asyncio
@respx.mock
async def test_get_news_dedupes_by_url():
    svc = _service_with_key()
    duplicate_article = {
        "title": "Same story twice",
        "description": "desc",
        "content": "content",
        "url": "https://example.com/dupe",
        "urlToImage": None,
        "source": {"name": "Example News"},
        "publishedAt": "2026-09-28T10:00:00Z",
    }
    respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(
            200,
            json={"status": "ok", "totalResults": 2, "articles": [duplicate_article, duplicate_article]},
        )
    )

    result = await svc.get_news(category="business")

    assert len(result["articles"]) == 1


@pytest.mark.asyncio
@respx.mock
async def test_india_category_uses_country_filter():
    svc = _service_with_key()
    route = respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(200, json={"status": "ok", "totalResults": 0, "articles": []})
    )

    await svc.get_news(category="india")

    assert route.called
    sent_request = route.calls.last.request
    assert "country=in" in str(sent_request.url)
