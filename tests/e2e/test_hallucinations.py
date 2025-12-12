import pytest
from unittest.mock import MagicMock
from asyncclick.testing import CliRunner as AsyncCliRunner
from src.cli import cli

@pytest.mark.asyncio
async def test_clean_system_empty_logs(monkeypatch):
    """
    Phase 6: Hallucination Check - Clean System
    Mock empty logs.
    Expect: Prompt clearly shows 0 errors.
    """
    monkeypatch.setenv("INCEPTION_API_KEY", "test")

    # Mock log analyzer to return clean result
    async def fake_analyze(*args, **kwargs):
        return {
            "hardware_errors": [],
            "driver_errors": [],
            "service_errors": [],
            "security_warnings": [],
            "recommendations": ["✅ No error level issues found"]
        }

    monkeypatch.setattr("src.cli.analyze_system_logs", fake_analyze)

    # Mock subprocess (system info)
    async def fake_create_subprocess_shell(cmd, **kwargs):
        mock_proc = MagicMock()
        mock_proc.returncode = 0

        # Async mock for communicate
        async def async_communicate():
            return (b"", b"")

        mock_proc.communicate = async_communicate
        return mock_proc

    monkeypatch.setattr("asyncio.create_subprocess_shell", fake_create_subprocess_shell)

    # Mock Client to verify prompt
    captured_prompt = ""
    async def fake_query(self, prompt, context=None, stream=True):
        nonlocal captured_prompt
        captured_prompt = prompt
        yield "System is clean."

    monkeypatch.setattr("src.agent.client.InceptionClient.query", fake_query)

    runner = AsyncCliRunner()
    # Need to set provider to inception to hit the mock
    await runner.invoke(cli, ["--provider", "inception", "diagnose"])

    assert "Hardware errors: 0" in captured_prompt
    assert "Service errors: 0" in captured_prompt

@pytest.mark.asyncio
async def test_os_context_debian(monkeypatch):
    """
    Phase 6: Hallucination Check - OS Context
    Mock /etc/os-release as Debian.
    Expect: Prompt contains Debian.
    """
    monkeypatch.setenv("INCEPTION_API_KEY", "test")

    # Mock logs
    async def fake_analyze(*args, **kwargs):
        return {"hardware_errors": [], "driver_errors": [], "service_errors": [], "security_warnings": [], "recommendations": []}
    monkeypatch.setattr("src.cli.analyze_system_logs", fake_analyze)

    # Mock subprocess for OS release
    async def fake_create_subprocess_shell(cmd, **kwargs):
        mock_proc = MagicMock()
        mock_proc.returncode = 0

        stdout = b""
        if "os-release" in cmd:
            stdout = b"NAME=Debian\nID=debian"

        async def async_communicate():
            return (stdout, b"")

        mock_proc.communicate = async_communicate
        return mock_proc

    monkeypatch.setattr("asyncio.create_subprocess_shell", fake_create_subprocess_shell)

    # Mock Client
    captured_prompt = ""
    async def fake_query(self, prompt, context=None, stream=True):
        nonlocal captured_prompt
        captured_prompt = prompt
        yield "Use apt-get install..."

    monkeypatch.setattr("src.agent.client.InceptionClient.query", fake_query)

    runner = AsyncCliRunner()
    await runner.invoke(cli, ["--provider", "inception", "diagnose"])

    assert "Debian" in captured_prompt
