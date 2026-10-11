# full-stack-athlete

## Project Overview
- Library for turning a prompt-driven daily strength/running/mobility
  training loop into a deterministic, tested Python core orchestrated with
  LangGraph, with a thin CLI.
- **Status: skeleton only.** No application code yet — the architecture is
  still being iterated on. Do not implement features (plugins, Garmin
  integration, the LangGraph graph, etc.) until explicitly asked.
- Design reference: `docs/architecture.md` (still being iterated on; naming
  not final — "lift-and-run" is a working name).

## Commands
- `uv sync --extra dev` — install all dev dependencies
- `just check` — the authoritative verification gate: ruff lint, ruff format check, mypy, pytest (identical to what CI runs on every PR)
- `uv run pytest` — run tests with coverage
- `uv run ruff check src/ tests/` — lint
- `uv run mypy` — type-check
- `uv run full-stack-athlete` (alias `fsa`) — placeholder CLI command (prints version; Typer collapses to the single registered command when there's only one)

## Automation & Verification
- `just check` is the single CI-authoritative gate — `.github/workflows/ci.yml` runs this exact command, nothing more, nothing less. Locally and in CI it always means: `ruff check src/ tests/`, `ruff format --check src/ tests/`, `mypy`, `pytest`, in that order, fail-fast.
- `main` is branch-protected: the `check` CI status must be green and every change must go through a pull request, with no exception for the repo owner — there is no direct-push path around the gate.

## Conventions
- Use pydantic for domain models once they exist — not dataclasses.
- Explicit over implicit; no magic numbers; no commented-out code; no bare `except`; decompose functions over ~30 lines.
- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
- Use `importlib.metadata.version("full-stack-athlete")` for `__version__` — never hardcode it.

## Testing Rules
- Test-first for anything beyond a trivial change.
- No real network calls in the default test run.
- Run lint and typecheck before declaring any task done.

## Agentic Behavior Rules
- Do not start implementing architecture features (plugins, graph nodes, Garmin integration, data models) until explicitly asked — right now we are iterating on the design, not building it.
- Before deleting or overwriting any file, confirm with the user.
- Before making changes across more than 3 files, present a plan and wait.
- When uncertain between two approaches, present both with tradeoffs.
- Never install new dependencies without asking first.
- Never merge a pull request — always create the PR and stop; merging `main` always requires human review, no exceptions.
- Never modify this file during a task unless explicitly asked.

## Never Do
- Never commit secrets (`.env`) — only `.env.example`, once one exists.
