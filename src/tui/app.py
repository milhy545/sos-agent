from textual.app import App
from src.tui.screens.menu import MainMenu
from src.agent.config import load_config
from src.agent.client import SOSAgentClient


class SOSApp(App):
    """SOS Agent TUI Application."""

    CSS_PATH = "styles.css"
    TITLE = "SOS Agent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        self.config = None

    async def on_mount(self) -> None:
        self.config = await load_config(None)
        self.client = SOSAgentClient(self.config)
        self.push_screen(MainMenu())


def start_tui():
    """Entry point for the TUI."""
    app = SOSApp()
    app.run()


if __name__ == "__main__":
    start_tui()
