"""AllureGraph-AI — Webhook Delivery System

Reliable webhook delivery for:
- Job completion notifications
- Monitor change alerts
- Usage threshold warnings
"""

import httpx
import json
import hashlib
import hmac
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class WebhookEvent:
    """A webhook event to deliver."""
    event_type: str  # job.completed | monitor.changed | usage.threshold
    payload: dict
    webhook_url: str
    user_id: str
    attempt: int = 0
    max_attempts: int = 3


class WebhookDelivery:
    """Deliver webhooks with retry and signature verification."""

    def __init__(self, signing_secret: str = ""):
        self.signing_secret = signing_secret

    def sign_payload(self, payload: str, timestamp: int) -> str:
        """Sign webhook payload with HMAC-SHA256."""
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            self.signing_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"v1={signature}"

    async def deliver(self, event: WebhookEvent) -> dict:
        """Deliver a webhook event with retries."""
        timestamp = int(time.time())
        payload_json = json.dumps(event.payload)
        signature = self.sign_payload(payload_json, timestamp)

        headers = {
            "Content-Type": "application/json",
            "X-AllureGraph-Event": event.event_type,
            "X-AllureGraph-Timestamp": str(timestamp),
            "X-AllureGraph-Signature": signature,
            "User-Agent": "AllureGraph-AI/1.0",
        }

        for attempt in range(event.max_attempts):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        event.webhook_url,
                        content=payload_json,
                        headers=headers,
                    )

                    if response.status_code < 300:
                        return {
                            "status": "delivered",
                            "status_code": response.status_code,
                            "attempt": attempt + 1,
                        }

                    # Retry on 5xx
                    if response.status_code >= 500:
                        continue

                    # Don't retry on 4xx (client error)
                    return {
                        "status": "failed",
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                        "error": f"HTTP {response.status_code}",
                    }

            except Exception as e:
                if attempt == event.max_attempts - 1:
                    return {
                        "status": "failed",
                        "attempt": attempt + 1,
                        "error": str(e),
                    }
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

        return {"status": "exhausted", "attempts": event.max_attempts}
