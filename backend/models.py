from typing import List, Optional
from pydantic import BaseModel, Field


class Article(BaseModel):
    title: str = ""
    description: Optional[str] = ""
    content: Optional[str] = ""
    url: str = ""
    urlToImage: Optional[str] = ""
    publishedAt: Optional[str] = ""
    source: dict = Field(default_factory=lambda: {"name": "Unknown"})


class NewsResponse(BaseModel):
    status: str
    totalResults: int
    articles: List[Article]
    mode: str  # "live" | "demo"


class ArticleRequest(BaseModel):
    title: str = ""
    description: Optional[str] = ""
    content: Optional[str] = ""
    url: Optional[str] = ""


class KeyTerm(BaseModel):
    term: str
    meaning: str


class SummaryResponse(BaseModel):
    summary: str
    what_happened: str
    why_it_matters: str
    key_terms: List[KeyTerm] = []
    key_takeaways: List[str] = []
    beginner_explanation: str


class HealthResponse(BaseModel):
    status: str
    news_api: bool
    groq_api: bool
