"""AllureGraph-AI — Intelligence Layer

Advanced features that differentiate AllureGraph from generic scrapers:
- Competitor price monitoring with change detection
- Social proof aggregation and scoring
- Lead scoring and enrichment pipelines
- Trend detection and content gap analysis
- Scheduled monitoring with webhook alerts
"""

import json
from typing import Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class MonitorConfig:
    """Configuration for a monitoring job."""
    url: str
    prompt: str
    frequency: str = "daily"  # hourly | daily | weekly
    webhook_url: Optional[str] = None
    change_threshold: float = 0.1  # 10% change triggers alert
    user_id: str = ""
    is_active: bool = True
    last_check: Optional[datetime] = None
    last_result: Optional[dict] = None


@dataclass
class CompetitorProfile:
    """Tracked competitor."""
    name: str
    url: str
    pricing_url: Optional[str] = None
    last_pricing: Optional[dict] = None
    price_history: list[dict] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None


class CompetitorMonitor:
    """Track competitor pricing and feature changes."""

    def __init__(self, engine=None):
        from core.engine import AllureGraphEngine
        self.engine = engine or AllureGraphEngine()

    async def check_pricing(self, competitor: CompetitorProfile) -> dict:
        """Scrape competitor pricing and detect changes."""
        if not competitor.pricing_url:
            return {"status": "no_pricing_url"}

        result = await self.engine.smart_scrape(
            url=competitor.pricing_url,
            prompt=(
                "Extract complete pricing: all plan names, prices (monthly and annual), "
                "features per plan, limits, and any promotions. Return as JSON."
            ),
        )

        changes = self._detect_changes(competitor.last_pricing, result)

        # Update history
        competitor.last_pricing = result
        competitor.last_updated = datetime.utcnow()
        competitor.price_history.append({
            "date": datetime.utcnow().isoformat(),
            "data": result,
        })

        return {
            "competitor": competitor.name,
            "current_pricing": result,
            "changes_detected": len(changes) > 0,
            "changes": changes,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def _detect_changes(self, old: Optional[dict], new: dict) -> list[dict]:
        """Detect meaningful pricing changes."""
        if not old:
            return []

        changes = []
        # Simple diff detection — can be enhanced with deep comparison
        old_str = json.dumps(old, sort_keys=True)
        new_str = json.dumps(new, sort_keys=True)

        if old_str != new_str:
            changes.append({
                "type": "pricing_change",
                "description": "Pricing page content has changed",
                "severity": "medium",
            })

        return changes


class LeadScorer:
    """Score and prioritize extracted leads."""

    SCORING_RULES = {
        "has_email": 20,
        "has_phone": 15,
        "has_company": 10,
        "has_title": 10,
        "has_linkedin": 15,
        "has_instagram": 5,
        "has_website": 10,
        "is_decision_maker": 25,  # CEO, CTO, VP, Director, Head
    }

    DECISION_MAKER_TITLES = [
        "ceo", "cto", "cfo", "coo", "vp", "vice president",
        "director", "head of", "founder", "co-founder", "owner",
        "managing director", "partner", "chief",
    ]

    def score_lead(self, lead: dict) -> int:
        """Calculate a lead quality score (0-100)."""
        score = 0

        if lead.get("email"):
            score += self.SCORING_RULES["has_email"]
        if lead.get("phone"):
            score += self.SCORING_RULES["has_phone"]
        if lead.get("company"):
            score += self.SCORING_RULES["has_company"]
        if lead.get("title"):
            score += self.SCORING_RULES["has_title"]
            # Check if decision maker
            title_lower = lead["title"].lower()
            if any(dm in title_lower for dm in self.DECISION_MAKER_TITLES):
                score += self.SCORING_RULES["is_decision_maker"]
        if lead.get("social_links", {}).get("linkedin"):
            score += self.SCORING_RULES["has_linkedin"]
        if lead.get("social_links", {}).get("instagram"):
            score += self.SCORING_RULES["has_instagram"]

        return min(score, 100)

    def rank_leads(self, leads: list[dict]) -> list[dict]:
        """Score and rank a list of leads."""
        scored = []
        for lead in leads:
            lead_copy = lead.copy()
            lead_copy["_score"] = self.score_lead(lead)
            scored.append(lead_copy)

        return sorted(scored, key=lambda x: x["_score"], reverse=True)


class TrendDetector:
    """Detect trends and content opportunities."""

    def __init__(self, engine=None):
        from core.engine import AllureGraphEngine
        self.engine = engine or AllureGraphEngine()

    async def find_trending_topics(self, niche: str, platforms: list[str] = None) -> dict:
        """Research trending topics in a niche."""
        if not platforms:
            platforms = ["x", "instagram", "google"]

        results = await self.engine.search_and_extract(
            query=f"trending topics {niche} {datetime.utcnow().strftime('%B %Y')}",
            prompt=(
                f"Find the most trending and viral topics in the '{niche}' niche. "
                "Extract: topic name, estimated engagement/volume, growth trend, "
                "key examples, and recommended content angles. Return as JSON array."
            ),
        )

        return {
            "niche": niche,
            "platforms": platforms,
            "trends": results,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    async def content_gap_analysis(self, your_url: str, competitor_urls: list[str]) -> dict:
        """Find content gaps between you and competitors."""
        # Scrape your content
        your_content = await self.engine.smart_scrape(
            url=your_url,
            prompt="List all main topics, categories, and content themes covered on this site.",
        )

        # Scrape competitor content
        competitor_content = []
        for url in competitor_urls:
            content = await self.engine.smart_scrape(
                url=url,
                prompt="List all main topics, categories, and content themes covered.",
            )
            competitor_content.append({"url": url, "topics": content})

        return {
            "your_topics": your_content,
            "competitor_topics": competitor_content,
            "analyzed_at": datetime.utcnow().isoformat(),
        }


class SocialProofAggregator:
    """Aggregate and analyze social proof across platforms."""

    def __init__(self, engine=None):
        from core.engine import AllureGraphEngine
        self.engine = engine or AllureGraphEngine()

    async def aggregate_reviews(self, business_name: str, platforms: list[str] = None) -> dict:
        """Aggregate reviews from multiple platforms."""
        if not platforms:
            platforms = ["google", "trustpilot", "g2"]

        all_reviews = []
        platform_scores = {}

        for platform in platforms:
            search_query = f"{business_name} reviews {platform}"
            result = await self.engine.search_and_extract(
                query=search_query,
                prompt=(
                    f"Extract reviews of '{business_name}' from {platform}: "
                    "reviewer name, rating, review text, date, and platform."
                ),
            )
            if isinstance(result, list):
                all_reviews.extend(result)
                # Calculate platform average
                ratings = [r.get("rating", 0) for r in result if r.get("rating")]
                if ratings:
                    platform_scores[platform] = sum(ratings) / len(ratings)

        # Calculate overall score
        overall_score = sum(platform_scores.values()) / len(platform_scores) if platform_scores else 0

        return {
            "business": business_name,
            "overall_score": round(overall_score, 2),
            "platform_scores": platform_scores,
            "total_reviews": len(all_reviews),
            "reviews": all_reviews,
            "aggregated_at": datetime.utcnow().isoformat(),
        }

    def calculate_trust_score(self, reviews: list[dict]) -> dict:
        """Calculate a trust score based on review patterns."""
        if not reviews:
            return {"score": 0, "confidence": "low", "factors": []}

        total = len(reviews)
        ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        # Factor in review volume, recency, and rating distribution
        factors = []

        if total >= 50:
            factors.append({"name": "high_volume", "impact": +10})
        elif total >= 20:
            factors.append({"name": "moderate_volume", "impact": +5})
        else:
            factors.append({"name": "low_volume", "impact": -5})

        if avg_rating >= 4.5:
            factors.append({"name": "excellent_rating", "impact": +15})
        elif avg_rating >= 4.0:
            factors.append({"name": "good_rating", "impact": +10})
        elif avg_rating >= 3.0:
            factors.append({"name": "average_rating", "impact": 0})
        else:
            factors.append({"name": "poor_rating", "impact": -15})

        base_score = 50 + sum(f["impact"] for f in factors)
        trust_score = max(0, min(100, base_score))

        return {
            "score": trust_score,
            "confidence": "high" if total >= 50 else "medium" if total >= 20 else "low",
            "avg_rating": round(avg_rating, 2),
            "total_reviews": total,
            "factors": factors,
        }
