# Repository Rules & Standards

**Repository**: [milhy545/sos-agent](https://github.com/milhy545/sos-agent)
**Last Updated**: 2024-12-03

---

## 📋 Overview

This document describes all repository rules, branch protection policies, and development standards for SOS Agent.

---

## 🛡️ Branch Protection Rules

### Master Branch Protection

The `master` branch is protected with the following rules:

#### ✅ Required Status Checks
- **CodeQL Analysis** must pass before merging
- Strict mode: Branches must be up-to-date before merging

#### ❌ Blocked Actions
- **Force pushes**: Disabled (prevents rewriting history)
- **Branch deletion**: Disabled (master branch cannot be deleted)
- **Direct commits**: Allowed for repo owner (no PR required for solo project)

#### 💬 Conversation Resolution
- **Required**: All PR conversations must be resolved before merging
- Ensures all feedback is addressed

#### 🔓 Admin Enforcement
- **Disabled**: Repository admins can bypass rules when necessary
- Useful for hotfixes and emergency patches

---

## 👥 Code Ownership (CODEOWNERS)

Automatic review requests are configured via `.github/CODEOWNERS`:

| Pattern | Owner | Reason |
|---------|-------|--------|
| `*` | @milhy545 | Default owner for all files |
| `/src/agent/` | @milhy545 | Core agent code |
| `.env.example` | @milhy545 | Security-critical template |
| `.gitignore` | @milhy545 | Prevents API key leaks |
| `/.github/` | @milhy545 | CI/CD and workflows |
| `/docs/` | @milhy545 | Documentation |
| `*.md` | @milhy545 | All markdown files |
| `pyproject.toml` | @milhy545 | Dependencies |
| `install.sh` | @milhy545 | Installer script |

---

## 🔒 Security Standards

### Secret Protection

**Never commit**:
- `.env` files (use `.env.example` instead)
- API keys (Gemini, OpenAI, Inception, Claude)
- SSH keys or credentials
- Any files matching `.gitignore` patterns

**Automated Protection**:
- Dependabot: Weekly dependency updates
- CodeQL: Code security scanning on push
- Secret Scanning: GitHub's automatic secret detection
- TruffleHog: Additional secret scanning (planned)

### Security-Critical Files

These files require extra review:
- `.env.example` - Template for API keys
- `.gitignore` - Protects secrets from commit
- `install.sh` - Runs with user privileges
- `.github/workflows/security.yml` - Security automation

---

## 🔄 Workflow Requirements

### CI/CD Checks

All commits to `master` trigger:

1. **CodeQL Analysis** (required)
   - Language: Python
   - Scans for security vulnerabilities
   - Must pass before merge

2. **Dependency Scanning** (automated)
   - Dependabot checks weekly
   - Auto-creates PRs for updates

3. **Secret Scanning** (automated)
   - GitHub scans all commits
   - Alerts on detected secrets

### Pull Request Guidelines

Even though direct commits are allowed, PRs are recommended for:
- Major feature additions
- Breaking changes
- Dependency updates
- Security-sensitive modifications

**PR Checklist**:
- [ ] All CI checks pass
- [ ] Documentation updated (both EN + CZ)
- [ ] CHANGELOG.md updated
- [ ] No secrets in diff
- [ ] All conversations resolved

---

## 📦 Dependency Management

### Poetry Configuration

Dependencies are managed via `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.11"
asyncclick = "^8.3.0"
rich = "^14.2.0"
google-generativeai = "^0.8.0"
openai = "^1.59.0"
aiohttp = "^3.13.0"
```

### Update Policy

- **Minor/Patch updates**: Auto-approved by Dependabot
- **Major updates**: Manual review required
- **Security updates**: Immediate application

---

## 🌍 Documentation Standards

### Bilingual Requirement

**All documentation must have both versions**:
- `README.md` + `README.cz.md`
- `GEMINI_API_POLICIES.md` + `GEMINI_API_POLICIES.cz.md`
- Future docs follow same pattern

### Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| `README.md` | User guide | End users |
| `docs/ARCHITECTURE.md` | System design | Developers |
| `docs/DEVELOPMENT.md` | Dev history | AI agents |
| `docs/GEMINI_API_POLICIES.md` | API best practices | All |
| `CHANGELOG.md` | Version history | All |
| `INSTALL.md` | Installation guide | New users |

---

## 🤖 AI Agent Collaboration

### Before Making Changes

**AI agents MUST**:
1. ✅ Read `docs/DEVELOPMENT.md` first
2. ✅ Check `docs/ARCHITECTURE.md` for design
3. ✅ Review `CHANGELOG.md` for history
4. ✅ Consult official API docs before guessing

### Critical Rules

- ❌ **Never re-fix solved bugs** (check DEVELOPMENT.md)
- ❌ **Never commit API keys** (use .env.example)
- ❌ **Never break bilingual docs** (update both EN + CZ)
- ✅ **Always document lessons learned**
- ✅ **Always test before commit**
- ✅ **Always update CHANGELOG.md**

### Golden Rule

**"ALWAYS CHECK DOCUMENTATION FIRST, THEN CODE"**

Not the other way around! Read:
1. `docs/DEVELOPMENT.md`
2. `docs/ARCHITECTURE.md`
3. Official API docs
4. Then start coding

---

## 🚀 Release Process

### Version Numbering

Follows [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., `0.1.0`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. Update `CHANGELOG.md` with version number
2. Update version in `pyproject.toml`
3. Test all diagnostic categories
4. Test both languages (EN/CS)
5. Create git tag: `git tag v0.1.0`
6. Push with tags: `git push --tags`
7. Create GitHub release

---

## 🔧 Emergency Procedures

### Hotfix Process

For critical security issues:

1. **Create hotfix branch**: `git checkout -b hotfix/critical-issue`
2. **Apply minimal fix**
3. **Test thoroughly**
4. **Skip CI if necessary** (admin bypass available)
5. **Merge directly to master**
6. **Document in DEVELOPMENT.md**

### Reverting Changes

If a commit breaks production:

```bash
# Revert specific commit
git revert <commit-hash>

# Force push if needed (admins only)
git push --force-with-lease origin master
```

---

## 📊 Repository Statistics

- **License**: MIT
- **Language**: Python 3.11+
- **Primary Branch**: `master`
- **CI/CD**: GitHub Actions
- **Security Scanning**: CodeQL + Dependabot
- **Documentation**: Bilingual (EN + CZ)

---

## 🔗 Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development history
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines (planned)

---

*This document defines repository standards for SOS Agent. Update when policies change.*
