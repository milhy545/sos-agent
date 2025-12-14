from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, RichLog
from textual.containers import Grid, Vertical

class LogsScreen(Screen):
    """Screen for viewing logs."""

    CSS_PATH = "../styles.css"
    BINDINGS = [
        ("escape", "back", "Back"),
        ("a", "filter_all", "All"),
        ("e", "filter_error", "Errors"),
        ("w", "filter_warning", "Warnings"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("SYSTEM LOGS VIEWER", classes="title")

        with Grid(classes="logs-controls"):
            yield Button("All Logs (A)", id="btn-all", variant="primary")
            yield Button("Errors Only (E)", id="btn-error", variant="error")
            yield Button("Warnings (W)", id="btn-warning", variant="warning")
            yield Button("Back to Menu", id="btn-back", variant="default")

        yield RichLog(id="log-view", highlight=True, markup=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        """Load logs on mount."""
        self.query_one(RichLog).write("Loading logs... (Mock)")
        # In a real scenario, we would stream logs here or load from a file.
        # For this exercise, we will simulate loading some logs.
        self.load_mock_logs()

    def load_mock_logs(self) -> None:
        log = self.query_one(RichLog)
        log.clear()
        log.write("[bold green]INFO[/] System started successfully.")
        log.write("[bold green]INFO[/] Loaded configuration.")
        log.write("[bold red]ERROR[/] Connection to primary server failed.")
        log.write("[bold yellow]WARNING[/] High memory usage detected (85%).")
        log.write("[bold green]INFO[/] User logged in.")
        log.write("[bold red]ERROR[/] Module 'kernel_driver' did not load.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-back":
            self.action_back()
        elif btn_id == "btn-all":
            self.action_filter_all()
        elif btn_id == "btn-error":
            self.action_filter_error()
        elif btn_id == "btn-warning":
            self.action_filter_warning()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_filter_all(self) -> None:
        self.load_mock_logs() # Reset
        self.notify("Showing all logs")

    def action_filter_error(self) -> None:
        log = self.query_one(RichLog)
        log.clear()
        log.write("[bold red]ERROR[/] Connection to primary server failed.")
        log.write("[bold red]ERROR[/] Module 'kernel_driver' did not load.")
        self.notify("Showing errors only")

    def action_filter_warning(self) -> None:
        log = self.query_one(RichLog)
        log.clear()
        log.write("[bold yellow]WARNING[/] High memory usage detected (85%).")
        self.notify("Showing warnings only")
