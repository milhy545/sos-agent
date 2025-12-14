import pytest
from unittest.mock import patch, AsyncMock, Mock
from asyncclick.testing import CliRunner
from src.cli import diagnose


@pytest.mark.asyncio
async def test_diagnose_issue_flag(tmp_path):
    """Test that --issue flag saves to session."""
    with (
        patch("src.cli.SOSAgentClient"),
        patch("src.cli.safe_permission_handler", return_value={"behavior": "allow"}),
        patch(
            "src.cli.analyze_system_logs",
            return_value={
                "hardware_errors": [],
                "driver_errors": [],
                "service_errors": [],
                "security_warnings": [],
                "recommendations": [],
            },
        ),
    ):
        mock_subprocess = AsyncMock()
        mock_subprocess.communicate.return_value = (b"", b"")
        with patch("asyncio.create_subprocess_shell", return_value=mock_subprocess):
            with patch("src.cli.FileSessionStore") as mock_store_cls:
                mock_store_instance = mock_store_cls.return_value
                mock_store_instance.save_issue = AsyncMock()

                runner = CliRunner()
                result = await runner.invoke(
                    diagnose, ["--issue", "Test Issue"], obj={"client": Mock()}
                )

                if result.exception:
                    raise result.exception

                mock_store_instance.save_issue.assert_called_with("Test Issue")


@pytest.mark.asyncio
async def test_diagnose_prompt_includes_issue():
    """Ensure issue text propagates into the diagnostic prompt."""
    with (
        patch("src.cli.safe_permission_handler", return_value={"behavior": "allow"}),
        patch(
            "src.cli.analyze_system_logs",
            return_value={
                "hardware_errors": [],
                "driver_errors": [],
                "service_errors": [],
                "security_warnings": [],
                "recommendations": [],
            },
        ),
    ):
        mock_subprocess = AsyncMock()
        mock_subprocess.communicate.return_value = (b"", b"")
        with patch("asyncio.create_subprocess_shell", return_value=mock_subprocess):
            with patch("src.cli.FileSessionStore") as mock_store_cls:
                mock_store = mock_store_cls.return_value
                mock_store.save_issue = AsyncMock()

                async def _fake_stream(task):
                    assert "User Issue Description" in task
                    assert "Network keeps dropping" in task
                    if False:
                        yield "noop"

                with patch("src.cli.SOSAgentClient") as mock_client_cls:
                    mock_client = mock_client_cls.return_value
                    mock_client.execute_rescue_task.side_effect = _fake_stream

                    runner = CliRunner()
                    result = await runner.invoke(
                        diagnose,
                        ["--issue", "Network keeps dropping"],
                        obj={"client": Mock()},
                    )

                    if result.exception:
                        raise result.exception
