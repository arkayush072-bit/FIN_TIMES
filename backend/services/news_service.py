"""Retrieve NewsAPI articles, with a credential-free demo for local use."""

import httpx

from backend.config import get_settings
from backend.models import Article

settings = get_settings()

DEMO_ARTICLES = [
    Article(
        title="Demo: Understanding interest rates",
        description=(
            "This fictional example explores how a change in borrowing costs "
            "can affect household budgets and business investment."
        ),
        source={"name": "FinNews demo"},
    ),
    Article(
        title="Demo: Reading a company's earnings report",
        description=(
            "In this fictional example, a company reports higher revenue but "
            "lower profit because its operating costs increased."
        ),
        source={"name": "FinNews demo"},
    ),
    Article(
        title="Demo: What inflation means for a budget",
        description=(
            "This fictional example shows how rising prices reduce the amount "
            "of goods and services a household can buy with the same income."
        ),
        source={"name": "FinNews demo"},
    ),
]


async def fetch_news(query: str, page_size: int) -> tuple[list[Article], str]:
    if not settings.NEWS_API_KEY:
        return DEMO_ARTICLES[:page_size], "demo"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                settings.NEWS_API_URL,
                params={
                    "q": query,
                    "pageSize": page_size,
                    "language": "en",
                    "sortBy": "publishedAt",
                },
                headers={"X-Api-Key": settings.NEWS_API_KEY},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"NewsAPI returned HTTP {exc.response.status_code}. "
            "Check the server API key and provider quota."
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError("NewsAPI could not be reached. Please try again later.") from exc
    except ValueError as exc:
        raise RuntimeError("NewsAPI returned an invalid response.") from exc

    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise RuntimeError("NewsAPI could not complete the request.")
    items = payload.get("articles")
    if not isinstance(items, list):
        raise RuntimeError("NewsAPI returned an invalid article list.")

    articles = []
    for item in items:
        if not isinstance(item, dict) or not item.get("title") or item["title"] == "[Removed]":
            continue
        articles.append(Article(
            title=item["title"],
            description=item.get("description") or "",
            content=item.get("content") or "",
            url=item.get("url") or "",
            urlToImage=item.get("urlToImage") or "",
            publishedAt=item.get("publishedAt") or "",
            source=item.get("source") or {"name": "Unknown"},
        ))
    return articles[:page_size], "live"
