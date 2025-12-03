"""AgentAPI client for SOS Agent - uses HTTP API to control Claude Code."""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class AgentAPIClient:
    """
    Client for Coder AgentAPI - controls Claude Code via HTTP.

    Uses your Claude CLI OAuth authentication automatically.
    No API keys required!
    """

    def __init__(
        self,
        api_url: str = "http://localhost:3284",
        agentapi_path: Optional[str] = None,
        claude_path: str = "/usr/bin/claude",
    ):
        """
        Initialize AgentAPI client.

        Args:
            api_url: AgentAPI server URL
            agentapi_path: Path to agentapi binary (auto-detected if None)
            claude_path: Path to Claude CLI
        """
        self.api_url = api_url
        self.claude_path = claude_path
        self.server_process: Optional[subprocess.Popen] = None

        # Auto-detect agentapi binary
        if agentapi_path is None:
            project_root = Path(__file__).parent.parent.parent
            agentapi_path = str(project_root / "agentapi")

        self.agentapi_path = agentapi_path

        logger.info(f"AgentAPI client initialized: {api_url}")

    async def start_server(self) -> None:
        """Start AgentAPI server in background."""
        # Check if our managed process is running
        if self.server_process and self.server_process.poll() is None:
            logger.info("AgentAPI server already running (managed process)")
            return

        # Check if server is already running (external process)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status < 500:
                        logger.info("AgentAPI server already running (external process)")
                        return
        except (aiohttp.ClientError, asyncio.TimeoutError):
            # Server not running, proceed to start it
            pass

        logger.info(f"Starting AgentAPI server: {self.agentapi_path} server -- {self.claude_path}")

        try:
            self.server_process = subprocess.Popen(
                [self.agentapi_path, "server", "--", self.claude_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for server to be ready
            await asyncio.sleep(3)

            # Check if server started successfully
            if self.server_process.poll() is not None:
                stderr = self.server_process.stderr.read().decode() if self.server_process.stderr else ""
                raise RuntimeError(f"AgentAPI server failed to start: {stderr}")

            logger.info("AgentAPI server started successfully")

        except Exception as e:
            logger.error(f"Failed to start AgentAPI server: {e}")
            raise

    async def stop_server(self) -> None:
        """Stop AgentAPI server."""
        if self.server_process:
            logger.info("Stopping AgentAPI server")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None

    async def send_message(self, content: str) -> Dict[str, Any]:
        """
        Send a message to the agent.

        Args:
            content: Message content

        Returns:
            API response dict
        """
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": content,
                "type": "user"
            }

            async with session.post(
                f"{self.api_url}/message",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_messages(self) -> list[Dict[str, Any]]:
        """
        Get all messages in conversation.

        Returns:
            List of message dicts
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/messages") as response:
                response.raise_for_status()
                data = await response.json()
                # AgentAPI returns {"messages": [...]}
                return data.get("messages", [])

    async def query_stream(self, task: str) -> AsyncIterator[str]:
        """
        Send a query and stream responses.

        Args:
            task: Task description

        Yields:
            Response chunks
        """
        # Send message
        await self.send_message(task)

        # Poll for responses
        last_message_count = 0
        max_polls = 60  # 60 * 2 seconds = 2 minutes timeout
        poll_count = 0

        while poll_count < max_polls:
            await asyncio.sleep(2)  # Poll every 2 seconds

            try:
                messages = await self.get_messages()

                # Ensure messages is a list
                if not isinstance(messages, list):
                    logger.error(f"Expected list of messages, got: {type(messages)}")
                    messages = []

                # Check for new messages
                if len(messages) > last_message_count:
                    # Yield new messages
                    # Ensure last_message_count is int (not slice)
                    start_idx = int(last_message_count) if isinstance(last_message_count, (int, float)) else 0
                    new_messages = messages[start_idx:]
                    for msg in new_messages:
                        if isinstance(msg, dict) and msg.get("role") == "agent":
                            content = msg.get("content", "")
                            # Filter out TUI/welcome messages
                            if content and not content.startswith("╭"):
                                yield content

                    last_message_count = len(messages)

                # Check if agent is done (last message is from agent)
                if messages and isinstance(messages[-1], dict) and messages[-1].get("role") == "agent":
                    # Wait a bit more to ensure no more messages
                    await asyncio.sleep(3)
                    final_messages = await self.get_messages()

                    if isinstance(final_messages, list) and len(final_messages) == len(messages):
                        # No new messages, agent is done
                        break
                    elif isinstance(final_messages, list):
                        # New messages arrived, continue polling
                        last_message_count = len(messages)

            except Exception as e:
                logger.error(f"Error polling messages: {e}", exc_info=True)
                break

            poll_count += 1

        if poll_count >= max_polls:
            logger.warning("Query stream timed out")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_server()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_server()
