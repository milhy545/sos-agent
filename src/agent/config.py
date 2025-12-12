"""Configuration management for SOS Agent."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class SOSConfig:
    """SOS Agent configuration."""

    # API Configuration
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    inception_api_key: str = field(
        default_factory=lambda: os.getenv("INCEPTION_API_KEY", "")
    )

    # Agent Options
    permission_mode: str = "plan"  # "plan" or "acceptEdits"
    emergency_mode: bool = False
    model: str = "claude-sonnet-4"
    ai_provider: str = "auto"  # auto-detect based on available keys
    gemini_model: str = "gemini-2.0-flash-exp"
    openai_model: str = "gpt-4o"
    inception_model: str = "mercury-coder"
    ai_language: str = field(
        default_factory=lambda: os.getenv("SOS_AI_LANGUAGE", "en")
    )  # "en" or "cs"

    # Tool Configuration
    allowed_tools: List[str] = field(
        default_factory=lambda: [
            "Read",
            "Write",
            "Bash",
            "Grep",
            "Glob",
            "analyze_system_logs",
            "check_system_health",
            "manage_processes",
            "emergency_cleanup",
        ]
    )
    disallowed_tools: List[str] = field(
        default_factory=lambda: ["WebSearch", "WebFetch"]
    )

    # Paths
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    config_dir: Path = field(default_factory=lambda: Path("config"))

    # System Context
    shell: str = "/bin/zsh"  # Alpine Linux uses ZSH
    ssh_port: int = 22
    critical_services: List[str] = field(
        default_factory=lambda: ["sshd", "NetworkManager", "ollama", "tailscaled"]
    )

    # ZEN Coordinator Integration
    zen_coordinator_url: Optional[str] = None
    memory_mcp_enabled: bool = False
    memory_mcp_port: Optional[int] = None

    @classmethod
    def from_yaml(cls, config_path: Path) -> "SOSConfig":
        """Load configuration from YAML file."""
        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})

    def to_yaml(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "permission_mode": self.permission_mode,
            "emergency_mode": self.emergency_mode,
            "ai_provider": self.ai_provider,
            "gemini_model": self.gemini_model,
            "openai_model": self.openai_model,
            "inception_model": self.inception_model,
            "ai_language": self.ai_language,
            "model": self.model,
            "allowed_tools": self.allowed_tools,
            "disallowed_tools": self.disallowed_tools,
            "log_dir": str(self.log_dir),
            "config_dir": str(self.config_dir),
            "shell": self.shell,
            "critical_services": self.critical_services,
        }

        if self.ssh_port != 22:
            data["ssh_port"] = self.ssh_port
        if self.zen_coordinator_url:
            data["zen_coordinator_url"] = self.zen_coordinator_url
        if self.memory_mcp_enabled:
            data["memory_mcp_enabled"] = self.memory_mcp_enabled
        if self.memory_mcp_port:
            data["memory_mcp_port"] = self.memory_mcp_port

        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)


async def load_config(config_path: Optional[str] = None) -> SOSConfig:
    """Load configuration from file or create default."""
    if config_path:
        path = Path(config_path)
        if path.exists():
            return SOSConfig.from_yaml(path)

    # Try default location
    default_path = Path("config/default.yaml")
    if default_path.exists():
        return SOSConfig.from_yaml(default_path)

    # Return default config
    config = SOSConfig()

    # Create default config file if it doesn't exist
    default_path.parent.mkdir(parents=True, exist_ok=True)
    config.to_yaml(default_path)

    return config
