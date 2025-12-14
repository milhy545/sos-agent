from dataclasses import dataclass
from typing import List, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from src.tui.screens.chat import ChatScreen
from src.tui.screens.diagnostics import DiagnosticsScreen
from src.tui.screens.fix import FixScreen
from src.tui.screens.logs import LogsScreen
from src.tui.screens.monitor import MonitorScreen
from src.tui.screens.setup import SetupScreen
from src.session.store import FileSessionStore


@dataclass
class MenuItem:
    id: str
    label: str
    action: str
    key: str
    variant: str = "default"
    implemented: bool = True
    classes: str = ""


class MainMenu(Screen):
    """Main menu screen for SOS Agent."""

    CSS_PATH = "../styles.css"

    MENU_ITEMS: List[MenuItem] = [
        MenuItem("btn-1", "1. System Diagnostics", "diagnose", "1", variant="primary"),
        MenuItem("btn-2", "2. Fix Issues", "fix", "2"),
        MenuItem("btn-3", "3. Monitor System", "monitor", "3"),
        MenuItem("btn-4", "4. AI Chat Assistant", "chat", "4"),
        MenuItem("btn-5", "5. Setup & Config", "setup", "5"),
        MenuItem("btn-6", "6. Logs & History", "logs", "6"),
        MenuItem(
            "btn-7", "7. Boot/GRUB Check", "boot", "7", implemented=False
        ),
        MenuItem(
            "btn-8", "8. Optimize Apps", "optimize", "8", implemented=False
        ),
        MenuItem(
            "btn-9",
            "9. EMERGENCY RECOVERY",
            "emergency",
            "9",
            classes="btn-emergency",
            implemented=False,
        ),
        MenuItem("btn-0", "0. Quit", "quit", "0", variant="error"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Generate bindings dynamically
        self.BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("escape", "quit", "Quit"),
        ]
        for item in self.MENU_ITEMS:
            self.BINDINGS.append(Binding(item.key, item.action, item.label))

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("SOS AGENT - CYBERPUNK EDITION", id="title", classes="title")

        # Status Bar
        yield Static(
            "Status: Online | Provider: Unknown | Last Diagnosis: None",
            id="status-bar",
            classes="status-bar",
        )

        with Grid(classes="menu-grid"):
            for item in self.MENU_ITEMS:
                label = item.label
                if not item.implemented:
                    label += " (Coming Soon)"

                yield Button(
                    label,
                    id=item.id,
                    variant=item.variant,
                    classes=item.classes,
                    disabled=not item.implemented and item.action != "quit",
                )

        yield Footer()

    async def on_mount(self) -> None:
        """Refresh status bar on mount."""
        await self.update_status_bar()

    async def on_screen_resume(self) -> None:
        """Refresh status bar when returning to menu."""
        await self.update_status_bar()

    async def update_status_bar(self) -> None:
        """Update the status bar with current session info."""
        provider = "Unknown"
        last_diag = "None"
        current_issue = "None"

        # Get provider from config if available
        if hasattr(self.app, "config") and self.app.config:
            provider = getattr(self.app.config, "ai_provider", "Unknown").upper()

        # Get last diagnostic result and issue
        try:
            store = FileSessionStore()

            last_diag_data = await store.get_last_diagnostic_result()
            if last_diag_data:
                last_diag = "Recorded"

            issue = await store.get_issue()
            if issue:
                # Show snippet (first 30 chars)
                current_issue = (issue[:30] + "...") if len(issue) > 30 else issue

        except Exception:
            pass

        status_text = f"Status: Online | Provider: {provider} | Issue: {current_issue} | Last Diagnosis: {last_diag}"
        self.query_one("#status-bar").update(status_text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses by mapping ID to action."""
        btn_id = event.button.id
        for item in self.MENU_ITEMS:
            if item.id == btn_id:
                # Dispatch action
                method_name = f"action_{item.action}"
                if hasattr(self, method_name):
                    getattr(self, method_name)()
                else:
                    self.notify(f"Action {item.action} not implemented yet.", severity="warning")
                return

    def action_quit(self) -> None:
        self.app.exit()

    def action_diagnose(self) -> None:
        self.app.push_screen(DiagnosticsScreen())

    def action_fix(self) -> None:
        self.app.push_screen(FixScreen())

    def action_monitor(self) -> None:
        self.app.push_screen(MonitorScreen())

    def action_chat(self) -> None:
        self.app.push_screen(ChatScreen())

    def action_setup(self) -> None:
        self.app.push_screen(SetupScreen())

    def action_logs(self) -> None:
        self.app.push_screen(LogsScreen())

    def action_boot(self) -> None:
        self.notify("Boot check coming soon!", severity="info")

    def action_optimize(self) -> None:
        self.notify("Optimization tools coming soon!", severity="info")

    def action_emergency(self) -> None:
        self.notify("Emergency Recovery not implemented yet.", severity="error")
