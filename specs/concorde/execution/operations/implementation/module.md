# Implementation

## Purpose

Implementation changes and exercises a [Module](../../../glossary.json#concept.module)'s code
against its [Spec](../../../glossary.json#concept.spec). It provides two Operations: `implement`
lets a worker change the bound Modules' code toward a stated goal, then audits it and runs the
configured checks, resuming the worker with failures for a limited number of rounds; `test` runs the
checks itself and lets a read-only worker interpret the results into a
test report. Neither worker ever changes a Spec — a
missing or contradictory promise stops the run with a
[Spec gap](../../../glossary.json#concept.spec-gap) — and `implement`'s only Spec edit is the
[Operation](../../../glossary.json#concept.operation) clearing a pending marker once its file
exists; readiness and delivery are the
[execution commands](../../../glossary.json#concept.execution-command) of other Modules.

## Core concepts

### Workers change or read code, checks decide

Both Operations are worker-backed. `implement` uses
[task type](../../../glossary.json#concept.task-type) `implement`: the files bound by the Modules'
realizations are writable (pending entries included), their Specs stay read-only, and other
implementation files show by name only. `test` uses task type `test`: the same files readable,
nothing writable. Neither worker can change a Spec, so disagreement between Spec and code can only
be reported.

Whether the code passes is never the worker's word. Checks run outside the worker and read-only,
so it cannot fake a green result or change the worktree through one: in `implement` the
[configured checks](../../../glossary.json#concept.configured-check) run after the worker and send
their failures back to it as a [resume round](../../../glossary.json#concept.resume-round), and in
`test` the Operation runs them first and the worker only interprets their results. A failing check
is not a failed `test` run; it is for the task level to follow up with `implement`, `specify` or a
decision.

### The code change and the test report

`implement` returns a [run result](../../../glossary.json#concept.run-result) whose `output` is
a **code change**, defined by the
[code change contract](contracts.md#contract.implementation.code-change), which the Operation
composes from the [run record](../../../glossary.json#concept.run-record) itself:
changed/created files, deletions performed or refused, rounds used and the last round's checks.
`test` returns a **test report**, defined by the
[test report contract](contracts.md#contract.implementation.test-report): the Operation's results
decide pass/fail, and the worker adds, per failure, the scenario or requirement concerned, its
cause, and whether the defect is code, a test, the Spec or the environment. Each worker returns
only its own output part (`addresses`, or `failures` and `notes`); the Operation adds everything it
observed itself.

### The checked Modules

The set of checked Modules is the same for both Operations: the bound Modules together with every
Module that uses one of them, directly or through further uses, as Check execution's
`checked_modules` computes it. A selective check runs only when some test verifies a scenario of
those Modules, and a readiness check never runs here; a check that does not run is not listed.

### Pending files

A file a Spec declares as pending does not exist until `implement` creates it. Pre-creating pending
files lets the [write hook](../../../glossary.json#concept.write-hook) and sandbox treat them as
ordinary writable files. After the worker, an unused file or directory disappears and stays pending;
one that now exists has its pending marker cleared — the only Spec edit `implement` makes, an
observed fact rather than the worker's claim. A file meant to stay empty is removed and stays
pending; it needs some content to count as created.

## Overview

The two Operations side by side: `implement` checks after its worker and loops back to it, `test`
checks before its worker and only asks it to explain the results.

```d2 illustrative
implement: implement {
  direction: down
  grant: "Freeze the implement grant;\npre-create pending files"
  worker: "Worker changes the\nbound Modules' code"
  checks: "Run the configured checks\noutside the worker"
  markers: "Clear the pending markers\nof files that now exist"
  output: "Code change"
  grant -> worker -> checks
  worker <- checks: "a check fails, rounds left:\nresume with the failures" {style.stroke-dash: 3}
  checks -> markers: "all pass, or\nrounds used up"
  markers -> output
}
test: test {
  direction: down
  grant: "Freeze the test grant"
  checks: "Run the configured checks"
  worker: "Read-only worker interprets\nthe check results"
  output: "Test report"
  grant -> checks -> worker -> output
}
```

## Running implement and test

The caller runs both Operations after the Specs state what the code must do and declare new files
as pending entries:

```text
concorde run implement [--modules <module-id>[,<module-id>…]] --goal "<text>" [--input <run-id>]… [--rounds <n>]
concorde run test [--modules <module-id>[,<module-id>…]] [--focus "<text>"]
```

Both work on the [workspace](../../../glossary.json#concept.workspace) whose binding lies in the
worktree they start in and need one: an [unbound run](../../../glossary.json#concept.unbound-run) of
either is refused. `--modules` defaults to the binding's Modules. Each worker's brief carries the
workspace's goal as context, as `specify`'s does, beside the run's own argument: `implement`'s
`--goal` states the run's own task, which may be one step of the workspace's goal, and `test`'s
`--focus` narrows what its worker looks at, never which checks run. `implement` also admits earlier
`ok` outputs via `--input`, and `--rounds` sets the resume-round limit (0 or more); without it the
limit is the [worker configuration](../../../glossary.json#concept.worker-configuration)'s
`limits.rounds`, and three when that is not set. For example, after `specify` declares
`src/concorde/issues/severity.py` pending, `implement --goal "accept and store the report severity"`
lets the worker create it and change the other Issues files, returning once the checks pass or the
rounds run out.

`implement`'s `status` is `ok` when the last round's checks passed; `blocked` when the worker
reported a Spec gap or another problem it cannot solve within its grant, such as a change that needs
a file only an unbound Module binds, ending the
[error chain](../../../glossary.json#concept.error-chain) in its own link, unresumed; `failed` when
checks still fail after the last round (one link per failing check, exit code and log tail), the
audit found a change outside the grant, the worker ended `failed` or could not be run, or the grant
could not be computed — for instance because a writable file is also bound by an unbound Module,
which is refused before any worker starts. A run with no configured check ends `ok` with no check
evidence, which the result states, and the caller should run `test` or add checks. Whenever the
worker returned a result, the output holds the code change whatever the status, and edits stay
uncommitted.

`test`'s `status` is `ok` whenever the checks were interpreted, passing or not; `blocked` when the
worker could not interpret them; `failed` when the checks or the worker could not be run, the worker
ended `failed`, or the audit found any change. Only `ok` carries a report; the host evidence of any
other run still lists the check results. Running `test` again is safe.

## How implement is built

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `implement` [grant](../../../glossary.json#concept.grant) | Operation, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Pre-create every pending file/directory the grant makes writable, empty | Workers | cannot create (`failed`) |
| 3 | Generate settings, tools and the [brief](../../../glossary.json#concept.brief) | Workers | — |
| 4 | Launch the worker and wait for its [worker result](../../../glossary.json#concept.worker-result) | Workers, worker | launch error/timeout (`failed`) |
| 5 | [Audit](../../../glossary.json#concept.write-audit) against the grant | Workers | write outside the grant (`failed`); worker `blocked`/`failed` (passed on) |
| 6 | After a clean audit of a worker that ended `ok`, run the configured checks of the bound Modules and of every Module that uses one of them | Workers, Check execution | — |
| 7 | While a check fails with rounds left, resume the session, repeat 5–6 | Workers, worker | rounds used, still failing (`failed`) |
| 8 | Perform proposed deletions after a clean audit; remove pre-created paths still empty; write the run record | Workers | — |
| 9 | Remove any pre-created path still empty that step 8 left; clear the pending marker of every entry that now exists | Operation, Spec core | — (a marker update that fails is recorded as `pending-markers` evidence) |
| 10 | Return the run's output | Operation, Execution runner | — |

The main path, the resume loop and the exits, which all meet at steps 8–10:

```d2 illustrative
direction: down
grant: 1 Freeze the implement grant
precreate: 2 Pre-create pending files
brief: 3 Settings, tools and brief
launch: 4 Launch or resume the worker
audit: 5 Audit against the grant
checks: 6 Run the configured checks
record: "8 Proposed deletions after a clean audit, empty pre-created paths removed, run record"
markers: "9 Leftover empty paths removed, pending markers of existing entries cleared"
output: 10 Return the code change
stopped: "failed, no worker launched" {shape: oval}
grant -> precreate -> brief -> launch -> audit
audit -> checks: worker ok, audit clean
launch <- checks: "7 a check fails, rounds left: resume with the failures"
checks -> record: "all passed, or none configured: ok"
checks -> record: "still failing, rounds used up: failed" {style.stroke-dash: 3}
audit -> record: "write outside the grant, timeout, limit reached, invalid result: failed;\nworker blocked or failed: its status, unresumed" {style.stroke-dash: 3}
launch -> record: "launch error: failed" {style.stroke-dash: 3}
precreate -> record: "cannot create: failed" {style.stroke-dash: 3}
grant -> stopped: Specs not loaded, Module unknown {style.stroke-dash: 3}
record -> markers -> output
```

Once launched, steps 8–10 run whatever the status, so Specs and the run record stay consistent after
a failure. Steps 1–8 are the
[standard worker sequence](../../../glossary.json#concept.standard-worker-sequence); step 9 is this
Operation's own. Workers already removes the pre-created paths that stayed empty when its run ends;
step 9 repeats that removal for any it left, so the markers it then clears follow the files that
really exist. When the marker update cannot be read or written, step 9 records the failure as
`pending-markers` evidence, clears nothing and keeps the status and error chain the run already had.

The worker can read, search, edit and write files and run commands — Read, Glob, Grep, Edit, Write
and Bash on the Claude Code backend, their counterparts on pi, the default
[worker backend](../../../glossary.json#concept.worker-backend); both enforce the same grant.
Commands run in the backend's sandbox — reads the granted files and toolchain, writes only the
grant's writable files and the [run directory](../../../glossary.json#concept.run-directory), no
network. When the configuration names the project's interpreter in `python`, the brief names it and
puts it first on the worker's PATH as `python`, and the sandbox may read its environment and the
installation it resolves to; since the sandbox allows a read at a path's real location, the
directory holding each symbolic link on that way is readable too, but never the home directory or
one that holds it. The worker may use it to
try things, but its own runs are never evidence, and a file it creates outside its writable paths is
silently lost, which the brief says. The worker cannot delete a file itself: it names deletions in
its result, and the Operation performs those inside the writable paths after a clean audit and
refuses the rest.

Each resume round continues the same session with the failures and is only for failed checks — an
audit violation, a Spec gap or any other reported problem ends the run at once. Proposed deletions
and the removal of empty pre-created paths happen after the last round's checks, so the recorded
check results describe the worktree before them; a caller that needs checks of the final state runs
`test`.

## How test is built

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `test` grant | Operation, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Run the configured checks of the bound Modules and of every Module that uses one of them outside any worker, logs kept in the run directory | Operation, Check execution | a check cannot start (`failed`) |
| 3 | Generate settings, tools and the brief with the focus and failing-log tails | Workers | — |
| 4 | Launch the worker and wait for its worker result | Workers, worker | launch error/timeout (`failed`); worker `blocked`/`failed` (passed on) |
| 5 | Audit: read-only grant, so any change the audit observes is a violation; write the run record | Workers | any observed change (`failed`) |
| 6 | Return the run's output | Operation, Execution runner | — |

The `test` worker can only read and search (Read, Glob and Grep on Claude Code) and never runs a
command: running checks is the Operation's own evidence. The check logs are material: the brief
lists every check result with its log path and carries the last part of every log that did not
pass, and the run directory's check logs are made readable to the worker beside its grant, so it
can open every full log, passing ones included; nothing becomes writable. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.implementation.operations"></a>

The **Implement and test Operations** realization holds both Operations' steps, worker
instructions, result schemas and tests.

## What it relies on

<a id="uses-operations"></a>

**Operations** lists `implement` and `test` in its catalog as Operations that need a bound
workspace, `implement` writing the bound Modules' code, and names this Module as their provider;
Implementation never calls another Operation. Implementation relies on Operations'
standard worker sequence and its mapping of worker and audit outcomes to run statuses for steps 1–8
of `implement` and the worker launch of `test`; its own steps extend that sequence.

<a id="uses-execution"></a>

**Execution**'s [runner](../../../glossary.json#concept.execution-runner) runs both Operations'
steps: it reads the [workspace binding](../../../glossary.json#concept.workspace-binding), refuses
an unbound run, holds the [workspace lock](../../../glossary.json#concept.workspace-lock), settles
the Modules and inputs, and wraps the code change or test report in the run result. Implementation
relies on it for the workspace's goal and Modules, and on the lock for no other run changing the
workspace while its audit compares the workspace with the state before the worker started.

<a id="uses-workers"></a>

**Workers** turns the frozen grant into settings, launches and resumes the worker with this
Module's brief, collects its worker result, audits the worktree and writes the run record — the last
defence against a write outside the grant.

<a id="uses-checks"></a>

**Check execution** runs the bound Modules' configured checks read-only, returning a
[check result](../../../glossary.json#concept.check-result) per check — command, exit status and log
— the only evidence of whether checks passed.

<a id="uses-spec"></a>

**Spec core** computes the `implement` and `test` grants — a file bound by several Modules is
writable only when all are bound — and loads the realizations whose markers step 9 clears.
