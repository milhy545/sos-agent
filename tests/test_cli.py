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

    class DummyFixer:
        id = "dummy"
        name = "Dummy Fix"
        category = "hardware"
        requires_root = False

        async def check(self):
            return True, "Needs attention"

        async def apply(self, dry_run=False):
            return ["noop"] if dry_run else ["fixed"]

    with patch("src.cli.get_all_fixers", return_value=[DummyFixer()]):
        result = await runner.invoke(cli, ["fix", "hardware", "--dry-run"])

    assert result.exit_code == 0
    assert "Planned actions" in result.output
    mock_client_cls.return_value.execute_rescue_task.assert_not_called()


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

    pytest.importorskip("textual")
    import src.tui.app as tui_app

    with patch.object(tui_app, "start_tui_async") as mock_start:
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

    result = await runner.invoke(
        cli, ["optimize-apps", "--platform", "flatpak", "--ai"]
    )
    assert result.exit_code == 0
    assert "Optimizing flatpak" in result.output
    mock_client_cls.return_value.execute_rescue_task.assert_called_once()


@pytest.mark.asyncio
async def test_cli_fix_ai_fallback(runner, mock_client_cls):
    """AI path still available when requested."""
    from asyncclick.testing import CliRunner as AsyncCliRunner

    runner = AsyncCliRunner()

    result = await runner.invoke(cli, ["fix", "hardware", "--ai"])

    assert result.exit_code == 0
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


@pytest.mark.asyncio
async def test_cli_chat_missing_key():
    """Chat should warn when no API key is configured."""
    from asyncclick.testing import CliRunner as AsyncCliRunner
    from src.agent.config import SOSConfig

    runner = AsyncCliRunner()
    cfg = SOSConfig(
        gemini_api_key="",
        openai_api_key="",
        inception_api_key="",
        anthropic_api_key="",
    )

    with patch("src.cli.load_config", new_callable=AsyncMock, return_value=cfg):
        with patch("src.cli.SOSAgentClient"):
            with patch("src.cli.FileSessionStore"):
                result = await runner.invoke(
                    cli, ["chat"], obj={"client": object(), "config": cfg}
                )

                assert result.exit_code == 0
                assert "No API key configured" in result.output


@pytest.mark.asyncio
async def test_cli_chat_message_flow():
    """Chat single message stores history and streams response."""
    from asyncclick.testing import CliRunner as AsyncCliRunner
    from src.agent.config import SOSConfig

    runner = AsyncCliRunner()
    cfg = SOSConfig(openai_api_key="test-key")

    with patch("src.cli.load_config", new_callable=AsyncMock, return_value=cfg):
        with patch("src.cli.FileSessionStore") as mock_store_cls:
            mock_store = mock_store_cls.return_value
            mock_store.get_issue = AsyncMock(return_value="Slow Wi-Fi")
            mock_store.get_chat_history = AsyncMock(return_value=[])
            mock_store.save_chat_message = AsyncMock()

            async def _fake_stream(task):
                assert "Slow Wi-Fi" in task
                if False:
                    yield "noop"

            with patch("src.cli.SOSAgentClient") as mock_client_cls:
                mock_client = mock_client_cls.return_value
                mock_client.execute_rescue_task.side_effect = _fake_stream

                result = await runner.invoke(
                    cli,
                    ["chat", "--message", "Hello"],
                    obj={"client": mock_client, "config": cfg},
                )

                assert result.exit_code == 0
                mock_store.save_chat_message.assert_any_call("user", "Hello")
