---
description: "Analyze durable design and temporal attempt artifacts non-destructively."
scripts:
  py: .specify/extensions/concorde/scripts/python/workspace.py --phase analyze
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Concorde Installed Workspace Gate

Before any hook, setup step, prerequisite check, or artifact access, run `{SCRIPT}` from the target
project root and parse its canonical JSON. Stop on any status other than `resolved` or `selected`. Use
the returned `workspace.feature_directory`, `workspace.feature_abstract`, `workspace.feature_design`, `workspace.feature_implementation`, durable `workspace.*_dir` fields,
`workspace.attempt_dir`, plan-phase paths, and `workspace.attempt_state` as the sole path authority.
Require Protocol v9 `workspace.workspace_kind`, `workspace.feature_id`, `workspace.providing_module`,
`workspace.parent_context`, and bounded `workspace.siblings`. Treat `workspace.module_summary` and
`workspace.module_design` as navigation references that are never loaded implicitly: read `module.md`
only where a phase names it as bounded context, and open the module `design.md` only for a specific
recorded detail and cite it. When `workspace_kind` is `subfeature`, read
`parent_context.feature_abstract`, `parent_context.feature_design`, and
`parent_context.feature_implementation` only as aggregate durable context. Never load a
sibling design/implementation body or any parent/sibling `attempt/` artifact implicitly, and
write only through the selected sub-feature's returned paths.

Do not execute a later core helper that would re-resolve a root-level plan or task path. When a later
step says to run `{SCRIPT}`, reuse or refresh this installed-adapter result. Derive `AVAILABLE_DOCS`
by checking the returned durable and temporal paths. For `plan` or `tasks`, create the returned
`attempt_dir` when absent and seed a missing artifact from the active `plan-template` or
`tasks-template` resolved by `specify preset resolve`; never create a feature-root compatibility copy.
For `checklist`, resolve `checklist-template` separately through the same public preset resolver.

## Pre-Execution Checks

**Check for extension hooks (before analysis)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_analyze` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `$speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Goal.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

Every analysis hook is inside the same mutation budget as analysis. Before executing a mandatory
hook, require its maintained contract to be read-only except for the same required
`workspace.reflections` record; otherwise stop before invoking it and report the incompatible hook.

## Goal

Identify inconsistencies, duplications, ambiguities, and underspecified items across durable `design.md`, durable accepted `implementation.md`, and the active `attempt/plan.md` and `attempt/tasks.md` before implementation. This command MUST run only after `$speckit-tasks` has successfully produced a complete task list.

## Operating Constraints

**READ-ONLY EXCEPT REFLECTION RECORDING**: Do **not** modify any file except the project reflection
log (`workspace.reflections`). This phase may create that log from its resolved template when absent
and append a new entry or matching occurrence per Reflection Recording below; it never repairs,
reorders, renumbers, or deletes reflection content. Every other file MUST remain byte-identical. A
run that meets no recordable problem MUST make zero filesystem changes. Output a structured analysis
report. Offer an optional remediation plan (user must explicitly approve before any follow-up editing
commands would be invoked manually).

**Constitution Authority**: The project constitution (`.specify/memory/constitution.md`) is **non-negotiable** within this analysis scope. Constitution conflicts are automatically CRITICAL and require adjustment of the spec, plan, or tasks—not dilution, reinterpretation, or silent ignoring of the principle. If a principle itself needs to change, that must occur in a separate, explicit constitution update outside `$speckit-analyze`.

## Execution Steps

### 1. Initialize Analysis Context

Run `{SCRIPT}` once from repo root and parse JSON for FEATURE_DIR, FEATURE_DESIGN, FEATURE_IMPLEMENTATION, IMPL_PLAN, TASKS, and AVAILABLE_DOCS. Use the returned absolute paths:

- SPEC = FEATURE_DESIGN
- IMPLEMENTATION = FEATURE_IMPLEMENTATION
- PLAN = IMPL_PLAN
- TASKS = TASKS

Abort with an error message if any required file is missing (instruct the user to run missing prerequisite command).
For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact:

**From design.md:**

