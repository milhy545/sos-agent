import os
import pytest
from src.agent.config import SOSConfig, load_config

def test_config_defaults():
    config = SOSConfig()
    assert config.permission_mode == "plan"
    assert config.ai_provider == "auto"
    assert config.emergency_mode is False
    assert "sshd" in config.critical_services
    assert config.ai_language == "en"

def test_config_from_env(mock_env):
    # mock_env fixture sets SOS_AI_LANGUAGE="en"
    config = SOSConfig()
    assert config.gemini_api_key == "test_gemini_key"
    assert config.openai_api_key == "test_openai_key"
    assert config.inception_api_key == "test_inception_key"

def test_load_config_default(tmp_path):
    # Test loading from default location (mocking file existence)
    # Since load_config checks hardcoded "config/default.yaml", we can pass a path

    config_file = tmp_path / "test_config.yaml"
    config = SOSConfig(ai_provider="openai", model="gpt-4-test")
    config.to_yaml(config_file)

    loaded_config = SOSConfig.from_yaml(config_file)
    assert loaded_config.ai_provider == "openai"
    assert loaded_config.model == "gpt-4-test"
    assert loaded_config.permission_mode == "plan"  # Default preserved

@pytest.mark.asyncio
async def test_load_config_async_wrapper(tmp_path):
    config_file = tmp_path / "test_config_async.yaml"
    config = SOSConfig(emergency_mode=True)
    config.to_yaml(config_file)

    loaded = await load_config(str(config_file))
    assert loaded.emergency_mode is True

def test_config_env_priority(monkeypatch):
    monkeypatch.setenv("SOS_AI_LANGUAGE", "cs")
    config = SOSConfig()
    assert config.ai_language == "cs"
