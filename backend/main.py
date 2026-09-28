from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.config import get_settings
from backend.routers import news, ai
from backend.models import HealthResponse

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
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(news.router)
app.include_router(ai.router)

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
app.mount("/static", StaticFiles(directory=PUBLIC_DIR / "static"), name="static")


@app.get("/", tags=["root"])
async def root():
    return FileResponse(PUBLIC_DIR / "index.html")


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
