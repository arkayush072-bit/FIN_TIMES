"""
Pydantic models for FinNews AI requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

class Article(BaseModel):
    title: str
    description: Optional[str] = ""
    content: Optional[str] = ""
    url: str
    image_url: Optional[str] = None
    source: Optional[str] = "Unknown"
    published_at: Optional[str] = None


class NewsResponse(BaseModel):
    articles: List[Article] = Field(default_factory=list)
    total_results: int = 0
    demo_mode: bool = False
    error: Optional[str] = None


class CategoriesResponse(BaseModel):
    categories: List[str]


# ---------------------------------------------------------------------------
# Summarize
# ---------------------------------------------------------------------------

class SummarizeRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field("", max_length=2000)
    content: Optional[str] = Field("", max_length=20000)
    url: str = Field(..., min_length=1, max_length=2000)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()


class BatchSummarizeRequest(BaseModel):
    articles: List[SummarizeRequest] = Field(..., min_length=1, max_length=5)


class KeyTerm(BaseModel):
    term: str
    meaning: str


class SummarizeResponse(BaseModel):
    summary: str
    what_happened: str
    why_it_matters: str
    key_terms: List[KeyTerm] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    beginner_explanation: str
    cached: bool = False
    demo_mode: bool = False


class BatchSummarizeResponse(BaseModel):
    results: List[SummarizeResponse]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    service: str
    news_api_configured: bool
    groq_api_configured: bool
    demo_mode: bool
