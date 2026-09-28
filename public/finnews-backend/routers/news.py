from fastapi import APIRouter, HTTPException, Query
from models import NewsResponse
from services.news_service import fetch_news

router = APIRouter(prefix="/api", tags=["news"])


@router.get("/news", response_model=NewsResponse)
async def get_news(
    q: str = Query("finance", min_length=1, max_length=200),
    page_size: int = Query(12, ge=1, le=50),
):
    """
    Fetch financial news articles for a given query.

    - If NEWS_API_KEY is missing -> returns 3 demo articles with mode="demo".
    - If NewsAPI is unreachable / errors -> 502 with a clear message.
    """
    try:
        articles, mode = await fetch_news(q, page_size)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    return NewsResponse(
        status="ok",
        totalResults=len(articles),
        articles=articles,
        mode=mode,
    )
