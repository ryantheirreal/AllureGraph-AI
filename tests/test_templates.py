"""Tests for AllureGraph-AI templates."""

import pytest
from core.templates import (
    TEMPLATES, get_template, list_templates, get_categories,
    TelegramChannelData, InstagramProfileData, ProductData
)


def test_templates_count():
    assert len(TEMPLATES) >= 14


def test_all_templates_have_required_fields():
    required = ["name", "description", "category", "credits", "graph_type", "prompt"]
    for slug, template in TEMPLATES.items():
        for field in required:
            assert field in template, f"Template '{slug}' missing field '{field}'"


def test_get_template_valid():
    t = get_template("telegram_channel")
    assert t is not None
    assert t["credits"] == 2
    assert t["graph_type"] == "smart"


def test_get_template_invalid():
    assert get_template("nonexistent") is None


def test_list_templates_all():
    templates = list_templates()
    assert len(templates) >= 14
    assert all("slug" in t for t in templates)


def test_list_templates_by_category():
    social = list_templates(category="social")
    assert len(social) >= 3
    assert all(t["category"] == "social" for t in social)


def test_get_categories():
    cats = get_categories()
    assert "social" in cats
    assert "ecommerce" in cats
    assert "intelligence" in cats
    assert "leads" in cats


def test_schema_telegram():
    data = TelegramChannelData(channel_name="Test", member_count=1000)
    assert data.channel_name == "Test"
    assert data.member_count == 1000
    assert data.messages == []


def test_schema_instagram():
    data = InstagramProfileData(username="test", followers=5000)
    assert data.username == "test"
    assert data.followers == 5000
    assert data.is_verified is False


def test_schema_product():
    data = ProductData(name="iPhone", price="R$ 4.999")
    assert data.name == "iPhone"
    assert data.currency == "BRL"
    assert data.availability == "in_stock"
