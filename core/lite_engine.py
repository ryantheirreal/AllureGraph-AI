"""AllureGraph-AI — Lite Engine

Lightweight scraping engine for Render free tier (no Playwright/ScrapeGraphAI).
Uses httpx + BeautifulSoup + LLM for extraction.
Full engine activates on paid tier with Playwright.
"""

import os
import json
import httpx
from bs4 import BeautifulSoup
from typing import Any, Optional


class LiteEngine:
    """Lightweight scraper — httpx + BS4 + LLM extraction."""

    def __init__(self, llm_provider: str = "gemini", llm_model: Optional[str] = None):
        self.llm_provider = llm_provider
        self.llm_model = llm_model or "gemini-1.5-flash"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
        }

    async def scrape(self, url: str, prompt: str, **kwargs) -> Any:
        """Fetch URL, clean HTML, extract with LLM."""
        html = await self._fetch(url)
        if not html:
            return {"error": "Failed to fetch URL"}

        text = self._clean_html(html)
        result = await self._extract_with_llm(text, prompt, url)
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
        """Fetch URL content with httpx."""
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                return resp.text
        except Exception as e:
            return None

    def _clean_html(self, html: str) -> str:
        """Extract readable text from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Limit to ~8000 chars for LLM context
        if len(text) > 8000:
            text = text[:8000] + "\n...[truncated]"

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
