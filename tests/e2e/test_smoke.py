import os
import sys
import pytest
from unittest.mock import MagicMock
from src.agent.config import SOSConfig
from src.agent.client import SOSAgentClient
from src.cli import cli
from asyncclick.testing import CliRunner as AsyncCliRunner

@pytest.mark.asyncio
async def test_python_version():
    """Verify running on Python 3.11+."""
    assert sys.version_info >= (3, 11), "SOS Agent requires Python 3.11+"

@pytest.mark.asyncio
async def test_provider_init_gemini(monkeypatch):
    """Verify Gemini provider initialization."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    config = SOSConfig(ai_provider="gemini")
    # Force the key because config default factory uses os.getenv at instantiation
    # but we are creating clean config.
    # Actually, SOSConfig() calls os.getenv in default_factory.
    # So monkeypatching before init is correct.

    # We need to verify SOSAgentClient init
    client = SOSAgentClient(config)
    assert client.client_type == "gemini"
    assert client.config.gemini_api_key == "test_key"

@pytest.mark.asyncio
async def test_provider_init_mercury(monkeypatch):
    """Verify Mercury (Inception) provider initialization."""
    monkeypatch.setenv("INCEPTION_API_KEY", "test_key")
    config = SOSConfig(ai_provider="inception")
    client = SOSAgentClient(config)
    assert client.client_type == "inception"
    assert client.config.inception_api_key == "test_key"

@pytest.mark.asyncio
async def test_provider_init_openai(monkeypatch):
    """Verify OpenAI provider initialization."""
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    config = SOSConfig(ai_provider="openai")
    client = SOSAgentClient(config)
    assert client.client_type == "openai"
    assert client.config.openai_api_key == "test_key"

@pytest.mark.asyncio
async def test_env_loading_behavior(monkeypatch):
    """
    Verify that SOSConfig picks up environment variables.
    Note: Actual .env file loading is handled by the shell wrapper (install.sh)
    or Poetry, not by the Python code itself (no python-dotenv).
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env_defined_key")
    config = SOSConfig()
    assert config.anthropic_api_key == "env_defined_key"

@pytest.mark.asyncio
async def test_cli_help():
    """Smoke test for CLI entry point."""
    runner = AsyncCliRunner()
    result = await runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "SOS Agent" in result.output
