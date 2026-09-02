# Concorde workflow

The workflow keeps durable intent/architecture, executable implementation/evidence, temporary work,
and generated projections distinct while allowing an explicit implementation attempt to reconcile
all affected sources together.

## Lifecycle

```text
initialize module hierarchy
        ↓
specify / clarify one direct feature file
        ↓
review requirements-quality checklists
        ↓
plan against module architecture + code/tests
        ↓
generate dependency-ordered tasks
        ↓
analyze ↔ implement ↔ converge
        ↓
validate full reconciled repository
        ↓
Proposal 8 delivery removes attempt only
```

## 1. Initialize

`concorde.init` proposes Profile 7 control state, `.concorde/reflections/log.md`, and a root
`architecture.md`. The maintainer
reviews exact files/digests before apply. Existing configured hierarchies return unchanged rather
than receiving starter prose.

The root architecture defines responsibility/boundary, inventories, entity/relationship vocabulary,
representative interactions, a required Archify system overview, and optional additional module diagram declarations. Product modules are created
only from product responsibilities, never from Concorde's internal roles.

## 2. Specify and clarify

`concorde.specify` creates or revises one direct module feature file. It embeds every meaningful
interface and references existing architecture entities. A new feature is registered in the
providing architecture's immediate feature inventory; structural entity/relationship changes remain
explicit architecture work.

`concorde.clarify` asks a small number of high-impact questions and reconciles each answer through
front matter, usage, interfaces, failures, requirements, and Architecture Zoom. It never redefines a
module entity inside a feature.

For a new file, the first Protocol 12 response leaves stable-ID attempt fields unresolved. After the
feature front matter exists, specification reruns the resolver and evaluates the built-in
requirements checklist under the returned `.concorde/attempts/<stable-feature-id>/checklists/` path.
Custom checklists remain reviewer-owned.

## 3. Plan

`concorde.plan` runs Workspace Protocol 12 and reads:

- the complete selected feature file;
- the providing module architecture and bounded ancestry;
- explicitly relevant related-feature interfaces;
- the constitution;
- current source code and tests; and
- existing selected attempt artifacts.

It writes plan/research/data model/quickstart under the returned `attempt_dir`. There is no prose
implementation baseline: requested behavior is compared directly with code and tests. Planning
names every required module architecture, feature/interface, code, test, fixture, projection,
package, and public-guide reconciliation.

Planning does not edit durable sources. It records conflicts, workarounds, and provisional prototype
choices in `.concorde/reflections/log.md` and keeps going when a safe bounded assumption is possible.
New entries reserve their ID atomically through the installed reflection helper. The separate
reflection-triage/v3 merge workflow removes only validated merged `small` `fast-loop` entries and
leaves all other routes for maintainer disposition.

## 4. Tasks

`concorde.tasks` produces dependency-ordered, test-first tasks. Every task has a stable ID, exact
paths, requirement or acceptance trace, dependencies, and a proportionate verification check.

Tasks may explicitly own durable reconciliation when the planned change affects architecture entity
identity/type/locator, relationships/interactions, module inventories, feature outcome/usage,
embedded interfaces/failures, requirements, or Architecture Zoom. This keeps architecture,
behavior, implementation, and evidence coherent in the same attempt.

## 5. Analyze, implement, and converge

`concorde.analyze` is a read-only consistency/coverage audit. It can append only a centralized
reflection when the audit itself encounters a framework/tooling conflict.

`concorde.implement` executes tasks phase-by-phase. Before checking a task it records compact attempt
evidence: task/trace, actual command, outcome, evidence path, scope, and limitation. Only a passed
proportionate check permits completion. Unexpected durable changes stop task completion.

`concorde.converge` compares current repository/evidence state with feature intent, architecture, and plan,
then appends only genuinely remaining tasks. It preserves existing task IDs/text/markers.

## 6. Validation and projections

Validation checks the complete module/entity/relationship/interaction and
feature/interface/Architecture Zoom graph plus layout, attempts, diagrams, reflections, and path
safety. Tests and doc/package builds prove behavior and projection freshness.

Architecture diagrams are changed as source + textual architecture + generated output/freshness in
one task. Generated output never substitutes for an entity or interface definition.

## 7. Delivery

`concorde.deliver` is invoked only after architecture/feature/code/tests/projections already
agree and every task/checklist has evidence.

Proposal mode returns a digest-bound Delivery Proposal 8 naming exactly the selected attempt. The
invocation authorizes immediate apply without a second question. Apply rechecks digest, validation,
completion, and safe paths, then atomically removes the attempt. It writes no durable narrative.

Any failure preserves the entire attempt and every durable/executable authority.

## Fast loop

`concorde.fast-loop` is an alternative for one small, fully understood, single-feature/single-module
change with no active attempt, migration, new topology/type/compatibility policy, or multi-feature
coordination. It directly reconciles the minimal design/architecture/code/test set and runs focused
evidence. Otherwise use the full lifecycle.

## LangGraph prompt-stage composition

The Markdown files under `commands/` are complete canonical prompts. Agent projections wrap those
prompts for Codex or Claude; workflow graphs resolve the same bodies through
`concorde.command_assets.load_command_prompt`. Generated skills are never prompt authority.

`concorde.workflows.build_standard_dev_loop` uses LangGraph's public `StateGraph`, `START`, `END`,
`compile()`, and `invoke()` APIs to build this topology:

```text
START → specify → plan → tasks → deliver → END
```

Stages are ordered prompt bundles rather than copied or merged fragments:

| Stage | Canonical prompts |
|---|---|
| specify | `concorde.specify` |
| plan | `concorde.plan` |
| tasks | `concorde.tasks`, then `concorde.implement` |
| deliver | `concorde.validate`, then `concorde.deliver` |

The graph receives an injected executor. Each invocation contains the user request, immutable stage
definition and prompts, and all prior successful stage results. The executor decides how an
authorized agent or model consumes those prompts; the example only records them. An executor
exception remains visible and prevents downstream nodes.

LangGraph is optional and constrained to `langgraph>=1.2,<2`. It is a development dependency in this
checkout and imported only when a graph is built, so ordinary Concorde imports and the offline base
installer remain dependency-free. Installed workflow hosts must provide that optional package in
their Python environment. Run the real graph without credentials or network calls:

```bash
uv run python examples/standard_dev_loop.py "Add audit logging"
```

## Reflections

Planning, tasks, implementation, analysis, and convergence record problems when they must assume,
work around, defer, or stop. This includes choices that may be suboptimal but are acceptable for a
prototype. Repeated problems add occurrences rather than duplicate entries. Maintainers alone decide
resolved/dismissed status and notes.
