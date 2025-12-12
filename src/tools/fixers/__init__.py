from typing import List, Dict, Type
from .base import Fixer
from .network import DNSFixer
from .services import ServicesFixer
from .disk import DiskCleanupFixer

FIXERS: Dict[str, Type[Fixer]] = {
    DNSFixer().id: DNSFixer,
    ServicesFixer().id: ServicesFixer,
    DiskCleanupFixer().id: DiskCleanupFixer,
}


def get_fixer(fixer_id: str) -> Fixer:
    if fixer_id in FIXERS:
        return FIXERS[fixer_id]()
    raise ValueError(f"Unknown fixer: {fixer_id}")


def get_all_fixers() -> List[Fixer]:
    return [cls() for cls in FIXERS.values()]
