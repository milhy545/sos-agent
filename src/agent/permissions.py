"""Permission handling and safety controls for system operations."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Critical services that must NEVER be stopped or disabled
CRITICAL_SERVICES = [
    "sshd",
    "NetworkManager",
    "ollama",
    "tailscaled",
]

# Emergency whitelist - read-only commands auto-approved in emergency mode
EMERGENCY_WHITELIST = [
    "journalctl",
    "systemctl status",
    "free -h",
    "df -h",
    "ps aux",
    "top -bn1",
    "sensors",
    "lsblk",
    "ip addr",
    "ss -tulpn",
]

# Operations that always require explicit approval
RESTRICTED_OPERATIONS = [
    "systemctl stop",
    "systemctl disable",
    "rm -rf",
    "reboot",
    "shutdown",
    "mkfs",
    "dd if=",
]


async def safe_permission_handler(
    tool_name: str, input_data: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, str]:
    """
    Custom permission handler for system-level operations.

    Args:
        tool_name: Name of the tool being invoked
        input_data: Input parameters for the tool
        context: Additional context (emergency_mode, etc.)

    Returns:
        Permission decision dict with "behavior" and optional "reason"
    """
    emergency_mode = context.get("emergency_mode", False)

    # Check for critical tool usage
    if tool_name == "Bash":
        command = input_data.get("command", "")

        # Protect critical services
        for service in CRITICAL_SERVICES:
            if f"systemctl stop {service}" in command:
                logger.critical(
                    f"Blocked attempt to stop critical service: {service}"
                )
                return {
                    "behavior": "deny",
                    "reason": f"❌ Cannot stop critical service: {service}",
                }
            if f"systemctl disable {service}" in command:
                logger.critical(
                    f"Blocked attempt to disable critical service: {service}"
                )
                return {
                    "behavior": "deny",
                    "reason": f"❌ Cannot disable critical service: {service}",
                }

        # Check for restricted operations
        for op in RESTRICTED_OPERATIONS:
            if op in command:
                if not emergency_mode:
                    logger.warning(
                        f"Restricted operation requested: {op} (not in emergency mode)"
                    )
                    return {
                        "behavior": "deny",
                        "reason": f"⚠️  Restricted operation requires approval: {op}",
                    }

        # In emergency mode, allow whitelisted commands
        if emergency_mode:
            for allowed_cmd in EMERGENCY_WHITELIST:
                if command.startswith(allowed_cmd):
                    logger.info(f"Emergency whitelist allowed: {command}")
                    return {"behavior": "allow"}

    # Default: allow with logging
    logger.debug(f"Tool allowed: {tool_name}")
    return {"behavior": "allow"}


def is_safe_read_operation(command: str) -> bool:
    """Check if a command is a safe read-only operation."""
    safe_commands = [
        "cat",
        "less",
        "head",
        "tail",
        "grep",
        "find",
        "ls",
        "journalctl",
        "systemctl status",
        "free",
        "df",
        "du",
        "ps",
        "top",
        "htop",
        "sensors",
        "lsblk",
        "lsmod",
        "ip",
        "ss",
        "netstat",
    ]

    return any(command.strip().startswith(cmd) for cmd in safe_commands)
