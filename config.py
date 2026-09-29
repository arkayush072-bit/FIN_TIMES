"""
Configuration and environment loading for FinNews AI.

All secrets are read from environment variables (populated from a local
.env file via python-dotenv). Nothing here is ever sent to the frontend.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load variables from a .env file if one exists (local development).
# In production, real environment variables set by the host take priority.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # --- API keys (never logged, never exposed to the frontend) ---
    news_api_key: str = field(default_factory=lambda: os.getenv("NEWS_API_KEY", "").strip())
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", "").strip())

    # --- External APIs ---
    news_api_base_url: str = "https://newsapi.org/v2"
    groq_api_url: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Timeouts (seconds) ---
    news_api_timeout: float = 10.0
    groq_api_timeout: float = 30.0

    # --- Server ---
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))

    # --- Limits ---
    max_request_body_bytes: int = 100 * 1024  # 100 KB
    max_article_chars: int = 4000
    max_batch_summarize: int = 5
    summarize_rate_limit_per_minute: int = 10

    # --- CORS ---
    cors_origins: tuple = (
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    )

    @property
    def demo_mode(self) -> bool:
        """True when either API key is missing -> app falls back to sample data."""
        return not (self.news_api_key and self.groq_api_key)

    @property
    def news_configured(self) -> bool:
        return bool(self.news_api_key)

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key)


settings = Settings()
