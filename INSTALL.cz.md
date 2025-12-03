# 🆘 SOS Agent - Instalační Návod

## Rychlá Instalace (Jeden Příkaz)

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/sos-agent/main/install.sh | bash
```

Nebo stáhni a spusť manuálně:

```bash
git clone https://github.com/YOUR_USERNAME/sos-agent.git
cd sos-agent
./install.sh
```

## Co Instalátor Udělá

1. ✅ Zkontroluje, že máš Python 3.11+
2. ✅ Vytvoří adresář `~/.sos-agent/`
3. ✅ Nastaví izolované Python prostředí
4. ✅ Nainstaluje všechny závislosti automaticky
5. ✅ Vytvoří globální příkaz `sos`
6. ✅ Přidá `~/.local/bin` do PATH (pokud není)
7. ✅ Spustí setup wizard pro API klíče

## Po Instalaci

Prostě zadej odkudkoliv:

```bash
sos
```

## První Spuštění

Nakonfiguruj svého AI providera (Gemini, OpenAI, nebo Inception Labs):

```bash
sos setup
```

Wizard se zeptá na API klíče. Získej je tady:
- **Gemini**: https://aistudio.google.com/app/apikey (Zdarma!)
- **OpenAI**: https://platform.openai.com/api-keys
- **Inception Labs**: https://inceptionlabs.ai

## Příklady Použití

```bash
# Rychlá kontrola hardwaru
sos diagnose --category hardware

# Zkontroluj síť
sos diagnose --category network

# Kompletní systémová diagnostika
sos diagnose --category all

# Zobraz všechny příkazy
sos --help
```

## Požadavky

- **Python 3.11+** (zkontroluj: `python3 --version`)
- **Linux** (Alpine, Debian, Ubuntu, Arch, atd.)
- **Internet** (pro API volání)

## Odinstalace

```bash
rm -rf ~/.sos-agent
rm ~/.local/bin/sos
```

## Řešení Problémů

### "sos: command not found"

Znovu načti shell:

```bash
source ~/.zshrc    # pro ZSH
source ~/.bashrc   # pro Bash
```

Nebo restartuj terminál.

### "Python 3.11+ required"

Nainstaluj Python 3.11+:

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

Spusť setup wizard:

```bash
sos setup
```

Nebo ručně vytvoř `~/.sos-agent/.env`:

```bash
GEMINI_API_KEY=tvuj_klic_zde
OPENAI_API_KEY=tvuj_klic_zde
INCEPTION_API_KEY=tvuj_klic_zde
```

## Podpora

- 📖 Dokumentace: [README.cz.md](README.cz.md)
- 🐛 Problémy: GitHub Issues
- 💬 Diskuze: GitHub Discussions
