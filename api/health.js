export const access = "public";
export const methods = ["GET"];

export default async function health(req, res) {
  // Gateway credentials are opaque. Real readiness is established by a news or
  // summary request, not by reading secrets or making paid calls on page load.
  return res.json({ status: "ok", runtime: "hatchable", news_api: null, groq_api: null });
}
