import asyncio
from datetime import datetime
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, LoadingIndicator, Markdown
from textual.containers import Vertical, Center
from textual.worker import Worker, WorkerState

from src.tools.log_analyzer import analyze_system_logs

class DiagnosticsScreen(Screen):
    """Screen for running system diagnostics."""

    CSS_PATH = "../styles.css"
    BINDINGS = [
        ("escape", "back", "Back"),
        ("r", "run", "Run Diagnostics"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("SYSTEM DIAGNOSTICS", classes="title")

        with Vertical(id="diag-container"):
            yield Center(Button("Run Diagnostics (R)", id="btn-run", variant="primary"))
            yield LoadingIndicator(id="loading", classes="hidden")
            yield Markdown(id="results")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#results").update("Press 'Run Diagnostics' to start analysis.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-run":
            self.action_run()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_run(self) -> None:
        """Start the diagnostic worker."""
        self.query_one("#btn-run").disabled = True
        self.query_one("#loading").remove_class("hidden")
        self.query_one("#results").update("Analyzing system logs... This may take a moment.")

        self.run_worker(self.run_diagnostics(), exclusive=True, thread=True)

    async def run_diagnostics(self) -> str:
        """Run the actual diagnostic logic."""
        # We call the existing log_analyzer tool
        try:
            results = await analyze_system_logs(time_range="24h", severity="warning")

            # Save to session store
            if hasattr(self.app, "config"): # Ensure app context
                from src.session.store import FileSessionStore
                store = FileSessionStore()
                await store.save_diagnostic_result(results)
                # Also update current issue if recommendations exist
                if results.get("recommendations"):
                     await store.save_issue(results["recommendations"][0])

            # Format results as Markdown
            md = f"# Diagnostic Results - {datetime.now().strftime('%H:%M:%S')}\n\n"

            if results.get("recommendations"):
                md += "## Recommendations\n"
                for rec in results["recommendations"]:
                    md += f"- {rec}\n"

            if results.get("hardware_errors"):
                md += f"\n## 🔴 Hardware Errors ({len(results['hardware_errors'])})\n"
                for err in results["hardware_errors"]:
                    md += f"- **{err['unit']}**: {err['message']}\n"

            if results.get("driver_errors"):
                md += f"\n## ⚠️ Driver Errors ({len(results['driver_errors'])})\n"
                for err in results["driver_errors"]:
                    md += f"- **{err['unit']}**: {err['message']}\n"

            if results.get("service_errors"):
                md += f"\n## ⚠️ Service Errors ({len(results['service_errors'])})\n"
                for err in results["service_errors"]:
                    md += f"- **{err['unit']}**: {err['message']}\n"

            return md

        except Exception as e:
            return f"# Error\nFailed to run diagnostics: {str(e)}"

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker completion."""
        if event.state == WorkerState.SUCCESS:
            result = event.worker.result
            self.query_one("#loading").add_class("hidden")
            self.query_one("#results").update(result)
            self.query_one("#btn-run").disabled = False
            self.notify("Diagnostics complete.", severity="information")

        elif event.state == WorkerState.ERROR:
            self.query_one("#loading").add_class("hidden")
            self.query_one("#results").update(f"Error: {event.worker.error}")
            self.query_one("#btn-run").disabled = False
            self.notify("Diagnostics failed.", severity="error")
