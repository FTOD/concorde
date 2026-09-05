---
id: module.concorde.lifecycle
kind: module
parent: module.concorde
modules: []
features:
  - feature.lifecycle.specify-behavior
  - feature.lifecycle.plan-attempt
  - feature.lifecycle.execute-and-reconcile
  - feature.lifecycle.deliver-attempt
  - feature.lifecycle.fast-loop
  - feature.lifecycle.standard-development-loop
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-lifecycle-system-overview.html
---

# Architecture: Lifecycle

## Responsibility

Carry one selected feature from specification through permission-bounded planning, dependency-ordered
tasks, reconciled implementation, deterministic validation gates, and cleanup-only delivery inside
one committed-base isolated worktree, including the bounded fast loop. Normative evolution of the
Concorde repository's own Protocol is excluded.

## Boundary

Lifecycle owns the eleven lifecycle leaf Skill prompts (specify, clarify, checklist, tasks, analyze,
implement, converge, taskstoissues, deliver, fast-loop, and the internal plan-author), the two paired
Operations (`concorde-plan`, a context → author graph, and `concorde-standard-dev-loop`, a specify →
nested plan → tasks/implement → validate/deliver graph), the temporal attempt and its plan/tasks/
checklist formats, Delivery Proposal 9, and the cleanup-only delivery Tool. It does not own Protocol 13
resolution or deterministic validation rules (`module.concorde.understanding`), the LangGraph runtime,
policy compiler, process launcher, or public projection (`module.concorde.capabilities`), reflection
semantics (`module.concorde.reflections`), or product code.
The root `feature.concorde.evolve-protocol` owns normative Concorde Protocol changes and runs outside
every Lifecycle Skill, Operation, attempt, and delivery.
Before any lifecycle mutation, `module.concorde.capabilities` enforces the default linked-worktree
boundary; lifecycle never imports primary-worktree dirty state into a feature workspace.

## Operation Contract Boundary

This module owns two concrete instances of `entity.concorde.operation`: `concorde-plan` and
`concorde-standard-dev-loop`, each with one associated Skill and one primary `operation.py`.
It owns the domain meanings of `concorde-plan-context@1`, `concorde-plan-author-context@1`,
`concorde-plan-result@1`, and the standard-loop input/result, defined in the providing features.
Understanding owns resolved planning context; Capabilities owns common transport and enforcement.

