import pytest
from asyncclick.testing import CliRunner as AsyncCliRunner
from unittest.mock import MagicMock, patch
from src.cli import cli

@pytest.mark.asyncio
async def test_full_user_journey(monkeypatch):
    """
    Simulate a full session: diagnose -> fix -> optimize.
    """
    monkeypatch.setenv("INCEPTION_API_KEY", "test")

    # Mock Log Analysis
    async def fake_analyze(*args, **kwargs):
        return {
            "hardware_errors": [],
            "driver_errors": [{"message": "NVIDIA error", "unit": "kernel", "timestamp": "2025-01-01 00:00:00"}],
            "service_errors": [],
            "security_warnings": [],
            "recommendations": ["Update driver"]
        }
    monkeypatch.setattr("src.cli.analyze_system_logs", fake_analyze)

    # Mock Subprocess (shared)
    async def fake_subprocess(cmd, **kwargs):
        mock_proc = MagicMock()
        mock_proc.returncode = 0

        stdout = b""
        if "os-release" in cmd:
            stdout = b"NAME=Ubuntu"
        elif "-k" in cmd:
            stdout = b"NVIDIA error"

        async def async_communicate():
            return (stdout, b"")
        mock_proc.communicate = async_communicate
        return mock_proc

    monkeypatch.setattr("asyncio.create_subprocess_shell", fake_subprocess)

    # Mock Client
    async def fake_query(self, prompt, context=None, stream=True):
        # Specific prompts first
        if "Fix" in prompt and "issues detected" in prompt:
            yield "Fixing GPU... done."
        elif "Optimize" in prompt:
            yield "Optimizing apps... done."
        elif "Analyze" in prompt:
            yield "Diagnostic Result: GPU issue found."
        else:
            yield "OK"

    monkeypatch.setattr("src.agent.client.InceptionClient.query", fake_query)

    runner = AsyncCliRunner()

    # Step 1: Diagnose
    res1 = await runner.invoke(cli, ["--provider", "inception", "diagnose", "--category", "hardware"])
    assert res1.exit_code == 0
    assert "GPU issue found" in res1.output

    # Step 2: Fix
    res2 = await runner.invoke(cli, ["--provider", "inception", "fix", "hardware"])
    assert res2.exit_code == 0
    assert "Fixing GPU" in res2.output

    # Step 3: Optimize
    res3 = await runner.invoke(cli, ["--provider", "inception", "optimize-apps", "--platform", "docker"])
    assert res3.exit_code == 0
    assert "Optimizing apps" in res3.output
