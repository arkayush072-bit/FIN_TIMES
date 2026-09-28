# Update your FinNews website on Hatchable

**Your website:** https://k6octh.hatchable.site

## What is ready, and what is still needed

The update contains a classic navy-blue and red design, an ivory background,
serif headlines, a responsive layout, and the three API routes used by the new
frontend. The design is running in this coding task's Preview.

The public Hatchable site has **not** been changed by this task. When checked on
28 September 2026, the site loaded, but `/api/health` returned `Function not found`
and listed no deployed API routes. The current live page also uses an older API
contract. Update the frontend **and** the API files together using this guide.

A public website URL identifies the project; it does not grant permission to edit
its Hatchable account. This task currently has no authenticated Hatchable connection.

## Step 1 — Open the existing project

1. Open [the Hatchable console](https://hatchable.com/console).
2. Sign in to the account that owns `k6octh.hatchable.site`.
3. Find the existing project whose website address matches that URL.
4. Keep it open in a browser tab. The display name may differ from `FinNews AI`.

**Check:** you can see your project in the console. If you cannot, use the account
that originally created it or ask the owner to give your account editing access.

## Step 2 — Connect an editor to Hatchable

If you already use a ChatGPT or Claude chat connected to Hatchable, use that chat.
Otherwise:

1. Open [Hatchable's connection page](https://hatchable.com/start).
2. Choose the AI editor you use, such as ChatGPT or Claude.
3. Follow its connection/sign-in flow and approve access with the **same Hatchable
   account** from Step 1.
4. In that connected chat, send:

> Find my existing Hatchable project serving https://k6octh.hatchable.site.
> Read its files and tell me the project ID before changing it.

**Check:** the connected editor finds your existing project. If it cannot list your
projects, finish connecting Hatchable before continuing. This does not require
pasting your Hatchable token into a conversation.

## Step 3 — Apply the prepared update to that project

1. Download `finnews-hatchable-update.zip` from this task's Outputs.
2. Attach it to the Hatchable-connected chat. If your editor cannot open zip
   attachments, unzip it locally and attach the seven source files listed below.
3. Send this message with the files:

> Update my existing Hatchable project serving https://k6octh.hatchable.site
> using the attached FinNews files. Confirm the project ID from that URL first.
> Read the current files, then apply public/index.html,
> public/static/news-placeholder.svg, api/health.js, api/news.js,
> api/summarize.js, and lib/finnews.js. Merge the attached hatchable.toml API
> declarations into the existing manifest, preserving unrelated settings and
> files. Keep the navy-blue and red design. Use Hatchable's API proxy for the
> newsapi and groq integrations; keep credentials out of source and chat.
> Run dry_run_deploy, fix any platform validation errors, and deploy the update
> to this existing project. Report the deployment URL and whether it is a draft.
> Do not create another project or import the zip as a new app.

**Check:** the connected editor reports a successful platform validation and
deployment. The tests run in this coding task use a mock Hatchable SDK and cannot
replace Hatchable's own `dry_run_deploy`.

A GitHub push alone does not deploy this update. Hatchable's zip/GitHub **import**
flow creates another project, so it is not the way to update your existing URL.

## Step 4 — Connect the two provider accounts

After the integration declarations have been applied, open the existing project's
**Setup** page in Hatchable. Connect the APIs named `newsapi` and `groq`.
The exact credential controls can vary with Hatchable's selected authentication
mode; the required settings are:

| Connection | Base URL | Authentication |
| --- | --- | --- |
| `newsapi` | `https://newsapi.org/v2` | API key using `X-Api-Key: YOUR_KEY`, or `Authorization: Bearer YOUR_KEY` |
| `groq` | `https://api.groq.com/openai/v1` | API key using `Authorization: Bearer YOUR_KEY` |

`YOUR_KEY` is a placeholder: enter your own key only into Hatchable's credential
fields. If a field says **API key**, enter the key itself; if the UI separately
asks for an authorization scheme, choose **Bearer**. Do not prefix a key twice.
Do not add provider secrets to `hatchable.toml`, browser JavaScript, or the chat.
The platform's API proxy supplies the headers for each request.

### Get the NewsAPI key

1. Sign in or create an account at [NewsAPI](https://newsapi.org/register).
2. Obtain your API key from your account.
3. Use a plan that permits your intended deployment. NewsAPI explicitly limits
   its free Developer plan to development/testing and excludes staging and
   production. Check [the current plan rules](https://newsapi.org/pricing) before
   enabling it on this published site; this guide does not authorize a purchase.
4. Save the key in Hatchable's `newsapi` connection.

### Get the Groq key

1. Sign in to [Groq's API key page](https://console.groq.com/keys).
2. Create a key for this app and save it in Hatchable's `groq` connection.
3. The app requests `llama-3.3-70b-versatile`. Your account must have access to the
   model and enough quota for a completion.

If these APIs are already connected to this project, check the base URLs and
credential grants before creating replacement keys.

**Check:** both connections are configured. A local Python `.env` file does not
configure the Hatchable app; these are separate runtimes.

## Step 5 — Verify the deployed update

Use the deployment URL reported by the connected editor. If it is a draft, test
there while signed into the project owner's account before promoting it.

Ask the connected editor:

> On the deployment you just created, verify GET /api/health and
> GET /api/news?q=finance&page_size=1. Confirm news returns mode "live" and an
> article. POST that article's title, description, content, and url to
> /api/summarize. Confirm a nonempty summary with mode "live". Report HTTP
> failures without showing credentials. Then check the page's search and
> Simplify with AI button.

For the live URL after promotion, you can also open:

- [API health](https://k6octh.hatchable.site/api/health): expect `status: "ok"`.
  `news_api: null` and `groq_api: null` are intentional here: health checks do not
  inspect gateway-managed secrets or spend API quota.
- [News request](https://k6octh.hatchable.site/api/news?q=finance&page_size=1):
  expect `mode: "live"` and a real article.
- [The dashboard](https://k6octh.hatchable.site): expect the navy/red design,
  **Live** under news source mode, and a working **Simplify with AI** dialog.

## Step 6 — Make the update live

If Hatchable reports a draft, open the project's **History** tab, review that
deployment, and select **Promote to live**. This owner action is part of
Hatchable's deployment flow. If the deployment was already auto-promoted, no
additional promotion is needed.

Reload https://k6octh.hatchable.site and repeat the health/news/page checks above.
If the old page is cached, use a hard refresh (Ctrl+Shift+R on Windows/Linux or
Cmd+Shift+R on macOS).

**Finished means:** the existing URL shows the new design, news is live, and the
AI summary works on a real article. If a step fails, send me the step number and
error text or a screenshot with keys hidden, and I can guide the next fix.

## Common problems

| What you see | What to check |
| --- | --- |
| `Function not found` / HTTP 404 | The matching `api/*.js` routes were not deployed to the URL being tested. Deploy the frontend and backend together. |
| Setup required | Connect the named API in this project's Setup page, or grant this project access to the saved credential. |
| HTTP 401 from a provider | Check the key, header scheme, and base URL in the relevant connection. |
| HTTP 429 | Check provider quota and rate limits; repeated refreshes/searches make additional API calls. |
| News works but summaries fail | Check the `groq` connection, model access, and quota; inspect the project's logs without sharing credentials. |
| The old site remains visible | Confirm which project was updated, whether the deploy is a draft, and whether it was promoted to live. |
| Demo data in local Preview | Expected without local `.env` keys. The prepared Hatchable routes use live providers and report setup/provider errors instead of silently returning demo data. |

## Source files in the bundle

```text
hatchable.toml
api/health.js
api/news.js
api/summarize.js
lib/finnews.js
public/index.html
public/static/news-placeholder.svg
DEPLOYMENT.md  # this guide; not an API route
```

No Python installation, Node installation, or npm build is needed on Hatchable.

References: [Hatchable project structure](https://hatchable.com/docs/developers/project-structure),
[API proxy](https://hatchable.com/docs/developers/sdk#api),
[deployments and promotion](https://hatchable.com/docs/developers/import-export),
[NewsAPI authentication](https://newsapi.org/docs/authentication),
[Groq API compatibility](https://console.groq.com/docs/openai).