Data flow is standard-loop input → explicit plan input → typed context/author handoff →
typed plan result → tasks/implementation → validation/delivery evidence. An Operation invocation is
one run; an attempt is feature-owned temporal state that can span several runs. Delivery invalidates
attempt artifact refs. The shared service implements JSON admission and typed mappings; each
Operation keeps its literal topology and one primary Python boundary.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.lifecycle.plan-input` | type | concorde-plan-context@1 caller fields: feature_path, request, constraints, and optional supporting source_artifacts; distinct from Understanding's internal Skill. | `concept:concorde-plan-context@1` |
| `entity.lifecycle.plan-author-input` | type | concorde-plan-author-context@1: original task plus the typed resolved planning context. | `concept:concorde-plan-author-context@1` |
| `entity.lifecycle.plan-result` | type | concorde-plan-result@1: selected feature identity, source digest, attempt path, and authored artifact references. | `concept:concorde-plan-result@1` |
| `entity.lifecycle.standard-loop-input` | type | concorde-standard-dev-loop-context@1: selected feature path and development intent/constraints. | `concept:concorde-standard-dev-loop-context@1` |
| `entity.lifecycle.standard-loop-result` | type | concorde-standard-dev-loop-result@1: selected feature identity, completed direct capabilities, and cleanup outcome. | `concept:concorde-standard-dev-loop-result@1` |
| `entity.lifecycle.specify-skill` | document | Public leaf prompt that authors or revises one direct feature's outcome, interfaces, usage, requirements, and architecture zoom; invokes Tools but never orchestrates Skills. | `skills/concorde-specify/SKILL.md` |
| `entity.lifecycle.clarify-skill` | document | Public leaf prompt that resolves material ambiguity in one direct feature file before planning proceeds. | `skills/concorde-clarify/SKILL.md` |
| `entity.lifecycle.checklist-skill` | document | Public leaf prompt that generates and revises one feature's temporal requirements-quality checklist. | `skills/concorde-checklist/SKILL.md` |
| `entity.lifecycle.tasks-skill` | document | Public leaf prompt that generates dependency-ordered, test-first, traced tasks for one selected attempt. | `skills/concorde-tasks/SKILL.md` |
| `entity.lifecycle.analyze-skill` | document | Public leaf prompt that reports cross-artifact consistency of one feature, its architecture, and its attempt without mutation. | `skills/concorde-analyze/SKILL.md` |
| `entity.lifecycle.implement-skill` | document | Public leaf prompt that executes every dependency-ready task, reconciling code, tests, and specification with proportionate evidence. | `skills/concorde-implement/SKILL.md` |
| `entity.lifecycle.converge-skill` | document | Public leaf prompt that appends remaining verified work discovered during implementation to one active task list. | `skills/concorde-converge/SKILL.md` |
| `entity.lifecycle.taskstoissues-skill` | document | Public leaf prompt that converts one attempt's dependency-ordered task list into tracked issues. | `skills/concorde-taskstoissues/SKILL.md` |
| `entity.lifecycle.deliver-skill` | document | Public leaf prompt that validates and removes exactly one completed attempt under Delivery Proposal 9. | `skills/concorde-deliver/SKILL.md` |
| `entity.lifecycle.fast-loop-skill` | document | Public leaf prompt that reconciles one eligible, small, already-specified change directly, without creating an attempt. | `skills/concorde-fast-loop/SKILL.md` |
| `entity.lifecycle.plan-author-skill` | document | Internal unprojected leaf prompt that authors the temporal plan, research, data model, quickstart, and initial tasks from a resolved planning-context receipt, writing only the selected attempt and authorized reflections. | `skills/concorde-plan-author/SKILL.md` |
| `entity.lifecycle.plan-operation` | program | Public two-stage context → author planning LangGraph that dispatches a bounded-context leaf before the internal plan-author leaf. | `operations/concorde-plan/operation.py` |
| `entity.lifecycle.plan-operation-skill` | document | Installed public planning invocation, policy, and failure contract paired with the planning graph. | `operations/concorde-plan/SKILL.md` |
| `entity.lifecycle.standard-dev-loop` | program | Four-stage specify → nested plan → tasks → deliver LangGraph over six direct public capability occurrences. | `operations/concorde-standard-dev-loop/operation.py` |
| `entity.lifecycle.standard-dev-loop-skill` | document | Installed invocation, ordering, nested-planner, and failure contract paired with the standard graph. | `operations/concorde-standard-dev-loop/SKILL.md` |
| `entity.lifecycle.delivery` | program | Proposes and applies digest-bound Delivery Proposal 9 removal of one complete attempt. | `src/concorde/lifecycle/delivery.py` |
| `entity.lifecycle.attempt` | directory | Temporary plan/tasks/research/checklists/validation memory keyed by exact stable feature ID. | `concept:.concorde/attempts/<stable-feature-id>` |
| `entity.lifecycle.delivery9` | schema | Digest-bound proposal/result schema for removing one complete attempt. | `concept:Delivery Proposal 9` |
| `entity.lifecycle.plan-template` | document | Temporal planning format grounded in feature, architecture, code, tests, risks, and evidence. | `templates/plan-template.md` |
| `entity.lifecycle.tasks-template` | document | Dependency-ordered traced task format with test-first and evidence gates. | `templates/tasks-template.md` |
| `entity.lifecycle.checklist-template` | document | Reviewer-owned requirements-quality checklist format. | `templates/checklist-template.md` |
| `entity.lifecycle.tests` | test | Topology, policy-narrowing, evidence-grammar, and delivery-safety evidence for every lifecycle phase. | `tests/concorde/lifecycle` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.lifecycle.plan-operation` | `reads_from` | `entity.lifecycle.plan-input` | validates one plan input object; inherited project configuration remains separate. |
| `entity.lifecycle.plan-author-skill` | `reads_from` | `entity.lifecycle.plan-author-input` | receives original task plus validated context, with no opaque prior-result string. |
| `entity.lifecycle.plan-operation` | `generates` | `entity.lifecycle.plan-result` | exposes one domain result to its parent after context and author succeed. |
| `entity.lifecycle.standard-dev-loop` | `reads_from` | `entity.lifecycle.standard-loop-input` | maps explicit task fields into the nested plan input after specification. |
| `entity.lifecycle.standard-dev-loop` | `reads_from` | `entity.lifecycle.plan-result` | verifies identity, source digest, and attempt refs before tasks/implementation. |
| `entity.lifecycle.standard-dev-loop` | `generates` | `entity.lifecycle.standard-loop-result` | returns the terminal domain result only after validated delivery. |
| `entity.lifecycle.plan-operation` | `composes` | `module.concorde.understanding` | Dispatches understanding's internal bounded-context leaf as its read-only first stage. |
| `entity.lifecycle.plan-operation` | `composes` | `entity.lifecycle.plan-author-skill` | Sequences the internal plan-authoring leaf as its second stage with the context result as prior input. |
| `entity.lifecycle.plan-operation-skill` | `documents` | `entity.lifecycle.plan-operation` | Supplies the installed public planning invocation, policy, and failure contract. |
| `entity.lifecycle.standard-dev-loop` | `composes` | `entity.lifecycle.specify-skill` | Runs specification as the first direct stage. |
| `entity.lifecycle.standard-dev-loop` | `composes` | `entity.lifecycle.plan-operation` | Dispatches the public planning Operation as one opaque nested stage without flattening its internals. |
| `entity.lifecycle.standard-dev-loop` | `composes` | `entity.lifecycle.tasks-skill` | Runs task generation as part of the tasks/implement stage. |
| `entity.lifecycle.standard-dev-loop` | `composes` | `entity.lifecycle.implement-skill` | Runs implementation as part of the tasks/implement stage. |
| `entity.lifecycle.standard-dev-loop` | `composes` | `module.concorde.understanding` | Dispatches understanding's validate leaf as part of the validate/deliver stage. |
| `entity.lifecycle.standard-dev-loop` | `composes` | `entity.lifecycle.deliver-skill` | Runs delivery as the closing occurrence of the validate/deliver stage. |
| `entity.lifecycle.standard-dev-loop-skill` | `documents` | `entity.lifecycle.standard-dev-loop` | Supplies the installed four-stage invocation, ordering, and failure contract. |
| `entity.lifecycle.plan-operation` | `depends_on` | `module.concorde.capabilities` | Builds its LangGraph, compiles per-leaf policy, and receives its enforced launch from the shared operation runtime. |
| `entity.lifecycle.standard-dev-loop` | `depends_on` | `module.concorde.capabilities` | Builds its LangGraph, compiles per-leaf policy, and receives its enforced launch from the shared operation runtime. |
| `entity.lifecycle.specify-skill` | `calls` | `module.concorde.understanding` | Resolves Protocol 13 workspace context, then reruns it once a new stable ID is authored. |
| `entity.lifecycle.implement-skill` | `calls` | `module.concorde.understanding` | Resolves attempt/code context and invokes deterministic validation Tools during reconciliation. |
| `entity.lifecycle.analyze-skill` | `calls` | `module.concorde.understanding` | Reads bounded feature, architecture, and attempt context without mutation. |
| `entity.lifecycle.fast-loop-skill` | `calls` | `module.concorde.understanding` | Resolves the anchor feature and every explicitly discovered affected feature before mutation. |
| `entity.lifecycle.deliver-skill` | `calls` | `entity.lifecycle.delivery` | Invokes the native delivery Tool to propose, then apply, cleanup. |
| `entity.lifecycle.delivery` | `calls` | `module.concorde.understanding` | Reruns deterministic project validation before revalidating removal eligibility. |
| `entity.lifecycle.delivery` | `validates` | `entity.lifecycle.attempt` | Checks task/checklist completion, evidence, digest, and safe removal paths before applying Proposal 9. |
| `entity.lifecycle.delivery` | `implements` | `entity.lifecycle.delivery9` | Realizes the digest-bound proposal/result schema. |
| `entity.lifecycle.specify-skill` | `writes_to` | `entity.concorde.specification` | Authors or revises the direct feature file. |
| `entity.lifecycle.clarify-skill` | `writes_to` | `entity.concorde.specification` | Resolves ambiguity directly inside the existing direct feature file. |
| `entity.lifecycle.specify-skill` | `writes_to` | `entity.lifecycle.attempt` | Seeds the requirements-quality checklist once workspace resolution confirms the authored stable ID. |
| `entity.lifecycle.checklist-skill` | `writes_to` | `entity.lifecycle.attempt` | Writes the temporal requirements-quality checklist. |
| `entity.lifecycle.converge-skill` | `writes_to` | `entity.lifecycle.attempt` | Appends newly discovered verified work to the active task list. |
| `entity.lifecycle.taskstoissues-skill` | `reads_from` | `entity.lifecycle.attempt` | Converts the current dependency-ordered task list into tracked issues without changing it. |
| `entity.lifecycle.analyze-skill` | `reads_from` | `entity.lifecycle.attempt` | Reports plan, task, and checklist consistency without mutation. |
| `entity.lifecycle.plan-author-skill` | `writes_to` | `entity.lifecycle.attempt` | Writes the plan, research, data model, quickstart, and initial tasks only into the selected attempt. |
| `entity.lifecycle.implement-skill` | `writes_to` | `entity.lifecycle.attempt` | Checks completed tasks and appends one evidence block per task. |
| `entity.lifecycle.implement-skill` | `writes_to` | `entity.concorde.source-code` | Changes only task-authorized implementation paths. |
| `entity.lifecycle.implement-skill` | `writes_to` | `entity.concorde.tests` | Records required test-first evidence beside the code it proves. |
| `entity.lifecycle.fast-loop-skill` | `writes_to` | `entity.concorde.specification` | Directly reconciles affected architecture and feature text for one eligible small change. |
| `entity.lifecycle.fast-loop-skill` | `writes_to` | `entity.concorde.source-code` | Directly reconciles affected code for the same eligible change. |
| `entity.lifecycle.fast-loop-skill` | `writes_to` | `entity.concorde.tests` | Directly reconciles affected tests for the same eligible change. |
| `entity.lifecycle.plan-author-skill` | `writes_to` | `module.concorde.reflections` | Records one unresolved problem per file without performing triage. |
| `entity.lifecycle.implement-skill` | `writes_to` | `module.concorde.reflections` | Records difficult choices and unresolved problems discovered during execution. |
| `entity.lifecycle.fast-loop-skill` | `writes_to` | `module.concorde.reflections` | Records a problem when preflight or evidence limits are discovered. |
| `entity.lifecycle.plan-author-skill` | `reads_from` | `entity.lifecycle.plan-template` | Uses the temporal planning format as a reference, not a prompt fragment. |
| `entity.lifecycle.tasks-skill` | `reads_from` | `entity.lifecycle.tasks-template` | Uses the dependency-ordered task format as a reference. |
| `entity.lifecycle.checklist-skill` | `reads_from` | `entity.lifecycle.checklist-template` | Uses the requirements-quality checklist format as a reference. |
| `entity.concorde.coding-agent` | `implements` | `entity.lifecycle.specify-skill` | Follows the installed prompt and stays within its declared read/write effects. |
| `entity.concorde.coding-agent` | `implements` | `entity.lifecycle.implement-skill` | Follows the installed prompt and stays within its declared read/write effects. |
| `entity.concorde.coding-agent` | `implements` | `entity.lifecycle.deliver-skill` | Follows the installed prompt and stays within its declared read/write effects. |
| `entity.concorde.coding-agent` | `implements` | `entity.lifecycle.fast-loop-skill` | Follows the installed prompt and stays within its declared read/write effects. |
| `entity.lifecycle.attempt` | `depends_on` | `entity.concorde.specification` | Stable feature identity relates temporal state to the durable direct feature file it targets. |
| `entity.lifecycle.plan-operation` | `tested_by` | `entity.lifecycle.tests` | Real LangGraph and policy-narrowing tests prove stage order, bounded context, and write scope. |
| `entity.lifecycle.standard-dev-loop` | `tested_by` | `entity.lifecycle.tests` | Nested and non-union tests prove public opacity and per-leaf handoff. |
| `entity.lifecycle.delivery` | `tested_by` | `entity.lifecycle.tests` | Proposal, digest, rollback, and retention cases establish cleanup safety. |

