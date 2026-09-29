# Redeploy the existing FinNews AI site

Site: https://k6octh.hatchable.site

## What was wrong

- The previous repair commit `d43acdfd6f7284a159d788b7fa9a5ccfd18c7815` was on
  `coderabbit/make-repo-runnable/6c0398c7`, absent from default branch `main`.
- `public/index.html` on main called `http://localhost:8000`; the live page was a
  different revision using the incompatible `/api/simplify` contract.
- `backend/main.py` served API metadata at `/`, had no `/health`, and used imports
  that failed with `uvicorn backend.main:app` from the repository root.
- `backend/services/news_service.py` accidentally duplicated the AI service and
  did not define the imported `fetch_news` function.
- `requirements.txt`, `Procfile`, and production startup were missing.
- `hatchable.toml` still described Threshold and lacked API connections. There were
  no `api/*.js` handlers. On 29 September 2026 the live `/api/health` returned
  HTTP 404, `Function not found`, and an empty `available_routes` list.
- `public/finnews-backend/` held redundant Python source, which static hosting cannot execute.

These are verified repository/runtime mismatches. No evidence established a reused
build cache, the private Git Sync branch, or the latest draft's status. Do not
attribute the stale deployment to a single cache file. CSS/JS now use
`?v=classic-2`; FastAPI's root response revalidates with `Cache-Control: no-cache`.
Bump both asset versions in `public/index.html` when publishing asset changes.

## Git Sync and promotion

1. Merge this PR into `main` on GitHub. It contains one atomic commit.
2. Open [Hatchable Console](https://hatchable.com/console), then the existing project
   whose URL is `k6octh.hatchable.site`.
3. In its Git Sync settings, confirm repository `arkayush072-bit/FIN_TIMES`, branch
   `main`, and repository root. Trigger sync/redeploy using that screen's control
   and confirm the imported revision matches the merged commit. Exact sync control
   labels are account-specific and were not accessible from this task.
4. Check deployment validation/logs. All of `public/`, `api/`, `pages/`, `lib/`,
   and `hatchable.toml` must be present together. An authorized Hatchable-connected
   editor can run `dry_run_deploy` then `deploy` if the console reports blockers.
5. Open the resulting draft, verify the checks below, then select **Promote** for
   that deployment in the console's deployment history. Published projects may
   keep updates in a draft until this owner action. Hard refresh the public URL
   after promotion; a browser refresh alone does not promote a draft.

Do not import a second project to update this URL. The public URL is not editing
access. This coding task has no authenticated Hatchable connection and cannot
confirm the sync, platform validator, or promotion on your behalf.

## Runtime and providers

Hatchable routes `api/news.js` to `/api/news`, `api/summarize.js` to
`/api/summarize`, `api/health.js` to `/api/health`, and `pages/health.js` to
`/health`. It serves `public/` at `/`. The adapters use the Hatchable API proxy
and retain the Python API contract; no frontend framework or Node packages.

On the project's **Setup** page, verify the existing `newsapi` and `groq`
connections declared in `hatchable.toml`. NewsAPI's base URL is
`https://newsapi.org/v2`, authenticated with `X-Api-Key` or its supported bearer
header; Groq's is `https://api.groq.com/openai/v1`, with bearer authentication.
Keep credentials in Hatchable's connection controls, never in source/browser code.
This update does not modify keys. Local `.env` settings do not configure Hatchable.

A missing connection (`SetupRequired`) returns labeled demo data. Rejected keys,
quota errors, and malformed provider responses return 502 without leaking provider
error text. Health returns provider fields `null` on Hatchable because the proxy
keeps credentials opaque; a 200 health response alone does not prove provider access.

For a Python host instead, install `requirements.txt`, run `sh start.sh` from the
repository root with the host-provided `PORT`, and use `/health` as the health path.
Hatchable does not provide a documented Uvicorn start-command setting.

## Check the draft, then the live URL

- `/`: centered FinNews AI masthead, cream paper, navy square buttons.
- `/health` and `/api/health`: HTTP 200 JSON with `status: "ok"`.
- `/api/news?q=finance&page_size=1`: HTTP 200, article array, `mode: "demo"` or
  `"live"`. Only `live` proves NewsAPI access.
- `/static/style.css?v=classic-2` and `/static/app.js?v=classic-2`: HTTP 200.
- Click **Simplify with AI** and **Summarize briefing**. Without Groq, explanations
  explicitly say demo; only a real summary with `mode: "live"` proves Groq access.
- Search, select Markets/Business/Economy/Technology, refresh, and check a mobile viewport.

## Changelog

Recovered the unmerged repair; restored news fetching and package imports; added
PORT-aware startup and health checks; removed public Python duplicates; served
HTML/assets from FastAPI; completed classic editorial styling; added cache-busted
assets, demo banner, batch summaries, and stale-response protection.

References: [Hatchable structure](https://hatchable.com/docs/developers/project-structure),
[API proxy](https://hatchable.com/docs/developers/sdk#api),
[deployment and promotion](https://hatchable.com/docs/developers/import-export).
