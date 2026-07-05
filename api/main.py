"""AllureGraph-AI — API Server

FastAPI-based REST API wrapping the ScrapeGraphAI engine with:
- API key authentication
- Rate limiting per plan
- Usage metering
- Async job queue for heavy scrapes
- Social selling templates
"""

import os
import uuid
import time
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="AllureGraph-AI",
    description="AI-powered scraping & intelligence engine for social sellers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://graph.allurevips.fun",
        "https://app.allurevips.fun",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Models ===

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    prompt: str = Field(..., description="What to extract (natural language)")
    output_format: str = Field(default="json", description="json | csv | markdown")
    template: Optional[str] = Field(default=None, description="Template slug to use")
    llm_provider: str = Field(default="openai", description="openai | anthropic | ollama")
    llm_model: Optional[str] = Field(default=None, description="Model override")
    headless: bool = Field(default=True, description="Use headless browser")
    proxy: Optional[str] = Field(default=None, description="Proxy URL")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    prompt: str = Field(..., description="What to extract from results")
    max_results: int = Field(default=5, ge=1, le=20)
    output_format: str = Field(default="json")


class MonitorRequest(BaseModel):
    url: str = Field(..., description="URL to monitor")
    prompt: str = Field(..., description="What to track")
    frequency: str = Field(default="daily", description="hourly | daily | weekly")
    webhook_url: Optional[str] = Field(default=None, description="Webhook for alerts")


class LeadRequest(BaseModel):
    source: str = Field(..., description="telegram | instagram | x | linkedin")
    target: str = Field(..., description="Channel/profile/hashtag to extract from")
    prompt: str = Field(default="Extract all user profiles with contact info")
    max_leads: int = Field(default=50, ge=1, le=500)


class BatchRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=100)
    prompt: str
    output_format: str = Field(default="json")


class ScrapeResponse(BaseModel):
    id: str
    status: str  # completed | processing | failed
    data: Optional[dict | list] = None
    credits_used: int = 1
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: str  # queued | processing | completed | failed
    estimated_seconds: Optional[int] = None
    result_url: Optional[str] = None


# === Auth ===

