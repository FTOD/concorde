# Check execution

## Purpose

Check execution is the deterministic service of the execution part that runs a project's
[configured checks](../../glossary.json#concept.configured-check), such as a test suite or linter.
It returns their status and logs without model reasoning. In Concorde, Method calls it in these
ways:

- through the round validations its Operations give the worker harness between a worker's rounds
- directly through Operations such as testing and code review
- through the [execution commands](../../glossary.json#concept.execution-command) `task-validation`
  and `delivery`

Checks read the worktree but cannot directly change its files. The boundary restricts filesystem
writes only. It does not restrict these aspects:

- reads
- network
- credentials

The service records which inputs were checked. If the inputs differ after the run from before it,
the service refuses a result. It never decides whether a passing check means correct code or
whether a workspace is ready to deliver. It reads no [Spec](../../glossary.json#concept.spec).
Its caller says:

- which Modules' checks run
- which files a Module's result depends on
- which tests a selective check runs

## Core concepts

For a project checked with `pytest tests/`, this service performs these steps:

- starts that command
- waits for it
- returns its exit status and captured output

Pytest performs the assertions. Check execution manages these aspects of the command:

- the command itself
- its boundary
- its timeout
- its result

A test answers whether the code is right. A check answers what one command produced on exactly
this input, and whether that result can be trusted. A configured command can itself depend on
external services, so its output need not be identical on every run.

### Configured checks and their results

<a id="concept.configured-check"></a><a id="concept.check-result"></a>

A **configured check** is declared in its Module's own checks file,
`.concorde/checks/<module id>.json`, for example in `.concorde/checks/module.checks.json`:

```json
{"checks": [
  {"id": "check.checks.runtime",
   "argv": ["{python}", "-m", "pytest", "-p", "no:cacheprovider", "tests/concorde/harness/checks"],
   "timeout_seconds": 300,
   "inputs": ["pyproject.toml", "conftest.py", "tests/concorde/support", "src"]}
]}
```

One file per Module keeps parallel changes to different Modules' checks apart. The files stay
under `.concorde/` with the project configuration rather than beside the Module. This is because
a check command is trusted host input. The work it verifies must not be able to rewrite that
command. The checks files are Check execution's own format
([checks files](service.md#checks-files)). Check execution validates that format itself. The
Module identity a file is named after is a label. So a project checks code without the spec part
installed.

The check service receives these inputs:

- a worktree
- the Modules to run
- the files each Module's result depends on
- a log directory

In Concorde, Method's steps select the Modules and name their implementation files through the
Spec tooling. For each [Module](../../glossary.json#concept.module), the service performs these
steps:

- digests the relevant input
- runs each check in the boundary
- saves logs
- returns one **check result** per check

A check result records these items:

- The check and its Module.
- The status and the exit code.
- The digest of the input it measured.
- The saved log with the digest of that log.

Each check result also names each write of the check's trace node the operating system refused.
After the run, a digest mismatch fails with `stale_evidence`, because the result would vouch for
input that changed. A stored result stays valid only while a fresh measurement matches it.
[The check service](service.md) gives the exact declaration and records.

### The read-only check boundary

<a id="concept.read-only-check-boundary"></a>

Inside the **[read-only check boundary](../../glossary.json#concept.read-only-check-boundary)**,
any of these file actions fails at the system call:

- create
- change
- rename
- delete

A command writes only to its **check scratch**, fresh each run. These variables point to the
scratch:

- `TMPDIR`
- `XDG_CACHE_HOME`
- `CONCORDE_CHECK_TMPDIR`
- `CONCORDE_CHECK_REPORT_DIR`

If a check hard-codes a cache or report path inside the project, it fails and must be pointed at
the scratch. A source-rewriting tool, e.g. a fix-mode formatter, isn't a check. Only Linux with a
root-owned bubblewrap and the needed namespaces is supported. When the boundary cannot be
established, the command does not start, and the run is refused with a sandbox error. There is no subprocess fallback. [The boundary](boundary.md)
describes the environment and mounts.

### Diagnostic spans

The runner marks sandbox setup and each command as a **diagnostic span**. Spans are kept only in
a caller-opened trace or under `CONCORDE_DIAGNOSTIC_TIMING_DIR`. Spans never change a run's
outcome. [The timing spans](timing.md) describes the record and summary.

## Overview

Two pictures show Check execution: its place among the programs that call it, and what one call
does.

### Its place in the levels of work

Check execution is no level of the [levels of work](../../module.md#the-levels-of-work). It is a
service the runs call in-process. Since the runs that call it hold their workspace's lock while it
works, Check execution cannot itself be a run. Only programs call it, never a model. Its callers
are the steps of runs at level 4 and the round validation a run's step hands the worker harness.
The harness calls that round validation between a worker's rounds. Check execution calls nothing
above it. It starts none of these:

- a worker
- a run
- an agent

```d2 illustrative
method: Method {
  validation: "Round validations of\nworker-backed steps"
  ops: "Steps of test, code_review,\nsurvey and code_to_spec"
  readiness: "Validation's steps, in\ntask-validation and delivery"
}
harness: Worker harness
checks: Check execution
harness -> method.validation: "calls after\neach clean round"
method.validation -> checks
method.ops -> checks
method.readiness -> checks
```

Check execution knows none of its callers. They rely on these:

- the [check result](../../glossary.json#concept.check-result)
- the stale-measurement rule
- the boundary refusing to run rather than running a check unconfined

Every call returns to the caller's step. The check results go up as that caller's evidence. A
failure goes up as this Module's own error link. Examples are `stale_evidence` or a boundary that
cannot be established. The `service_error` of [the check service](service.md) makes that link.
The caller keeps it as a cause under its link. The check result is owned here, next to the runner
that produces it. So every caller consumes one record and never runs checks another way.

Every check it runs is a [trace node](../../glossary.json#concept.trace-node) with its log. The
node is placed only in the directory the caller names. That directory is the `checks/` of the
calling run's or worker round's node in the [run store](../../glossary.json#concept.run-store).
This Module hands a check's output to no worker itself. A round validation puts the bounded tail
of a failed check's log into what it asks the worker to repair. The `test` and `code_review`
Operations are consumers of their own. They make the full logs of the checks they ran readable to
their workers as task material.

The calling code, not an AI worker, decides when to run checks:

| Caller, in Concorde | Use of the result |
| --- | --- |
| The round validation of a worker-backed step | After a clean audit, record the checks and pass failures to the worker's next [resume round](../../glossary.json#concept.resume-round) when allowed |
| `test` and `code_review` Operations | Supply recorded check results to a worker for interpretation or review |
| `task-validation` and `delivery` execution commands | Use the results in the readiness decision; Delivery reuses Validation's steps |

These are ordinary service calls inside a run, not nested runs. Check execution launches no
Concorde worker. Users configure commands and see the results through the runs that call it.
There is no separate Check execution command to start.

### One call of the check service

A caller names these:

- a worktree
- the Modules to run
- a log directory

For each Module, the service performs these steps:

- measures the inputs
- runs each check in the boundary
- measures again

If the service cannot establish a boundary, it starts no command. If a measurement changed, the
call fails with `stale_evidence`.

```d2 illustrative
direction: down
select: "For each Module the caller names:\nselect its checks"
before: "Digest the Module's inputs"
boundary: "Set up the read-only boundary\nwith a fresh scratch"
run: "Run the check's command\nwithin its time limit"
logs: "Save its log and\nits check result"
after: "Digest the Module's inputs again"
result: "Return one check result\nper check"
refused: "Refused with a sandbox error:\nno command starts"
stale: "Fails with stale_evidence"
select -> before -> boundary -> run -> logs
logs -> boundary: "next check"
logs -> after: "last check of the Module"
after -> result: "digests match"
after -> stale: "digests differ" {style.stroke-dash: 3}
boundary -> refused: "cannot be established" {style.stroke-dash: 3}
```

## What the boundary enforces

<a id="design"></a>

Checks produce evidence that a workspace is ready. Only if the check could not change what it
measured is that evidence worth having. So one guarantee is enforced. The boundary states plainly
what it leaves out:

| Concern | Enforced |
| --- | --- |
| Writing any host file outside the scratch, through any path name, hard link, inherited descriptor or nested namespace | Yes, by the operating system |
| Descendant processes outliving the run | Yes: the host ends the whole process tree |
| Reading files the developer's user can read | Not enforced |
| Network access | Not enforced: the network namespace is shared with the host |
| Host sockets: abstract Unix sockets and filesystem sockets such as an SSH agent or a container daemon | Not enforced: a read-only mount does not stop connecting to a socket, so a command could ask a host service to act, including changing the project |
| Environment and credentials | Not enforced by the boundary, which passes on whatever environment its caller gives; the check service builds that environment from `PATH`, `LANG`, the proxy and TLS trust variables and the check's own `env`, so a credential reaches a configured check only through one of those, such as a proxy address carrying one, or through a file the check can read |

The omissions are deliberate. Configured checks are commands the project itself chose. The host
runs them, never a worker. A worker only receives their results. The boundary cannot stop a
process outside it, or a host service a check talked to, from changing the project during the run.
Because of this, the service measures its input before and after the run. It turns that race into
`stale_evidence` rather than false evidence. A change undone before the second measurement is not
detected.

## Inside

The check runner runs each configured check inside the read-only boundary. The boundary provides
the scratch the check may write. The runner records a check result and diagnostic spans.

```d2
checks: Check execution {
  runner: Check runner {
    "src/concorde/execution/checks/"
  }
  check: Configured check
  result: Check result
  boundary: Read-only check boundary
  runner -> check: runs
  runner -> result: records
  runner -> boundary: enforces
  check -> boundary: runs inside
}
```

The timing recorder lives here because check runs and sandbox setup are the slowest deterministic
steps a host takes. The recorder is passive and holds no content. So it can stay on in any run.
The open trace and the enclosing span are held per execution context. Each thread or asynchronous
task therefore writes its timings into the trace opened where its work started. When a scope
ends, the thread or task gets its previous trace back. If a sink fails, the recorder performs
these actions:

- catches the failure
- marks the trace incomplete
- writes the one `CONCORDE_TIMING_INCOMPLETE` line

Nothing else follows from the sink failure. The work's own result or exception passes through a
span unchanged.

<a id="realization.checks.runner"></a>The **check runner** has three parts:

- The executor mounts the filesystem read-only except the scratch. It holds a process descriptor
  to end every descendant before removing the scratch.
- The timing recorder keeps diagnostic spans.
- The check service selects a Module's checks. It measures input before and after the run,
  turning a concurrent change into `stale_evidence`. It owns the check result, so no consumer runs
  checks another way.

<a id="realization.checks.tests"></a>The **check tests** run real sandboxed processes. Where the
platform can't enforce the boundary, the tests fail rather than skip. They show what the boundary
blocks, not that checks are adequate. The tests exercise the timing recorder and summary.

## What Check execution relies on

<a id="uses-tracing"></a>

**Tracing** gives every check the shape of a [trace node](../../glossary.json#concept.trace-node).
Before the command starts and after it ends, the check service writes that node through Tracing's
library in the folder its caller names. Tracing also gives the error contract the check service's
failures follow. The check service relies on the
[node contract](../../kernel/tracing/contracts.md#contract.tracing.node).

Check execution relies on no other Module and on no part but the kernel. Its caller supplies
these:

- the Modules it checks
- the files their results depend on
- the tests a selective check runs

Its paths follow the canonical project-relative form of the Kernel's
[typed values](../../kernel/contracts.md#typed-values).