## Relationship Types

| Predicate | Direction and meaning |
|---|---|
| `composes` | From a controlling Operation to a direct canonical Skill, a public Operation, or the module that owns an internal leaf it dispatches, whose identity and result it sequences without taking ownership or flattening internals. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.lifecycle.specify` | Maintainer invokes `concorde-specify` for a new or revised direct feature. | First require the acting agent's linked worktree at the primary worktree's committed `HEAD` (or an explicit primary override) and exclude primary dirty state; resolve workspace context through `module.concorde.understanding`; for a new stable ID accept unavailable attempt fields on the first gate; author valid front matter and body; rerun the gate; write only the resolved checklist path into `entity.lifecycle.attempt`. | One validated direct feature file and, once selected, a seeded temporal checklist in the owned worktree. | `interface.concorde.specify` |
| `interaction.lifecycle.plan` | Maintainer or the standard loop invokes `concorde-plan` for one selected feature. | Before planning or attempt creation require the committed-base linked worktree; `entity.lifecycle.plan-operation` dispatches `module.concorde.understanding`'s bounded-context leaf; passes its read-only result to `entity.lifecycle.plan-author-skill`; the author writes only `entity.lifecycle.attempt` and authorized `module.concorde.reflections` entries. | Temporal plan and task artifacts in the owned worktree, or a bounded named failure leaving durable sources unchanged. | `interface.concorde.plan`, `contract.lifecycle.plan` |
| `interaction.lifecycle.implement` | Maintainer delegates an approved dependency-ordered attempt to `concorde-implement`. | `entity.lifecycle.implement-skill` resolves the attempt and protected sources through `module.concorde.understanding`; executes each dependency-ready task test-first; writes `entity.concorde.source-code` and `entity.concorde.tests`; records one evidence block per task and any problems in `entity.lifecycle.attempt` and `module.concorde.reflections`. | Reconciled sources with truthful task/evidence state, or dependents stopped after a failing task while prior evidence is preserved. | `interface.concorde.implement` |
| `interaction.lifecycle.deliver` | Maintainer invokes `concorde-deliver` for a selected feature with a complete attempt. | `entity.lifecycle.deliver-skill` calls `entity.lifecycle.delivery`; delivery revalidates tasks, checklists, evidence, and digest through `module.concorde.understanding`; verifies the safe canonical `entity.lifecycle.attempt` path; atomically removes exactly that attempt. | No-active-attempt state with every durable authority retained, or the full attempt preserved on any ineligibility. | `interface.concorde.deliver` |
| `interaction.lifecycle.standard-loop` | Maintainer invokes the installed `concorde-standard-dev-loop` Operation skill for normal feature work. | Reject normative Concorde Protocol evolution before construction; establish one committed-base linked worktree before the first mutating stage; then `entity.lifecycle.standard-dev-loop` resolves each direct occurrence and its launch through `module.concorde.capabilities`; runs specify, opaque plan, tasks/implement, validate/deliver in that same worktree; stops all downstream occurrences on any failure. | Four ordered stage groups of results in one isolated worktree, the correct completed prefix after a failure, or a pre-mutation route to `feature.concorde.evolve-protocol`. | `contract.lifecycle.standard-development-loop` |
| `interaction.lifecycle.fast-loop` | Maintainer explicitly requests one small, already-specified change. | Establish the committed-base linked worktree before mutation; `entity.lifecycle.fast-loop-skill` resolves the anchor and every explicitly discovered affected feature through `module.concorde.understanding`; rejects structural, interface, policy, Protocol-semantic, or other ambiguity; edits every bounded owner directly; runs proportional checks. | Exact changed sources with disclosed checks and evidence limits and no attempt, while primary dirty state remains untouched; a normal rejection redirects to the full lifecycle while Protocol evolution redirects to its root isolated-worktree feature. | `interface.concorde.fast-loop` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.lifecycle.specify-behavior` | Author or revise one direct feature's complete outcome, interfaces, usage, requirements, and architecture zoom in its sole feature file. |
| `feature.lifecycle.plan-attempt` | Resolve permission-bounded planning context and author one temporal plan and task scaffold for a selected feature without dependency internals. |
| `feature.lifecycle.execute-and-reconcile` | Execute every dependency-ready task and reconcile affected architecture, code, tests, and projections with proportionate evidence. |
| `feature.lifecycle.deliver-attempt` | Verify one complete attempt and atomically remove exactly its temporal workspace. |
| `feature.lifecycle.fast-loop` | Reconcile one eligible small already-specified change directly without creating an attempt. |
| `feature.lifecycle.standard-development-loop` | Run specify, nested bounded planning, tasks/implementation, and validation/delivery as one controlled four-stage Operation. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- `skills/<name>/SKILL.md` is the sole prompt authority for a leaf capability; installed files are
  generated projections.