- Overview/Context
- Functional Requirements
- Success Criteria (measurable outcomes — e.g., performance, security, availability, user success, business impact)
- User Stories
- Edge Cases (if present)
- Feature-diagram roles, maintained JSON paths, textual counterparts, and sufficiency rationales

**From the project reflection log (`workspace.reflections`, when present):**

- Every entry whose `Feature` is the selected root: identifier, `Kind`, `Concerns`, `Effect`,
  `Status`, `Date`
- For each such entry, whether its `Concerns` or `Feature` source changed after its `Date`
  (deterministic proxy: `git log -1 --format=%cs -- <path>` later than `Date`, or a stable ID that
  no longer resolves) — such an entry is **stale**
- A malformed log is reported as a finding; it is never repaired here

**From abstract.md:**

- Every statement of purpose, functionality, structure, and logic, and every `FR-NNN` it cites (the abstract summarizes design.md and must not exceed it)

**From implementation.md:**

- Accepted realization baseline, durable decisions, scenario realization, traceability, and known limitations (the placeholder means no accepted baseline)

**From plan.md:**

- Architecture/stack choices
- Data Model references
- Phases
- Technical constraints

**From tasks.md:**

- Task IDs
- Descriptions
- Phase grouping
- Parallel markers [P]
- Referenced file paths

**From constitution:**

- Load `.specify/memory/constitution.md` for principle validation

### 3. Build Semantic Models

Create internal representations (do not include raw artifacts in output):

