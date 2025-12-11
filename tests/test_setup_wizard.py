import pytest
from unittest.mock import Mock, patch, MagicMock
from src.setup_wizard import get_api_key, setup_wizard
import io
import sys

def test_get_api_key_valid():
    with patch("builtins.input", return_value="valid_api_key_123"):
        with patch("builtins.print") as mock_print:
            key = get_api_key("Test", "ENV_VAR", "url", optional=False)
            assert key == "valid_api_key_123"

def test_get_api_key_optional_skip():
    with patch("builtins.input", return_value=""):
        key = get_api_key("Test", "ENV_VAR", "url", optional=True)
        assert key == ""

def test_get_api_key_required_retry():
    with patch("builtins.input", side_effect=["", "valid_key_12345"]):
        with patch("builtins.print") as mock_print:
            key = get_api_key("Test", "ENV_VAR", "url", optional=False)
            assert key == "valid_key_12345"

def test_setup_wizard_flow(tmp_path):
    # Mock input sequence:
    # 1. "y" (start)
    # 2. "1" (English)
    # 3. "gemini_key_12345" (Gemini)
    # 4. "" (OpenAI skip)
    # 5. "" (Inception skip)

    inputs = ["y", "1", "gemini_key_12345", "", ""]

    with patch("builtins.input", side_effect=inputs):
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            setup_wizard()

            env_file = tmp_path / ".env"
            assert env_file.exists()
            content = env_file.read_text()
            assert "GEMINI_API_KEY=gemini_key_12345" in content
            assert "SOS_AI_LANGUAGE=en" in content
            assert "OPENAI_API_KEY" not in content # Skipped

def test_setup_wizard_cancel():
    with patch("builtins.input", return_value="n"):
        with pytest.raises(SystemExit):
            setup_wizard()

def test_setup_wizard_existing_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING_VAR=value\nGEMINI_API_KEY=old_key\n")

    inputs = ["y", "2", "new_gemini_key_12345", "", ""] # Czech language

    with patch("builtins.input", side_effect=inputs):
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            setup_wizard()

            content = env_file.read_text()
            assert "EXISTING_VAR=value" in content
            assert "GEMINI_API_KEY=new_gemini_key_12345" in content
            assert "SOS_AI_LANGUAGE=cs" in content
