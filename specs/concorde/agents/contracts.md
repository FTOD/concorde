# Agent interfaces

This document gives the exact inventory, inputs, outputs and limits of every Agent. The
[entry](module.md) explains what the Agents are for; the typed stage values named here are defined
by the Harness, and the meaning of plans, tasks, findings and Issue decisions by their owning
Modules.

## Inventory

The `agents` Python package is the inventory:

| Name | Value |
| --- | --- |
| `agents.DOMAIN_AGENTS` | `spec_reviewer`, `context_assessor`, `planner`, `task_author`, `programmer`, `code_reviewer`, `issue_solver` |
| `agents.TASK_SUBAGENT_PROFILES` | `tester`, plus `maintenance-worker` when `agents/source/` exists |
| `agents.TASK_SUBAGENTS` | the names of those profiles |
| `agents.AGENTS` | the hyphenated Domain Agent names followed by the Task subagent names: nine in the source checkout, eight in an installed package |
| `agents.external_name(name)` | `concorde-` plus the hyphenated Domain Agent name, e.g. `concorde-task-author`; the name of the prepared native agent |

Each Domain Agent module `agents/<name>/__init__.py` exports `PROFILE` (a Harness worker profile),
`PUBLIC = False`, `CONTEXT_SELECTION = "bound"`, `DETERMINISTIC = False`, `USES = ()`,
`EXTERNAL_NAME` and `KIND = "agent"`. It exports no `STATE` or `run`: a Domain Agent is not an
Operation. Task subagent profiles are `TaskSubagentProfile` records with `name`, `prompt`, `tools`,
`extensions`, `source_only` and an optional `acceptance_role`; they are never worker profiles.

The user session has no profile and no inventory entry.

### Inventory metadata

The metadata of this document carries the extension `concorde.agents`: an array with one object per
Agent and exactly these string fields.

