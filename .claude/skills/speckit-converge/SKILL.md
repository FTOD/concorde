---
name: speckit-converge
description: Append remaining implementation work to the selected temporal task list.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: preset:concorde
user-invocable: true
disable-model-invocation: false
---

# Speckit Converge Skill

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Concorde Installed Workspace Gate

Before any hook, setup step, prerequisite check, or artifact access, run `.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase converge` from the target
project root and parse its canonical JSON. Stop on any status other than `resolved` or `selected`. Use
the returned `workspace.feature_directory`, `workspace.feature_design`, `workspace.feature_implementation`, durable `workspace.*_dir` fields,
`workspace.attempt_dir`, plan-phase paths, and `workspace.attempt_state` as the sole path authority.
Require Protocol v9 `workspace.workspace_kind`, `workspace.feature_id`, `workspace.providing_module`,
`workspace.parent_context`, and bounded `workspace.siblings`. Treat `workspace.module_summary` and
`workspace.module_design` as navigation references that are never loaded implicitly: read `module.md`
only where a phase names it as bounded context, and open the module `design.md` only for a specific
recorded detail and cite it. When `workspace_kind` is `subfeature`,
read the parent `feature_design` and `feature_implementation` only as aggregate durable context. Never load a
sibling design/implementation body or any parent/sibling `attempt/` artifact implicitly, and
write only through the selected sub-feature's returned paths.

Do not execute a later core helper that would re-resolve a root-level plan or task path. When a later
step says to run `.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase converge`, reuse or refresh this installed-adapter result. Derive `AVAILABLE_DOCS`
by checking the returned durable and temporal paths. For `plan` or `tasks`, create the returned
`attempt_dir` when absent and seed a missing artifact from the active `plan-template` or
`tasks-template` resolved by `specify preset resolve`; never create a feature-root compatibility copy.
For `checklist`, resolve `checklist-template` separately through the same public preset resolver.

## Pre-Execution Checks

**Check for extension hooks (before convergence)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_converge` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `$speckit-git-commit`.
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):

    ```text
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **Mandatory hook** (`optional: false`):

    ```text
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Goal.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.

- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Goal

Close the gap between what a feature's specification, accepted realization, active implementation plan,
and tasks call for and what the codebase currently implements. Read root `design.md` as durable intent,
root `implementation.md` as the accepted realization baseline (the placeholder means no accepted
baseline), and the active
`attempt/plan.md` plus `attempt/tasks.md` as the chosen delivery approach (with the
constitution as governing constraints), then assess the current
state of the code, determine which requirements, acceptance criteria, plan decisions, and
existing tasks are unmet, incomplete, or only partially satisfied, and **append each piece
of remaining work as a new, traceable task** at the bottom of `tasks.md` so that
`$speckit-implement` can complete it. This command MUST run only after
`$speckit-implement` has run on the current `tasks.md`, and after `$speckit-tasks` has produced a complete `tasks.md`.

This is **not** a diff tool and does **not** track changes. It assesses the present state
of the code relative to the feature's artifacts — no git, no branch comparison, no history.

## Operating Constraints

**APPEND-ONLY, NEVER REWRITE**: The command's **only** writes are appending a new
`## Phase N: Convergence` section to `tasks.md` and appending to the project reflection log
(`workspace.reflections`, per Reflection Recording below). It MUST NOT:

- modify `abstract.md`, feature `design.md`, feature `implementation.md`, `plan.md`, or any module `module.md`/`design.md` in any way;
- rewrite, renumber, reorder, or delete any existing task (including tasks from a prior
  Convergence phase);
- modify, create, or delete any application code — completing the appended tasks is the
  job of `$speckit-implement`.

When the codebase already satisfies everything, the command MUST leave `tasks.md`
**byte-for-byte unchanged** (no empty Convergence header) and report a clean result.

**Constitution Authority**: The project constitution (`.specify/memory/constitution.md`) is
**non-negotiable**. Code that violates a MUST principle is the highest-severity finding and
produces a corresponding remediation task. If the constitution is an unfilled template,
skip constitution checks gracefully rather than failing.

## Execution Steps

### 1. Initialize Convergence Context

Run `.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase converge` once from repo root and parse JSON for FEATURE_DIR, FEATURE_DESIGN, FEATURE_IMPLEMENTATION, IMPL_PLAN, TASKS, and AVAILABLE_DOCS. Use the returned absolute paths:

- SPEC = FEATURE_DESIGN
- IMPLEMENTATION = FEATURE_IMPLEMENTATION
- PLAN = IMPL_PLAN
- TASKS = TASKS
- CONSTITUTION = `.specify/memory/constitution.md` (if present)
If `design.md`, `implementation.md`, `plan.md`, or `tasks.md` is missing, STOP with a clear, actionable message naming the
prerequisite command to run (`$speckit-specify` for a missing spec, `$speckit-plan` for a missing plan,
`$speckit-tasks` for missing tasks). Do not produce partial output.
For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact:

**From design.md:**

