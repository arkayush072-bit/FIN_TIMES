from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    NEWS_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    ALLOWED_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"
    NEWS_PAGE_SIZE: int = 12
    NEWS_API_URL: str = "https://newsapi.org/v2/everything"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
