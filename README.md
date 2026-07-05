# AllureGraph-AI

> The AI-powered scraping & intelligence engine for social sellers and digital businesses.

## What is AllureGraph?

AllureGraph-AI is a next-generation AI scraping platform that uses LLMs to intelligently extract, transform, and deliver structured data from any source. Built for social sellers, digital entrepreneurs, and businesses that need competitive intelligence.

## Why AllureGraph?

| Feature | Apify | Firecrawl | AllureGraph |
|---------|-------|-----------|-------------|
| AI-powered extraction | ❌ | ✅ | ✅ |
| Social selling templates | ❌ | ❌ | ✅ |
| Telegram/IG/X native | ❌ | ❌ | ✅ |
| Competitor monitoring | ❌ | ❌ | ✅ |
| Pay-per-scrape API | ✅ | ✅ | ✅ |
| Self-host option | ✅ | ❌ | ✅ |
| Portuguese/LATAM focus | ❌ | ❌ | ✅ |
| AllureVIPs integration | ❌ | ❌ | ✅ |

## Architecture

```
┌─────────────────────────────────────────────────┐
│              AllureGraph-AI Platform             │
├─────────────────────────────────────────────────┤
│  API Layer (FastAPI / Vercel Edge)              │
│  ├── /scrape    — single URL AI extraction      │
│  ├── /search    — multi-source search + extract │
│  ├── /monitor   — scheduled competitor watch    │
│  ├── /leads     — social lead extraction        │
│  └── /batch     — bulk scraping pipeline        │
├─────────────────────────────────────────────────┤
│  Core Engine (forked ScrapeGraphAI)             │
│  ├── SmartScraper — LLM-driven page extraction  │
│  ├── SearchGraph  — multi-source search         │
│  ├── OmniScraper  — vision + text extraction    │
│  ├── DepthSearch  — recursive crawling          │
│  └── CodeGen      — auto-generate scrapers      │
├─────────────────────────────────────────────────┤
│  Intelligence Layer                             │
│  ├── Competitor price tracker                   │
│  ├── Social proof aggregator                    │
│  ├── Lead finder (Telegram/IG/X)                │
│  ├── Content research engine                    │
│  └── Trend detector                             │
├─────────────────────────────────────────────────┤
│  Templates (Social Selling Focused)             │
│  ├── telegram_channel_extract                   │
│  ├── instagram_profile_scrape                   │
│  ├── product_price_compare                      │
│  ├── review_aggregator                          │
│  ├── competitor_offer_monitor                   │
│  └── lead_enrichment                            │
├─────────────────────────────────────────────────┤
│  Billing & Auth (Stripe + Supabase)             │
│  ├── API key management                         │
│  ├── Usage metering                             │
│  ├── Plan limits enforcement                    │
│  └── AllureVIPs SSO integration                 │
└─────────────────────────────────────────────────┘
```

## Pricing

| Plan | Price | Scrapes/mo | Features |
|------|-------|------------|----------|
| Starter | $29/mo | 500 | API access, 5 templates |
| Pro | $99/mo | 5,000 | All templates, monitoring, webhooks |
| Business | $299/mo | 25,000 | Priority, custom templates, SLA |
| Enterprise | Custom | Unlimited | Self-host, dedicated support |
| AllureVIPs Pro | Included | 1,000 | Bundled with R$197/mo plan |

## Tech Stack

- **Core Engine**: Python (ScrapeGraphAI fork) + LangChain + Playwright
- **API**: FastAPI + Redis + Celery (async jobs)
- **Dashboard**: React + Vite + Tailwind (shared with AllureVIPs)
- **Database**: Supabase (PostgreSQL)
- **Queue**: Redis + BullMQ
- **LLM**: Claude / GPT-4o / Ollama (user choice)
- **Deploy**: Vercel (dashboard) + Railway/Fly.io (Python API)

## Quick Start

```bash
# API
curl -X POST https://graph.allurevips.fun/api/scrape \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/products",
    "prompt": "Extract all product names, prices, and descriptions",
    "output_format": "json"
  }'
```

## Roadmap

- [x] Core engine (ScrapeGraphAI fork)
- [ ] REST API with auth
- [ ] Dashboard + usage metrics
- [ ] Social selling templates
- [ ] Competitor monitoring (scheduled)
- [ ] AllureVIPs integration
- [ ] Telegram bot for scraping
- [ ] Chrome extension
- [ ] Marketplace (community templates)

## License

Proprietary — AllureVIPs LLC
