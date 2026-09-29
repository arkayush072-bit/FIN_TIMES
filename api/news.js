import { api } from "hatchable";
import { DEMO_ARTICLES, normalizeArticles, providerError } from "lib/finnews.js";

export const access = "public";
export const methods = ["GET"];

export default async function news(req, res) {
  const query = req.query?.q ?? "finance";
  const rawSize = req.query?.page_size ?? "12";
  const pageSize = Number(rawSize);
  if (typeof query !== "string" || !query.trim() || query.length > 200 ||
      !["string", "number"].includes(typeof rawSize) ||
      !Number.isInteger(pageSize) || pageSize < 1 || pageSize > 50) {
    return res.status(422).json({ detail: "Use a query of 1–200 characters and page_size of 1–50." });
  }

  try {
    const result = await api.call("newsapi", {
      method: "GET",
      path: "/everything",
      query: { q: query, pageSize, language: "en", sortBy: "publishedAt" },
    });
    if (result.status < 200 || result.status >= 300 || result.body?.status !== "ok") {
      throw new Error("NewsAPI rejected the request");
    }
    const articles = normalizeArticles(result.body.articles, pageSize);
    return res.json({ status: "ok", totalResults: articles.length, articles, mode: "live" });
  } catch (error) {
    if (error?.code === "SetupRequired") {
      const articles = normalizeArticles(DEMO_ARTICLES, pageSize);
      return res.json({ status: "ok", totalResults: articles.length, articles, mode: "demo" });
    }
    return providerError(error, res, "NewsAPI");
  }
}
