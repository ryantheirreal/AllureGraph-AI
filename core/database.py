"""AllureGraph-AI — Database Schema & Supabase Integration

Supabase tables for:
- Users & auth
- API keys
- Usage tracking
- Jobs (async scrapes)
- Monitors (scheduled tasks)
- Results cache
"""

import os
from datetime import datetime
from typing import Optional

# SQL schema for Supabase migration
SCHEMA_SQL = """
-- AllureGraph-AI Database Schema
-- Run this in Supabase SQL Editor

-- Users (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS ag_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    plan TEXT NOT NULL DEFAULT 'starter',
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    credits_monthly_limit INTEGER NOT NULL DEFAULT 500,
    allurevips_user_id UUID, -- Link to AllureVIPs if bundled
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- API Keys
CREATE TABLE IF NOT EXISTS ag_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES ag_profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Default',
    key_hash TEXT NOT NULL UNIQUE, -- SHA-256 of the full key
    key_prefix TEXT NOT NULL, -- First 12 chars for display
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ag_api_keys_hash ON ag_api_keys(key_hash);
CREATE INDEX idx_ag_api_keys_user ON ag_api_keys(user_id);

-- Usage Records
CREATE TABLE IF NOT EXISTS ag_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES ag_profiles(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES ag_api_keys(id),
    credits INTEGER NOT NULL DEFAULT 1,
    endpoint TEXT NOT NULL, -- scrape | search | batch | monitor | leads
    template TEXT, -- template slug if used
    url TEXT,
    duration_ms INTEGER,
    status TEXT NOT NULL DEFAULT 'completed', -- completed | failed
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ag_usage_user ON ag_usage(user_id, created_at DESC);
CREATE INDEX idx_ag_usage_period ON ag_usage(user_id, created_at);

-- Jobs (async scrapes)
CREATE TABLE IF NOT EXISTS ag_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES ag_profiles(id) ON DELETE CASCADE,
    type TEXT NOT NULL, -- batch | leads | deep_crawl
    status TEXT NOT NULL DEFAULT 'queued', -- queued | processing | completed | failed
    progress REAL DEFAULT 0, -- 0.0 to 1.0
    input JSONB NOT NULL,
    result JSONB,
    error TEXT,
    credits_used INTEGER DEFAULT 0,
    webhook_url TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ag_jobs_user ON ag_jobs(user_id, created_at DESC);
CREATE INDEX idx_ag_jobs_status ON ag_jobs(status);

-- Monitors (scheduled scrapes)
CREATE TABLE IF NOT EXISTS ag_monitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES ag_profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    prompt TEXT NOT NULL,
    template TEXT,
    frequency TEXT NOT NULL DEFAULT 'daily', -- hourly | daily | weekly
    is_active BOOLEAN NOT NULL DEFAULT true,
    webhook_url TEXT,
    last_result JSONB,
    last_checked_at TIMESTAMPTZ,
    changes_detected INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ag_monitors_user ON ag_monitors(user_id);
CREATE INDEX idx_ag_monitors_active ON ag_monitors(is_active, frequency);

-- Results Cache
CREATE TABLE IF NOT EXISTS ag_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_hash TEXT NOT NULL, -- SHA-256 of URL + prompt
    url TEXT NOT NULL,
    prompt TEXT NOT NULL,
    result JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ag_cache_hash ON ag_cache(url_hash);
CREATE INDEX idx_ag_cache_expires ON ag_cache(expires_at);

-- Row Level Security
ALTER TABLE ag_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ag_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE ag_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE ag_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ag_monitors ENABLE ROW LEVEL SECURITY;

-- Policies: users can only see their own data
CREATE POLICY "Users see own profile" ON ag_profiles FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users see own keys" ON ag_api_keys FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own usage" ON ag_usage FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own jobs" ON ag_jobs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own monitors" ON ag_monitors FOR ALL USING (auth.uid() = user_id);

-- Functions
CREATE OR REPLACE FUNCTION get_usage_this_period(p_user_id UUID)
RETURNS INTEGER AS $$
    SELECT COALESCE(SUM(credits), 0)::INTEGER
    FROM ag_usage
    WHERE user_id = p_user_id
    AND created_at >= date_trunc('month', NOW())
    AND status = 'completed';
$$ LANGUAGE sql STABLE;
"""


class SupabaseClient:
    """Supabase client wrapper for AllureGraph."""

    def __init__(self):
        from supabase import create_client
        self.client = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_SERVICE_KEY", ""),
        )

    async def get_user_by_api_key(self, key_hash: str) -> Optional[dict]:
        """Look up user by API key hash."""
        result = self.client.table("ag_api_keys").select(
            "*, ag_profiles(*)"
        ).eq("key_hash", key_hash).eq("is_active", True).single().execute()

        if result.data:
            return result.data.get("ag_profiles")
        return None

    async def record_usage(self, user_id: str, credits: int, endpoint: str, **kwargs):
        """Record API usage."""
        self.client.table("ag_usage").insert({
            "user_id": user_id,
            "credits": credits,
            "endpoint": endpoint,
            "template": kwargs.get("template"),
            "url": kwargs.get("url"),
            "duration_ms": kwargs.get("duration_ms"),
            "status": kwargs.get("status", "completed"),
        }).execute()

    async def get_credits_used(self, user_id: str) -> int:
        """Get credits used in current billing period."""
        result = self.client.rpc("get_usage_this_period", {"p_user_id": user_id}).execute()
        return result.data or 0

    async def create_api_key(self, user_id: str, name: str, key_hash: str, key_prefix: str):
        """Create a new API key."""
        self.client.table("ag_api_keys").insert({
            "user_id": user_id,
            "name": name,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
        }).execute()
