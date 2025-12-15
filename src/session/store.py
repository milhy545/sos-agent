"""Session persistence layer for SOS Agent."""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionStore(ABC):
    """Abstract base class for session storage."""

    @abstractmethod
    async def save_chat_message(self, role: str, content: str) -> None:
        """Save a chat message to history."""
        pass

    @abstractmethod
    async def get_chat_history(self) -> List[Dict[str, str]]:
        """Retrieve chat history."""
        pass

    @abstractmethod
    async def save_issue(self, issue: str) -> None:
        """Save the current diagnostic issue description."""
        pass

    @abstractmethod
    async def get_issue(self) -> Optional[str]:
        """Retrieve the current diagnostic issue."""
        pass

    @abstractmethod
    async def save_diagnostic_result(self, result: Dict[str, Any]) -> None:
        """Save a diagnostic result."""
        pass

    @abstractmethod
    async def get_last_diagnostic_result(self) -> Optional[Dict[str, Any]]:
        """Retrieve the last diagnostic result."""
        pass

    @abstractmethod
    async def clear_session(self) -> None:
        """Clear all session data."""
        pass


class FileSessionStore(SessionStore):
    """JSON file-based session storage."""

    def __init__(self, path: Optional[Path] = None):
        """Initialize file session store."""
        if path is None:
            # Default to ~/.config/sos-agent/session.json
            self.path = Path.home() / ".config" / "sos-agent" / "session.json"
        else:
            self.path = path

        self._ensure_dir()
        self._data: Dict[str, Any] = self._load()

    def _ensure_dir(self) -> None:
        """Ensure the configuration directory exists."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create config directory: {e}")

    def _load(self) -> Dict[str, Any]:
        """Load session data from file."""
        if not self.path.exists():
            return {"chat_history": [], "current_issue": None}

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session file: {e}")
            return {"chat_history": [], "current_issue": None}

    def _save(self) -> None:
        """Save session data to file."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save session file: {e}")

    async def save_chat_message(self, role: str, content: str) -> None:
        """Save a chat message to history."""
        if "chat_history" not in self._data:
            self._data["chat_history"] = []

        self._data["chat_history"].append(
            {
                "role": role,
                "content": content,
                "timestamp": "TODO: timestamp",  # Optional, purely for potential future use
            }
        )
        self._save()

    async def get_chat_history(self) -> List[Dict[str, str]]:
        """Retrieve chat history."""
        return self._data.get("chat_history", [])

    async def save_issue(self, issue: str) -> None:
        """Save the current diagnostic issue description."""
        self._data["current_issue"] = issue
        self._save()

    async def get_issue(self) -> Optional[str]:
        """Retrieve the current diagnostic issue."""
        return self._data.get("current_issue")

    async def save_diagnostic_result(self, result: Dict[str, Any]) -> None:
        """Save a diagnostic result."""
        self._data["last_diagnostic"] = result
        self._save()

    async def get_last_diagnostic_result(self) -> Optional[Dict[str, Any]]:
        """Retrieve the last diagnostic result."""
        return self._data.get("last_diagnostic")

    async def clear_session(self) -> None:
        """Clear all session data."""
        self._data = {
            "chat_history": [],
            "current_issue": None,
            "last_diagnostic": None,
        }
        self._save()
