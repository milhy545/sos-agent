import os
import shutil
import logging

logger = logging.getLogger(__name__)


def is_root() -> bool:
    """Check if running as root."""
    return os.geteuid() == 0


def has_sudo() -> bool:
    """Check if sudo is available."""
    return shutil.which("sudo") is not None


def get_sudo_wrapper() -> str:
    """Get the command to elevate privileges."""
    if is_root():
        return ""
    if has_sudo():
        # TODO: Handle ASKPASS if needed
        return "sudo"
    # Fallback to pkexec if available?
    if shutil.which("pkexec"):
        return "pkexec"
    return ""


def require_root(func):
    """Decorator to ensure function runs as root or warns."""
    # This is useful for CLI, but for fixers we check .requires_root
    pass
