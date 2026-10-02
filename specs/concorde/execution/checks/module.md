# Check execution

## Purpose

Check execution is the deterministic service of the execution part that runs a project's
[configured checks](../../glossary.json#concept.configured-check), such as a test suite or linter,
and returns their status and logs without model reasoning. In Concorde it is called by Method: by
the round validations its Operations give the worker harness between a worker's rounds, directly by
Operations such as testing and code review, and by the
[execution commands](../../glossary.json#concept.execution-command) `task-validation` and
`delivery`. Checks read the worktree but cannot directly change its files; the boundary restricts
filesystem writes only, not reads, network or credentials. The service records which inputs were
checked and refuses a result if they differ after the run from before it. It never decides whether
a passing check means correct code or whether a workspace is ready to deliver, and it reads no
[Spec](../../glossary.json#concept.spec): which Modules' checks run, which files a Module's result
depends on and which tests a selective check runs are its caller's to say.

## Core concepts

For a project checked with `pytest tests/`, this service starts that command, waits for it and
returns its exit status and captured output. Pytest performs the assertions; Check execution
manages the command, its boundary, timeout and result. A test answers whether the code is right; a
check answers what one command produced on exactly this input, and whether that result can be
trusted. A configured command can itself depend on external services, so its output need not be
identical on every run.

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

One file per Module keeps parallel changes to different Modules' checks apart, and the files stay
under `.concorde/` with the project configuration rather than beside the Module: a check command is
trusted host input, which the work it verifies must not be able to rewrite. The checks files are
Check execution's own format ([checks files](service.md#checks-files)), which it validates itself;
the Module identity a file is named after is a label, so a project checks code without the spec part
installed.

The check service is called with a worktree, the Modules to run, the files each Module's result
depends on and a log directory; in Concorde, Method's steps select the Modules and name their
implementation files through the Spec tooling. For each [Module](../../glossary.json#concept.module)
it digests the relevant input, runs each check in the boundary, saves logs, and returns one
**check result** per check. A digest mismatch after the run
fails with `stale_evidence`, because the result would vouch for input that changed; a stored result
stays valid only while a fresh measurement matches it. Exact declaration and records:
[the check service](service.md).

### The read-only check boundary

<a id="concept.read-only-check-boundary"></a>

Inside the **[read-only check boundary](../../glossary.json#concept.read-only-check-boundary)**, any
file create/change/rename/delete fails at the system call; a command writes only to its
**check scratch**, pointed to by `TMPDIR`,
`XDG_CACHE_HOME`, `CONCORDE_CHECK_TMPDIR` and `CONCORDE_CHECK_REPORT_DIR`, fresh each run. A check
that hard-codes a cache or report path inside the project fails and must be pointed at the scratch;
a source-rewriting tool, e.g. a fix-mode formatter, isn't a check. When the boundary cannot be
established (only Linux with a root-owned bubblewrap and the needed namespaces is supported), the
command does not start and the run is refused with a sandbox error; there is no subprocess fallback.
Environment/mounts: [the boundary](boundary.md).

### Diagnostic spans

The runner marks sandbox setup and each command as a
**diagnostic span**, kept only in a caller-opened
trace or under `CONCORDE_DIAGNOSTIC_TIMING_DIR`; spans never change a run's outcome. Record/summary:
[the timing spans](timing.md).

## Overview

Two pictures show Check execution: its place among the programs that call it, and what one call
does.

### Its place in the levels of work

Check execution is no level of the [levels of work](../../module.md#the-levels-of-work): it is a
service the runs call in-process, and it cannot itself be a run, since the runs that call it hold
their workspace's lock while it works. Only programs call it, never a model: the steps of runs at
level 4, and the round validation a run's step hands the worker harness, which the harness calls
between a worker's rounds. It calls nothing above it and starts no worker, run or agent.

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

Check execution knows none of its callers. They rely on the
[check result](../../glossary.json#concept.check-result), the stale-measurement rule, and the
boundary refusing to run rather than running a check unconfined. Every call returns to the caller's
step: the check results go up as that caller's evidence, and a failure, such as `stale_evidence` or
a boundary that cannot be established, goes up as this Module's own error link, made by
`service_error` of [the check service](service.md), which the caller keeps as a cause under its
link. The check result is owned here, next to the runner that produces it, so every caller consumes
one record and never runs checks another way. Every check it runs is a
[trace node](../../glossary.json#concept.trace-node) with its log, placed only in the directory the
caller names, the `checks/` of the calling run's or worker round's node in the
[run store](../../glossary.json#concept.run-store). This Module hands a check's output to no worker
itself: a round validation puts the bounded tail of a failed check's log into what it asks the
worker to repair, and the `test` and `code_review` Operations, consumers of their own, make the full
logs of the checks they ran readable to their workers as task material.

The calling code, not an AI worker, decides when to run checks:

| Caller, in Concorde | Use of the result |
| --- | --- |
| The round validation of a worker-backed step | After a clean audit, record the checks and pass failures to the worker's next [resume round](../../glossary.json#concept.resume-round) when allowed |
| `test` and `code_review` Operations | Supply recorded check results to a worker for interpretation or review |
| `task-validation` and `delivery` execution commands | Use the results in the readiness decision; Delivery reuses Validation's steps |

These are ordinary service calls inside a run, not nested runs. Check execution launches no
Concorde worker. Users configure commands and see the results through the runs that call it; there
is no separate Check execution command to start.

### One call of the check service

A caller names a worktree, the Modules to run and a log directory. For each Module the service
measures the inputs, runs each check in the boundary and measures again; a boundary it cannot
establish starts no command, and a measurement that changed fails the call with `stale_evidence`:

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

Checks produce evidence that a workspace is ready, and that evidence is only worth having if
the check could not change what it measured. So one guarantee is enforced, and the boundary states
plainly what it leaves out:

| Concern | Enforced |
| --- | --- |
| Writing any host file outside the scratch, through any path name, hard link, inherited descriptor or nested namespace | Yes, by the operating system |
| Descendant processes outliving the run | Yes: the host ends the whole process tree |
| Reading files the developer's user can read | Not enforced |
| Network access | Not enforced: the network namespace is shared with the host |
| Host sockets: abstract Unix sockets and filesystem sockets such as an SSH agent or a container daemon | Not enforced: a read-only mount does not stop connecting to a socket, so a command could ask a host service to act, including changing the project |
| Environment and credentials | Not enforced by the boundary, which passes on whatever environment its caller gives; the check service builds that environment from `PATH`, `LANG`, the proxy and TLS trust variables and the check's own `env`, so a credential reaches a configured check only through one of those, such as a proxy address carrying one, or through a file the check can read |

The omissions are deliberate: configured checks are commands the project itself chose, run by the
host and never by a worker, which only receives their results. Because the boundary cannot stop a
process outside it, or a host service a check talked to, from changing the project during the run,
the service measures its input before and after and turns that race into `stale_evidence` rather
than false evidence. A change undone before the second measurement is not detected.

## Inside

The check runner runs each configured check inside the read-only boundary, which provides the
scratch the check may write, and records a check result and diagnostic spans:

```d2
checks: Check execution {
  runner: Check runner {
    "check_executor.py"
    "timing.py"
    "checks.py"
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
steps a host takes; it is passive and holds no content, so it can stay on in any run. The open
trace and the enclosing span are held per execution context, so each thread or asynchronous task
writes its timings into the trace opened where its work started and gets its previous trace back
when a scope ends; a failing sink is caught, marks the trace incomplete and writes the one
`CONCORDE_TIMING_INCOMPLETE` line, and nothing else follows from it; the work's own result or
exception passes through a span unchanged.

- <a id="realization.checks.runner"></a>The **check runner** has three parts: the executor mounts
  the filesystem read-only except the scratch, holding a process descriptor to end every descendant
  before removing the scratch; the timing recorder keeps diagnostic spans; the check service selects
  a Module's checks, measures input before and after the run — turning a concurrent change into
  `stale_evidence` — and owns the check result, so no consumer runs checks another way.
- <a id="realization.checks.tests"></a>The **check tests** run real sandboxed processes, failing
  rather than skipping where the platform can't enforce the boundary — showing what it blocks, not
  that checks are adequate — and exercise the timing recorder and summary.

## What Check execution relies on

<a id="uses-tracing"></a>

**Tracing** gives every check the shape of a [trace node](../../glossary.json#concept.trace-node),
which the check service writes through Tracing's library before the command starts and after it
ended, in the folder its caller names, and the error contract its failures follow. It relies on the
[node contract](../../kernel/tracing/contracts.md#contract.tracing.node).

Check execution relies on no other Module and on no part but the kernel: the Modules it checks,
the files their results depend on and the tests a selective check runs come from its caller, and
its paths follow the canonical project-relative form of the Kernel's
[typed values](../../kernel/contracts.md#typed-values).
