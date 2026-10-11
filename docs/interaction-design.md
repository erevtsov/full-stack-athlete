# full-stack-athlete — Interaction Design

> Decisions on how users interact with the library, made 2026-10-10. Companion to [`architecture.md`](architecture.md), which describes the behavior being ported and the proposed internals. Where the two conflict on interaction (triggers, feedback entry, config), this document wins. Implementation details are still being designed and are not recorded here.

## 1. Users

- The first user is the project owner. The library must not assume that stays true: nothing athlete-specific (Garmin, an Obsidian vault, 5/3/1, a particular equipment list) lives in the core. It is configuration or a plugin.

## 2. Callers

- The core is exposed through a thin CLI and a Python API.
- **First caller:** a Claude-mediated routine (scheduled run plus chat turns) invoking the CLI.
- **Later caller:** an autonomous scheduler (e.g. launchd) running the same commands with a configured LLM provider.
- The core does not know or care which caller is driving it.

## 3. Integration ports

Three ports keep external systems out of the core. One adapter each ships first.

| Port | Responsibility | First adapter |
| --- | --- | --- |
| `Device` | Fetch activities and wellness; build, push, schedule and verify workouts | Garmin |
| `Store` | Read and write session history | Markdown vault (frontmatter + typed sections) |
| `Notifier` | Send the end-of-run summary | Push notification |

Others add Strava, SQLite, email, etc. by writing an adapter. Shipping more than one adapter per port is out of scope until a second real user needs it.

## 4. LLM provider interface

- Every LLM node (context narrative, ambiguous-activity classification, borderline wellness, feedback parsing) issues a **typed request** and expects a **typed pydantic response**. Any provider that can fill the schema works.
- Providers: **deferred-to-caller** (first), Anthropic API, local model.
- **Claude-mediated flow (two-phase):**
  1. `run` does all deterministic work. At an LLM node it stops, exits `needs_llm`, and prints a JSON request (typed input + expected output schema) and a `thread_id`.
  2. The caller answers and runs `resume --thread <id> --answer '<json>'`.
  3. Pause and resume are backed by the checkpointer and `interrupt()` (architecture.md §5.4).
- Switching to autonomous mode changes only which provider is configured.

## 5. Commands

| Command | Purpose |
| --- | --- |
| `validate` | Check the config and the adapters (device reachable, store writable) |
| `run [--date]` | Run the daily graph. Exits `done`, or `needs_llm` with a request and `thread_id` |
| `resume --thread X --answer …` | Supply the answer to a pending LLM request and continue |
| `feedback --date D "<text>"` | Parse the text into typed edits and resume that day's thread |
| `dry-run` | Full graph with no writes or pushes; print the diffs |
| `reconcile --days N` | Run reconciliation on its own |
| `verify --date D` | Re-verify a pushed workout |

## 6. Athlete feedback

- Entry is the explicit `feedback --date D "<text>"` command only. A chat turn or a script invokes it.
- Feedback always resumes that day's thread and re-enters at the earliest affected node (architecture.md §9).
- A note-based inbox (e.g. a `## Feedback` section read through `Store`) is deferred. If added, it is a second source feeding the same `feedback` entry point.

## 7. Configuration

- One hand-edited YAML file holds the athlete (equipment, injuries), the active scheduler/program/modules with their append-only activation history, `Device`/`Store`/`Notifier` settings, and the LLM provider.
- A pydantic model validates it, and every error names the offending field. `validate` runs this check.
- **Secrets** (Garmin session, API keys) are never in the YAML. They come from the environment or the OS keychain.
- An `init` wizard that writes the same YAML is planned but not v1. The schema is to be documented well enough that adding it changes nothing underneath.

## 8. Nutrition (deferred)

- Natural-language logging ("2 eggs and a large oat-milk latte") parsed by the LLM into a typed `MealEntry` (items, quantities, estimated kcal/protein/carbs/fat, confidence), viewed against daily/weekly targets.
- **Standalone tracking.** The scheduler never reads it. The training core does not import the nutrition module.
- Out of v1. The shared pieces (LLM provider interface, `Store`, CLI, config) are designed so adding it later requires no rewrite.
- Estimates are labelled as estimates with a confidence value and are user-correctable. Food databases, barcode scanning, micronutrients and meal planning are out of scope.
- Possible later coupling, not decided: a one-way `NutritionSignal` into the fatigue rule, or training-load-driven targets.

## 9. Open items

- Core/graph relationship: pure deterministic core with thin LangGraph wrappers is recommended, pending confirmation.
- Package layout: a single package with subpackages versus separate distributions per adapter.
- Plugin discovery: in-tree versus entry points for third-party plugins.
- The items in architecture.md §16 not answered above (self-reported fields, per-set logging, mobility "completed", multi-program scheduling, power-module questions).
