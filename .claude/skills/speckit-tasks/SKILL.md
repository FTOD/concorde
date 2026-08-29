---
name: speckit-tasks
description: Generate dependency-ordered tasks in the selected implementation workspace.
argument-hint: "Optional task generation constraints"
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: preset:concorde-core
user-invocable: true
disable-model-invocation: false
---

# Speckit Tasks Skill

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Concorde Installed Workspace Gate

Before any hook, setup step, prerequisite check, or artifact access, run `.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase tasks` from the target
project root and parse its canonical JSON. Stop on any status other than `resolved` or `selected`. Use
the returned `workspace.feature_directory`, `workspace.feature_spec`, `workspace.feature_design`, durable `workspace.*_dir` fields,
`workspace.implementation_dir`, plan-phase paths, and `workspace.implementation_state` as the sole path authority.
Require Protocol v5 `workspace.workspace_kind`, `workspace.feature_id`, `workspace.providing_module`,
`workspace.parent_context`, and bounded `workspace.siblings`. Treat `workspace.module_summary` and
`workspace.module_design` as navigation references that are never loaded implicitly: read `module.md`
only where a phase names it as bounded context, and open the module `design.md` only for a specific
recorded detail and cite it. When `workspace_kind` is `subfeature`,
read the parent `feature_spec` and `feature_design` only as aggregate durable context. Never load a
sibling specification/implementation body or any parent/sibling `implementation/` artifact implicitly, and
write only through the selected sub-feature's returned paths.

Do not execute a later core helper that would re-resolve a root-level plan or task path. When a later
step says to run `.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase tasks`, reuse or refresh this installed-adapter result. Derive `AVAILABLE_DOCS`
by checking the returned durable and temporal paths. For `plan` or `tasks`, create the returned
`implementation_dir` when absent and seed a missing artifact from the active `plan-template` or
`tasks-template` resolved by `specify preset resolve`; never create a feature-root compatibility copy.
For `checklist`, resolve `checklist-template` separately through the same public preset resolver.

## Pre-Execution Checks

