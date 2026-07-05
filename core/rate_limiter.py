"""AllureGraph-AI — Rate Limiting

Redis-based rate limiting per API key with plan-aware limits.
"""

import os
import time
from typing import Optional


PLAN_LIMITS = {
    "starter": {"per_minute": 10, "per_hour": 100, "per_day": 500},
    "pro": {"per_minute": 30, "per_hour": 500, "per_day": 5000},
    "business": {"per_minute": 60, "per_hour": 1000, "per_day": 25000},
    "enterprise": {"per_minute": 120, "per_hour": 5000, "per_day": 100000},
    "allurevips_pro": {"per_minute": 20, "per_hour": 200, "per_day": 1000},
}


class RateLimiter:
    """Redis sliding-window rate limiter."""

    def __init__(self, redis_client=None):
        self.redis = redis_client

    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0")
            )

    async def check_rate_limit(self, api_key: str, plan: str) -> dict:
        """Check if request is within rate limits.

        Returns:
            {"allowed": bool, "remaining": int, "reset_at": int}
        """
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])
        now = int(time.time())

        # Check per-minute limit (sliding window)
        minute_key = f"rl:{api_key}:min:{now // 60}"
        minute_count = await self.redis.incr(minute_key)
        if minute_count == 1:
            await self.redis.expire(minute_key, 120)  # 2 min TTL

        if minute_count > limits["per_minute"]:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_at": (now // 60 + 1) * 60,
                "limit": limits["per_minute"],
                "window": "minute",
            }

        # Check per-hour limit
        hour_key = f"rl:{api_key}:hr:{now // 3600}"
        hour_count = await self.redis.incr(hour_key)
        if hour_count == 1:
            await self.redis.expire(hour_key, 7200)

        if hour_count > limits["per_hour"]:
            return {
                "allowed": False,
                "remaining": 0,
                "reset_at": (now // 3600 + 1) * 3600,
                "limit": limits["per_hour"],
                "window": "hour",
            }

        remaining = limits["per_minute"] - minute_count
        return {
            "allowed": True,
            "remaining": max(0, remaining),
            "reset_at": (now // 60 + 1) * 60,
            "limit": limits["per_minute"],
            "window": "minute",
        }

    async def get_usage_stats(self, api_key: str) -> dict:
        """Get current usage stats for an API key."""
        now = int(time.time())

        minute_key = f"rl:{api_key}:min:{now // 60}"
        hour_key = f"rl:{api_key}:hr:{now // 3600}"

        minute_count = int(await self.redis.get(minute_key) or 0)
        hour_count = int(await self.redis.get(hour_key) or 0)

        return {
            "requests_this_minute": minute_count,
            "requests_this_hour": hour_count,
        }
