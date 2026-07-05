"""AllureGraph-AI — Async Task Queue

Celery tasks for heavy/long-running scraping jobs:
- Batch scrapes
- Lead extraction
- Scheduled monitoring
- Deep crawls
"""

import os
import json
from celery import Celery
from datetime import datetime

# Redis as broker + result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "alluregraph",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min max per task
    task_soft_time_limit=240,  # Warn at 4 min
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (memory leak prevention)
    worker_prefetch_multiplier=1,  # Fair distribution
)


@celery_app.task(bind=True, max_retries=3)
def batch_scrape_task(self, job_id: str, urls: list[str], prompt: str, user_id: str, output_format: str = "json"):
    """Process a batch of URLs for scraping."""
    import asyncio
    from core.engine import AllureGraphEngine

    engine = AllureGraphEngine()
    results = []
    errors = []

    for i, url in enumerate(urls):
        try:
            result = asyncio.run(engine.smart_scrape(
                url=url,
                prompt=prompt,
                output_format=output_format,
            ))
            results.append({"url": url, "data": result, "status": "success"})
        except Exception as e:
            errors.append({"url": url, "error": str(e), "status": "failed"})

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1,
                "total": len(urls),
                "percent": int((i + 1) / len(urls) * 100),
            }
        )

    return {
        "job_id": job_id,
        "status": "completed",
        "total_urls": len(urls),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "completed_at": datetime.utcnow().isoformat(),
    }


@celery_app.task(bind=True, max_retries=2)
def lead_extraction_task(self, job_id: str, source: str, target: str, prompt: str, max_leads: int, user_id: str):
    """Extract leads from social platforms."""
    import asyncio
    from core.engine import AllureGraphEngine

    engine = AllureGraphEngine()

    # Map source to appropriate URL/approach
    source_urls = {
        "telegram": f"https://t.me/s/{target}",
        "instagram": f"https://www.instagram.com/{target}/",
        "x": f"https://x.com/{target}",
        "linkedin": f"https://www.linkedin.com/company/{target}/",
    }

    url = source_urls.get(source)
    if not url:
        return {"job_id": job_id, "status": "failed", "error": f"Unknown source: {source}"}

    try:
        result = asyncio.run(engine.smart_scrape(
            url=url,
            prompt=f"{prompt}\n\nExtract up to {max_leads} leads/profiles.",
            output_format="json",
        ))

        return {
            "job_id": job_id,
            "status": "completed",
            "source": source,
            "target": target,
            "leads_found": len(result) if isinstance(result, list) else 1,
            "data": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
        }


@celery_app.task(bind=True)
def monitor_task(self, job_id: str, url: str, prompt: str, user_id: str, webhook_url: str = None):
    """Execute a single monitoring check."""
    import asyncio
    import httpx
    from core.engine import AllureGraphEngine

    engine = AllureGraphEngine()

    try:
        result = asyncio.run(engine.smart_scrape(
            url=url,
            prompt=prompt,
            output_format="json",
        ))

        payload = {
            "job_id": job_id,
            "status": "completed",
            "url": url,
            "data": result,
            "checked_at": datetime.utcnow().isoformat(),
        }

        # Send webhook if configured
        if webhook_url:
            try:
                httpx.post(webhook_url, json=payload, timeout=10)
            except Exception:
                pass  # Don't fail the task for webhook issues

        return payload

    except Exception as e:
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
        }


@celery_app.task
def cleanup_old_jobs():
    """Periodic task to clean up old job results."""
    # TODO: Clean Redis keys older than 7 days
    pass


# Periodic schedule
celery_app.conf.beat_schedule = {
    "cleanup-old-jobs": {
        "task": "core.tasks.cleanup_old_jobs",
        "schedule": 86400.0,  # Daily
    },
}
