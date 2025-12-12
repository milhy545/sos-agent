import pytest
from unittest.mock import patch, AsyncMock
from click.testing import CliRunner
from src.cli import cli


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("SOS_AI_LANGUAGE", "en")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("INCEPTION_API_KEY", "test_inception_key")


@pytest.fixture
def mock_client_cls():
    with patch("src.cli.SOSAgentClient") as MockClient:
        instance = MockClient.return_value

        async def mock_execute(*args, **kwargs):
            yield "Diagnostic result..."

        instance.execute_rescue_task.side_effect = mock_execute
        yield MockClient


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.asyncio
async def test_cli_diagnose_hardware(runner, mock_client_cls):
    # Setup mock logs
    with patch("src.cli.analyze_system_logs", new_callable=AsyncMock) as mock_logs:
        mock_logs.return_value = {
            "hardware_errors": [],
            "driver_errors": [],
            "service_errors": [],
            "security_warnings": [],
            "recommendations": [],
        }

        from asyncclick.testing import CliRunner as AsyncCliRunner

        runner = AsyncCliRunner()

        result = await runner.invoke(cli, ["diagnose", "--category", "hardware"])

        assert result.exit_code == 0
        assert "Running hardware diagnostics" in result.output
        mock_client_cls.return_value.execute_rescue_task.assert_called_once()


@pytest.mark.asyncio
async def test_cli_emergency_mode(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    # Mock confirmation to yes
    result = await runner.invoke(cli, ["emergency"], input="y\n")

    assert result.exit_code == 0
    assert "EMERGENCY MODE ACTIVATED" in result.output
    mock_client_cls.return_value.execute_rescue_task.assert_called_once()


@pytest.mark.asyncio
async def test_cli_fix_dry_run(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    result = await runner.invoke(cli, ["fix", "hardware", "--dry-run"])

    assert result.exit_code == 0
    assert "dry-run" in result.output
    mock_client_cls.return_value.execute_rescue_task.assert_called_once()


@pytest.mark.asyncio
async def test_cli_monitor_interrupt(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    # We need to interrupt the infinite loop in monitor
    with patch("asyncio.sleep", side_effect=KeyboardInterrupt):
        result = await runner.invoke(cli, ["monitor", "--interval", "1"])

        assert "Monitoring stopped" in result.output


@pytest.mark.asyncio
async def test_cli_setup_wizard_call(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        result = await runner.invoke(cli, ["setup"])

        assert result.exit_code == 0
        assert "Setup completed successfully" in result.output
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_cli_menu(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    with patch("src.tui.app.start_tui") as mock_start:
        result = await runner.invoke(cli, ["menu"])
        assert result.exit_code == 0
        mock_start.assert_called_once()


@pytest.mark.asyncio
async def test_cli_check_boot(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    result = await runner.invoke(cli, ["check-boot"])
    assert result.exit_code == 0
    assert "Checking boot configuration" in result.output
    mock_client_cls.return_value.execute_rescue_task.assert_called_once()


@pytest.mark.asyncio
async def test_cli_optimize_apps(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    result = await runner.invoke(cli, ["optimize-apps", "--platform", "flatpak"])
    assert result.exit_code == 0
    assert "Optimizing flatpak" in result.output
    mock_client_cls.return_value.execute_rescue_task.assert_called_once()


@pytest.mark.asyncio
async def test_cli_gcloud_check_no_project(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    with patch("src.gcloud.manager.GCloudManager") as MockManager:
        instance = MockManager.return_value
        instance.get_current_project.return_value = None

        result = await runner.invoke(cli, ["gcloud", "check"])
        assert result.exit_code == 0
        assert "No active GCloud project" in result.output


@pytest.mark.asyncio
async def test_cli_gcloud_list_projects(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    with patch("src.gcloud.manager.GCloudManager") as MockManager:
        instance = MockManager.return_value
        instance.list_projects.return_value = []

        result = await runner.invoke(cli, ["gcloud", "list-projects"])
        assert result.exit_code == 0
        assert "Google Cloud Projects" in result.output


@pytest.mark.asyncio
async def test_cli_gcloud_enable_api(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    with patch("src.gcloud.manager.GCloudManager") as MockManager:
        instance = MockManager.return_value
        instance.enable_api.return_value = True

        result = await runner.invoke(
            cli, ["gcloud", "enable-api", "--project", "test-proj"]
        )
        assert result.exit_code == 0
        assert "enabled successfully" in result.output


@pytest.mark.asyncio
async def test_cli_gcloud_setup_safe(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    with patch("src.gcloud.manager.GCloudManager"):
        result = await runner.invoke(cli, ["gcloud", "init"])
        assert result.exit_code == 0
        assert "Safe Mode" in result.output


@pytest.mark.asyncio
async def test_cli_gcloud_setup_auto_cancelled(runner, mock_client_cls):
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    with patch("src.gcloud.manager.GCloudManager"):
        # Decline confirmation
        result = await runner.invoke(cli, ["gcloud", "init", "--auto"], input="n\n")
        assert result.exit_code == 0
        assert "Setup cancelled" in result.output
