import assert from "node:assert/strict";
import { test } from "node:test";
import { api } from "hatchable";
import * as health from "../api/health.js";
import * as news from "../api/news.js";
import * as summarize from "../api/summarize.js";

function response() {
  return {
    statusCode: 200,
    status(code) { this.statusCode = code; return this; },
    json(data) { this.body = data; return this; },
  };
}

function mockProvider(t, implementation) {
  return t.mock.method(api, "call", implementation);
}

test("Hatchable route declarations match the frontend contract", () => {
  for (const route of [health, news, summarize]) assert.equal(route.access, "public");
  assert.deepEqual(health.methods, ["GET"]);
  assert.deepEqual(news.methods, ["GET"]);
  assert.deepEqual(summarize.methods, ["POST"]);
});

test("health does not claim live credentials or spend provider quota", async t => {
  const call = mockProvider(t, () => assert.fail("health must not call a provider"));
  const res = await health.default({}, response());
  assert.deepEqual(res.body, { status: "ok", runtime: "hatchable", news_api: null, groq_api: null });
  assert.equal(call.mock.callCount(), 0);
});

test("news uses the configured gateway, normalizes missing fields, and limits results", async t => {
  mockProvider(t, async (name, options) => {
    assert.equal(name, "newsapi");
    assert.deepEqual(options, {
      method: "GET", path: "/everything",
      query: { q: "stock market", pageSize: 1, language: "en", sortBy: "publishedAt" },
    });
    return { status: 200, body: { status: "ok", articles: [
      null, { title: "[Removed]" },
      { title: "Synthetic headline", source: null, description: null },
      { title: "Second headline" },
    ] } };
  });
  const res = await news.default({ query: { q: "stock market", page_size: "1" } }, response());
  assert.equal(res.body.mode, "live");
  assert.equal(res.body.totalResults, 1);
  assert.equal(res.body.articles[0].description, "");
  assert.deepEqual(res.body.articles[0].source, { name: "Unknown" });
});

test("invalid news parameters never reach the provider", async t => {
  mockProvider(t, () => assert.fail("invalid query reached provider"));
  for (const query of [{ q: "" }, { q: " " }, { q: ["finance"] }, { q: "a".repeat(201) },
    { page_size: "0" }, { page_size: "51" }, { page_size: "1.5" }, { page_size: ["1"] }]) {
    assert.equal((await news.default({ query }, response())).statusCode, 422);
  }
});

test("news provider errors are redacted and never silently return demo data", async t => {
  mockProvider(t, async () => { throw new Error("synthetic-secret-do-not-return"); });
  const res = await news.default({}, response());
  assert.equal(res.statusCode, 502);
  assert.ok(!JSON.stringify(res.body).includes("synthetic-secret"));
  assert.equal(res.body.mode, undefined);
});

test("malformed or rejected news responses return 502", async t => {
  let result;
  mockProvider(t, async () => result);
  for (result of [{ status: 401, body: {} }, { status: 200, body: { status: "error" } },
    { status: 200, body: { status: "ok", articles: null } }]) {
    assert.equal((await news.default({}, response())).statusCode, 502);
  }
});

test("unconfigured integrations preserve Hatchable's setup signal", async t => {
  const setup = Object.assign(new Error("Connect the API"), { code: "SetupRequired" });
  mockProvider(t, async () => { throw setup; });
  await assert.rejects(news.default({}, response()), error => error === setup);
  await assert.rejects(summarize.default({ body: { title: "Test" } }, response()), error => error === setup);
});

test("summaries use Groq through the gateway and normalize the response", async t => {
  mockProvider(t, async (name, options) => {
    assert.equal(name, "groq");
    assert.equal(options.path, "/chat/completions");
    assert.equal(options.body.model, "llama-3.3-70b-versatile");
    assert.equal(options.body.messages[1].content.length, 6500);
    assert.deepEqual(options.body.response_format, { type: "json_object" });
    assert.equal(options.headers, undefined);
    return { status: 200, body: { choices: [{ message: { content: '```json\n' + JSON.stringify({
      summary: "Synthetic summary", key_terms: [null, { term: "Inflation", meaning: "Rising prices" }],
      key_takeaways: [null, "Check the source"],
    }) + '\n```' } }] } };
  });
  const res = await summarize.default({ body: { title: "Test", content: "a".repeat(7000) } }, response());
  assert.equal(res.body.mode, "live");
  assert.equal(res.body.summary, "Synthetic summary");
  assert.deepEqual(res.body.key_terms, [{ term: "Inflation", meaning: "Rising prices" }]);
  assert.deepEqual(res.body.key_takeaways, ["Check the source"]);
});

test("invalid or empty articles never spend provider quota", async t => {
  mockProvider(t, () => assert.fail("invalid article reached provider"));
  for (const body of [null, [], "text", { title: 1 }, { content: {} }]) {
    assert.equal((await summarize.default({ body }, response())).statusCode, 422);
  }
  for (const body of [{}, { title: " " }]) {
    assert.equal((await summarize.default({ body }, response())).statusCode, 400);
  }
});

test("malformed AI outputs fail clearly instead of displaying a false live summary", async t => {
  let content;
  mockProvider(t, async () => ({ status: 200, body: { choices: [{ message: { content } }] } }));
  for (content of ["", "not JSON", "null", "[]", '{}', '{"summary":7}']) {
    assert.equal((await summarize.default({ body: { title: "Test" } }, response())).statusCode, 502);
  }
});

test("Groq rejects upstream failures without exposing the provider body", async t => {
  mockProvider(t, async () => ({ status: 429, body: { error: "synthetic-private-details" } }));
  const res = await summarize.default({ body: { title: "Test" } }, response());
  assert.equal(res.statusCode, 502);
  assert.ok(!JSON.stringify(res.body).includes("synthetic-private-details"));
});