- **Requirements inventory**: For each Functional Requirement (FR-###) and Success Criterion (SC-###), record a stable key. Use the explicit FR-/SC- identifier as the primary key when present, and optionally also derive an imperative-phrase slug for readability (e.g., "User can upload file" → `user-can-upload-file`). Include only Success Criteria items that require buildable work (e.g., load-testing infrastructure, security audit tooling), and exclude post-launch outcome metrics and business KPIs (e.g., "Reduce support tickets by 50%").
- **User story/action inventory**: Discrete user actions with acceptance criteria
- **Accepted-realization inventory**: Durable implementation decisions, scenario realization,
  evidence, and limitations from feature `implementation.md`; preserve an explicit no-baseline state
- **Plan-decision inventory**: Named technical decisions, constraints, and planned touch-points from
  `attempt/plan.md`
- **Task coverage mapping**: Map each task to one or more requirements or stories (inference by keyword / explicit reference patterns like IDs or key phrases)
- **Constitution rule set**: Extract principle names and MUST/SHOULD normative statements

### 4. Detection Passes (Token-Efficient Analysis)

Focus on high-signal findings. Limit to 50 findings total; aggregate remainder in overflow summary.

Every reported item uses exactly one primary finding category from this required taxonomy:
`absent evidence`, `disagreement`, `ambiguity`, `duplication`, or `coverage gap`. The detection
passes below provide subtypes and evidence; do not collapse absent evidence into agreement or use
generic inconsistency when one of the five categories applies.

#### A. Duplication Detection

- Identify near-duplicate requirements
- Mark lower-quality phrasing for consolidation

#### B. Ambiguity Detection

- Flag vague adjectives (fast, scalable, secure, intuitive, robust) lacking measurable criteria
- Flag unresolved placeholders (TODO, TKTK, ???, `<placeholder>`, etc.)

#### C. Underspecification

- Requirements with verbs but missing object or measurable outcome
- User stories missing acceptance criteria alignment
- Tasks referencing files or components not defined in spec/plan

#### D. Constitution Alignment

- Any requirement or plan element conflicting with a MUST principle
- Missing mandated sections or quality gates from constitution

#### E. Coverage Gaps

- Requirements with zero associated tasks
- Tasks with no mapped requirement/story
- Success Criteria requiring buildable work (performance, security, availability) not reflected in tasks
- Required feature diagrams with no plan/tasks coverage for prose alignment, contract traceability,
  `diagrams/` placement, Archify validation, delivery, automatic feature-page embedding,
  visual-review status, or freshness

#### F. Inconsistency

- Terminology drift (same concept named differently across files)
- Data entities referenced in plan but absent in spec (or vice versa)
- Task ordering contradictions (e.g., integration tasks before foundational setup tasks without dependency note)
- Conflicting requirements (e.g., one requires Next.js while other specifies Vue)
- Feature diagram participants/interactions that conflict with textual scenarios or contracts, or
  diagram sources outside `diagrams/`, undeclared/unembedded diagrams, or generated projections
  treated as maintained authority
- More than one `role: core` diagram, a core diagram whose kind is not `architecture`, or a
  sequence/workflow/data-flow/lifecycle view presented as the feature's core component model

#### G. Abstract Disagreement

- An `abstract.md` statement that `design.md` does not support, or that contradicts a requirement,
  scope boundary, or success criterion: report it as `disagreement`, naming the disagreeing
  statement and the prevailing `design.md` requirement (`FR-NNN`/section; design.md wins; the
  abstract is fixed through `$speckit-specify` or
  `$speckit-clarify`, never by this command)
- A `Logic` rule citing an `FR-NNN` that `design.md` does not define, or a missing/extra/misordered
  abstract section

### 5. Severity Assignment

Use this heuristic to prioritize findings:

- **CRITICAL**: Violates constitution MUST, missing core spec artifact, or requirement with zero coverage that blocks baseline functionality
- **HIGH**: Duplicate or conflicting requirement, ambiguous security/performance attribute, untestable acceptance criterion
- **MEDIUM**: Terminology drift, missing non-functional task coverage, underspecified edge case
- **LOW**: Style/wording improvements, minor redundancy not affecting execution order

### 6. Produce Compact Analysis Report

Output a Markdown report (no file writes) with the following structure:

## Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A1 | Duplication | HIGH | design.md:L120-134 | Two similar requirements ... | Merge phrasing; keep clearer version |

(Add one row per finding; generate stable IDs prefixed by category initial.)

**Reflections:** (when the project log exists)

| Entry | Kind | Concerns | Effect | Status | Stale? |
|-------|------|----------|--------|--------|--------|

List every entry attributed to the selected feature; mark stale entries; end with
`Open for this feature: <count>` and, when a `deferred` open entry names genuine remaining work,
recommend `$speckit-converge`.

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|

**Constitution Alignment Issues:** (if any)

**Unmapped Tasks:** (if any)

**Metrics:**

- Total Requirements
- Total Tasks
- Coverage % (requirements with >=1 task)
- Ambiguity Count
- Duplication Count
- Critical Issues Count

### 7. Provide Next Actions

At end of report, output a concise Next Actions block:

- If CRITICAL issues exist: Recommend resolving before `$speckit-implement`
- If only LOW/MEDIUM: User may proceed, but provide improvement suggestions
- Provide explicit command suggestions: e.g., "Run $speckit-specify with refinement", "Run $speckit-plan to adjust architecture", "Manually edit tasks.md to add coverage for 'performance-metrics'"

### 8. Offer Remediation

Ask the user: "Would you like me to suggest concrete remediation edits for the top N issues?" (Do NOT apply them automatically.)

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

After reporting, check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_analyze` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `$speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

An after-analysis hook is also inside the analysis mutation budget and MUST satisfy the same
read-only-except-reflection contract before invocation.

## Operating Principles

### Context Efficiency

- **Minimal high-signal tokens**: Focus on actionable findings, not exhaustive documentation
- **Progressive disclosure**: Load artifacts incrementally; don't dump all content into analysis
- **Token-efficient output**: Limit findings table to 50 rows; summarize overflow
- **Deterministic results**: Rerunning without changes should produce consistent IDs and counts

### Analysis Guidelines

- **NEVER modify files other than `workspace.reflections`** (analysis may create or append/update
  that log only as specified by Reflection Recording; when it has nothing to record, it writes
  nothing)
- **NEVER propose editing `implementation.md` or any module `module.md`/`design.md`**; when analysis surfaces rationale, alternatives, or implementation detail worth keeping, recommend recording it inside the attempt (`attempt/research.md` or `attempt/validation.md`) so delivery can carry it forward
- **NEVER hallucinate missing sections** (if absent, report them accurately)
- **Prioritize constitution violations** (these are always CRITICAL)
- **Use examples over exhaustive rules** (cite specific instances, not generic patterns)
- **Report zero issues gracefully** (emit success report with coverage statistics)

## Context

$ARGUMENTS
