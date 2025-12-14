from textual.app import ComposeResult
from textual.screen import Screen
from textual import events
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    Label,
    Select,
    RadioSet,
    RadioButton,
    Input,
)
from pathlib import Path
from textual.containers import Vertical, Horizontal, Container, VerticalScroll
from typing import Any, cast
from src.agent.config import load_config
from src.agent.client import SOSAgentClient


class SetupScreen(Screen):
    """Configuration and Setup screen."""

    CSS_PATH = "../styles.css"
    BINDINGS = [("escape", "back", "Back to Menu")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Setup & Configuration", classes="title")

        with VerticalScroll(id="setup-scroll"):
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
                        ["auto", "gemini", "openai", "inception", "claude-agentapi"],
                        id="provider-select",
                    )

                with Vertical(classes="panel"):
                    yield Label("Model")
                    yield Select([], id="model-select")

                with Vertical(classes="panel"):
                    yield Label("API Keys (Masked)")
                    yield Label("Gemini: ************", id="key-gemini")
                    yield Label("OpenAI: ************", id="key-openai")
                    yield Label("Inception: ************", id="key-inception")

        yield Static(id="status-output", classes="status-box")
        with Horizontal(id="setup-actions"):
            yield Button("Health Check", id="btn-health", variant="success")
            yield Button("Save & Apply", id="btn-save", variant="primary")

        yield Footer()

    async def on_mount(self) -> None:
        """Load current config."""
        self.config = await load_config(None)

        # Set UI state
        self.query_one("#lang-radio", RadioSet)
        if getattr(self.config, "ai_language", "en") == "cs":
            self.query_one("#lang-cz", RadioButton).value = True
        else:
            self.query_one("#lang-en", RadioButton).value = True

        # Provider
        provider_select = self.query_one("#provider-select", Select)
        provider_select.value = self.config.ai_provider

        await self._sync_model_select()
        provider_select.focus()

        # Keys
        # We don't show real keys for security, just status
        gemini_label = cast(Label, self.query_one("#key-gemini", Label))
        if self.config.gemini_api_key:
            gemini_label.update("Gemini: [green]Configured[/green]")
        else:
            gemini_label.update("Gemini: [red]Missing[/red]")

        openai_label = cast(Label, self.query_one("#key-openai", Label))
        if self.config.openai_api_key:
            openai_label.update("OpenAI: [green]Configured[/green]")
        else:
            openai_label.update("OpenAI: [red]Missing[/red]")

        inception_label = cast(Label, self.query_one("#key-inception", Label))
        if self.config.inception_api_key:
            inception_label.update("Inception: [green]Configured[/green]")
        else:
            inception_label.update("Inception: [red]Missing[/red]")

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "provider-select":
            await self._sync_model_select()

    async def _sync_model_select(self) -> None:
        provider_select = self.query_one("#provider-select", Select)
        model_select = self.query_one("#model-select", Select)
        provider = str(provider_select.value) if provider_select.value else "auto"

        options: list[tuple[str, str]] = []
        current_value: str | None = None

        if provider == "gemini":
            options = [
                ("gemini-2.0-flash-exp", "gemini-2.0-flash-exp"),
                ("gemini-2.0-flash", "gemini-2.0-flash"),
                ("gemini-1.5-pro", "gemini-1.5-pro"),
            ]
            current_value = self.config.gemini_model
        elif provider == "openai":
            options = [
                ("gpt-4o", "gpt-4o"),
                ("gpt-4o-mini", "gpt-4o-mini"),
                ("o1-mini", "o1-mini"),
            ]
            current_value = self.config.openai_model
        elif provider == "inception":
            options = [
                ("mercury-coder", "mercury-coder"),
                ("mercury", "mercury"),
            ]
            current_value = self.config.inception_model
        elif provider == "claude-agentapi":
            options = [
                ("claude-sonnet-4", "claude-sonnet-4"),
                ("claude-opus-4", "claude-opus-4"),
            ]
            current_value = self.config.model
        else:
            # auto mode: keep per-provider models, but don't force a single one
            options = [("(auto)", "(auto)")]
            current_value = "(auto)"

        model_select.set_options(options)
        model_select.value = current_value if current_value else options[0][1]

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-health":
            await self.run_health_check()
        elif event.button.id == "btn-save":
            await self.save_settings()

    async def run_health_check(self) -> None:
        """Run connectivity check via AI client."""
        output = cast(Static, self.query_one("#status-output", Static))
        output.update("[yellow]Running health check (Ping AI)...[/yellow]")

        try:
            app_client = getattr(self.app, "client", None)
            if not app_client:
                output.update("[red]Error: Client not initialized.[/red]")
                return

            client = cast(SOSAgentClient, app_client)
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

    async def save_settings(self) -> None:
        lang_radio = self.query_one("#lang-radio", RadioSet)
        pressed = lang_radio.pressed_button
        ai_language = "cs" if pressed and pressed.id == "lang-cz" else "en"

        provider_select = self.query_one("#provider-select", Select)
        provider = str(provider_select.value) if provider_select.value else "auto"

        model_select = self.query_one("#model-select", Select)
        model_value = str(model_select.value) if model_select.value else ""

        self.config.ai_language = ai_language
        self.config.ai_provider = provider

        if provider == "gemini" and model_value and model_value != "(auto)":
            self.config.gemini_model = model_value
        elif provider == "openai" and model_value and model_value != "(auto)":
            self.config.openai_model = model_value
        elif provider == "inception" and model_value and model_value != "(auto)":
            self.config.inception_model = model_value
        elif provider == "claude-agentapi" and model_value and model_value != "(auto)":
            self.config.model = model_value

        config_path = Path("config/default.yaml")
        self.config.to_yaml(config_path)

        # Apply changes to the running app immediately
        try:
            app = cast(Any, self.app)
            app.config = self.config
            app.client = SOSAgentClient(self.config)
            self.notify("Uloženo + aplikováno (config/default.yaml)")
        except Exception as e:
            self.notify(f"Uloženo, ale klient nešel přepnout: {e}")

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        """Arrow-key navigation between focusable controls (when not inside inputs/selects)."""
        focused = getattr(self.app, "focused", None)
        if isinstance(focused, (Input, Select, RadioSet)):
            return

        if event.key in {"up", "left"}:
            self.app.action_focus_previous()
            event.prevent_default()
            event.stop()
        elif event.key in {"down", "right"}:
            self.app.action_focus_next()
            event.prevent_default()
            event.stop()
