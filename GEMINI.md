# SOS Agent - Gemini Context

## Project Overview
**SOS Agent** is an AI-powered system rescue and optimization tool designed for Linux systems. It acts as an intelligent system administrator, providing diagnostics, performance analysis, and recovery assistance using multiple AI models (Gemini, OpenAI, Inception Labs Mercury, Claude).

Key features include:
- **Multi-Model Support:** Seamlessly switches between Gemini, OpenAI, Mercury, and Claude.
- **Real Data Diagnostics:** Analyzes actual system logs (`journalctl`, including kernel logs), hardware info, and resource usage.
- **Safety First:** Explicitly protects critical services (sshd, NetworkManager) and favors non-destructive operations.
- **Bilingual:** Fully supports English and Czech (output and documentation).

## Tech Stack
- **Language:** Python 3.11+
- **Dependency Management:** Poetry
- **CLI Framework:** `asyncclick`, `rich`
- **AI Integration:** `google-generativeai`, `openai`, custom clients for Mercury/AgentAPI.
- **System Tools:** `systemd`, `journalctl`, `psutil`.

## Key Architecture & Patterns

### 1. AI Client Factory
The system uses a factory pattern in `src/agent/client.py` to manage different AI providers.
- **Unified Interface:** All clients implement a `query(prompt, context, stream)` method.
- **Configuration:** Providers are selected via CLI flags (`--provider`) or `config/default.yaml`.

### 2. Diagnostic Workflow (CRITICAL)
**Rule: "Rescue Agent must first identify what it's rescuing"**
The agent strictly follows a "Collect -> Analyze -> Act" workflow.
1. **Collect Data:** `src/tools/log_analyzer.py` MUST be called to fetch real system/kernel logs.
2. **Analyze:** The collected text/JSON data is inserted into the prompt context.
3. **Act:** The AI model generates recommendations based *only* on the provided data.
*Note: Never ask the AI to "check logs" without providing the log content in the prompt.*

### 3. Mercury (Inception Labs) Specifics
The Mercury model is a diffusion LLM and behaves differently:
- **Formatting:** It requires explicit user prompt instructions to **avoid ASCII tables** and use bullet points.
- **Repetition:** It tends to echo prompts, so specific "Do NOT repeat this prompt" instructions are used.

## Development Workflow

### Installation & Setup
```bash
# Install dependencies
poetry install --with dev

# Setup environment
cp .env.example .env
# Populate .env with API keys (GEMINI_API_KEY, etc.)
```

### Running the CLI
```bash
# Run via Poetry
poetry run python -m src.cli diagnose --category hardware

# Run via installed script (simulating end-user)
./sos-launcher.sh diagnose --category services
```

### Testing & Quality
**Note:** There are currently no automated tests (pytest is set up but empty). Testing is primarily manual.
```bash
# Type checking
poetry run mypy src/

# Formatting & Linting
poetry run black src/
poetry run ruff check src/
```

## Critical "Golden Rules" (from DEVELOPMENT.md)

1.  **Always Look Back:** Verify the result matches intention. Don't just send text to terminal; verify it displayed correctly.
2.  **System Detection First:** Identify OS, hardware, and kernel before diagnosing.
3.  **Real Data Collection:** Ensure `log_analyzer.py` captures **BOTH** system and kernel logs (`journalctl -k`). GPU/driver errors often live in kernel logs.
4.  **Warning Levels:** Critical issues can appear as warnings. Collect both `ERROR` and `WARNING` levels.

## Directory Structure
- `src/`: Source code.
    - `agent/`: AI client implementations (`gemini_client.py`, `openai_client.py`, etc.).
    - `tools/`: System interaction tools (`log_analyzer.py`).
    - `monitors/`: Real-time monitoring logic.
    - `cli.py`: Main entry point and command definitions.
- `docs/`: Extensive documentation. **Read `DEVELOPMENT.md` before complex changes.**
- `config/`: Default configuration YAMLs.

## Configuration
- **`.env`**: API keys and local overrides. **Never commit this.**
- **`config/default.yaml`**: Application defaults (model selection, timeouts).

## Documentation
- `README.md` / `README.cz.md`: User-facing documentation.
- `docs/DEVELOPMENT.md`: History of bugs, fixes, and architectural decisions. **Highly recommended reading.**
- `docs/ARCHITECTURE.md`: High-level system design.
