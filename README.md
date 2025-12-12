# 🆘 SOS Agent - System Rescue & Optimization

**AI-Powered System Administrator Agent for Emergency Diagnostics & Recovery**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency-Poetry-blue)](https://python-poetry.org/)

SOS Agent is an intelligent system rescue tool powered by multiple AI models. It provides emergency diagnostics, performance optimization, and recovery assistance for Linux systems.

## ✨ Features

- 🤖 **Multi-Model AI Support**
  - Google Gemini (default, fast & free tier)
  - OpenAI GPT-4o (powerful reasoning)
  - Inception Labs Mercury (specialized for coding)
  - Claude via AgentAPI (OAuth, experimental)

- 🔧 **Comprehensive System Diagnostics**
  - Hardware health monitoring
  - Service status checks
  - Log analysis & error detection
  - Performance metrics

- 🛡️ **Safety First**
  - Protected critical services (sshd, NetworkManager)
  - Emergency mode for urgent situations
  - Automatic backup recommendations

- 📊 **Interactive TUI (Text User Interface)**
  - Cyberpunk-themed visual interface
  - Persistent Chat with context
  - Guided Fixer system with Dry-Run safety
  - Real-time Dashboards

## 🚀 Quick Start

### One-Command Installation

```bash
# Download and run installer
curl -fsSL https://raw.githubusercontent.com/milhy545/sos-agent/main/install.sh | bash
```

Or manual installation:

```bash
git clone https://github.com/milhy545/sos-agent.git
cd sos-agent
./install.sh
```

**That's it!** The installer handles everything automatically:
- ✅ Checks Python 3.11+
- ✅ Creates isolated environment
- ✅ Installs dependencies
- ✅ Creates global `sos` command
- ✅ Runs setup wizard

### First Run

Configure your AI provider:

```bash
sos setup
```

Then start diagnosing:

```bash
sos diagnose --category hardware
```

📖 **Detailed installation guide**: [INSTALL.md](INSTALL.md) | [INSTALL.cz.md](INSTALL.cz.md)

## 📖 Usage

### Available Commands

```bash
sos menu                        # 🖥️ Launch Interactive TUI (Recommended)
sos diagnose --category <type>  # Run diagnostics (CLI)
sos diagnose --issue "problem"  # Run diagnostics with specific issue
sos fix                         # Interactive fix mode (CLI)
sos emergency                   # Emergency fallback diagnostics
sos monitor                     # Real-time system monitoring
sos check-boot                  # Boot/GRUB diagnostics
sos optimize-apps               # Clean & optimize applications
sos setup                       # Configure API keys
```

### 🖥️ Interactive TUI

Launch the full interface with:

```bash
sos menu
```

Features:
- **Grid Menu**: Fast navigation (0-9 keys).
- **Chat**: Persistent AI chat with system context.
- **Fixers**: Guided fix interface with Dry-Run support.
- **Monitor**: Real-time dashboards.
- **Cyberpunk Theme**: High contrast for emergency visibility.

### Diagnostic Categories

- `hardware` - CPU, RAM, disk, sensors
- `network` - Connectivity, interfaces, firewall
- `services` - Systemd services status
- `security` - Security audits & vulnerabilities
- `performance` - CPU/RAM/disk performance analysis

## 🔑 Configuration

### API Keys

Get your API keys:

- **Gemini**: https://aistudio.google.com/app/apikey (Recommended ⭐)
- **OpenAI**: https://platform.openai.com/api-keys
- **Inception Labs**: https://inceptionlabs.ai

Add to `.env`:

```bash
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # Optional
INCEPTION_API_KEY=your_key_here  # Optional
```

### Switch AI Provider

Edit `config/default.yaml`:

```yaml
ai_provider: gemini  # or "openai", "inception"
gemini_model: gemini-2.0-flash-exp
openai_model: gpt-4o
inception_model: mercury-coder
```

## 🛠️ Development

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black src/
poetry run ruff check src/

# Type checking
poetry run mypy src/
```

## 🌍 Localization

Documentation is available in:
- 🇬🇧 English - `README.md`
- 🇨🇿 Czech - `README.cz.md`

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design & components
- [Multi-Model Setup](docs/MULTIMODEL_SETUP.md) - AI provider configuration
- [Debug History](docs/DEBUG_HISTORY.md) - Known issues & fixes
- [Contributing](CONTRIBUTING.md) - How to contribute

## ⚠️ Safety

SOS Agent protects critical services:
- **Never disabled**: sshd, NetworkManager, ollama, tailscaled
- **Emergency mode**: Read-only diagnostics only
- **Backup first**: Always recommends backups before changes

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- 🐛 Issues: https://github.com/milhy545/sos-agent/issues
- 💬 Discussions: https://github.com/milhy545/sos-agent/discussions
- 📧 Email: [milhy545@gmail.com](mailto:milhy545@gmail.com)

---

**Built with ❤️ for system administrators who need AI assistance in emergencies**
