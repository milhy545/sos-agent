import pytest
from unittest.mock import patch, MagicMock
from asyncclick.testing import CliRunner as AsyncCliRunner
from src.agent.permissions import safe_permission_handler
from src.cli import cli

@pytest.mark.asyncio
async def test_critical_services_protection():
    """
    Phase 3: Critical Services Protection (Logic Unit Test)
    Attempt to stop sshd, NetworkManager, ollama.
    Expect: HARD DENY.
    """
    critical_cmds = [
        "systemctl stop sshd",
        "systemctl stop NetworkManager",
        "systemctl stop ollama",
        "systemctl disable tailscaled"
    ]

    for cmd in critical_cmds:
        result = await safe_permission_handler(
            "Bash",
            {"command": cmd},
            {"emergency_mode": False}
        )
        assert result["behavior"] == "deny", f"Failed to block: {cmd}"
        assert "critical service" in result["reason"].lower()

@pytest.mark.asyncio
async def test_forbidden_commands():
    """
    Phase 3: Forbidden Commands (Logic Unit Test)
    Attempt rm -rf, mkfs.
    Expect: DENY (unless approved, but here checking detection).
    """
    forbidden = [
        "rm -rf /",
        "mkfs.ext4 /dev/sda1",
        "dd if=/dev/zero of=/dev/sda"
    ]

    for cmd in forbidden:
        result = await safe_permission_handler(
            "Bash",
            {"command": cmd},
            {"emergency_mode": False}
        )
        assert result["behavior"] == "deny", f"Failed to block: {cmd}"
        assert "restricted operation" in result["reason"].lower()

@pytest.mark.asyncio
async def test_emergency_whitelist():
    """
    Phase 4: Emergency Mode Whitelist (Logic Unit Test)
    Verify safe commands are allowed in emergency mode without extra checks.
    """
    safe_cmds = [
        "journalctl -xe",
        "free -h",
        "top -bn1"
    ]

    for cmd in safe_cmds:
        result = await safe_permission_handler(
            "Bash",
            {"command": cmd},
            {"emergency_mode": True}
        )
        assert result["behavior"] == "allow", f"Failed to whitelist: {cmd}"

@pytest.mark.asyncio
async def test_safety_integration_real(monkeypatch):
    """
    Phase 3: Integration Test
    Verify that the permission handler is ACTUALLY called during execution.
    """
    monkeypatch.setenv("INCEPTION_API_KEY", "test")

    # Mock Client to return a command suggestion
    # Note: Since the current client doesn't support 'tools',
    # we simulate it returning text, and check if any mechanism validates it.
    async def fake_query(self, prompt, context=None, stream=True):
        yield "I suggest running: systemctl stop sshd"

    monkeypatch.setattr("src.agent.client.InceptionClient.query", fake_query)

    # Spy on the handler
    # Note: We must patch it where it is used (src.cli) because it was imported with 'from'
    with patch("src.cli.safe_permission_handler", side_effect=safe_permission_handler) as mock_handler:
        runner = AsyncCliRunner()
        await runner.invoke(cli, ["--provider", "inception", "fix", "services"])

        # We expect the handler to be called because the agent suggested a command
        # (Assuming the system parses suggestions and checks permissions)
        assert mock_handler.called
