import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.agent.inception_client import InceptionClient
import aiohttp
import json

@pytest.fixture
def client():
    return InceptionClient(api_key="test_key", language="en")

def test_init_check(client):
    assert client.api_key == "test_key"
    assert client.language == "en"

def test_init_failed():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            InceptionClient()

@pytest.mark.asyncio
async def test_query_non_stream(client):
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = MockSession.return_value
        mock_session.__aenter__.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response content"}}]
        }
        mock_session.post.return_value.__aenter__.return_value = mock_response

        chunks = []
        async for chunk in client.query("Test", stream=False):
            chunks.append(chunk)

        assert chunks == ["Response content"]

@pytest.mark.asyncio
async def test_query_stream(client):
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = MockSession.return_value
        mock_session.__aenter__.return_value = mock_session

        mock_response = AsyncMock()

        # Simulate SSE lines
        lines = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
            b'data: {"choices": [{"delta": {"content": " World"}}]}\n',
            b'data: [DONE]\n'
        ]

        async def content_iterator():
            for line in lines:
                yield line

        mock_response.content = content_iterator()
        mock_session.post.return_value.__aenter__.return_value = mock_response

        chunks = []
        async for chunk in client.query("Test", stream=True):
            chunks.append(chunk)

        assert chunks == ["Hello", " World"]

@pytest.mark.asyncio
async def test_query_stream_error(client):
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = MockSession.return_value
        mock_session.__aenter__.return_value = mock_session

        mock_session.post.side_effect = Exception("Network Error")

        chunks = []
        async for chunk in client.query("Test", stream=True):
            chunks.append(chunk)

        assert any("Error" in c for c in chunks)

def test_init_czech_language():
    client = InceptionClient(api_key="test", language="cs")
    assert client.language == "cs"
