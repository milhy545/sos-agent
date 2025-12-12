## SOS Agent – úkoly pro Jules (podrobný plán)

- [ ] F1 Architektura & UX: navrhnout session/chat model, stavové struktury (issue, diag, fixy), cyberpunk TUI styl (tmavé bg, azuro/magenta/žlutý akcent, ASCII box). Definovat layout menu + stavová lišta.
- [ ] F2 Popis problému: přidat `--issue` do `sos diagnose`, ukládat do session, propisovat do promptu. Testy: CLI parsing, session store, prompt obsahuje issue (mock AI).
- [ ] F3 TUI menu (`sos menu`): mřížkové číslování 0–9, 2–3 sloupce, sekce Diagnostika/Opravy/Monitoring/Nastavení/Logy/Chat, šipky+Enter+0/q. Testy: snapshot/render, navigace, návrat.
- [ ] F4 Chat/interactive: přidat `sos chat` + vstup z TUI, perzistentní historie session; fallback bez klíče. Testy: uchování kontextu, prázdné vstupy.
- [ ] F5 Fixery: vytvořit rozhraní v `src/tools/` (dry-run, confirm, sudo guard, zálohy). Implementovat první fixer (DNS/network reset), napojit na `sos fix` + TUI. Testy: dry-run/run, confirm, mock shell.
- [ ] F6 Diag→Fix: mapovat výsledky diagnózy na doporučené fixy, akční plán + potvrzení; přidat další fixery (services restart, disk cleanup, boot check). Testy: mapping, vícekategoriové případy.
- [ ] F7 Monitoring panel: TUI start/stop pro existující monitory, zobrazení metrik. Testy: start/stop, stav v TUI.
- [ ] F8 Setup menu (TUI pro `sos setup`): volba jazyka, výběr barevného schématu, přepínač default AI provider/model, viditelné API klíče (maskované) + health check. Testy: render/přepínače bez reálných klíčů.
- [ ] F9 Dokumentace EN/CZ: README, INSTALL, DEVELOPMENT, CHANGELOG – nové příkazy, TUI ukázky, flow fixers/confirm, nastavení jazyka/barev/modelu.
- [ ] F10 QA: `poetry run pytest`, `ruff`, `black`, `mypy`; ruční průchod TUI v různých šířkách; verifikace chování bez AI klíče.
- [ ] Každá fáze: dokončit testy a sanity check výstupů před přechodem na další fázi (žádné přeskakování regresí).
