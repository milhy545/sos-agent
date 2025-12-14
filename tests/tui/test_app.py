import pytest
from src.tui.app import SOSApp
from src.tui.screens.menu import MainMenu
from src.tui.screens.diagnostics import DiagnosticsScreen
from src.tui.screens.logs import LogsScreen
from src.tui.screens.fix import FixScreen

@pytest.mark.asyncio
async def test_app_startup():
    """Test that the app starts and loads the main menu."""
    app = SOSApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainMenu)
        assert app.title == "SOS Agent"

@pytest.mark.asyncio
async def test_menu_structure():
    """Test that the menu items are generated correctly."""
    app = SOSApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, MainMenu)

        # Check title content
        title = screen.query_one("#title")
        assert title.id == "title"

        # Check bindings generation
        bindings = {b.key: b.action for b in screen.BINDINGS}
        assert bindings["1"] == "diagnose"
        assert bindings["q"] == "quit"

        # Check buttons exist and have correct labels
        btn1 = screen.query_one("#btn-1")
        assert "System Diagnostics" in str(btn1.label)

        # Check unimplemented item
        btn7 = screen.query_one("#btn-7")
        assert "Coming Soon" in str(btn7.label)
        assert btn7.disabled is True

@pytest.mark.asyncio
async def test_navigation_diagnostics():
    """Test navigation to Diagnostics screen."""
    app = SOSApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click("#btn-1")
        await pilot.pause()

        assert isinstance(app.screen, DiagnosticsScreen)

        # Go back using Escape, as there is no #btn-back on this screen (it uses bindings)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainMenu)

@pytest.mark.asyncio
async def test_navigation_logs():
    """Test navigation to Logs screen."""
    app = SOSApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        await pilot.click("#btn-6")
        await pilot.pause()

        assert isinstance(app.screen, LogsScreen)

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainMenu)

@pytest.mark.asyncio
async def test_navigation_fix():
    """Test navigation to Fix screen."""
    app = SOSApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        await pilot.click("#btn-2")
        await pilot.pause()

        assert isinstance(app.screen, FixScreen)

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainMenu)

@pytest.mark.asyncio
async def test_unimplemented_action():
    """Test pressing key for unimplemented action."""
    app = SOSApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        await pilot.press("7")
        await pilot.pause()

        # Should still be on Main Menu
        assert isinstance(app.screen, MainMenu)