| Field | Values |
| --- | --- |
| `id` | the hyphenated Agent name |
| `family` | `domain` or `task` |
| `scope` | `distributed`, or `source-only` for a profile with `source_only` set |
| `registration` | `invocation` for Domain Agents (a one-off definition in each call's capsule), `project` for Task subagents (a definition under `.pi/agents/`) |
| `source` | the canonical instruction path: `agents/<name>/spec.md` or the Task subagent's prompt |

Package validation (rule `CONCORDE-SPEC-AGENTS-001`) requires exactly one registered document to
carry this extension, loads every Domain Agent profile and validates it, and compares the array with
the inventory, ignoring order. A malformed entry, a duplicate, a missing or extra Agent, or any
differing field is a finding, as is a Domain Agent directory under `agents/` that the inventory does
not list.

## Domain Agent invocation

A capability prepares every Domain Agent call; the user session invokes the returned call unchanged
through Pi's `subagent` tool.

- **Capsule.** The Host writes a fresh capsule directory holding `context.json`, copies of the
  admitted Spec, Protocol and reference files, a one-off agent file
  `.pi/agents/concorde-<name>.md`, and a child extension that supplies `report_issue` and, when
  granted, `run_checks`. The code-reviewer's capsule also holds read-only copies of the granted
  implementation files. The programmer instead receives the path of the actual candidate and the
  intended write paths, and reads and writes the real files there, never capsule copies.
- **Definition fields.** The prepared agent has `systemPromptMode: replace`, no inherited project
  or global context, no Skills, `defaultContext: fresh`, `allowNestedSubagents: false`, the
  profile's tools plus `report_issue`, and a timeout from the configured worker selection or else
  the profile. Its `acceptanceRole` is `writer` for the programmer and `read-only` otherwise.
- **Instructions.** `prompts/native/<name>.md` followed by `agents/<name>/spec.md`, rendered to
  `generated/native/<name>.md`; `generated/agents/<name>.md` holds the same bytes.
- **Result.** The Agent calls native structured output with exactly `invocation_id` (the issued
  identity) and `result`, a typed `concorde-agent-stage-result` or `concorde-review-stage-result`
  bound to the context identity in `context.json`. The Host admits it only after checking native
  completion and current inputs.

### Domain Agent profiles

Stage pairs: **stage** is `concorde-agent-stage-context` / `concorde-agent-stage-result`;
**review** is `concorde-review-stage-context` / `concorde-review-stage-result`.

| Agent | Phase, pair | Workspace | Reads | Writes | Stage inputs (required in bold) | Result fields | Tools | Timeout |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context-assessor | `context-solve`, stage | capsule | Spec context | none | none | `outcome`: `sufficient`, `spec_incomplete`, `unsupported`, `conflicting` | read, grep, find, ls | 1800 s |
| planner | `plan`, stage | capsule | Spec context, references | none | `concorde-plan-artifact` | `plan` | read, grep, find, ls | 1800 s |
| task-author | `tasks`, stage | capsule | Spec context, references | none | **`concorde-plan-artifact`**, **`concorde-task-identity-constraints`**, `concorde-implementation-task`, `concorde-review-result`, `concorde-task-scope-feedback` | `tasks` | read, grep, find, ls | 1800 s |
| programmer | `implementation`, stage | project | Spec context, implementation, references | implementation | **`concorde-implementation-task`**, `concorde-review-result` | `tasks` | read, grep, find, ls, edit, write, bash, run_checks | 3600 s |
| spec-reviewer | `spec-review`, review | capsule | Spec context | none | review input | review status | read, grep, find, ls | 1800 s |
| code-reviewer | `code-review`, review | project | Spec context, implementation, references | none | review input | review status | read, grep, find, ls, run_checks | 3600 s |
| issue-solver | `issue-solve`, stage | capsule | Spec context | none | **`concorde-issue-selection`** | `issue_decision` | read, grep, find, ls | 1800 s |

No profile declares network access or credentials. The code-reviewer's profile also lists `bash`,
which the native preparation removes for the `code-review` phase, so a native code-reviewer has no
shell.

### context-assessor

Decides whether the task can be carried out from the Module's complete Spec context. It sees the
names of implementation files but never their contents, and does not search elsewhere for missing
meaning. `sufficient` has no blockers; `spec_incomplete` carries real Issue receipts naming the
missing question and the blocked step; `unsupported` means the Spec settles that the task is
prohibited; `conflicting` means the Spec contradicts itself. It returns no documents, plan or tasks.

### planner

Runs only after an accepted `sufficient` assessment. It writes an actionable, contract-level plan
for the requested change from the Specs and the admitted external references alone, never from
code, and may name the realizations (and so the files) a piece of work concerns. It returns no
tasks or documents. A missing behavioural promise is reported as a gap instead of invented.

### task-author

Turns the accepted plan into a nonempty list of tasks, each with a new `id` outside the reserved set
in `concorde-task-identity-constraints`, a `target_id`, a `description`, observable `acceptance`
that cites relevant requirement or scenario identities, and `complete: false`. Acceptance covers
implementation only; later checks, reviews, readiness and delivery are never task conditions. With
a prior task list and a `concorde-review-result` it writes repair tasks for the blocking findings;
with `concorde-task-scope-feedback` it replaces a list that mixed implementation with later
responsibilities. It reads no code.

### programmer

Fulfils the supplied tasks in the actual candidate, writing only files the Module's realizations
bind, including pending entries. It never edits Specs, metadata, the registry, configuration,
control state or other worktrees. Every test it writes declares the scenarios it verifies, naming
only scenario identities in its context. It returns every task unchanged except `complete: true`
for fulfilled ones, and states which checks it ran and what it deferred to the Host because an
input was outside its grant. It never commits, reviews, marks ready or delivers. Partial edits stay
in the candidate after a failure or cancellation.

### spec-reviewer

Reads the Module's complete admitted Specs as a newcomer and checks them against representative
tasks derived from the request, including a mandatory check that every imported term is used with
its owner's meaning. It reports each concrete problem once through `report_issue` and returns
`no_findings` (with nonempty covered tasks and no Issues), `findings`, or `incomplete`.

### code-reviewer

Compares the granted implementation and the scoped changes with the complete admitted contracts,
runs the configured checks through `run_checks`, and reports concrete behaviour defects. A test
that declares a scenario of this Module but does not exercise it is a defect. Implementation outside
the grant belongs to other Modules' reviews. Results as for the spec-reviewer; unavailable evidence
is never a pass.

### issue-solver

Chooses the next bounded action for one selected Issue revision from the Spec context, bounded
feedback and at most five admitted duplicate candidates. `issue_decision` has exactly `action`,
`intent`, `rationale` and `duplicate_of`; `action` is one of `develop`, `spec-repair`, `verify`,
`resolved`, `duplicate`, `not-actionable` or `needs-decision`, and `duplicate_of` is set only for
`duplicate`. It reads no implementation, edits nothing and closes nothing; development and Spec
repair return to the user session, and verification is done by fresh reviewers.

## Task subagent interfaces

Distribution projects each Task subagent profile into `.pi/agents/<name>.md` with this front
matter, followed by the resolved prompt:

| Field | tester | maintenance-worker |
| --- | --- | --- |
| `tools` | read, grep, find, ls, test_command | read, grep, find, ls, bash, edit, write |
| `extensions` | `concorde-tester.ts` and the Concorde session entry to test | `concorde-maintenance.ts`, `concorde-brief-lifecycle.ts` |
| `acceptanceRole` | `read-only` | none |
| common | `systemPromptMode: replace`, `inheritProjectContext: false`, `inheritGlobalContext: false`, `inheritSkills: false`, `defaultContext: fresh`, `excludeTools: subagent`, `async: true`, `completionGuard: false` | same |
| installed in consumers | yes | no |

`test_command` takes `command` (a string of at most 32768 characters), `timeout` (1 to 3600
seconds, default 600) and `reports` (relative names of files under `CONCORDE_CHECK_REPORT_DIR` to
export). It runs the command in the Harness's operating-system read-only sandbox with fresh writable
scratch in `CONCORDE_CHECK_TMPDIR`, a private `/tmp` backed by that scratch, and existing host
`/tmp` inputs readable through `CONCORDE_TEST_HOST_TMP`. Before the scratch is removed, the Host
exports bounded output and the named reports to primary run evidence and returns a manifest; an
export failure is reported with the original result.

The `concorde-maintenance.ts` extension blocks every tool call when the working directory is not a
Concorde source checkout, and always blocks the `subagent` and `concorde` tools.

The maintenance-worker's progress messages carry a fenced `task-brief` JSON object with string
fields `goal`, `grant`, `stage`, `objective`, `blocker` (`"none"` when there is none) and `next`,
and array fields `decisions`, `completed`, `checks` and `evidence`; each text is at most 2000
characters, each list at most 16 entries and the object at most 12000 characters. The source user
session uses the same fields with its `update_task_brief` tool.

## Coordinator status commands

The coordinator instructions use the primary checkout's status command, run in the primary
checkout, never in a child:

| Step | Command |
| --- | --- |
| Register a candidate | `scripts/concorde.py status --register "$candidate" --task "$goal" --mode maintenance` |
| Read all records | `scripts/concorde.py status` |
| Bind a launched child | `scripts/concorde.py status --change-id "$change_id" --child "$child_id" --phase maintenance` (or `--phase test`) |
| Release a stopped child | the bind command with `--release`, using the current owner's phase |
| Record an authorized merge | `scripts/concorde.py status --change-id "$change_id" --manual-merge "$commit" --cleanup pending` |

Registering an already registered candidate returns the existing record without changing its goal
or mode. The coordinator instructions are projected only into `.pi/extensions/concorde-coordinator.ts`,
which appends them to the system prompt of the source user session.
