"""Google Cloud Platform manager for SOS Agent."""

import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GCloudProject:
    """Google Cloud Project information."""

    project_id: str
    name: str
    project_number: str
    lifecycle_state: str


@dataclass
class QuotaStatus:
    """Gemini API quota status."""

    project_id: str
    limit_name: str
    limit_value: int
    current_usage: int
    is_exceeded: bool
    region: str


class GCloudManager:
    """Manages Google Cloud operations for SOS Agent."""

    def __init__(self):
        """Initialize GCloud manager."""
        self._check_gcloud_installed()

    def _check_gcloud_installed(self) -> bool:
        """Check if gcloud CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["gcloud", "version"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug(f"gcloud version: {result.stdout}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"gcloud CLI not found or not authenticated: {e}")
            raise RuntimeError(
                "gcloud CLI not installed or not authenticated. "
                "Install: https://cloud.google.com/sdk/docs/install"
            )

    def _run_gcloud_command(self, args: List[str]) -> Dict[str, Any]:
        """Run gcloud command and return JSON output."""
        cmd = ["gcloud"] + args + ["--format=json"]
        logger.debug(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout) if result.stdout else {}
        except subprocess.CalledProcessError as e:
            logger.error(f"gcloud command failed: {e.stderr}")
            raise RuntimeError(f"gcloud command failed: {e.stderr}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse gcloud output: {e}")
            raise RuntimeError(f"Failed to parse gcloud output: {e}")

    def list_projects(self) -> List[GCloudProject]:
        """List all Google Cloud projects."""
        logger.info("Listing Google Cloud projects...")
        data = self._run_gcloud_command(["projects", "list"])

        projects = []
        for item in data:
            projects.append(
                GCloudProject(
                    project_id=item["projectId"],
                    name=item["name"],
                    project_number=item["projectNumber"],
                    lifecycle_state=item["lifecycleState"],
                )
            )

        logger.info(f"Found {len(projects)} projects")
        return projects

    def get_current_project(self) -> Optional[str]:
        """Get currently active project."""
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True,
                check=True,
            )
            project_id = result.stdout.strip()
            logger.info(f"Current project: {project_id}")
            return project_id if project_id else None
        except subprocess.CalledProcessError:
            logger.warning("No active project set")
            return None

    def check_quota_status(self, project_id: Optional[str] = None) -> QuotaStatus:
        """Check Gemini API quota status for a project."""
        if not project_id:
            project_id = self.get_current_project()
            if not project_id:
                raise ValueError("No project specified and no active project found")

        logger.info(f"Checking quota status for project: {project_id}")

        try:
            # Get quota information from GCP
            data = self._run_gcloud_command(
                [
                    "services",
                    "quota",
                    "describe",
                    "generativelanguage.googleapis.com/generate_content_requests",
                    f"--project={project_id}",
                    "--consumer=projects/" + project_id,
                ]
            )

            # Parse quota data
            limit_value = int(
                data.get("consumerQuotaLimits", [{}])[0]
                .get("quotaLimit", {})
                .get("defaultLimit", 0)
            )
            current_usage = int(
                data.get("consumerQuotaMetrics", [{}])[0].get("usage", 0)
            )

            return QuotaStatus(
                project_id=project_id,
                limit_name="GenerateContentRequestsPerMinutePerProjectPerRegion",
                limit_value=limit_value,
                current_usage=current_usage,
                is_exceeded=current_usage >= limit_value,
                region="us-central1",
            )

        except Exception as e:
            logger.warning(f"Could not fetch quota details: {e}")
            # Return basic status based on project state
            return QuotaStatus(
                project_id=project_id,
                limit_name="GenerateContentRequestsPerMinutePerProjectPerRegion",
                limit_value=0,
                current_usage=0,
                is_exceeded=True,
                region="us-central1",
            )

    def is_api_enabled(
        self, project_id: str, api_name: str = "generativelanguage.googleapis.com"
    ) -> bool:
        """Check if API is enabled for project."""
        logger.info(f"Checking if {api_name} is enabled in {project_id}...")

        try:
            data = self._run_gcloud_command(
                [
                    "services",
                    "list",
                    f"--project={project_id}",
                    "--enabled",
                    f"--filter=name:{api_name}",
                ]
            )

            return len(data) > 0
        except Exception as e:
            logger.error(f"Failed to check API status: {e}")
            return False

    def create_project(
        self, project_id: Optional[str] = None, auto_confirm: bool = False
    ) -> GCloudProject:
        """Create a new Google Cloud project.

        Args:
            project_id: Optional custom project ID. If None, auto-generates.
            auto_confirm: If True, skips confirmation prompt (for --auto mode).

        Returns:
            GCloudProject: Created project information.

        Raises:
            RuntimeError: If project creation fails.
        """
        if not auto_confirm:
            raise RuntimeError(
                "Auto-mode not enabled. Use --auto flag to allow automatic project creation."
            )

        # Auto-generate project ID if not provided
        if not project_id:
            import random
            import string

            random_suffix = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=6)
            )
            project_id = f"sos-agent-{random_suffix}"

        logger.info(f"Creating new project: {project_id}")

        try:
            # Create project
            self._run_gcloud_command(
                [
                    "projects",
                    "create",
                    project_id,
                    "--name=SOS Agent",
                ]
            )

            # Set as active project
            subprocess.run(
                ["gcloud", "config", "set", "project", project_id],
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Project {project_id} created and set as active")

            # Get project details
            projects = self.list_projects()
            for project in projects:
                if project.project_id == project_id:
                    return project

            raise RuntimeError(f"Project {project_id} created but not found in list")

        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise RuntimeError(f"Failed to create project: {e}")

    def enable_api(
        self, project_id: str, api_name: str = "generativelanguage.googleapis.com"
    ) -> bool:
        """Enable API for project."""
        logger.info(f"Enabling {api_name} for project {project_id}...")

        try:
            subprocess.run(
                ["gcloud", "services", "enable", api_name, f"--project={project_id}"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"{api_name} enabled successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to enable API: {e.stderr}")
            raise RuntimeError(f"Failed to enable API: {e.stderr}")

    def create_api_key(self, project_id: str) -> str:
        """Create a new API key for Gemini.

        Note: This requires the API Keys API to be enabled and may need
        additional setup. Alternative: Use gcloud auth application-default login.
        """
        logger.warning(
            "API key creation via gcloud is limited. Using application-default credentials."
        )
        logger.info("Run: gcloud auth application-default login")
        raise NotImplementedError(
            "Automatic API key creation requires additional setup. "
            "Please create an API key manually at: "
            "https://aistudio.google.com/app/apikey"
        )

    def get_project_info(self, project_id: str) -> Dict[str, Any]:
        """Get detailed project information."""
        logger.info(f"Getting info for project: {project_id}")
        return self._run_gcloud_command(["projects", "describe", project_id])
