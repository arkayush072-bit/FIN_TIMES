# FinNews AI — repository guide

This repository contains a financial news dashboard and a Python FastAPI backend.
The former Threshold static-site instructions no longer describe this code.

## Setup and startup

Follow README.md. Install requirements.txt in a virtual environment, then run
`PORT=8000 sh start.sh` from the repo root.
The backend serves public/index.html and /api endpoints together. No frontend
build, Node.js packages, or database are needed.

## Files and conventions

- public/index.html and public/static/{style.css,app.js}: vanilla frontend.
- public/static/news-placeholder.svg: local fallback image.
- backend/: canonical Python package; use package-qualified imports.
- backend/services/: provider integrations and credential-free demo behavior.
- tests/: unittest tests with synthetic provider responses.

Keep frontend changes framework-free and preserve the responsive layout.
Keep Python source out of public/. Keep provider keys on the backend; never
commit .env. Preserve demo mode so startup works without provider credentials.
Label sample data and explanations clearly. Retain the educational disclaimer.

## Validation

Run `python -m unittest discover -s tests -v` and `python -m pip check` after
backend or dependency changes. For frontend changes, check the running dashboard
in a browser, including news loading and the summary dialog.

## Hatchable deployment

Hatchable runs the plain JavaScript handlers in api/ and pages/, with shared helpers in
lib/. These implement the same frontend contract as the local Python backend.
Use only the Hatchable SDK and static imports; no npm dependencies or build step.
The newsapi and groq integrations are declared in hatchable.toml. Their keys are
connected by the owner on Hatchable's Setup page and attached by its API proxy;
never put keys in source. Hosted routes use labeled demo data when the API proxy raises SetupRequired; configured provider errors remain errors.
Run `node --import ./tests/hatchable-loader.mjs --test tests/hatchable.test.mjs`
with Node 24+ to test the handler contract with a mock SDK. A real Hatchable
`dry_run_deploy` and deployed API smoke test are still required before claiming
platform readiness. Update the existing project; importing a zip creates a new
project and does not update the old one.

## Visual style

The current dashboard uses a classic newspaper style: ivory paper, navy blue
text/actions, red accents, serif headlines, and fine rules. Colors live in the
:root block in public/static/style.css. Keep keyboard focus visible, category button
states accessible, and the summary dialog keyboard-operable. Preserve the
prefers-reduced-motion override.

Existing Hatchable website: https://k6octh.hatchable.site. Its authenticated
project ID must be resolved through Hatchable before writes; the public hostname
alone is not edit access. See docs/HATCHABLE_GUIDE.md for the owner-facing steps.
