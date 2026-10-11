# full-stack-athlete — Implementation Design

> **Status: in progress.** The pure-core, thin-graph structure is decided; the other items in §9 are still open. Describes how the code is organized, for the behavior in [`architecture.md`](architecture.md) and the user-facing decisions in [`interaction-design.md`](interaction-design.md). Items marked **Decision needed** are listed in §9. No application code exists yet, and none should be written until this is approved.

## 1. Principle

The rules are plain, typed, side-effect-free functions over pydantic models. LangGraph is the orchestrator around them. It provides sequencing, per-date fan-out, checkpointing and pause/resume, and holds no domain logic. A reader should be able to test every scheduling, reconciliation and validation rule without constructing a graph, a checkpointer, or an LLM.

## 2. Layers and the dependency rule

Dependencies point downward only.

```
cli / api
   │
 graph        LangGraph wrappers; the only layer that performs I/O or calls the LLM
   │
 core         pure rules: state derivation, scheduler, reconcile, validation, plugins
   │
 models       pydantic domain types; ports (Protocols) for Device, Store, Notifier, LLMProvider
   ▲
adapters      implement ports (Garmin, markdown vault, push notifier, LLM providers)
```

- `models` and `ports` import nothing from the project.
- `core` imports `models` and port *types* only, and never performs I/O.
- `adapters` import `models` and `ports`. Nothing in `core` or `graph` imports a concrete adapter. They are injected at run time from config.
- `nutrition` (deferred) is its own subpackage. The training `core` never imports it.

## 3. Package layout

```
src/full_stack_athlete/
  models/        athlete, session notes, device data, sessions, training state
  ports/         device.py  store.py  notifier.py  llm.py
  core/
    state.py         derive_training_state
    scheduler/       Scheduler protocol + implementations
    plugins/         lifting, running, mobility, power
    reconcile/       classifier, interval extraction
    validate.py      equipment, injury, rotation, substitution coverage
  graph/         state.py  nodes.py  build.py
  adapters/
    garmin/  vault/  notifier/  llm/
  config.py      YAML schema (pydantic) and adapter/plugin wiring
  cli.py
tests/
  fixtures/      real notes + device JSON from Sep–Oct 2026
```

This replaces the `lift_and_run/` layout in architecture.md §13. The distribution is `full-stack-athlete`, the import package is `full_stack_athlete`, and the CLI is `full-stack-athlete` with a short alias `fsa`.

## 4. Graph nodes are wrappers

Each node does three things: read the slice of `LoopState` it needs, call one `core` function (or one port), and return the state update. If a node contains a conditional that encodes a domain rule, that rule belongs in `core`.

- Ports are injected through the graph's run-time config, not imported, so tests substitute in-memory fakes.
- Conditional edges (`decide → generate_*`, `validate → repair`) read a field set by a `core` function, such as `decision.session_type`. The edge does not recompute the rule.

## 5. The LLM boundary

```python
class LLMRequest(BaseModel, Generic[T]):
    purpose: str            # "context_narrative", "classify_activity", "parse_feedback", ...
    input: BaseModel
    response_model: type[T]

class LLMProvider(Protocol):
    def complete(self, request: LLMRequest[T]) -> T: ...
```

- Only `graph` calls an `LLMProvider`. `core` never does; it hands back a request or consumes a typed result.
- Providers: Anthropic API, local model, and **deferred-to-caller**. The deferred provider does not answer. It raises LangGraph's `interrupt()` with the serialized request (input plus JSON Schema of `response_model`), and `run` exits `needs_llm` with the `thread_id`. `resume --answer` validates the JSON against `response_model` and continues.
- **Resume re-executes the interrupted node from its start.** Each LLM call therefore sits in its own node with no side effects before it. Writes and pushes happen in later nodes only.

## 6. Ports

Minimal sketches, to be refined when each is built.

```python
class Device(Protocol):
    def activities(self, since: date) -> list[Activity]: ...
    def wellness(self, on: date) -> Wellness | None: ...
    def push(self, workout: GarminWorkout | DeviceWorkout, on: date) -> PushResult: ...
    def verify(self, result: PushResult, session: Session) -> list[VerificationError]: ...

class Store(Protocol):
    def load_history(self, window: DateRange) -> list[SessionNote]: ...
    def write_note(self, note: SessionNote) -> None: ...
    def apply(self, action: ReconAction) -> None: ...

class Notifier(Protocol):
    def send(self, summary: str) -> None: ...
```

