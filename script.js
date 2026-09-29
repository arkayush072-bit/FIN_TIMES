(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------

  const state = {
    category: "business",
    searchQuery: "",
    articles: [],
    lastFocusedElement: null,
  };

  // -----------------------------------------------------------------------
  // DOM references
  // -----------------------------------------------------------------------

  const el = {
    demoBanner: document.getElementById("demo-banner"),
    toastRegion: document.getElementById("toast-region"),
    mastheadDate: document.getElementById("masthead-date"),

    navLinks: document.querySelectorAll(".nav-link"),
    filterPills: document.querySelectorAll(".filter-pill"),
    searchForm: document.getElementById("search-form"),
    searchInput: document.getElementById("search-input"),

    fetchBtn: document.getElementById("fetch-news-btn"),
    refreshBtn: document.getElementById("refresh-btn"),

    skeletonGrid: document.getElementById("skeleton-grid"),
    newsGrid: document.getElementById("news-grid"),
    emptyState: document.getElementById("empty-state"),
    errorState: document.getElementById("error-state"),

    modalOverlay: document.getElementById("modal-overlay"),
    modalClose: document.getElementById("modal-close"),
    modalTitle: document.getElementById("modal-title"),
    modalMeta: document.getElementById("modal-meta"),
    modalLoading: document.getElementById("modal-loading"),
    modalContent: document.getElementById("modal-content"),
    modalError: document.getElementById("modal-error"),
    modalReadOriginal: document.getElementById("modal-read-original"),

    summarySummary: document.getElementById("summary-summary"),
    summaryWhatHappened: document.getElementById("summary-what-happened"),
    summaryWhyMatters: document.getElementById("summary-why-matters"),
    summaryKeyTerms: document.getElementById("summary-key-terms"),
    summaryTakeaways: document.getElementById("summary-takeaways"),
    summaryBeginner: document.getElementById("summary-beginner"),
  };

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------

  function init() {
    renderMastheadDate();
    bindEvents();
    renderSkeletons(6);
    fetchNews();
  }

  function renderMastheadDate() {
    const today = new Date();
    const formatted = today.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    el.mastheadDate.textContent = formatted;
  }

  function bindEvents() {
    el.fetchBtn.addEventListener("click", () => fetchNews());
    el.refreshBtn.addEventListener("click", () => fetchNews());

    el.navLinks.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        setCategory(link.dataset.category, link);
      });
    });

    el.filterPills.forEach((pill) => {
      pill.addEventListener("click", () => {
        const category = pill.dataset.category === "all" ? "business" : pill.dataset.category;
        setCategory(category, pill, pill.dataset.category === "all");
      });
    });

    el.searchForm.addEventListener("submit", (e) => e.preventDefault());
    el.searchInput.addEventListener("input", debounce(onSearchInput, 300));

    el.modalClose.addEventListener("click", closeModal);
    el.modalOverlay.addEventListener("click", (e) => {
      if (e.target === el.modalOverlay) closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !el.modalOverlay.hidden) closeModal();
    });
  }

  function setCategory(category, activeEl, isAll) {
    state.category = category;
    state.searchQuery = "";
    el.searchInput.value = "";

    el.navLinks.forEach((l) => l.classList.remove("active"));
    el.filterPills.forEach((p) => p.classList.remove("active"));

    if (activeEl && activeEl.classList.contains("nav-link")) {
      activeEl.classList.add("active");
      const matchingPill = Array.from(el.filterPills).find(
        (p) => p.dataset.category === (isAll ? "all" : category)
      );
      if (matchingPill) matchingPill.classList.add("active");
    } else if (activeEl) {
      activeEl.classList.add("active");
      const matchingLink = Array.from(el.navLinks).find((l) => l.dataset.category === category);
      if (matchingLink) matchingLink.classList.add("active");
    }

    fetchNews();
  }

  function onSearchInput() {
    const query = el.searchInput.value.trim();
    state.searchQuery = query;
    if (query) {
      searchNews(query);
    } else {
      fetchNews();
    }
  }

  // -----------------------------------------------------------------------
  // API calls
  // -----------------------------------------------------------------------

  async function fetchNews() {
    showLoadingState();
    try {
      const url = `/api/news?category=${encodeURIComponent(state.category)}&page=1&page_size=12`;
      const resp = await fetch(url);
      const data = await resp.json();
      handleNewsResponse(data);
    } catch (err) {
      showErrorState();
      showToast("Unable to fetch the latest news. Please try again.");
    }
  }

  async function searchNews(query) {
    showLoadingState();
    try {
      const url = `/api/search?q=${encodeURIComponent(query)}&page=1&page_size=12`;
      const resp = await fetch(url);
      const data = await resp.json();
      handleNewsResponse(data);
    } catch (err) {
      showErrorState();
      showToast("Unable to fetch the latest news. Please try again.");
    }
  }

  function handleNewsResponse(data) {
    toggleDemoBanner(Boolean(data.demo_mode));

    if (data.error) {
      showErrorState();
      showToast(data.error);
      return;
    }

    state.articles = data.articles || [];

    if (state.articles.length === 0) {
      showEmptyState();
      return;
    }

    renderNewsGrid(state.articles);
  }

  async function requestSummary(article) {
    const resp = await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: article.title,
        description: article.description || "",
        content: article.content || "",
        url: article.url,
      }),
    });

    if (!resp.ok) {
      let message = "AI summarization is temporarily unavailable.";
      try {
        const errBody = await resp.json();
        if (errBody && errBody.detail) message = errBody.detail;
      } catch (_) {
        /* ignore parse failure, use default message */
      }
      throw new Error(message);
    }

    return resp.json();
  }

  // -----------------------------------------------------------------------
  // Rendering — news grid
  // -----------------------------------------------------------------------

  function showLoadingState() {
    el.errorState.hidden = true;
    el.emptyState.hidden = true;
    el.newsGrid.hidden = true;
    el.skeletonGrid.hidden = false;
  }

  function showErrorState() {
    el.skeletonGrid.hidden = true;
    el.newsGrid.hidden = true;
    el.emptyState.hidden = true;
    el.errorState.hidden = false;
  }

  function showEmptyState() {
    el.skeletonGrid.hidden = true;
    el.newsGrid.hidden = true;
    el.errorState.hidden = true;
    el.emptyState.hidden = false;
  }

  function renderSkeletons(count) {
    el.skeletonGrid.innerHTML = "";
    for (let i = 0; i < count; i++) {
      const card = document.createElement("div");
      card.className = "skeleton-card";
      card.innerHTML = `
        <div class="skeleton-block skeleton-image"></div>
        <div class="skeleton-block skeleton-line"></div>
        <div class="skeleton-block skeleton-line short"></div>
      `;
      el.skeletonGrid.appendChild(card);
    }
  }

  function renderNewsGrid(articles) {
    el.skeletonGrid.hidden = true;
    el.errorState.hidden = true;
    el.emptyState.hidden = true;
    el.newsGrid.hidden = false;
    el.newsGrid.innerHTML = "";

    articles.forEach((article) => {
      el.newsGrid.appendChild(buildCard(article));
    });
  }

  function buildCard(article) {
    const card = document.createElement("article");
    card.className = "news-card";

    if (article.image_url) {
      const imageWrap = document.createElement("div");
      imageWrap.className = "card-image-wrap";
      const img = document.createElement("img");
      img.src = article.image_url;
      img.alt = "";
      img.loading = "lazy";
      img.addEventListener("error", () => imageWrap.remove());
      imageWrap.appendChild(img);
      card.appendChild(imageWrap);
    }

    const category = document.createElement("p");
    category.className = "card-category";
    category.textContent = state.category === "business" ? "Business" : capitalize(state.category);

    const title = document.createElement("h3");
    title.className = "card-title";
    title.textContent = article.title;

    const meta = document.createElement("p");
    meta.className = "card-meta";
    meta.textContent = [article.source, formatRelativeTime(article.published_at)]
      .filter(Boolean)
      .join(" \u2014 ");

    const description = document.createElement("p");
    description.className = "card-description";
    description.textContent = article.description || "";

    const simplifyBtn = document.createElement("button");
    simplifyBtn.className = "card-simplify-btn";
    simplifyBtn.textContent = "Simplify with AI";
    simplifyBtn.addEventListener("click", () => openModal(article));

    card.appendChild(category);
    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(description);
    card.appendChild(simplifyBtn);

    return card;
  }

  // -----------------------------------------------------------------------
  // Modal / summarize flow
  // -----------------------------------------------------------------------

  function openModal(article) {
    state.lastFocusedElement = document.activeElement;

    el.modalTitle.textContent = article.title;
    el.modalMeta.textContent = [article.source, formatRelativeTime(article.published_at)]
      .filter(Boolean)
      .join(" \u2014 ");
    el.modalReadOriginal.href = article.url;

    el.modalContent.hidden = true;
    el.modalError.hidden = true;
    el.modalLoading.hidden = false;

    el.modalOverlay.hidden = false;
    el.modalClose.focus();
    document.body.style.overflow = "hidden";

    requestSummary(article)
      .then((summary) => {
        if (summary.demo_mode) toggleDemoBanner(true);
        renderSummary(summary);
      })
      .catch((err) => {
        el.modalLoading.hidden = true;
        el.modalError.hidden = false;
        el.modalError.textContent = err.message || "AI summarization is temporarily unavailable.";
        showToast(err.message || "AI summarization is temporarily unavailable.");
      });
  }

  function renderSummary(summary) {
    el.modalLoading.hidden = true;
    el.modalContent.hidden = false;

    el.summarySummary.textContent = summary.summary;
    el.summaryWhatHappened.textContent = summary.what_happened;
    el.summaryWhyMatters.textContent = summary.why_it_matters;
    el.summaryBeginner.textContent = summary.beginner_explanation;

    el.summaryKeyTerms.innerHTML = "";
    (summary.key_terms || []).forEach((kt) => {
      const dt = document.createElement("dt");
      dt.textContent = kt.term;
      const dd = document.createElement("dd");
      dd.textContent = kt.meaning;
      el.summaryKeyTerms.appendChild(dt);
      el.summaryKeyTerms.appendChild(dd);
    });

    el.summaryTakeaways.innerHTML = "";
    (summary.key_takeaways || []).forEach((point) => {
      const li = document.createElement("li");
      li.textContent = point;
      el.summaryTakeaways.appendChild(li);
    });

    if (summary.cached) {
      showToast("Loaded from cache.", "success");
    }
  }

  function closeModal() {
    el.modalOverlay.hidden = true;
    document.body.style.overflow = "";
    if (state.lastFocusedElement) {
      state.lastFocusedElement.focus();
    }
  }

  // -----------------------------------------------------------------------
  // Toasts
  // -----------------------------------------------------------------------

  function showToast(message, kind) {
    const toast = document.createElement("div");
    toast.className = "toast" + (kind === "success" ? " toast-success" : "");
    toast.textContent = message;
    el.toastRegion.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  function toggleDemoBanner(show) {
    el.demoBanner.hidden = !show;
  }

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------

  function debounce(fn, delay) {
    let timer = null;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function formatRelativeTime(isoString) {
    if (!isoString) return "";
    const then = new Date(isoString);
    if (isNaN(then.getTime())) return "";
    const diffMs = Date.now() - then.getTime();
    const diffMins = Math.round(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.round(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.round(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return then.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
