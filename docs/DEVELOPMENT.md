# SOS Agent - Development History & Lessons Learned

**Last Updated**: 2024-12-03

This document tracks all development decisions, bugs fixed, and lessons learned during SOS Agent development. **READ THIS BEFORE MAKING CHANGES** to avoid repeating past mistakes.

---

## 🚨 CRITICAL LESSONS LEARNED

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
