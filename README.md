# FinNews AI

AI-powered financial news simplifier. FinNews AI fetches the latest financial, business and
economic news from **NewsAPI** and uses **Groq's `llama-3.3-70b-versatile`** model to turn each
article into a beginner-friendly, plain-language summary.

**Educational and informational only.** FinNews AI never outputs buy/sell/hold advice, price
predictions, or guaranteed-return claims.

---

## Overview

- Fetch the latest business, markets, economy, technology, India and global financial news.
- Simplify any article on demand into six structured sections: summary, what happened, why it
  matters, key terms, key takeaways, and a zero-background explanation.
- News and AI summarization are **separate, user-triggered actions** — nothing is auto-summarized.
- Runs fully in **Demo Mode** with realistic sample data when no API keys are configured, so you
  can see the whole app before signing up for anything.

## Features

- Classic editorial (WSJ / FT–style) frontend — plain HTML, CSS and JavaScript, no build step.
- FastAPI backend with async NewsAPI and Groq clients.
- Article-level caching (by `hash(url + "summary")`) so the same article is never summarized twice.
- Graceful, friendly error handling for provider outages, rate limits, and bad API keys — the app
  itself never goes down just because a third-party API does.
- Input sanitization (HTML/script stripping) on everything shown in the browser.
- Basic per-IP rate limiting on the summarize endpoint.
- Fully mocked pytest suite — runs without any real API keys.

## Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Python 3.11+, FastAPI, Uvicorn, Pydantic, HTTPX (async) |
| AI         | Groq API — `llama-3.3-70b-versatile` |
| News       | NewsAPI |
| Frontend   | HTML5, CSS3, vanilla JavaScript (no frameworks, no build tools) |
| Tests      | pytest, pytest-asyncio, respx (HTTP mocking) |

## Architecture

```
                 ┌──────────────────────────┐
   Browser       │   frontend/ (static)     │
   ───────────►  │   index.html/.css/.js    │
                 └────────────┬─────────────┘
                              │ fetch()
                              ▼
                 ┌──────────────────────────┐
                 │   FastAPI  (backend/)     │
                 │   main.py — routes        │
                 └───┬─────────────┬────────┘
                     │             │
        GET /api/news│             │POST /api/summarize
        GET /api/search             │
                     ▼             ▼
         ┌───────────────┐   ┌───────────────────┐
         │ news_service   │   │ cache_service      │
         │ (NewsAPI)      │   │ (in-memory, TTL)    │
         └───────┬────────┘   └─────────┬──────────┘
                 │                      │ miss
                 ▼                      ▼
         ┌───────────────┐   ┌───────────────────┐
         │   NewsAPI      │   │   ai_service       │
         │  (external)    │   │   (Groq client)     │
         └───────────────┘   └─────────┬──────────┘
                                        ▼
                              ┌───────────────────┐
                              │  Groq API           │
                              │  llama-3.3-70b-      │
                              │  versatile           │
                              └───────────────────┘
```

News retrieval and AI summarization are independent flows — fetching news never calls Groq, and
summarizing never re-fetches news.

## Folder structure

```
finnews-ai/
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + routes + static mount
│   ├── config.py                # env loading, settings
│   ├── models.py                 # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── news_service.py       # NewsAPI client
│   │   ├── ai_service.py         # Groq client + prompt engineering
│   │   └── cache_service.py      # in-memory cache (Redis-swappable)
│   └── utils/
│       ├── __init__.py
│       └── validators.py         # sanitize HTML, validate URLs, truncate
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_news_service.py
│   ├── test_ai_service.py
│   └── test_routes.py
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Install

### 1. Clone / unzip the project, then create a virtual environment

**macOS / Linux**
```bash
cd finnews-ai
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
cd finnews-ai
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

Then edit `.env`:

```
NEWS_API_KEY=your_newsapi_key
GROQ_API_KEY=your_groq_api_key
```

- Get a free NewsAPI key: https://newsapi.org/register
- Get a free Groq API key: https://console.groq.com/keys

If you skip this step, the app still runs — it just serves **Demo Mode** sample data instead of
live news and AI summaries, and shows a banner saying so.

### 4. Run the backend

```bash
uvicorn backend.main:app --reload
```

### 5. Open the frontend

