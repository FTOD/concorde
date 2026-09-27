# Specification

## Purpose

Specification changes Specs on the main agent's behalf. It provides the `specify` Operation: a
worker bound to one or more Modules edits those Modules' own Spec documents to a stated intent,
including declaring pending realization entries for files a later `implement` run will create. The
Operation reconciles the registry mirror, validates the result and returns the Spec change it
observed,
so the main agent can close Spec gaps and fix where code may go before anyone writes it.
Specification never touches code, creates the files it declares or changes another Module's
documents; a Spec that fails validation stops the run for a decision, not another guess.

## Terminology

| Term | Definition |
| --- | --- |
| Spec change | The result of one specify run: the documents the worker changed, the documents the Operation created for it, the pending entries declared, the worker's account of the promises it changed, the Modules affected and the validation outcome. |
| [Main agent](../../../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../../../vocabulary.md#concept.concorde.worker) | |
| [Spec](../../../vocabulary.md#concept.concorde.spec) | |
| [Task type](../../../vocabulary.md#concept.concorde.task-type) | |
| [Error chain](../../../vocabulary.md#concept.concorde.error-chain) | |
| [Operation](../module.md#concept.operations.operation) | |
| [Execution runner](../../module.md#concept.execution.runner) | |
| [Run result](../../module.md#concept.execution.run-result) | |
| [Workspace](../../module.md#concept.execution.workspace) | |
| [Grant](../../../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Structural check](../../../spec-tooling/spec/module.md#concept.spec.structural-check) | |
| [Impact index](../../../spec-tooling/spec/module.md#concept.spec.impact-index) | |
| [Project registry](../../../spec-tooling/spec/module.md#concept.spec.registry) | |
| [Brief](../../workers/module.md#concept.workers.brief) | |
| [Worker result](../../workers/module.md#concept.workers.worker-result) | |
| [Write audit](../../workers/module.md#concept.workers.audit) | |

A Spec change is the observed outcome; the intent is what was asked for. The two may differ, which
is why the result reports what changed, not the intent.

## Usage

The main agent runs the Operation in a task worktree, typically after `understand` reported Spec
gaps or a plan that starts with a Spec change:

```text
concorde run specify [--modules <module-id>[,<module-id>…]] --intent "<text>" [--input <run-id>]…
```

The run works on the [workspace](../../module.md#concept.execution.workspace) whose binding lies in
the worktree it starts in and briefs the worker with that workspace's goal; it needs a binding,
because only a bound workspace may change. `--modules` names the Modules whose documents may change
(default: the binding's), `--intent` states the change in plain words, and `--input` admits an
earlier `ok` run's output of the same workspace as material. For
example, `--intent "add an optional severity to Issue reports; declare
src/concorde/issues/severity.py as pending"` has the worker edit the Issues entry, contract and
scenario documents, adding the new file as a pending entry.

<a id="concept.specification.spec-change"></a>

The Operation returns a [run result](../../module.md#concept.execution.run-result) whose `output`
is a **Spec change**, defined by the
[Spec change contract](contracts.md#contract.specification.spec-change): the Operation's own
observation of the changed, created and deleted documents, added pending entries, affected Modules and
validation findings, plus the worker's summary of what it changed and what it would still need.

`status` is `ok` when the change was made and validation reports no new error; `blocked` when the
worker could not make the change — a contradicted promise, or an unbound Module's document needed —
or validation finds a new error. The error chain then ends in the worker's own link with its
options, or, for a new validation error, in the Operation's `new_structural_errors` link (reason
`decision`) with one cause per finding, its rule, file and message; `failed` when the worker could
not be run or the audit found a write outside the grant. Edits stay uncommitted, for the
main agent to accept, retry, repair or discard; `blocked`/`failed` still carries the observed
change, except after an audit violation or a failure before the worker ran.

The worker can write only documents its Modules already own. When the change needs a new document of
a bound Module, the worker proposes it and ends `blocked`; the Operation then creates each proposed
document, empty and registered in its Module's `owns` and the registry mirror, and launches a
worker once more, with the same intent and a brief naming the created documents, to fill them. A
proposal it may not create — a Module the run is not bound to, a path outside the folder of that
Module's entry, a file already there — creates nothing and the run stays `blocked`, with
`document-refused` evidence naming the reason. An owned document is deleted only by proposing it;
the Operation performs the deletion after a clean audit. A change spanning several
Modules, such as a contract version increment, needs them all bound in one run.

## Design

The Operation is worker-backed, run with task type `specify`: the bound Modules' own documents
(reading files and metadata) are writable, other Modules' selected documents stay read-only, and
implementation files show by name only. Declaring a pending entry is the one way a `specify` worker
decides where code goes; only `implement` may create it.

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Validate the workspace's Specs as a baseline | Operation, Spec core | Specs cannot load (`failed`) |
| 2 | Compute and freeze the `specify` [grant](../../../spec-tooling/spec/module.md#concept.spec.grant) | Workers, Spec core | unknown Module (`failed`) |
| 3 | Generate settings, tools and the [brief](../../workers/module.md#concept.workers.brief) | Workers | — |
| 4 | Launch the worker and wait for its [worker result](../../workers/module.md#concept.workers.worker-result) | Workers, worker | launch error/timeout (`failed`); worker `blocked`/`failed` (passed on) |
| 5 | [Audit](../../workers/module.md#concept.workers.audit), perform proposed deletions, write the run record | Workers | a write outside the grant (`failed`) |
| 5a | When the worker ended `blocked` proposing new documents of bound Modules: create them, empty and owned, regenerate the registry mirror, and repeat steps 2–5 once with a brief naming them | Operation, Workers | a proposal it may not create (`blocked`, `document-refused`); the second worker's own outcome |
| 6 | Regenerate the [registry](../../../spec-tooling/spec/module.md#concept.spec.registry) mirror from the changed entries | Operation, Spec core | — |
| 7 | Validate again and compare with the baseline | Operation, Spec core | a new error (`blocked`) |
| 8 | Compute changed documents, added entries and affected Modules via the [impact index](../../../spec-tooling/spec/module.md#concept.spec.impact-index) | Operation, Spec core | — |
| 9 | Return the Spec change as the run's output | Operation, Execution runner | — |

When the worker ends `blocked` or `failed` after editing, steps 6–8 still run so the result shows
what was left behind, and the status stays the worker's; only an audit violation skips them.

No grant shows the Protocol copy, so the brief states the rules for writing Spec documents and
ends with the project's own copy of Spec writing guidelines, `.concorde/protocol/kinds/module.md`,
as material: the overview, Required format, Writing guidance and templates. The two parts cover
machine-checkable structure and syntax and content requiring reader and editor judgment;
structural validation does not establish semantic sufficiency. The worker runs no configured
checks and has only Read, Glob, Grep, Edit and Write —
no Bash, web tools or MCP server — and pending files are never pre-created, since the grant has no
implementation path.

Validation is structural: the same
[checks](../../../spec-tooling/spec/module.md#concept.spec.structural-check) `concorde spec-validation` runs.
Comparing with the baseline lets `specify` repair an already-broken worktree — pre-existing errors
do not stop the run, only ones the change introduced. After each round the Operation validates the same
way and resumes the worker, at most twice, with every error its change introduced, so the worker
repairs the Specs it broke itself; only errors left after the last round stop the run for the main
agent's decision.

The registry sits outside every Module's write set, so an edited `module` block leaves the mirror
stale; step 6 is the reconciliation the Protocol provides, touching only existing Modules' mirrored
fields, never adding or removing one. The result's facts come from the Operation's own diff; the
worker's account stays a claim. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

<a id="realization.specification.operation"></a>

The **Specify Operation** realization holds the Operation's steps, worker instructions and result schema
in `src/concorde/specification/` (`operation.py` declares `SPECIFY`), prompt
`prompts/workers/specify.md`, tested against a fake worker.

### Outside

<a id="uses-operations"></a>

**Operations** lists `specify` in its catalog as an Operation that needs a bound workspace and
writes the bound Modules' Specs, and names this Module as its provider; Specification never calls
another Operation or command, not even `task-validation` — its own validation is one of its steps.

<a id="uses-execution"></a>

**Execution**'s [runner](../../module.md#concept.execution.runner) runs the Operation's steps: it
reads the workspace binding, refuses an unbound run, holds the workspace lock, settles the Modules
and inputs, and wraps the Spec change in the
[run result](../../module.md#concept.execution.run-result). Specification relies on it for the
workspace's goal and Modules, and on the lock for no other run changing the workspace while its
audit and validation compare it with the baseline.

<a id="uses-workers"></a>

**Workers** turns the frozen grant into settings, launches the worker with this Module's brief,
collects its [worker result](../../workers/module.md#concept.workers.worker-result), audits
the worktree and writes the run record; any change beyond the bound Modules' documents fails the
run.

<a id="uses-spec"></a>

**Spec core** computes the `specify` [grant](../../../spec-tooling/spec/module.md#concept.spec.grant),
runs the structural checks, regenerates the registry mirror and answers impact questions, always
from the workspace's Specs. Specification relies on its checks as the definition of a
structurally valid Spec and never adds checks of its own.
