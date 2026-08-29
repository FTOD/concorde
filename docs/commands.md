---
title: Commands and Installed Surfaces
sidebar_position: 7
---

# Commands and Installed Surfaces

Concorde has two command families. Nine familiar Spec Kit phases continue to own feature delivery;
five Concorde-specific surfaces manage architecture, selected-workspace validation, acceptance, and
workflow questions. Four are deterministic runtime-backed operations. `ask` is a read-only procedure
followed directly by the coding agent.

In an agent integration, names such as `$speckit-plan` or `$speckit-concorde-context` are **skills or
slash commands invoked in the agent conversation**. They are not commands to paste into Bash. The
installed instructions may direct the agent to run actual shell or Python programs as part of the
workflow.

The normative command behavior is defined by
[Feature 001](../specs/concorde/features/001-concorde-workflow/design.md); distribution of the
installed surfaces is defined by
[Feature 003](../specs/concorde/features/003-install-concorde-speckit/design.md).

## Concorde-specific operations

Feature operations use Feature Workspace Protocol v8 (acceptance proposal v6) over Architecture
Source Profile 4. Features are created and selected through the
normal Spec Kit lifecycle (see [Creating and selecting a feature](#creating-and-selecting-a-feature)
below); Concorde adds no creation or selection command. `impl.accept` accepts either valid level
while operating on exactly one lifecycle root. `context` reports containment summaries separately
from cross-module refinement, and `validate` rejects a third feature level.

Agent integrations may render dots as hyphens. The examples below use Codex-style skill names.

### `$speckit-concorde-ask <question>`

Use at any lifecycle stage when the uncertainty is about Concorde itself: what a concept means, when
to use a command, where an artifact belongs, which source is authoritative, or how the workflow
applies to a named module or feature in the current project.

The agent reads the smallest relevant installed sources under `.specify/extensions/concorde/` and
`.specify/presets/concorde-core/`. For project-specific questions it additionally reads only the
needed constitution, module summaries (`module.md`) and feature abstracts (`abstract.md`) first, then
one-level architecture and contract sources; it opens a `design.md` only for a requirement's exact
wording and a module `design.md` or feature `implementation.md` only when the question asks for implementation detail,
rationale, or accepted realization, and cites each file it opens. Its Markdown answer cites
project-relative paths and distinguishes framework rules, project observations, inference, and
uncertainty. Ambiguous questions receive one focused clarification instead of guessed project facts.

Unlike the four operations below, `ask` invokes no launcher or Python runtime. It never changes
selection, files, generated output, or lifecycle state, and a recommended command remains advice
until you invoke it separately.

### `$speckit-concorde-init`

Use once when a Spec Kit project has no configured Concorde project architecture. It proposes four
top-level specification files:
`.concorde/config.json` (Architecture Source Profile 4), a `module.md` summary in the required
shape, a seeded `design.md` design reference, and a first level view at
`<root>/architecture/diagrams/level-view.json`, plus any accepted initial contracts under
`<root>/architecture/contracts/`. Review the proposal before approval; it does not silently overwrite
existing maintained content.

The result names the workflow mechanics explicitly: Skills are the maintainer-facing interface,
Scripts perform deterministic operations, and Workspace Files distinguish durable sources, temporal
`attempt/` memory, and generated projections. These are not automatically created as product modules.
When `.concorde/config.json` already resolves a complete root package, init returns `unchanged` with
the current root paths, children, features, and contracts instead of comparing it with starter text.

Do not use it to create every module in advance. Decompose only when another abstraction level has a
meaningful responsibility and boundary.

### `$speckit-concorde-context <module-or-feature-id>`

Use before deciding feature ownership, reviewing a boundary, or giving an agent architectural
context for implementation. A module target returns that module and its immediate level, with
`summary` and `design_reference` paths and the `diagrams` list (every diagram beneath the module's
`architecture/diagrams/`) as navigation references; externals and current-level scenarios are drawn
from all of those diagrams. It never expands the body of a module `design.md` or feature
`implementation.md`. A feature target resolves through the module at which it is
specified and additionally returns feature workspace paths (`abstract.md`, `design.md`, `implementation.md`, and
the attempt), declared feature diagrams, relevant contract content, evidence, and architecture
readiness (whose `affected_views` list every diagram of the module).
When the project reflection log exists, both targets return `reflections` (its path and the open
entry count per feature) and feature summaries carry `reflections_open`.

The runtime output is automatically available to the agent that invoked the skill. The operation is
read-only and does not select the feature. Conversation context may retain the result temporarily,
but future sessions should retrieve it again.

The actual POSIX launcher used underneath the skill is:

```bash
.specify/extensions/concorde/scripts/bash/concorde.sh \
  context module.example --format json
```

Running the launcher manually returns canonical JSON; the skill adds agent interpretation and
presentation.

### Creating and selecting a feature

Concorde has no feature-creation command. Create a feature with the normal `$speckit-specify` phase
after setting `SPECIFY_FEATURE_DIRECTORY` to the canonical feature root inside the Concorde
hierarchy: `<module directory>/features/NNN-<short-name>` for a top-level feature, or
`<parent feature root>/subfeatures/NNN-<short-name>` for one immediate sub-feature.

```bash
# a top-level feature of the api module
export SPECIFY_FEATURE_DIRECTORY=specs/example/architecture/modules/api/features/002-observe-health

# an immediate sub-feature of feature 001-checkout
export SPECIFY_FEATURE_DIRECTORY=specs/example/features/001-checkout/subfeatures/003-capture-payment
```

Then, in the agent conversation:

```text
$speckit-specify Describe the feature's required behavior and why it matters.
```

The Concorde specify addendum authors `abstract.md` and `design.md` and seeds adjacent placeholder
`implementation.md`, which states that no realization has been accepted yet, and persists the root to
`.specify/feature.json`. Record the
feature's identity and placement in design front matter (`id`, `module`, and `parent_feature` for
a sub-feature), register it in the module's `features` list (or the parent's `subfeatures` list),
then run `$speckit-concorde-validate`. Validation deterministically checks registration, canonical
path, two-level containment, and identity.

