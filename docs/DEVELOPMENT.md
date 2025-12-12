# SOS Agent - Development History & Lessons Learned

**Last Updated**: 2024-12-04 (Evening Session)

This document tracks all development decisions, bugs fixed, and lessons learned during SOS Agent development. **READ THIS BEFORE MAKING CHANGES** to avoid repeating past mistakes.

---

## 🎯 **GOLDEN RULES (DESATERO)**

### **Rule #1: "VŽDY SE OHLÉDNI ZA SVOJÍ PRACÍ"**
**"ALWAYS LOOK BACK AT YOUR WORK BEFORE FINISHING"**

Before completing ANY task:
1. **Verify** the result matches your intention
2. **Check** reality vs assumption
3. **Test** that output is human-readable (if for humans)
4. **Confirm** commands executed successfully

**Example**: Don't just send text to terminal - verify it displayed correctly!

---

### **Rule #2: "RESCUE AGENT MUSÍ NEJDŘÍV ZJISTIT CO ZACHRAŇUJE"**
**"A RESCUE AGENT MUST FIRST IDENTIFY WHAT IT'S RESCUING"**

**System detection is STEP ONE, not an afterthought!**

A rescue agent diagnosing a system without knowing:
- What OS (Debian vs Red Hat vs Arch)
- What hardware (CPU, GPU)
- What kernel version

**...is like a mechanic trying to fix a car in a kitchen.**

**Implementation**:
```python
# STEP 1: Detect system (ALWAYS FIRST!)
os_info = await get_os_release()  # /etc/os-release
cpu_info = await get_cpu_info()   # lscpu
kernel = await get_kernel_version()  # uname -a

# STEP 2: Then diagnose problems
# STEP 3: Provide fixes using CORRECT package manager for detected OS
```

**Bad example**: AI suggests `dnf` commands on Debian system
**Good example**: AI detects Debian → uses `apt` commands

---

## 🚨 CRITICAL LESSONS LEARNED

### **Issue #3: AI Hallucination - No Real Data Collection** ⚠️ **FIXED**
**Date**: 2024-12-04
**Discovered By**: User testing session
**Problem**: AI providers (Gemini, Mercury, OpenAI) were "vaříc z vody" (making things up) instead of analyzing actual system data
**Root Cause**:
- `tools/log_analyzer.py` existed with full journalctl parsing capability
- BUT `cli.py` diagnose() function never called it!
- AI was only receiving **text instructions** to "analyze logs", not actual log data
- Result: AI providers hallucinated problems based on general knowledge instead of diagnosing real issues

**Evidence**:
```python
# OLD CODE (cli.py:102-123) - NO DATA COLLECTION
task = f"""
Perform comprehensive system diagnostics focusing on: {category}

Steps:
1. Analyze system logs for errors in the last 24 hours
2. Check system resource usage (CPU, RAM, disk space)
...
"""
# AI received instructions but NO ACTUAL DATA!
```

**Working Solution** (cli.py:103-183):
```python
# NEW CODE - COLLECT REAL DATA FIRST
console.print("[dim]Collecting system logs...[/dim]")
log_data = await analyze_system_logs(time_range="24h", severity="error")

console.print("[dim]Checking system resources...[/dim]")
# Collect free -h, df -h, uptime output

# Then send ACTUAL DATA to AI
task = f"""
=== SYSTEM LOGS (Last 24h) ===
Hardware Errors: {len(log_data['hardware_errors'])} found

Hardware Error Details:
{actual_error_list_from_logs}

=== SYSTEM RESOURCES ===
{actual_free_df_uptime_output}

Based on the ACTUAL DATA above (not speculation):
...
"""
```

**Before/After Comparison**:
| Before | After |
|--------|-------|
| "V souboru /var/log/syslog najdete chybové zprávy..." (hallucination) | "Fatal glibc error: CPU does not support x86-64-v2" (real error from logs) |
| Generic advice about "disk I/O latency" | Specific tracker-extract-3.service failures with timestamps |
| Tipování problémů | Analýza skutečných chyb |

