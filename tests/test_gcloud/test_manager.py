import pytest
from unittest.mock import patch
import subprocess
from src.gcloud.manager import GCloudManager


@pytest.fixture
def manager():
    with patch("subprocess.run") as mock_run:
        # Mock successful version check
        mock_run.return_value.stdout = "Google Cloud SDK 410.0.0"
        mock_run.return_value.returncode = 0
        return GCloudManager()


def test_init_check_installed(manager):
    # The fixture already initialized manager, verifying check passed
    assert isinstance(manager, GCloudManager)


def test_init_check_failed():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError) as exc:
            GCloudManager()
        assert "not installed" in str(exc.value)


def test_list_projects(manager):
    mock_output = [
        {
            "projectId": "test-project-1",
            "name": "Test Project 1",
            "projectNumber": "123",
            "lifecycleState": "ACTIVE",
        },
        {
            "projectId": "test-project-2",
            "name": "Test Project 2",
            "projectNumber": "456",
            "lifecycleState": "DELETE_REQUESTED",
        },
    ]

    with patch.object(manager, "_run_gcloud_command", return_value=mock_output):
        projects = manager.list_projects()

        assert len(projects) == 2
        assert projects[0].project_id == "test-project-1"
        assert projects[1].lifecycle_state == "DELETE_REQUESTED"


def test_get_current_project(manager):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "active-project-123\n"
        mock_run.return_value.returncode = 0

        project = manager.get_current_project()
        assert project == "active-project-123"


def test_get_current_project_none(manager):
    with patch(
        "subprocess.run", side_effect=subprocess.CalledProcessError(1, ["gcloud"])
    ):
        project = manager.get_current_project()
        assert project is None


def test_is_api_enabled_true(manager):
    with patch.object(manager, "_run_gcloud_command", return_value=[{"name": "api"}]):
        assert manager.is_api_enabled("proj", "api") is True


def test_is_api_enabled_false(manager):
    with patch.object(manager, "_run_gcloud_command", return_value=[]):
        assert manager.is_api_enabled("proj", "api") is False


def test_create_project_auto(manager):
    with patch.object(manager, "_run_gcloud_command") as mock_run_cmd:
        with patch("subprocess.run"):
            # Mock list_projects to verify creation
            mock_run_cmd.side_effect = [
                {},  # create output (ignored)
                [  # list projects output
                    {
                        "projectId": "auto-gen-id",
                        "name": "SOS Agent",
                        "projectNumber": "1",
                        "lifecycleState": "ACTIVE",
                    }
                ],
            ]

            project = manager.create_project(
                project_id="auto-gen-id", auto_confirm=True
            )

            assert project.project_id == "auto-gen-id"
            assert mock_run_cmd.call_count == 2


def test_create_project_no_auto(manager):
    with pytest.raises(RuntimeError):
        manager.create_project(auto_confirm=False)


def test_enable_api(manager):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        assert manager.enable_api("proj") is True


def test_check_quota_status_success(manager):
    mock_quota_data = {
        "consumerQuotaLimits": [{"quotaLimit": {"defaultLimit": "100"}}],
        "consumerQuotaMetrics": [{"usage": "50"}],
    }

    with patch.object(manager, "_run_gcloud_command", return_value=mock_quota_data):
        status = manager.check_quota_status("proj")

        assert status.limit_value == 100
        assert status.current_usage == 50
        assert status.is_exceeded is False


def test_check_quota_status_failed(manager):
    with patch.object(
        manager, "_run_gcloud_command", side_effect=Exception("API Error")
    ):
        status = manager.check_quota_status("proj")

        assert status.is_exceeded is True  # Fallback is True (assume worst)
