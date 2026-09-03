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
Proposal 9 delivery removes attempt only
```

## 1. Initialize

`concorde-init` proposes Profile 7 control state, `.concorde/reflections/index.json`, and a root
`architecture.md`. The maintainer
reviews exact files/digests before apply. Existing configured hierarchies return unchanged rather
than receiving starter prose. On request the same Skill scaffolds the packaged project docsite as a
separate reviewed proposal.

The root architecture defines responsibility/boundary, inventories, entity/relationship vocabulary,
representative interactions, a required Archify system overview, and optional additional module diagram declarations. Product modules are created
only from product responsibilities, never from Concorde's internal roles.

## 2. Specify and clarify

`concorde-specify` creates or revises one direct module feature file. It embeds every meaningful
interface and references existing architecture entities. A new feature is registered in the
providing architecture's immediate feature inventory; structural entity/relationship changes remain
explicit architecture work.

`concorde-clarify` asks a small number of high-impact questions and reconciles each answer through
front matter, usage, interfaces, failures, requirements, and Architecture Zoom. It never redefines a
module entity inside a feature.

For a new file, the first Protocol 13 response leaves stable-ID attempt fields unresolved. After the
feature front matter exists, specification reruns the resolver and evaluates the built-in
requirements checklist under the returned `.concorde/attempts/<stable-feature-id>/checklists/` path.
Custom checklists remain reviewer-owned.

## 3. Plan

Public Operation `concorde-plan` first launches internal read-only `concorde-plan-context`, then
passes its immutable result to `concorde-plan-author`. Trusted code resolves:

- the complete selected feature file;
- the providing module architecture and bounded ancestry;
- only feature bodies that uniquely own an exact `interfaces.required` ID, with that ID as reason;
- the constitution;
- providing-module owned source code/tests (never dependency internals); and
- existing selected attempt artifacts.

The author writes plan/research/data model/quickstart only under the returned `attempt_dir` plus
authorized per-file reflection state. There is no prose
implementation baseline: requested behavior is compared directly with code and tests. Planning
names every required module architecture, feature/interface, code, test, fixture, projection,
package, and public-guide reconciliation.

Each leaf receives a distinct default-deny Codex permission profile or Claude restricted strict
sandbox configuration. Missing/widened/unsafe/unenforceable policy stops before launch; LangGraph and
prompts do not enforce files. Planning does not edit durable sources. Planning and task generation
record concrete problems in `.concorde/reflections/<bucket>/R-NNN.md`: recording supplies detailed problem
facts but no root-cause analysis, proposed fix, or human-intervention decision. New documents reserve
their ID atomically through the installed helper. Reflection-triage/v5 completes those details later,
preserves User Comments, removes only validated merged `small` `fast-loop` documents, and leaves all
other routes for maintainer disposition.

## 4. Tasks

`concorde-tasks` produces dependency-ordered, test-first tasks. Every task has a stable ID, exact
paths, requirement or acceptance trace, dependencies, and a proportionate verification check.

Tasks may explicitly own durable reconciliation when the planned change affects architecture entity
identity/type/locator, relationships/interactions, module inventories, feature outcome/usage,
embedded interfaces/failures, requirements, or Architecture Zoom. This keeps architecture,
behavior, implementation, and evidence coherent in the same attempt.

## 5. Analyze, implement, and converge

`concorde-analyze` is a read-only consistency/coverage audit. Planning and tasks are the normal
reflection-recording points; another phase records a new document only for a distinct problem that
must persist beyond its ordinary report/evidence.

`concorde-implement` executes tasks phase-by-phase. Before checking a task it records compact attempt
evidence: task/trace, actual command, outcome, evidence path, scope, and limitation. Only a passed
proportionate check permits completion. Unexpected durable changes stop task completion.

`concorde-converge` compares current repository/evidence state with feature intent, architecture, and plan,
then appends only genuinely remaining tasks. It preserves existing task IDs/text/markers.

## 6. Validation and projections

Validation checks the complete module/entity/relationship/interaction and
feature/interface/Architecture Zoom graph plus layout, attempts, diagrams, reflections, and path
safety. Tests and doc/package builds prove behavior and projection freshness.

Architecture diagrams are changed as source + textual architecture + generated output/freshness in
one task. Generated output never substitutes for an entity or interface definition.

## 7. Delivery

`concorde-deliver` is invoked only after architecture/feature/code/tests/projections already
agree and every task/checklist has evidence.

Proposal mode returns a digest-bound Delivery Proposal 9 naming exactly the selected attempt. The
invocation authorizes immediate apply without a second question. Apply rechecks digest, validation,
completion, and safe paths, then atomically removes the attempt. It writes no durable narrative.

Any failure preserves the entire attempt and every durable/executable authority.

## Fast loop

`concorde-fast-loop` is an alternative for one small, fully understood, single-feature/single-module
change with no active attempt, migration, new topology/type/compatibility policy, or multi-feature
coordination. It directly reconciles the minimal design/architecture/code/test set and runs focused
evidence. Otherwise use the full lifecycle.

## LangGraph Operations

The 17 Markdown files under `skills/` are complete canonical public/internal leaves with exposure and
effects. Agent projections expose only 15 public leaves; Operation graphs may load the two internal
planner leaves through `concorde.skill_assets.load_skill_prompt`. Generated skills are never prompt authority.

`operations/concorde-standard-dev-loop/operation.py` uses the shared Operation runtime and LangGraph's public `StateGraph`, `START`, `END`,
`compile()`, and `invoke()` APIs to build this topology:

```text
START → specify → plan → tasks → deliver → END
```

Stages are ordered direct capability bundles rather than copied or flattened fragments:

| Stage | Direct capabilities |
|---|---|
| specify | `concorde-specify` |
| plan | public nested Operation `concorde-plan` |
| tasks | `concorde-tasks`, then `concorde-implement` |
| deliver | `concorde-validate`, then `concorde-deliver` |

The graph receives an injected executor/optional nested dispatcher. Each direct leaf invocation
contains request, occurrence binding, canonical prompt/effects, exact prior capability results, and
an immutable normalized/native launch specification. A real injectable boundary can call `codex exec`
or `claude -p` and return a digest-bound receipt; tests inject recorders and never call a live model.
Nested planner internals resolve only inside its graph. Any policy/executor/nested exception remains
visible and prevents downstream occurrences; same-stage leaves never share their permission union.

LangGraph is optional and constrained to `langgraph>=1.2,<2`. It is a development dependency in this
checkout and imported only when a graph is built, so ordinary Concorde imports and the offline base
installer remain dependency-free. Installed workflow hosts must provide that optional package in
their Python environment. Run the real graph without credentials or network calls:

```bash
uv run python operations/concorde-standard-dev-loop/operation.py "Add audit logging" --describe-policy
```

## Reflections

Planning and task generation are the normal recording points. Each new `R-NNN.md` is created under
`.concorde/reflections/pending/` and contains enough Context, Expected, Observed, Impact, and
Evidence for later investigation, but no recommendation or human-intervention judgment. Repeated
problems add occurrences rather than duplicate files. Maintainers alone edit User Comments and
decide resolved/dismissed status and resolution notes. Immediately after creating the document or
appending an occurrence, the writer runs `reflections_queue.py --validate-entry R-NNN`, a bounded,
read-only check that reports findings attributable to that one entry separately from unrelated ones,
and corrects only its own new entry until it reports valid.

The collection is split into three tracked buckets that mirror triage state: `pending/` (not yet
investigated), `planned/` (`human_intervention: not-required`; automation may proceed), and
`needs-comments/` (`human_intervention: required`; waiting for maintainer input). After the parent
persists a validated triage completion it runs `reflections_queue.py --relocate R-NNN`, which moves
the document into the folder its front matter now requires. Nothing else moves reflection files, and
maintainer status never changes the bucket.

The reflection-triage Operation is conditional before model launch: `status` launches none,
`investigate` launches only a zero-write analyzer, and `implement` selects exactly `fast-loop` or the
public nested planner route. Only triage fills the analysis, proposed resolution, and intervention
decision/rationale. The parent persists the validated result while preserving User Comments;
implementer policies are restricted to isolated reflection worktrees and authorized reflection paths.
Once a maintainer closes a reflection with `status: resolved` or `dismissed` plus a `resolution_note`,
the `close` action removes its document with `reflections_queue.py --remove-closed`; closure means
removal, and Git history keeps the record.
