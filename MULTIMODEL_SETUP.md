# SOS Agent - Multi-Model Setup Guide

SOS Agent teď podporuje 3 AI providery:
1. **Gemini** (default) - Google Gemini API
2. **OpenAI** - OpenAI API  
3. **Claude AgentAPI** - Claude přes OAuth (no API key)

## Quick Start

### 1. Získej API klíče

**Gemini:**
```bash
# Jdi na https://aistudio.google.com/app/apikey
# Vytvoř nový API key
# Zkopíruj ho
```

**OpenAI:**
```bash
# Jdi na https://platform.openai.com/api-keys
# Vytvoř nový API key
# Zkopíruj ho
```

### 2. Nastav .env

```bash
cd /home/milhy777/Develop/Production/sos-agent
nano .env
```

Přidej klíče:
```
GEMINI_API_KEY=tvuj_gemini_klic_zde
OPENAI_API_KEY=tvuj_openai_klic_zde
```

### 3. Test s Gemini (default)

```bash
poetry run sos diagnose --category hardware
```

### 4. Test s OpenAI

```bash
# Vytvoř config soubor
cat > config/openai.yaml << 'YAML'
ai_provider: openai
openai_model: gpt-4o
YAML

# Spusť s OpenAI
poetry run sos diagnose --category hardware
```

### 5. Přepínání providerů

Edit `config/default.yaml`:
```yaml
ai_provider: gemini  # nebo "openai" nebo "claude-agentapi"
gemini_model: gemini-2.0-flash-exp
openai_model: gpt-4o
```

## Modely

### Gemini
- `gemini-2.0-flash-exp` (default, nejrychlejší)
- `gemini-2.0-flash-thinking-exp` (s reasoning)
- `gemini-pro`

### OpenAI
- `gpt-4o` (default, nejlepší)
- `gpt-4o-mini` (levnější)
- `o1-preview` (advanced reasoning)

### Claude AgentAPI
- Používá Claude Code OAuth
- Nevyžaduje API key
- Aktuálně má auth problémy (timeout)

## Troubleshooting

**"GEMINI_API_KEY not found":**
```bash
# Check .env soubor
cat .env | grep GEMINI

# Nebo export direct
export GEMINI_API_KEY="your-key-here"
```

**"OPENAI_API_KEY not found":**
```bash
# Check .env soubor  
cat .env | grep OPENAI

# Nebo export direct
export OPENAI_API_KEY="your-key-here"
```

**Test API klíče:**
```python
# Test Gemini
import google.generativeai as genai
genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = model.generate_content("Hello!")
print(response.text)

# Test OpenAI
from openai import OpenAI
client = OpenAI(api_key="YOUR_KEY")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Co funguje

✅ Gemini API client
✅ OpenAI API client
✅ Multi-model switching
✅ Streaming responses
✅ Config management
🟡 Claude AgentAPI (auth problém)

