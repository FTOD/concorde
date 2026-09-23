# Agent definitions

The exact inventory, definition fields and per-Agent values of every Agent, and the requirements and
scenarios of this Module. The [entry](module.md) explains what the Agents are for; the meaning of an
assessment, plan, task, completion, review result and decision belongs to the providers that accept
them.

## Inventory

| Name | Value |
| --- | --- |
| `agents.AGENTS` | `spec_reviewer`, `context_assessor`, `planner`, `task_author`, `programmer`, `code_reviewer`, `issue_solver` |
| `agents.definition(name)` | The `DEFINITION` of `agents/<name>/`, for a bare, hyphenated or `concorde-` prefixed name; an unknown name raises |
| `agents.external_name(name)` | `concorde-` plus the hyphenated name, for example `concorde-task-author`; the name of the Agent definition file a call launches |

Each package `agents/<name>/` holds `__init__.py`, which exports exactly `DEFINITION`, and the
Agent's own instructions `spec.md`. A directory under `agents/` that holds a `spec.md` but is not
listed by the inventory is a finding. The Task subagent definitions that Pi session keeps under
`agents/` (`agents/task_subagent.py` and `agents/source/`) have no `spec.md` and are not Agents.

### Inventory metadata

The metadata of this document carries the extension `concorde.agents`: an array with one object per
Agent and exactly these string fields.

| Field | Values |
| --- | --- |
| `id` | the hyphenated Agent name |
| `source` | the Agent's instruction source, `agents/<name>/spec.md` |
| `hook` | the entry point of the Agent's hook, as in its definition |

Package validation requires exactly one registered document to carry this extension, loads every
definition, and compares the array with the inventory, ignoring order. A malformed entry, a
duplicate, a missing or extra Agent, or any differing field is a finding.

## Definition fields

A `DEFINITION` is written in the record format that Task context's Agent binding reads:

