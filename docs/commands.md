---
title: Commands and Installed Surfaces
sidebar_position: 7
---

# Commands and Installed Surfaces

Concorde has two command families. Nine familiar Spec Kit phases continue to own feature delivery;
seven Concorde-specific surfaces manage architecture, nested workspace selection, validation,
hardening, and workflow questions. Six are deterministic runtime-backed operations. `ask` is a
read-only procedure followed directly by the coding agent.

In an agent integration, names such as `$speckit-plan` or `$speckit-concorde-context` are **skills or
slash commands invoked in the agent conversation**. They are not commands to paste into Bash. The
installed instructions may direct the agent to run actual shell or Python programs as part of the
workflow.

The normative command behavior is defined by
[Feature 001](../specs/concorde/features/001-concorde-workflow/spec.md); distribution of the
installed surfaces is defined by
[Feature 003](../specs/concorde/features/003-install-concorde-speckit/spec.md).

## Concorde-specific operations

Agent integrations may render dots as hyphens. The examples below use Codex-style skill names.

### `$speckit-concorde-ask <question>`

Use at any lifecycle stage when the uncertainty is about Concorde itself: what a concept means, when
to use a command, where an artifact belongs, which source is authoritative, or how the workflow
applies to a named module or feature in the current project.

The agent reads the smallest relevant installed sources under `.specify/extensions/concorde/` and
`.specify/presets/concorde-core/`. For project-specific questions it additionally reads only the
needed constitution, module, one-level architecture, contract, feature specification, and accepted
design sources. Its Markdown answer cites project-relative paths and distinguishes framework rules,
project observations, inference, and uncertainty. Ambiguous questions receive one focused
clarification instead of guessed project facts.

Unlike the six operations below, `ask` invokes no launcher or Python runtime. It never changes
selection, files, generated output, or lifecycle state, and a recommended command remains advice
until you invoke it separately.

### `$speckit-concorde-init`

Use once when a Spec Kit project has no Concorde root architecture. It proposes the root module,
configuration, contracts, and one-level view. Review the proposal before approval; it does not
silently overwrite existing maintained content.

Do not use it to create every module in advance. Decompose only when another abstraction level has a
meaningful responsibility and boundary.

### `$speckit-concorde-context <module-or-feature-id>`

Use before deciding feature ownership, reviewing a boundary, or giving an agent architectural
context for implementation. A module target returns that module and its immediate level. A feature
target resolves through its providing module and additionally returns feature workspace paths,
declared diagrams, relevant contract content, evidence, and architecture readiness.

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

### `$speckit-concorde-feature-create ...`

Use after bounded-context review has identified the providing module for new behavior. Supply the
module ID, stable feature ID, and short directory name. Concorde proposes placement and affected
architecture first; after approval it creates one nested feature root, establishes `spec.md` and
`design.md`, registers the feature, and selects it.

```text
$speckit-concorde-feature-create \
  --module-id module.example.checkout \
  --feature-id feature.example.checkout.refunds \
  --short-name checkout-refunds
```

Do not use it when the feature already exists; select the existing feature instead.

### `$speckit-concorde-feature-select <feature-id-or-root>`

Use before running normal phases on an existing nested feature. Selection validates the workspace
and atomically updates `.specify/feature.json`; subsequent Spec Kit commands derive all durable and
temporary paths from that record.

If a non-empty implementation attempt already exists, explicitly choose to resume it. Selection does
not create a second attempt or move artifacts to a flat feature directory.

### `$speckit-concorde-validate [path-or-id]`

Use after architecture, contract, feature metadata, diagram, or evidence changes; use it again before
hardening. With no target it validates the configured package. A path or stable ID requests a safely
bounded validation scope.

Validation is deterministic and read-only. A successful runtime exit can still contain warnings;
errors produce an invalid result. It reports unknown evidence rather than treating structurally
valid sources as proof of implementation agreement.

### `$speckit-concorde-feature-harden [feature-id-or-root]`

Use only when the selected implementation attempt is task-complete, all existing checklist items are
satisfied, evidence has been reviewed, and the maintainer accepts the result as a milestone.