- Leaf Skills never embed a multi-Skill LangGraph or duplicate another Skill's prompt body; only the
  two paired Operations compose ordered capabilities.
- Templates remain readable format references, not prompt fragments merged into Skill prompts.
- Direct capability topology is literal, mixed Skill/Operation, order-preserving, and acyclic;
  `concorde-standard-dev-loop` never flattens `concorde-plan`'s internal stages.
- Graph construction fails before execution when any direct leaf lacks a non-null launch factory or
  any nested Operation lacks an explicit enforcing dispatcher.
- Leaf effects remain owned by canonical Skill metadata; occurrence bindings and effective
  configuration may narrow but never widen them.
- The fast loop applies only when deterministic preflight establishes durable required behavior, no
  active attempt, and no structural, interface, policy, or normative Concorde Protocol change. A
  normal ineligible condition redirects to the full lifecycle; Protocol evolution redirects to the
  root isolated-worktree feature instead of mutating.
- Delivery removes exactly one selected stable-ID attempt after revalidating eligibility and digest;
  it creates no implementation narrative and amends no architectural intent.
- Every lifecycle phase is a use case of changing one feature; the Skills and Operations that realize
  a phase are owned here regardless of their physical directory.
- Lifecycle never hosts normative Concorde Protocol evolution: that root feature intentionally uses
  no Lifecycle Skill, Operation, attempt, checklist, or delivery.
- Every mutating Lifecycle entry uses one linked worktree from the primary worktree's exact committed
  `HEAD` before planning or control creation. Staged, unstaged, untracked, and ignored primary paths
  remain outside authority unless the maintainer explicitly names the primary-worktree exception.
