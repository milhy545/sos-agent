"""SOS Agent client with multi-model support (AgentAPI, Gemini, OpenAI)."""

import logging
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

from .agentapi_client import AgentAPIClient
from .gemini_client import GeminiClient
from .openai_client import OpenAIClient
from .inception_client import InceptionClient
from .config import SOSConfig

logger = logging.getLogger(__name__)


class SOSAgentClient:
    """
    SOS Agent client for system rescue operations.

    Supports multiple AI providers:
    - Claude via AgentAPI (OAuth, no API key needed)
    - Google Gemini (requires GEMINI_API_KEY)
    - OpenAI (requires OPENAI_API_KEY)
    - Inception Labs Mercury (requires INCEPTION_API_KEY)
    """

    def __init__(self, config: SOSConfig):
        """
        Initialize SOS Agent client.

        Args:
            config: SOS Agent configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize AI client based on provider
        if config.ai_provider == "claude-agentapi":
            self.client = AgentAPIClient(
                api_url="http://localhost:3284",
                claude_path="/usr/bin/claude",
            )
            self.client_type = "agentapi"
        elif config.ai_provider == "gemini":
            self.client = GeminiClient(
                api_key=config.gemini_api_key,
                model=config.gemini_model,
            )
            self.client_type = "gemini"
        elif config.ai_provider == "openai":
            self.client = OpenAIClient(
                api_key=config.openai_api_key,
                model=config.openai_model,
            )
            self.client_type = "openai"
        elif config.ai_provider == "inception":
            self.client = InceptionClient(
                api_key=config.inception_api_key,
                model=config.inception_model,
                language=config.ai_language,
            )
            self.client_type = "inception"
        else:
            raise ValueError(f"Unknown AI provider: {config.ai_provider}")

        self.logger.info(f"SOS Agent initialized with provider: {config.ai_provider}")

    async def execute_rescue_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Execute a rescue task with comprehensive error handling.

        Args:
            task: Task description for the agent
            context: Additional context (emergency_mode, system_state, etc.)
            stream: Whether to stream responses

        Yields:
            Response messages from the agent
        """
        ctx = context or {}

        # Add system context to task
        ctx.setdefault("emergency_mode", self.config.emergency_mode)
        ctx.setdefault("shell", self.config.shell)
        ctx.setdefault("critical_services", self.config.critical_services)

        # Build contextualized task
        full_task = self._build_task_with_context(task, ctx)

        self.logger.info(
            f"Executing rescue task via {self.client_type}: {task[:100]}..."
        )
        self.logger.debug(f"Context: {ctx}")

        try:
            if self.client_type == "agentapi":
                # AgentAPI workflow
                await self.client.start_server()

                async for response_chunk in self.client.query_stream(full_task):
                    yield response_chunk

                await self.client.stop_server()

            elif self.client_type in ["gemini", "openai", "inception"]:
                # Direct API workflow (Gemini/OpenAI/Inception)
                async for response_chunk in self.client.query(
                    full_task, context=ctx, stream=stream
                ):
                    yield response_chunk

        except Exception as e:
            self.logger.critical(
                f"{self.client_type.upper()} error: {e}", exc_info=True
            )
            yield f"❌ ERROR: {str(e)}\\n\\nℹ️  Check your {self.client_type.upper()} configuration"

    def _build_task_with_context(self, task: str, context: Dict[str, Any]) -> str:
        """
        Build task with system context prepended.

        Args:
            task: Original task
            context: Context dict

        Returns:
            Task with context
        """
        context_str = f"""
System Context:
- Emergency Mode: {context.get('emergency_mode', False)}
- Shell: {context.get('shell', 'zsh')}
- Critical Services: {', '.join(context.get('critical_services', []))}

IMPORTANT SAFETY RULES:
- NEVER stop or disable: {', '.join(context.get('critical_services', []))}
- Always explain before making changes
- Verify changes don't break system stability

Task:
{task}
"""
        return context_str.strip()

    async def execute_emergency_diagnostics(self) -> AsyncIterator[str]:
        """
        Execute emergency diagnostics without agent.

        Fallback when agent fails - runs basic system checks directly.
        """
        self.logger.warning("Executing emergency fallback diagnostics")

        import subprocess

        try:
            # Basic system info
            commands = [
                ("Free Memory", f"{self.config.shell} -c 'free -h'"),
                ("Disk Space", f"{self.config.shell} -c 'df -h'"),
                ("System Load", f"{self.config.shell} -c 'uptime'"),
                (
                    "Critical Services",
                    f"{self.config.shell} -c 'systemctl status sshd NetworkManager'",
                ),
            ]

            results = []
            for name, cmd in commands:
                try:
                    result = subprocess.run(
                        cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=10,
                        shell=True,
                    )
                    output = result.stdout or result.stderr
                    results.append(f"### {name}\\n```\\n{output}\\n```\\n")
                except Exception as e:
                    results.append(f"### {name}\\n❌ Error: {e}\\n")

            yield "\\n".join(results)

        except Exception as e:
            self.logger.critical(f"Emergency diagnostics failed: {e}")
            yield f"❌ Emergency diagnostics failed: {e}"
