"""AllureGraph-AI — Billing & Usage Metering

Stripe integration for:
- Plan management (Starter, Pro, Business, Enterprise)
- Usage-based billing (credits per scrape)
- API key generation and validation
- AllureVIPs bundle integration
"""

import os
import uuid
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


# Plan definitions
PLANS = {
    "starter": {
        "name": "Starter",
        "price_usd": 29,
        "credits_monthly": 500,
        "templates": 5,
        "monitors": 2,
        "batch_size": 10,
        "support": "community",
        "features": ["API access", "5 templates", "JSON/CSV export", "2 monitors"],
    },
    "pro": {
        "name": "Pro",
        "price_usd": 99,
        "credits_monthly": 5000,
        "templates": "all",
        "monitors": 20,
        "batch_size": 50,
        "support": "priority",
        "features": ["All templates", "Webhooks", "20 monitors", "Priority queue", "Custom prompts"],
    },
    "business": {
        "name": "Business",
        "price_usd": 299,
        "credits_monthly": 25000,
        "templates": "all",
        "monitors": 100,
        "batch_size": 100,
        "support": "dedicated",
        "features": ["Custom templates", "SLA 99.9%", "100 monitors", "Dedicated queue", "API analytics"],
    },
    "enterprise": {
        "name": "Enterprise",
        "price_usd": None,  # Custom
        "credits_monthly": None,  # Unlimited
        "templates": "all",
        "monitors": "unlimited",
        "batch_size": 500,
        "support": "white-glove",
        "features": ["Self-host option", "Unlimited credits", "Custom SLA", "White-label", "Dedicated infra"],
    },
    "allurevips_pro": {
        "name": "AllureVIPs Pro Bundle",
        "price_usd": 0,  # Included in R$197/mo AllureVIPs plan
        "credits_monthly": 1000,
        "templates": "all",
        "monitors": 10,
        "batch_size": 25,
        "support": "priority",
        "features": ["Bundled with AllureVIPs Pro", "All templates", "10 monitors", "Intelligence panel"],
    },
}


@dataclass
class APIKey:
    """API Key model."""
    key: str
    user_id: str
    plan: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True


def generate_api_key(user_id: str) -> str:
    """Generate a new AllureGraph API key.

    Format: ag_live_xxxxxxxxxxxxxxxxxxxx (production)
            ag_test_xxxxxxxxxxxxxxxxxxxx (sandbox)
    """
    prefix = "ag_live"
    random_part = uuid.uuid4().hex[:24]
    return f"{prefix}_{random_part}"


def validate_api_key(key: str) -> bool:
    """Validate API key format."""
    if not key:
        return False
    return key.startswith("ag_live_") or key.startswith("ag_test_")


class UsageMeter:
    """Track and enforce usage limits."""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

    async def check_credits(self, user_id: str) -> dict:
        """Check if user has credits remaining."""
        # TODO: Query Supabase for current period usage
        return {
            "has_credits": True,
            "credits_used": 0,
            "credits_limit": 5000,
            "credits_remaining": 5000,
        }

    async def record_usage(self, user_id: str, credits: int = 1, metadata: dict = None):
        """Record a scrape credit usage."""
        # TODO: Insert into Supabase usage table
        usage_record = {
            "user_id": user_id,
            "credits": credits,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        return usage_record

    async def get_usage_summary(self, user_id: str, period_start: datetime = None) -> dict:
        """Get usage summary for billing period."""
        if not period_start:
            # Default to start of current month
            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0)

        # TODO: Query Supabase
        return {
            "user_id": user_id,
            "period_start": period_start.isoformat(),
            "period_end": (period_start + timedelta(days=30)).isoformat(),
            "total_scrapes": 0,
            "total_credits": 0,
            "by_type": {
                "smart_scrape": 0,
                "search": 0,
                "batch": 0,
                "monitor": 0,
                "leads": 0,
            },
        }


class StripeIntegration:
    """Stripe billing integration."""

    def __init__(self):
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.stripe = stripe

    async def create_customer(self, email: str, name: str, metadata: dict = None) -> str:
        """Create a Stripe customer."""
        customer = self.stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {},
        )
        return customer.id

    async def create_subscription(self, customer_id: str, plan: str) -> dict:
        """Create a subscription for a plan."""
        # Price IDs would be configured in env
        price_ids = {
            "starter": os.getenv("STRIPE_PRICE_STARTER"),
            "pro": os.getenv("STRIPE_PRICE_PRO"),
            "business": os.getenv("STRIPE_PRICE_BUSINESS"),
        }

        price_id = price_ids.get(plan)
        if not price_id:
            raise ValueError(f"No Stripe price for plan: {plan}")

        subscription = self.stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_period_days=7,
        )

        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "trial_end": subscription.trial_end,
        }

    async def record_usage_event(self, subscription_id: str, credits: int):
        """Record metered usage for overage billing."""
        # For usage-based billing above plan limits
        self.stripe.SubscriptionItem.create_usage_record(
            subscription_id,
            quantity=credits,
            timestamp="now",
        )