**Check for extension hooks (before tasks generation)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_tasks` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `$speckit-git-commit`.
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
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

    Wait for the result of the hook command before proceeding to the Outline.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

1. **Setup**: Run `.venv/bin/python .specify/extensions/concorde/scripts/python/workspace.py --phase tasks` from repo root and parse FEATURE_DIR, IMPLEMENTATION_DIR, FEATURE_SPEC, FEATURE_DESIGN, IMPL_PLAN, TASKS, TASKS_TEMPLATE_CONTENT, TASKS_TEMPLATE, and AVAILABLE_DOCS. Path fields must be absolute when provided. `AVAILABLE_DOCS` contains feature-root-relative paths such as `implementation.md`, `implementation/research.md`, and `contracts/`. After a hardening, the task list lives in the fresh `implementation/` beneath the same root, never in a root-level copy. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents** using the returned paths:
   - **Required**: IMPL_PLAN (proposed tech stack, libraries, structure), FEATURE_SPEC (user stories with priorities), FEATURE_DESIGN (accepted realization baseline; the placeholder means no accepted baseline)
   - **Optional**: `IMPLEMENTATION_DIR/data-model.md` (entities), `FEATURE_DIR/contracts/` (durable interface contracts), `IMPLEMENTATION_DIR/research.md` (decisions), `IMPLEMENTATION_DIR/quickstart.md` (test scenarios)
   - **IF REFERENCED**: Load feature-owned Archify JSON beside `FEATURE_SPEC` as durable explanatory
     sources; do not confuse them with module-level `architecture.json` or generated HTML.
   - **IF EXISTS**: Load `.specify/memory/constitution.md` for project principles and governance constraints
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, libraries, project structure
   - Load spec.md and extract user stories with their priorities (P1, P2, P3, etc.)
   - Load the feature design.md and distinguish retained accepted realization from changes proposed by plan.md; when it is the placeholder, treat every planned decision as new work against no accepted baseline
   - Read the level's `module.md` as bounded architecture context; consult a module `design.md` only for a specific recorded detail and cite it
   - If data-model.md exists: Extract entities and map to user stories
   - If contracts/ exists: Map interface contracts to user stories
   - If research.md exists: Extract decisions for setup tasks
   - Generate tasks organized by user story (see Task Generation Rules below)
   - Generate dependency graph showing user story completion order
   - Create parallel execution examples per user story
   - Validate task completeness (each user story has all needed tasks, independently testable)
   - First generate a task that verifies any `role: core` diagram is the feature's single stable
     component-interaction view and uses Archify `architecture`; a sequence diagram can never satisfy
     that task. For every required core or `role: supplemental` diagram, generate tasks for aligned
     prose, scenario/contract traceability, maintained Archify JSON, showcase validation, HTML
     delivery, truthful visual-review status, freshness, and automatic embedding on the canonical
     feature page. Require its source under the feature's `diagrams/` directory. Do not create a task
     that edits generated HTML as intent.

4. **Generate TASKS (`IMPLEMENTATION_DIR/tasks.md`)**: Use TASKS_TEMPLATE_CONTENT (from the JSON output above) as the structure. For compatibility with older setup scripts that omit TASKS_TEMPLATE_CONTENT, read TASKS_TEMPLATE instead. Fill with:
   - Correct feature name from plan.md
   - Phase 1: Setup tasks (project initialization)
   - Phase 2: Foundational tasks (blocking prerequisites for all user stories)
   - Phase 3+: One phase per user story (in priority order from spec.md)
   - Each phase includes: story goal, independent test criteria, tests (if requested), implementation tasks
   - Final Phase: Polish & cross-cutting concerns
   - All tasks must follow the strict checklist format (see Task Generation Rules below)
   - Clear file paths for each task
   - Dependencies section showing story completion order
   - Parallel execution examples per story
   - Implementation strategy section (MVP first, incremental delivery)

## Reflection Recording

Every phase after specification records the difficulties and problems it meets in the project's one
reflection log: the maintained file returned as `workspace.reflections`
(`<specification_root>/reflections.md`). It is never per feature or per attempt, and no operation
removes it.

- **When**: whenever this phase cannot follow the specification, the accepted design reference, an
  existing implementation it depends on, the installed guidance, the level's architecture, or the
  plan as written, or must assume, work around, defer, or stop — record it in this phase, before the
  completion report, not later. A problem met and solved within the phase is still recorded.
- **Where**: append to `workspace.reflections`. If the file does not exist, create it first from the
  template resolved by `specify preset resolve reflections-template`. Append only; never rewrite,
  reorder, renumber, or delete entries.
- **What**: one `### R-NNN · <short title>` entry (the next unused identifier) with the fields, in
  order, `Phase` (this phase), `Date`, `Feature` (`workspace.feature_id`), `Kind`
  (`specification`, `architecture`, `guidance`, `tooling`, `environment`, or `implementation`),
  `Concerns` (a stable ID or project-relative path anywhere in the project — another feature, its
  design reference or code, a module, a contract, an instruction, a tool), `Expected`, `Observed`,
  `Effect` (`assumed`, `worked-around`, `deferred`, or `blocked`), `Action`, `Improvement`, and
  `Status: open`. The grammar is fixed by the log template and checked by
  `speckit.concorde.validate` (`CONCORDE-REFLECT-001` to `-004`).
- **Never fix in place**: a problem with `tldr.md`, `spec.md`, any `design.md`, any `module.md`, a
  contract, a view, a diagram, or another feature's code or tests is recorded, not edited; the
  owning phase or the maintainer changes that source later.
- **Update, don't duplicate**: when the log already holds the same problem — recorded by any phase
  on any feature — add a line under its `- **Occurrences**:` list
  (`<phase> <date> <feature-id> — <context>`) instead of a new entry. Never change a `Status` or
  `Note` a maintainer set.
