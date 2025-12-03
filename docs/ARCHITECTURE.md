# SOS Agent - System Architecture

**Version**: 0.1.0
**Last Updated**: 2024-12-03

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │  sos command  │  (CLI entry point)
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │   CLI Layer   │  (asyncclick, Rich console)
         │  (src/cli.py) │
         └───────┬───────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │   SOSAgentClient           │  (Unified interface)
    │   (src/agent/client.py)    │
    └────────┬───────────────────┘
             │
             ├─────────────┬─────────────┬─────────────┐
             ▼             ▼             ▼             ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
    │  Gemini    │ │  OpenAI    │ │  Mercury   │ │   Claude   │
    │  Client    │ │  Client    │ │  Client    │ │  AgentAPI  │
    └────────────┘ └────────────┘ └────────────┘ └────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                         │
                         ▼
                   ┌──────────┐
                   │   APIs   │
                   └──────────┘
```

---

## 📦 Component Breakdown

### 1. CLI Layer (`src/cli.py`)
**Responsibility**: User interface, command parsing, output formatting

**Key Components**:
- `@cli.group()` - Main command group
- `diagnose()` - System diagnostics command
- `gcloud()` - GCloud management commands
- `setup()` - Setup wizard launcher

**Technology**: AsyncClick (async CLI framework), Rich (terminal formatting)

**Input**: User commands (`sos diagnose --category hardware`)
**Output**: Formatted diagnostic reports

---

### 2. Agent Client Layer (`src/agent/client.py`)
**Responsibility**: Unified interface to multiple AI providers

**Key Class**: `SOSAgentClient`

**Factory Pattern**:
```python
if config.ai_provider == "gemini":
    self.client = GeminiClient(...)
elif config.ai_provider == "openai":
    self.client = OpenAIClient(...)
elif config.ai_provider == "inception":
    self.client = InceptionClient(...)
elif config.ai_provider == "claude-agentapi":
    self.client = AgentAPIClient(...)
```

**Methods**:
- `execute_rescue_task(task, context, stream)` - Main entry point for diagnostics
- Handles streaming responses from all providers

---

### 3. AI Provider Clients

#### 3.1 Gemini Client (`src/agent/gemini_client.py`)
- **API**: Google Generative AI SDK
- **Model**: `gemini-2.0-flash-exp`
- **Streaming**: Native streaming support
- **Rate Limits**: 5 RPM / 25 RPD (free tier)
- **Status**: ⚠️ Often quota-exceeded

#### 3.2 OpenAI Client (`src/agent/openai_client.py`)
- **API**: OpenAI Python SDK
- **Model**: `gpt-4o`
- **Streaming**: AsyncOpenAI with SSE
- **Cost**: $0.005/1K input, $0.015/1K output
- **Status**: ✅ Working (user quota issue)

#### 3.3 Mercury Client (`src/agent/inception_client.py`)
- **API**: Inception Labs (OpenAI-compatible)
- **Model**: `mercury-coder`
- **Type**: Diffusion LLM (not autoregressive!)
- **Streaming**: Custom SSE parsing
- **Special Handling**: Requires explicit "no tables" prompt
- **Status**: ✅ Primary provider

#### 3.4 Claude AgentAPI (`src/agent/agentapi_client.py`)
- **API**: Claude Agent SDK
- **Auth**: OAuth via Claude CLI
- **Model**: `claude-sonnet-4`
- **Status**: ⚠️ Has auth timeout issues

---

### 4. Configuration Layer (`src/agent/config.py`)

**Key Class**: `SOSConfig` (dataclass)

**Configuration Sources** (priority order):
1. Command-line flags (`--provider inception`)
2. Environment variables (`.env` file)
3. Default values

**Key Parameters**:
```python
@dataclass
class SOSConfig:
    # API Keys
    gemini_api_key: str
    openai_api_key: str
    inception_api_key: str

    # Provider selection
    ai_provider: str = "gemini"  # Default

    # Language
    ai_language: str = "en"  # "en" or "cs"

    # Models
    gemini_model: str = "gemini-2.0-flash-exp"
    openai_model: str = "gpt-4o"
    inception_model: str = "mercury-coder"
```

---

### 5. GCloud Management (`src/gcloud/manager.py`)

**Class**: `GCloudManager`

**Capabilities**:
- List GCP projects
- Check Gemini API quota status
- Create new projects (auto-mode)
- Enable Gemini API
- Detect banned/quota-exceeded projects

**Safety Levels**:
- **Level 1 (Safe)**: Read-only, provides guidance
- **Level 2 (Auto)**: Requires `--auto` flag, creates resources

---

### 6. Setup Wizard (`src/setup_wizard.py`)

**Purpose**: Interactive first-time configuration

**Flow**:
1. Welcome banner
2. Language selection (EN/CS)
3. Gemini API key (required)
4. OpenAI API key (optional)
5. Mercury API key (optional)
6. Save to `.env`
7. Configuration summary

---

## 🔄 Data Flow

### Example: Hardware Diagnostics

```
User: sos --provider inception diagnose --category hardware
  │
  ▼
CLI parses command
  │
  ▼
SOSConfig loaded from .env
  ai_provider = "inception"
  ai_language = "cs"
  │
  ▼
SOSAgentClient initialized
  Creates InceptionClient(language="cs")
  │
  ▼
User prompt constructed in cli.py:
  "Perform system diagnostics: hardware
   IMPORTANT: Format as flowing text, no tables"
  │
  ▼
