import pytest
from unittest.mock import MagicMock, AsyncMock
from src.agent.inception_client import InceptionClient


@pytest.mark.asyncio
async def test_mercury_language_cs(monkeypatch):
    """
    Phase 5: AI Consistency - Language
    Verify that setting language='cs' adds Czech instruction to system prompt.
    """
    monkeypatch.setenv("INCEPTION_API_KEY", "test")

    # Mock aiohttp
    mock_post = MagicMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()
    # Mock json response for non-stream
    mock_response.json.return_value = {"choices": [{"message": {"content": "Odpověď"}}]}
    # Mock context manager
    mock_post.return_value.__aenter__.return_value = mock_response

    # Capture the payload sent to post
    captured_payload = {}

    def side_effect(url, json, headers):
        nonlocal captured_payload
        captured_payload = json
        return mock_post.return_value

    # Mock ClientSession
    mock_session = MagicMock()
    mock_session.post.side_effect = side_effect

    mock_session_cls = MagicMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session

    monkeypatch.setattr("aiohttp.ClientSession", mock_session_cls)

    client = InceptionClient(language="cs")

    # Run query (non-stream for simplicity or stream=False)
    results = []
    async for chunk in client.query("Hello", stream=False):
        results.append(chunk)

    # Verify System Prompt
    system_msg = next(m for m in captured_payload["messages"] if m["role"] == "system")
    assert "Respond in Czech language (Čeština)." in system_msg["content"]
    assert "Use plain text formatting without ASCII tables" in system_msg["content"]


@pytest.mark.asyncio
async def test_quota_handling(monkeypatch):
    """
    Phase 5: Quota Handling
    Simulate 429 error.
    """
    monkeypatch.setenv("INCEPTION_API_KEY", "test")

    # Mock ClientSession raising exception
    MagicMock()
    # Create exception

    async def fake_query(*args, **kwargs):
        raise Exception("429 Too Many Requests")

    client = InceptionClient()
    # Monkeypatch query directly to simulate failure logic inside query is harder with inner context managers
    # But InceptionClient catches Exception.

    # Let's mock aiohttp.ClientSession to raise inside post
    mock_session_cls = MagicMock()
    mock_session_inst = MagicMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session_inst

    mock_post = MagicMock()
    mock_post.side_effect = Exception("429 Too Many Requests")
    mock_session_inst.post = mock_post

    monkeypatch.setattr("aiohttp.ClientSession", mock_session_cls)

    results = []
    async for chunk in client.query("test"):
        results.append(chunk)

    output = "".join(results)
    assert "❌ Inception Labs API Error" in output
    assert "429 Too Many Requests" in output
