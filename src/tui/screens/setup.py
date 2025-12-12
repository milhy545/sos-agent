from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    Label,
    Select,
    RadioSet,
    RadioButton,
)
from textual.containers import Vertical, Horizontal, Container
from src.agent.config import load_config


class SetupScreen(Screen):
    """Configuration and Setup screen."""

    CSS_PATH = "../styles.css"
    BINDINGS = [("escape", "back", "Back to Menu")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Setup & Configuration", classes="title")

        with Container(classes="setup-container"):
            with Vertical(classes="panel"):
                yield Label("Language / Jazyk")
                yield RadioSet(
                    RadioButton("English", id="lang-en"),
                    RadioButton("Čeština", id="lang-cz"),
                    id="lang-radio",
                )

            with Vertical(classes="panel"):
                yield Label("AI Provider")
                yield Select.from_values(
                    ["gemini", "openai", "claude-agentapi"], id="provider-select"
                )

            with Vertical(classes="panel"):
                yield Label("API Keys (Masked)")
                yield Label("Gemini: ************", id="key-gemini")
                yield Label("OpenAI: ************", id="key-openai")

            with Horizontal():
                yield Button("Health Check", id="btn-health", variant="success")
                yield Button("Save Settings", id="btn-save", variant="primary")

            yield Static(id="status-output", classes="status-box")

        yield Footer()

    async def on_mount(self) -> None:
        """Load current config."""
        self.config = await load_config(None)

        # Set UI state
        # Language
        # TODO: Implement language in config

        # Provider
        # provider = self.config.ai_provider or "gemini"
        # Select widget usage might vary slightly by version, assuming standard
        # self.query_one("#provider-select").value = provider

        # Keys
        # We don't show real keys for security, just status
        if self.config.google_api_key:
            self.query_one("#key-gemini").update("Gemini: [green]Configured[/green]")
        else:
            self.query_one("#key-gemini").update("Gemini: [red]Missing[/red]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-health":
            await self.run_health_check()
        elif event.button.id == "btn-save":
            self.save_settings()

    async def run_health_check(self) -> None:
        """Run connectivity check via AI client."""
        output = self.query_one("#status-output")
        output.update("[yellow]Running health check (Ping AI)...[/yellow]")

        try:
            if not getattr(self.app, "client", None):
                output.update("[red]Error: Client not initialized.[/red]")
                return

            client = self.app.client
            response_text = ""

            # Use a short timeout task
            async for chunk in client.execute_rescue_task(
                "Ping. Respond with 'Pong'.", stream=False
            ):
                if hasattr(chunk, "content"):  # AgentAPI
                    for block in chunk.content:
                        if hasattr(block, "text"):
                            response_text += block.text
                elif isinstance(chunk, dict) and "content" in chunk:  # Claude
                    for block in chunk["content"]:
                        if block.get("type") == "text":
                            response_text += block["text"]
                else:
                    response_text += str(chunk)

            if response_text:
                output.update(
                    f"[green]Health Check Passed![/green]\nProvider: {client.client_type}\nResponse: {response_text.strip()[:100]}"
                )
            else:
                output.update("[red]Health Check Failed: No response[/red]")

        except Exception as e:
            output.update(f"[red]Health Check Failed: {e}[/red]")

    def save_settings(self) -> None:
        self.notify("Settings saving not yet implemented.")

    def action_back(self) -> None:
        self.app.pop_screen()
