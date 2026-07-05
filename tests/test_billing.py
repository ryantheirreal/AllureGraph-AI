"""Tests for AllureGraph-AI billing module."""

import pytest
from core.billing import (
    PLANS, generate_api_key, validate_api_key,
    UsageMeter, LeadScorer
)
from core.intelligence import LeadScorer as IntelLeadScorer


def test_plans_exist():
    assert "starter" in PLANS
    assert "pro" in PLANS
    assert "business" in PLANS
    assert "enterprise" in PLANS
    assert "allurevips_pro" in PLANS


def test_plan_pricing():
    assert PLANS["starter"]["price_usd"] == 29
    assert PLANS["pro"]["price_usd"] == 99
    assert PLANS["business"]["price_usd"] == 299
    assert PLANS["allurevips_pro"]["price_usd"] == 0


def test_plan_credits():
    assert PLANS["starter"]["credits_monthly"] == 500
    assert PLANS["pro"]["credits_monthly"] == 5000
    assert PLANS["business"]["credits_monthly"] == 25000


def test_generate_api_key():
    key = generate_api_key("user_123")
    assert key.startswith("ag_live_")
    assert len(key) == 32  # ag_live_ (8) + 24 chars


def test_generate_unique_keys():
    key1 = generate_api_key("user_1")
    key2 = generate_api_key("user_1")
    assert key1 != key2


def test_validate_api_key_valid():
    assert validate_api_key("ag_live_abc123def456ghi789jkl012") is True
    assert validate_api_key("ag_test_abc123def456ghi789jkl012") is True


def test_validate_api_key_invalid():
    assert validate_api_key("") is False
    assert validate_api_key("sk_live_xxx") is False
    assert validate_api_key("invalid") is False
    assert validate_api_key(None) is False
