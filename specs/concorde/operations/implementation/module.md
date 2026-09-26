# Implementation

## Purpose

Implementation changes and exercises a Module's code against its Spec. It provides two
Operations: `implement` lets a worker change the bound Modules' code toward a stated goal, then the
host audits it and runs the configured checks, resuming the worker with failures for a limited
number of rounds; `test` runs the checks through the host and lets a read-only worker interpret
the results into a test report. Neither worker ever changes a Spec — a missing or contradictory
promise stops the run with a Spec gap — and `implement`'s only Spec edit is the host clearing a
pending marker once its file exists; readiness and delivery belong to other Operations.

## Terminology

| Term | Definition |
| --- | --- |
| Code change | The result of one implement run: the files the worker changed, created or had deleted, the configured check results of the last round, the rounds used and the worker's account of the change. |
| Test report | The result of one test run: the host's configured check results for the bound Modules together with the worker's interpretation of every failure against their Specs. |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Implementation context](../../vocabulary.md#concept.concorde.implementation-context) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Operation](../module.md#concept.operations.operation) | |
| [Operation host](../module.md#concept.operations.host) | |
| [Operation result](../module.md#concept.operations.result) | |
| [Grant](../../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Brief](../../agents/workers/module.md#concept.workers.brief) | |
| [Worker result](../../agents/workers/module.md#concept.workers.worker-result) | |
| [Write audit](../../agents/workers/module.md#concept.workers.audit) | |
| [Resume round](../../agents/workers/module.md#concept.workers.resume-round) | |
| [Configured check](../../checks/module.md#concept.checks.configured-check) | |
| [Check result](../../checks/module.md#concept.checks.check-result) | |

A code change is what `implement` produced; a test report is what `test` found. Both carry check
results the host recorded itself, never a worker's word about whether checks passed.

## Usage

The main agent runs both Operations after the Specs state what the code must do and declare new
files as pending entries:

```text
concorde run implement --task <task-id> --modules <module-id>[,<module-id>…] --goal "<text>" [--input <run-id>]… [--rounds <n>]
concorde run test --task <task-id> --modules <module-id>[,<module-id>…] [--focus "<text>"]
```

`--modules` defaults to the task's Modules. `implement` takes `--goal`, admits earlier `ok` outputs
via `--input`, and `--rounds` overrides the resume-round limit (0+, default 3). For example, after
`specify` declares `src/concorde/issues/severity.py` pending, `implement --goal "accept and store
the report severity"` lets the worker create it and change the other Issues files, returning once
the checks pass or the rounds run out.

```d2
ops: Implement and test Operations
change: Code change
report: Test report
ops -> change: produces
ops -> report: produces
```

<a id="concept.implementation.code-change"></a>

`implement` returns an [Operation result](../module.md#concept.operations.result) whose `output` is
a **code change**, defined by the
[code change contract](contracts.md#contract.implementation.code-change). `status` is `ok` when the
last round's checks passed; `blocked` when the worker reported a Spec gap or another problem it
cannot solve within its grant, such as a file shared with an unbound Module, ending the
[error chain](../../vocabulary.md#concept.concorde.error-chain) in its own link, unresumed;
`failed` when checks still fail after the last round (one link per failing check, exit code and log
tail), the audit found a change outside the grant, or the host could not run the worker. A run with
no configured check ends `ok` with no check evidence, which the result states, and the main agent
should run `test` or add checks. Whenever the worker returned a result, the output holds the code
change whatever the status, and edits stay uncommitted.

<a id="concept.implementation.test-report"></a>

`test` returns a **test report**, defined by the
[test report contract](contracts.md#contract.implementation.test-report). `--focus` narrows what
the worker looks at, never which checks run; the host's results decide pass/fail, and the worker
adds, per failure, the scenario or requirement concerned, its cause, and whether the defect is
code, a test, the Spec or the environment. `status` is `ok` whenever the checks were interpreted,
passing or not; `blocked` when the worker could not interpret them; `failed` when the host could
not run them or the worker, or the audit found any change. Only `ok` carries a report; the host
evidence of any other run still lists the check results. Running `test` again is safe.

## Design

Both Operations are worker-backed. `implement` uses task type `implement`: the files bound by the
Modules' realizations are writable (pending entries included), their Specs stay read-only, and
other implementation files show by name only. `test` uses task type `test`: the same files
readable, nothing writable. Neither worker can change a Spec, so disagreement between Spec and code
can only be reported.

How Implementation is built:

```d2
implementation: Implementation {
  ops: Implement and test Operations {
    "src/concorde/implementation/"
    "prompts/workers/implement.md"
    "prompts/workers/test.md"
    "tests/concorde/implementation/"
  }
}
```

### The implement Operation

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `implement` [grant](../../spec-tooling/spec/module.md#concept.spec.grant) | Workers, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Pre-create every pending file/directory the grant makes writable, empty | Workers | cannot create (`failed`) |
| 3 | Generate settings, tools and the [brief](../../agents/workers/module.md#concept.workers.brief) | Workers | — |
| 4 | Launch the worker and wait for its [worker result](../../agents/workers/module.md#concept.workers.worker-result) | Workers, worker | launch error/timeout (`failed`) |
| 5 | [Audit](../../agents/workers/module.md#concept.workers.audit) against the grant | Workers | write outside the grant (`failed`); worker `blocked`/`failed` (passed on) |
| 6 | Run the bound Modules' [configured checks](../../checks/module.md#concept.checks.configured-check) | Workers, Check execution | — |
| 7 | While a check fails with rounds left, [resume](../../agents/workers/module.md#concept.workers.resume-round) the session, repeat 5–6 | Workers, worker | rounds used, still failing (`failed`) |
| 8 | Perform proposed deletions after a clean audit; write the run record | Workers | — |
| 9 | Remove empty pre-created paths; clear the pending marker of every entry that now exists | host, Spec core | — |
| 10 | Return the Operation result | host | — |

Once launched, steps 8–10 run whatever the status, so Specs and the run record stay consistent
after a failure. Steps 1–8 are the standard worker sequence; step 9 is this Operation's own, and the
host composes the code change from the run record itself: changed/created files, deletions
performed or refused, rounds used and the last round's checks.

The worker gets Read, Glob, Grep, Edit, Write and Bash. Bash runs in Claude Code's sandbox — reads
the granted files and toolchain, writes only the grant's writable files and the run directory, no
network. The worker may use it to try things, but its own runs are never evidence, and a file it
creates outside its writable paths is silently lost, which the brief says. The worker cannot
delete a file itself: it names deletions in its result, and the host performs those inside the
writable paths after a clean audit and refuses the rest.

Checks run outside the worker and read-only, so it cannot fake a green result or change the
worktree through one. Each resume round continues the same session with the failures and is only
for failed checks — an audit violation, a Spec gap or any other reported problem ends the run at
once.

Pre-creating pending files lets the write hook and sandbox treat them as ordinary writable files.
Steps 8–9 then keep the Specs consistent: an unused file or directory disappears and stays pending;
one that now exists has its pending marker cleared — the only Spec edit `implement` makes, an
observed fact rather than the worker's claim. A file meant to stay empty is removed and stays
pending; it needs some content to count as created.

### The test Operation

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute the `test` grant, frozen by Workers at launch | Workers, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Run the configured checks outside any worker, logs kept in the run directory | host, Check execution | a check cannot start (`failed`) |
| 3 | Generate settings, tools and the brief with the focus and failing-log tails | Workers | — |
| 4 | Launch the worker and wait for its worker result | Workers, worker | launch error/timeout (`failed`); worker `blocked` (passed on) |
| 5 | Audit: read-only grant, so any change is a violation; write the run record | Workers | any change (`failed`) |
| 6 | Return the Operation result | host | — |

The `test` worker gets Read, Glob and Grep only and never runs a command: running checks is the
host's own evidence, and the check logs are task material, so the brief carries the last part of
every log that did not pass and widens nothing. A failing check is not a failed run; it is for the
main agent to follow up with `implement`, `specify` or a decision. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.implementation.operations"></a>

The **Implement and test Operations** realization holds both Operations' host steps, worker
instructions, result schemas and tests. Each worker returns only its own output part (`addresses`,
or `failures` and `notes`); the host adds everything it observed itself.

## Relationships

```d2
implementation: Implementation
operations: Operations
agents: Agents {
  workers: Workers
}
checks: Check execution
spec: Spec core
implementation -> operations
implementation -> agents.workers
implementation -> checks
implementation -> spec
```

<a id="uses-operations"></a>

**Operations** lists `implement` and `test` in its catalog, dispatches `concorde run` to this
Module, and provides the host runner and [Operation result](../module.md#concept.operations.result)
envelope; Implementation never calls another Operation.

<a id="uses-workers"></a>

**Workers** turns the frozen grant into settings, launches and resumes the worker with this
Module's brief, collects its
[worker result](../../agents/workers/module.md#concept.workers.worker-result), audits the
worktree and writes the run record — the last defence against a write outside the grant.

<a id="uses-checks"></a>

**Check execution** runs the bound Modules'
[configured checks](../../checks/module.md#concept.checks.configured-check) read-only,
returning a [check result](../../checks/module.md#concept.checks.check-result) per check —
command, exit status and log — the only evidence of whether checks passed.

<a id="uses-spec"></a>

**Spec core** computes the `implement` and `test`
[grants](../../spec-tooling/spec/module.md#concept.spec.grant) — a file bound by several Modules is
writable only when all are bound — and loads the realizations whose markers step 9 clears.