Garmin-specific rules from architecture.md §8 (plain-pound weights, device by name, clear-then-schedule, substitution registry) live inside the Garmin adapter. The device-neutral part of workout planning, `Session`, is what `core` produces. The adapter turns it into a workout.

## 7. Plugins

- Scheduler, lifting, running, mobility and power implement the `Discipline` model in architecture.md §17.2.
- **Discovery (v1): in-tree registry.** The config names a plugin and the registry resolves it. Entry-point discovery for third-party packages can be added without changing the plugin protocols.
- A plugin owns its parameters (TMs, VDOT, volume tables) as validated data blocks read through `Store`, not as code constants.

## 8. Testing

- **`core`:** unit tests over the real-day fixtures in architecture.md §14. No graph, no fakes beyond plain data.
- **Fakes:** in-memory `Device`, `Store`, `Notifier`, and a scripted `LLMProvider`. The default test run makes no network calls.
- **Port contract tests:** one suite per port, run against every adapter (the fake and the real one), so adapters cannot drift from the interface.
- **Graph:** a few end-to-end tests with fakes for the pause/resume path, fan-out, and idempotent re-run. A full dry-run snapshot for a fixed date.
- Property tests (`hypothesis`) for unit conversions, as listed in architecture.md §14.

## 9. Decisions needed

1. ~~Confirm the pure-core, thin-graph structure~~ **Decided 2026-10-10** (§1, §4). Alternatives were a graph-centric design and a hand-written orchestrator with LangGraph only for the LLM pause. Both were judged worse.
2. ~~Single package vs. separate distributions per adapter~~ **Decided 2026-10-10:** one package with adapter subpackages. Adapter-specific dependencies (e.g. the Garmin client) are optional extras such as `full-stack-athlete[garmin]`. Splitting into separate distributions later is mostly moving directories, since the layers are already kept apart.
3. ~~Enforcing the layer rule in CI~~ **Decided 2026-10-10:** a plain pytest test that walks each module's imports with `ast` and fails on a forbidden boundary crossing (§2). No new dependency, and it runs in `just check`. `import-linter` stays an option if the rules get more complex.
4. ~~Python version~~ **Decided 2026-10-10:** 3.14, since this is a new project. Compatibility was checked on 2026-10-10 in a throwaway venv (langgraph 1.2.14, langgraph-checkpoint-sqlite 3.1.1, pydantic 2.14.0, langchain-core 1.6.9): a graph with an `interrupt()`, a SQLite checkpoint and a `Command(resume=…)` in a second process-level compile ran correctly on CPython 3.14.3, and the interrupted node re-entered from its start as §5 assumes. Caveats: langgraph's PyPI classifiers list only up to 3.13, even though `requires-python` is `>=3.10`; and `langsmith` (pulled in by `langchain-core`) calls `asyncio.iscoroutinefunction`, which emits a `DeprecationWarning` on 3.14 and is slated for removal in 3.16. Do not turn warnings into errors in pytest without filtering that one. The upgrade is step 0 of the implementation plan (§10); no config has been changed yet. Switching needs `requires-python`, `.python-version` (currently 3.12, so CI is on 3.12), ruff `target-version` and mypy `python_version` changed together.
5. ~~Dependencies~~ **Approved 2026-10-10**, to be added when the step that needs it starts, not before:
   - `langgraph` and `langgraph-checkpoint-sqlite`, with the graph wiring (§10 step 5).
   - `PyYAML`, with the config schema (§10 has no separate config step yet; it lands with the first step that needs config). Chosen over `ruamel.yaml` because the config is only read and validated; revisit if the future `init` wizard needs to rewrite a user's file in place.
   - The Garmin client (`garminconnect`), as the optional extra `full-stack-athlete[garmin]`, with the Garmin adapter (§10 step 6).

   Any dependency beyond these still needs a fresh approval.

## 10. Suggested build order

Sketch only, to be agreed before any code.

0. Move the project to Python 3.14: `requires-python`, `.python-version`, ruff `target-version` and mypy `python_version` together (see §9.4). First step of the implementation plan, no earlier.
1. `models` and `ports`, with fakes.
2. `core` state derivation and scheduler against the fixtures.
3. `core` reconcile classifier and validators.
4. Vault `Store` adapter plus its contract tests.
5. Graph wiring, pause/resume and the CLI.
6. Garmin `Device` adapter, ported from the current scripts.
