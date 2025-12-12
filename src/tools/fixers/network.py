import asyncio
import logging
from typing import Tuple, List
from .base import Fixer
from src.agent.privilege import is_root

logger = logging.getLogger(__name__)


class DNSFixer(Fixer):
    """Fixer to reset DNS settings."""

    @property
    def id(self) -> str:
        return "dns_reset"

    @property
    def name(self) -> str:
        return "Reset DNS Configuration to Public DNS"

    @property
    def category(self) -> str:
        return "network"

    async def check(self) -> Tuple[bool, str]:
        """Check connectivity."""
        try:
            # Try to resolve google.com
            # Note: In a real environment we might use socket.gethostbyname
            # But here we simulate a check.
            proc = await asyncio.create_subprocess_shell(
                "ping -c 1 google.com",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            if proc.returncode != 0:
                return True, "Cannot reach google.com (DNS or Connectivity issue)"
            return False, "Connectivity appears normal"
        except Exception:
            return True, "Failed to execute connectivity check"

    async def apply(self, dry_run: bool = False) -> List[str]:
        actions = []

        # Dry run actions
        if dry_run:
            actions.append("Backup current /etc/resolv.conf to /etc/resolv.conf.bak")
            actions.append("Set nameserver 8.8.8.8 in /etc/resolv.conf")
            actions.append("Set nameserver 1.1.1.1 in /etc/resolv.conf")
            actions.append("Restart NetworkManager service")
            return actions

        if not is_root():
            raise PermissionError("Root privileges required to reset DNS")

        try:
            # Backup
            await asyncio.create_subprocess_shell(
                "cp /etc/resolv.conf /etc/resolv.conf.bak"
            )
            actions.append("Backed up /etc/resolv.conf")

            # Write new DNS (using tee to write as root if we were using sudo wrapper, but we check is_root)
            content = "nameserver 8.8.8.8\nnameserver 1.1.1.1\n"
            # async write to file? simpler to use shell for permission reasons if managed
            # But since we are root:
            with open("/etc/resolv.conf", "w") as f:
                f.write(content)
            actions.append("Updated /etc/resolv.conf")

            # Restart NetworkManager
            # We should check if it exists first? assuming systemd
            proc = await asyncio.create_subprocess_shell(
                "systemctl restart NetworkManager"
            )
            await proc.communicate()
            if proc.returncode == 0:
                actions.append("Restarted NetworkManager")
            else:
                actions.append(
                    "Failed to restart NetworkManager (might not be running)"
                )

        except Exception as e:
            logger.error(f"DNS Fix failed: {e}")
            actions.append(f"Failed: {e}")

        return actions
