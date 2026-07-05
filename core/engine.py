"""AllureGraph-AI Core Engine

The main engine that wraps ScrapeGraphAI graphs with:
- Unified API interface
- Template system
- LLM provider switching
- Result formatting
- Error handling and retries
"""

import os
import json
import asyncio
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class EngineConfig:
    """Configuration for the AllureGraph engine."""
    llm_provider: str = "openai"  # openai | anthropic | ollama
    llm_model: Optional[str] = None
    temperature: float = 0.1
    max_retries: int = 3
    timeout_seconds: int = 120
    headless: bool = True
    proxy: Optional[str] = None

    @property
    def resolved_model(self) -> str:
        """Resolve the actual model name."""
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-sonnet-4-20250514",
            "ollama": "llama3.1",
        }
        return self.llm_model or defaults.get(self.llm_provider, "gpt-4o-mini")


class AllureGraphEngine:
    """Main scraping engine powering AllureGraph-AI."""

    def __init__(self, llm_provider: str = "openai", llm_model: Optional[str] = None):
        self.config = EngineConfig(
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

    def _get_graph_config(self) -> dict:
        """Build the ScrapeGraphAI graph configuration."""
        config = {
            "llm": {
                "model": f"{self.config.llm_provider}/{self.config.resolved_model}",
                "temperature": self.config.temperature,
            },
            "headless": self.config.headless,
            "verbose": False,
        }

        # Add API keys based on provider
        if self.config.llm_provider == "openai":
            config["llm"]["api_key"] = os.getenv("OPENAI_API_KEY")
        elif self.config.llm_provider == "anthropic":
            config["llm"]["api_key"] = os.getenv("ANTHROPIC_API_KEY")
        elif self.config.llm_provider == "ollama":
            config["llm"]["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        if self.config.proxy:
            config["loader_kwargs"] = {"proxy": {"server": self.config.proxy}}

        return config

    async def smart_scrape(
        self,
        url: str,
        prompt: str,
        output_format: str = "json",
        headless: bool = True,
        proxy: Optional[str] = None,
    ) -> Any:
        """Execute an AI-powered smart scrape on a single URL.

        Uses ScrapeGraphAI's SmartScraperGraph to:
        1. Fetch the page (with Playwright for JS rendering)
        2. Parse and chunk the content
        3. Use LLM to extract exactly what the prompt asks for
        4. Return structured data
        """
        self.config.headless = headless
        self.config.proxy = proxy

        graph_config = self._get_graph_config()

        # Import here to avoid loading heavy deps at startup
        from scrapegraphai.graphs import SmartScraperGraph

        graph = SmartScraperGraph(
            prompt=prompt,
            source=url,
            config=graph_config,
        )

        # Run in thread pool (ScrapeGraphAI is sync)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, graph.run)

        return self._format_output(result, output_format)

    async def search_and_extract(
        self,
        query: str,
        prompt: str,
        max_results: int = 5,
        output_format: str = "json",
    ) -> Any:
        """Search the web and extract structured data from results."""
        graph_config = self._get_graph_config()

        from scrapegraphai.graphs import SearchGraph

        graph = SearchGraph(
            prompt=f"{prompt}\n\nSearch query: {query}",
            config=graph_config,
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, graph.run)

        return self._format_output(result, output_format)

    async def omni_scrape(
        self,
        url: str,
        prompt: str,
        output_format: str = "json",
    ) -> Any:
        """Vision-enabled scraping — uses screenshots + text."""
        graph_config = self._get_graph_config()

        from scrapegraphai.graphs import OmniScraperGraph

        graph = OmniScraperGraph(
            prompt=prompt,
            source=url,
            config=graph_config,
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, graph.run)

        return self._format_output(result, output_format)

    async def depth_search(
        self,
        url: str,
        prompt: str,
        max_depth: int = 2,
        output_format: str = "json",
    ) -> Any:
        """Recursive crawl + extract."""
        graph_config = self._get_graph_config()

        from scrapegraphai.graphs import DepthSearchGraph

        graph = DepthSearchGraph(
            prompt=prompt,
            source=url,
            config=graph_config,
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, graph.run)

        return self._format_output(result, output_format)

    async def generate_scraper(
        self,
        url: str,
        prompt: str,
    ) -> str:
        """Auto-generate a reusable scraper script."""
        graph_config = self._get_graph_config()

        from scrapegraphai.graphs import ScriptCreatorGraph

        graph = ScriptCreatorGraph(
            prompt=prompt,
            source=url,
            config=graph_config,
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, graph.run)

        return result

    def _format_output(self, data: Any, output_format: str) -> Any:
        """Format engine output based on requested format."""
        if output_format == "json":
            return data
        elif output_format == "csv":
            # Convert to CSV-ready format
            if isinstance(data, list):
                return {"rows": data, "format": "csv"}
            return {"rows": [data], "format": "csv"}
        elif output_format == "markdown":
            if isinstance(data, dict):
                lines = [f"| {k} | {v} |" for k, v in data.items()]
                return "\n".join(["| Key | Value |", "|-----|-------|"] + lines)
            return str(data)
        return data


class TemplateEngine:
    """Pre-built scraping templates for common social selling tasks."""

    TEMPLATES = {
        "telegram_channel": {
            "prompt": "Extract all visible information: channel name, description, member count, recent messages (text, date, views, forwards), pinned messages, and any links or media.",
            "graph_type": "smart",
        },
        "instagram_profile": {
            "prompt": "Extract: username, full name, bio, follower count, following count, post count, profile picture URL, recent posts (image, caption, likes, comments, date), highlights, and any links in bio.",
            "graph_type": "omni",  # Uses vision for image posts
        },
        "product_prices": {
            "prompt": "Extract all products with: name, current price, original price (if discounted), discount percentage, availability status, rating, review count, and product URL.",
            "graph_type": "smart",
        },
        "competitor_offers": {
            "prompt": "Extract all offers/plans/pricing: plan name, price, billing period, features included, limitations, CTAs, and any promotional messaging or discounts.",
            "graph_type": "smart",
        },
        "review_aggregator": {
            "prompt": "Extract all reviews: reviewer name, rating (stars), review text, date, verified purchase status, helpful votes, and any images attached.",
            "graph_type": "smart",
        },
        "lead_enrichment": {
            "prompt": "Extract contact and professional information: full name, title, company, email, phone, social media links, location, and any other professional details.",
            "graph_type": "smart",
        },
        "content_research": {
            "prompt": "Extract content performance data: title, author, publish date, engagement metrics (likes, shares, comments), word count, topics/tags, and key takeaways.",
            "graph_type": "search",
        },
        "x_profile": {
            "prompt": "Extract: display name, handle, bio, follower/following counts, join date, location, recent tweets (text, likes, retweets, replies, date), pinned tweet, and any links.",
            "graph_type": "smart",
        },
    }

    @classmethod
    def get_template(cls, slug: str) -> Optional[dict]:
        """Get a template by slug."""
        return cls.TEMPLATES.get(slug)

    @classmethod
    def list_templates(cls) -> list[str]:
        """List all available template slugs."""
        return list(cls.TEMPLATES.keys())

    @classmethod
    async def execute_template(
        cls,
        slug: str,
        url: str,
        engine: AllureGraphEngine,
        output_format: str = "json",
    ) -> Any:
        """Execute a pre-built template."""
        template = cls.get_template(slug)
        if not template:
            raise ValueError(f"Template '{slug}' not found")

        graph_type = template["graph_type"]
        prompt = template["prompt"]

        if graph_type == "smart":
            return await engine.smart_scrape(url, prompt, output_format)
        elif graph_type == "omni":
            return await engine.omni_scrape(url, prompt, output_format)
        elif graph_type == "search":
            return await engine.search_and_extract(url, prompt, output_format=output_format)
        else:
            return await engine.smart_scrape(url, prompt, output_format)
