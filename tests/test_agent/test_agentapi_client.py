import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.agent.agentapi_client import AgentAPIClient
import aiohttp


@pytest.fixture
def api_client():
    return AgentAPIClient(api_url="http://test-url", agentapi_path="/bin/agentapi")


@pytest.mark.asyncio
async def test_start_server_already_managed(api_client):
    api_client.server_process = Mock()
    api_client.server_process.poll.return_value = None  # Running

    await api_client.start_server()

    # Should not start new process
    api_client.server_process.poll.assert_called()


@pytest.mark.asyncio
async def test_start_server_external(api_client):
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = MockSession.return_value
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.get.return_value.__aenter__.return_value = mock_response

        await api_client.start_server()

        # Should detect external server and return without starting new one
        assert api_client.server_process is None


@pytest.mark.asyncio
async def test_start_server_success(api_client):
    with patch("aiohttp.ClientSession") as MockSession:
        # Mock external check failure
        mock_session = MockSession.return_value
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.side_effect = aiohttp.ClientError("Not running")

        with patch("subprocess.Popen") as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None  # Running successfully
            mock_popen.return_value = mock_process

            # Reduce sleep time
            with patch("asyncio.sleep", return_value=None):
                await api_client.start_server()

            assert api_client.server_process == mock_process
            mock_popen.assert_called_once()


@pytest.mark.asyncio
async def test_stop_server(api_client):
    mock_process = Mock()
    api_client.server_process = mock_process

    await api_client.stop_server()

    mock_process.terminate.assert_called_once()
    assert api_client.server_process is None


@pytest.mark.asyncio
async def test_send_message(api_client):
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = MockSession.return_value
        mock_session.__aenter__.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_session.post.return_value.__aenter__.return_value = mock_response

        result = await api_client.send_message("Hello")

        assert result == {"status": "ok"}
        mock_session.post.assert_called()


@pytest.mark.asyncio
async def test_get_messages(api_client):
    with patch("aiohttp.ClientSession") as MockSession:
        mock_session = MockSession.return_value
        mock_session.__aenter__.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "messages": [{"role": "agent", "content": "Hi"}]
        }
        mock_session.get.return_value.__aenter__.return_value = mock_response

        messages = await api_client.get_messages()

        assert len(messages) == 1
        assert messages[0]["content"] == "Hi"


@pytest.mark.asyncio
async def test_query_stream(api_client):
    # Mock send_message
    api_client.send_message = AsyncMock()

    # Mock get_messages sequence
    # 1. No messages
    # 2. One agent message
    # 3. Same message (agent done)
    api_client.get_messages = AsyncMock(
        side_effect=[
            [],
            [{"role": "agent", "content": "Hello"}],
            [{"role": "agent", "content": "Hello"}],
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        chunks = []
        async for chunk in api_client.query_stream("Task"):
            chunks.append(chunk)

        assert chunks == ["Hello"]
