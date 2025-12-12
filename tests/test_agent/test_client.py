import pytest
from unittest.mock import patch
from src.agent.client import SOSAgentClient
from src.agent.config import SOSConfig


@pytest.fixture
def mock_config():
    config = SOSConfig()
    config.gemini_api_key = "test_key"
    config.openai_api_key = "test_key"
    config.inception_api_key = "test_key"
    return config


def test_client_init_gemini(mock_config):
    mock_config.ai_provider = "gemini"
    with patch("src.agent.gemini_client.genai"):
        client = SOSAgentClient(mock_config)
        assert client.client_type == "gemini"


def test_client_init_openai(mock_config):
    mock_config.ai_provider = "openai"
    # It uses AsyncOpenAI, not OpenAI directly usually
    with patch("src.agent.openai_client.AsyncOpenAI"):
        client = SOSAgentClient(mock_config)
        assert client.client_type == "openai"


def test_client_init_invalid(mock_config):
    mock_config.ai_provider = "invalid"
    with pytest.raises(ValueError):
        SOSAgentClient(mock_config)


@pytest.mark.asyncio
async def test_execute_rescue_task_gemini(mock_config):
    mock_config.ai_provider = "gemini"

    # Mock GeminiClient
    with patch("src.agent.client.GeminiClient") as MockGemini:
        mock_gemini_instance = MockGemini.return_value

        # Setup async generator for query
        async def mock_query(*args, **kwargs):
            yield "Response chunk 1"
            yield "Response chunk 2"

        mock_gemini_instance.query.side_effect = mock_query

        client = SOSAgentClient(mock_config)

        responses = []
        async for chunk in client.execute_rescue_task("Fix system"):
            responses.append(chunk)

        assert responses == ["Response chunk 1", "Response chunk 2"]
        mock_gemini_instance.query.assert_called_once()

        # Verify context injection
        call_args = mock_gemini_instance.query.call_args
        task_arg = call_args[0][0]
        assert "System Context:" in task_arg
        assert "IMPORTANT SAFETY RULES:" in task_arg


@pytest.mark.asyncio
async def test_execute_rescue_task_error_handling(mock_config):
    mock_config.ai_provider = "gemini"
    with patch("src.agent.client.GeminiClient") as MockGemini:
        mock_instance = MockGemini.return_value
        mock_instance.query.side_effect = Exception("API Error")

        client = SOSAgentClient(mock_config)

        responses = []
        async for chunk in client.execute_rescue_task("Task"):
            responses.append(chunk)

        assert any("❌ ERROR" in r for r in responses)


@pytest.mark.asyncio
async def test_execute_emergency_diagnostics(mock_config):
    # This doesn't need a specific provider
    mock_config.ai_provider = "gemini"
    with patch("src.agent.client.GeminiClient"):  # Just to satisfy init
        client = SOSAgentClient(mock_config)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "Memory OK"
            mock_run.return_value.returncode = 0

            responses = []
            async for chunk in client.execute_emergency_diagnostics():
                responses.append(chunk)

            output = "".join(responses)
            assert "Free Memory" in output
            assert "Memory OK" in output
