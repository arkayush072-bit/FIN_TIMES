import { api } from "hatchable";
import { SUMMARY_PROMPT, parseSummary, providerError, text } from "lib/finnews.js";

export const access = "public";
export const methods = ["POST"];

export default async function summarize(req, res) {
  const body = req.body;
  if (!body || typeof body !== "object" || Array.isArray(body) ||
      ["title", "description", "content"].some(key => body[key] != null && typeof body[key] !== "string")) {
    return res.status(422).json({ detail: "Supply an article object with string title, description, and content fields." });
  }
  const articleText = [body.title, body.description, body.content]
    .map(text).map(value => value.trim()).filter(Boolean).join("\n\n").slice(0, 6500);
  if (!articleText) {
    return res.status(400).json({ detail: "Article has no content to summarize." });
  }

  try {
    const result = await api.call("groq", {
      method: "POST",
      path: "/chat/completions",
      body: {
        model: "llama-3.3-70b-versatile",
        temperature: 0.2,
        max_tokens: 900,
        response_format: { type: "json_object" },
        messages: [
          { role: "system", content: SUMMARY_PROMPT },
          { role: "user", content: articleText },
        ],
      },
    });
    if (result.status < 200 || result.status >= 300) throw new Error("Groq rejected the request");
    return res.json(parseSummary(result.body?.choices?.[0]?.message?.content));
  } catch (error) {
    return providerError(error, res, "Groq");
  }
}
