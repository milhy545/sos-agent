import asyncio
from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static, RichLog, Select
from textual.containers import Vertical, Horizontal, VerticalScroll
from src.session.store import FileSessionStore
from src.tools.log_analyzer import analyze_system_logs
from src.agent.client import SOSAgentClient


class DiagnosticsScreen(Screen):
    """Diagnostics hub in TUI."""

    CSS_PATH = "../styles.css"
    BINDINGS = [("escape", "back", "Back to Menu")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        client_type = getattr(getattr(self.app, "client", None), "client_type", None)
        suffix = f" ({client_type})" if client_type else ""
        yield Static(f"Diagnostics Center{suffix}", classes="title")

        with VerticalScroll(id="diag-scroll"):
            with Vertical(id="diag-panel", classes="panel"):
                yield Static(
                    "Spusť diagnostiku přímo odsud.\n"
                    "Použije uložený `--issue` jako kontext.",
                    classes="body",
                )
                yield Static("", id="diag-issue")
                yield Select.from_values(
                    ["all", "hardware", "services", "network"],
                    id="diag-category",
                )
                yield RichLog(id="diag-log", wrap=True)

        with Horizontal(id="diag-actions"):
            yield Button("Run Diagnostics", id="btn-run", variant="success")
            yield Button("Refresh Issue", id="btn-refresh", variant="primary")

        yield Footer()

    async def on_mount(self) -> None:
        await self._load_issue()

    async def on_show(self) -> None:
        client_type = getattr(getattr(self.app, "client", None), "client_type", None)
        suffix = f" ({client_type})" if client_type else ""
        self.query_one(".title", Static).update(f"Diagnostics Center{suffix}")

    async def _load_issue(self) -> None:
        store = FileSessionStore()
        issue = await store.get_issue()
        issue_label = self.query_one("#diag-issue", Static)
        issue_label.update(
            f"[bold yellow]Aktuální problém:[/bold yellow] {issue}"
            if issue
            else "[dim]Žádný uložený problém z `--issue`.[/dim]"
        )
        log = self.query_one("#diag-log", RichLog)
        log.clear()
        log.write("Ready.")

    async def _collect_system_info(self) -> tuple[str, str]:
        async def _cmd(cmd: str) -> str:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, _ = await proc.communicate()
            return out.decode(errors="replace")

        try:
            os_release = await _cmd("cat /etc/os-release")
            uname = await _cmd("uname -a")
            system_info = f"OS:\\n{os_release}\\nKernel:\\n{uname}"
        except Exception:
            system_info = "Could not detect OS info."

        try:
            free = await _cmd("free -h")
            df = await _cmd("df -h /")
            uptime = await _cmd("uptime")
            resources = f"Memory:\\n{free}\\nDisk:\\n{df}\\nLoad:\\n{uptime}"
        except Exception:
            resources = "Could not collect resource info."

        return system_info, resources

    async def _run_diagnostics(self, category: str) -> None:
        log = self.query_one("#diag-log", RichLog)
        log.clear()
        log.write("[dim]Collecting logs...[/dim]")

        errors = await analyze_system_logs(time_range="24h", severity="error")
        warnings = await analyze_system_logs(time_range="24h", severity="warning")

        def _dedupe(entries):
            seen = set()
            unique = []
            for entry in entries:
                key = (entry.get("unit", ""), entry.get("message", ""))
                if key in seen:
                    continue
                seen.add(key)
                unique.append(entry)
            return unique

        log_data = {
            "hardware_errors": _dedupe(
                errors["hardware_errors"] + warnings["hardware_errors"]
            ),
            "driver_errors": _dedupe(
                errors["driver_errors"] + warnings["driver_errors"]
            ),
            "service_errors": _dedupe(
                errors["service_errors"] + warnings["service_errors"]
            ),
            "security_warnings": _dedupe(
                errors["security_warnings"] + warnings["security_warnings"]
            ),
            "recommendations": errors["recommendations"] + warnings["recommendations"],
        }

        log.write("[dim]Collecting system info...[/dim]")
        system_info, resources = await self._collect_system_info()

        store = FileSessionStore()
        issue = await store.get_issue()

        prompt = f"""
Analyze the REAL collected data and return a concise one-page summary (max ~25 lines).

User Issue Description:
{issue if issue else "No specific issue provided."}

Category: {category}

System:
{system_info}

Resources:
{resources}

Log summary (last 24h, deduped):
- Hardware errors: {len(log_data['hardware_errors'])}
- Driver errors: {len(log_data['driver_errors'])}
- Service errors: {len(log_data['service_errors'])}
- Security warnings: {len(log_data['security_warnings'])}

Analyzer Recommendations (automated pre-analysis):
{chr(10).join(f"- {r}" for r in log_data['recommendations'])}
""".strip()

        app_client = getattr(self.app, "client", None)
        if not app_client:
            log.write("[red]Client not initialized.[/red]")
            return
        client = app_client
        assert isinstance(client, SOSAgentClient)

        log.write("[bold cyan]Running diagnostics...[/bold cyan]")
        response_text = ""
        async for chunk in client.execute_rescue_task(prompt):
            response_text += str(chunk)
        log.write(response_text)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh":
            await self._load_issue()
        elif event.button.id == "btn-run":
            category = str(self.query_one("#diag-category", Select).value or "all")
            await self._run_diagnostics(category)

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        focused = getattr(self.app, "focused", None)
        if isinstance(focused, Select):
            return
        if event.key in {"up", "left"}:
            self.app.action_focus_previous()
            event.prevent_default()
            event.stop()
        elif event.key in {"down", "right"}:
            self.app.action_focus_next()
            event.prevent_default()
            event.stop()
