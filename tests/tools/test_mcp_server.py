"""Tests for SOS Agent MCP Server."""

import pytest
from unittest.mock import MagicMock, patch
from src.tools.mcp_server import create_sos_mcp_server


@pytest.fixture
def mock_claude_sdk():
    """Mock claude_agent_sdk to avoid runtime dependencies during test."""
    with patch("src.tools.mcp_server.create_sdk_mcp_server") as mock_create, \
         patch("src.tools.mcp_server.tool") as mock_tool:

        # Configure tool decorator to return the function it decorates (or a mock wrapper)
        def tool_decorator(name, description, input_schema=None):
            def decorator(func):
                return func
            return decorator

        mock_tool.side_effect = tool_decorator
        yield mock_create


def test_create_sos_mcp_server_success(mock_claude_sdk):
    """Test successful creation of SOS MCP server."""
    # Call the function
    result = create_sos_mcp_server()

    # Verify create_sdk_mcp_server was called
    assert mock_claude_sdk.called

    # Get arguments passed to create_sdk_mcp_server
    args, kwargs = mock_claude_sdk.call_args

    # Check server name
    assert kwargs.get("name") == "sos-tools" or args[0] == "sos-tools"

    # Check tools list
    tools = kwargs.get("tools")
    assert tools is not None
    assert len(tools) > 0

    # Check if analyze_system_logs_mcp is in the tools list
    # Since we mocked the decorator to return the function, the tool in list should be the function
    tool_func = tools[0]
    assert tool_func.__name__ == "analyze_logs_wrapper"


def test_create_sos_mcp_server_returns_config(mock_claude_sdk):
    """Test that function returns the config object from SDK."""
    mock_config = MagicMock()
    mock_claude_sdk.return_value = mock_config

    result = create_sos_mcp_server()

    assert result == mock_config
