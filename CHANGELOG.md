# Changelog

All notable changes to SOS Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2024-12-03

### 🎉 Initial Release

First public release of SOS Agent - AI-Powered System Rescue & Diagnostics Agent.

### ✨ Added

#### Multi-Model AI Support
- Google Gemini integration (`gemini-2.0-flash-exp`)
- OpenAI GPT-4o integration
- Inception Labs Mercury integration (`mercury-coder`)
- Claude AgentAPI integration (experimental)
- Provider selection via `--provider` flag

#### Diagnostics Features
- Hardware diagnostics (logs, drivers, disk health)
- Network diagnostics (connectivity, DHCP, interfaces)
- Services diagnostics (critical service status)
- Comprehensive system scans (`--category all`)

#### GCloud Management
- Level 1 (Safe): Check quota, list projects, show status
- Level 2 (Auto): Create projects, enable APIs (`--auto` flag)
- Quota monitoring and ban detection
- Automatic fallback recommendations

#### Internationalization
- Language selection in setup wizard
- English (EN) and Czech (CS) support
- Dynamic AI response language (`SOS_AI_LANGUAGE`)

#### Installation & Setup
- Standalone installer (`install.sh`)
- Interactive setup wizard (`sos setup`)
- Global `sos` command
- Automatic PATH configuration
- `.env` template with examples

#### Security
- Comprehensive `.gitignore` (protects API keys)
- Dependabot for dependency updates
- CodeQL security scanning
- Secret scanning with TruffleHog
- GitHub Actions CI/CD

#### Documentation
- README.md (English)
- README.cz.md (Czech)
- INSTALL.md (installation guide)
- GEMINI_API_POLICIES.md (rate limits, best practices)
- ARCHITECTURE.md (system design)
- DEVELOPMENT.md (development history, lessons learned)

### 🐛 Fixed

#### Mercury Formatting Issues
- Fixed narrow ASCII table output (was ~70 chars)
- Fixed prompt repetition in responses
- Added explicit "no tables" instruction
- Natural flowing text format

#### Installation Issues
- Fixed `.env` not loading in `sos` launcher script
- Fixed PATH not updated automatically
- Fixed missing `set -a` for environment sourcing

#### Git Issues
- Fixed GitHub email privacy error (GH007)
- Configured `user.email` to use noreply address

### 🔧 Changed

- Default provider changed from Claude to Gemini (free tier)
- Setup wizard now asks for language preference first
- Diagnostic prompts optimized for diffusion models (Mercury)

### ⚠️ Known Issues

- Claude AgentAPI has auth timeout issues (non-critical)
- GCloud quota check requires `gcloud alpha` (cosmetic)
- Gemini free tier has strict rate limits (5 RPM / 25 RPD)

### 📊 Testing

All diagnostic categories tested successfully:
- ✅ Hardware diagnostics
- ✅ Network diagnostics
- ✅ Services diagnostics
- ✅ Language switching (EN/CS)
- ✅ GCloud commands

---

## [Unreleased]

### 🚀 Planned Features

#### AI Integrations
- [ ] Perplexity AI research integration
- [ ] OpenAI Codex code fixes
- [ ] GitHub issue search integration
- [ ] Computer vision diagnostics (screenshot analysis)

#### Enhanced Diagnostics
- [ ] Boot/GRUB diagnostics
- [ ] Application optimization
- [ ] Performance monitoring
- [ ] Emergency recovery mode

#### Improvements
- [ ] Unit tests
- [ ] CI/CD automation
- [ ] More languages (DE, FR, ES)
- [ ] Web dashboard

---

## Version History

- **0.1.0** (2024-12-03) - Initial release

---

## How to Update

To update to the latest version:

```bash
cd ~/.sos-agent
git pull origin master
poetry install --no-interaction
```

Or reinstall:

```bash
curl -fsSL https://raw.githubusercontent.com/milhy545/sos-agent/main/install.sh | bash
```

---

*For detailed development history, see [DEVELOPMENT.md](docs/DEVELOPMENT.md)*
