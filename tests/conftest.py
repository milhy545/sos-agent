import pytest
import os
import sys

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture
def mock_env(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("SOS_AI_LANGUAGE", "en")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("INCEPTION_API_KEY", "test_inception_key")
    monkeypatch.setenv("CLAUDE_API_KEY", "test_claude_key")
