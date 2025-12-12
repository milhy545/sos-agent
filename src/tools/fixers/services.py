import asyncio
from typing import Tuple, List
from .base import Fixer
from src.agent.privilege import is_root


class ServicesFixer(Fixer):
    @property
    def id(self) -> str:
        return "services_restart"

    @property
    def name(self) -> str:
        return "Restart Critical Services"

    @property
    def category(self) -> str:
        return "services"

    async def check(self) -> Tuple[bool, str]:
        # Check specific services
        services = ["NetworkManager", "sshd", "cron"]
        failed = []
        for svc in services:
            proc = await asyncio.create_subprocess_shell(
                f"systemctl is-active {svc}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            if proc.returncode != 0:
                failed.append(svc)

        if failed:
            return True, f"Services not active: {', '.join(failed)}"
        return False, "All critical services running"

    async def apply(self, dry_run: bool = False) -> List[str]:
        services = ["NetworkManager", "sshd", "cron"]
        actions = []

        if dry_run:
            for svc in services:
                actions.append(f"Check status of {svc}")
                actions.append(f"Restart {svc} if failed")
            return actions

        if not is_root():
            raise PermissionError("Root privileges required to restart services")

        for svc in services:
            proc = await asyncio.create_subprocess_shell(
                f"systemctl restart {svc}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            if proc.returncode == 0:
                actions.append(f"Restarted {svc}")
            else:
                actions.append(f"Failed to restart {svc}")

        return actions
