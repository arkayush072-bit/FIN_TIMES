import json
import re
from typing import Dict, Any
from groq import AsyncGroq
from backend.config import get_settings
from backend.models import Article, SummaryResponse, KeyTerm

settings = get_settings()

SYSTEM_PROMPT = """
You are FinNews AI, a financial news simplification assistant.

Your job is to explain the supplied news article clearly and accurately.

Rules:
- Use only information present in the article.
- Never invent facts, statistics, quotes or causes.
- Preserve important numbers and names exactly when they are provided.
- Explain financial terminology in simple language.
- Do not give personalized investment advice.
- Do not tell the reader to buy, sell or hold any asset.
- Do not predict a stock price or market outcome.
- If the article does not provide enough information, say so.
- Keep the response concise.
- Return ONLY valid JSON.

Required JSON:
{
  "summary": "2-4 sentence summary",
  "what_happened": "plain-language explanation",
  "why_it_matters": "why the event may matter according to the article",
  "key_terms": [
    {"term": "term", "meaning": "simple meaning"}
  ],
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
  "beginner_explanation": "very simple explanation for a student or beginner"
}
""".strip()


def _demo_summary(article: Article) -> SummaryResponse:
    """Used when GROQ_API_KEY is missing or AI is unavailable."""
    text = article.description or article.content or ""
    return SummaryResponse(
        mode="demo",
        summary=text[:360] if text else "No summary available.",
        what_happened="This demo article discusses a financial or economic development and the factors readers should watch.",
        why_it_matters="Financial news can affect business expectations, borrowing costs, consumer activity and market sentiment.",
        key_terms=[
            KeyTerm(term="Inflation", meaning="A general increase in prices over time."),
            KeyTerm(term="Interest rate", meaning="The cost of borrowing money or the return earned on lending."),
            KeyTerm(term="Market sentiment", meaning="The overall attitude investors have toward a market or asset."),
        ],
        key_takeaways=[
            "Check the original article for exact figures and context.",
            "Market reactions can change as new information becomes available.",
            "This summary is educational and is not investment advice.",
        ],
        beginner_explanation=(
            "In simple terms, the article describes an economic or business event "
            "and explains why people who follow financial markets may pay attention to it."
        ),
    )


def _extract_json(text: str) -> Dict[str, Any]:
    """Robustly extract JSON from an LLM response (handles ```json fences)."""
    cleaned = (text or "").strip()

    # Strip markdown code fences
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to salvage the first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    # Last resort — return a plain-text summary
    return {"summary": cleaned}


async def summarize_article(article: Article) -> SummaryResponse:
    """Call Groq to simplify an article. Falls back to demo summary if no key."""
    if not settings.GROQ_API_KEY:
        return _demo_summary(article)

    article_text = "\n\n".join(
        [x for x in [article.title, article.description, article.content] if x]
    )[:6500]

    try:
        async with AsyncGroq(api_key=settings.GROQ_API_KEY) as client:
            completion = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                temperature=0.2,
                max_tokens=900,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": article_text},
                ],
            )
    except Exception as e:
        raise RuntimeError(f"Groq API error: {e}") from e

    content = completion.choices[0].message.content if completion.choices else ""
    data = _extract_json(content)

    # Normalize key_terms
    key_terms = []
    for item in (data.get("key_terms") or []):
        if isinstance(item, dict) and item.get("term"):
            key_terms.append(
                KeyTerm(
                    term=str(item.get("term", "")),
                    meaning=str(item.get("meaning", "")),
                )
            )

    # Normalize key_takeaways
    takeaways = [str(x) for x in (data.get("key_takeaways") or []) if x]

    return SummaryResponse(
        summary=data.get("summary") or "No summary available.",
        what_happened=data.get("what_happened") or "Not available.",
        why_it_matters=data.get("why_it_matters") or "Not available.",
        key_terms=key_terms,
        key_takeaways=takeaways,
        beginner_explanation=data.get("beginner_explanation") or "Not available.",
    )
