import pytest
from asyncclick.testing import CliRunner
from src.cli import diagnose

@pytest.mark.asyncio
async def test_diagnose_issue_flag(tmp_path, mocker):
    """Test that --issue flag saves to session."""
    # Mock SOSAgentClient and permissions
    mocker.patch("src.cli.SOSAgentClient")
    mocker.patch("src.cli.safe_permission_handler", return_value={"behavior": "allow"})
    mocker.patch("src.cli.analyze_system_logs", return_value={
        "hardware_errors": [], "driver_errors": [], "service_errors": [],
        "security_warnings": [], "recommendations": []
    })

    # Mock subprocess calls
    mock_subprocess = mocker.AsyncMock()
    mock_subprocess.communicate.return_value = (b"", b"")
    mocker.patch("asyncio.create_subprocess_shell", return_value=mock_subprocess)

    # Mock FileSessionStore
    mock_store_cls = mocker.patch("src.cli.FileSessionStore")
    mock_store_instance = mock_store_cls.return_value
    mock_store_instance.save_issue = mocker.AsyncMock()

    runner = CliRunner()
    result = await runner.invoke(diagnose, ["--issue", "Test Issue"], obj={"client": mocker.Mock()})

    # Check result
    if result.exception:
        raise result.exception

    mock_store_instance.save_issue.assert_called_with("Test Issue")
