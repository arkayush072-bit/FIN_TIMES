# FinNews AI

A financial news dashboard with a FastAPI backend. Fetch articles from NewsAPI
and simplify them with Groq, or run the full dashboard with built-in demo data
without any API keys. The frontend is plain HTML, CSS, and JavaScript; no Node.js
installation or frontend build is required.

## Run locally

Requires Python 3.9 or newer with `pip` and `venv`. Run these commands from the
repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

On Windows, use `python` instead of `python3` and activate with
`.venv\Scripts\Activate.ps1` in PowerShell.

Open **http://localhost:8000**. The same server provides the dashboard and API,
so there is no separate frontend process or API URL to edit. Stop with Ctrl+C.
For development, add `--reload` to the server command.

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

## Live news and AI summaries (optional)

Copy `.env.example` to `.env` in the repository root and set your own keys:

```dotenv
NEWS_API_KEY=
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

Restart the server after editing configuration. Keys stay on the backend and
`.env` is ignored by Git. Each provider works independently:

- No `NEWS_API_KEY`: returns the same three clearly labeled fictional articles
  for every search/category (or fewer when `page_size` is smaller).
- No `GROQ_API_KEY`: returns a clearly labeled sample explanation.
- Configured provider failures return an error; they do not silently become demo
  results. Real provider access depends on valid keys, quota, and network access.

`ALLOWED_ORIGINS` is a comma-separated list for a separately hosted frontend.
The default single-server setup does not require CORS configuration.
`NEWS_API_URL` can override the NewsAPI endpoint for integration testing.

## Checks

With the virtual environment activated:

```bash
python -m unittest discover -s tests -v
python -m pip check
```

The tests cover startup, serving the dashboard, demo news/summaries, request
validation, and provider responses/errors using synthetic mocks. They do not
use real credentials or spend provider quota.

## Repository layout

- `public/`: dashboard and local image fallback.
- `backend/main.py`: application entry point, API routes, and static serving.
- `backend/routers/`: news, summary, and validation endpoints.
- `backend/services/`: NewsAPI and Groq integrations and demo data.
- `.env.example`: optional configuration template.
- `requirements.txt`: pinned direct Python dependencies.
- `tests/`: API and provider regression tests.

## Hosting

Run the Uvicorn command above on a host that supports a long-running Python
web service, using the port required by that host. Route browser traffic to this
application so `/api/*` and `/static/*` are available at the same origin.
Serving `public/` alone on a static host will not run the API. For Hatchable, use the JavaScript handlers and deployment procedure below. No database is required.

## Deploy the existing app on Hatchable

Hatchable uses a JavaScript sandbox, so it runs `api/*.js` and `lib/*.js` instead
of the Python backend. The handlers have the same URLs and JSON responses as
FastAPI. `public/` is served at the site root, including `/static/` assets.
The hosted handlers call real NewsAPI and Groq APIs; they do not fall back to
sample data when a connection is missing or fails.

1. Connect an authorized Hatchable MCP client to your **existing project**.
   Read its current files first and apply the changes from `api/`, `lib/`,
   `public/`, and `hatchable.toml`. Python files and the local virtualenv are not
   needed on Hatchable. A fresh GitHub/zip import creates another project; it
   does not update an existing deployment. A Git push alone is not a deployment.
2. Run Hatchable's `dry_run_deploy` to validate these files, then `deploy` on that
   project. This repository's local mock tests cannot replace that validation.
3. On that project's **Setup** page, connect the `newsapi` and `groq` APIs
   declared in `hatchable.toml`. Set NewsAPI's base URL to
   `https://newsapi.org/v2` and Groq's to `https://api.groq.com/openai/v1`.
   Use your NewsAPI key as `X-Api-Key` (or its supported Authorization header)
   and your Groq key as `Authorization: Bearer <key>` through the platform's
   API connection settings. The proxy attaches authentication; keys must not
   be placed in repository files or frontend JavaScript. A local `.env` is not
   uploaded or used by these handlers.
4. Verify `/api/news?q=finance&page_size=1` returns `mode: "live"`, then submit
   that article to `/api/summarize` and confirm `mode: "live"` and a real summary.
   `/api/health` confirms only that the handler is running; its provider fields
   are `null` because gateway-managed credentials cannot be checked by reading
   environment variables.
5. If Hatchable creates a draft, review it and use **Promote to live** in the
   project's History tab. Public projects can require this owner action.

Hatchable contract tests (Node 24+, no npm installation):

```bash
node --import ./tests/hatchable-loader.mjs --test tests/hatchable.test.mjs
```

Reference: [project structure](https://hatchable.com/docs/developers/project-structure),
[API proxy SDK](https://hatchable.com/docs/developers/sdk#api),
[deployment flow](https://hatchable.com/docs/developers/import-export).

For the existing **k6octh.hatchable.site** project, follow the
[step-by-step Hatchable guide](docs/HATCHABLE_GUIDE.md). It includes the exact
update prompt, provider connection settings, verification links, and draft
promotion steps.
