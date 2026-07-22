# Agent guide

This file is for AI coding agents and automation tools working in this repository.

## Project purpose

Simple Gateway Logger is a focused macOS diagnostic script for AT&T fiber gateways. It compares gateway-side diagnostics with local-machine network checks and writes each check cycle to CSV.

Keep the project narrow. Do not turn it into a generic network monitoring platform, dashboard, daemon, router abstraction layer, or cross-platform framework unless explicitly asked.

## Important files

- `main.py`: application entry point, scheduler, Selenium gateway checks, local diagnostics, CSV output.
- `config.py`: user-facing runtime configuration and safety toggles.
- `tests/`: parser, logging, orchestration, Selenium, cleanup, and bufferbloat tests.
- `.github/workflows/ci.yml`: public CI checks.
- `README.md`: human-facing overview and quickstart.
- `CONTRIBUTING.md`: contributor commands and expectations.
- `uv.lock`: locked dependency state; update when dependencies change.

## Commands

Use these before considering a change complete:

```bash
uv run ruff check .
uv run ruff format . --check
uv run ty check
uv run pytest -q
```

Use `uv sync` when dependencies need to be installed locally. If dependencies change, update `uv.lock`.

Use linting, type checks, and tests for verification. Do not run `uv run python main.py` unless the task specifically needs live gateway or local-network behavior.

## Safety and scope

- Do not commit `.env`, CSV logs, raw gateway logs, local caches, or personal network artifacts.
- Treat CSV/log output as potentially sensitive because it can contain local network metadata.
- Keep optional diagnostics opt-in when they require privileged access, local LAN assumptions, or broad process cleanup.
- Avoid broad `pkill`, `sudo`, or Chrome flags unless guarded by explicit config toggles.
- Prefer standard-library handling for structured formats such as CSV.
- Pass user-editable config values as parameters to subprocess/Selenium APIs when possible; avoid string interpolation into shell or JavaScript contexts.

## Documentation rules

- Keep the README concise: purpose, quickstart, common config, then optional details.
- Put agent-specific operational guidance here, not in the README.
- Keep `main.py` script metadata dependencies in sync with `pyproject.toml`.
- If behavior changes, update README, CONTRIBUTING, tests, and CI together when relevant.
