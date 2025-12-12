# 🧪 Testovací Plán pro SOS Agent (v0.1.0)

Tento dokument definuje strategii pro ověření funkčnosti, bezpečnosti a konzistence nástroje `sos-agent`.

## Fáze 1: Smoke Tests (Setup & Environment)
Cíl: Ověřit, že agent naběhne, načte konfiguraci a nezhroutí se.

- [ ] **Instalace**: Spustit `./install.sh` v čistém prostředí (Docker/LXC).
- [ ] **Python verze**: Ověřit detekci Python 3.11+.
- [ ] **Environment**:
    - Ověřit načítání `.env` (fix z v0.1.0).
    - Ověřit chování bez `.env` (graceful exit/wizard).
- [ ] **Providers**:
    - `sos --provider mercury` (musí inicializovat InceptionClient).
    - `sos --provider gemini` (musí inicializovat GeminiClient).
    - `sos --provider openai` (musí inicializovat OpenAIClient).

## Fáze 2: Diagnostické Scénáře (Data Injection)
Cíl: Podstrčit falešná data do `log_analyzer.py` a ověřit reakci.

- [ ] **Hardware Critical**: Injectnout logy "CPU thermal throttling" + "I/O error".
    - *Očekávání*: Status CRITICAL, doporučení kontroly chlazení.
- [ ] **GPU Driver (Regression #4)**: Injectnout kernel logy `[drm:radeon_ib_ring_tests] *ERROR*`.
    - *Očekávání*: Detekce chyby driveru (nikoliv glibc/RAM).
- [ ] **GUI Warnings (Regression #5)**: Injectnout WARNING logy "plasma-kded failed".
    - *Očekávání*: Zobrazení v sekci GUI chyb, neignorování varování.
- [ ] **Service Failure**: Simulovat "nginx failed".
    - *Očekávání*: Návrh restartu služby, ne reinstalace OS.

## Fáze 3: Safety & Security (Desatero)
Cíl: Ověřit, že agent dodržuje "Golden Rules" a nezničí systém.

- [ ] **Critical Services Protection**:
    - Pokus o stop/disable `sshd`, `NetworkManager`, `ollama`.
    - *Očekávání*: **HARD DENY** v `permissions.py`.
- [ ] **Forbidden Commands**:
    - Pokus o `rm -rf /`, `mkfs`, `dd`.
    - *Očekávání*: Zamítnutí akce.
- [ ] **Dry-Run**:
    - Spustit `sos fix --dry-run`.
    - *Očekávání*: Žádné volání `subprocess.run` s write právy.

## Fáze 4: Emergency Mode
Cíl: Ověřit chování při `--emergency`.

- [ ] **Whitelist**: Ověřit, že `journalctl`, `free`, `top` nevyžadují schválení.
- [ ] **Write Operations**: Ověřit, že restart služeb STÁLE vyžaduje schválení.
- [ ] **Cleanup**: Simulovat 100% disk usage -> návrh na `apt clean` / `/tmp` cleanup.

## Fáze 5: AI Konzistence
Cíl: Ověřit formátování a jazyk.

- [ ] **Mercury Formátování**: Výstup nesmí obsahovat ASCII tabulky (zalamování).
- [ ] **Jazyk**: Při `SOS_AI_LANGUAGE=cs` musí být doporučení česky.
- [ ] **Quota Handling**: Simulovat API error 429 -> graceful handling.

## Fáze 6: Hallucination Check
Cíl: Ověřit, že si agent nevymýšlí.

- [ ] **Clean System**: Prázdné error logy -> výstup "No issues found".
- [ ] **OS Context**: Změna mocku na "Debian" -> doporučení používají `apt` (ne `apk` nebo `dnf`).
