# Command reference

Installed Codex skills use hyphenated names such as `$speckit-plan`; other integrations may present
slash commands. All phase-sensitive commands resolve Feature Workspace Protocol 12 before accessing
paths.

## Framework commands

### `speckit.concorde.init`

Proposes and explicitly applies the root Profile 7 module hierarchy plus
`.concorde/reflections/log.md`. Apply is review-gated and
digest-bound. Existing configured projects return `unchanged`.

### `speckit.concorde.context <stable-id>`

Returns exactly one bounded module or feature context. Module output contains current-level entities,
relationships, interactions, children, features, externals, diagrams, and navigation. Feature output
contains `feature_path`, providing architecture, ancestry, related summaries, interface/zoom summaries,
attempt state, and source/test hints. Read-only.

### `speckit.concorde.validate [target]`

Runs deterministic Profile 7 validation and returns sorted findings, status, source digest, and
summary. Exit codes are 0 success, 1 invalid, 2 conflict, and 3 failed. Read-only.

### `speckit.concorde.ask <question>`

Answers from installed guidance and the smallest bounded project sources, with Basis and Sources.
It never invokes another command or mutates the workspace.

### `speckit.concorde.deliver [feature]`

Generates Proposal 8 and, under the same explicit invocation, applies it. Eligibility requires
complete tasks/checklists, passed evidence, current validation, safe real paths, and current digest.
Apply removes exactly one attempt and changes no durable/executable source.

## Spec Kit lifecycle commands modified by the preset

### `speckit.specify <description>`

Creates or revises one direct module `features/<NNN-name>.md` file. The file embeds interfaces and an
Architecture Zoom. New features reconcile the module's immediate feature inventory. Writes the
built-in requirements checklist under the returned attempt checklist directory. A missing feature's
first Protocol 12 response has unresolved/null attempt fields; after writing its stable ID, specify
reruns the resolver before creating the checklist and never derives the attempt key from the filename.

### `speckit.clarify [focus]`

Asks up to five high-impact questions and writes answers into the owning parts of the selected
feature file. Architecture identity conflicts are routed to module architecture instead of redefined.

### `speckit.checklist [focus]`

Creates a reviewer-owned requirements-quality checklist. Items judge clarity/completeness/
consistency/testability of English requirements; they do not represent product work.

### `speckit.plan [constraints]`

Creates the selected `.concorde/attempts/<stable-feature-id>/` and plans from feature file +
architecture + current code/tests. Writes only temporal plan/research/data-model/quickstart/
validation artifacts. Records provisional choices and unresolved conflicts in
`.concorde/reflections/log.md`.

### `speckit.tasks [constraints]`

Generates test-first tasks with stable IDs, exact paths, traces, dependencies, parallel markers, and
verification commands. Includes explicit architecture/feature/interface reconciliation where needed.

### `speckit.analyze`

Read-only semantic consistency, coverage, and delivery-readiness audit. It reports findings without
applying fixes.

### `speckit.implement`

Executes tasks phase-by-phase and records passed evidence before completion. May edit architecture,
feature files, code, tests, fixtures, projections, and public docs only through explicit traced
tasks.

### `speckit.converge`

Appends only remaining executable tasks after comparing current state/evidence with feature intent,
architecture, and plan. Preserves existing task history.

### `speckit.taskstoissues`

Groups tasks into dependency-aware issues while preserving IDs, traces, paths, ownership, and
acceptance checks. External creation occurs only when the invocation and integration authorize it.

### `speckit.fast-loop`

Direct no-attempt path for one eligible small change. Rejects active attempts, migrations, new
topology/types/compatibility policy, broad setup, destructive work, and multi-feature coordination.

## Hooks

Normal phases inspect `.specify/extensions.yml`. Enabled unconditional mandatory hooks execute and
gate completion; enabled unconditional optional hooks are presented; conditional hooks are left to
the hook executor. Hooks never expand a phase's source-authority or mutation boundary.

## Workspace fields

Protocol 12 groups fields into identity, direct feature/architecture context, temporal attempt
paths/state, process reflection state, and executable source/test context. Treat returned paths as
the only authority and related/ancestry summaries as navigation only.