| Field | Meaning |
| --- | --- |
| `name` | The underscored Agent name, equal to its package name |
| `instructions` | `agents/<name>/spec.md` |
| `workspace` | `capsule` (a private directory of copies) or `project` (the candidate itself) |
| `phase` | The stage the Agent performs, such as `plan` or `code-review` |
| `context`, `result` | The typed input and result, a stage pair: `concorde-agent-stage-context` with `concorde-agent-stage-result`, or `concorde-review-stage-context` with `concorde-review-stage-result` |
| `reads` | The context parts delivered: `spec-context`, `implementation` (contents of the Module's implementation files), `references` (its external context) |
| `writes` | `implementation` or nothing |
| `network`, `credentials` | `False` and `"none"` for every Agent |
| `stage_inputs`, `required_inputs` | The stage input types the Agent accepts, and those it cannot run without |
| `output_fields` | The result fields the Agent may fill beyond the common ones |
| `outcomes` | The outcomes it may return, when narrower than its result type allows |
| `tools` | Its tools, from `read`, `grep`, `find`, `ls`, `edit`, `write`, `bash` and `run_checks` |
| `timeout_seconds` | Its default time limit |
| `hook` | The `module:attribute` entry point of its Agent hook in the provider |

A call adds `report_issue` and `structured_output` to the tools; no definition lists them.

## The seven Agents

| Agent | Phase, pair | Workspace | Reads | Writes | Stage inputs (required in bold) | Result fields | Tools | Timeout | Hook |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context assessor | `context-solve`, stage | capsule | spec-context | none | none | `outcome`: `sufficient`, `spec_incomplete`, `unsupported`, `conflicting` | read, grep, find, ls | 1800 s | `concorde.planning.hooks:context_assessor` |
| planner | `plan`, stage | capsule | spec-context, references | none | `concorde-plan-artifact` | `plan` | read, grep, find, ls | 1800 s | `concorde.planning.hooks:planner` |
| task author | `tasks`, stage | capsule | spec-context, references | none | **`concorde-plan-artifact`**, **`concorde-task-identity-constraints`**, `concorde-implementation-task`, `concorde-review-result`, `concorde-task-scope-feedback`, `concorde-issue-context` | `tasks` | read, grep, find, ls | 1800 s | `concorde.planning.hooks:task_author` |
| programmer | `implementation`, stage | project | spec-context, implementation, references | implementation | **`concorde-implementation-task`**, `concorde-review-result`, `concorde-issue-context` | `tasks` | read, grep, find, ls, edit, write, bash, run_checks | 3600 s | `concorde.implementation.hooks:programmer` |
| spec reviewer | `spec-review`, review | capsule | spec-context | none | review input | review status | read, grep, find, ls | 1800 s | `concorde.review.native:spec_reviewer` |
| code reviewer | `code-review`, review | project | spec-context, implementation, references | none | review input | review status | read, grep, find, ls, run_checks | 3600 s | `concorde.review.native:code_reviewer` |
| issue solver | `issue-solve`, stage | capsule | spec-context | none | **`concorde-issue-selection`** | `issue_decision` | read, grep, find, ls | 1800 s | `concorde.issue_solving.native:issue_solver` |

The code reviewer's workspace is the project so that its `run_checks` measures the candidate, but
its capsule holds copies of the implementation files it reviews; it has no shell.

## What each Agent is told

Each Agent's rendered instructions are `prompts/native/<name>.md`, which states the transport rules
(read `context.json`, submit once through structured output with the issued invocation identity, a
proposal is not acceptance), followed by `agents/<name>/spec.md`, which states the job. The spec
reviewer and code reviewer include `prompts/workflow-host/review-scope-and-result.md`. The build
renders them to `generated/native/<name>.md`. The following summarises each job; the instructions
are the canonical text.

- **context assessor.** Decides whether the task can be carried out from the Module's complete Spec
  context. It sees implementation file names but never their contents and does not search
  elsewhere for missing meaning. `sufficient` has no blockers; `spec_incomplete` carries Issue
  receipts naming the missing question and the blocked step; `unsupported` means the Spec settles
  that the task is prohibited; `conflicting` means the Spec contradicts itself.
- **planner.** Writes an actionable, contract-level plan from the Specs and admitted external
  references alone, never from code, and may name the realizations a piece of work concerns. A
  missing behavioural promise is reported as a gap instead of invented.
- **task author.** Turns the accepted plan into a nonempty list of tasks, each with a new `id`
  outside the reserved set, a `target_id`, a `description`, observable `acceptance` that cites
  relevant requirement or scenario identities, and `complete: false`. Acceptance covers
  implementation only. With a prior list and a review result it writes repair tasks for the blocking
  findings; with scope feedback it replaces a list that mixed implementation with later steps.
- **programmer.** Fulfils the supplied tasks in the candidate, writing only files the Module's
  realizations bind, including pending entries, and never Specs, metadata, the registry,
  configuration, control state or other worktrees. It returns every task unchanged except `complete: true` for fulfilled ones, and states
  which checks it ran. It never commits, reviews, marks ready or delivers.
- **spec reviewer.** Reads the Module's admitted Specs as a newcomer against representative tasks
  derived from the request, including whether every imported term is used with its owner's meaning,
  reports each problem once through `report_issue`, and returns `no_findings`, `findings` or
  `incomplete`.
- **code reviewer.** Compares the granted implementation and the scoped changes with the admitted
  contracts, runs the configured checks through `run_checks`, and reports concrete behaviour
  defects; a test that declares a scenario of this Module without exercising it is a defect.
  Unavailable evidence is never a pass.
- **issue solver.** Chooses the next bounded action for one selected Issue revision from the Spec
  context, bounded feedback and at most five admitted duplicate candidates. `issue_decision` has
  exactly `action`, `intent`, `rationale` and `duplicate_of`; it reads no implementation, edits
  nothing and closes nothing.

## Requirements

### req.agents.single-definition — One definition per Agent

Every Agent SHALL have exactly one definition in this Module, from which its binding, rendering,
launch tools and model selection key are all derived.

### req.agents.terminal — Agents never delegate

No Agent definition SHALL list a tool that delegates a task, starts another agent or invokes a
Concorde capability.

This is the one statement of the rule. Agent execution's launch preflight refuses a call whose
tools exceed the definition, so a delegating tool cannot be added at launch either.

### req.agents.known-tools — Only Harness tools

An Agent definition SHALL list only tools from `read`, `grep`, `find`, `ls`, `edit`, `write`, `bash`
and `run_checks`.

### req.agents.writers-only-mutate — Only writers get mutating tools

An Agent definition SHALL list `edit`, `write` or `bash` only when it declares implementation
writes.

The programmer is the only such Agent; the code reviewer in particular has no `bash`.

### req.agents.hook-named — Every Agent names its hook

Every Agent definition SHALL name the `module:attribute` entry point of the Agent hook its provider
implements.

### req.agents.instruction-source — Instructions come from the definition

Every Agent's rendered instructions SHALL consist of its shared native rules followed by its own
instruction source and the shared fragments that source includes.

## Scenarios

### scenario.agents.inventory — One definition for every Agent

- GIVEN the source checkout with seven Agent packages
- WHEN the build renders Agent instructions and Task context binds each Agent
- THEN every Agent's binding and instructions come from its own definition and instruction source
- AND the inventory metadata lists the same seven Agents with the same sources and hooks

### scenario.agents.inventory-drift — A drifted inventory is a finding

- GIVEN an inventory whose metadata misses, duplicates or differs from an Agent, or an unlisted directory under `agents/`
- WHEN package validation compares them
- THEN each difference is a finding
- BUT no second definition is created or used

### scenario.agents.domain-tools — Each Agent gets exactly its tools

- GIVEN the seven Agent definitions
- WHEN a call is prepared for each of them
- THEN the Agent definition file lists the definition's tools plus `report_issue` and no delegation tool
- AND only the programmer has `edit`, `write` or `bash`
- AND the code reviewer has `run_checks` and no `bash`
- AND the prepared Agent starts with fresh context and without inherited project or global instructions or Skills

### scenario.agents.invalid-definition — A definition outside the rules is refused

- GIVEN a definition that lists a delegating or unknown tool, lists `edit`, `write` or `bash` without implementation writes, or names no hook
- WHEN the inventory is loaded
- THEN loading fails naming the Agent and the violated rule
- BUT no call of that Agent can be prepared
