import asyncio
from textual.app import App
from src.tui.screens.menu import MainMenu
from src.agent.config import SOSConfig, load_config
from src.agent.client import SOSAgentClient


class SOSApp(App):
    """SOS Agent TUI Application."""

    CSS_PATH = "styles.css"
    TITLE = "SOS Agent"

    def __init__(self, init_client: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._init_client = init_client
        self.client: SOSAgentClient | None = None
        self.config: SOSConfig | None = None

    async def on_mount(self) -> None:
        self.config = await load_config(None)
        if self._init_client:
            assert self.config is not None
            self.client = SOSAgentClient(self.config)
        self.push_screen(MainMenu())


async def start_tui_async() -> None:
    """Entry point for the TUI (async-safe for asyncclick)."""
    app = SOSApp()
    await app.run_async()


def start_tui() -> None:
    """Entry point for the TUI (sync wrapper)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(start_tui_async())
        return

    # If we're already in an event loop, schedule and return.
    # Prefer `start_tui_async()` from async callers.
    asyncio.create_task(start_tui_async())


if __name__ == "__main__":
    start_tui()
