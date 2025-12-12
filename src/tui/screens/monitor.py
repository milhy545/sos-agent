import psutil
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, ProgressBar, Static
from textual.containers import Vertical, Grid


class MonitorScreen(Screen):
    """System monitoring screen."""

    CSS_PATH = "../styles.css"
    BINDINGS = [("escape", "back", "Back to Menu")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("System Monitor", classes="title")

        with Grid(classes="monitor-grid"):
            with Vertical(classes="monitor-panel"):
                yield Label("CPU Usage")
                yield ProgressBar(total=100, show_eta=False, id="cpu-bar")
                yield Label("0%", id="cpu-label")

            with Vertical(classes="monitor-panel"):
                yield Label("Memory Usage")
                yield ProgressBar(total=100, show_eta=False, id="ram-bar")
                yield Label("0%", id="ram-label")

            with Vertical(classes="monitor-panel"):
                yield Label("Disk Usage (Root)")
                yield ProgressBar(total=100, show_eta=False, id="disk-bar")
                yield Label("0%", id="disk-label")

        yield Footer()

    def on_mount(self) -> None:
        """Start monitoring."""
        self.update_stats()
        self.set_interval(1.0, self.update_stats)

    def update_stats(self) -> None:
        """Update system metrics."""
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        self.query_one("#cpu-bar", ProgressBar).progress = cpu
        self.query_one("#cpu-label", Label).update(f"{cpu}%")

        self.query_one("#ram-bar", ProgressBar).progress = ram
        self.query_one("#ram-label", Label).update(f"{ram}%")

        self.query_one("#disk-bar", ProgressBar).progress = disk
        self.query_one("#disk-label", Label).update(f"{disk}%")

    def action_back(self) -> None:
        self.app.pop_screen()
