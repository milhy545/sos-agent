import pytest
import json
from unittest.mock import MagicMock
from src.tools.log_analyzer import analyze_system_logs


# Helper to create JSON log line
def create_log_line(message, unit="kernel", priority="3", timestamp="1600000000000000"):
    return json.dumps(
        {
            "MESSAGE": message,
            "_SYSTEMD_UNIT": unit,
            "PRIORITY": priority,
            "__REALTIME_TIMESTAMP": timestamp,
        }
    )


@pytest.mark.asyncio
async def test_gpu_regression_radeon(monkeypatch):
    """
    Phase 2: GPU Driver (Regression #4)
    Inject kernel log: [drm:radeon_ib_ring_tests] *ERROR*
    Expect: Detection in driver_errors.
    """
    gpu_log = create_log_line("[drm:radeon_ib_ring_tests] *ERROR* ring gfx test failed")

    # Mock subprocess
    async def fake_create_subprocess_exec(program, *args, **kwargs):
        mock_proc = MagicMock()
        mock_proc.returncode = 0

        # Determine output based on command
        if "-k" in args:  # Kernel logs
            stdout = gpu_log.encode()
        else:  # System logs
            stdout = b""

        async def async_communicate():
            return (stdout, b"")

        mock_proc.communicate = async_communicate
        return mock_proc

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_create_subprocess_exec)

    results = await analyze_system_logs(time_range="1h")

    # Verification
    assert len(results["driver_errors"]) > 0
    assert any("radeon" in e["message"] for e in results["driver_errors"])
    assert any("driver" in r.lower() for r in results["recommendations"])


@pytest.mark.asyncio
async def test_hardware_critical_thermal(monkeypatch):
    """
    Phase 2: Hardware Critical
    Inject: CPU thermal throttling
    Expect: Status CRITICAL in recommendations.
    """
    hw_log = create_log_line("CPU thermal throttling detected", unit="kernel")

    async def fake_create_subprocess_exec(program, *args, **kwargs):
        mock_proc = MagicMock()
        mock_proc.returncode = 0

        if "-k" in args:
            stdout = hw_log.encode()
        else:
            stdout = b""

        async def async_communicate():
            return (stdout, b"")

        mock_proc.communicate = async_communicate
        return mock_proc

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_create_subprocess_exec)

    results = await analyze_system_logs()

    assert len(results["hardware_errors"]) > 0
    assert any("CRITICAL" in r for r in results["recommendations"])
    assert any("thermal" in e["message"] for e in results["hardware_errors"])


@pytest.mark.asyncio
async def test_gui_warnings_plasma(monkeypatch):
    """
    Phase 2: GUI Warnings (Regression #5)
    Inject: plasma-kded failed
    Expect: In service_errors.
    """
    gui_log = create_log_line("plasma-kded failed to start", unit="plasma-kded.service")

    async def fake_create_subprocess_exec(program, *args, **kwargs):
        mock_proc = MagicMock()
        mock_proc.returncode = 0

        if "-k" in args:
            stdout = b""
        else:
            stdout = gui_log.encode()

        async def async_communicate():
            return (stdout, b"")

        mock_proc.communicate = async_communicate
        return mock_proc

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_create_subprocess_exec)

    results = await analyze_system_logs(severity="warning")

    assert len(results["service_errors"]) > 0
    assert any("plasma" in e["message"] for e in results["service_errors"])


@pytest.mark.asyncio
async def test_service_failure_nginx(monkeypatch):
    """
    Phase 2: Service Failure
    Inject: nginx failed
    Expect: Service error.
    """
    svc_log = create_log_line(
        "nginx.service: Failed with result 'exit-code'.", unit="nginx.service"
    )

    async def fake_create_subprocess_exec(program, *args, **kwargs):
        mock_proc = MagicMock()
        mock_proc.returncode = 0

        if "-k" in args:
            stdout = b""
        else:
            stdout = svc_log.encode()

        async def async_communicate():
            return (stdout, b"")

        mock_proc.communicate = async_communicate
        return mock_proc

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_create_subprocess_exec)

    results = await analyze_system_logs()

    assert len(results["service_errors"]) > 0
    assert any("nginx" in e["message"] for e in results["service_errors"])
