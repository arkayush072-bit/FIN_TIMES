"""
NewsService — talks to NewsAPI (https://newsapi.org) and normalizes
whatever comes back into our own Article shape. Falls back to a small set
of realistic sample articles when no API key is configured (Demo Mode),
or when NewsAPI itself fails, so the frontend never has to special-case
"no key" vs "provider down" beyond the message it shows.
"""

import logging
from typing import Optional

import httpx

from ..config import settings
from ..utils.validators import sanitize_article_text, is_safe_url

logger = logging.getLogger("finnews.news_service")

# Categories exposed to the frontend. NewsAPI's own `category` query param
# only understands "business", so everything else is layered on top of it
# with keyword refinement or a different endpoint entirely (see below).
CATEGORIES = ["Markets", "Business", "Economy", "Technology", "India", "Global"]

_CATEGORY_KEYWORDS = {
    "markets": "stock market OR shares OR Wall Street OR Nasdaq OR Dow Jones",
    "economy": "inflation OR GDP OR interest rates OR central bank OR unemployment",
    "technology": "tech OR technology OR AI OR software OR startup",
    "business": None,  # top-headlines?category=business as-is
}

DEMO_ARTICLES = [
    {
        "title": "Federal Reserve Holds Interest Rates Steady, Signals Caution Ahead",
        "description": "Policymakers kept the benchmark rate unchanged, citing mixed signals on inflation and employment.",
        "content": (
            "The Federal Reserve left its benchmark interest rate unchanged at its latest meeting, "
            "extending a pause that began earlier in the year. Officials said recent data on inflation "
            "and the labor market were sending mixed signals, and that they preferred to gather more "
            "evidence before making another move. Markets had largely priced in the pause, and major "
            "indexes were little changed following the announcement. The central bank's next meeting "
            "is scheduled for later in the year, and traders will be watching upcoming jobs and "
            "inflation reports closely for hints about the path ahead."
        ),
        "url": "https://example.com/demo/fed-holds-rates-steady",
        "image_url": None,
        "source": "Demo Wire",
        "published_at": "2026-09-27T14:30:00Z",
        "category": "Economy",
    },
    {
        "title": "Tech Shares Lead Broad Market Rally After Strong Earnings",
        "description": "Several large technology companies beat quarterly profit expectations, lifting the wider market.",
        "content": (
            "A wave of stronger-than-expected earnings from major technology companies helped push "
            "broad stock indexes higher this week. Several firms reported revenue and profit ahead of "
            "analyst estimates, driven in part by continued corporate spending on cloud computing and "
            "artificial intelligence infrastructure. Shares of chipmakers and software companies were "
            "among the biggest gainers. Analysts cautioned that valuations in the sector remain elevated "
            "compared with historical averages, and that future gains may depend on companies continuing "
            "to deliver on high expectations."
        ),
        "url": "https://example.com/demo/tech-shares-rally",
        "image_url": None,
        "source": "Demo Wire",
        "published_at": "2026-09-27T09:15:00Z",
        "category": "Markets",
    },
    {
        "title": "India's GDP Growth Beats Forecasts, Driven by Services and Manufacturing",
        "description": "The economy expanded faster than economists expected last quarter, official data showed.",
        "content": (
            "India's economy grew faster than most economists had forecast in the latest quarter, "
            "according to government data, with strength in the services and manufacturing sectors "
            "offsetting a slower pace of agricultural growth. Officials pointed to steady consumer "
            "demand and continued investment in infrastructure projects as key drivers. Economists said "
            "the figures support expectations that the country will remain one of the world's "
            "faster-growing major economies this year, though they flagged global trade conditions "
            "and energy prices as risks to watch."
        ),
        "url": "https://example.com/demo/india-gdp-beats-forecasts",
        "image_url": None,
        "source": "Demo Wire",
        "published_at": "2026-09-26T11:00:00Z",
        "category": "India",
    },
    {
        "title": "Oil Prices Climb on Supply Concerns as Global Demand Holds Firm",
        "description": "Crude prices rose after producers signaled no immediate increase in output.",
        "content": (
            "Crude oil prices rose this week after major producing nations signaled they would not "
            "increase output in the near term, even as global demand has held up better than some "
            "analysts expected. The move added to concerns about tight supply heading into the winter "
            "months. Energy stocks moved higher in step with crude prices, while airlines and other "
            "fuel-intensive businesses saw shares dip on worries about higher input costs. Analysts said "
            "prices could remain volatile depending on production decisions and demand data."
        ),
        "url": "https://example.com/demo/oil-prices-climb",
        "image_url": None,
        "source": "Demo Wire",
        "published_at": "2026-09-25T16:45:00Z",
        "category": "Global",
    },
    {
        "title": "Retailer Shares Slide After Weak Holiday Season Guidance",
        "description": "A major retail chain cut its full-year profit outlook, citing softer consumer spending.",
        "content": (
            "Shares of a major retail chain fell sharply after the company lowered its full-year profit "
            "guidance, citing softer-than-expected consumer spending heading into the holiday shopping "
            "season. Executives said shoppers were being more selective and trading down to cheaper "
            "products. The news weighed on other retail stocks as well, as investors worried the trend "
            "could be broader across the sector. Some analysts said the pullback may be temporary if "
            "wage growth and lower borrowing costs support spending later in the year."
        ),
        "url": "https://example.com/demo/retailer-shares-slide",
        "image_url": None,
        "source": "Demo Wire",
        "published_at": "2026-09-24T13:20:00Z",
        "category": "Business",
    },
    {
        "title": "Startup Funding Rebounds as Investors Return to Growth-Stage Deals",
        "description": "Venture capital investment rose for a second straight quarter after a prolonged slowdown.",
        "content": (
            "Venture capital funding for startups rose for a second consecutive quarter, according to "
            "industry data, as investors showed renewed appetite for growth-stage deals after a "
            "prolonged slowdown. Much of the increase was concentrated in companies working on "
            "artificial intelligence and enterprise software. Founders and investors said deal terms "
            "remain more disciplined than during the previous boom, with more emphasis on a clear path "
            "to profitability rather than growth at any cost."
        ),
        "url": "https://example.com/demo/startup-funding-rebounds",
        "image_url": None,
        "source": "Demo Wire",
        "published_at": "2026-09-23T10:05:00Z",
        "category": "Technology",
    },
    {
        "title": "Currency Markets Steady as Traders Await Central Bank Signals",
        "description": "Major currencies traded in a narrow range ahead of upcoming policy meetings.",
        "content": (
            "Major currencies traded in a relatively narrow range this week as investors waited for "
            "signals from upcoming central bank meetings before placing new bets. Trading desks "
            "described activity as cautious, with many participants reluctant to take large positions "
            "ahead of fresh economic data. Strategists said the coming weeks could bring more volatility "
            "once policymakers provide clearer guidance on the likely path for interest rates."
        ),
        "url": "https://example.com/demo/currency-markets-steady",
        "image_url": None,
        "source": "Demo Wire",
        "published_at": "2026-09-22T08:40:00Z",
        "category": "Markets",
    },
    {
        "title": "Small Businesses Report Improved Confidence Despite Lingering Cost Pressures",
        "description": "A widely watched survey showed optimism ticking up even as owners cite persistent expenses.",
        "content": (
            "A closely watched survey of small business owners showed confidence improving modestly, "
            "even as many respondents continued to cite rising costs for labor, materials and insurance "
            "as ongoing challenges. Owners in the survey pointed to steadier customer demand as a reason "
            "for cautious optimism. Economists said small business sentiment is often a useful early "
            "signal for broader economic momentum, since smaller firms tend to be more sensitive to "
            "local conditions than large corporations."
        ),
        "url": "https://example.com/demo/small-business-confidence",
        "image_url": None,
        "source": "Demo Wire",
        "published_at": "2026-09-21T15:10:00Z",
        "category": "Business",
    },
]


