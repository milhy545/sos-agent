# 🆘 SOS Agent - Installation Guide

## Quick Install (One Command)

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/sos-agent/main/install.sh | bash
```

Or download and run manually:

```bash
git clone https://github.com/YOUR_USERNAME/sos-agent.git
cd sos-agent
./install.sh
```

## What the Installer Does

1. ✅ Checks Python 3.11+ is installed
2. ✅ Creates `~/.sos-agent/` directory
3. ✅ Sets up isolated Python virtual environment
4. ✅ Installs all dependencies automatically
5. ✅ Creates global `sos` command
6. ✅ Adds `~/.local/bin` to PATH if needed
7. ✅ Runs setup wizard for API keys

## After Installation

Just type from anywhere:

```bash
sos
```

## First Time Setup

Configure your AI provider (Gemini, OpenAI, or Inception Labs):

```bash
sos setup
```

The wizard will ask for API keys. Get them here:
- **Gemini**: https://aistudio.google.com/app/apikey (Free tier available!)
- **OpenAI**: https://platform.openai.com/api-keys
- **Inception Labs**: https://inceptionlabs.ai

## Usage Examples

```bash
# Quick hardware check
sos diagnose --category hardware

# Check network issues
sos diagnose --category network

# Full system diagnostics
sos diagnose --category all

# Show all commands
sos --help
```

## Requirements

- **Python 3.11+** (check with `python3 --version`)
- **Linux** (Alpine, Debian, Ubuntu, Arch, etc.)
- **Internet connection** (for API calls)

## Uninstall

```bash
rm -rf ~/.sos-agent
rm ~/.local/bin/sos
```

## Troubleshooting

### "sos: command not found"

Reload your shell:

```bash
source ~/.zshrc    # for ZSH
source ~/.bashrc   # for Bash
```

Or restart your terminal.

### "Python 3.11+ required"

Install Python 3.11+:

**Alpine Linux:**
```bash
apk add python3 py3-pip
```

**Debian/Ubuntu:**
```bash
apt install python3 python3-pip python3-venv
```

**Arch Linux:**
```bash
pacman -S python python-pip
```

### "API key not found"

Run the setup wizard:

```bash
sos setup
```

Or manually create `~/.sos-agent/.env`:

```bash
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
INCEPTION_API_KEY=your_key_here
```

## Support

- 📖 Documentation: [README.md](README.md)
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
