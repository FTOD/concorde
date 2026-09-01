---
name: speckit-implement
description: Execute all tasks in the selected feature attempt workspace.
argument-hint: "Optional implementation guidance or task filter"
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: preset:concorde
user-invocable: true
disable-model-invocation: false
---

# Speckit Implement Skill

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Concorde Installed Workspace Gate

Before any hook, setup step, prerequisite check, or artifact access, run `python3 .specify/extensions/concorde/scripts/python/workspace.py --phase implement` from the target
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
Bind `CHECKLISTS_DIR` to the returned `workspace.checklists_dir`; never derive it from `FEATURE_DIR`.

Do not execute a later core helper that would re-resolve a root-level plan or task path. When a later
step says to run `python3 .specify/extensions/concorde/scripts/python/workspace.py --phase implement`, reuse or refresh this installed-adapter result. Derive `AVAILABLE_DOCS`
by checking the returned durable and temporal paths. For `plan` or `tasks`, create the returned
`attempt_dir` when absent and seed a missing artifact from the active `plan-template` or
`tasks-template` resolved by `specify preset resolve`; never create a feature-root compatibility copy.
For `checklist`, resolve `checklist-template` separately through the same public preset resolver.

## Pre-Execution Checks

**Check for extension hooks (before implementation)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_implement` key
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

1. Run `python3 .specify/extensions/concorde/scripts/python/workspace.py --phase implement` from repo root and parse FEATURE_DIR, ATTEMPT_DIR, FEATURE_ABSTRACT, FEATURE_DESIGN, FEATURE_IMPLEMENTATION, IMPL_PLAN, TASKS, and AVAILABLE_DOCS. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if `CHECKLISTS_DIR/` exists):
   - Treat checklist markers as a read-only gate: scan checkbox state, report status, and ask before proceeding when needed; do NOT modify checklist files or markers
   - `CHECKLISTS_DIR/requirements.md` is the built-in spec-quality checklist maintained by `$speckit-specify` and `$speckit-clarify`; custom checklists generated by `$speckit-checklist` are reviewer-owned requirements-quality review artifacts
   - For custom checklists, `[x]` means the reviewer determined the requirements-quality criterion is satisfied; it does NOT mean implementation work is complete
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Checked items: Lines matching `- [X]` or `- [x]`
     - Unchecked items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Checked | Unchecked | Status |
     |-----------|-------|---------|-----------|--------|
     | ux.md     | 12    | 12      | 0         | ✓ PASS |
     | test.md   | 8     | 5       | 3         | ✗ FAIL |
     | security.md | 6   | 6       | 0         | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 unchecked items
     - **FAIL**: One or more checklists have unchecked items

   - **If any checklist has unchecked items**:
     - Display the table with unchecked item counts
     - **STOP** and ask: "Some checklists have unchecked items. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are checked**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **ORIENTATION ONLY**: Read FEATURE_ABSTRACT as the selected feature's bounded summary; it never
     substitutes for FEATURE_DESIGN.
   - **REQUIRED**: Read FEATURE_DESIGN for behavioral authority and FEATURE_IMPLEMENTATION for the accepted
     realization baseline (the placeholder means no accepted baseline). Implement the plan's delta
     without editing `abstract.md`, feature `design.md`, feature `implementation.md`, or any module `module.md`/`design.md`; promotion belongs
     only to the explicit Concorde delivery command after all tasks are complete. Record
     rationale, alternatives, and implementation detail discovered during execution inside the
     attempt (`ATTEMPT_DIR/research.md` or `ATTEMPT_DIR/validation.md`) so delivery
     can carry them into feature `implementation.md` and the module `design.md`. Record every
     difficulty or problem met while executing — including existing code or tests of another
     feature that disagree with that feature's design reference (an `implementation` entry whose
     `Concerns` names that feature; never edit its sources) — in the project reflection log per
     Reflection Recording below, in the same phase, before the completion report.
   - **REQUIRED**: Read TASKS (`ATTEMPT_DIR/tasks.md`) for the complete task list and execution plan
   - **REQUIRED**: Read IMPL_PLAN (`ATTEMPT_DIR/plan.md`) for tech stack, architecture, and file structure
   - **IF EXISTS**: Read `ATTEMPT_DIR/data-model.md` for entities and relationships
   - **IF EXISTS**: Read `FEATURE_DIR/contracts/` for durable API specifications and test requirements
   - **IF EXISTS**: Read `ATTEMPT_DIR/research.md` for technical decisions and constraints
   - **IF EXISTS**: Read .specify/memory/constitution.md for governance constraints
   - **IF EXISTS**: Read `ATTEMPT_DIR/quickstart.md` for integration scenarios
   - **IF REFERENCED**: Read feature-owned Archify JSON beside the durable `design.md` and its textual
     explanation. Treat generated HTML and visual receipts as reproducible evidence, never as source.
   - **BOUNDARY**: Do not load unrelated deeper architecture. Follow only plan/task paths and a
     deliberately opened, cited module `design.md`; parent/sibling attempts and sibling bodies remain
     excluded.

4. **Project Setup Verification**:
   - **REQUIRED**: Treat repository/tool detection and setup-file inspection as read-only by
     default. Before creating or extending an ignore file or changing tool configuration, identify
     one dependency-ready executable task that explicitly supplies all of:
     - its stable task ID;
     - its requirement, acceptance-outcome, or named plan-section trace token;
     - the detected tool;
     - the exact project-relative setup file being changed; and
     - an action authorizing the required creation or edit.
   - Plan content may explain why a tool is relevant but cannot independently authorize a setup
     mutation. Repository/tool detection alone MUST NOT authorize a write. When no qualifying task
     exists, preserve every setup file byte-for-byte, report the missing task coverage, and continue
     or stop according to whether the dependency-ready task can proceed without that setup. Never
     synthesize authorization from repository detection.

   **Read-Only Detection & Authorized Mutation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (inspect
     `.gitignore` if so; mutate it only through the task-bound gate above):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker is named in plan.md → inspect `.dockerignore`
   - Check if .eslintrc* exists → inspect `.eslintignore`
   - Check if eslint.config.* exists → inspect the config's `ignores` entries
   - Check if .prettierrc* exists → inspect `.prettierignore`
   - Check if .npmrc or package.json exists → inspect `.npmignore` when publishing is in scope
   - Check if terraform files (*.tf) exist → inspect `.terraformignore`
   - Check if helm charts are present → inspect `.helmignore`

   **If the setup file already exists**: Inspect it for essential patterns; append a missing critical
   pattern only when the qualifying executable task names that exact target and authorizes the edit
   **If the setup file is missing**: Create it only when the qualifying executable task names that
   exact target and authorizes creation; otherwise preserve project setup byte-for-byte

   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `*.dll`, `autom4te.cache/`, `config.status`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

6. Execute implementation following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

7. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation
   - **Feature diagrams**: Reject any declaration that designates a sequence, workflow, data-flow, or
     lifecycle diagram as `role: core`. The optional single core view must use Archify
     `architecture` and show stable components and interactions; dynamic views are
     `role: supplemental`. When a task changes one, update the maintained JSON and textual
     counterpart together; run Archify showcase validation after each candidate edit and delivery at
     completion; run visual checks when the environment supports them, inspect captures before
     claiming perceptual review, and record skipped/pending truthfully. Keep
     `meta.legend.mode: hidden` in every maintained Concorde diagram. Keep the source under
     `diagrams/`, declare it in `design.md`, and verify provenance, generated freshness, and automatic
     feature-page embedding.

### Evidence before completion

For every executable task, write or update its compact Attempt Evidence in
`ATTEMPT_DIR/validation.md` before changing its task marker to `[X]`. The evidence MUST name:

- the task ID and requirement/acceptance trace;
- the verification command or check actually run;
- the outcome (`passed`, `failed`, or truthfully `skipped`);
- the relevant artifact or project-relative evidence path; and
- every material limitation on what the check proves.

Only a `passed` proportionate check authorizes completion. A task with missing evidence, a skipped
required check, or failed verification MUST remain unchecked; do not reinterpret intent, test
existence, or a structurally valid diagram as implementation proof.

At implementation start and completion, record a protected-authority SHA-256 comparison in
`ATTEMPT_DIR/validation.md` for the selected durable trio, any returned parent durable trio, module
summary/reference, and canonical bounded sibling-summary JSON. Do not hash sibling bodies. Any
unexpected protected-authority change stops the phase before further task completion and is recorded
as a problem in `workspace.reflections`.

8. Progress tracking and error handling:
   - Report progress after each completed task
   - Before marking a task failed, and before any halt, record the problem in the project reflection
     log (Reflection Recording below); a halt gets `Effect: blocked` with the stop reason in `Action`
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT** For completed tasks, first satisfy Evidence before completion, then mark the task
     `[X]` in the tasks file.

9. Completion validation:
   - Verify all required tasks are completed
   - Check that implemented features match the original specification
   - Validate that tests pass and coverage meets requirements
   - Confirm the implementation follows the technical plan
   - Confirm every required feature diagram is text-aligned, declared from `diagrams/`, validated,
     freshly delivered, embedded on the canonical feature page, and not being used as the authority
     for behavior or contracts

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `$speckit-tasks` first to regenerate the task list.

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

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_implement`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_implement` key.
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

Report final status with summary of completed work, then the line
`Reflections added: <identifiers or none> · open for this feature: <count>`.

## Done When

- [ ] All tasks in tasks.md completed and marked `[X]`
- [ ] Implementation validated against specification, plan, and test coverage
- [ ] Durable `implementation.md` and every module `module.md`/`design.md` were not updated and `attempt/` was not removed automatically
- [ ] Extension hooks dispatched or skipped according to the rules in Mandatory Post-Execution Hooks above
- [ ] Completion reported to user with summary of completed work
