"""AllureGraph-AI — Lite Engine

Lightweight scraping engine for Render free tier (no Playwright/ScrapeGraphAI).
Uses httpx + BeautifulSoup + LLM for extraction.
Full engine activates on paid tier with Playwright.
"""

import os
import json
import httpx
import asyncio
import time
import random
import ipaddress
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Any, Optional


# Common user agents for rotation
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]


def _is_blocked_ip(hostname: str) -> bool:
    """Return True if hostname resolves to an internal/private IP (SSRF guard)."""
    blocked_prefixes = (
        "127.",
        "10.",
        "192.168.",
    )
    blocked_ranges = ("172.16.", "172.17.", "172.18.", "172.19.", "172.20.",
                      "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
                      "172.26.", "172.27.", "172.28.", "172.29.", "172.30.",
                      "172.31.")
    if hostname.startswith(blocked_prefixes) or hostname.startswith(blocked_ranges):
        return True
    try:
        ip = ipaddress.ip_address(hostname)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


class LiteEngine:
    """Lightweight scraper — httpx + BS4 + LLM extraction."""

    def __init__(self, llm_provider: str = "gemini", llm_model: Optional[str] = None):
        self.llm_provider = llm_provider
        self.llm_model = llm_model or "gemini-1.5-flash"
        self.base_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
        }
        # In-memory cache: {cache_key: (timestamp, result)} — TTL = 1 hour
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl_seconds: int = 3600

    def _random_headers(self) -> dict:
        """Build headers with a randomly rotated User-Agent."""
        return {**self.base_headers, "User-Agent": random.choice(_USER_AGENTS)}

    def _cache_get(self, key: str) -> Optional[Any]:
        """Return cached value if present and not expired."""
        entry = self._cache.get(key)
        if not entry:
            return None
        ts, value = entry
        if (time.time() - ts) > self._cache_ttl_seconds:
            self._cache.pop(key, None)
            return None
        return value

    def _cache_set(self, key: str, value: Any) -> None:
        """Store a value in cache with current timestamp."""
        self._cache[key] = (time.time(), value)

    async def scrape(self, url: str, prompt: str, **kwargs) -> Any:
        """Fetch URL, clean HTML, extract with LLM."""
        max_content_length = kwargs.get("max_content_length", 50000)

        cache_key = f"{url}::{prompt}::{max_content_length}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        html = await self._fetch(url)
        if not html:
            return {"error": "Failed to fetch URL"}

        text = self._clean_html(html, max_content_length=max_content_length)
        result = await self._extract_with_llm(text, prompt, url)
        self._cache_set(cache_key, result)
        return result

    async def search(self, query: str, prompt: str, max_results: int = 5) -> Any:
        """Search DuckDuckGo and extract from results."""
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return {"error": "No search results found"}

        context = "\n\n".join([
            f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}"
            for r in results
        ])

        result = await self._extract_with_llm(context, prompt)
        return {"search_results": results, "extracted": result}

    async def _fetch(self, url: str) -> Optional[str]:
        """Fetch URL content with httpx. Retries up to 3 times with exponential backoff."""
        # SSRF protection: reject internal/private addresses
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
        except Exception:
            return None

        if not parsed.scheme.startswith("http"):
            return None
        if _is_blocked_ip(hostname):
            return None

        backoffs = [1, 2, 4]  # seconds
        last_exc: Optional[Exception] = None

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    resp = await client.get(url, headers=self._random_headers())
                    resp.raise_for_status()
                    return resp.text
            except Exception as e:
                last_exc = e
                if attempt < len(backoffs):
                    await asyncio.sleep(backoffs[attempt])

        return None

    def _clean_html(self, html: str, max_content_length: int = 50000) -> str:
        """Extract readable text from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Limit to caller-configured max chars (default 50000)
        if len(text) > max_content_length:
            text = text[:max_content_length] + "\n...[truncated]"

        return text

    async def _extract_with_llm(self, text: str, prompt: str, url: str = "") -> Any:
        """Use Gemini LLM to extract structured data from text."""
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            # Fallback: return raw text chunks
            return {"raw_text": text[:2000], "note": "Set GEMINI_API_KEY for AI extraction"}

        user_msg = f"""You are a data extraction AI. Given webpage content, extract exactly what the user asks for.
Return valid JSON only. Be precise and structured.

URL: {url}

Page content:
{text}

Extraction task: {prompt}

Return the extracted data as valid JSON."""

        try:
            endpoint = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.llm_model}:generateContent?key={api_key}"
            )
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    endpoint,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {"parts": [{"text": user_msg}]}
                        ],
                        "generationConfig": {
                            "temperature": 0.1,
                            "responseMimeType": "application/json",
                        },
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_response": content}
        except Exception as e:
            return {"error": str(e)}