Selection is plain Spec Kit selection: `.specify/feature.json` `feature_directory`, written by
specify or set explicitly with `export SPECIFY_FEATURE_DIRECTORY=<feature root>` (the standard Spec
Kit scripts persist it). Concorde adds no selection command and no second selection store. Before
every normal phase the Concorde workspace adapter resolves and validates the selected root: safe
path, canonical `abstract.md`/`design.md`/`implementation.md` trio with no legacy names, workspace
kind, parent context and sibling summaries for a sub-feature, durable and temporal paths, the
`module.md` and `design.md` of the module at which the feature is specified (`providing_module`) as
navigation references, and `attempt_state`. A non-empty
`attempt/` attempt appears as `attempt_state: active`; there is no separate resume
step—decide whether to continue that attempt or accept or archive it.

### `$speckit-concorde-validate [path-or-id]`

Use after architecture, contract, feature metadata, diagram, or evidence changes; use it again before
acceptance. With no target it validates the configured package. A path or stable ID requests a safely
bounded validation scope.

Validation is deterministic and read-only. A successful runtime exit can still contain warnings;
errors produce an invalid result. It reports unknown evidence rather than treating structurally
valid sources as proof of implementation agreement.

Beyond identity, hierarchy, contract, scenario, view, and evidence rules, it checks the module
summary shape (required sections, a structure link to at least one level view or a leaf rationale, inventory
tables, a reachable design reference), the reading budget (`CONCORDE-SUMMARY-005`, a warning that
never changes the status), and the presence of a real `design.md` beside every `module.md`
(`CONCORDE-MODULE-002`). Among the view and layout rules, every diagram under a module's
`architecture/diagrams/` must be referenced from that level's `module.md`, `design.md`, or the
reflection log (`CONCORDE-VIEW-006`); every maintained module or feature Archify source must set
`meta.legend.mode` to `hidden` (`CONCORDE-VIEW-007`); and legacy layout is reported: an `architecture.json`,
`contracts/`, or `modules/` directly at a module root or a `view`/`architecture_view` front-matter
field (`CONCORDE-LAYOUT-010`), and a child module outside `<parent>/architecture/modules/<name>/`
(`CONCORDE-LAYOUT-011`). At each feature root it checks the abstract shape—exactly the five sections
in order (`CONCORDE-ABSTRACT-001`), a structure link or inline sketch (`CONCORDE-ABSTRACT-002`), and
`Logic` rules citing requirement IDs that exist in `design.md` (`CONCORDE-ABSTRACT-003`)—its reading
budget (`CONCORDE-ABSTRACT-004`, a warning), and the durable trio: a missing `implementation.md`
(`CONCORDE-LAYOUT-005`), legacy `spec.md`/`tldr.md` names (`CONCORDE-LAYOUT-007`), a legacy
`implementation/` attempt directory (`CONCORDE-LAYOUT-008`), or a missing `abstract.md`
(`CONCORDE-LAYOUT-009`).

### `$speckit-concorde-impl-accept [feature-id-or-root]`

Use only when the selected implementation attempt is task-complete, all existing checklist items are
satisfied, evidence has been reviewed, and the maintainer accepts the result as a milestone.

The skill first asks the runtime for eligibility, then the agent drafts candidate feature
`implementation.md` and, when the attempt produced implementation detail or rationale worth keeping, a full
replacement `design.md` for the module at which the feature is specified. The runtime returns the
digest-bound proposal location and exact cleanup target; the digest covers the current module
`design.md`. Nothing is changed until the maintainer explicitly approves those exact bytes and
paths. Successful apply writes feature `implementation.md`, amends module `design.md` when proposed,
and removes the complete `attempt/` directory as one atomic operation, reporting digests for
both documents; stale or unsafe proposals change nothing, and `abstract.md`, `design.md`, `module.md`, and
the project reflection log are never edited. Eligibility summarizes the feature's reflection entries
by status; the candidate must cite every open one among its known limitations or apply refuses with
`CONCORDE-ACCEPT-012`.

