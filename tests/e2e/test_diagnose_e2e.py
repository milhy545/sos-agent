import asyncio
import os
from typing import Dict, Any

import pytest
from asyncclick.testing import CliRunner as AsyncCliRunner

from src.cli import cli


@pytest.mark.asyncio
async def test_diagnose_stub_provider(monkeypatch):
    """
    End-to-end diagnostika s mockovaným providerem a daty:
    - analyzátor vrací známé chyby
    - sběr systémových údajů je deterministický
    - provider vrátí výstup reagující na zjištěné chyby
    """

    # Zajistit, že auto provider zvolí Inception (Mercury) díky klíči v env
    monkeypatch.setenv("INCEPTION_API_KEY", "test_key")

    async def fake_analyze_system_logs(
        log_path: str = "/var/log", time_range: str = "24h", severity: str = "error"
    ) -> Dict[str, Any]:
        return {
            "hardware_errors": [],
            "driver_errors": [],
            "service_errors": [
                {
                    "timestamp": "2025-01-01 12:00:00",
                    "unit": "service-x.service",
                    "priority": "3",
                    "message": "Service X failed to start",
                }
            ],
            "security_warnings": [],
            "recommendations": ["Restart service-x.service"],
        }

    # Mock sběru logů
    monkeypatch.setattr("src.tools.log_analyzer.analyze_system_logs", fake_analyze_system_logs)
    monkeypatch.setattr("src.cli.analyze_system_logs", fake_analyze_system_logs)

    # Mock asynchronních subprocess výstupů (free/df/uptime/os-release/uname)
    class FakeProcess:
        def __init__(self, cmd: str):
            self.cmd = cmd
            self.returncode = 0

        async def communicate(self):
            if "free -h" in self.cmd:
                return (b"Mem: 1G 500M 500M", b"")
            if "df -h /" in self.cmd:
                return (b"/dev/sda1 10G 5G 5G 50% /", b"")
            if "uptime" in self.cmd:
                return (b"up 1 day, load average: 0.10", b"")
            if "cat /etc/os-release" in self.cmd:
                return (b"NAME=TestOS\nVERSION=1.0", b"")
            if "uname -a" in self.cmd:
                return (b"Linux test 5.10.0-0", b"")
            return (b"", b"")

    async def fake_create_subprocess_shell(cmd, *args, **kwargs):
        return FakeProcess(cmd)

    monkeypatch.setattr(
        "src.cli.asyncio.create_subprocess_shell", fake_create_subprocess_shell
    )

    # Mock Mercury klienta tak, aby reagoval na detekovanou službu
    async def fake_inception_query(self, prompt: str, context=None, stream=True):
        assert "service-x.service" in prompt  # kontrola, že se logy propsaly do promptu
        yield "Nalezen problém se službou service-x.service, doporučuji restart."

    monkeypatch.setattr("src.agent.client.InceptionClient.query", fake_inception_query)

    runner = AsyncCliRunner()
    result = await runner.invoke(cli, ["diagnose", "--category", "services"])

    assert result.exit_code == 0
    assert "service-x.service" in result.output
    assert "restart" in result.output.lower()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("RUN_E2E_MERCURY") or not os.getenv("INCEPTION_API_KEY"),
    reason="Vyžaduje Mercury (Inception) API klíč a RUN_E2E_MERCURY=1",
)
async def test_diagnose_mercury_live():
    """
    Volitelný integrační test proti reálnému Mercury (Inception) API.
    Spouští se pouze, pokud jsou k dispozici env proměnné.
    """
    runner = AsyncCliRunner()
    result = await runner.invoke(cli, ["--provider", "inception", "diagnose", "--category", "hardware"])

    # Základní ověření, že volání doběhlo a něco vrátilo
    assert result.exit_code == 0
    assert result.output.strip(), "Očekáváme nějaký výstup z Mercury"
