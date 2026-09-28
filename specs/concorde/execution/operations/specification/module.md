# Specification

## Purpose

Specification changes Specs on the [main agent](../../../glossary.json#concept.main-agent)'s behalf.
It provides the `specify` [Operation](../../../glossary.json#concept.operation): a worker bound to
one or more Modules edits those Modules' own [Spec](../../../glossary.json#concept.spec) documents
to a stated intent, including declaring pending realization entries for files a later `implement`
run will create. The Operation reconciles the registry mirror, validates the result and returns the
[Spec change](../../../glossary.json#concept.spec-change) it observed, so the main agent can close
[Spec gaps](../../../glossary.json#concept.spec-gap) and fix where code may go before anyone writes
it. Specification never touches code, creates the files it declares or changes another
[Module](../../../glossary.json#concept.module)'s documents; a Spec that still fails validation after
the worker's bounded repair rounds stops the run for a decision, not another guess.

## Usage

The main agent runs the Operation in a task worktree, typically after `understand` reported Spec
gaps or a plan that starts with a Spec change:

```text
concorde run specify [--modules <module-id>[,<module-id>…]] --intent "<text>" [--input <run-id>]…
```

The run works on the [workspace](../../../glossary.json#concept.workspace) whose binding lies in the
worktree it starts in and briefs the worker with that workspace's goal; it needs a binding, because
only a bound workspace may change. `--modules` names the Modules whose documents may change
(default: the binding's), `--intent` states the change in plain words, and `--input` admits an
earlier `ok` run's output of the same workspace as material. For example,
`--intent "add an optional severity to Issue reports; declare src/concorde/issues/severity.py as pending"`
has the worker edit the Issues entry, contract and scenario documents for
[Issue reports](../../../glossary.json#concept.issue-report), adding the new file as a pending
entry.

<a id="concept.spec-change"></a>

The Operation returns a [run result](../../../glossary.json#concept.run-result) whose `output` is a
**Spec change**, defined by the
[Spec change contract](contracts.md#contract.specification.spec-change): the Operation's own
observation of the changed, created and deleted documents, added pending entries, affected Modules
and validation findings, plus the worker's summary of what it changed and what it would still need.

`status` is `ok` when the change was made and validation reports no new error; `blocked` when the
worker could not make the change — a contradicted promise, or an unbound Module's document needed —
or validation finds a new error. The [error chain](../../../glossary.json#concept.error-chain) then
ends in the worker's own link with its options, or, for a new validation error, in the Operation's
`new_structural_errors` link (reason `decision`) with one cause per finding, its rule, file and
message; `failed` when the worker could not be run or the audit found a write outside the grant.
Edits stay uncommitted, for the main agent to accept, retry, repair or discard; `blocked`/`failed`
still carries the observed change, except after an audit violation or a failure before the worker
ran.

The worker can write only documents its Modules already own, and the project glossary's entries
those Modules own; a changed glossary shows among the changed documents. When the change needs a
new document of a bound Module, the worker proposes it and ends `blocked`; the Operation then
creates each proposed document, empty and registered in its Module's `owns` and the registry
mirror, and launches a worker once more, with the same intent and a brief naming the created
documents, to fill them. A proposal it may not create — a Module the run is not bound to, a path
outside the folder of that Module's entry, a file already there — refuses the whole list, since the
change needs all of them: nothing is created, no second worker runs and the run stays `blocked`,
with `document-refused` evidence naming the reason for each refused proposal. An owned document is
deleted only by proposing it; the Operation performs the deletion after a clean audit. A change
spanning several
Modules, such as a contract version increment, needs them all bound in one run.

## Design

The Operation is worker-backed, run with [task type](../../../glossary.json#concept.task-type)
`specify`: the bound Modules' own documents (reading files and metadata) and the project glossary
are writable — the write audit reports any glossary entry changed whose owner is not a bound
Module — other Modules' selected documents stay read-only, and implementation files show by name
only. Declaring a
pending entry is the one way a `specify` worker decides where code goes; only `implement` may create
it.

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Validate the workspace's Specs as a baseline | Operation, Spec core | Specs cannot load (`failed`) |
| 2 | Compute and freeze the `specify` [grant](../../../glossary.json#concept.grant) | Operation, Spec core | unknown Module (`failed`) |
| 3 | Generate settings, tools and the [brief](../../../glossary.json#concept.brief) | Workers | — |
| 4 | Launch the worker and wait for its [worker result](../../../glossary.json#concept.worker-result) | Workers, worker | launch error/timeout (`failed`); worker `blocked`/`failed` (passed on) |
| 5 | [Audit](../../../glossary.json#concept.write-audit), perform proposed deletions, write the [run record](../../../glossary.json#concept.run-record) | Workers | a write outside the grant (`failed`) |
| 5a | When the worker ended `blocked` proposing new documents of bound Modules: create them, empty and owned, regenerate the registry mirror, and repeat steps 2–5 once with a brief naming them | Operation, Workers | a proposal it may not create (`blocked`, `document-refused`); the second worker's own outcome |
| 6 | Regenerate the [registry](../../../glossary.json#concept.registry) mirror from the changed entries | Operation, Spec core | — |
| 7 | Validate again and compare with the baseline | Operation, Spec core | a new error left after the last repair round of a worker that ended `ok` (`blocked`) |
| 8 | Compute changed documents, added entries and affected Modules via the [impact index](../../../glossary.json#concept.impact-index) | Operation, Spec core | — |
| 9 | Return the Spec change as the run's output | Operation, Execution runner | — |

When the worker ends `blocked` or `failed` after editing — including a round that timed out or
reached a limit, and an invalid worker result — steps 6–8 still run so the result shows what was
left behind, and the status stays the worker's, with any new error reported in the validation
findings; only an audit violation skips them. Steps 6 and 8 never stop the run themselves: when an
entry the worker edited cannot be read, step 6 records the registry command's refusal as evidence
and leaves the mirror unchanged, step 7 reports the unreadable entry as a new error, treated like
any other, and step 8 reports the affected Modules it could still compute, with evidence naming
each Module whose [Spec context](../../../glossary.json#concept.spec-context) it could not.

No grant shows the [Protocol copy](../../../glossary.json#concept.protocol-copy), so the brief
states the rules for writing Spec documents and ends with the project's own copy of Spec writing
guidelines, `.concorde/protocol/kinds/module.md`, as material: the overview, Required format,
Writing guidance and templates. The two parts cover machine-checkable structure and syntax and
content requiring reader and editor judgment; structural validation does not establish semantic
sufficiency. The worker runs no [configured checks](../../../glossary.json#concept.configured-check)
and has only Read, Glob, Grep, Edit and Write — no Bash, web tools or MCP server — and pending files
are never pre-created, since the grant has no implementation path.

Validation is structural: the same [checks](../../../glossary.json#concept.structural-check)
`concorde spec-validation` runs. Comparing with the baseline lets `specify` repair an already-broken
worktree — pre-existing errors do not stop the run, only ones the change introduced. A finding is
the same as a baseline one when its rule, file and message match; line numbers are ignored, since
any edit shifts them, so an error that only moved stays pre-existing, and another occurrence with
the same rule, file and message counts as pre-existing too. After each round that the worker ended
`ok` with a clean audit, the Operation validates the same way and resumes the worker, at most twice
per worker launch, with every error its change introduced, so the worker repairs the Specs it broke
itself; the second worker launched to fill created documents gets its own two repair rounds. Only
errors left after the last round stop the run for the main agent's decision.

The registry sits outside every Module's write set, so an edited `module` block leaves the mirror
stale; step 6 is the reconciliation the Protocol provides, touching only existing Modules' mirrored
fields, never adding or removing one. The result's facts come from the Operation's own diff; the
worker's account stays a claim. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

<a id="realization.specification.operation"></a>

The **Specify Operation** realization holds the Operation's steps, worker instructions and result
schema in `src/concorde/specification/` (`operation.py` declares `SPECIFY`), prompt
`prompts/workers/specify.md`, tested against a fake worker.

### Outside

<a id="uses-operations"></a>

**Operations** lists `specify` in its catalog as an Operation that needs a bound workspace and
writes the bound Modules' Specs, and names this Module as its provider; Specification never calls
another Operation or command, not even `task-validation` — its own validation is one of its steps.

<a id="uses-execution"></a>

**Execution**'s [runner](../../../glossary.json#concept.execution-runner) runs the Operation's
steps: it reads the [workspace binding](../../../glossary.json#concept.workspace-binding), refuses
an [unbound run](../../../glossary.json#concept.unbound-run), holds the
[workspace lock](../../../glossary.json#concept.workspace-lock), settles the Modules and inputs, and
wraps the Spec change in the [run result](../../../glossary.json#concept.run-result). Specification
relies on it for the workspace's goal and Modules, and on the lock for no other run changing the
workspace while its audit and validation compare it with the baseline.

<a id="uses-workers"></a>

**Workers** turns the frozen grant into settings, launches the worker with this Module's brief,
collects its [worker result](../../../glossary.json#concept.worker-result), audits
the worktree and writes the run record; any change beyond the bound Modules' documents fails the
run.

<a id="uses-spec"></a>

**Spec core** computes the `specify` [grant](../../../glossary.json#concept.grant),
runs the structural checks, regenerates the registry mirror and answers impact questions, always
from the workspace's Specs. Specification relies on its checks as the definition of a
structurally valid Spec and never adds checks of its own.
