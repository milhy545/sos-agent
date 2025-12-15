"""Claude SDK Client Adapter for SOS Agent."""

import logging
from typing import Any, AsyncIterator, Dict, Optional, Union

from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import (
    AssistantMessage,
    ClaudeAgentOptions,
    McpHttpServerConfig,
    McpSdkServerConfig,
    McpSSEServerConfig,
    McpStdioServerConfig,
    ResultMessage,
    TextBlock,
)
from src.tools.mcp_server import create_sos_mcp_server

logger = logging.getLogger(__name__)


class ClaudeSDKClientAdapter:
    """Adapter for ClaudeSDKClient to match SOS Agent interface."""

    def __init__(self, mcp_enabled: bool = True):
        self.mcp_enabled = mcp_enabled

    async def _create_client(self) -> ClaudeSDKClient:
        """Create and configure Claude SDK client."""
        mcp_servers: Dict[
            str,
            Union[
                McpStdioServerConfig,
                McpSSEServerConfig,
                McpHttpServerConfig,
                McpSdkServerConfig,
            ],
        ] = {}

        if self.mcp_enabled:
            sos_mcp = create_sos_mcp_server()
            # Use "sos-tools" as the server alias
            mcp_servers["sos-tools"] = sos_mcp
            logger.info("In-process MCP server 'sos-tools' enabled")

        options = ClaudeAgentOptions(
            mcp_servers=mcp_servers,
            # We can add more options here from SOSConfig if needed
        )

        return ClaudeSDKClient(options)

    async def query(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Execute query using Claude SDK.

        This handles the connection lifecycle for a single query.
        """
        try:
            client = await self._create_client()
        except Exception as e:
            logger.error(f"Failed to create Claude SDK client: {e}")
            yield f"❌ Error initializing Claude SDK: {e}"
            return

        logger.debug(f"Starting Claude SDK query: {task[:50]}...")

        try:
            async with client:
                # Send the task
                await client.query(task)

                # Stream responses
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                yield block.text
                    elif isinstance(message, ResultMessage):
                        # Conversation complete
                        pass

        except Exception as e:
            logger.error(f"Claude SDK query failed: {e}", exc_info=True)
            yield f"❌ Error during execution: {str(e)}"
