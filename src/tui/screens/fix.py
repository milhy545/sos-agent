from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    ListView,
    ListItem,
    Label,
    RichLog,
)
from textual.containers import Horizontal, Vertical
from src.tools.fixers import get_all_fixers
from src.agent.privilege import is_root


class FixScreen(Screen):
    """Screen for applying system fixes."""

    CSS_PATH = "../styles.css"
    BINDINGS = [("escape", "back", "Back to Menu")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("System Fixers", classes="title")

        with Horizontal():
            with Vertical(id="fixer-list-container", classes="panel"):
                yield Label("Available Fixers:")
                yield ListView(id="fixer-list")

            with Vertical(id="fixer-details-container", classes="panel"):
                yield Label("Details & Output:", id="details-label")
                yield RichLog(id="fix-log", markup=True, wrap=True)

                with Horizontal(id="fix-actions"):
                    yield Button("Check Status", id="btn-check", variant="primary")
                    yield Button("Dry Run Fix", id="btn-dry-run", variant="warning")
                    yield Button(
                        "EXECUTE FIX", id="btn-execute", variant="error", disabled=True
                    )

        yield Footer()

    def on_mount(self) -> None:
        """Load fixers."""
        self.fixers = get_all_fixers()
        list_view = self.query_one("#fixer-list", ListView)

        for fixer in self.fixers:
            list_view.append(
                ListItem(Label(f"{fixer.name} ({fixer.category})"), id=fixer.id)
            )

        self.selected_fixer = None

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle fixer selection."""
        if not event.item:
            return

        fixer_id = event.item.id
        self.selected_fixer = next((f for f in self.fixers if f.id == fixer_id), None)

        if self.selected_fixer:
            log = self.query_one(RichLog)
            log.clear()
            log.write(
                f"[bold cyan]Selected Fixer:[/bold cyan] {self.selected_fixer.name}"
            )
            log.write(f"Category: {self.selected_fixer.category}")
            log.write(f"Requires Root: {self.selected_fixer.requires_root}")

            # Reset buttons
            self.query_one("#btn-execute").disabled = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle buttons."""
        if not self.selected_fixer:
            return

        log = self.query_one(RichLog)
        btn_id = event.button.id

        if btn_id == "btn-check":
            log.write("\n[dim]Checking status...[/dim]")
            needs_fix, reason = await self.selected_fixer.check()
            if needs_fix:
                log.write(f"[bold red]Issue Detected:[/bold red] {reason}")
            else:
                log.write(f"[bold green]Status OK:[/bold green] {reason}")

        elif btn_id == "btn-dry-run":
            log.write("\n[dim]Running Dry Run...[/dim]")
            plan = await self.selected_fixer.apply(dry_run=True)
            log.write("[bold yellow]Plan:[/bold yellow]")
            for step in plan:
                log.write(f"- {step}")

            log.write(
                "\n[bold]Review the plan above. Click 'EXECUTE FIX' to apply.[/bold]"
            )
            self.query_one("#btn-execute").disabled = False

        elif btn_id == "btn-execute":
            if self.selected_fixer.requires_root and not is_root():
                log.write(
                    "\n[bold red]ERROR: This fix requires ROOT privileges.[/bold red]"
                )
                log.write("Please run 'sudo sos menu' to execute this fix.")
                return

            log.write("\n[bold red]EXECUTING FIX...[/bold red]")
            try:
                results = await self.selected_fixer.apply(dry_run=False)
                for res in results:
                    log.write(f"[green]✓ {res}[/green]")
                log.write("[bold green]Fix Applied Successfully![/bold green]")
                self.query_one("#btn-execute").disabled = True
            except Exception as e:
                log.write(f"[bold red]Fix Failed:[/bold red] {e}")

    def action_back(self) -> None:
        self.app.pop_screen()
