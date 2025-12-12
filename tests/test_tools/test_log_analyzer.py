import pytest
from unittest.mock import patch, AsyncMock
from src.tools.log_analyzer import analyze_system_logs


@pytest.mark.asyncio
async def test_analyze_system_logs_success():
    """Test successful log analysis."""
    with patch("asyncio.create_subprocess_exec") as mock_shell:
        process_all = AsyncMock()
        process_all.communicate.return_value = (
            b'{"MESSAGE": "Test error", "_SYSTEMD_UNIT": "test.service", "PRIORITY": "3", "__REALTIME_TIMESTAMP": "1630000000000"}\n',
            b"",
        )
        process_all.returncode = 0

        process_kernel = AsyncMock()
        process_kernel.communicate.return_value = (
            b'{"MESSAGE": "Kernel error", "_SYSTEMD_UNIT": "kernel", "PRIORITY": "3", "__REALTIME_TIMESTAMP": "1630000000000"}\n',
            b"",
        )
        process_kernel.returncode = 0

        mock_shell.side_effect = [process_all, process_kernel]

        results = await analyze_system_logs()

        assert len(results["service_errors"]) > 0
        assert "Test error" in results["service_errors"][0]["message"]
        assert "Kernel error" in results["service_errors"][1]["message"]


@pytest.mark.asyncio
async def test_analyze_system_logs_kernel_failure_silenced():
    """
    Test the BUG where kernel log failure is ignored if system logs succeed.
    """
    with patch("asyncio.create_subprocess_exec") as mock_shell:
        # Setup mock for process_all (SUCCESS)
        process_all = AsyncMock()
        process_all.communicate.return_value = (
            b'{"MESSAGE": "System ok", "PRIORITY": "6"}\n',
            b"",
        )
        process_all.returncode = 0

        # Setup mock for process_kernel (FAILURE)
        process_kernel = AsyncMock()
        process_kernel.communicate.return_value = (
            b"",
            b"Permission denied for kernel logs",
        )
        process_kernel.returncode = 1

        # Configure side_effect
        mock_shell.side_effect = [process_all, process_kernel]

        results = await analyze_system_logs()

        recommendations = results.get("recommendations", [])

        # We specifically want to see a warning about journalctl failing or permission denied
        # The current code swallows the kernel error completely if process_all succeeds.

        warning_found = False
        for r in recommendations:
            if (
                "failed to read" in r.lower()
                or "permission denied" in r.lower()
                or "kernel logs" in r.lower()
            ):
                warning_found = True
                break

        assert (
            warning_found
        ), f"Should report kernel log retrieval failure. Actual: {recommendations}"


@pytest.mark.asyncio
async def test_analyze_system_logs_all_failure():
    """Test when system logs fail."""
    with patch("asyncio.create_subprocess_exec") as mock_shell:
        process_all = AsyncMock()
        process_all.communicate.return_value = (b"", b"Journalctl failed")
        process_all.returncode = 1

        process_kernel = AsyncMock()
        process_kernel.communicate.return_value = (b"", b"")
        process_kernel.returncode = 1

        mock_shell.side_effect = [process_all, process_kernel]

        results = await analyze_system_logs()

        recommendations = results["recommendations"]
        assert any("Failed to read journalctl" in r for r in recommendations)


@pytest.mark.asyncio
async def test_analyze_system_logs_parsing():
    """Test parsing of various log formats."""
    with patch("asyncio.create_subprocess_exec") as mock_shell:
        process_all = AsyncMock()
        output = b"""
        {"MESSAGE": "Hardware error CPU", "_SYSTEMD_UNIT": "", "PRIORITY": "3"}
        Invalid JSON line
        {"MESSAGE": "Driver failed", "_SYSTEMD_UNIT": "nvidia", "PRIORITY": "3"}
        """
        process_all.communicate.return_value = (output.strip(), b"")
        process_all.returncode = 0

        process_kernel = AsyncMock()
        process_kernel.communicate.return_value = (b"", b"")
        process_kernel.returncode = 0

        mock_shell.side_effect = [process_all, process_kernel]

        results = await analyze_system_logs()

        assert len(results["hardware_errors"]) == 1
        assert len(results["driver_errors"]) == 1
