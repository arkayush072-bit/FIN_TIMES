"""
Small, dependency-free sanitization helpers.

We deliberately avoid pulling in a full HTML parser for this — the goal is
to strip anything that could execute in a browser (script/iframe tags,
inline event handlers, javascript: URLs) from text that ultimately gets
rendered in the frontend, not to support arbitrary rich HTML.
"""

import re
from urllib.parse import urlparse

_SCRIPT_TAG_RE = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
_IFRAME_TAG_RE = re.compile(r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", re.IGNORECASE | re.DOTALL)
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_ON_ATTR_RE = re.compile(r'on\w+\s*=\s*(".*?"|\'.*?\'|[^\s>]+)', re.IGNORECASE)
_JS_URL_RE = re.compile(r"javascript\s*:", re.IGNORECASE)


def strip_html(text: str) -> str:
    """Remove script/iframe blocks, all remaining tags, event handler
    attributes and javascript: URLs from a string."""
    if not text:
        return ""
    cleaned = _SCRIPT_TAG_RE.sub("", text)
    cleaned = _IFRAME_TAG_RE.sub("", cleaned)
    cleaned = _ON_ATTR_RE.sub("", cleaned)
    cleaned = _JS_URL_RE.sub("", cleaned)
    cleaned = _ANY_TAG_RE.sub("", cleaned)
    return cleaned.strip()


def truncate(text: str, max_chars: int) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "\u2026"  # trailing ellipsis


def is_safe_url(url: str) -> bool:
    """Only allow http(s) URLs; reject javascript:, data:, file:, etc."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def sanitize_article_text(text: str, max_chars: int) -> str:
    """Full pipeline used before article content is sent to the AI service
    or rendered on a card: strip HTML, then truncate."""
    return truncate(strip_html(text or ""), max_chars)
