"""Tests for session storage."""

import json
import pytest
from pathlib import Path
from src.session.store import FileSessionStore

@pytest.fixture
def session_file(tmp_path):
    """Create a temporary session file path."""
    return tmp_path / "session.json"

@pytest.mark.asyncio
async def test_file_session_store_init(session_file):
    """Test initialization and file creation."""
    store = FileSessionStore(path=session_file)
    assert store.path == session_file
    # Should create empty default
    data = store._load()
    assert data == {"chat_history": [], "current_issue": None}

@pytest.mark.asyncio
async def test_save_and_get_issue(session_file):
    """Test saving and retrieving issue."""
    store = FileSessionStore(path=session_file)
    await store.save_issue("System is slow")

    # Check in memory
    assert await store.get_issue() == "System is slow"

    # Check on disk
    with open(session_file, "r") as f:
        data = json.load(f)
    assert data["current_issue"] == "System is slow"

    # Reload store
    store2 = FileSessionStore(path=session_file)
    assert await store2.get_issue() == "System is slow"

@pytest.mark.asyncio
async def test_chat_history(session_file):
    """Test chat history persistence."""
    store = FileSessionStore(path=session_file)
    await store.save_chat_message("user", "Hello")
    await store.save_chat_message("assistant", "Hi there")

    history = await store.get_chat_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there"

@pytest.mark.asyncio
async def test_clear_session(session_file):
    """Test clearing the session."""
    store = FileSessionStore(path=session_file)
    await store.save_issue("Issue")
    await store.save_chat_message("user", "msg")

    await store.clear_session()

    assert await store.get_issue() is None
    assert await store.get_chat_history() == []

    with open(session_file, "r") as f:
        data = json.load(f)
    assert data == {"chat_history": [], "current_issue": None}
