# Implementation

## Purpose

Implementation changes and exercises a [Module](../../../glossary.json#concept.module)'s code
against its [Spec](../../../glossary.json#concept.spec). It provides two Operations: `implement`
lets a worker change the bound Modules' code toward a stated goal, then audits it and runs the
configured checks, resuming the worker with failures for a limited number of rounds; `test` runs the
checks itself and lets a read-only worker interpret the results into a
[test report](../../../glossary.json#concept.test-report). Neither worker ever changes a Spec — a
missing or contradictory promise stops the run with a
[Spec gap](../../../glossary.json#concept.spec-gap) — and `implement`'s only Spec edit is the
[Operation](../../../glossary.json#concept.operation) clearing a pending marker once its file
exists; readiness and delivery are the
[execution commands](../../../glossary.json#concept.execution-command) of other Modules.

## Usage

The [main agent](../../../glossary.json#concept.main-agent) runs both Operations after the Specs
state what the code must do and declare new files as pending entries:

```text
concorde run implement [--modules <module-id>[,<module-id>…]] --goal "<text>" [--input <run-id>]… [--rounds <n>]
concorde run test [--modules <module-id>[,<module-id>…]] [--focus "<text>"]
```

Both work on the [workspace](../../../glossary.json#concept.workspace) whose binding lies in the
worktree they start in and need one: an [unbound run](../../../glossary.json#concept.unbound-run) of
either is refused. `--modules` defaults to the binding's Modules, and the worker is briefed with the
workspace's goal. `implement` takes `--goal`, admits earlier `ok` outputs via `--input`, and
`--rounds` overrides the resume-round limit (0+, default 3). For example, after `specify` declares
`src/concorde/issues/severity.py` pending, `implement --goal "accept and store the report severity"`
lets the worker create it and change the other Issues files, returning once the checks pass or the
rounds run out.

<a id="concept.code-change"></a>

`implement` returns a [run result](../../../glossary.json#concept.run-result) whose `output` is
a **[code change](../../../glossary.json#concept.code-change)**, defined by the
[code change contract](contracts.md#contract.implementation.code-change). `status` is `ok` when the
last round's checks passed; `blocked` when the worker reported a Spec gap or another problem it
cannot solve within its grant, such as a file shared with an unbound Module, ending the
[error chain](../../../glossary.json#concept.error-chain) in its own link, unresumed;
`failed` when checks still fail after the last round (one link per failing check, exit code and log
tail), the audit found a change outside the grant, or the worker could not be run. A run with
no configured check ends `ok` with no check evidence, which the result states, and the main agent
should run `test` or add checks. Whenever the worker returned a result, the output holds the code
change whatever the status, and edits stay uncommitted.

<a id="concept.test-report"></a>

`test` returns a **test report**, defined by the
[test report contract](contracts.md#contract.implementation.test-report). `--focus` narrows what the
worker looks at, never which checks run; the Operation's results decide pass/fail, and the worker
adds, per failure, the scenario or requirement concerned, its cause, and whether the defect is code,
a test, the Spec or the environment. `status` is `ok` whenever the checks were interpreted, passing
or not; `blocked` when the worker could not interpret them; `failed` when the checks or the worker
could not be run, or the audit found any change. Only `ok` carries a report; the host evidence of
any other run still lists the check results. Running `test` again is safe.

## Design

Both Operations are worker-backed. `implement` uses
[task type](../../../glossary.json#concept.task-type) `implement`: the files bound by the Modules'
realizations are writable (pending entries included), their Specs stay read-only, and other
implementation files show by name only. `test` uses task type `test`: the same files readable,
nothing writable. Neither worker can change a Spec, so disagreement between Spec and code can only
be reported.

### The implement Operation

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `implement` [grant](../../../glossary.json#concept.grant) | Workers, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Pre-create every pending file/directory the grant makes writable, empty | Workers | cannot create (`failed`) |
| 3 | Generate settings, tools and the [brief](../../../glossary.json#concept.brief) | Workers | — |
| 4 | Launch the worker and wait for its [worker result](../../../glossary.json#concept.worker-result) | Workers, worker | launch error/timeout (`failed`) |
| 5 | [Audit](../../../glossary.json#concept.write-audit) against the grant | Workers | write outside the grant (`failed`); worker `blocked`/`failed` (passed on) |
| 6 | Run the bound Modules' [configured checks](../../../glossary.json#concept.configured-check) | Workers, Check execution | — |
| 7 | While a check fails with rounds left, [resume](../../../glossary.json#concept.resume-round) the session, repeat 5–6 | Workers, worker | rounds used, still failing (`failed`) |
| 8 | Perform proposed deletions after a clean audit; write the [run record](../../../glossary.json#concept.run-record) | Workers | — |
| 9 | Remove empty pre-created paths; clear the pending marker of every entry that now exists | Operation, Spec core | — |
| 10 | Return the run's output | Operation, Execution runner | — |

Once launched, steps 8–10 run whatever the status, so Specs and the run record stay consistent after
a failure. Steps 1–8 are the
[standard worker sequence](../../../glossary.json#concept.standard-worker-sequence); step 9 is this
Operation's own, and the Operation composes the code change from the run record itself:
changed/created files, deletions performed or refused, rounds used and the last round's checks.

The worker gets Read, Glob, Grep, Edit, Write and Bash. Bash runs in Claude Code's sandbox — reads
the granted files and toolchain, writes only the grant's writable files and the
[run directory](../../../glossary.json#concept.run-directory), no network. The worker may use it to
try things, but its own runs are never evidence, and a file it creates outside its writable paths is
silently lost, which the brief says. The worker cannot delete a file itself: it names deletions in
its result, and the Operation performs those inside the writable paths after a clean audit and
refuses the rest.

Checks run outside the worker and read-only, so it cannot fake a green result or change the
worktree through one. Each resume round continues the same session with the failures and is only
for failed checks — an audit violation, a Spec gap or any other reported problem ends the run at
once.

Pre-creating pending files lets the [write hook](../../../glossary.json#concept.write-hook) and
sandbox treat them as ordinary writable files. Steps 8–9 then keep the Specs consistent: an unused
file or directory disappears and stays pending; one that now exists has its pending marker cleared —
the only Spec edit `implement` makes, an observed fact rather than the worker's claim. A file meant
to stay empty is removed and stays pending; it needs some content to count as created.

### The test Operation

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute the `test` grant, frozen by Workers at launch | Workers, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Run the configured checks outside any worker, logs kept in the run directory | Operation, Check execution | a check cannot start (`failed`) |
| 3 | Generate settings, tools and the brief with the focus and failing-log tails | Workers | — |
| 4 | Launch the worker and wait for its worker result | Workers, worker | launch error/timeout (`failed`); worker `blocked` (passed on) |
| 5 | Audit: read-only grant, so any change is a violation; write the run record | Workers | any change (`failed`) |
| 6 | Return the run's output | Operation, Execution runner | — |

The `test` worker gets Read, Glob and Grep only and never runs a command: running checks is the
Operation's own evidence, and the check logs are material, so the brief carries the last part of
every log that did not pass and widens nothing. A failing check is not a failed run; it is for the
main agent to follow up with `implement`, `specify` or a decision. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.implementation.operations"></a>

The **Implement and test Operations** realization holds both Operations' steps, worker
instructions, result schemas and tests. Each worker returns only its own output part (`addresses`,
or `failures` and `notes`); the Operation adds everything it observed itself.

### Outside

<a id="uses-operations"></a>

**Operations** lists `implement` and `test` in its catalog as Operations that need a bound
workspace, `implement` writing the bound Modules' code, and names this Module as their provider;
Implementation never calls another Operation.

<a id="uses-execution"></a>

**Execution**'s [runner](../../../glossary.json#concept.execution-runner) runs both Operations'
steps: it reads the [workspace binding](../../../glossary.json#concept.workspace-binding), refuses
an unbound run, holds the [workspace lock](../../../glossary.json#concept.workspace-lock), settles
the Modules and inputs, and wraps the code change or test report in the
[run result](../../../glossary.json#concept.run-result). Implementation relies on it for the
workspace's goal and Modules, and on the lock for no other run changing the workspace while its
audit compares the workspace with the state before the worker started.

<a id="uses-workers"></a>

**Workers** turns the frozen grant into settings, launches and resumes the worker with this
Module's brief, collects its
[worker result](../../../glossary.json#concept.worker-result), audits the
worktree and writes the run record — the last defence against a write outside the grant.

<a id="uses-checks"></a>

**Check execution** runs the bound Modules'
[configured checks](../../../glossary.json#concept.configured-check) read-only,
returning a [check result](../../../glossary.json#concept.check-result) per check —
command, exit status and log — the only evidence of whether checks passed.

<a id="uses-spec"></a>

**Spec core** computes the `implement` and `test`
[grants](../../../glossary.json#concept.grant) — a file bound by several Modules is
writable only when all are bound — and loads the realizations whose markers step 9 clears.
