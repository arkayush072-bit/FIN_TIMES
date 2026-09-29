// Shared, dependency-free helpers for Hatchable's JavaScript runtime.
export const SUMMARY_PROMPT = `You are FinNews AI, a financial news simplification assistant.
Explain only the supplied article. Never invent facts, figures, quotes, or causes.
Preserve the article's numbers and names. Explain jargon in simple language.
Do not give personalized investment advice or tell readers to buy, sell, or hold.
Do not predict prices or market outcomes. Say when the article lacks information.
Return ONLY a JSON object with these fields:
summary (2-4 sentences), what_happened, why_it_matters, beginner_explanation,
key_terms (an array of objects with term and meaning strings),
key_takeaways (an array of strings). Keep the response concise.`;

export function text(value) {
  return typeof value === "string" ? value : "";
}

export function normalizeArticles(items, pageSize) {
  if (!Array.isArray(items)) throw new Error("Invalid article list");
  return items
    .filter(item => text(item?.title) && item.title !== "[Removed]")
    .slice(0, pageSize)
    .map(item => ({
      title: item.title,
      description: text(item.description),
      content: text(item.content),
      url: text(item.url),
      urlToImage: text(item.urlToImage),
      publishedAt: text(item.publishedAt),
      source: { name: text(item.source?.name) || "Unknown" },
    }));
}

export function parseSummary(content) {
  const clean = text(content).trim().replace(/^```(?:json)?\s*/i, "").replace(/```$/, "").trim();
  const data = JSON.parse(clean);
  if (!data || Array.isArray(data) || typeof data !== "object" || !text(data.summary).trim()) {
    throw new Error("Invalid summary");
  }
  return {
    mode: "live",
    summary: data.summary,
    what_happened: text(data.what_happened) || "Not available.",
    why_it_matters: text(data.why_it_matters) || "Not available.",
    beginner_explanation: text(data.beginner_explanation) || "Not available.",
    key_terms: Array.isArray(data.key_terms)
      ? data.key_terms.filter(item => text(item?.term)).map(item => ({
          term: item.term, meaning: text(item.meaning),
        })) : [],
    key_takeaways: Array.isArray(data.key_takeaways)
      ? data.key_takeaways.filter(item => text(item)) : [],
  };
}

export function providerError(error, res, provider) {
  // Let Hatchable's built-in setup flow handle an unconnected integration.
  if (error?.code === "SetupRequired") throw error;
  // Provider errors may contain credentials or request details; keep them private.
  return res.status(502).json({
    detail: `${provider} request failed. Check the connection and quota in Hatchable Setup, then retry.`,
  });
}

export const DEMO_ARTICLES = [
  {
    "title": "Demo: Understanding interest rates",
    "description": "This fictional example explores how a change in borrowing costs can affect household budgets and business investment.",
    "source": {
      "name": "FinNews demo"
    }
  },
  {
    "title": "Demo: Reading a company's earnings report",
    "description": "In this fictional example, a company reports higher revenue but lower profit because its operating costs increased.",
    "source": {
      "name": "FinNews demo"
    }
  },
  {
    "title": "Demo: What inflation means for a budget",
    "description": "This fictional example shows how rising prices reduce the amount of goods and services a household can buy with the same income.",
    "source": {
      "name": "FinNews demo"
    }
  }
];

export function demoSummary(article) {
  return {
    mode: "demo",
    summary: text(article.description) || text(article.content).slice(0, 360) || text(article.title),
    what_happened: "This sample repeats the supplied article text without AI analysis.",
    why_it_matters: "Read the original source for context and exact figures.",
    beginner_explanation: "A live AI explanation is not available in demo mode.",
    key_terms: [],
    key_takeaways: ["Verify information with the original source.", "This is not investment advice."],
  };
}
