from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static, Label
from textual.containers import Horizontal, Vertical
from src.tui.screens.chat import ChatScreen
from src.tui.screens.fix import FixScreen
from src.tui.screens.monitor import MonitorScreen
from src.tui.screens.setup import SetupScreen
from src.tui.screens.diagnostics import DiagnosticsScreen
from src.tui.screens.logs import LogsScreen
from src.session.store import FileSessionStore


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

        with Vertical(id="status-bar"):
            yield Static(
                "SOS AGENT // antiX-cli-cc EDITION", id="title", classes="title"
            )
            yield Label("Session: loading...", id="session-label")
            yield Label("Provider: loading...", id="provider-label")

        with Vertical(classes="menu-grid"):
            with Horizontal(classes="menu-row"):
                yield Button("1. System Diagnostics", id="btn-1", variant="primary")
                yield Button("2. Fix Issues", id="btn-2")
            with Horizontal(classes="menu-row"):
                yield Button("3. Monitor System", id="btn-3")
                yield Button("4. AI Chat Assistant", id="btn-4")
            with Horizontal(classes="menu-row"):
                yield Button("5. Setup & Config", id="btn-5")
                yield Button("6. Logs & History", id="btn-6")
            with Horizontal(classes="menu-row"):
                yield Button("7. Boot/GRUB Check", id="btn-7")
                yield Button("8. Optimize Apps", id="btn-8")
            with Horizontal(classes="menu-row"):
                yield Button(
                    "9. EMERGENCY RECOVERY",
                    id="btn-9",
                    classes="btn-emergency",
                )
                yield Button("0. Quit", id="btn-0", variant="error")

        yield Footer()

    async def on_mount(self) -> None:
        await self._refresh_status()
        # Default focus for keyboard navigation
        self.query_one("#btn-1", Button).focus()

    async def on_show(self) -> None:
        await self._refresh_status()

    async def _refresh_status(self) -> None:
        # Show current issue status
        store = FileSessionStore()
        issue = await store.get_issue()
        label = self.query_one("#session-label", Label)
        if issue:
            label.update(f"[yellow]Issue:[/yellow] {issue}")
        else:
            label.update("[dim]No issue stored. Run sos diagnose --issue ...[/dim]")

        provider_label = self.query_one("#provider-label", Label)
        cfg = getattr(self.app, "config", None)
        client = getattr(self.app, "client", None)
        provider = getattr(cfg, "ai_provider", "unknown") if cfg else "unknown"
        lang = getattr(cfg, "ai_language", "en") if cfg else "en"
        model = ""
        if cfg:
            if provider == "gemini":
                model = getattr(cfg, "gemini_model", "")
            elif provider == "openai":
                model = getattr(cfg, "openai_model", "")
            elif provider == "inception":
                model = getattr(cfg, "inception_model", "")
            elif provider == "claude-agentapi":
                model = getattr(cfg, "model", "")
        runtime = getattr(client, "client_type", None)
        runtime_str = f" (active: {runtime})" if runtime else ""
        model_str = f" / {model}" if model else ""
        provider_label.update(
            f"[cyan]Provider:[/cyan] {provider}{model_str}{runtime_str}  [cyan]Lang:[/cyan] {lang}"
        )

    def on_key(self, event: events.Key) -> None:
        """Arrow-key navigation between menu buttons."""
        key = event.key
        if key not in {"up", "down", "left", "right"}:
            return

        layout = [
            ["btn-1", "btn-2"],
            ["btn-3", "btn-4"],
            ["btn-5", "btn-6"],
            ["btn-7", "btn-8"],
            ["btn-9", "btn-0"],
        ]

        focused = getattr(self.app, "focused", None)
        focused_id = getattr(focused, "id", None)
        row = col = None
        for r, cols in enumerate(layout):
            for c, bid in enumerate(cols):
                if bid == focused_id:
                    row, col = r, c
                    break
            if row is not None:
                break

        if row is None or col is None:
            self.query_one("#btn-1", Button).focus()
            event.prevent_default()
            event.stop()
            return

        new_row, new_col = row, col
        if key == "up":
            new_row = max(0, row - 1)
        elif key == "down":
            new_row = min(len(layout) - 1, row + 1)
        elif key == "left":
            new_col = max(0, col - 1)
        elif key == "right":
            new_col = min(len(layout[row]) - 1, col + 1)

        self.query_one(f"#{layout[new_row][new_col]}", Button).focus()
        event.prevent_default()
        event.stop()

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
        elif btn_id == "btn-6":
            self.action_logs()
        elif btn_id == "btn-9":
            self.action_emergency()
        # Add other actions as they are implemented

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

    def action_emergency(self) -> None:
        self.notify("Emergency mode not implemented in TUI yet")
