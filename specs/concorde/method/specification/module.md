# Specification

## Purpose

Specification changes Specs on the caller's behalf. It provides the `specify`
[Operation](../../glossary.json#concept.operation). A worker bound to one or more Modules edits
those Modules' own [Spec](../../glossary.json#concept.spec) documents to a stated intent.
The Operation does these things:

- Reconciles the registry mirror.
- Validates the result.
- Returns the [Spec change](../../glossary.json#concept.spec-change) it observed.

The caller can thus close [Spec gaps](../../glossary.json#concept.spec-gap) before anyone writes
code. Specification never does any of these things:

- Touches code.
- Creates an implementation file.
- Binds a file that does not exist.
- Changes another [Module](../../glossary.json#concept.module)'s documents.

When a Spec still fails validation after the worker's bounded repair rounds, the run stops for a
decision, not another guess.

## Core concepts

### The Spec change

<a id="concept.spec-change"></a>

The Operation returns a [run result](../../glossary.json#concept.run-result) whose `output` is a
**Spec change**, defined by the [Spec change contract](contracts.md#contract.specification.spec-change).
It contains these things:

- The Operation's own observation of the changed, created and deleted documents.
- The Operation's own observation of affected Modules.
- The Operation's own observation of validation findings.
- The worker's summary of what it changed and what it would still need.

The result's facts come from the Operation's own diff. The worker's account stays a claim.

### What a specify worker may write

The Operation is worker-backed, run with [task type](../../glossary.json#concept.task-type)
`specify`. The bound Modules' own documents (reading files and metadata) and the project glossary
are writable. Method's round validation includes a glossary ownership audit. It reports any changed
glossary entry whose owner is not a bound Module. Other Modules' selected documents stay read-only.
Implementation files show by name only. A worker may bind to a realization only a file that exists.
The task level creates and binds a new file before the run that fills it. A file is never declared
before it exists.

### Validation against a baseline

Validation is structural: the same [checks](../../glossary.json#concept.structural-check) `concorde
spec-validation` runs. Before the worker starts, the Operation validates the workspace's Specs as a
baseline. It compares every later validation with that baseline. Comparing with the baseline lets
`specify` repair an already-broken worktree. Pre-existing errors do not stop the run. Only errors
the change introduced stop it. This comparison is the step's own validation. The Operation hands it
to the worker harness as part of round validation ([standard worker
sequence](../../glossary.json#concept.standard-worker-sequence)). After each round that the worker
ended `ok` with a clean audit, the worker harness calls that validation and resumes the worker with
every error its change introduced, at most twice per worker launch. The worker thus repairs the
Specs it broke itself. Only errors left after the last round stop the run for a decision at the task
level.

## Overview

Who does what in one `specify` run:

- The task level states the intent and decides what to do with the result.
- The worker edits and proposes.
- The Operation does these things:
  - Validates.
  - Creates what the worker proposed.
  - Observes the change.

[How it is built](#how-it-is-built) gives every step and exit.

```d2 illustrative
direction: down
classes: {
  agent: {style: {fill: "#e8edff"; stroke: "#3b5bdb"; stroke-width: 2; border-radius: 6}}
  program: {style: {fill: "#f3f4f6"; stroke: "#6b7280"; stroke-width: 2; border-radius: 6}}
}
intent: "Task level: states the intent and the Modules" {class: agent}
baseline: "Operation: validate the Specs as a baseline" {class: program}
prepare: "Operation: freeze the specify grant" {class: program}
edit: "Worker: edits the bound Modules'\nown documents" {class: agent}
check: "Operation: validate against the baseline" {class: program}
create: "Operation: create the proposed documents,\nempty and owned" {class: program}
observe: "Operation: regenerate the registry mirror,\nvalidate again, observe the Spec change" {class: program}
decide: "Task level: accepts, retries, repairs\nor discards the uncommitted edits" {class: agent}
intent -> baseline -> prepare -> edit
edit -> check: ended ok
check -> edit: "new errors: resume\n(at most twice per launch)" {style.stroke-dash: 3}
edit -> create: "blocked, proposing\nnew documents" {style.stroke-dash: 3}
create -> prepare: "launch once more" {style.stroke-dash: 3}
check -> observe: "no new error, or\nrepair rounds used up"
observe -> decide
```

## Running specify

The caller runs the Operation in a task worktree, typically after `understand` reported Spec
gaps or a plan that starts with a Spec change:

```text
concorde run specify [--modules <module-id>[,<module-id>…]] --intent "<text>" [--input <run-id>]…
```

The run works on the [workspace](../../glossary.json#concept.workspace) whose binding lies in the
worktree it starts in. It briefs the worker with that workspace's goal. It needs a binding, because
only a bound workspace may change. The arguments do these things:

- `--modules` names the Modules whose documents may change (default: the binding's).
- `--intent` states the change in plain words.
- `--input` admits an earlier `ok` run's output of the same workspace as material.

For example, `--intent "add an optional severity to Issue reports"` has the worker edit the Issues
entry, contract and scenario documents for
[Issue reports](../../glossary.json#concept.issue-report). The task level then does these things:

- Creates `src/concorde/issues/severity.py`.
- Binds it to Issues.
- Has `implement` fill it.

The `status` values mean these things:

- When the change was made and validation reports no new error, the status is `ok`.
- When the worker could not make the change or validation finds a new error, the status is
  `blocked`.
- When the worker could not be run or the audit found a write outside the grant, the status is
  `failed`.

A contradicted promise or a needed document of an unbound Module can prevent the worker from making
the change. When the worker cannot make the change, the [error
chain](../../glossary.json#concept.error-chain) ends in the worker's own link with its options. For
a new validation error, it ends in the Operation's `new_structural_errors` link (reason `decision`).
That link has one cause per finding, with its rule, file and message. Edits stay uncommitted. Within
its authority, the task level can accept, retry, repair or discard them. Except after an audit
violation or a failure before the worker ran, `blocked`/`failed` still carries the observed change.

### New and deleted documents

The worker can write only these:

- Documents its Modules already own.
- Entries of the project glossary that those Modules own.

A changed glossary shows among the changed documents. When the change needs a new document of a
bound Module, the worker proposes it and ends `blocked`. The Operation then does these things:

- Creates each proposed document, empty and registered in its Module's `owns` and the registry
  mirror.
- Launches a worker once more, with the same intent and a brief naming the created documents, to
  fill them.

A document may lie in a subfolder of the entry's folder. Its one line links to the entry by a
relative path, such as `../module.md`. The Operation may not create a proposal in any of these
cases:

- The Module is not one the run is bound to.
- The path is outside the folder of that Module's entry.
- The file is already there.
- The path is proposed more than once.

If any proposal is one it may not create, the Operation refuses the whole list, since the change
needs all of them. In that case, these things hold:

- Nothing is created.
- No second worker runs.
- The run stays `blocked`, with `document-refused` evidence naming the reason for each refused
  proposal.

An owned document is deleted only by proposing it. After a clean audit, the
Operation performs the deletion. A change spanning several Modules, such as a contract version
increment, needs them all bound in one run.

## How it is built

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Validate the workspace's Specs as a baseline | Operation, Spec core | Specs cannot load (`failed`) |
| 2 | Compute and freeze the `specify` [grant](../../glossary.json#concept.grant) | Operation, Spec core | unknown Module (`failed`) |
| 3 | Generate settings, tools and the [brief](../../glossary.json#concept.brief) | Workers | — |
| 4 | Launch the worker and wait for its [worker result](../../glossary.json#concept.worker-result); after each round it ended `ok` with a clean audit, validate against the baseline and, at most twice per worker launch, resume it with every error its change introduced | Workers, worker, Operation | launch error/timeout (`failed`); worker `blocked`/`failed` (passed on) |
| 5 | [Audit](../../glossary.json#concept.write-audit), perform proposed deletions, write the [run record](../../glossary.json#concept.run-record) | Workers | a write outside the grant (`failed`) |
| 5a | When the worker ended `blocked` proposing new documents of bound Modules: create them, empty and owned, regenerate the registry mirror, and repeat steps 2–5 once with a brief naming them | Operation, Workers | a proposal it may not create (`blocked`, `document-refused`); the second worker's own outcome |
| 6 | Regenerate the [registry](../../glossary.json#concept.registry) mirror from the changed entries | Operation, Spec core | — |
| 7 | Validate again and compare with the baseline | Operation, Spec core | a new error left after the last repair round of a worker that ended `ok` (`blocked`) |
| 8 | Compute changed documents, added entries and affected Modules via the [impact index](../../glossary.json#concept.impact-index) | Operation, Spec core | — |
| 9 | Return the Spec change as the run's output | Operation, Execution runner | — |

The repair loop inside each worker launch, the one relaunch of step 5a and the exits:

```d2 illustrative
direction: down
baseline: 1 Validate the Specs as a baseline
grant: 2 Freeze the specify grant
brief: 3 Settings, tools and brief
launch: 4 Launch or resume the worker
audit: 5 Audit against the grant
repair: 4 Validate against the baseline
record: "5 Proposed deletions after a clean audit, run record"
create: "5a Create the proposed documents, empty and owned;\nregenerate the registry mirror"
registry: 6 Regenerate the registry mirror
validate: 7 Validate again against the baseline
impact: 8 Changed documents, added entries, affected Modules
output: 9 Return the Spec change
stopped: "failed, nothing observed" {shape: oval}
baseline -> grant -> brief -> launch -> audit
audit -> repair: worker ok, audit clean
launch <- repair: "new errors, repair rounds left (two per launch): resume with them"
repair -> record: "no new error, or repair rounds used up"
launch -> record: "launch error: failed" {style.stroke-dash: 3}
audit -> record: "timeout, limit reached, invalid result: failed;\nworker blocked or failed: its status" {style.stroke-dash: 3}
audit -> stopped: write outside the grant {style.stroke-dash: 3}
record -> registry: "no documents proposed"
record -> create: "worker blocked, proposing new documents (first launch only)" {style.stroke-dash: 3}
grant <- create: "all created: launch once more, the brief naming them" {style.stroke-dash: 3}
create -> registry: "a proposal refused: blocked, nothing created" {style.stroke-dash: 3}
baseline -> stopped: Specs cannot load {style.stroke-dash: 3}
grant -> stopped: unknown Module {style.stroke-dash: 3}
registry -> validate
validate -> impact: "no new error: the worker's status"
validate -> impact: "a new error left after an ok worker: blocked" {style.stroke-dash: 3}
impact -> output
```

Except after an audit violation, steps 6–8 still run when the worker ends `blocked` or `failed`
after editing. This includes these cases:

- A round timed out.
- A round reached a limit.
- A worker result was invalid.

The result thus shows what was left behind. The status stays the worker's, with any new error
reported in the validation findings. Only an audit violation skips those steps.

Steps 6 and 8 never stop the run themselves. When an entry the worker edited cannot be read,
the steps do the following:

- Step 6 records the registry command's refusal as evidence and leaves the mirror unchanged.
- Step 7 reports the unreadable entry as a new error, treated like any other.
- Step 8 reports the affected Modules it could still compute.

In that case, step 8 also gives evidence naming each Module whose
[Spec context](../../glossary.json#concept.spec-context) it could not compute.

No grant shows the [Protocol copy](../../glossary.json#concept.protocol-copy), so the brief states
the rules for writing Spec documents. It ends with the project's own copy of Spec writing
guidelines, `.concorde/protocol/kinds/module.md`, as material:

- The overview.
- Required format.
- Writing guidance.
- Sentence style.
- Evaluating a Spec.
- Templates.

Together they cover machine-checkable structure and syntax and content requiring reader and editor
judgment. Structural validation does not establish semantic sufficiency. The worker runs no
[configured checks](../../glossary.json#concept.configured-check). It has only Read, Glob, Grep,
Edit and Write. It has no Bash, web tools or MCP server. Its grant has no writable implementation
path.

A finding is the same as a baseline one when its rule, file and message match. Line numbers are ignored, since any edit shifts them. An error that only moved thus stays
pre-existing. Another occurrence with the same rule, file and message counts as pre-existing too.
The repair rounds validate the same way. The second worker launched to fill created documents gets
its own two repair rounds.

The registry sits outside every Module's write set, so an edited `module` block leaves the mirror
stale. Step 6 is the reconciliation the Protocol provides. It touches only existing Modules'
mirrored fields, never adding or removing one. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

<a id="realization.specification.operation"></a>

The **Specify Operation** realization holds the Operation's steps, worker instructions and result
schema in `src/concorde/method/specification/` and prompt `prompts/workers/specify.md`.
`operation.py` declares `SPECIFY`. The realization is tested against a fake worker.

## What it relies on

<a id="uses-operations"></a>

**Operations**, Execution's Operation framework, is what `specify` plugs into. Method registers
its definition as an Operation that needs a bound workspace and writes the bound Modules' Specs.
Method names this Module as its provider ([Method](../module.md#the-operations-and-commands-it-provides)).
Specification never calls another Operation or command, not even `task-validation`. Its own
validation is one of its steps.

<a id="uses-execution"></a>

**Execution**'s [runner](../../glossary.json#concept.execution-runner) runs the Operation's steps:

- It reads the [workspace binding](../../glossary.json#concept.workspace-binding).
- It refuses an [unbound run](../../glossary.json#concept.unbound-run).
- It holds the [workspace lock](../../glossary.json#concept.workspace-lock).
- It settles the Modules and inputs.
- It wraps the Spec change in the run result.

Specification relies on it for the workspace's goal and Modules. During the audit and validation
comparison with the baseline, Specification relies on the lock to prevent another run from
changing the workspace.

<a id="uses-workers"></a>

**Workers**, in the worker harness, does these things:

- Receives the frozen grant as data through Method's standard worker sequence.
- Receives this Module's round validation through Method's standard worker sequence.
- Turns the grant into settings.
- Launches the worker with this Module's instructions.
- Collects its worker result.
- Audits the worktree.
- Calls the round validation after each clean round.
- Writes the run record.

Any change beyond the bound Modules' documents fails the run.

<a id="uses-spec"></a>

Always from the workspace's Specs, **Spec core** does these things:

- Computes the `specify` grant.
- Runs the structural checks.
- Regenerates the registry mirror.
- Answers impact questions.

Specification relies on its checks as the definition of a structurally valid Spec. Specification
never adds checks of its own.
