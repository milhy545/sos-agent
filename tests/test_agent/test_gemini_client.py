import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.agent.gemini_client import GeminiClient
from google.generativeai.types import GenerationConfig

@pytest.fixture
def gemini_client(mock_env):
    with patch("src.agent.gemini_client.genai.configure"):
        with patch("src.agent.gemini_client.genai.GenerativeModel") as MockModel:
            client = GeminiClient(api_key="test_key")
            return client

def test_init(gemini_client):
    assert gemini_client.model_name == "gemini-2.0-flash-exp"
    assert gemini_client.api_key == "test_key"

@pytest.mark.asyncio
async def test_query_stream(gemini_client):
    mock_response = [
        Mock(text="Chunk 1"),
        Mock(text="Chunk 2")
    ]
    gemini_client.model.generate_content.return_value = mock_response

    chunks = []
    async for chunk in gemini_client.query("prompt", stream=True):
        chunks.append(chunk)

    assert chunks == ["Chunk 1", "Chunk 2"]

@pytest.mark.asyncio
async def test_query_non_stream(gemini_client):
    mock_response = Mock(text="Full response")
    gemini_client.model.generate_content.return_value = mock_response

    chunks = []
    async for chunk in gemini_client.query("prompt", stream=False):
        chunks.append(chunk)

    assert chunks == ["Full response"]

@pytest.mark.asyncio
async def test_query_error(gemini_client):
    gemini_client.model.generate_content.side_effect = Exception("API Error")

    chunks = []
    async for chunk in gemini_client.query("prompt"):
        chunks.append(chunk)

    assert any("Gemini API Error" in c for c in chunks)
