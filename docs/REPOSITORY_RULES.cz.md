# Pravidla Repozitáře & Standardy

**Repozitář**: [milhy545/sos-agent](https://github.com/milhy545/sos-agent)
**Poslední aktualizace**: 2024-12-03

---

## 📋 Přehled

Tento dokument popisuje všechna pravidla repozitáře, politiky ochrany větví a vývojové standardy pro SOS Agent.

---

## 🛡️ Pravidla Ochrany Větví

### Ochrana Master Větve

Větev `master` je chráněna následujícími pravidly:

#### ✅ Povinné Kontroly Stavu
- **CodeQL Analýza** musí projít před mergem
- Striktní režim: Větve musí být aktuální před mergem

#### ❌ Blokované Akce
- **Force push**: Zakázáno (zabraňuje přepisování historie)
- **Smazání větve**: Zakázáno (master větev nelze smazat)
- **Přímé commity**: Povoleno pro vlastníka (není nutné PR pro solo projekt)

#### 💬 Vyřešení Konverzací
- **Povinné**: Všechny PR konverzace musí být vyřešeny před mergem
- Zajišťuje, že všechna zpětná vazba je zpracována

#### 🔓 Vynucení pro Adminy
- **Vypnuto**: Administrátoři repozitáře mohou v případě potřeby obejít pravidla
- Užitečné pro hotfixy a nouzové opravy

---

## 👥 Vlastnictví Kódu (CODEOWNERS)

Automatické žádosti o review jsou konfigurovány přes `.github/CODEOWNERS`:

| Vzor | Vlastník | Důvod |
|------|----------|-------|
| `*` | @milhy545 | Výchozí vlastník všech souborů |
| `/src/agent/` | @milhy545 | Jádro kódu agenta |
| `.env.example` | @milhy545 | Bezpečnostně kritická šablona |
| `.gitignore` | @milhy545 | Zabraňuje úniku API klíčů |
| `/.github/` | @milhy545 | CI/CD a workflows |
| `/docs/` | @milhy545 | Dokumentace |
| `*.md` | @milhy545 | Všechny markdown soubory |
| `pyproject.toml` | @milhy545 | Závislosti |
| `install.sh` | @milhy545 | Instalační skript |

---

## 🔒 Bezpečnostní Standardy

### Ochrana Tajemství

**Nikdy necommitovat**:
- `.env` soubory (použít `.env.example`)
- API klíče (Gemini, OpenAI, Inception, Claude)
- SSH klíče nebo přihlašovací údaje
- Jakékoliv soubory odpovídající `.gitignore` vzorům

**Automatizovaná Ochrana**:
- Dependabot: Týdenní aktualizace závislostí
- CodeQL: Skenování bezpečnosti kódu při push
- Secret Scanning: Automatická detekce tajemství GitHubem
- TruffleHog: Další skenování tajemství (plánováno)

### Bezpečnostně Kritické Soubory

Tyto soubory vyžadují extra kontrolu:
- `.env.example` - Šablona pro API klíče
- `.gitignore` - Chrání tajemství před commitem
- `install.sh` - Běží s uživatelskými právy
- `.github/workflows/security.yml` - Bezpečnostní automatizace

---

## 🔄 Požadavky na Workflow

### CI/CD Kontroly

Všechny commity do `master` spouští:

1. **CodeQL Analýza** (povinná)
   - Jazyk: Python
   - Skenuje bezpečnostní zranitelnosti
   - Musí projít před mergem

2. **Skenování Závislostí** (automatické)
   - Dependabot kontroluje týdně
   - Automaticky vytváří PR pro aktualizace

3. **Skenování Tajemství** (automatické)
   - GitHub skenuje všechny commity
   - Upozorňuje na detekovaná tajemství

### Pokyny pro Pull Requesty

Přestože jsou přímé commity povoleny, PR jsou doporučeny pro:
- Větší přidání funkcí
- Zlomové změny
- Aktualizace závislostí
- Bezpečnostně citlivé modifikace

**PR Checklist**:
- [ ] Všechny CI kontroly prošly
- [ ] Dokumentace aktualizována (EN + CZ)
- [ ] CHANGELOG.md aktualizován
- [ ] Žádná tajemství v diff
- [ ] Všechny konverzace vyřešeny

---

## 📦 Správa Závislostí

### Konfigurace Poetry

Závislosti jsou spravovány přes `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.11"
asyncclick = "^8.3.0"
rich = "^14.2.0"
google-generativeai = "^0.8.0"
openai = "^1.59.0"
aiohttp = "^3.13.0"
```

### Politika Aktualizací

- **Minor/Patch aktualizace**: Auto-schváleny Dependabotem
- **Major aktualizace**: Vyžaduje manuální kontrolu
- **Bezpečnostní aktualizace**: Okamžitá aplikace

---

## 🌍 Standardy Dokumentace

### Požadavek na Dvojjazyčnost

**Všechna dokumentace musí mít obě verze**:
- `README.md` + `README.cz.md`
- `GEMINI_API_POLICIES.md` + `GEMINI_API_POLICIES.cz.md`
- Budoucí dokumenty následují stejný vzor

### Soubory Dokumentace

| Soubor | Účel | Publikum |
|--------|------|----------|
| `README.md` | Uživatelská příručka | Koncoví uživatelé |
| `docs/ARCHITECTURE.md` | Design systému | Vývojáři |
| `docs/DEVELOPMENT.md` | Historie vývoje | AI agenti |
| `docs/GEMINI_API_POLICIES.md` | API best practices | Všichni |
| `CHANGELOG.md` | Historie verzí | Všichni |
| `INSTALL.md` | Průvodce instalací | Noví uživatelé |

---

## 🤖 Spolupráce AI Agentů

### Před Prováděním Změn

**AI agenti MUSÍ**:
1. ✅ Nejprve přečíst `docs/DEVELOPMENT.md`
2. ✅ Zkontrolovat `docs/ARCHITECTURE.md` pro design
3. ✅ Zkontrolovat `CHANGELOG.md` pro historii
4. ✅ Konzultovat oficiální API dokumentaci před hádáním

### Kritická Pravidla

- ❌ **Nikdy neopravovat vyřešené bugy** (zkontrolovat DEVELOPMENT.md)
- ❌ **Nikdy necommitovat API klíče** (použít .env.example)
- ❌ **Nikdy nerozbít dvojjazyčné dokumenty** (aktualizovat EN + CZ)
- ✅ **Vždy dokumentovat získané poznatky**
- ✅ **Vždy testovat před commitem**
- ✅ **Vždy aktualizovat CHANGELOG.md**

### Zlaté Pravidlo

**"VŽDY NEJDŘÍV DOKUMENTACI, PAK KÓD"**

Ne naopak! Číst:
1. `docs/DEVELOPMENT.md`
2. `docs/ARCHITECTURE.md`
3. Oficiální API dokumentaci
4. Pak začít kódovat

---

## 🚀 Proces Vydání

### Číslování Verzí

Následuje [Sémantické Verzování](https://semver.org/):
- `MAJOR.MINOR.PATCH` (např. `0.1.0`)
- **MAJOR**: Zlomové změny
- **MINOR**: Nové funkce (zpětně kompatibilní)
- **PATCH**: Opravy bugů

### Checklist Vydání

1. Aktualizovat `CHANGELOG.md` s číslem verze
2. Aktualizovat verzi v `pyproject.toml`
3. Otestovat všechny diagnostické kategorie
4. Otestovat oba jazyky (EN/CS)
5. Vytvořit git tag: `git tag v0.1.0`
6. Push s tagy: `git push --tags`
7. Vytvořit GitHub release

---

## 🔧 Nouzové Procedury

### Proces Hotfixu

Pro kritické bezpečnostní problémy:

1. **Vytvořit hotfix větev**: `git checkout -b hotfix/critical-issue`
2. **Aplikovat minimální opravu**
3. **Důkladně otestovat**
4. **Přeskočit CI pokud nutné** (obchod admina dostupný)
5. **Merge přímo do master**
6. **Dokumentovat v DEVELOPMENT.md**

### Vrácení Změn

Pokud commit rozbije produkci:

```bash
# Vrátit konkrétní commit
git revert <commit-hash>

# Force push pokud nutné (pouze admini)
git push --force-with-lease origin master
```

---

## 📊 Statistiky Repozitáře

- **Licence**: MIT
- **Jazyk**: Python 3.11+
- **Primární Větev**: `master`
- **CI/CD**: GitHub Actions
- **Bezpečnostní Skenování**: CodeQL + Dependabot
- **Dokumentace**: Dvojjazyčná (EN + CZ)

---

## 🔗 Související Dokumenty

- [ARCHITECTURE.md](ARCHITECTURE.md) - Design systému
- [DEVELOPMENT.md](DEVELOPMENT.md) - Historie vývoje
- [CHANGELOG.md](../CHANGELOG.md) - Historie verzí
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Pokyny pro přispívání (plánováno)

---

*Tento dokument definuje standardy repozitáře pro SOS Agent. Aktualizovat při změně politik.*