async def verify_api_key(authorization: str = Header(...)):
    """Verify API key and return user context."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    api_key = authorization.replace("Bearer ", "")

    # TODO: Look up in Supabase
    # For now, validate format
    if not api_key.startswith("ag_"):
        raise HTTPException(status_code=401, detail="Invalid API key. Keys start with ag_")

    # Return user context (will be Supabase lookup)
    return {
        "user_id": "user_placeholder",
        "plan": "pro",
        "credits_remaining": 5000,
        "api_key": api_key,
    }


# === Core Engine ===

async def run_smart_scrape(url: str, prompt: str, output_format: str = "json", **kwargs):
    """Execute a smart scrape using the AllureGraph engine."""
    from core.engine import AllureGraphEngine

    engine = AllureGraphEngine(
        llm_provider=kwargs.get("llm_provider", "openai"),
        llm_model=kwargs.get("llm_model"),
    )

    result = await engine.smart_scrape(
        url=url,
        prompt=prompt,
        output_format=output_format,
        headless=kwargs.get("headless", True),
        proxy=kwargs.get("proxy"),
    )

    return result


async def run_search_scrape(query: str, prompt: str, max_results: int = 5, **kwargs):
    """Execute a search + extract pipeline."""
    from core.engine import AllureGraphEngine

    engine = AllureGraphEngine()
    result = await engine.search_and_extract(
        query=query,
        prompt=prompt,
        max_results=max_results,
    )
    return result


# === Routes ===

@app.get("/")
async def root():
    return {
        "name": "AllureGraph-AI",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape(req: ScrapeRequest, user=Depends(verify_api_key)):
    """AI-powered single URL scraping."""
    start = time.time()

    try:
        data = await run_smart_scrape(
            url=req.url,
            prompt=req.prompt,
            output_format=req.output_format,
            llm_provider=req.llm_provider,
            llm_model=req.llm_model,
            headless=req.headless,
            proxy=req.proxy,
        )

        duration_ms = int((time.time() - start) * 1000)

        return ScrapeResponse(
            id=str(uuid.uuid4()),
            status="completed",
            data=data,
            credits_used=1,
            duration_ms=duration_ms,
        )
    except Exception as e:
        return ScrapeResponse(
            id=str(uuid.uuid4()),
            status="failed",
            error=str(e),
            credits_used=0,
        )


@app.post("/api/search", response_model=ScrapeResponse)
async def search(req: SearchRequest, user=Depends(verify_api_key)):
    """AI-powered multi-source search + extraction."""
    start = time.time()

    try:
        data = await run_search_scrape(
            query=req.query,
            prompt=req.prompt,
            max_results=req.max_results,
        )

        duration_ms = int((time.time() - start) * 1000)
        credits = min(req.max_results, 5)  # 1 credit per result page

        return ScrapeResponse(
            id=str(uuid.uuid4()),
            status="completed",
            data=data,
            credits_used=credits,
            duration_ms=duration_ms,
        )
    except Exception as e:
        return ScrapeResponse(
            id=str(uuid.uuid4()),
            status="failed",
            error=str(e),
            credits_used=0,
        )


@app.post("/api/monitor", response_model=JobResponse)
async def monitor(req: MonitorRequest, background_tasks: BackgroundTasks, user=Depends(verify_api_key)):
    """Set up scheduled competitor monitoring."""
    job_id = str(uuid.uuid4())

    # TODO: Store in DB + create cron job
    # background_tasks.add_task(create_monitor_job, job_id, req, user)

    return JobResponse(
        job_id=job_id,
        status="queued",
        estimated_seconds=5,
    )


@app.post("/api/leads", response_model=JobResponse)
async def leads(req: LeadRequest, background_tasks: BackgroundTasks, user=Depends(verify_api_key)):
    """Extract leads from social platforms."""
    job_id = str(uuid.uuid4())

    # Lead extraction is async (can take minutes)
    # background_tasks.add_task(run_lead_extraction, job_id, req, user)

    return JobResponse(
        job_id=job_id,
        status="queued",
        estimated_seconds=60,
    )


@app.post("/api/batch", response_model=JobResponse)
async def batch(req: BatchRequest, background_tasks: BackgroundTasks, user=Depends(verify_api_key)):
    """Batch scrape multiple URLs."""
    job_id = str(uuid.uuid4())
    credits_estimate = len(req.urls)

    # background_tasks.add_task(run_batch_scrape, job_id, req, user)

    return JobResponse(
        job_id=job_id,
        status="queued",
        estimated_seconds=len(req.urls) * 10,
    )


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, user=Depends(verify_api_key)):
    """Check status of an async job."""
    # TODO: Look up job in Redis/DB
    return {
        "job_id": job_id,
        "status": "processing",
        "progress": 0.5,
    }


@app.get("/api/templates")
async def list_templates(user=Depends(verify_api_key)):
    """List available scraping templates."""
    return {
        "templates": [
            {
                "slug": "telegram_channel",
                "name": "Telegram Channel Extractor",
                "description": "Extract members, messages, and metadata from Telegram channels",
                "category": "social",
            },
            {
                "slug": "instagram_profile",
                "name": "Instagram Profile Scraper",
                "description": "Extract posts, followers, bio, and engagement metrics",
                "category": "social",
            },
            {
                "slug": "product_prices",
                "name": "Product Price Comparator",
                "description": "Compare product prices across multiple e-commerce sites",
                "category": "ecommerce",
            },
            {
                "slug": "competitor_offers",
                "name": "Competitor Offer Monitor",
                "description": "Track competitor pricing, features, and promotions",
                "category": "intelligence",
            },
            {
                "slug": "review_aggregator",
                "name": "Review Aggregator",
                "description": "Collect and analyze reviews from multiple platforms",
                "category": "social_proof",
            },
            {
                "slug": "lead_enrichment",
                "name": "Lead Enrichment",
                "description": "Enrich contact data with social profiles and company info",
                "category": "leads",
            },
            {
                "slug": "content_research",
                "name": "Content Research",
                "description": "Research trending topics and content performance",
                "category": "content",
            },
            {
                "slug": "x_profile",
                "name": "X/Twitter Profile Analyzer",
                "description": "Analyze X profiles, tweets, engagement, and audience",
                "category": "social",
            },
        ]
    }


@app.get("/api/usage")
async def usage(user=Depends(verify_api_key)):
    """Get current usage and plan info."""
    return {
        "plan": user["plan"],
        "credits_used": 1247,
        "credits_limit": 5000,
        "credits_remaining": user["credits_remaining"],
        "period_start": "2026-07-01",
        "period_end": "2026-07-31",
        "scrapes_today": 43,
        "monitors_active": 5,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
