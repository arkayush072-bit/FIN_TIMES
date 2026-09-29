/* ============================================================
       FINNEWS AI - FRONTEND (talks to FastAPI backend)
       Backend endpoints:
         GET  /api/news?q=finance&page_size=12
         POST /api/summarize  { title, description, content, url }
         GET  /api/health
       ============================================================ */

    // The dashboard and API are served by the same application.
    const API_BASE = "";

    let articles = [];
    let activeQuery = "finance";
    let searchTimer = null;
    let summaryOpener = null;
    let newsRequest = null;
    let summaryRequestId = 0;

    const $ = (id) => document.getElementById(id);

    function setStatus(message, type = "") {
      $("status").textContent = message;
      $("status").className = "status " + type;
    }

    function escapeHtml(value = "") {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function truncate(text, max = 700) {
      if (!text) return "";
      return text.length > max ? text.slice(0, max) + "..." : text;
    }

    function formatDate(dateString) {
      if (!dateString) return "Unknown date";
      const date = new Date(dateString);
      if (Number.isNaN(date.getTime())) return "Unknown date";
      return date.toLocaleString([], {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    }

    function imageForArticle(article) {
      if (article.urlToImage) return article.urlToImage;
      return "/static/news-placeholder.svg";
    }

    function renderSkeletons() {
      $("newsGrid").innerHTML = Array.from({ length: 6 })
        .map(() => `<div class="skeleton"></div>`)
        .join("");
    }

    function renderArticles(list = articles) {
      $("articleCount").textContent = list.length;

      if (!list.length) {
        $("newsGrid").innerHTML = `
          <div class="empty">
            <h3>No financial news found</h3>
            <p>Try another search term or category.</p>
          </div>`;
        return;
      }

      $("newsGrid").innerHTML = list.map((article, index) => `
        <article class="card">
          <img
            class="card-image"
            src="${escapeHtml(imageForArticle(article))}"
            alt=""
            loading="lazy"
            onerror="this.onerror=null; this.src='/static/news-placeholder.svg'"
          />

          <div class="card-body">
            <div class="meta">
              <span class="source">${escapeHtml(article.source?.name || "Unknown source")}</span>
              <span>•</span>
              <span>${escapeHtml(formatDate(article.publishedAt))}</span>
            </div>

            <h3>${escapeHtml(article.title || "Untitled article")}</h3>

            <p>${escapeHtml(truncate(article.description || article.content || "No description available.", 180))}</p>

            <div class="card-actions">
              <button class="ai-btn" data-ai-index="${index}">Simplify with AI →</button>
              ${/^https?:\/\//i.test(article.url || "") ? `
                <a class="article-btn"
                   href="${escapeHtml(article.url)}"
                   target="_blank"
                   rel="noopener noreferrer">Read Original</a>
              ` : '<span class="article-btn">Sample article</span>'}
            </div>
          </div>
        </article>
      `).join("");

      document.querySelectorAll("[data-ai-index]").forEach(btn => {
        btn.addEventListener("click", () => {
          const index = Number(btn.dataset.aiIndex);
          openSummary(articles[index]);
        });
      });
    }

    // ---------- Frontend summary cache (per browser) ----------
    function cacheKey(article) {
      const raw = article.url || article.title || "";
      return "finnews_summary_classic2_" + JSON.stringify([raw, article.description, article.content]);
    }

    function getCachedSummary(article) {
      try {
        const raw = localStorage.getItem(cacheKey(article));
        if (!raw) return null;
        const item = JSON.parse(raw);
        // 10 min TTL
        if (Date.now() - item.time > 10 * 60 * 1000) {
          localStorage.removeItem(cacheKey(article));
          return null;
        }
        return item.data;
      } catch {
        return null;
      }
    }

    function setCachedSummary(article, data) {
      try {
        localStorage.setItem(cacheKey(article), JSON.stringify({
          time: Date.now(),
          data
        }));
      } catch { /* quota / private mode */ }
    }

    // ---------- Backend calls ----------
    async function checkBackendHealth() {
      try {
        const res = await fetch(`${API_BASE}/api/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        // Mode is also updated inside fetchNews(), but this gives early feedback
        if (data.news_api === false) {
          $("modeLabel").textContent = "Demo";
        }
      } catch {
        $("modeLabel").textContent = "Offline";
        setStatus("The news service is temporarily unavailable. Please retry.", "error");
      }
    }

    async function fetchNews(query = activeQuery) {
      clearTimeout(searchTimer);
      newsRequest?.abort();
      const request = new AbortController();
      newsRequest = request;
      activeQuery = query;
      $("batchBtn").disabled = true;
      $("demoBanner").hidden = true;
      document.querySelectorAll(".filter").forEach(button => {
        const active = button.dataset.query === query;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", String(active));
      });
      renderSkeletons();
      setStatus("Fetching news...");

      try {
        const params = new URLSearchParams({
          q: query,
          page_size: "12",
        });

        const res = await fetch(`${API_BASE}/api/news?${params.toString()}`, { signal: request.signal });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error ${res.status}`);
        }

        const data = await res.json();
        if (request !== newsRequest) return;
        articles = data.articles || [];
        $("demoBanner").hidden = data.mode !== "demo";
        $("batchBtn").disabled = !articles.length;

        $("modeLabel").textContent = data.mode === "live" ? "Live" : "Demo";

        renderArticles();
        setStatus(
          data.mode === "live"
            ? `${articles.length} articles loaded`
            : "Demo mode — showing sample articles",
          "ok"
        );
      } catch (error) {
        console.error(error);
        if (request !== newsRequest || error.name === "AbortError") return;
        $("modeLabel").textContent = "Offline";
        articles = [];
        renderArticles();
        setStatus("Could not fetch news", "error");
        $("newsGrid").innerHTML = `
          <div class="empty">
            <h3>Backend connection failed</h3>
            <p>${escapeHtml(error.message || "Please retry in a moment.")}</p>
            <button class="primary-btn" style="margin-top:12px" id="retryBtn">Try Again</button>
          </div>`;
        $("retryBtn").addEventListener("click", () => fetchNews(activeQuery));
      }
    }

    async function summarizeWithBackend(article) {
      const res = await fetch(`${API_BASE}/api/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: article.title || "",
          description: article.description || "",
          content: article.content || "",
          url: article.url || "",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }
      return await res.json();
    }

    function showSummary(title) {
      summaryOpener = document.activeElement;
      $("summaryModal").classList.add("show");
      document.body.style.overflow = "hidden";
      $("closeSummary").focus();
      $("summaryTitle").textContent = title;
      $("aiContent").innerHTML = `<div class="empty">Preparing your briefing…</div>`;

    }

    async function openSummary(article) {
      const requestId = ++summaryRequestId;
      showSummary(article.title || "Financial News");
      const cached = getCachedSummary(article);

      try {
        const summary = cached || await summarizeWithBackend(article);
        if (!cached && summary.mode === "live") setCachedSummary(article, summary);
        if (requestId === summaryRequestId) renderSummary(summary);
      } catch (error) {
        console.error(error);
        if (requestId !== summaryRequestId) return;
        $("aiContent").innerHTML = `
          <div class="ai-block">
            <h4>AI summarization unavailable</h4>
            <p>${escapeHtml(error.message || "Please try again later.")}</p>
          </div>
          <div class="notice">
            You can still read the original article using the button on the news card.
          </div>`;
      }
    }

    function renderSummary(data) {
      const terms = Array.isArray(data.key_terms)
        ? data.key_terms.map(item => `
            <span class="term">
              <strong>${escapeHtml(item.term || "")}</strong> — ${escapeHtml(item.meaning || "")}
            </span>
          `).join("")
        : "";

      const takeaways = Array.isArray(data.key_takeaways)
        ? `<ul>${data.key_takeaways.map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>`
        : "";

      $("aiContent").innerHTML = `
        ${data.mode === "demo" ? '<div class="notice">Demo explanation — this is a sample, not an AI-generated analysis.</div>' : ""}
        <div class="ai-block">
          <h4>Short Summary</h4>
          <p>${escapeHtml(data.summary || "No summary available.")}</p>
        </div>

        <div class="ai-block">
          <h4>What Happened?</h4>
          <p>${escapeHtml(data.what_happened || "Not available.")}</p>
        </div>

        <div class="ai-block">
          <h4>Why It Matters</h4>
          <p>${escapeHtml(data.why_it_matters || "Not available.")}</p>
        </div>

        <div class="ai-block">
          <h4>Key Financial Terms</h4>
          ${terms || "<p>No specific terms identified.</p>"}
        </div>

        <div class="ai-block">
          <h4>Key Takeaways</h4>
          ${takeaways || "<p>No takeaways available.</p>"}
        </div>

        <div class="ai-block">
          <h4>Beginner Explanation</h4>
          <p>${escapeHtml(data.beginner_explanation || "Not available.")}</p>
        </div>
      `;
    }

    async function openBatchSummary() {
      const requestId = ++summaryRequestId;
      const briefing = [...articles];
      showSummary("Your briefing, simplified");
      $("aiContent").textContent = "Preparing the briefing…";
      const results = [];
      // Sequential calls avoid a burst of provider requests. Closing stops the queue.
      for (const article of briefing) {
        if (requestId !== summaryRequestId) return;
        try {
          const cached = getCachedSummary(article);
          const summary = cached || await summarizeWithBackend(article);
          if (!cached && summary.mode === "live") setCachedSummary(article, summary);
          results.push(`<section class="batch-item"><h3>${escapeHtml(article.title)}</h3>
            ${summary.mode === "demo" ? '<p class="notice">Demo explanation — sample text, not AI analysis.</p>' : ''}
            <p>${escapeHtml(summary.summary)}</p></section>`);
        } catch {
          results.push(`<section class="batch-item"><h3>${escapeHtml(article.title)}</h3>
            <p>Summary unavailable for this article. Please try its Simplify button again.</p></section>`);
        }
        if (requestId !== summaryRequestId) return;
        $("aiContent").innerHTML = `<p>${results.length} of ${briefing.length} articles processed</p>` + results.join("");
      }
    }
    $("batchBtn").addEventListener("click", openBatchSummary);

    // ---------- Event wiring ----------
    function closeSummary() {
      summaryRequestId++;
      $("summaryModal").classList.remove("show");
      document.body.style.overflow = "";
      if (summaryOpener?.isConnected) summaryOpener.focus();
    }
    $("closeSummary").addEventListener("click", closeSummary);

    $("refreshBtn").addEventListener("click", () => fetchNews(activeQuery));
    $("latestBtn").addEventListener("click", () => fetchNews(activeQuery));

    $("searchBtn").addEventListener("click", () => {
      const q = $("searchInput").value.trim();
      if (q) fetchNews(q);
    });

    $("searchInput").addEventListener("keydown", event => {
      if (event.key === "Enter") {
        const q = event.target.value.trim();
        if (q) fetchNews(q);
      }
    });

    $("searchInput").addEventListener("input", event => {
      clearTimeout(searchTimer);
      const q = event.target.value.trim();
      if (!q) { fetchNews("finance"); return; }
      if (q.length < 3) return;
      searchTimer = setTimeout(() => fetchNews(q), 700);
    });

    document.querySelectorAll(".filter").forEach(button => {
      button.setAttribute("aria-pressed", String(button.classList.contains("active")));
      button.addEventListener("click", () => {
        document.querySelectorAll(".filter").forEach(b => {
          b.classList.remove("active");
          b.setAttribute("aria-pressed", "false");
        });
        button.classList.add("active");
        button.setAttribute("aria-pressed", "true");
        $("searchInput").value = "";
        fetchNews(button.dataset.query);
      });
    });

    // Close summary modal by backdrop click or Escape
    window.addEventListener("click", (event) => {
      if (event.target === $("summaryModal")) closeSummary();
    });

    window.addEventListener("keydown", (event) => {
      if (!$("summaryModal").classList.contains("show")) return;
      if (event.key === "Escape") closeSummary();
      // The close button is the dialog's only interactive control.
      if (event.key === "Tab") {
        event.preventDefault();
        $("closeSummary").focus();
      }
    });

    // ---------- Initial load ----------
    const today = new Date();
    $("editionDate").dateTime = today.toISOString().slice(0, 10);
    $("editionDate").textContent = new Intl.DateTimeFormat("en", {
      weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC"
    }).format(today) + " · UTC edition";
    checkBackendHealth();
    fetchNews();
