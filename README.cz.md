# 🆘 SOS Agent - Záchrana & Optimalizace Systému

**AI-Powered Systémový Administrátorský Agent pro Nouzovou Diagnostiku & Obnovu**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency-Poetry-blue)](https://python-poetry.org/)

SOS Agent je inteligentní nástroj pro záchranu systému, který využívá několik AI modelů. Poskytuje nouzovou diagnostiku, optimalizaci výkonu a asistenci při obnově Linuxových systémů.

## ✨ Funkce

- 🤖 **Podpora Více AI Modelů**
  - Google Gemini (výchozí, rychlý & bezplatný tier)
  - OpenAI GPT-4o (silné uvažování)
  - Inception Labs Mercury (specializovaný na kódování)
  - Claude přes AgentAPI (OAuth, experimentální)

- 🔧 **Komplexní Systémová Diagnostika**
  - Monitorování zdraví hardware
  - Kontrola stavu služeb
  - Analýza logů & detekce chyb
  - Metriky výkonu

- 🛡️ **Bezpečnost Předně**
  - Ochrana kritických služeb (sshd, NetworkManager)
  - Nouzový režim pro urgentní situace
  - Automatická doporučení zálohování

- 📊 **Interaktivní TUI (Textové Rozhraní)**
  - Cyberpunk vizuální styl
  - Perzistentní Chat s kontextem
  - Systém Fixerů s Dry-Run kontrolou
  - Real-time Dashboardy

## 🚀 Rychlý Start

### Instalace Jedním Příkazem

```bash
# Stáhnout a spustit instalátor
curl -fsSL https://raw.githubusercontent.com/milhy545/sos-agent/main/install.sh | bash
```

Nebo manuální instalace:

```bash
git clone https://github.com/milhy545/sos-agent.git
cd sos-agent
./install.sh
```

**A to je vše!** Instalátor vše vyřeší automaticky:
- ✅ Zkontroluje Python 3.11+
- ✅ Vytvoří izolované prostředí
- ✅ Nainstaluje závislosti
- ✅ Vytvoří globální příkaz `sos`
- ✅ Spustí setup wizard

### První Spuštění

Nakonfiguruj svého AI providera:

```bash
sos setup
```

Pak začni diagnostikovat:

```bash
sos diagnose --category hardware
```

📖 **Detailní instalační průvodce**: [INSTALL.md](INSTALL.md) | [INSTALL.cz.md](INSTALL.cz.md)

## 📖 Použití

### Dostupné Příkazy

```bash
sos menu                       # 🖥️ Spustit Interaktivní TUI (Doporučeno)
sos diagnose --category <typ>  # Spustit diagnostiku (CLI)
sos diagnose --issue "problem" # Diagnostika konkrétního problému
sos chat --message "ahoj"      # Chat s agentem (uchovává kontext session)
sos fix                        # Interaktivní režim oprav (CLI)
sos emergency                  # Nouzová fallback diagnostika
sos monitor                    # Real-time monitoring systému
sos check-boot                 # Boot/GRUB diagnostika
sos optimize-apps              # Vyčistit & optimalizovat aplikace
sos setup                      # Nakonfigurovat API klíče
```

### 🖥️ Interaktivní TUI

Spusťte plné rozhraní pomocí:

```bash
sos menu
```

Funkce:
- **Mřížkové menu**: Rychlá navigace (klávesy 0-9).
- **antiX-cli-cc nádech**: Stavový pruh s uloženým problémem + neon mřížka.
- **Chat**: Perzistentní AI chat s kontextem systému/problému.
- **Fixery**: Průvodce opravami s Dry-Run + dvojitým potvrzením.
- **Diagnostika Hub**: Náhled posledního `--issue` + tipy pro CLI.
- **Logy**: Zobrazení posledních logů agenta přímo v TUI.
- **Monitor**: Spuštění/zastavení dashboardu v reálném čase.
- **Cyberpunk Vzhled**: Vysoký kontrast pro viditelnost v nouzi.

### Kategorie Diagnostiky

- `hardware` - CPU, RAM, disk, senzory
- `network` - Konektivita, rozhraní, firewall
- `services` - Stav systemd služeb
- `security` - Bezpečnostní audity & zranitelnosti
- `performance` - Analýza výkonu CPU/RAM/disk

## 🔑 Konfigurace

### API Klíče

Získej své API klíče:

- **Gemini**: https://aistudio.google.com/app/apikey (Doporučeno ⭐)
- **OpenAI**: https://platform.openai.com/api-keys
- **Inception Labs**: https://inceptionlabs.ai

Přidej do `.env`:

```bash
GEMINI_API_KEY=tvuj_klic_zde
OPENAI_API_KEY=tvuj_klic_zde  # Volitelné
INCEPTION_API_KEY=tvuj_klic_zde  # Volitelné
```

### Přepnutí AI Providera

Uprav `config/default.yaml`:

```yaml
ai_provider: gemini  # nebo "openai", "inception"
gemini_model: gemini-2.0-flash-exp
openai_model: gpt-4o
inception_model: mercury-coder
```

## ⚠️ Bezpečnost

SOS Agent chrání kritické služby:
- **Nikdy nevypnuté**: sshd, NetworkManager, ollama, tailscaled
- **Nouzový režim**: Pouze read-only diagnostika
- **Zálohuj první**: Vždy doporučí zálohu před změnami

## 📄 Licence

MIT License - viz [LICENSE](LICENSE) pro detaily.

## 🆘 Podpora

- 🐛 Issues: https://github.com/milhy545/sos-agent/issues
- 💬 Diskuze: https://github.com/milhy545/sos-agent/discussions
- 📧 Email: [milhy545@gmail.com](mailto:milhy545@gmail.com)

---

**Vytvořeno s ❤️ pro systémové administrátory, kteří potřebují AI asistenci v nouzi**
