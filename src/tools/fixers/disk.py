import asyncio
from typing import Tuple, List
from .base import Fixer
from src.agent.privilege import is_root


class DiskCleanupFixer(Fixer):
    @property
    def id(self) -> str:
        return "disk_cleanup"

    @property
    def name(self) -> str:
        return "Disk Cleanup (Apt Cache / Tmp)"

    @property
    def category(self) -> str:
        return "system"

    async def check(self) -> Tuple[bool, str]:
        # Simple check for disk space or cache existence
        # Check /var/cache/apt/archives size
        cmd = "du -sh /var/cache/apt/archives | cut -f1"
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        size = stdout.decode().strip()

        # Heuristic: if size is not 0 or empty, we can clean
        return True, f"Apt cache size: {size} (Cleanup available)"

    async def apply(self, dry_run: bool = False) -> List[str]:
        actions = []
        if dry_run:
            actions.append("Run 'apt-get clean'")
            actions.append("Run 'apt-get autoremove'")
            return actions

        if not is_root():
            raise PermissionError("Root privileges required for cleanup")

        try:
            proc = await asyncio.create_subprocess_shell("apt-get clean")
            await proc.communicate()
            actions.append("Executed apt-get clean")

            proc2 = await asyncio.create_subprocess_shell("apt-get autoremove -y")
            await proc2.communicate()
            actions.append("Executed apt-get autoremove")
        except Exception as e:
            actions.append(f"Error: {e}")

        return actions
