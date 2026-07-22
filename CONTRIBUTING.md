# Contributing

Small fixes and practical improvements are welcome. For a larger change, open an issue first so we
can confirm that it fits this project's deliberately narrow scope.

## Setup

```bash
uv sync
```

## Checks

```bash
uv run ruff check .
uv run ruff format . --check
uv run ty check
uv run pytest -q
```

Please keep changes focused, update tests or documentation when behavior changes, and do not commit
`.env` files, network logs, CSV output, or other local data.
