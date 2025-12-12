import pytest
from src.tui.app import SOSApp
from src.tui.screens.menu import MainMenu

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
