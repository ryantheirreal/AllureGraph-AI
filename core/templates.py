"""AllureGraph-AI — Social Selling Templates

Pre-built extraction templates optimized for:
- Telegram channels/groups
- Instagram profiles and posts
- X/Twitter accounts
- E-commerce products
- Competitor intelligence
- Lead generation
- Content research

Each template defines:
- prompt: The LLM extraction prompt
- graph_type: Which ScrapeGraphAI graph to use
- schema: Pydantic model for structured output
- credits: How many credits this template costs
- category: Template category for filtering
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


# === Output Schemas ===

class TelegramChannelData(BaseModel):
    channel_name: str = ""
    description: str = ""
    member_count: Optional[int] = None
    messages: list[dict] = Field(default_factory=list)
    pinned_messages: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    admin_contacts: list[str] = Field(default_factory=list)


class InstagramProfileData(BaseModel):
    username: str = ""
    full_name: str = ""
    bio: str = ""
    followers: Optional[int] = None
    following: Optional[int] = None
    posts_count: Optional[int] = None
    profile_pic_url: str = ""
    recent_posts: list[dict] = Field(default_factory=list)
    bio_links: list[str] = Field(default_factory=list)
    is_verified: bool = False


class ProductData(BaseModel):
    name: str = ""
    price: str = ""
    original_price: Optional[str] = None
    discount_percent: Optional[int] = None
    currency: str = "BRL"
    availability: str = "in_stock"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    url: str = ""
    image_url: str = ""
    seller: str = ""


class CompetitorOfferData(BaseModel):
    company_name: str = ""
    plans: list[dict] = Field(default_factory=list)
    promotions: list[str] = Field(default_factory=list)
    pricing_model: str = ""  # subscription | one-time | usage-based
    free_trial: bool = False
    trial_days: Optional[int] = None
    key_features: list[str] = Field(default_factory=list)


class LeadData(BaseModel):
    name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    company: str = ""
    title: str = ""
    location: str = ""
    social_links: dict = Field(default_factory=dict)
    source: str = ""


class ReviewData(BaseModel):
    reviewer_name: str = ""
    rating: Optional[float] = None
    text: str = ""
    date: str = ""
    verified: bool = False
    helpful_votes: int = 0
    platform: str = ""


class ContentData(BaseModel):
    title: str = ""
    author: str = ""
    publish_date: str = ""
    engagement: dict = Field(default_factory=dict)
    word_count: Optional[int] = None
    topics: list[str] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list)
    url: str = ""


class XProfileData(BaseModel):
    display_name: str = ""
    handle: str = ""
    bio: str = ""
    followers: Optional[int] = None
    following: Optional[int] = None
    join_date: str = ""
    location: str = ""
    recent_tweets: list[dict] = Field(default_factory=list)
    pinned_tweet: Optional[dict] = None
    is_verified: bool = False


# === Template Definitions ===

TEMPLATES = {
    # ===== SOCIAL =====
    "telegram_channel": {
        "name": "Telegram Channel Extractor",
        "description": "Extract members, messages, metadata from Telegram channels",
        "category": "social",
        "credits": 2,
        "graph_type": "smart",
        "schema": TelegramChannelData,
        "prompt": (
            "Extract all visible information from this Telegram channel: "
            "channel name, description, member/subscriber count, "
            "recent messages (text content, date, view count, forward count), "
            "pinned messages, all links mentioned, and any admin/contact information. "
            "Return as structured JSON."
        ),
        "url_pattern": "https://t.me/s/{target}",
    },
    "instagram_profile": {
        "name": "Instagram Profile Scraper",
        "description": "Extract posts, followers, bio, engagement from Instagram profiles",
        "category": "social",
        "credits": 3,
        "graph_type": "omni",
        "schema": InstagramProfileData,
        "prompt": (
            "Extract complete profile information: username, full name, bio text, "
            "follower count, following count, total posts count, profile picture URL, "
            "recent posts (image URL, caption, likes count, comments count, post date), "
            "story highlights, bio links, and verification status. Return as structured JSON."
        ),
        "url_pattern": "https://www.instagram.com/{target}/",
    },
    "x_profile": {
        "name": "X/Twitter Profile Analyzer",
        "description": "Analyze X profiles: tweets, engagement, audience metrics",
        "category": "social",
        "credits": 2,
        "graph_type": "smart",
        "schema": XProfileData,
        "prompt": (
            "Extract: display name, @handle, bio, follower count, following count, "
            "account creation date, location, recent tweets (text, likes, retweets, "
            "replies, date posted), pinned tweet, verification badge status, "
            "and any links in bio. Return as structured JSON."
        ),
        "url_pattern": "https://x.com/{target}",
    },

    # ===== E-COMMERCE =====
    "product_prices": {
        "name": "Product Price Comparator",
        "description": "Compare product prices across e-commerce sites",
        "category": "ecommerce",
        "credits": 1,
        "graph_type": "smart",
        "schema": ProductData,
        "prompt": (
            "Extract ALL products visible on this page with: product name, "
            "current price, original price (if discounted), discount percentage, "
            "currency, availability/stock status, star rating, number of reviews, "
            "product URL/link, image URL, and seller name. Return as JSON array."
        ),
    },
    "shopee_products": {
        "name": "Shopee Product Extractor",
        "description": "Extract products from Shopee search/category pages",
        "category": "ecommerce",
        "credits": 2,
        "graph_type": "smart",
        "schema": ProductData,
        "prompt": (
            "Extract all products from this Shopee page: product name, price in BRL, "
            "original price if discounted, discount badge, sold count, rating stars, "
            "review count, seller name, free shipping badge, and product link. "
            "Return as JSON array."
        ),
    },
    "mercadolivre_products": {
        "name": "Mercado Livre Extractor",
        "description": "Extract products from Mercado Livre listings",
        "category": "ecommerce",
        "credits": 2,
        "graph_type": "smart",
        "schema": ProductData,
        "prompt": (
            "Extract all products from this Mercado Livre page: product title, "
            "price in BRL, installment info, shipping type (full/free), seller reputation, "
            "sold quantity, rating, and product URL. Return as JSON array."
        ),
    },

    # ===== INTELLIGENCE =====
    "competitor_offers": {
        "name": "Competitor Offer Monitor",
        "description": "Track competitor pricing, features, and promotions",
        "category": "intelligence",
        "credits": 2,
        "graph_type": "smart",
        "schema": CompetitorOfferData,
        "prompt": (
            "Analyze this company's pricing/offers page and extract: company name, "
            "all plans/tiers (name, price, billing period, included features, limits), "
            "any active promotions or discounts, pricing model type, "
            "free trial availability and duration, and key differentiating features. "
            "Return as structured JSON."
        ),
    },
    "saas_pricing": {
        "name": "SaaS Pricing Intelligence",
        "description": "Extract and compare SaaS pricing pages",
        "category": "intelligence",
        "credits": 2,
        "graph_type": "smart",
        "schema": CompetitorOfferData,
        "prompt": (
            "Extract complete pricing information from this SaaS: all plan names, "
            "monthly and annual prices, feature lists per plan, usage limits, "
            "enterprise/custom options, any current promotions, money-back guarantees, "
            "and comparison with competitors if shown. Return as structured JSON."
        ),
    },

    # ===== LEADS =====
    "lead_enrichment": {
        "name": "Lead Enrichment",
        "description": "Enrich contact data with social and company info",
        "category": "leads",
        "credits": 3,
        "graph_type": "smart",
        "schema": LeadData,
        "prompt": (
            "Extract all contact and professional information visible: full name, "
            "job title, company name, email addresses, phone numbers, "
            "social media profile links (LinkedIn, X, Instagram, etc.), "
            "physical location, and any other professional details. Return as JSON."
        ),
    },
    "linkedin_company": {
        "name": "LinkedIn Company Extractor",
        "description": "Extract company info and employee data from LinkedIn",
        "category": "leads",
        "credits": 3,
        "graph_type": "smart",
        "schema": LeadData,
        "prompt": (
            "Extract company information: company name, industry, size, headquarters, "
            "description, website, specialties, and any visible employee profiles "
            "(name, title, profile URL). Return as structured JSON."
        ),
    },

    # ===== SOCIAL PROOF =====
    "review_aggregator": {
        "name": "Review Aggregator",
        "description": "Collect reviews from multiple platforms",
        "category": "social_proof",
        "credits": 2,
        "graph_type": "smart",
        "schema": ReviewData,
        "prompt": (
            "Extract ALL reviews visible: reviewer name/username, star rating, "
            "review text/body, date posted, verified purchase indicator, "
            "helpful votes/likes count, and platform name. Return as JSON array."
        ),
    },
    "google_reviews": {
        "name": "Google Reviews Extractor",
        "description": "Extract Google Business reviews",
        "category": "social_proof",
        "credits": 2,
        "graph_type": "smart",
        "schema": ReviewData,
        "prompt": (
            "Extract all Google reviews: reviewer name, profile photo indicator, "
            "star rating (1-5), review text, date/time ago, owner response if any, "
            "and review photos if present. Return as JSON array."
        ),
    },

    # ===== CONTENT =====
    "content_research": {
        "name": "Content Research",
        "description": "Research trending topics and content performance",
        "category": "content",
        "credits": 3,
        "graph_type": "search",
        "schema": ContentData,
        "prompt": (
            "Research this topic and extract from results: article titles, authors, "
            "publication dates, engagement metrics (likes, shares, comments), "
            "word count estimates, main topics/tags, key takeaways/summaries, "
            "and source URLs. Return as JSON array."
        ),
    },
    "trending_hashtags": {
        "name": "Trending Hashtags Finder",
        "description": "Find trending hashtags for a niche",
        "category": "content",
        "credits": 2,
        "graph_type": "search",
        "schema": ContentData,
        "prompt": (
            "Find the most popular and trending hashtags related to this topic. "
            "Extract: hashtag, estimated post volume, growth trend, "
            "related hashtags, and example top posts using each. Return as JSON array."
        ),
    },
}


def get_template(slug: str) -> Optional[dict]:
    """Get a template by slug."""
    return TEMPLATES.get(slug)


def list_templates(category: Optional[str] = None) -> list[dict]:
    """List all templates, optionally filtered by category."""
    templates = []
    for slug, t in TEMPLATES.items():
        if category and t["category"] != category:
            continue
        templates.append({
            "slug": slug,
            "name": t["name"],
            "description": t["description"],
            "category": t["category"],
            "credits": t["credits"],
        })
    return templates


def get_categories() -> list[str]:
    """Get all template categories."""
    return list(set(t["category"] for t in TEMPLATES.values()))
