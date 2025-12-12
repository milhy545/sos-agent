from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Grid
from src.tui.screens.chat import ChatScreen
from src.tui.screens.fix import FixScreen
from src.tui.screens.monitor import MonitorScreen
from src.tui.screens.setup import SetupScreen


class MainMenu(Screen):
    """Main menu screen for SOS Agent."""

    CSS_PATH = "../styles.css"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("0", "quit", "Quit"),
        ("1", "diagnose", "Diagnose"),
        ("2", "fix", "Fix"),
        ("3", "monitor", "Monitor"),
        ("4", "chat", "Chat"),
        ("5", "setup", "Setup"),
        ("6", "logs", "Logs"),
        ("7", "boot", "Boot Check"),
        ("8", "optimize", "Optimize"),
        ("9", "emergency", "Emergency"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("SOS AGENT - CYBERPUNK EDITION", id="title", classes="title")

        with Grid(classes="menu-grid"):
            yield Button("1. System Diagnostics", id="btn-1", variant="primary")
            yield Button("2. Fix Issues", id="btn-2")
            yield Button("3. Monitor System", id="btn-3")
            yield Button("4. AI Chat Assistant", id="btn-4")
            yield Button("5. Setup & Config", id="btn-5")
            yield Button("6. Logs & History", id="btn-6")
            yield Button("7. Boot/GRUB Check", id="btn-7")
            yield Button("8. Optimize Apps", id="btn-8")
            yield Button("9. EMERGENCY RECOVERY", id="btn-9", classes="btn-emergency")
            yield Button("0. Quit", id="btn-0", variant="error")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        btn_id = event.button.id
        if btn_id == "btn-0":
            self.app.exit()
        elif btn_id == "btn-1":
            self.action_diagnose()
        elif btn_id == "btn-2":
            self.action_fix()
        elif btn_id == "btn-3":
            self.action_monitor()
        elif btn_id == "btn-4":
            self.action_chat()
        elif btn_id == "btn-5":
            self.action_setup()
        elif btn_id == "btn-9":
            self.action_emergency()
        # Add other actions as they are implemented

    def action_quit(self) -> None:
        self.app.exit()

    def action_diagnose(self) -> None:
        self.notify("Diagnostics not implemented in TUI yet")

    def action_fix(self) -> None:
        self.app.push_screen(FixScreen())

    def action_monitor(self) -> None:
        self.app.push_screen(MonitorScreen())

    def action_chat(self) -> None:
        self.app.push_screen(ChatScreen())

    def action_setup(self) -> None:
        self.app.push_screen(SetupScreen())

    def action_emergency(self) -> None:
        self.notify("Emergency mode not implemented in TUI yet")
