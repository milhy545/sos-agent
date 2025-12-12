from abc import ABC, abstractmethod
from typing import List, Tuple


class Fixer(ABC):
    """Abstract base class for system fixers."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the fixer."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the fixer."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Category (network, services, system, etc.)."""
        pass

    @property
    def requires_root(self) -> bool:
        """Whether this fixer requires root privileges."""
        return True

    @abstractmethod
    async def check(self) -> Tuple[bool, str]:
        """
        Check if the fix is needed.
        Returns: (needs_fix: bool, reason: str)
        """
        pass

    @abstractmethod
    async def apply(self, dry_run: bool = False) -> List[str]:
        """
        Apply the fix.
        Args:
            dry_run: If True, return actions without executing.
        Returns: List of actions taken or planned.
        """
        pass
