# Contributing Guide

Human and AI-assisted contributions are welcome. Review generated changes the same way as hand-written changes: keep them small, typed, lint-clean, tested, and free of secrets.

This project has been developed with help from AI coding tools including Claude Code, Windsurf, and Codex. Human judgment owns the scope, defaults, safety posture, and final review.


## Project Specification
- **Python**: `>=3.11`
- **Runner**: Astral `uv`
- **Lint/Format**: `ruff`
- **Typing**: `ty`
- **Testing**: `pytest`
- **Entrypoint**: `main.py`
- **Config**: `config.py`
- **Secrets**: `.env` (loaded via `python-dotenv`)
- **External Tool**: `speedtest` (via `brew`)
- **Agent Guide**: `AGENTS.md`


## Core Commands
- **Sync Dependencies**: `uv sync`
- **Run Application**: `uv run python main.py`
- **Run Tests**: `uv run pytest -q`
- **Check & Fix All**: `uv run ruff check --fix . && uv run ruff format . && uv run ty check && uv run pytest -q`
- **Add Dependency**: `uv add <package>`
* * *


## Zero-Setup Execution (`main.py`)
`main.py` uses `uv` script dependency metadata so the app can run with `uv run python main.py` without a prior `uv sync`.

Keep the runtime dependencies in `main.py` in sync with the core application dependencies in `pyproject.toml`.
* * *


## Development Workflow & PR Checklist
1. Branch from `main`.
2. Make small, atomic commits using the Conventional Commits spec.
3. Ensure all checks pass locally before opening a Pull Request:

    - `uv run ruff check --fix . && uv run ruff format .`
      - (see [pyproject.toml](pyproject.toml) for ruff criteria)
    - `uv run ty check`
    - `uv run pytest -q`

4. The PR must have a clear summary of the problem and solution.
5. Confirm there is no scope creep.
6. Do not commit secrets.
