"""SOS Agent client with multi-model support (AgentAPI, Gemini, OpenAI)."""

import logging
from typing import Any, AsyncIterator, Dict, Optional

from .agentapi_client import AgentAPIClient
from .gemini_client import GeminiClient
from .openai_client import OpenAIClient
from .inception_client import InceptionClient
from .claude_sdk_client import ClaudeSDKClientAdapter
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

        provider = config.ai_provider
        if provider == "auto":
            provider = self._auto_select_provider(config)
            self.logger.info(f"Auto-selected provider: {provider}")
            self.config.ai_provider = provider

        # Initialize AI client based on provider
        self.client: Any
        if provider == "claude-agentapi":
            self.client = AgentAPIClient(
                api_url="http://localhost:3284",
                claude_path="/usr/bin/claude",
            )
            self.client_type = "agentapi"
        elif provider == "claude-sdk":
            self.client = ClaudeSDKClientAdapter(mcp_enabled=config.mcp_server_enabled)
            self.client_type = "claude-sdk"
        elif provider == "gemini":
            if not config.gemini_api_key:
                raise ValueError(
                    "Gemini provider vyžaduje GEMINI_API_KEY. "
                    "Doplňte klíč nebo zvolte jiného providera."
                )
            self.client = GeminiClient(
                api_key=config.gemini_api_key,
                model=config.gemini_model,
            )
            self.client_type = "gemini"
        elif provider == "openai":
            if not config.openai_api_key:
                raise ValueError(
                    "OpenAI provider vyžaduje OPENAI_API_KEY. "
                    "Doplňte klíč nebo zvolte jiného providera."
                )
            self.client = OpenAIClient(
                api_key=config.openai_api_key,
                model=config.openai_model,
            )
            self.client_type = "openai"
        elif provider == "inception":
            if not config.inception_api_key:
                raise ValueError(
                    "Inception provider vyžaduje INCEPTION_API_KEY. "
                    "Doplňte klíč nebo zvolte jiného providera."
                )
            self.client = InceptionClient(
                api_key=config.inception_api_key,
                model=config.inception_model,
                language=config.ai_language,
            )
            self.client_type = "inception"
        else:
            raise ValueError(f"Unknown AI provider: {provider}")

        self.logger.info(f"SOS Agent initialized with provider: {config.ai_provider}")

    def _auto_select_provider(self, config: SOSConfig) -> str:
        """Vyber providera podle dostupných klíčů nebo AgentAPI fallback."""
        if config.gemini_api_key:
            return "gemini"
        if config.inception_api_key:
            return "inception"
        if config.openai_api_key:
            return "openai"
        return "claude-agentapi"

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

        async def _query() -> AsyncIterator[str]:
            if self.client_type == "agentapi":
                await self.client.start_server()
                try:
                    async for response_chunk in self.client.query_stream(full_task):
                        yield response_chunk
                finally:
                    await self.client.stop_server()
            elif self.client_type in ["gemini", "openai", "inception", "claude-sdk"]:
                # Direct API workflow (Gemini/OpenAI/Inception/ClaudeSDK)
                async for response_chunk in self.client.query(
                    full_task, context=ctx, stream=stream
                ):
                    yield response_chunk

        try:
            async for chunk in _query():
                yield chunk
            return
        except Exception as e:
            self.logger.critical(
                f"{self.client_type.upper()} error: {e}", exc_info=True
            )

            fallback = self._get_fallback_provider(error=e)
            if fallback:
                self.logger.warning(
                    "Provider failover triggered",
                    extra={
                        "from": self.client_type,
                        "to": fallback,
                        "reason": str(e)[:200],
                    },
                )
                try:
                    self._switch_provider(fallback)
                    async for chunk in _query():
                        yield chunk
                    return
                except Exception as e2:
                    self.logger.critical(
                        f"Failover provider {fallback} error: {e2}", exc_info=True
                    )

            yield (
                f"❌ ERROR: {str(e)}\n\nℹ️  Check your {self.client_type.upper()} configuration"
            )

    def _switch_provider(self, provider: str) -> None:
        """Reinitialize underlying provider client in-place."""
        self.config.ai_provider = provider
        if provider == "claude-agentapi":
            self.client = AgentAPIClient(
                api_url="http://localhost:3284",
                claude_path="/usr/bin/claude",
            )
            self.client_type = "agentapi"
            return
        if provider == "gemini":
            self.client = GeminiClient(
                api_key=self.config.gemini_api_key,
                model=self.config.gemini_model,
            )
            self.client_type = "gemini"
            return
        if provider == "openai":
            self.client = OpenAIClient(
                api_key=self.config.openai_api_key,
                model=self.config.openai_model,
            )
            self.client_type = "openai"
            return
        if provider == "inception":
            self.client = InceptionClient(
                api_key=self.config.inception_api_key,
                model=self.config.inception_model,
                language=self.config.ai_language,
            )
            self.client_type = "inception"
            return
        raise ValueError(f"Unknown AI provider: {provider}")

    def _get_fallback_provider(self, error: Exception) -> Optional[str]:
        """Select a fallback provider for quota/rate issues."""
        msg = str(error).lower()
        is_quota = any(
            token in msg
            for token in (
                "quota",
                "resource_exhausted",
                "rate limit",
                "429",
                "too many requests",
            )
        )
        if not is_quota:
            return None

        if self.client_type == "gemini":
            if self.config.inception_api_key:
                return "inception"
            if self.config.openai_api_key:
                return "openai"
            if self.config.anthropic_api_key:
                return "claude-agentapi"
        return None

    def _build_task_with_context(self, task: str, context: Dict[str, Any]) -> str:
        """
        Build task with system context prepended.

        Args:
            task: Original task
            context: Context dict

        Returns:
            Task with context
        """
        language = (self.config.ai_language or "en").lower()
        language_instruction = (
            "Language: Czech (cs). Respond in Czech.\n"
            if language.startswith("cs")
            else "Language: English (en). Respond in English.\n"
        )

        context_str = f"""
{language_instruction}
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
