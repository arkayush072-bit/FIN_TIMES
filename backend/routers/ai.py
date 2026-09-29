from fastapi import APIRouter, HTTPException
from backend.models import ArticleRequest, SummaryResponse, Article
from backend.services.ai_service import summarize_article

router = APIRouter(prefix="/api", tags=["ai"])


@router.post("/summarize", response_model=SummaryResponse)
async def summarize(payload: ArticleRequest):
    """
    Simplify a financial news article using Groq (LLaMA 3.3 70B).

    - If GROQ_API_KEY is missing -> returns a demo summary (never errors).
    - If Groq returns an error -> 502 with details.
    """
    article = Article(
        title=payload.title or "",
        description=payload.description or "",
        content=payload.content or "",
        url=payload.url or "",
        source={"name": "Unknown"},
    )

    if not (article.title or article.description or article.content):
        raise HTTPException(
            status_code=400,
            detail="Article has no content to summarize.",
        )

    try:
        return await summarize_article(article)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
