from textual import events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, RichLog, Static
from src.session.store import FileSessionStore
from src.agent.client import SOSAgentClient
from src.agent.config import load_config


class ChatScreen(Screen):
    """Chat screen for interacting with the AI Agent."""

    CSS_PATH = "../styles.css"
    BINDINGS = [("escape", "back", "Back to Menu")]

    def __init__(
        self, name: str | None = None, id: str | None = None, classes: str | None = None
    ):
        super().__init__(name, id, classes)
        self.store = FileSessionStore()
        # Client will be accessed from app or initialized lazily if app doesn't have it
        self.client: SOSAgentClient | None = None
        self.prompt_history: list[str] = []
        self.prompt_history_index: int | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        client_type = getattr(getattr(self.app, "client", None), "client_type", None)
        suffix = f" ({client_type})" if client_type else ""
        yield Static(f"SOS Chat Assistant{suffix}", classes="title")
        yield RichLog(id="chat-log", markup=True, wrap=True)
        yield Input(placeholder="Type your message...", id="chat-input")
        yield Footer()

    async def on_mount(self) -> None:
        """Load history and initialize client."""
        # Load history
        history = await self.store.get_chat_history()
        log = self.query_one(RichLog)
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            style = "chat-message-user" if role == "user" else "chat-message-ai"
            log.write(f"[{style}]{role.upper()}: {content}[/{style}]")

        # Initialize client if not present in app
        if hasattr(self.app, "client") and self.app.client:
            self.client = self.app.client
        else:
            # Fallback: load config and create client
            config = await load_config(None)
            self.client = SOSAgentClient(config)

    async def on_show(self) -> None:
        # Refresh title with current client type
        client_type = getattr(getattr(self.app, "client", None), "client_type", None)
        suffix = f" ({client_type})" if client_type else ""
        self.query_one(Static).update(f"SOS Chat Assistant{suffix}")

    def action_back(self) -> None:
        self.app.pop_screen()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input."""
        message = event.value
        if not message:
            return

        if not self.prompt_history or self.prompt_history[-1] != message:
            self.prompt_history.append(message)
        self.prompt_history_index = None

        input_widget = self.query_one(Input)
        input_widget.value = ""

        log = self.query_one(RichLog)
        log.write(f"[chat-message-user]USER: {message}[/chat-message-user]")

        await self.store.save_chat_message("user", message)

        # Get context (issue)
        issue = await self.store.get_issue()
        context_msg = ""
        if issue:
            context_msg = f"Context (User Issue): {issue}\n\n"

        # Prepare prompt
        # In a real chat, we should send history.
        # For this implementation, we'll append the last user message to the task
        # Ideally, execute_rescue_task should support chat history, but currently it takes a 'task' string.
        # We will wrap it.

        full_prompt = f"{context_msg}{message}"

        log.write("[chat-message-ai]AI: ...[/chat-message-ai]")

        # We need to handle the streaming response and update the log
        # Since RichLog appends, we might want to buffer the AI response or just print chunks?
        # RichLog.write appends a new line usually.
        # Textual's RichLog doesn't support updating the last line easily unless we use a static widget we update?
        # Better: Accumulate response and write it at the end, or write chunks.
        # For now, let's accumulate and write at the end for simplicity, or try to stream if possible.
        # Streaming to RichLog: log.write(chunk) works but might create many lines.

        response_content = ""
        try:
            if self.client:
                # We need to run this in a way that doesn't block the UI loop too much
                # But execute_rescue_task is async generator.

                # Note: execute_rescue_task returns a stream
                stream = self.client.execute_rescue_task(full_prompt)

                async for chunk in stream:
                    text_chunk = ""
                    if hasattr(chunk, "content"):
                        for block in chunk.content:
                            if hasattr(block, "text"):
                                text_chunk += block.text
                    elif isinstance(chunk, dict) and "content" in chunk:
                        for block in chunk["content"]:
                            if block.get("type") == "text":
                                text_chunk += block["text"]
                    elif isinstance(chunk, str):
                        text_chunk = chunk

                    if text_chunk:
                        response_content += text_chunk
                        # Optional: Streaming update logic here (complex with RichLog)

                # Write full response
                log.write(f"[chat-message-ai]AI: {response_content}[/chat-message-ai]")
                await self.store.save_chat_message("assistant", response_content)

        except Exception as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    def on_key(self, event: events.Key) -> None:
        """Enable ↑/↓ prompt history when the input is focused."""
        focused = getattr(self.app, "focused", None)
        input_widget = self.query_one("#chat-input", Input)
        if focused is not input_widget:
            return
        if not self.prompt_history:
            return

        if event.key == "up":
            if self.prompt_history_index is None:
                self.prompt_history_index = len(self.prompt_history) - 1
            else:
                self.prompt_history_index = max(0, self.prompt_history_index - 1)
            input_widget.value = self.prompt_history[self.prompt_history_index]
            event.prevent_default()
            event.stop()
        elif event.key == "down":
            if self.prompt_history_index is None:
                return
            if self.prompt_history_index >= len(self.prompt_history) - 1:
                self.prompt_history_index = None
                input_widget.value = ""
            else:
                self.prompt_history_index += 1
                input_widget.value = self.prompt_history[self.prompt_history_index]
            event.prevent_default()
            event.stop()
