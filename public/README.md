# FinNews AI

Classic financial news briefing: FastAPI plus vanilla HTML, CSS, and JavaScript.
NewsAPI supplies news; Groq simplifies articles. Missing provider credentials produce
clearly labeled demo articles/explanations. Configured provider failures stay errors.
No frontend framework, build step, database, Docker, or external font service.

## Run locally

From the repository root, with Python 3.9+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PORT=8000 sh start.sh
```

Open http://localhost:8000. Stop with Ctrl+C. `start.sh` and `Procfile` launch
`python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
The host's `PORT` takes precedence; 8000 is only the local fallback. No production reload.

FastAPI serves `public/index.html` at `/`, assets at `/static`, `/health`,
`/api/health`, `/api/news?q=finance&page_size=12`, and `POST /api/summarize`.
`public/` is this repository's frontend directory; no duplicate `frontend/` is needed.
The browser uses relative API URLs. API routes are registered before the root static mount.

Keep existing `NEWS_API_KEY` and `GROQ_API_KEY` in server environment configuration.
Do not commit keys or `.env`. Optional settings: `GROQ_MODEL`, `NEWS_API_URL`,
`ALLOWED_ORIGINS`. Each provider can run independently in demo or live mode.
Demo search/categories intentionally show the same three fictional examples.

## Verification

With the virtualenv activated:

```bash
python -m unittest discover -s tests -v
python -m pip check
node --check public/static/app.js
node --import ./tests/hatchable-loader.mjs --test tests/hatchable.test.mjs
curl -f http://localhost:8000/
curl -f http://localhost:8000/health
curl -f 'http://localhost:8000/api/news?q=finance&page_size=1'
curl -f 'http://localhost:8000/static/style.css?v=classic-2'
curl -f 'http://localhost:8000/static/app.js?v=classic-2'
curl -f -H 'Content-Type: application/json' -d '{"title":"Demo article","description":"A fictional economic example."}' http://localhost:8000/api/summarize
```

Node 24+ is only needed for the Hatchable handler tests; no npm installation.
Tests use synthetic provider responses. Real account credentials, access, and quota
must be verified on the deployed service. In the browser, try categories, search,
Refresh, Simplify with AI, and Summarize briefing; Escape closes the dialog.

## Deployment and recovered work

See [Hatchable deployment guide](docs/HATCHABLE_GUIDE.md) for this existing site:
https://k6octh.hatchable.site. The GitHub default branch is `main`; verify that
Hatchable Git Sync watches it. Merge the PR before syncing or promoting.

The prior commit `d43acdfd6f7284a159d788b7fa9a5ccfd18c7815` survived on
`coderabbit/make-repo-runnable/6c0398c7`, but was absent from `main`. This update
restores its API fixes, tests, local image, and Hatchable adapters and completes
the requested redesign. No `.env` or API keys were changed.

Hatchable runs the restored JavaScript `api/`, `pages/`, and `lib/` adapters;
its documented runtime does **not** execute the Python Procfile. FastAPI remains
the canonical single-server application for a Python-capable host. Both runtimes
serve the same frontend and API contract. Do not deploy just `public/` when APIs are needed.