Visit **http://localhost:8000** — FastAPI serves the frontend directly, so there's nothing extra
to start.

---

## API reference

All responses are JSON. Base URL for local development: `http://localhost:8000`.

### `GET /health`

```bash
curl http://localhost:8000/health
```
```json
{
  "status": "healthy",
  "service": "FinNews AI",
  "news_api_configured": false,
  "groq_api_configured": false,
  "demo_mode": true
}
```

### `GET /api/news?category=business&page=1&page_size=10`

```bash
curl "http://localhost:8000/api/news?category=markets&page=1&page_size=10"
```

### `GET /api/search?q=interest+rates`

```bash
curl "http://localhost:8000/api/search?q=interest%20rates"
```

### `GET /api/categories`

```bash
curl http://localhost:8000/api/categories
```

### `POST /api/summarize`

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{
        "title": "Fed holds interest rates steady",
        "description": "Policymakers kept rates unchanged.",
        "content": "The Federal Reserve left its benchmark rate unchanged...",
        "url": "https://example.com/fed-holds-rates"
      }'
```

### `POST /api/summarize/batch`

```bash
curl -X POST http://localhost:8000/api/summarize/batch \
  -H "Content-Type: application/json" \
  -d '{"articles": [
        {"title": "Article 1", "description": "", "content": "...", "url": "https://example.com/1"},
        {"title": "Article 2", "description": "", "content": "...", "url": "https://example.com/2"}
      ]}'
```

---

## Testing

The full suite runs without any real API keys — every external call (NewsAPI, Groq) is mocked
with `respx`.

```bash
pip install -r requirements.txt
pytest -v
```

Covers: health check shape, successful and failed news fetches, empty-result handling,
de-duplication, category routing, successful and failed AI summaries, cache-hit behavior (Groq is
only ever called once per article), input validation (422 on bad input), and end-to-end route
behavior through FastAPI's `TestClient`.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| App shows "Demo Mode" banner | `NEWS_API_KEY` or `GROQ_API_KEY` missing from `.env`. Add both and restart. |
| `API configuration error` message | The key is present but rejected (401) — double-check it was copied correctly and hasn't expired. |
| `Unable to fetch the latest news` | NewsAPI is down, rate limited, or timed out. Wait and retry — this is a provider issue, not an app crash. |
| `AI summarization is temporarily unavailable` | Groq is down, rate limited, or timed out. The article list still works independently. |
| Frontend looks stale after editing CSS/JS | Bump the `?v=` query string in `index.html`'s `<link>`/`<script>` tags, or hard-refresh. |
| `422 Unprocessable Entity` on `/api/summarize` | Check the request body matches the shape in the API reference above (title/url required). |

## Security notes

- API keys live only in `.env` (git-ignored) — never hardcoded, sent to the frontend, or logged.
- CORS is restricted to local development origins by default; update `cors_origins` in
  `backend/config.py` for your deployed frontend domain(s).
- Request bodies are capped at 100 KB.
- `/api/summarize` is rate-limited per IP (10 requests/minute by default).
- All article text is HTML-stripped before being sent to the model or rendered in the browser.
- No stack traces are ever returned to the client — only the friendly messages listed above.

## Deployment

- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- The app reads `PORT` from the environment — never hardcode it.
- FastAPI mounts `frontend/` at `/static` and serves `frontend/index.html` at `/`.
- `/health` returns `200` and is suitable for host health checks.
- Set `NEWS_API_KEY` and `GROQ_API_KEY` as real environment variables on your host (not `.env` —
  that file is for local development only).
- The in-memory cache and rate limiter are per-process; if you deploy multiple workers/instances
  behind a load balancer, swap `CacheService` for a shared backend (e.g. Redis) using the same
  `get/set/clear` interface.

---

## Known limitations

- Cache and rate limiting are in-memory and per-process — they reset on restart and aren't shared
  across multiple server instances.
- Demo Mode sample articles are static placeholder content, not live data.
- No user accounts, authentication, or persistence — this is a stateless news/summary tool.

## Future improvements

- Swap the in-memory cache for Redis for multi-instance deployments.
- Add pagination controls and infinite scroll to the frontend.
- Add a "saved articles" list using browser storage.
- Support additional languages for summaries.
