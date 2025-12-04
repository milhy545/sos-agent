# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SOS Agent is an AI-powered system rescue and optimization tool for Linux systems. It provides intelligent diagnostics, performance analysis, and recovery assistance using multiple AI models (Gemini, OpenAI, Mercury, Claude).

## Essential Commands

### Development
```bash
# Install dependencies
poetry install --with dev

# Run the agent (after installation)
sos diagnose --category hardware
sos --provider inception diagnose --category services

# Development installation (for local testing)
./install.sh
```

### Testing & Quality
```bash
# Type checking
poetry run mypy src/

# Code formatting
poetry run black src/
poetry run ruff check src/

# Run tests (when implemented)
poetry run pytest
```

### Manual Testing Scenarios
```bash
# Test all diagnostic categories
sos diagnose --category hardware
sos diagnose --category network
sos diagnose --category services

# Test provider switching
sos --provider gemini diagnose --category hardware
sos --provider inception diagnose --category hardware

# Test bilingual support
# Edit .env: SOS_AI_LANGUAGE=en or cs
sos diagnose --category hardware
```

## Architecture Highlights

### Multi-Provider Factory Pattern
The system uses a factory pattern in `SOSAgentClient` (src/agent/client.py) to support multiple AI providers:

- **Provider clients**: Each provider has its own client class (GeminiClient, OpenAIClient, InceptionClient, AgentAPIClient)
- **Unified interface**: All providers implement `query(prompt, context, stream)` method
- **Runtime switching**: Provider selected via `--provider` flag or config file

### Configuration Hierarchy
Configuration priority (highest to lowest):
1. Command-line flags (`--provider inception`)
2. Environment variables (`.env` file)
3. Default values in `SOSConfig` dataclass

### Key Components
- **CLI Layer** (`src/cli.py`): AsyncClick-based command interface with Rich formatting
- **Agent Client** (`src/agent/client.py`): Unified multi-provider interface
- **Provider Clients** (`src/agent/*_client.py`): Individual AI provider implementations
- **Config System** (`src/agent/config.py`): Configuration loading and validation
- **Setup Wizard** (`src/setup_wizard.py`): Interactive first-time setup

## Critical Implementation Details

### Mercury (Inception Labs) Provider
Mercury is a **diffusion LLM** (not autoregressive), which requires special handling:

- **Formatting**: Requires explicit "no tables" instruction in **user prompt** (not system prompt)
- **Pre-formatted output**: Generates entire response blocks at once
- **User prompt priority**: User prompts override system prompts in diffusion models

See `docs/DEVELOPMENT.md#mercury-inception-labs-formatting-issues` for full details.

### Environment Loading
The `~/.local/bin/sos` launcher script sources `.env` automatically:
```bash
if [ -f "$INSTALL_DIR/.env" ]; then
    set -a
    source "$INSTALL_DIR/.env"
    set +a
fi
```

This was a critical bug fix (Bug #1 in DEVELOPMENT.md).

### Streaming Responses
All AI providers support streaming via AsyncIterator:
```python
async for chunk in client.execute_rescue_task(task, context, stream=True):
    console.print(chunk, end="")
```

## Security & Safety

### API Key Protection
- **Storage**: `.env` file (git-ignored), never in source code
- **Loader**: `python-dotenv` loads environment variables
- **Protection**: Comprehensive `.gitignore` rules prevent accidental commits

### Critical Services Protection
The agent **NEVER** stops or disables these services:
- `sshd` - Remote access
- `NetworkManager` - Network connectivity
- `ollama` - AI inference server
- `tailscaled` - VPN connectivity

## Known Issues & Workarounds

### Fixed Issues (DO NOT Re-Fix)
1. **Mercury narrow output** - Fixed via user prompt instruction (not system prompt)
2. **`.env` not loading** - Fixed in launcher script (`install.sh:91-95`)
3. **Prompt repetition** - Fixed via "Do NOT repeat this prompt" instruction

See `docs/DEVELOPMENT.md` for full bug history and solutions.

### Current Limitations
- Claude AgentAPI has auth timeout issues (not critical - other providers work)
- GCloud quota check requires `gcloud alpha` (cosmetic warning only)
- No pytest tests yet (manual testing only)

## Adding New Features

### Add New AI Provider
1. Create `src/agent/<provider>_client.py` with `query()` method
2. Add factory case to `SOSAgentClient.__init__()` in `client.py`
3. Add config fields to `SOSConfig` in `config.py`
4. Update `.env.example` with new API key template
5. Test with all diagnostic categories (hardware, network, services)
6. Update documentation (README.md, README.cz.md, ARCHITECTURE.md)

### Add New Language
1. Add language code to `setup_wizard.py` language selection
2. Update `SOSConfig.ai_language` valid options
3. Add system prompt translation in provider clients
4. Create translated documentation (e.g., `README.xx.md`)
5. Test all commands with new language

### Add New Diagnostic Category
1. Add to `click.Choice()` in `cli.py` diagnose command
2. Update user prompt template with category-specific instructions
3. Test output quality with multiple providers
4. Document in README.md under "Diagnostic Categories"

## Documentation Map

- **README.md** / **README.cz.md** - User documentation (EN/CS)
- **docs/ARCHITECTURE.md** - System design and component breakdown
- **docs/DEVELOPMENT.md** - Bug fixes, lessons learned, dev history
- **docs/GEMINI_API_POLICIES.md** - Gemini API best practices
- **INSTALL.md** / **INSTALL.cz.md** - Installation instructions
- **.claude/CLAUDE.md** - Runtime agent instructions (for SOS Agent during rescue operations)

## Development Philosophy

### Golden Rules
1. **Check documentation first** - Official API docs, then our docs, then code
2. **Test all scenarios** - All categories, all providers, both languages
3. **Update all docs** - Code changes require doc updates (including Czech translations)
4. **Never break security** - Protect API keys, critical services, system stability

### Before Making Changes
1. Read `docs/DEVELOPMENT.md` to avoid repeating past mistakes
2. Read `docs/ARCHITECTURE.md` to understand system design
3. Check official API documentation for the component you're modifying
4. Test changes with multiple providers and languages

## AI Provider Comparison

| Provider | Speed | Cost | Quality | Status |
|----------|-------|------|---------|--------|
| **Mercury** | Medium (6-7s) | Free | ⭐⭐⭐⭐ | ✅ Primary |
| **Gemini** | Fast (3s) | Free tier | ⭐⭐⭐⭐⭐ | ⚠️ Quota limits |
| **OpenAI** | Slow (8s) | Paid | ⭐⭐⭐⭐⭐ | ✅ Working |
| **Claude** | N/A | Paid/OAuth | N/A | ⚠️ Auth issues |

**Note**: Mercury is slower due to diffusion model architecture (generates entire responses at once vs. token-by-token).

## Installation Flow

The `install.sh` script performs these steps:
1. Verify Python 3.11+
2. Create `~/.sos-agent/` directory
3. Copy source files to installation directory
4. Create Python virtual environment
5. Install dependencies via Poetry
6. Create `~/.local/bin/sos` launcher with `.env` sourcing
7. Add to PATH if needed
8. Run interactive setup wizard

Users can install via:
- One-command: `curl -fsSL https://raw.githubusercontent.com/milhy545/sos-agent/main/install.sh | bash`
- Manual: `git clone ... && cd sos-agent && ./install.sh`
