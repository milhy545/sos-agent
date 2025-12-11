# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in SOS Agent, please report it to:

- **Email**: [Create a GitHub Security Advisory](https://github.com/milhy545/sos-agent/security/advisories/new)
- **GitHub Issues**: For non-sensitive issues, you can [open an issue](https://github.com/milhy545/sos-agent/issues)

We take security seriously and will respond to valid reports within 48 hours.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Features

### Active Protections

- **Secret Scanning**: Enabled on all commits
- **Push Protection**: Prevents accidental API key commits
- **Dependabot**: Automated security updates for dependencies
- **CodeQL Analysis**: Static security analysis on all code changes

### Best Practices Implemented

1. **API Key Management**:
   - API keys stored in `.env` files (never committed to git)
   - `.env` files properly gitignored
   - Example template provided in `.env.example`

2. **Dependency Security**:
   - Poetry for deterministic dependency resolution
   - Regular automated updates via Dependabot
   - Security-focused dependency pinning

3. **Code Quality**:
   - Automated linting (Ruff)
   - Type checking (MyPy)
   - Code formatting (Black)
   - Comprehensive test coverage (60%+)

## Known Security Considerations

### API Key Storage

SOS Agent requires API keys for AI providers (Gemini, OpenAI, Mercury, Claude). These are stored in a local `.env` file which is:

- ✅ Listed in `.gitignore` (line 4)
- ✅ Protected by secret scanning
- ✅ Never uploaded to the repository
- ✅ Only accessible on your local machine

### System Commands

SOS Agent executes system diagnostic commands (e.g., `journalctl`, `systemctl`, `sensors`). These commands:

- Run with the user's permissions (no sudo required for diagnostics)
- Are predefined in `src/tools/` modules
- Do not accept arbitrary user input for command injection

### Critical Services Protection

The agent is programmed to **NEVER** stop or disable these services:

- `sshd` - Remote access
- `NetworkManager` - Network connectivity
- `ollama` - AI inference server
- `tailscaled` - VPN connectivity

This protection is hardcoded in the agent's system prompt.

## Security Audit Trail

### Recent Security Improvements

- **2025-12-11**: Branch protection enabled on `main` branch
- **2025-12-11**: CI/CD pipeline with security checks implemented
- **2025-12-05**: Dependabot configured for GitHub Actions
- **2025-12-03**: CodeQL security scanning enabled
- **2025-12-03**: Secret scanning with push protection activated

### Dismissed CodeQL Alerts

The following CodeQL alerts have been reviewed and dismissed as false positives:

1. **`py/clear-text-logging-sensitive-data`** (setup_wizard.py:193)
   - **Reason**: Logs provider *names* only (e.g., "Gemini"), not API keys
   - **Status**: False positive - CodeQL misidentified `api_keys.keys()`

2. **`py/clear-text-storage-sensitive-data`** (setup_wizard.py:181)
   - **Reason**: Standard `.env` pattern - file is gitignored
   - **Status**: Accepted risk - `.env` is industry standard for local config

## Responsible Disclosure

We follow responsible disclosure practices:

1. Report received within 48 hours
2. Initial assessment within 1 week
3. Fix developed and tested
4. Security advisory published (if applicable)
5. Credit given to reporter (if desired)

## Additional Resources

- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Python Security Guidelines](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

**Last Updated**: 2025-12-11
**Maintained By**: milhy545
