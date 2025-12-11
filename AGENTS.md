# Repository Guidelines

## Project Structure & Module Organization
- Core CLI lives in `src/cli.py`; AI provider clients and permissions live in `src/agent/` (`openai_client.py`, `gemini_client.py`, `inception_client.py`, `permissions.py`).
- Diagnostics and system helpers sit in `src/tools/` (e.g., `log_analyzer.py`) and `src/monitors/`; Google Cloud helpers are in `src/gcloud/`.
- Auth flows for Claude/AgentAPI live in `src/claude_cli_auth/`. Setup prompts reside in `src/setup_wizard.py`.
- Docs are in `docs/` (read `ARCHITECTURE.md`, `DEVELOPMENT.md`, and `REPOSITORY_RULES.md` before coding). User-facing installers and scripts are at repo root (`install.sh`, `sos-launcher.sh`). Tests belong in `tests/` (pytest style).

## Build, Test, and Development Commands
- `poetry install --with dev` — create the virtualenv with runtime and dev deps.
- `poetry run sos diagnose --category hardware` — run the CLI locally (any category works).
- `poetry run pytest` — execute the test suite (add tests under `tests/`).
- `poetry run black src` | `poetry run ruff check src` | `poetry run mypy src` — format, lint, and type-check; run all before pushing.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, snake_case for modules/functions, PascalCase for classes.
- Prefer type hints throughout; fail closed on permissions and shell calls.
- Keep prompts and system commands grounded in collected data (see `log_analyzer.py`); avoid speculative outputs.
- Documentation is bilingual; when touching docs, update both EN and CZ counterparts.

## Testing Guidelines
- Framework: pytest (+ pytest-asyncio for async code). Name files `test_*.py` and mirror the module path (e.g., `tests/tools/test_log_analyzer.py`).
- Cover: CLI flows that call data collectors, AI client adapters, and permission checks. Assert we send real system data, not placeholders.
- For commands invoking the shell, prefer fakes/mocks over live calls; record sample outputs where needed.

## Commit & Pull Request Guidelines
- Commit style follows Conventional Commits seen in history (`feat:`, `fix:`, `chore:`, `docs:`). Keep subjects imperative and short.
- PRs: include a clear summary, linked issue, notable before/after output (CLI snippets), and screenshots if UI/terminal formatting changes.
- Required checks: keep branch up to date; CodeQL must pass. Resolve every thread before merge. Update `CHANGELOG.md` and relevant docs (EN + CZ) for user-facing changes.

## Security & Configuration Tips
- Never commit secrets or `.env`; use `.env.example` as a template. Validate AI keys via `sos setup`.
- Treat `install.sh`, `config/default.yaml`, and `.gitignore` as sensitive; double-check diffs for privilege or path changes.
- Before coding, skim `docs/DEVELOPMENT.md` for known pitfalls and `docs/ARCHITECTURE.md` for flow expectations.
