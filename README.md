# hybrid-athlete

Library for turning a prompt-driven daily strength/running/mobility training
loop into a deterministic, tested Python core, orchestrated with LangGraph.
See [`docs/architecture.md`](docs/architecture.md) for the full design.

## Setup

```bash
uv sync --extra dev
```

Install `just` (not a Python dependency): `brew install just` (macOS) or [see installation guide](https://github.com/casey/just#installation)

## Usage

```bash
uv run hybrid-athlete
```

## Development

```bash
just check   # runs ruff check, ruff format --check, mypy, and pytest — the same gate CI runs
```

Individual steps, if you want to run just one:

```bash
uv run pytest
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy
```
