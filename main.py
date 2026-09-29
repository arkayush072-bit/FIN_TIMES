"""
FinNews AI — FastAPI application.

Serves the JSON API under /api/*, a /health check, and the static
vanilla-JS frontend from frontend/ at "/". Run with:

    uvicorn backend.main:app --reload

See README.md for full setup and deployment instructions.
"""

import logging
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .models import (
    BatchSummarizeRequest,
    BatchSummarizeResponse,
    CategoriesResponse,
    HealthResponse,
    NewsResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from .services.ai_service import ai_service, AIServiceError, RateLimitedError
from .services.news_service import news_service

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("finnews")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="FinNews AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Middleware: request logging + max body size
# ---------------------------------------------------------------------------

@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_request_body_bytes:
        return JSONResponse(
            status_code=413,
            content={"error": "Request body too large."},
        )
    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ---------------------------------------------------------------------------
# Very small fixed-window rate limiter for /api/summarize*, per client IP.
# Sufficient for a single-process demo app; swap for a shared store
# (e.g. Redis) behind a real load balancer.
# ---------------------------------------------------------------------------

_rate_limit_hits: dict[str, deque] = defaultdict(deque)


def _check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    window = 60.0
    hits = _rate_limit_hits[client_ip]
    while hits and now - hits[0] > window:
        hits.popleft()
    if len(hits) >= settings.summarize_rate_limit_per_minute:
        return False
    hits.append(now)
    return True


# ---------------------------------------------------------------------------
# Routes — health & meta
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        service="FinNews AI",
        news_api_configured=settings.news_configured,
        groq_api_configured=settings.groq_configured,
        demo_mode=settings.demo_mode,
    )


@app.get("/api/categories", response_model=CategoriesResponse)
async def get_categories():
    return CategoriesResponse(categories=news_service.categories())


# ---------------------------------------------------------------------------
# Routes — news
# ---------------------------------------------------------------------------

@app.get("/api/news", response_model=NewsResponse)
async def get_news(
    category: str = Query("business"),
    page: int = Query(1, ge=1, le=100),
    page_size: int = Query(10, ge=1, le=50),
):
    result = await news_service.get_news(category=category, page=page, page_size=page_size)
    return NewsResponse(
        articles=result["articles"],
        total_results=result["total_results"],
        demo_mode=result["demo_mode"],
        error=result.get("error"),
    )


@app.get("/api/search", response_model=NewsResponse)
async def search_news(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1, le=100),
    page_size: int = Query(10, ge=1, le=50),
):
    result = await news_service.search(query=q, page=page, page_size=page_size)
    return NewsResponse(
        articles=result["articles"],
        total_results=result["total_results"],
        demo_mode=result["demo_mode"],
        error=result.get("error"),
    )


# ---------------------------------------------------------------------------
# Routes — summarize
# ---------------------------------------------------------------------------

@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize(payload: SummarizeRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many summarize requests. Please slow down.")

    try:
        result = await ai_service.summarize(
            title=payload.title,
            description=payload.description or "",
            content=payload.content or "",
            url=payload.url,
        )
    except RateLimitedError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return SummarizeResponse(**result)


@app.post("/api/summarize/batch", response_model=BatchSummarizeResponse)
async def summarize_batch(payload: BatchSummarizeRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many summarize requests. Please slow down.")

    if len(payload.articles) > settings.max_batch_summarize:
        raise HTTPException(
            status_code=400,
            detail=f"Batch summarize is limited to {settings.max_batch_summarize} articles.",
        )

    results = []
    for article in payload.articles:
        try:
            result = await ai_service.summarize(
                title=article.title,
                description=article.description or "",
                content=article.content or "",
                url=article.url,
            )
            results.append(SummarizeResponse(**result))
        except (AIServiceError, RateLimitedError) as exc:
            # Don't fail the whole batch for one bad article — surface a
            # friendly placeholder for that entry instead.
            results.append(
                SummarizeResponse(
                    summary=str(exc),
                    what_happened="Not available in the source.",
                    why_it_matters="Not available in the source.",
                    key_terms=[],
                    key_takeaways=[],
                    beginner_explanation="Not available in the source.",
                    cached=False,
                    demo_mode=settings.demo_mode,
                )
            )

    return BatchSummarizeResponse(results=results)


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(str(index_path))
