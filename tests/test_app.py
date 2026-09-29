"""Regression coverage for startup and both demo/provider paths."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from backend import main
from backend.config import Settings
from backend.services import ai_service, news_service


class AppTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(_env_file=None, NEWS_API_KEY="", GROQ_API_KEY="")
        for module in (main, news_service, ai_service):
            patcher = patch.object(module, "settings", self.settings)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)

    def mock_news(self, handler):
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        patcher = patch.object(news_service.httpx, "AsyncClient", return_value=client)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        self.settings.NEWS_API_KEY = "synthetic-news-key"
        return mock

    def test_dashboard_static_asset_and_health(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("text/html", page.headers["content-type"])
        self.assertIn("FinNews AI", page.text)
        self.assertEqual(page.headers["cache-control"], "no-cache")
        for asset in ("style.css", "app.js"):
            path = f"/static/{asset}?v=classic-2"
            self.assertIn(path, page.text)
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/health").json(), self.client.get("/api/health").json())
        self.assertEqual(self.client.get("/static/news-placeholder.svg").status_code, 200)
        for path in ("/.env", "/backend/config.py", "/static/finnews-backend/config.py", "/finnews-backend/config.py"):
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get("/api/health").json(), {
            "status": "ok", "news_api": False, "groq_api": False,
        })

    def test_demo_news_and_page_size(self):
        response = self.client.get("/api/news")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "demo")
        self.assertEqual(data["totalResults"], 3)
        self.assertTrue(all(a["title"].startswith("Demo:") for a in data["articles"]))
        limited = self.client.get("/api/news?q=technology&page_size=1").json()
        self.assertEqual(limited["totalResults"], 1)

    def test_news_query_validation(self):
        for query in ("q=", "page_size=0", "page_size=51"):
            self.assertEqual(self.client.get(f"/api/news?{query}").status_code, 422)

    def test_demo_summary(self):
        article = self.client.get("/api/news").json()["articles"][0]
        response = self.client.post("/api/summarize", json=article)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "demo")
        self.assertEqual(response.json()["summary"], article["description"])
        self.assertTrue(response.json()["key_terms"])

    def test_empty_summary_is_rejected(self):
        self.assertEqual(self.client.post("/api/summarize", json={}).status_code, 400)

    def test_live_news_request_and_null_fields(self):
        def handler(request):
            self.assertEqual(request.url.params["q"], "stock market")
            self.assertEqual(request.url.params["pageSize"], "2")
            self.assertEqual(request.headers["X-Api-Key"], "synthetic-news-key")
            self.assertNotIn("apiKey", request.url.params)
            return httpx.Response(200, json={"status": "ok", "articles": [
                {"title": "[Removed]"},
                {"title": "Synthetic headline", "description": None, "source": None},
            ]})
        self.mock_news(handler)
        response = self.client.get("/api/news?q=stock%20market&page_size=2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "live")
        self.assertEqual(data["totalResults"], 1)
        self.assertEqual(data["articles"][0]["description"], "")
        self.assertEqual(data["articles"][0]["source"], {"name": "Unknown"})

    def test_news_provider_error_does_not_leak_key(self):
        self.mock_news(lambda request: httpx.Response(401, json={"status": "error"}))
        response = self.client.get("/api/news")
        self.assertEqual(response.status_code, 502)
        self.assertIn("401", response.json()["detail"])
        self.assertNotIn(self.settings.NEWS_API_KEY, response.text)

    def test_news_timeout(self):
        def handler(request):
            raise httpx.ReadTimeout("timeout", request=request)
        self.mock_news(handler)
        response = self.client.get("/api/news")
        self.assertEqual(response.status_code, 502)
        self.assertIn("could not be reached", response.json()["detail"])

    def test_news_invalid_payload(self):
        self.mock_news(lambda request: httpx.Response(200, json={"status": "ok", "articles": None}))
        self.assertEqual(self.client.get("/api/news").status_code, 502)

    def test_live_summary_and_client_cleanup(self):
        self.settings.GROQ_API_KEY = "synthetic-groq-key"
        client = AsyncMock()
        client.chat.completions.create.return_value = SimpleNamespace(choices=[
            SimpleNamespace(message=SimpleNamespace(content='```json\n{"summary":"Synthetic summary"}\n```'))
        ])
        with patch.object(ai_service, "AsyncGroq") as factory:
            factory.return_value.__aenter__.return_value = client
            response = self.client.post("/api/summarize", json={"title": "Synthetic headline"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["mode"], "live")
            self.assertEqual(response.json()["summary"], "Synthetic summary")
            factory.return_value.__aexit__.assert_awaited_once()

    def test_groq_provider_error(self):
        self.settings.GROQ_API_KEY = "synthetic-groq-key"
        client = AsyncMock()
        client.chat.completions.create.side_effect = RuntimeError("Provider unavailable")
        with patch.object(ai_service, "AsyncGroq") as factory:
            factory.return_value.__aenter__.return_value = client
            self.assertEqual(self.client.post("/api/summarize", json={"title": "Test"}).status_code, 502)


if __name__ == "__main__":
    unittest.main()