The skill first asks the runtime for eligibility, then the agent drafts the candidate durable
`design.md`. The runtime returns a digest-bound proposal and exact cleanup target. Nothing is changed
until the maintainer explicitly approves those exact bytes and paths. Successful apply updates the
design and removes the complete `implementation/` directory; stale or unsafe proposals change
nothing.

## Normal Spec Kit phases under Concorde

The `concorde-core` preset replaces the agent instructions for these phases so selected-workspace
resolution happens before any phase can choose a legacy flat path. It does not create a second
planning or implementation engine.

| Skill | Run it when | Concorde path behavior |
|---|---|---|
| `$speckit-specify` | Creating or revising required behavior and representative scenarios | Updates root `spec.md`; preserves accepted `design.md`; review state goes under `implementation/checklists/` |
| `$speckit-clarify` | Important behavioral ambiguity remains before planning | Updates durable specification answers; keeps checklist state temporary |
| `$speckit-checklist` | You need a requirements-quality review focused on a domain such as contracts, security, or UX | Reads durable context and writes only `implementation/checklists/*.md` |
| `$speckit-plan` | Behavior and architectural boundaries are ready for one implementation proposal | Reads root `spec.md` and `design.md`; writes plan artifacts under `implementation/` |
| `$speckit-tasks` | The plan is ready to become dependency-ordered executable work | Writes `implementation/tasks.md` |
| `$speckit-analyze` | Tasks exist and you want a read-only consistency check before coding | Compares durable spec/design with the active plan/tasks; does not edit them |
| `$speckit-implement` | The reviewed plan and tasks are ready to execute | Works from the selected durable sources and active attempt |
| `$speckit-converge` | Code exists and you need to discover what remains unbuilt | Assesses code against intent and appends missing work to the same tasks file |
| `$speckit-taskstoissues` | The active work should be executed as external issues | Converts the selected attempt's tasks without changing their authority |

A common order is:

```text
specify → clarify → checklist → plan → tasks → analyze
        → implement → converge → validate → harden
```

The order is not a blind pipeline. `clarify` and custom checklists are used when needed; validation
may run repeatedly; convergence can add tasks that require another implementation pass. Hardening is
never automatic.

## What actually runs

The installed workflow has four distinct layers:

1. **Package-neutral command Markdown** defines the procedure and behavior independent of any agent
   UI.
2. **An installed skill or slash command** presents that definition to the active coding-agent
   integration. It instructs the agent; it is not the Python implementation.
3. **A workspace adapter or portable launcher** resolves phase paths or locates the installed
   extension runtime using project-relative paths.
4. **The Concorde Python runtime** performs deterministic initialization, feature placement and
   selection, bounded-context projection, validation, and hardening controls.

For a normal Spec Kit phase, the agent invokes the workspace adapter, obtains the selected durable
and temporary paths, and continues the normal phase. For one of the six Concorde-specific operations,
the agent invokes a portable launcher, which calls the Python runtime and returns canonical JSON. For
`ask`, the agent follows the installed Markdown directly and returns cited prose without execution.

Repository-local `.agents/` skills are useful while Concorde develops itself, but users receive the
supported command surfaces from the installed preset and extension. Editing only a checkout-local
skill does not change the distributed framework.

## Short decision guide

| Situation | Next operation |
|---|---|
| You are unsure how Concorde works, when to use a command, or where an artifact belongs | `concorde-ask` |
| No root architecture exists | `concorde-init` |
| You do not know which module owns the behavior | `concorde-context` and architecture review |
| Ownership is known and the feature is new | `concorde-feature-create` |
| The feature exists but normal phases target something else | `concorde-feature-select` |
| Behavior is unclear | `specify` or `clarify` |
| Behavior is clear but no delivery approach exists | `plan` |
| The plan exists but is not executable | `tasks` |
| Tasks may not cover the durable intent | `analyze` |
| Approved tasks are ready | `implement` |
| Code may still be incomplete | `converge`, then implement remaining tasks |
| Architecture or evidence may be inconsistent | `concorde-validate` |
| The completed result is accepted as a milestone | `concorde-feature-harden` |