## Normal Spec Kit phases under Concorde

The `concorde-core` preset replaces the agent instructions for these phases so selected-workspace
resolution happens before any phase can choose a legacy flat path. It does not create a second
planning or implementation engine. It also carries six templates: `spec-template`, `plan-template`,
and `tasks-template` append Concorde guidance to Spec Kit's own templates, while `abstract-template`,
`implementation-template`, and `reflections-template` are whole documents that a phase resolves with
`specify preset resolve <name>`; they have no composed mirror under `.specify/templates/`. Every
phase after specification appends the problems it meets to the project reflection log
(`workspace.reflections`, seeded from `reflections-template`) and ends its report with the entries
added and the feature's open count.

| Skill | Run it when | Concorde path behavior |
|---|---|---|
| `$speckit-specify` | Creating or revising required behavior and representative scenarios | Authors root `abstract.md` and `design.md` together; seeds placeholder `implementation.md` for a new root and preserves an existing one byte-for-byte; review state goes under `attempt/checklists/` |
| `$speckit-clarify` | Important behavioral ambiguity remains before planning | Encodes answers into `design.md` and updates the abstract wherever it summarized the changed behavior; keeps checklist state temporary |
| `$speckit-checklist` | You need a requirements-quality review focused on a domain such as contracts, security, or UX | Reads durable context, the abstract included, and writes only `attempt/checklists/*.md` |
| `$speckit-plan` | Behavior and architectural boundaries are ready for one implementation proposal | Reads root `design.md` and feature `implementation.md` with module `module.md` as bounded context (the abstract orients only; module `design.md` only deliberately); writes plan artifacts under `attempt/`; records unresolved problems in the project reflection log |
| `$speckit-tasks` | The plan is ready to become dependency-ordered executable work | Writes `attempt/tasks.md` |
| `$speckit-analyze` | Tasks exist and you want a read-only consistency check before coding | Compares the durable trio with the active plan/tasks, reporting any abstract statement that `design.md` does not make and the feature's open reflection entries (flagging stale ones); edits nothing except appending to the reflection log |
| `$speckit-implement` | The reviewed plan and tasks are ready to execute | Works from the selected durable sources, with feature `implementation.md` as the accepted baseline, and the active attempt |
| `$speckit-converge` | Code exists and you need to discover what remains unbuilt | Assesses code against intent and appends missing work to the same tasks file; an open, deferred reflection entry of the feature is candidate work only when genuine |
| `$speckit-taskstoissues` | The active work should be executed as external issues | Converts the selected attempt's tasks without changing their authority |

A common order is:

```text
specify → clarify → checklist → plan → tasks → analyze
        → implement → converge → validate → accept
```

The order is not a blind pipeline. `clarify` and custom checklists are used when needed; validation
may run repeatedly; convergence can add tasks that require another implementation pass. Acceptance is
never automatic.

## What actually runs

The installed workflow has four distinct layers:

1. **Package-neutral command Markdown** defines the procedure and behavior independent of any agent
   UI.
2. **An installed skill or slash command** presents that definition to the active coding-agent
   integration. It instructs the agent; it is not the Python implementation.
3. **A workspace adapter or portable launcher** resolves phase paths or locates the installed
   extension runtime using project-relative paths.
4. **The Concorde Python runtime** performs deterministic initialization, selected-workspace
   resolution, bounded-context projection, validation, and acceptance controls.

For a normal Spec Kit phase, the agent invokes the workspace adapter, obtains the selected durable
and temporary paths, and continues the normal phase. For one of the four Concorde-specific
operations, the agent invokes a portable launcher, which calls the Python runtime and returns
canonical JSON. For `ask`, the agent follows the installed Markdown directly and returns cited prose
without execution.

Repository-local `.agents/` skills are useful while Concorde develops itself, but users receive the
supported command surfaces from the installed preset and extension. Editing only a checkout-local
skill does not change the distributed framework.

## Short decision guide

| Situation | Next operation |
|---|---|
| You are unsure how Concorde works, when to use a command, or where an artifact belongs | `concorde-ask` |
| No root architecture exists | `concorde-init` |
| You do not know where the behavior belongs in the hierarchy | `concorde-context` and architecture review |
| Placement is known and the feature is new | `specify` with `SPECIFY_FEATURE_DIRECTORY` at the canonical feature root |
| The feature exists but normal phases target something else | Set `SPECIFY_FEATURE_DIRECTORY` or edit `.specify/feature.json`, then rerun the phase |
| Behavior is unclear | `specify` or `clarify` |
| Behavior is clear but no delivery approach exists | `plan` |
| The plan exists but is not executable | `tasks` |
| Tasks may not cover the durable intent | `analyze` |
| Approved tasks are ready | `implement` |
| Code may still be incomplete | `converge`, then implement remaining tasks |
| Architecture or evidence may be inconsistent | `concorde-validate` |
| The completed result is accepted as a milestone | `concorde-impl-accept` |
