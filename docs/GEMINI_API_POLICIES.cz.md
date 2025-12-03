# Google Gemini API - Pravidla & Best Practices

**Poslední aktualizace**: 2024-12-03

## 📊 Free Tier Limity

| Metrika | Free Tier Limit |
|---------|-----------------|
| **RPM** (Požadavků za minutu) | 5 RPM |
| **RPD** (Požadavků za den) | 25 RPD |
| **Efektivní rychlost** | 1 požadavek každých 12 sekund |
| **Context Window** | 1M tokenů (plný přístup) |
| **Reset** | Denní kvóta se resetuje o půlnoci PT |

⚠️ **Důležité**: Free tier je určen pro **testování/prototypování**, NE produkci!

## 🚫 Časté Důvody Banu

### Porušení Obsahu
- ❌ **Nenávistné projevy, obtěžování, šikana**
- ❌ **Sexuálně explicitní nebo grafický obsah**
- ❌ **Násilí, nebezpečné instrukce**
- ❌ **Dezinformace, nelegální aktivity**
- ❌ **Porušení duševního vlastnictví**

### Technická Porušení
- ❌ **Obcházení bezpečnostních filtrů** (jailbreaky, prefixy)
- ❌ **Automatizované zneužití** (vysokofrekvenční scraping)
- ❌ **Manipulace s kvótou** (vícero účtů)

### Enforcement
- 🤖 **Automatické skenování** všech API požadavků
- 👁️ **Manuální kontrola** označených projektů
- ⚠️ **Dočasné pozastavení** → ❌ **Trvalý ban**

## ✅ Best Practices pro SOS Agent

### 1. Optimalizace Požadavků
```python
# ✅ DOBŘE: Sloučit více kontrol do jednoho požadavku
prompt = """
Zkontroluj systémové logy, využití zdrojů a stav služeb.
Poskytni komplexní diagnostiku.
"""

# ❌ ŠPATNĚ: Vícero sekvenčních požadavků
check_logs()  # Požadavek 1
check_cpu()   # Požadavek 2
check_disk()  # Požadavek 3
```

### 2. Strategie Rate Limiting
```python
# Exponenciální backoff při 429 chybách
import time

for attempt in range(3):
    try:
        response = gemini_api.generate(prompt)
        break
    except RateLimitError:
        wait_time = (2 ** attempt) * 60  # 1min, 2min, 4min
        time.sleep(wait_time)
```

### 3. Výběr Modelu
- **Gemini Flash** (výchozí): Rychlý, levný, dobrý na logy/diagnostiku
- **Gemini Pro**: Jen pro komplexní úvahy/security audity
- **Fallback**: Přepnout na Mercury/OpenAI pokud kvóta vyčerpána

### 4. Bezpečné Prompty pro Systémovou Diagnostiku
```bash
# ✅ BEZPEČNÉ: Technická systémová diagnostika
"Analyzuj /var/log/syslog pro hardwarové chyby"
"Zkontroluj stav systemd služeb a poskytni doporučení"
"Diagnostikuj problémy se síťovým připojením"

# ❌ VYHNOUT SE: Může spustit filtry
"Jak obejít firewall omezení"      # Bezpečnostní porušení
"Generuj škodlivé payloady"         # Nebezpečný obsah
```

### 5. Bezpečnost API Klíče
- ✅ Ukládej v `.env` souboru (git-ignored)
- ✅ Používej Google Cloud Secret Manager v produkci
- ❌ Nikdy nehardcoduj do zdrojového kódu
- ❌ Nikdy necommituj na GitHub

### 6. Ošetření Chyb
```python
if error.code == 429:  # Rate limit
    # Počkej a zkus znovu NEBO přepni providera
    use_fallback_provider("mercury")

elif error.code == 403:  # Kvóta vyčerpána / banned
    # Vytvoř nový GCP projekt (sos gcloud setup --auto)
    logger.warning("Gemini kvóta vyčerpána, přepínám na Mercury")
```

## 🔄 Obnova z Vyčerpané Kvóty

### Možnost 1: Počkat
- Kvóty se resetují o **půlnoci Pacific Time**
- Free tier: limit 25 požadavků/den

### Možnost 2: Přepnout Providera
```bash
sos --provider mercury diagnose    # Použij Mercury (bez kvóty)
sos --provider openai diagnose     # Použij OpenAI (separátní kvóta)
```

### Možnost 3: Vytvořit Nový Projekt
```bash
sos gcloud setup --auto            # Auto-vytvoř nový GCP projekt
```

⚠️ **Varování**: Nezneužívej vytváření projektů - Google sleduje vzorce účtů!

## 📈 Upgrade na Placenou Verzi

Pro vyhnutí se problémům s kvótou v produkci:

1. Aktivuj **Cloud Billing** v GCP Console
2. Upgraduj na **Pay-as-you-go** tier:
   - RPM: 1000+ (vs 5 zdarma)
   - TPM: 4M+ (vs limitovaný)
   - Bez denního limitu

3. Cena: ~$0.00025/1K tokenů (Flash) nebo $0.00125/1K (Pro)

## 🛡️ Jak SOS Agent Dodržuje Pravidla

1. **Pouze systémová diagnostika** - žádný uživatelský škodlivý obsah
2. **Rate limiting** - respektuje 5 RPM / 25 RPD limity
3. **Exponenciální backoff** - řeší 429 chyby elegantně
4. **Multi-provider** - fallback na Mercury/OpenAI
5. **Bezpečné prompty** - jen technické dotazy, žádné obcházení filtrů
6. **Bezpečnost API klíčů** - environment proměnné, nikdy necommitované

## 📚 Oficiální Zdroje

- [Dokumentace Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Pravidla Použití](https://ai.google.dev/gemini-api/docs/usage-policies)
- [Podmínky Služby](https://policies.google.com/terms)
- [Zakázané Použití Generativní AI](https://policies.google.com/terms/generative-ai/use-policy)

## 🚨 Pokud Dostaneš Ban

1. **Zkontroluj porušení**: Projdi API logy pro označený obsah
2. **Proces odvolání**: [GCP Support](https://console.cloud.google.com/support)
3. **Alternativa**: Použij Mercury/OpenAI (žádná Google omezení)
4. **Prevence**: Čti pravidla, testuj prompty pečlivě

---

**TL;DR pro Uživatele SOS Agent**:
- Free tier: 5 požadavků/min, 25/den
- Neobcházej filtry ani nespamuj požadavky
- Použij `--provider mercury` jako fallback
- `sos gcloud setup --auto` vytvoří nový projekt pokud banned