InceptionClient.query() called
  System prompt: "...Respond in Czech (Čeština)"
  User prompt: (diagnostic task)
  │
  ▼
Mercury API request (streaming)
  POST https://api.inceptionlabs.ai/v1/chat/completions
  │
  ▼
Stream chunks back to CLI
  │
  ▼
Rich console prints formatted output
  │
  ▼
User sees Czech diagnostic report
```

---

## 🔐 Security Architecture

### API Key Protection

**Storage**:
- `.env` file (git-ignored)
- Environment variables

**Never stored in**:
- Source code
- Git repository
- Logs

**`.gitignore` Protection**:
```gitignore
.env
.env.*
!.env.example
*.key
*.pem
*_key
*_secret
```

### GitHub Security

**Dependabot**: Weekly dependency updates
**CodeQL**: Automated code scanning
**Secret Scanning**: Detects committed secrets

---

## 📂 File Structure

```
sos-agent/
├── .github/
│   ├── dependabot.yml         # Dependency updates
│   └── workflows/
│       └── security.yml       # CodeQL, secret scan
├── docs/
│   ├── ARCHITECTURE.md        # This file
│   ├── DEVELOPMENT.md         # Dev history
│   ├── GEMINI_API_POLICIES.md # API best practices
│   └── GEMINI_API_POLICIES.cz.md
├── src/
│   ├── agent/
│   │   ├── client.py          # Unified client
│   │   ├── config.py          # Configuration
│   │   ├── gemini_client.py   # Gemini provider
│   │   ├── openai_client.py   # OpenAI provider
│   │   ├── inception_client.py # Mercury provider
│   │   └── agentapi_client.py # Claude provider
│   ├── gcloud/
│   │   └── manager.py         # GCloud operations
│   ├── cli.py                 # CLI commands
│   └── setup_wizard.py        # Setup wizard
├── .env.example               # Template config
├── .gitignore                 # Protects secrets
├── install.sh                 # Standalone installer
├── pyproject.toml             # Poetry dependencies
├── README.md                  # User documentation
└── README.cz.md               # Czech docs
```

---

## 🧪 Testing Strategy

### Unit Tests (Planned)
- Provider client mocking
- Configuration loading
- Prompt construction

### Integration Tests (Manual - 2024-12-03)
✅ Hardware diagnostics
✅ Network diagnostics
✅ Services diagnostics
✅ Language switching (EN/CS)
✅ GCloud commands

### CI/CD
- GitHub Actions on push
- CodeQL security scan
- Dependency vulnerability checks

---

## 🚀 Deployment

### Installation Methods

1. **One-Command Install**:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/milhy545/sos-agent/main/install.sh | bash
   ```

2. **Manual Install**:
   ```bash
   git clone https://github.com/milhy545/sos-agent.git
   cd sos-agent
   ./install.sh
   ```

### Install Process

1. Check Python 3.11+
2. Create `~/.sos-agent/` directory
3. Copy source files
4. Create Python venv
5. Install dependencies (Poetry)
6. Create `~/.local/bin/sos` launcher
7. Add to PATH if needed
8. Run setup wizard

---

## 📊 Performance Characteristics

### Response Times (observed)

| Provider | Category | Time | Quality |
|----------|----------|------|---------|
| Mercury | Hardware | 6s | ⭐⭐⭐⭐ |
| Mercury | Network | 7s | ⭐⭐⭐⭐ |
| Mercury | Services | 6s | ⭐⭐⭐⭐⭐ |
| Gemini | Hardware | 3s | ⭐⭐⭐⭐⭐ |
| OpenAI | Hardware | 8s | ⭐⭐⭐⭐⭐ |

**Note**: Mercury is slower than autoregressive models due to diffusion process

---

## 🔧 Extension Points

### Adding New AI Provider

1. Create `src/agent/<provider>_client.py`
2. Implement `query(prompt, context, stream)` method
3. Add to `SOSAgentClient` factory in `client.py`
4. Add config fields to `SOSConfig`
5. Update `.env.example`
6. Test with all diagnostic categories

### Adding New Language

1. Update `setup_wizard.py` language selection
2. Add language code to `SOSConfig.ai_language` options
3. Update provider clients' system prompts
4. Translate documentation (README.xx.md)
5. Test all commands

### Adding New Diagnostic Category

1. Add to `click.Choice()` in `cli.py`
2. Update prompt template with category-specific steps
3. Test output quality
4. Document in README

---

## 🐛 Known Issues & Workarounds

See [DEVELOPMENT.md](DEVELOPMENT.md) for full bug history

**Current Known Issues**:
- GCloud quota check requires `gcloud alpha` (cosmetic)
- Claude AgentAPI auth timeout (not critical)

---

## 📚 Dependencies

### Core Dependencies
- `asyncclick>=8.3.0` - Async CLI framework
- `rich>=14.2.0` - Terminal formatting
- `google-generativeai>=0.8.0` - Gemini API
- `openai>=1.59.0` - OpenAI API
- `aiohttp>=3.13.0` - Async HTTP (Mercury)
- `pydantic>=2.12.5` - Data validation
- `python-dotenv>=1.2.0` - .env loading

### Development Dependencies
- `poetry>=2.2.0` - Dependency management
- `black>=25.11.0` - Code formatting
- `ruff>=0.14.0` - Linting

---

*This document describes SOS Agent v0.1.0 architecture. Update as system evolves.*
