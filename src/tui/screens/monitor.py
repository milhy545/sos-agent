import psutil  # type: ignore[import-untyped]
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, ProgressBar, Static, Button
from textual.containers import Vertical, Container, Horizontal


class MonitorScreen(Screen):
    """System monitoring screen."""

    CSS_PATH = "../styles.css"
    BINDINGS = [("escape", "back", "Back to Menu")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("System Monitor", classes="title")

        with Container(classes="monitor-grid"):
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

        with Horizontal():
            yield Button("Start", id="btn-start", variant="primary")
            yield Button("Stop", id="btn-stop", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        """Start monitoring."""
        self.monitoring = True
        self.update_stats()
        self.timer = self.set_interval(1.0, self.update_stats)

    def update_stats(self) -> None:
        """Update system metrics."""
        if not getattr(self, "monitoring", False):
            return
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        self.query_one("#cpu-bar", ProgressBar).progress = cpu
        self.query_one("#cpu-label", Label).update(f"{cpu}%")

        self.query_one("#ram-bar", ProgressBar).progress = ram
        self.query_one("#ram-label", Label).update(f"{ram}%")

        self.query_one("#disk-bar", ProgressBar).progress = disk
        self.query_one("#disk-label", Label).update(f"{disk}%")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start":
            self.monitoring = True
        elif event.button.id == "btn-stop":
            self.monitoring = False

    def action_back(self) -> None:
        self.app.pop_screen()