**Lesson**: **VERIFY THAT DATA COLLECTION TOOLS ARE ACTUALLY CALLED!** Having the code isn't enough - check the execution path.

**Note**: This bug existed from initial release (2024-12-03) but wasn't noticed because AI responses *seemed* reasonable - they were just generic advice, not system-specific diagnostics.

---

### **Issue #4: Missing Kernel Logs - GPU Errors Invisible** ⚠️ **FIXED**
**Date**: 2024-12-04 (Evening)
**Discovered By**: Claude Code comparison with Mercury/Gemini output

**Problem**: Radeon GPU driver errors causing X11/Wayland crashes were NOT detected by AI providers

**Root Cause**:
1. `log_analyzer.py` only ran `journalctl` for system logs
2. **Kernel logs** (`journalctl -k`) were never collected
3. GPU/driver errors (DRM, Radeon) live in kernel logs, not systemd units
4. Result: AI providers blamed **glibc** instead of **Radeon driver**

**Evidence**:
```bash
# What was ACTUALLY causing X11 crashes:
journalctl -k -p err | grep radeon
[drm:radeon_ib_ring_tests] *ERROR* radeon: failed testing IB on GFX ring (-110)
[drm:uvd_v1_0_ib_test] *ERROR* radeon: fence wait timed out

# But log_analyzer NEVER saw these because it didn't check kernel logs!
```

