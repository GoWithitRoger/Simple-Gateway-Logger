# Contributing Guide (AI & Human)

Optimized for quick, safe contributions. Keep changes small, fully-typed, lint-clean, and tested.


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


## Core Commands
- **Sync Dependencies**: `uv sync`
- **Run Application**: `uv run python main.py`
- **Run Tests**: `uv run pytest -q`
- **Check & Fix All**: `uv run ruff check --fix . && uv run ruff format . && uv run ty check`
- **Add Dependency**: `uv add <package>`
* * *


## Zero-Setup Execution (`main.py`)
To enable zero-setup execution, `main.py` uses TOML frontmatter to declare its runtime dependencies. This allows running the app via `uv run python main.py` without requiring a prior `uv sync`.

The dependencies in the `main.py` frontmatter must be kept in sync with the core application dependencies in `pyproject.toml`.

**Example:**
```Python
# /// script
# dependencies = [
#   "python-dotenv",
#   "requests<3",
# ]
# ///
import requests
# ... app code
``` 

**Constraint**: This frontmatter method is only for the application's entry point (`main.py`). **All runtime dependencies required by `main.py` and any local modules it imports** (e.g., helper.py) *must* be declared in the frontmatter of `main.py`.
* * *


## Development Workflow & PR Checklist
1. Branch from `main`.
2. Make small, atomic commits using the Conventional Commits spec.
3. Ensure all checks pass locally before opening a Pull Request:

    - `uv run ruff check --fix . && uv run ruff format .`
    - `uv run ty check`
    - `uv run pytest`

4. The PR must have a clear summary of the problem and solution.
5. Confirm there is no scope creep.
6. Do not commit secrets.