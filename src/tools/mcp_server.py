"""In-process MCP server for SOS Agent custom tools."""

import logging
from typing import Any, Dict

from claude_agent_sdk import create_sdk_mcp_server, tool
from claude_agent_sdk.types import McpSdkServerConfig

from src.tools.log_analyzer import analyze_system_logs_mcp

logger = logging.getLogger(__name__)


def create_sos_mcp_server() -> McpSdkServerConfig:
    """
    Create in-process MCP server with SOS system tools.

    Returns:
        McpSdkServerConfig: Configuration for the MCP server.
    """
    logger.info("Creating SOS MCP server with system tools")

    # Register tools
    @tool(
        name="analyze_system_logs",
        description="Analyze system logs (journalctl) for errors, warnings, and security issues.",
        input_schema={
            "log_path": str,
            "time_range": str,
            "severity": str,
        },
    )
    async def analyze_logs_wrapper(args: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper for log analyzer tool."""
        # Ensure args are strings as expected by the underlying function
        str_args: Dict[str, str] = {k: str(v) for k, v in args.items()}
        return await analyze_system_logs_mcp(str_args)

    # Create server
    server_config = create_sdk_mcp_server(
        name="sos-tools",
        version="1.0.0",
        tools=[analyze_logs_wrapper],
    )

    return server_config
