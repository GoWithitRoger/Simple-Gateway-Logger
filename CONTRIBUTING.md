# Contributing Guide (AI Agents + Humans)

This project is optimized for quick, safe contributions by LLM coding agents and humans. Keep changes small, fully-typed, lint-clean, and tested.

## Project Basics
- Python: 3.11+ (see `pyproject.toml` → `requires-python = ">=3.11"`).
- Env/runner: Astral UV.
- Linting: Ruff (line length 88, target `py311`).
- Type checking: Ty.
- Testing: Pytest.
- Entry point: `main.py`.
- Configuration: `config.py`.
- Secrets: `.env` with `GATEWAY_ACCESS_CODE` (loaded via `python-dotenv`).
- External tool: Ookla Speedtest CLI on macOS (`brew install speedtest`).

## Quick Start
- Create virtual env (optional):
  - `uv venv`
- Sync deps from `pyproject.toml`:
  - `uv sync`
- Run the app:
  - `uv run python main.py`
- Run tests:
  - `uv run pytest -q`
- Lint (auto-fix):
  - `uv run ruff check --fix .`
- Format:
  - `uv run ruff format .`
- Type check:
  - `uv run ty check`
- Add a dependency:
  - `uv add <package>`
- Add a dev dependency:
  - `uv add --dev <package>`

## Development Workflow
1. Branch from `main` (e.g., `feat/something-useful`).
2. Make small commits using Conventional Commits:
   - `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
3. Keep scope tight; avoid unrelated refactors.
4. Before pushing, always run locally:
   - `uv run ruff check --fix .`
   - `uv run ruff format .`
   - `uv run ty check`
   - `uv run pytest`
5. Open a PR with:
   - Clear problem and solution summary.
   - Trade-offs or limitations.
   - Tests added/updated and rationale.

## Code Style & Quality
- PEP 8 enforced by Ruff; fix all lint before PR.
- Line length 88; target version `py311`.
- Prefer precise type hints for public functions; avoid `Any` when possible.
- Docstrings: concise Google-style summaries; include args/returns for non-trivial APIs.
- Imports grouped: stdlib, third-party, local. No wildcard imports.
- Keep modules cohesive; factor helpers to maintain readability.

## Configuration & Secrets
- User-editable settings live in `config.py`.
- Secrets are read from environment variables. Typical setup:
  - Create `.env` alongside `main.py` with: `GATEWAY_ACCESS_CODE='your_code_here'`.
- Do not commit real secrets.

## Testing Guidance
- Use `pytest` for unit/integration tests.
- Add tests for new behavior and bug fixes.
- Prefer realistic inputs; keep tests fast and deterministic.
- Use fixtures for shared setup.

## Project Structure (key files)
- `main.py` — application entry point.
- `config.py` — runtime configuration.
- `README.md` — end-user instructions.
- `pyproject.toml` — dependencies and tooling configuration.

## macOS Note
- Install Ookla Speedtest CLI for local speed tests:
  - `brew install speedtest`

## PR Review Checklist
- Lint clean: `uv run ruff check --fix .` and `uv run ruff format .`.
- Types pass: `uv run ty check`.
- Tests pass: `uv run pytest`.
- No scope creep; clear commits; comprehensive docstrings.

Thanks for contributing!