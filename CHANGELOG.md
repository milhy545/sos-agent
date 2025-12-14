# Changelog

All notable changes to SOS Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.2] - 2024-12-04 (Evening)

### 🎯 **GOLDEN RULES ADDED (DESATERO)**

#### Rule #1: "VŽDY SE OHLÉDNI ZA SVOJÍ PRACÍ"
"Always look back at your work before finishing" - verify results match intentions

#### Rule #2: "RESCUE AGENT MUSÍ NEJDŘÍV ZJISTIT CO ZACHRAŇUJE"
"A rescue agent must first identify what it's rescuing" - system detection is STEP ONE!

### 🐛 Critical Bug Fixes

#### Issue #4: Missing Kernel Logs - GPU Errors Invisible
**Problem**: Radeon GPU driver errors causing X11/Wayland crashes were not detected

**Root Cause**: `log_analyzer.py` only collected systemd unit logs, NOT kernel logs where GPU/driver errors live

**What AI said** (WRONG):
- Mercury: "glibc error → X11 crash"
- Gemini: "Reinstall OS"

**What was actually happening** (found by Claude):
- Radeon GPU driver timeout → X11 crash → Plasma restart loop

**Fix**:
- Added kernel log collection (`journalctl -k`) to log_analyzer.py
- Added `radeon` and `drm` keywords to driver error detection
- Kernel logs merged with system logs for complete picture

**Note**: Requires `systemd-journal` group membership or sudo for kernel log access

#### Issue #5: Warnings Ignored - GUI Crashes Hidden
**Problem**: X11/Plasma crashes logged at WARNING level were never collected

**Fix**:
- Collect BOTH errors AND warnings, then merge
- Prioritize GUI/Display errors in AI prompt
- Increased error limits from 10→20 per category

### ✨ New Features

#### System Detection (CRITICAL for rescue operations)
- Added OS detection (`/etc/os-release`, `uname -a`)
- AI now receives OS info BEFORE diagnostics
- AI uses correct package manager (apt vs dnf vs pacman)
- Prevents "wrong OS" fixes (e.g., `dnf` on Debian)

#### GUI Error Prioritization
- GUI/Display errors extracted and shown first
- Keywords: x11, wayland, plasma, kde, gnome, display, xorg
- Helps AI identify desktop environment issues faster

### 📝 Documentation Updates
- Added DESATERO (Golden Rules) to DEVELOPMENT.md
- Documented Issue #4 (kernel logs) and Issue #5 (warnings)
- Added before/after comparisons for all fixes
- Updated with real-world Radeon GPU diagnosis example

---

## [Unreleased]

## [0.2.0] - 2025-05-15

### ✨ Interactive TUI (Cyberpunk Edition)
- **Grid Menu**: Fast navigation (0-9 keys).
- **Persistent Chat**: AI Chat with session history and diagnostic context.
- **Fixer Framework**: Modular fixer interface with Dry-Run support.
- **Visuals**: Dark/Cyan/Magenta/Yellow theme.
- **Commands**: `sos menu` to launch TUI.

### ✨ CLI & TUI Upgrades (antiX-cli-cc flavor)
- `sos diagnose --issue` ukládá problém a vkládá ho do promptu.
- Nový příkaz `sos chat` (perzistentní historie, kontext z posledního `--issue`, fallback při chybějícím klíči).
- `sos fix` používá vestavěné fixery (DNS/Services/Disk) s Dry-Run + potvrzením; `--ai` volitelně vynutí AI plán.
- TUI menu rozšířeno o Diagnostics Hub, Logs viewer a neon status bar s posledním problémem; fixery mají double-confirm.
- Monitor TUI přidal start/stop kontrolu smyčky; logy/diagnostika přístupné přímo z TUI.

### 🐛 Improvements
- **Session Storage**: JSON-based session persistence in `~/.config/sos-agent/session.json`.
- **Issue Tracking**: `sos diagnose --issue <text>` saves issue context.
- **Sudo Guard**: Detects root privileges for fixers.


### Added
- End-to-end diagnostika: stub e2e test + volitelný live Mercury e2e (podmíněný env).
- Jednostránkové shrnutí diagnostiky: Top findings s logy, Quick actions vázané na nálezy (GUI/disk/auth), Resources, Security, Next steps; deduplikace logů.

### Changed
- Auto-provider fallback podle dostupných klíčů; bezpečnější defaulty (bez ZEN/portů, SSH 22).
- Timeouty a neblokující volání u providerů (Gemini/Inception), lepší hlášení při chybějících klíčích.

### Notes
- `.env` zůstává lokálně (necommitovat); live Mercury e2e vyžaduje `RUN_E2E_MERCURY=1` + `INCEPTION_API_KEY`.

---

## [0.1.1] - 2024-12-04

### 🐛 Critical Bug Fixes

#### Issue #3: AI Hallucination - No Real Data Collection
**Problem**: AI providers were generating generic advice instead of diagnosing actual system problems.

**Root Cause**: `tools/log_analyzer.py` existed but was never called by `cli.py diagnose()` function. AI received text instructions to "analyze logs" but no actual log data, causing hallucinated responses.

**Fix** (cli.py:103-183):
- Added `analyze_system_logs()` call to collect real journalctl data
- Added system resource collection (free, df, uptime)
- Modified AI prompt to include actual error logs with timestamps
- AI now analyzes real data instead of speculating

**Impact**:
- **Before**: "V souboru /var/log/syslog najdete chybové zprávy..." (generic hallucination)
- **After**: "Fatal glibc error: CPU does not support x86-64-v2" (actual error from system logs)

**See**: docs/DEVELOPMENT.md#issue-3-ai-hallucination---no-real-data-collection

### 📝 Documentation Updates
- Updated DEVELOPMENT.md with Issue #3 details and before/after comparison
- Added execution path verification lesson learned
- Updated CLAUDE.md with data collection workflow

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

## [0.2.0] - 2025-05-15

### ✨ Interactive TUI (Cyberpunk Edition)
- **Grid Menu**: Fast navigation (0-9 keys).
- **Persistent Chat**: AI Chat with session history and diagnostic context.
- **Fixer Framework**: Modular fixer interface with Dry-Run support.
- **Visuals**: Dark/Cyan/Magenta/Yellow theme.
- **Commands**: `sos menu` to launch TUI.

### 🐛 Improvements
- **Session Storage**: JSON-based session persistence in `~/.config/sos-agent/session.json`.
- **Issue Tracking**: `sos diagnose --issue <text>` saves issue context.
- **Sudo Guard**: Detects root privileges for fixers.


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
