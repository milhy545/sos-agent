# Google Gemini API - Policies & Best Practices

**Last Updated**: 2024-12-03

## 📊 Free Tier Rate Limits

| Metric | Free Tier Limit |
|--------|-----------------|
| **RPM** (Requests Per Minute) | 5 RPM |
| **RPD** (Requests Per Day) | 25 RPD |
| **Effective Rate** | 1 request every 12 seconds |
| **Context Window** | 1M tokens (full access) |
| **Reset** | Daily quota resets at midnight PT |

⚠️ **Important**: Free tier is designed for **testing/prototyping**, NOT production!

## 🚫 Common Ban Reasons

### Content Violations
- ❌ **Hate speech, harassment, bullying**
- ❌ **Sexually explicit or graphic content**
- ❌ **Violence, dangerous instructions**
- ❌ **Misinformation, illegal activity**
- ❌ **Intellectual property infringement**

### Technical Violations
- ❌ **Bypassing safety filters** (jailbreaks, prefills)
- ❌ **Automated abuse** (high-frequency scraping)
- ❌ **Quota manipulation** (multiple accounts)

### Enforcement
- 🤖 **Automated scanning** of all API requests
- 👁️ **Manual review** for flagged projects
- ⚠️ **Temporary suspension** → ❌ **Permanent ban**

## ✅ Best Practices for SOS Agent

### 1. Request Optimization
```python
# ✅ GOOD: Batch multiple checks into one request
prompt = """
Check system logs, resource usage, and service status.
Provide comprehensive diagnostics.
"""

# ❌ BAD: Multiple sequential requests
check_logs()  # Request 1
check_cpu()   # Request 2
check_disk()  # Request 3
```

### 2. Rate Limiting Strategy
```python
# Exponential backoff on 429 errors
import time

for attempt in range(3):
    try:
        response = gemini_api.generate(prompt)
        break
    except RateLimitError:
        wait_time = (2 ** attempt) * 60  # 1min, 2min, 4min
        time.sleep(wait_time)
```

### 3. Model Selection
- **Gemini Flash** (default): Fast, cheap, good for logs/diagnostics
- **Gemini Pro**: Only for complex reasoning/security audits
- **Fallback**: Switch to Mercury/OpenAI if quota exceeded

### 4. Safe Prompts for System Diagnostics
```bash
# ✅ SAFE: Technical system diagnostics
"Analyze /var/log/syslog for hardware errors"
"Check systemd service status and provide recommendations"
"Diagnose network connectivity issues"

# ❌ AVOID: Could trigger filters
"How to bypass firewall restrictions"  # Security violation
"Generate harmful payloads"             # Dangerous content
```

### 5. API Key Security
- ✅ Store in `.env` file (git-ignored)
- ✅ Use Google Cloud Secret Manager in production
- ❌ Never hardcode in source code
- ❌ Never commit to GitHub

### 6. Error Handling
```python
if error.code == 429:  # Rate limit
    # Wait and retry OR switch provider
    use_fallback_provider("mercury")

elif error.code == 403:  # Quota exceeded / banned
    # Create new GCP project (sos gcloud setup --auto)
    logger.warning("Gemini quota exceeded, switching to Mercury")
```

## 🔄 Recovery from Quota Exceeded

### Option 1: Wait
- Quotas reset at **midnight Pacific Time**
- Free tier: 25 requests/day limit

### Option 2: Switch Provider
```bash
sos --provider mercury diagnose    # Use Mercury (no quota)
sos --provider openai diagnose     # Use OpenAI (separate quota)
```

### Option 3: Create New Project
```bash
sos gcloud setup --auto            # Auto-create new GCP project
```

⚠️ **Warning**: Don't abuse project creation - Google tracks account patterns!

## 📈 Upgrading to Paid Tier

To avoid quota issues in production:

1. Enable **Cloud Billing** in GCP Console
2. Upgrade to **Pay-as-you-go** tier:
   - RPM: 1000+ (vs 5 free)
   - TPM: 4M+ (vs limited)
   - No daily cap

3. Cost: ~$0.00025/1K tokens (Flash) or $0.00125/1K (Pro)

## 🛡️ How SOS Agent Stays Compliant

1. **System diagnostics only** - no user-generated harmful content
2. **Rate limiting** - respects 5 RPM / 25 RPD limits
3. **Exponential backoff** - handles 429 errors gracefully
4. **Multi-provider** - fallback to Mercury/OpenAI
5. **Safe prompts** - technical queries only, no filter bypass
6. **API key security** - environment variables, never committed

## 📚 Official Resources

- [Rate Limits Documentation](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Usage Policies](https://ai.google.dev/gemini-api/docs/usage-policies)
- [Terms of Service](https://policies.google.com/terms)
- [Generative AI Prohibited Use Policy](https://policies.google.com/terms/generative-ai/use-policy)

## 🚨 If You Get Banned

1. **Check violation**: Review API logs for flagged content
2. **Appeal process**: [GCP Support](https://console.cloud.google.com/support)
3. **Alternative**: Use Mercury/OpenAI (no Google restrictions)
4. **Prevention**: Read policies, test prompts carefully

---

**TL;DR for SOS Agent Users**:
- Free tier: 5 requests/min, 25/day
- Don't bypass filters or spam requests
- Use `--provider mercury` as fallback
- `sos gcloud setup --auto` creates new project if banned
