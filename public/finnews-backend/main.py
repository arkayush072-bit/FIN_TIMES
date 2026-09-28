from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import news, ai
from models import HealthResponse

settings = get_settings()

app = FastAPI(
    title="FinNews AI API",
    description=(
        "AI-powered financial news simplification backend "
        "(NewsAPI + Groq LLaMA 3.3 70B)."
    ),
    version="1.0.0",
)

# CORS — must match the origin your frontend is served from
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(news.router)
app.include_router(ai.router)


@app.get("/", tags=["root"])
async def root():
    return {
        "name": "FinNews AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health():
    """
    Health check used by the frontend to display Live/Demo/Offline mode.
    """
    return HealthResponse(
        status="ok",
        news_api=bool(settings.NEWS_API_KEY),
        groq_api=bool(settings.GROQ_API_KEY),
    )