- Functional Requirements (FR-###)
- Success Criteria (SC-###) — include only items requiring buildable work; exclude
  post-launch outcome metrics and business KPIs
- User Stories and their Acceptance Scenarios
- Edge Cases (if present)
- Required feature diagrams, their core/supplemental roles, textual counterparts, and any explicit sufficiency rationale

**From implementation.md:**

- Accepted module/feature collaboration and scenario realization (the placeholder means no accepted
  baseline)
- Durable implementation decisions and evidence references
- Known limitations that remain part of the current baseline

**From plan.md:**

- Architecture/stack choices and technical decisions
- Data Model references
- Phases and named touch-points (files/components the plan says will be created or edited)
- Technical constraints

**From tasks.md:**

- Task IDs (to compute the next ID and next phase number)
- Descriptions, phase grouping, and referenced file paths

**From constitution (if not an unfilled template):**

- Principle names and MUST/SHOULD normative statements

### 3. Build the Intent Inventory

Create an internal model (do not echo raw artifacts):

- **Requirements inventory**: one stable key per FR-### / SC-### / user-story acceptance
  scenario (e.g. `US1/AC2`), plus the plan decisions and constitution principles that
  impose buildable obligations.
- **Code-scope map**: from the file paths named in `plan.md` and `tasks.md`, plus a keyword
  search for the concepts each requirement describes, derive the set of source files and
  components in scope for assessment. Bound the assessment to these — do **not** infer
  scope beyond what the artifacts define.

### 4. Assess the Codebase and Classify Findings

For each item in the intent inventory, inspect the current code in scope and produce a
`Finding` only where there is a gap. Classify every finding by **gap type**:

- **`missing`**: the required work is absent from the code entirely.
- **`partial`**: the work exists but does not yet fully satisfy the requirement /
  acceptance criterion / plan decision.
- **`contradicts`**: the code does something that conflicts with stated intent or a
  constitution MUST principle.
- **`unrequested`**: the code contains work not called for by the spec, plan, or tasks
  (surfaced for awareness — converge does **not** delete code, it only appends a task to
  review/justify or remove it).

Treat a missing required core component view, multiple core views, a non-architecture core view, or
missing, stale, unvalidated, or textually/contractually inconsistent required feature diagrams
as buildable gaps. Append work for `diagrams/` placement, declaration in `design.md`, maintained Archify
JSON, prose alignment, contract references, delivery, automatic feature-page embedding, truthful
visual-review evidence, and freshness; never append a task to hand-edit generated HTML or screenshots.

Each `Finding` records: a stable id, the `source-ref` it traces to, the `gap-type`, a
severity, and a short human-readable description with the evidence (the file/area observed).

**Edge cases:**

- **Little or no code yet**: treat the entire specified scope as `missing` remaining work
  rather than failing.
- **Nothing remains**: produce zero findings and follow the converged branch in Step 7.

### 5. Assign Severity

- **CRITICAL**: violates a constitution MUST principle, or a `missing`/`contradicts` gap
  that blocks baseline functionality of a P1 user story.
- **HIGH**: a `missing` or `partial` gap on a core functional requirement or acceptance
  criterion.
- **MEDIUM**: a `partial` gap on a secondary requirement, or an `unrequested` addition with
  unclear justification.
- **LOW**: minor partial gaps, polish, or low-risk `unrequested` additions.

### 6. Present the In-Session Findings Summary

Before appending anything, output a compact, severity-graded summary (no file writes yet):

## Convergence Findings

| ID | Gap Type | Severity | Source | Evidence | Remaining Work |
|----|----------|----------|--------|----------|----------------|
| F1 | missing  | HIGH     | FR-008 | Example: no append-only guard detected in path/to/module.py when writing tasks.md | Add append-only enforcement |

**Summary metrics:**

- Requirements / acceptance criteria checked
- Plan decisions checked
- Constitution principles checked (or "skipped — template")
- Findings by gap type (missing / partial / contradicts / unrequested)
- Findings by severity

### 7. Append Convergence Tasks (or report converged)

**If there are one or more actionable findings** (`tasks_appended` outcome):

Append to the **end** of `tasks.md`, per the append contract:

1. Scan all existing task IDs; let `M` be the maximum. Determine the next phase number `N`
   (highest existing phase + 1).
2. Write a single new section header `## Phase N: Convergence`.
3. Emit one checklist item per actionable finding, ordered CRITICAL/HIGH first, assigning
   zero-padded IDs `T{M+1:03d}, T{M+2:03d}, …`:

   ```markdown
   - [ ] T042 <imperative description> per <source-ref> (<gap-type>)
   ```

   `<source-ref>` traces the task to its origin: e.g. `FR-003`, `SC-002`,
   `US1/AC2`, `plan: storage decision`, `Constitution II`.

   `<gap-type>` is one of `missing`, `partial`, `contradicts`, `unrequested`.

   Constitution-violation tasks MUST be emitted first and described as
   `CRITICAL`.
4. Never reuse or renumber existing IDs. If a prior Convergence phase exists, add a new,
   separately-numbered one below it — do not touch the old one.
5. When execution surfaced rationale, alternatives, or implementation detail worth keeping, append a
   task that records it inside the attempt (`attempt/research.md` or
   `attempt/validation.md`) so delivery can carry it forward. Never append a task that edits
   `abstract.md`, feature `design.md`, feature `implementation.md`, or any module `module.md`/`design.md`.
6. Treat an `open` reflection entry attributed to this feature with `Effect: deferred` as candidate
   remaining work only when it is genuine remaining work of this feature's specification; never
   append work for `dismissed` entries or for entries attributed to other features, and never
   append a task that edits the log's maintainer-set statuses.

**If there are no actionable findings** (`converged` outcome):

- Do **not** modify `tasks.md` at all — no empty phase header.
- Report: **"✅ Converged — the implementation satisfies the spec, plan, and tasks."**
- Include the summary counts of what was checked.

### 8. Provide Next Actions (Handoff)

- On `tasks_appended`: state how many tasks were appended under which phase, and recommend
  running `$speckit-implement` to complete them; note that a follow-up converge
  run will find fewer or no remaining items.
- On `converged`: recommend proceeding to review / opening a PR. No further implement pass
  is needed for this feature's specified scope.
- In both cases end with `Reflections added: <identifiers or none> · open for this feature: <count>`.

## Reflection Recording

Every phase after specification records the difficulties and problems it meets in the project's one
reflection log: the maintained file returned as `workspace.reflections`
(`<specification_root>/reflections.md`). It is never per feature or per attempt, and no operation
removes it.

- **When**: whenever this phase cannot follow the specification, the accepted design reference, an
  existing implementation it depends on, the installed guidance, the level's architecture, or the
  plan as written, or must assume, work around, defer, or stop — record it in this phase, before the
  completion report, not later. A problem met and solved within the phase is still recorded.
- **Where**: ordinary recording writes only `workspace.reflections`. If the file does not exist,
  create it first from the template resolved by `specify preset resolve reflections-template`.
  Append a new entry or matching occurrence; never change or reuse an existing `R-NNN` identifier,
  delete an entry, or reverse a maintainer-set status or note as part of ordinary recording.
- **Centralized authority**: `workspace.reflections` is the only file that may persist a
  reflection entry or its `R-NNN` identity, status, note, or occurrences. Never copy or cite that
  reflection identity or entry content into attempt artifacts, feature/module documents, contracts,
  diagrams, code, or tests; those artifacts may state independently verified facts without
  reflection identity. Triage plans and completion reports may refer to an identifier for transient
  coordination, but they never become a second reflection record.
- **What**: one `### R-NNN · <short title>` entry (the next unused identifier) with the fields, in
  order, `Phase` (this phase), `Date`, `Feature` (`workspace.feature_id`), `Kind`
  (`specification`, `architecture`, `guidance`, `tooling`, `environment`, or `implementation`),
  `Concerns` (a stable ID or project-relative path anywhere in the project — another feature, its
  design reference or code, a module, a contract, an instruction, a tool), `Expected`, `Observed`,
  `Effect` (`assumed`, `worked-around`, `deferred`, or `blocked`), `Action`, `Improvement`, and
  `Status: open`. The grammar is fixed by the log template and checked by
  `speckit.concorde.validate` (`CONCORDE-REFLECT-001` to `-004`).
- **Never fix in place**: a problem with `abstract.md`, feature `design.md`, feature `implementation.md`, any `module.md`, a
  contract, a view, a diagram, or another feature's code or tests is recorded, not edited; the
  owning phase or the maintainer changes that source later.
- **Update, don't duplicate**: when ordinary recording finds the same problem — recorded by any phase
  on any feature — add a line under its `- **Occurrences**:` list
  (`<phase> <date> <feature-id> — <context>`) instead of a new entry. Never change a `Status` or
  `Note` a maintainer set.
- **Maintained reconciliation**: `workspace.reflections` is maintained docs/specs. An explicitly
  requested rename or documentation correction MAY rewrite existing entry text and references, but
  MUST preserve each exact `R-NNN` identifier, identifier uniqueness, required field structure,
  maintainer-owned status decision, occurrence identity, and problem meaning; renamed `Feature` and
  `Concerns` values MUST resolve, and the complete log MUST pass `speckit.concorde.validate`.
  Ordinary problem recording does not implicitly authorize this reconciliation.
- **Bounded**: recording never requires opening another root's `attempt/`; cite the other
  feature by stable ID or path.
- **Hygiene**: no secrets, credentials, or bulk output — cite the evidence path instead; keep
  `Expected`, `Observed`, and `Action` under about 150 words together.
- **Report**: end the completion report with `Reflections added: <identifiers or none> · open for
  this feature: <count>` (`workspace.reflections_open` at phase start plus the open entries added).

### 9. Check for extension hooks

After producing the result, check if `.specify/extensions.yml` exists in the project root.

- If it exists, read it and look for entries under the `hooks.after_converge` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- Report the convergence outcome (`converged` or `tasks_appended`) in-session before listing
  any hooks, so users can decide whether to run optional follow-up commands.
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `$speckit-git-commit`.
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):

    ```text
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **Mandatory hook** (`optional: false`):

    ```text
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.

- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
