# Check execution

## Purpose

Check execution is a deterministic service: it runs a project's
[configured checks](../../glossary.json#concept.configured-check), such as a test suite or linter,
and returns their status and logs without model reasoning. It is called by the Workers host code
between rounds, directly by Operations such as testing and code review, and by the
[execution commands](../../glossary.json#concept.execution-command) `task-validation` and
`delivery`. Checks read the worktree but cannot directly change its files; the boundary restricts
filesystem writes only, not reads, network or credentials. The service records which inputs were
checked and refuses a result if they differ after the run from before it. It never decides whether
a passing check means correct code or whether a workspace is ready to deliver.

## Usage

For a project checked with `pytest tests/`, this service starts that command, waits for it and
returns its exit status and captured output. Pytest performs the assertions; Check execution
manages the command, its boundary, timeout and result. A configured command can itself depend on
external services, so its output need not be identical on every run.

The calling code, not an AI worker, decides when to run checks:

| Caller | Use of the result |
| --- | --- |
| Workers host code | After a clean audit, record the checks and pass failures to a worker's next round when allowed |
| `test` and `code_review` Operations | Supply recorded check results to a worker for interpretation or review |
| `task-validation` and `delivery` execution commands | Use the results in the readiness decision; Delivery reuses Validation's steps |

These are ordinary service calls inside a run, not nested runs. Check execution launches no
Concorde worker. Users configure commands and see the results through the runs that call it; there
is no separate Check execution command to start.

<a id="concept.configured-check"></a><a id="concept.check-result"></a>

A **configured check** is declared in `.concorde/config.json` under `checks`, for example:

```json
{"id": "check.checks.runtime", "module": "module.checks",
 "argv": ["{python}", "-m", "pytest", "-p", "no:cacheprovider", "tests/concorde/harness/checks"],
 "timeout_seconds": 300,
 "inputs": ["pyproject.toml", "conftest.py", "tests/concorde/support", "src"]}
```

The check service is called with a worktree, the Modules to run — or changed paths mapped to Modules
via [boundary sets](../../glossary.json#concept.boundary-set) — and a log directory: for each
[Module](../../glossary.json#concept.module) it digests the relevant input, runs each check in the
boundary, saves logs, and returns one **check result** per check. A digest mismatch after the run
fails with `stale_evidence`, because the result would vouch for input that changed; a stored result
stays valid only while a fresh measurement matches it. Exact declaration and records:
[the check service](service.md).

<a id="concept.read-only-check-boundary"></a><a id="concept.check-scratch"></a>

Inside the **[read-only check boundary](../../glossary.json#concept.read-only-check-boundary)**, any
file create/change/rename/delete fails at the system call; a command writes only to its
**[check scratch](../../glossary.json#concept.check-scratch)**, pointed to by `TMPDIR`,
`XDG_CACHE_HOME`, `CONCORDE_CHECK_TMPDIR` and `CONCORDE_CHECK_REPORT_DIR`, fresh each run. A check
that hard-codes a cache or report path inside the project fails and must be pointed at the scratch;
a source-rewriting tool, e.g. a fix-mode formatter, isn't a check. When the boundary cannot be
established (only Linux with a root-owned bubblewrap and the needed namespaces is supported), the
command does not start and the run is refused with a sandbox error; there is no subprocess fallback.
Environment/mounts: [the boundary](boundary.md).

<a id="concept.diagnostic-span"></a>

The runner marks sandbox setup and each command as a
**[diagnostic span](../../glossary.json#concept.diagnostic-span)**, kept only in a caller-opened
trace or under `CONCORDE_DIAGNOSTIC_TIMING_DIR`; spans never change a run's outcome. Record/summary:
[the timing spans](timing.md).

## Design

Checks produce evidence that a workspace is ready, and that evidence is only worth having if
the check could not change what it measured. So one guarantee is enforced, and the boundary states
plainly what it leaves out:

| Concern | Enforced |
| --- | --- |
| Writing any host file outside the scratch, through any path name, hard link, inherited descriptor or nested namespace | Yes, by the kernel |
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

### Its place in the levels of work

Check execution is no level of the [levels of work](../../module.md#the-levels-of-work): it is a
service the runs call in-process, like Spec core, and it cannot itself be a run, since the runs that
call it hold their workspace's lock while it works. Only programs call it, never a model: runs at
level 4, in steps of their own — the [Operation](../../glossary.json#concept.operation) providers'
steps and the steps of the execution commands `task-validation` and `delivery`, which are
Validation's — and the Workers host code, which manages a worker run on behalf of the Operation that
launched it, between the worker's rounds. It calls nothing above it and starts no worker, run or
agent.

```d2
workers: Workers
operations: Operations {
  implementation: Implementation
  codereview: Code review
  adoption: Adoption
}
validation: Validation
checks: Check execution
workers -> checks
operations.implementation -> checks
operations.codereview -> checks
operations.adoption -> checks
validation -> checks
```

Workers, Validation and the Operation providers Implementation (for its `test` Operation), Code
review and Adoption (which maps changed paths to Modules with it) use this Module; it knows none of
them. They rely on the [check result](../../glossary.json#concept.check-result), the
stale-measurement rule, and the boundary refusing to run rather than running a check unconfined.
Every call returns to the caller's step: the check results go up as that caller's evidence, and a
failure, such as `stale_evidence` or a boundary that cannot be established, goes up as this
Module's own error link, made by `service_error` of [the check service](service.md), which the
caller keeps as a cause under its link. The check result is
owned here, next to the runner that produces it, so Workers, Validation and Delivery consume one
record and never run checks another way. Logs go only to the directory the caller names, usually the calling run's directory in the
[run store](../../glossary.json#concept.run-store); a check's output reaches a worker only as the
bounded log tail Workers puts into a [resume round](../../glossary.json#concept.resume-round), and
whether a worker needs more than its last 20,000 bytes is undecided.

<a id="uses-spec"></a>

**Spec core** loads the configuration and
[registry](../../glossary.json#concept.registry), from which the check service
takes each Module's checks and resolves its `ImplementationScope` — a [boundary
set](../../glossary.json#concept.boundary-set) whose digest is part of what a
check measures; changed paths map the same way. It also supplies safe relative-path rules for
inputs. Check execution relies on a Module's boundary set resolving the same way from the same
Specs before and after a run, so that a digest mismatch means the input changed; an invalid or
unreadable path fails the run before any command starts.

### Inside

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
  scratch: Check scratch
  span: Diagnostic span
  runner -> check: runs
  runner -> result: records
  runner -> span: records
  runner -> boundary: enforces
  check -> boundary: runs inside
  boundary -> scratch: provides
}
```

The timing recorder lives here because check runs and sandbox setup are the slowest deterministic
steps a host takes; it is passive and holds no content, so it can stay on in any run. The open
trace and the enclosing span are held per execution context, so each thread or asynchronous task
records into the trace opened where its work started and gets its previous trace back when a scope
ends; a failing sink is caught, marks the trace incomplete and writes the one
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
