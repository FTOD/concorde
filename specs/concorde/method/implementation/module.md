# Implementation

## Purpose

Implementation changes and exercises a [Module](../../glossary.json#concept.module)'s code
against its [Spec](../../glossary.json#concept.spec). It provides two Operations: `implement`
lets a worker change the bound Modules' code toward a stated goal, then audits it and runs the
configured checks, resuming the worker with failures for a limited number of rounds; `test` runs the
checks itself and lets a read-only worker interpret the results into a
test report. Neither worker ever changes a Spec — a
missing or contradictory promise stops the run with a
[Spec gap](../../glossary.json#concept.spec-gap) — and neither
[Operation](../../glossary.json#concept.operation) edits one either; readiness and delivery are
the
[execution commands](../../glossary.json#concept.execution-command) of other Modules.

## Core concepts

### Workers change or read code, checks decide

Both Operations are worker-backed, and both task types read the whole project's code, the
Protocol's ProjectImplementation, as [Spec core's grants](../../spec-tooling/spec/module.md#grants)
explain. `implement` uses [task type](../../glossary.json#concept.task-type) `implement`: the
files bound by the bound Modules' realizations, their implementation scope, are the only writable
ones, and their Specs stay read-only. `test` uses task type `test`: the same files readable, nothing
writable. Neither worker can change a Spec, so disagreement between Spec and code can only be
reported.

Whether the code passes is never the worker's word. Checks run outside the worker and read-only,
so it cannot fake a green result or change the worktree through one: in `implement` the
[configured checks](../../glossary.json#concept.configured-check) run after the worker and send
their failures back to it as a [resume round](../../glossary.json#concept.resume-round), and in
`test` the Operation runs them first and the worker only interprets their results. A failing check
is not a failed `test` run; it is for the task level to follow up with `implement`, `specify` or a
decision.

### The code change and the test report

`implement` returns a [run result](../../glossary.json#concept.run-result) whose `output` is
a **code change**, defined by the
[code change contract](contracts.md#contract.implementation.code-change), which the Operation
composes from the [run record](../../glossary.json#concept.run-record) itself:
changed/created files, deletions performed or refused, rounds used and the last round's checks.
`test` returns a **test report**, defined by the
[test report contract](contracts.md#contract.implementation.test-report): the Operation's results
decide pass/fail, and the worker adds, per failure, the scenario or requirement concerned, its
cause, and whether the defect is code, a test, the Spec or the environment. Each worker returns
only its own output part (`addresses`, or `failures` and `notes`); the Operation adds everything it
observed itself.

### The checked Modules

The set of checked Modules is the same for both Operations: the bound Modules together with every
Module that uses one of them, directly or through further uses, which Method computes from the
workspace's Specs through Spec core before it asks Check execution to run their checks. A selective check runs only when some test verifies a scenario of
those Modules, and a readiness check never runs here; a check that does not run is not listed.

### New files

A worker writes only the files its Modules bind and new files below the directories they bind,
since a realization binds only files that exist. A file the change needs anywhere else is created
and bound to its Module by the task level before the run, with the least content its format needs
to be valid, so that the grant makes it writable like any other bound file; a worker that needs a
file nobody created returns `blocked` naming it. `implement` itself creates no file outside the
worker and changes no Spec.

## Overview

The two Operations side by side: `implement` checks after its worker and loops back to it, `test`
checks before its worker and only asks it to explain the results.

```d2 illustrative
implement: implement {
  direction: down
  grant: "Freeze the implement grant"
  worker: "Worker changes the\nbound Modules' code"
  checks: "Run the configured checks\noutside the worker"
  output: "Code change"
  grant -> worker -> checks
  worker <- checks: "a check fails, rounds left:\nresume with the failures" {style.stroke-dash: 3}
  checks -> output: "all pass, or\nrounds used up"
}
test: test {
  direction: down
  grant: "Freeze the test grant"
  checks: "Run the configured checks"
  worker: "Read-only worker interprets\nthe check results"
  output: "Test report"
  grant -> checks -> worker -> output
  worker -> worker: "a failed check not interpreted once:\nresume once with the mismatches" {style.stroke-dash: 3}
}
```

## Running implement and test

The caller runs both Operations after the Specs state what the code must do and every new file
outside the bound directories has been created and bound:

```text
concorde run implement [--modules <module-id>[,<module-id>…]] --goal "<text>" [--input <run-id>]… [--rounds <n>]
concorde run test [--modules <module-id>[,<module-id>…]] [--focus "<text>"]
```

Both work on the [workspace](../../glossary.json#concept.workspace) whose binding lies in the
worktree they start in and need one: an [unbound run](../../glossary.json#concept.unbound-run) of
either is refused. `--modules` defaults to the binding's Modules. Each worker's brief carries the
workspace's goal as context, as `specify`'s does, beside the run's own argument: `implement`'s
`--goal` states the run's own task, which may be one step of the workspace's goal, and `test`'s
`--focus` narrows what its worker looks at, never which checks run. `implement` also admits earlier
`ok` outputs via `--input`, and `--rounds` sets the resume-round limit (0 or more); without it the
limit is the [worker configuration](../../glossary.json#concept.worker-configuration)'s
`limits.rounds`, and three when that is not set. For example, after the task level created
`src/concorde/issues/severity.py` and bound it to Issues,
`implement --goal "accept and store the report severity"` lets the worker fill it and change the
other Issues files, returning once the checks pass or the
rounds run out.

`implement`'s `status` is `ok` when the last round's checks passed; `blocked` when the worker
reported a Spec gap or another problem it cannot solve within its grant, such as a change that needs
a file only an unbound Module binds, ending the
[error chain](../../glossary.json#concept.error-chain) in its own link, unresumed; `failed` when
checks still fail after the last round (one link per failing check, exit code and log tail), the
audit found a change outside the grant, the worker ended `failed` or could not be run, or the grant
could not be computed — for instance because a writable file is also bound by an unbound Module,
which is refused before any worker starts. A run with no configured check ends `ok` with no check
evidence, which the result states, and the caller should run `test` or add checks. Whenever the
worker returned a result, the output holds the code change whatever the status, and edits stay
uncommitted.

`test`'s `status` is `ok` whenever the checks were interpreted, passing or not; `blocked` when the
worker could not interpret them; `failed` when the checks or the worker could not be run, the worker
ended `failed`, the audit found any change, or the worker's `failures` still do not hold exactly one
entry per check that did not pass after its resume round (`failures_unaccounted`). Only `ok` carries a report; the host evidence of any
other run still lists the check results. Running `test` again is safe.

## How implement is built

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `implement` [grant](../../glossary.json#concept.grant) | Operation, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Generate settings, tools and the [brief](../../glossary.json#concept.brief) | Workers | — |
| 3 | Launch the worker and wait for its [worker result](../../glossary.json#concept.worker-result) | Workers, worker | launch error/timeout (`failed`) |
| 4 | [Audit](../../glossary.json#concept.write-audit) against the grant | Workers | write outside the grant (`failed`); worker `blocked`/`failed` (passed on) |
| 5 | After a clean audit of a worker that ended `ok`, call the round validation, which runs the configured checks of the bound Modules and of every Module that uses one of them | Workers, Operation, Check execution | — |
| 6 | While the round validation reports a failing check with rounds left, resume the session with the failures, repeat 4–5 | Workers, worker | rounds used, still failing (`failed`) |
| 7 | Perform proposed deletions after a clean audit; write the run record | Workers | — |
| 8 | Compose the code change from the run record and return it | Operation, Execution runner | — |

The main path, the resume loop and the exits, which all meet at steps 7–8:

```d2 illustrative
direction: down
grant: 1 Freeze the implement grant
brief: 2 Settings, tools and brief
launch: 3 Launch or resume the worker
audit: 4 Audit against the grant
checks: 5 Run the configured checks
record: "7 Proposed deletions after a clean audit, run record"
output: 8 Return the code change
stopped: "failed, no worker launched" {shape: oval}
grant -> brief -> launch -> audit
audit -> checks: worker ok, audit clean
launch <- checks: "6 a check fails, rounds left: resume with the failures"
checks -> record: "all passed, or none configured: ok"
checks -> record: "still failing, rounds used up: failed" {style.stroke-dash: 3}
audit -> record: "write outside the grant, timeout, limit reached, invalid result: failed;\nworker blocked or failed: its status, unresumed" {style.stroke-dash: 3}
launch -> record: "launch error: failed" {style.stroke-dash: 3}
grant -> stopped: Specs not loaded, Module unknown {style.stroke-dash: 3}
record -> output
```

Once launched, steps 7–8 run whatever the status, so the run record and the output stay consistent
after a failure. Steps 1–7 are the
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence); step 8 is this
Operation's own.

The worker can read, search, edit and write files and run commands — Read, Glob, Grep, Edit, Write
and Bash on the Claude Code backend, their counterparts on pi, the default
[worker backend](../../glossary.json#concept.worker-backend); both enforce the same grant.
Commands run in the backend's sandbox — reads the granted files and toolchain, writes only the
grant's writable files and the `work/`, `home/` and `tmp/` directories of the worker's
[runtime directory](../../glossary.json#concept.runtime-directory), never its
[run directory](../../glossary.json#concept.run-directory), as
[Workers' access tables](../../worker-harness/workers/launch.md#run-directory-and-runtime-directory) say, no
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
happen after the last round's checks, so the recorded
check results describe the worktree before them; a caller that needs checks of the final state runs
`test`.

## How test is built

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `test` grant | Operation, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Run the configured checks of the bound Modules and of every Module that uses one of them outside any worker, logs kept in the run directory | Operation, Check execution | a check cannot start (`failed`) |
| 3 | Generate settings, tools and the brief with the focus and failing-log tails | Workers | — |
| 4 | Launch the worker and wait for its worker result | Workers, worker | launch error/timeout (`failed`); worker `blocked`/`failed` (passed on) |
| 5 | Audit: read-only grant, so any change the audit observes is a violation | Workers | any observed change (`failed`) |
| 6 | After a clean audit of a worker that ended `ok`, call the round validation, which checks that `failures` holds exactly one entry per check that did not pass and none for a check that passed; while it does not and the one resume round is left, resume the session with every mismatch and repeat 4–6; write the run record | Workers, Operation | — |
| 7 | Check the `failures` once more and return the run's output | Operation, Execution runner | `failures` still not one entry per check that did not pass (`failed`, `failures_unaccounted`) |

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

**Operations**, Execution's Operation framework, is what both Operations plug into: Method registers
their definitions as Operations that need a bound workspace, `implement` writing the bound Modules'
code, naming this Module as their provider
([Method](../module.md#the-operations-and-commands-it-provides)); Implementation never calls another
Operation. Implementation relies on Method's
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence) and its mapping of worker and audit outcomes to run statuses for steps 1–8
of `implement` and the worker launch of `test`; its own steps extend that sequence.

<a id="uses-execution"></a>

**Execution**'s [runner](../../glossary.json#concept.execution-runner) runs both Operations'
steps: it reads the [workspace binding](../../glossary.json#concept.workspace-binding), refuses
an unbound run, holds the [workspace lock](../../glossary.json#concept.workspace-lock), settles
the Modules and inputs, and wraps the code change or test report in the run result. Implementation
relies on it for the workspace's goal and Modules, and on the lock for no other run changing the
workspace while its audit compares the workspace with the state before the worker started.

<a id="uses-workers"></a>

**Workers**, in the worker harness, receives the frozen grant as data and `implement`'s round
validation, which runs the checks, through the standard worker sequence; it turns the grant into
settings, launches and resumes the worker with this Module's instructions and what the round
validation reports, collects its worker result, audits the worktree and writes the run record — the
last defence against a write outside the grant.

<a id="uses-checks"></a>

**Check execution** runs the checked Modules' configured checks read-only, for `implement`'s round
validation and `test`'s own step, returning a
[check result](../../glossary.json#concept.check-result) per check — command, exit status and log
— the only evidence of whether checks passed.

<a id="uses-spec"></a>

**Spec core** computes the `implement` and `test` grants — a file bound by several Modules is
writable only when all are bound — and loads the realizations whose markers step 9 clears.