class NewsService:
    def __init__(self) -> None:
        self._api_key = settings.news_api_key
        self._base_url = settings.news_api_base_url
        self._timeout = settings.news_api_timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_news(
        self, category: str = "business", page: int = 1, page_size: int = 10
    ) -> dict:
        if not self._api_key:
            return self._demo_response(category=category, page=page, page_size=page_size)

        category_norm = (category or "business").strip().lower()
        params = self._params_for_category(category_norm)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base_url}/{params['endpoint']}",
                    params={**params["query"], "page": page, "pageSize": page_size},
                    headers={"X-Api-Key": self._api_key},
                )
        except httpx.TimeoutException:
            logger.warning("NewsAPI request timed out (category=%s)", category_norm)
            return {"articles": [], "total_results": 0, "demo_mode": False,
                     "error": "Unable to fetch the latest news. Please try again."}
        except httpx.HTTPError as exc:
            logger.warning("NewsAPI network error: %s", exc)
            return {"articles": [], "total_results": 0, "demo_mode": False,
                     "error": "Unable to fetch the latest news. Please try again."}

        return self._handle_response(resp)

    async def search(self, query: str, page: int = 1, page_size: int = 10) -> dict:
        if not self._api_key:
            return self._demo_response(search_query=query, page=page, page_size=page_size)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base_url}/everything",
                    params={
                        "q": query,
                        "sortBy": "publishedAt",
                        "page": page,
                        "pageSize": page_size,
                        "language": "en",
                    },
                    headers={"X-Api-Key": self._api_key},
                )
        except httpx.TimeoutException:
            logger.warning("NewsAPI search timed out (q=%s)", query)
            return {"articles": [], "total_results": 0, "demo_mode": False,
                     "error": "Unable to fetch the latest news. Please try again."}
        except httpx.HTTPError as exc:
            logger.warning("NewsAPI search network error: %s", exc)
            return {"articles": [], "total_results": 0, "demo_mode": False,
                     "error": "Unable to fetch the latest news. Please try again."}

        return self._handle_response(resp)

    @staticmethod
    def categories() -> list[str]:
        return list(CATEGORIES)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _params_for_category(self, category: str) -> dict:
        """Build the NewsAPI endpoint + query params for a given category,
        per the routing rules in the spec:
          - India -> top-headlines?country=in
          - Global -> top-headlines (no country filter)
          - Business/Markets/Economy/Technology -> top-headlines?category=business
            with keyword refinement for the non-"business" ones
        """
        if category == "india":
            return {"endpoint": "top-headlines", "query": {"country": "in"}}
        if category == "global":
            return {"endpoint": "top-headlines", "query": {"language": "en"}}

        query: dict = {"category": "business", "language": "en"}
        keywords = _CATEGORY_KEYWORDS.get(category)
        if keywords:
            query["q"] = keywords
        return {"endpoint": "top-headlines", "query": query}

    def _handle_response(self, resp: httpx.Response) -> dict:
        if resp.status_code == 429:
            logger.warning("NewsAPI rate limit hit")
            return {"articles": [], "total_results": 0, "demo_mode": False,
                     "error": "We're being rate limited by the news provider. Please try again shortly."}

        if resp.status_code == 401:
            logger.error("NewsAPI rejected the configured API key")
            return {"articles": [], "total_results": 0, "demo_mode": False,
                     "error": "API configuration error. Check your environment variables."}

        if resp.status_code >= 400:
            logger.warning("NewsAPI returned status %s", resp.status_code)
            return {"articles": [], "total_results": 0, "demo_mode": False,
                     "error": "Unable to fetch the latest news. Please try again."}

        try:
            data = resp.json()
        except ValueError:
            logger.error("NewsAPI returned a non-JSON response")
            return {"articles": [], "total_results": 0, "demo_mode": False,
                     "error": "Unable to fetch the latest news. Please try again."}

        raw_articles = data.get("articles", []) or []
        articles = self._normalize_and_dedupe(raw_articles)

        return {
            "articles": articles,
            "total_results": data.get("totalResults", len(articles)),
            "demo_mode": False,
            "error": None,
        }

    def _normalize_and_dedupe(self, raw_articles: list) -> list[dict]:
        seen_urls: set[str] = set()
        normalized: list[dict] = []

        for item in raw_articles:
            url = (item.get("url") or "").strip()
            if not url or not is_safe_url(url) or url in seen_urls:
                continue
            seen_urls.add(url)

            source = item.get("source") or {}
            normalized.append({
                "title": sanitize_article_text(item.get("title") or "Untitled", 300),
                "description": sanitize_article_text(item.get("description") or "", 500),
                "content": sanitize_article_text(item.get("content") or "", settings.max_article_chars),
                "url": url,
                "image_url": item.get("urlToImage") or None,
                "source": source.get("name") or "Unknown",
                "published_at": item.get("publishedAt") or None,
            })

        return normalized

    def _demo_response(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        pool = DEMO_ARTICLES

        if search_query:
            q = search_query.lower()
            pool = [a for a in DEMO_ARTICLES if q in a["title"].lower() or q in a["description"].lower()]
        elif category and category.lower() not in ("business", "global", ""):
            cat_title = category.strip().lower()
            pool = [a for a in DEMO_ARTICLES if a["category"].lower() == cat_title]
            if not pool:
                pool = DEMO_ARTICLES

        start = max(0, (page - 1) * page_size)
        end = start + page_size
        page_items = pool[start:end]

        articles = [
            {
                "title": a["title"],
                "description": a["description"],
                "content": a["content"],
                "url": a["url"],
                "image_url": a["image_url"],
                "source": a["source"],
                "published_at": a["published_at"],
            }
            for a in page_items
        ]

        return {
            "articles": articles,
            "total_results": len(pool),
            "demo_mode": True,
            "error": None,
        }


news_service = NewsService()