- **Bounded**: recording never requires opening another root's `implementation/`; cite the other
  feature by stable ID or path.
- **Hygiene**: no secrets, credentials, or bulk output — cite the evidence path instead; keep
  `Expected`, `Observed`, and `Action` under about 150 words together.
- **Report**: end the completion report with `Reflections added: <identifiers or none> · open for
  this feature: <count>` (`workspace.reflections_open` at phase start plus the open entries added).

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_tasks`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_tasks` key.
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue to the Completion Report.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `$speckit-git-commit`.
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Mandatory hook** (`optional: false`) — **You MUST emit `EXECUTE_COMMAND:` for each mandatory hook**:
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

## Completion Report

Output the generated TASKS path and summary:
- Total task count
- Task count per user story
- Parallel opportunities identified
- Independent test criteria for each story
- Suggested MVP scope (typically just User Story 1)
- Format validation: Confirm ALL tasks follow the checklist format (checkbox, ID, labels, file paths)
- `Reflections added: <identifiers or none> · open for this feature: <count>` (see Reflection Recording)

Context for task generation: $ARGUMENTS

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story to enable independent implementation and testing.

**Tests are OPTIONAL**: Only generate test tasks if explicitly requested in the feature specification or if user requests TDD approach.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
4. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label
   - User Story phases: MUST have story label
   - Polish phase: NO story label
5. **Description**: Clear action with exact file path

**Examples**:

- ✅ CORRECT: `- [ ] T001 Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py`
- ✅ CORRECT: `- [ ] T012 [P] [US1] Create User model in src/models/user.py`
- ✅ CORRECT: `- [ ] T014 [US1] Implement UserService in src/services/user_service.py`
- ❌ WRONG: `- [ ] Create User model` (missing ID and Story label)
- ❌ WRONG: `T001 [US1] Create model` (missing checkbox)
- ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID)
- ❌ WRONG: `- [ ] T001 [US1] Create model` (missing file path)

### Task Organization

1. **From User Stories (spec.md)** - PRIMARY ORGANIZATION:
   - Each user story (P1, P2, P3...) gets its own phase
   - Map all related components to their story:
     - Models needed for that story
     - Services needed for that story
     - Interfaces/UI needed for that story
     - If tests requested: Tests specific to that story
   - Mark story dependencies (most stories should be independent)

2. **From Contracts**:
   - Map each interface contract → to the user story it serves
   - If tests requested: Each interface contract → contract test task [P] before implementation in that story's phase

3. **From Data Model**:
   - Map each entity to the user story(ies) that need it
   - If entity serves multiple stories: Put in earliest story or Setup phase
   - Relationships → service layer tasks in appropriate story phase

4. **From Setup/Infrastructure**:
   - Shared infrastructure → Setup phase (Phase 1)
   - Foundational/blocking tasks → Foundational phase (Phase 2)
   - Story-specific setup → within that story's phase

### Phase Structure

- **Phase 1**: Setup (project initialization)
- **Phase 2**: Foundational (blocking prerequisites - MUST complete before user stories)
- **Phase 3+**: User Stories in priority order (P1, P2, P3...)
  - Within each story: Tests (if requested) → Models → Services → Endpoints → Integration
  - Each phase should be a complete, independently testable increment
- **Final Phase**: Polish & Cross-Cutting Concerns

## Done When

- [ ] tasks.md generated with all phases, task IDs, and file paths
- [ ] Tasks implement the planned delta from the durable feature `design.md` and do not edit that file, `tldr.md`, `spec.md`, any module `module.md`, or any module `design.md` directly
- [ ] Every required feature diagram has complete source, validation, delivery, and freshness tasks
- [ ] Extension hooks dispatched or skipped according to the rules in Mandatory Post-Execution Hooks above
- [ ] Completion reported to user with task count, story breakdown, and MVP scope
