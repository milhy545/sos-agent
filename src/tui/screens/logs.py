from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, RichLog, Static
from textual.containers import Vertical, Horizontal


class LogsScreen(Screen):
    """View agent log output."""

    CSS_PATH = "../styles.css"
    BINDINGS = [("escape", "back", "Back to Menu")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Logs & History", classes="title")

        with Vertical(id="logs-panel", classes="panel"):
            yield RichLog(id="log-view", wrap=True)
            with Horizontal():
                yield Button("Refresh", id="btn-refresh", variant="primary")
                yield Button("Open File", id="btn-open", variant="default")

        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()

    async def on_mount(self) -> None:
        await self._load_log()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh":
            await self._load_log()
        elif event.button.id == "btn-open":
            self.notify("Soubor: logs/sos-agent.log")

    async def _load_log(self) -> None:
        log_widget = self.query_one("#log-view", RichLog)
        log_widget.clear()
        path = Path("logs/sos-agent.log")
        if not path.exists():
            log_widget.write("[red]Log file not found. Spusť nějaký příkaz sos.*[/red]")
            return
        try:
            content = path.read_text(encoding="utf-8").splitlines()[-100:]
        except Exception as e:
            log_widget.write(f"[red]Failed to read log: {e}[/red]")
            return

        for line in content:
            log_widget.write(line)