**What Mercury/Gemini said** (WRONG):
- Mercury: "glibc error → X11 crash" (indirect correlation, not root cause)
- Gemini: "Reinstall OS due to CPU incompatibility" (nuclear option, doesn't fix GPU)

**What Claude found** (CORRECT):
- Radeon GPU driver timeout → X11 server crash → Plasma restart loop

**Fix** (log_analyzer.py:49-82):
```python
# OLD: Only system logs
cmd = f"journalctl --since '{time_range} ago' -p {severity} --no-pager -o json"

# NEW: BOTH system AND kernel logs
cmd_system = f"journalctl --since '{time_range} ago' -p {severity} --no-pager -o json"
cmd_kernel = f"journalctl -k --since '{time_range} ago' -p {severity} --no-pager -o json"

# Merge outputs so AI sees BOTH
stdout = stdout_system + b"\n" + stdout_kernel
```

**Also added keywords** (log_analyzer.py:114-124):
```python
driver_keywords = [
    "radeon",  # AMD legacy GPUs - CRITICAL for old hardware!
    "drm",     # Direct Rendering Manager (GPU subsystem)
    # ...existing keywords
]
```

**Permissions issue**: Kernel logs require `systemd-journal` group membership or sudo
**Solution**: `usermod -a -G systemd-journal <user>` (requires re-login)

**Lesson**: **GPU/driver problems are in KERNEL logs, not systemd unit logs!** Always collect both.

---

### **Issue #5: Warnings Ignored - GUI Crashes Hidden** ⚠️ **FIXED**
**Date**: 2024-12-04
**Problem**: X11/Plasma crashes were logged at WARNING level, not ERROR level, so they were missed

**Evidence**:
```bash
# These were at WARNING level, not collected:
[2025-12-03 15:59:21] The X11 connection broke (error 1). Did the X11 server die?
[2025-12-03 15:59:22] plasma-kded.service: Failed with result 'exit-code'
```

**Fix** (cli.py:104-117):
```python
# OLD: Only errors
log_data = await analyze_system_logs(time_range="24h", severity="error")

# NEW: Errors + Warnings, then merge
log_data_errors = await analyze_system_logs(time_range="24h", severity="error")
log_data_warnings = await analyze_system_logs(time_range="24h", severity="warning")

# Combine both
log_data = {
    'service_errors': errors['service_errors'] + warnings['service_errors'],
    # ...
}
```

**Also**: Prioritize GUI errors in prompt (cli.py:186-193) so AI sees them first!

**Lesson**: **Critical problems can be logged as warnings, not just errors!** Collect both.

---

### Mercury (Inception Labs) Formatting Issues
**Date**: 2024-12-03
**Problem**: Mercury generates narrow ASCII tables (~70 chars) even in fullscreen terminals
**Root Cause**: Mercury is a **diffusion LLM** (not autoregressive like GPT). It generates entire text blocks at once with pre-formatted layouts
**Attempted Solutions That FAILED**:
- ❌ Changing system prompt alone ("format for wide terminals")
- ❌ Post-processing with `replace('\n', ' ')` (breaks paragraph structure)
- ❌ API parameters (Mercury is OpenAI-compatible, no special formatting params)

**Working Solution**:
```python
# In user prompt (NOT system prompt):
"IMPORTANT:
- Do NOT repeat this prompt or steps in your response
- Start directly with diagnostic results
- Format as natural flowing text paragraphs, NOT tables
- Use bullet points and numbered lists instead of ASCII tables"
```

**Why It Works**: User prompt has higher priority than system prompt in diffusion models.

**Lesson**: **ALWAYS CHECK OFFICIAL API DOCUMENTATION FIRST** before guessing solutions!

---

## 📋 Development Timeline

### 2024-12-03: Initial Release

#### Phase 1: Multi-Model Support
- ✅ Added Gemini, OpenAI, Mercury support
- ✅ Unified client interface (SOSAgentClient)
- ✅ Provider selection via `--provider` flag
- ❌ **Issue**: Gemini API quota exceeded (banned project)
- ✅ **Fix**: Added fallback to Mercury, GCloud management

#### Phase 2: Mercury Integration
- ✅ Inception Labs Mercury client created
- ❌ **Issue #1**: Narrow ASCII tables in output
- ❌ **Issue #2**: Prompt repetition in responses
- ✅ **Fix #1**: Explicit "no tables" instruction in user prompt
- ✅ **Fix #2**: "Do NOT repeat this prompt" instruction

#### Phase 3: Language Support
- ✅ Setup wizard language selection (EN/CS)
- ✅ `SOS_AI_LANGUAGE` config parameter
- ✅ Dynamic system prompts based on language
- ✅ Tested both languages - working perfectly

#### Phase 4: GCloud Management
- ✅ Level 1 (Safe): Check quota, list projects
- ✅ Level 2 (Auto): Create projects, enable API
- ⚠️ **Known Issue**: `gcloud services quota` requires alpha track
- ✅ **Workaround**: Graceful fallback with warning

#### Phase 5: Security & CI/CD
- ✅ Comprehensive `.gitignore` (protects API keys)
- ✅ Dependabot configuration
- ✅ CodeQL security scanning
- ✅ GitHub Actions workflows
- ✅ Claude GitHub App integration

---

## 🐛 Bug Fixes Log

### Bug #1: `.env` Not Loaded by `sos` Command
**Date**: 2024-12-03
**Symptom**: `sos --provider inception` fails with "INCEPTION_API_KEY not found"
**Root Cause**: Launcher script `~/.local/bin/sos` didn't source `.env`
**Fix**:
```bash
# Added to launcher script:
if [ -f "$INSTALL_DIR/.env" ]; then
    set -a
    source "$INSTALL_DIR/.env"
    set +a
fi
```
**Files Modified**: `install.sh` (line 91-95)

### Bug #2: Mercury Repeats User Prompt
**Date**: 2024-12-03
**Symptom**: Response starts with "Perform comprehensive system diagnostics focusing on..."
**Root Cause**: Diffusion models tend to echo prompts
**Fix**: Added explicit instruction "Do NOT repeat this prompt"
**Files Modified**: `src/cli.py` (line 117-122)

### Bug #3: GitHub Email Privacy Error
**Date**: 2024-12-03
**Symptom**: `git push` failed with "GH007: Your push would publish a private email"
**Fix**:
```bash
git config user.email "milhy545@users.noreply.github.com"
git commit --amend --reset-author --no-edit
```

---

## 🏗️ Architecture Decisions

### Why Multiple AI Providers?
- **Gemini**: Fast, free tier, but quota limits
- **OpenAI**: Powerful but expensive
- **Mercury**: Fast diffusion model, good for diagnostics
- **Claude**: OAuth via AgentAPI (experimental, has timeout issues)

**Decision**: Support all 4 with fallback strategy

### Why Standalone Installer?
- **Problem**: Users don't want to manually install Poetry, dependencies
- **Solution**: `install.sh` handles everything automatically
- **Trade-off**: Larger installation, but better UX

### Why Bilingual (EN/CS)?
- **User Request**: Czech user wants output in Czech
- **Implementation**: `SOS_AI_LANGUAGE` env var + dynamic system prompts
- **Benefit**: Easy to add more languages later

---

## 🔧 Configuration Files

### `.env` Structure
```bash
# API Keys (NEVER commit!)
GEMINI_API_KEY=xxx
OPENAI_API_KEY=xxx
INCEPTION_API_KEY=xxx

# Agent Config
SOS_AI_LANGUAGE=cs  # or "en"
SOS_LOG_LEVEL=INFO
SOS_EMERGENCY_MODE=false
```

### Important: `.gitignore` Protections
```gitignore
.env
.env.*
!.env.example
*.key
*.pem
*_key
*_secret
```
**Never remove these!** They protect API keys from being committed.

---

## 📊 Testing Results (2024-12-03)

All tests passed with Mercury provider:

| Test | Result | Notes |
|------|--------|-------|
| Hardware diagnostics | ✅ | Detects SSD/driver issues, 6 prioritized fixes |
| Network diagnostics | ✅ | Detects eth0/DHCP issues, 5 fixes |
| Services diagnostics | ✅ | Status of all services, 6 recommendations |
| Language (EN) | ✅ | English output working |
| Language (CS) | ✅ | Czech output working |
| GCloud check | ✅ | Detects quota/banned projects |

---

## 🚀 Future Improvements

### Planned Features
- [ ] Perplexity AI research integration
- [ ] OpenAI Codex code fixes
- [ ] GitHub issue search
- [ ] Computer vision diagnostics (screenshot analysis)

### Known Limitations
- Claude AgentAPI has auth timeout issues (not critical)
- GCloud quota check requires alpha track (cosmetic issue)
- Mercury sometimes generates verbose output (acceptable)

---

## 📚 References

### Official Documentation
- [Mercury API](https://www.inceptionlabs.ai/blog/introducing-mercury)
- [Gemini API Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

### Internal Documentation
- [GEMINI_API_POLICIES.md](GEMINI_API_POLICIES.md) - Rate limits, best practices
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

---

## 🤝 Contributing Guidelines for AI Agents

**Before making changes:**

1. ✅ **Read this file** to understand past issues
2. ✅ **Check official API docs** before guessing solutions
3. ✅ **Test all changes** with multiple scenarios
4. ✅ **Update this document** with new lessons learned
5. ✅ **Commit messages** should reference this doc

**When fixing bugs:**
- Document the root cause (not just the symptom)
- Explain why the fix works
- Add to "Bug Fixes Log" section above

**When adding features:**
- Update ARCHITECTURE.md
- Add usage examples to README.md
- Translate docs to Czech (README.cz.md)

---

*This document is maintained by AI agents working on SOS Agent. Keep it updated!*

### Phase 6: TUI Implementation (Cyberpunk Edition)
**Date**: 2025-05-15 (Current)
**Features**:
- Textual-based TUI with "AntiX" style grid menu.
- Persistent Session Storage (JSON).
- Chat interface integration.
- Fixer framework with Dry-Run support.

**Architecture**:
- `src/tui/` contains all UI logic.
- `src/session/` handles persistence.
- `src/tools/fixers/` implements modular fixers.

**Lessons Learned**:
- **AsyncClick vs Textual**: Mixing async click commands with Textual's event loop requires care. Textual runs its own loop.
- **Sudo in TUI**: Running sudo commands inside TUI is complex. We opted for checking root status and advising user to restart with sudo if needed, to preserve UI integrity.
