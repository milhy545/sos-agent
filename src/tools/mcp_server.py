"""In-process MCP server for SOS Agent custom tools."""

import logging

logger = logging.getLogger(__name__)


def create_sos_mcp_server():
    """
    Create in-process MCP server with SOS system tools.

    NOTE: This is a placeholder for future MCP integration.
    The Claude Agent SDK's create_sdk_mcp_server may not be available
    in the current version, so we'll register tools differently.

    For now, tools can be called directly from the agent via custom
    tool definitions in .claude/CLAUDE.md
    """
    logger.info("MCP server creation requested")

    # TODO: Implement when SDK supports in-process MCP servers
    # For now, tools are available via direct Python calls

    return None
