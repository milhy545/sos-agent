import pytest
from unittest.mock import patch, AsyncMock

pytest.importorskip("textual")
from src.tui.app import SOSApp
from src.tui.screens.menu import MainMenu
from src.tui.screens.fix import FixScreen
from src.tui.screens.chat import ChatScreen
from src.tui.screens.logs import LogsScreen


@pytest.mark.asyncio
async def test_app_startup():
    """Test that the app starts and loads the main menu."""
    app = SOSApp()
    async with app.run_test() as pilot:
        # Check if MainMenu is active
        assert isinstance(app.screen, MainMenu)

        # Check for button 1
        btn = app.screen.query_one("#btn-1")
        assert btn.label.plain == "1. System Diagnostics"

        # Check exit
        await pilot.press("q")
        # App should exit


@pytest.mark.asyncio
async def test_menu_to_fix_and_back():
    """Number bindings open fixers screen then return."""
    app = SOSApp()
    async with app.run_test() as pilot:
        await pilot.press("2")
        assert isinstance(app.screen, FixScreen)
        await pilot.press("escape")
        assert isinstance(app.screen, MainMenu)


@pytest.mark.asyncio
async def test_menu_to_chat():
    """Chat screen loads without crashing and respects bindings."""
    app = SOSApp()
    with patch("src.tui.screens.chat.FileSessionStore") as mock_store_cls:
        mock_store = mock_store_cls.return_value
        mock_store.get_chat_history = AsyncMock(return_value=[])
        mock_store.get_issue = AsyncMock(return_value=None)
        with patch(
            "src.tui.screens.chat.load_config", new_callable=AsyncMock
        ) as mock_cfg:
            mock_cfg.return_value = None
            async with app.run_test() as pilot:
                await pilot.press("4")
                assert isinstance(app.screen, ChatScreen)
                await pilot.press("escape")
                assert isinstance(app.screen, MainMenu)


@pytest.mark.asyncio
async def test_menu_to_logs():
    """Logs screen is reachable via key binding."""
    app = SOSApp()
    async with app.run_test() as pilot:
        await pilot.press("6")
        assert isinstance(app.screen, LogsScreen)
