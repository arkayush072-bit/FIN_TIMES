import json

import respx
import httpx

from backend.config import settings


def _groq_success_payload(summary_text: str = "A short summary.") -> dict:
    body = {
        "summary": summary_text,
        "what_happened": "Something happened.",
        "why_it_matters": "It matters because of X.",
        "key_terms": [{"term": "Inflation", "meaning": "Rising prices over time."}],
        "key_takeaways": ["Takeaway one."],
        "beginner_explanation": "Explained simply.",
    }
    return {"choices": [{"message": {"content": json.dumps(body)}}]}


# ---------------------------------------------------------------------------
# /api/news
# ---------------------------------------------------------------------------

@respx.mock
def test_get_news_returns_articles(client, live_mode):
    respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "ok",
                "totalResults": 1,
                "articles": [
                    {
                        "title": "Rates unchanged",
                        "description": "desc",
                        "content": "content",
                        "url": "https://example.com/rates-unchanged",
                        "urlToImage": None,
                        "source": {"name": "Example News"},
                        "publishedAt": "2026-09-28T10:00:00Z",
                    }
                ],
            },
        )
    )

    resp = client.get("/api/news?category=business")

    assert resp.status_code == 200
    data = resp.json()
    assert data["demo_mode"] is False
    assert len(data["articles"]) == 1
    assert data["articles"][0]["title"] == "Rates unchanged"


@respx.mock
def test_get_news_handles_provider_error_gracefully(client, live_mode):
    respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(500, json={"status": "error"})
    )

    resp = client.get("/api/news?category=business")

    # The route itself still responds 200 — the *provider* failed, the app didn't.
    assert resp.status_code == 200
    data = resp.json()
    assert data["articles"] == []
    assert data["error"] is not None


def test_get_news_without_keys_returns_demo_data(client):
    resp = client.get("/api/news?category=business")

    assert resp.status_code == 200
    data = resp.json()
    assert data["demo_mode"] is True
    assert len(data["articles"]) > 0


@respx.mock
def test_get_news_empty_results_returns_200_with_empty_array(client, live_mode):
    respx.get(f"{settings.news_api_base_url}/top-headlines").mock(
        return_value=httpx.Response(200, json={"status": "ok", "totalResults": 0, "articles": []})
    )

    resp = client.get("/api/news?category=business")

    assert resp.status_code == 200
    assert resp.json()["articles"] == []


# ---------------------------------------------------------------------------
# /api/summarize
# ---------------------------------------------------------------------------

@respx.mock
def test_summarize_returns_structured_json(client, live_mode):
    respx.post(settings.groq_api_url).mock(
        return_value=httpx.Response(200, json=_groq_success_payload())
    )

    resp = client.post(
        "/api/summarize",
        json={
            "title": "Fed holds rates",
            "description": "desc",
            "content": "content",
            "url": "https://example.com/fed-holds-rates-route",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"] == "A short summary."
    assert data["cached"] is False


@respx.mock
def test_summarize_handles_groq_failure_gracefully(client, live_mode):
    respx.post(settings.groq_api_url).mock(return_value=httpx.Response(503, json={"error": "down"}))
    respx.post(settings.groq_api_url).mock(return_value=httpx.Response(503, json={"error": "down"}))

    resp = client.post(
        "/api/summarize",
        json={
            "title": "Test",
            "description": "d",
            "content": "c",
            "url": "https://example.com/failure-case",
        },
    )

    assert resp.status_code == 502
    assert "temporarily unavailable" in resp.json()["detail"].lower()


def test_summarize_invalid_input_returns_422(client, live_mode):
    resp = client.post("/api/summarize", json={"description": "missing title and url"})
    assert resp.status_code == 422


def test_summarize_without_keys_returns_demo_summary(client):
    resp = client.post(
        "/api/summarize",
        json={
            "title": "Test",
            "description": "d",
            "content": "c",
            "url": "https://example.com/demo-case",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["demo_mode"] is True


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

def test_get_categories(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    assert "Markets" in resp.json()["categories"]


def test_index_serves_frontend(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "FinNews AI" in resp.text
