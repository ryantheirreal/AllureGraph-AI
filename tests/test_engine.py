"""Tests for AllureGraph-AI core engine."""

import pytest
from core.engine import AllureGraphEngine, EngineConfig, TemplateEngine


def test_engine_config_defaults():
    config = EngineConfig()
    assert config.llm_provider == "openai"
    assert config.resolved_model == "gpt-4o-mini"
    assert config.temperature == 0.1
    assert config.headless is True


def test_engine_config_anthropic():
    config = EngineConfig(llm_provider="anthropic")
    assert config.resolved_model == "claude-sonnet-4-20250514"


def test_engine_config_custom_model():
    config = EngineConfig(llm_provider="openai", llm_model="gpt-4o")
    assert config.resolved_model == "gpt-4o"


def test_engine_initialization():
    engine = AllureGraphEngine()
    assert engine.config.llm_provider == "openai"


def test_engine_graph_config():
    engine = AllureGraphEngine(llm_provider="openai")
    config = engine._get_graph_config()
    assert "llm" in config
    assert config["headless"] is True
    assert config["verbose"] is False


def test_template_engine_list():
    templates = TemplateEngine.list_templates()
    assert len(templates) > 0
    assert "telegram_channel" in templates
    assert "instagram_profile" in templates


def test_template_engine_get():
    template = TemplateEngine.get_template("telegram_channel")
    assert template is not None
    assert "prompt" in template
    assert template["graph_type"] == "smart"


def test_template_engine_invalid():
    template = TemplateEngine.get_template("nonexistent")
    assert template is None


def test_format_output_json():
    engine = AllureGraphEngine()
    data = {"name": "test", "price": "$10"}
    result = engine._format_output(data, "json")
    assert result == data


def test_format_output_csv():
    engine = AllureGraphEngine()
    data = [{"name": "a"}, {"name": "b"}]
    result = engine._format_output(data, "csv")
    assert result["format"] == "csv"
    assert len(result["rows"]) == 2


def test_format_output_markdown():
    engine = AllureGraphEngine()
    data = {"name": "test", "price": "$10"}
    result = engine._format_output(data, "markdown")
    assert "test" in result
    assert "$10" in result
