# Check execution

## Purpose

Check execution runs a project's configured checks, such as a test suite or linter, outside every
worker: they read the task worktree but cannot change its files. Workers relies on it between
resume rounds, and Operations such as validation, implementation and code review rely on it for
check results as evidence. The boundary restricts writes only, not reads, network or credentials.
It never decides whether a passing check means correct code, or which Modules changed; the service
that selects and runs a Module's checks is still to be written.

## Terminology

| Term | Definition |
| --- | --- |
| Configured check | A command that the project configuration assigns to one Module, with its arguments, time limit and the input paths its result depends on. |
| Check result | The record of one configured check run: the check, its Module, the status, the exit code, the digest of what was measured and the saved log with its digest. |
| Read-only check boundary | The Linux sandbox in which a check runs: the whole host filesystem read-only, one fresh writable scratch directory, private process and IPC namespaces, and the host's network. |
| Check scratch | The fresh directory outside the project that one run may write, holding its temporary files, caches and reports, removed after the run. |
| Diagnostic span | A bounded timing record of one named unit of host work, with its trace, parent, status and duration and never its arguments, output or messages. |
| [Module](../../vocabulary.md#concept.concorde.module) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Boundary set](../../spec-tooling/spec/module.md#concept.spec.boundary-set) | |

## Usage

<a id="concept.checks.configured-check"></a><a id="concept.checks.check-result"></a>

A **configured check** is declared in `.concorde/config.json` under `checks`, for example:

```json
{"id": "check.checks.runtime", "module": "module.harness.checks",
 "argv": ["{python}", "-m", "pytest", "-p", "no:cacheprovider", "tests/concorde/harness/checks"],
 "timeout_seconds": 300,
 "inputs": ["pyproject.toml", "conftest.py", "tests/concorde/support", "src"]}
```

The check service (not yet written) is called with a worktree, the Modules to run — or changed
paths mapped to Modules via boundary sets — and a log directory: for each Module it digests the
relevant input, runs each check in the boundary, saves logs, and returns one **check result** per
check. A digest mismatch after the run fails with `stale_evidence`, because the result would vouch
for input that changed; a stored result stays valid only while a fresh measurement matches it. Exact
declaration and records: [the check service](service.md).

<a id="concept.checks.read-only-boundary"></a><a id="concept.checks.scratch"></a>

Inside the **read-only check boundary**, any file create/change/rename/delete fails at the system
call; a command writes only to its **check scratch**, pointed to by `TMPDIR`, `XDG_CACHE_HOME`,
`CONCORDE_CHECK_TMPDIR` and `CONCORDE_CHECK_REPORT_DIR`, fresh each run. A check that hard-codes a
cache or report path inside the project fails and must be pointed at the scratch; a source-rewriting
tool, e.g. a fix-mode formatter, isn't a check. When the boundary cannot be established (only Linux
with a root-owned bubblewrap and the needed namespaces is supported), the command does not start and
the run is refused with a sandbox error; there is no subprocess fallback. Environment/mounts: [the
boundary](boundary.md).

<a id="concept.checks.diagnostic-span"></a>

The runner marks sandbox setup and each command as a **diagnostic span**, kept only in a
caller-opened trace or under `CONCORDE_DIAGNOSTIC_TIMING_DIR`; spans never change a run's outcome.
Record/summary: [the timing spans](timing.md).

## Design

Checks produce evidence that a task worktree is ready, and that evidence is only worth having if
the check could not change what it measured. So one guarantee is enforced, and the boundary states
plainly what it leaves out:

| Concern | Enforced |
| --- | --- |
| Writing any host file outside the scratch, through any path name, hard link, inherited descriptor or nested namespace | Yes, by the kernel |
| Descendant processes outliving the run | Yes: the host ends the whole process tree |
| Reading files the developer's user can read | Not enforced |
| Network access | Not enforced: the network namespace is shared with the host |
| Host sockets: abstract Unix sockets and filesystem sockets such as an SSH agent or a container daemon | Not enforced: a read-only mount does not stop connecting to a socket, so a command could ask a host service to act, including changing the project |
| Environment and credentials | Not enforced: the command receives the caller's environment, including any credentials in it |

The omissions are deliberate: configured checks are commands the project itself chose, run by the
host and never by a worker, which only receives their results. Because the boundary cannot stop a
process outside it, or a host service a check talked to, from changing the project during the run,
the service measures its input before and after and turns that race into `stale_evidence` rather
than false evidence. The check result is owned here, next to the runner that produces it, so
Workers, Validation and Delivery consume one record and never run checks another way. Logs go only
to the directory the caller names, usually the run directory in the primary worktree; a check's
output reaches a worker only as the bounded log tail Workers puts into a resume round, and whether
a worker needs more than its last 20,000 bytes is undecided. The timing recorder lives here because
check runs and sandbox setup are the slowest deterministic steps a host takes; it is passive and
holds no content, so it can stay on in any run.

```d2
checks: Check execution {
  runner: Check runner {
    "check_executor.py"
    "timing.py"
    "checks.py"
  }
}
```

- <a id="realization.checks.runner"></a>The **check runner** has three parts: the executor mounts
  the filesystem read-only except the scratch, holding a process descriptor to end every descendant
  before removing the scratch; the timing recorder keeps diagnostic spans; the check service selects
  a Module's checks, measures input before and after the run — turning a concurrent change into
  `stale_evidence` — and owns the check result, so no consumer runs checks another way.
- <a id="realization.checks.tests"></a>The **check tests** run real sandboxed processes, failing
  rather than skipping where the platform can't enforce the boundary — showing what it blocks, not
  that checks are adequate — and exercise the timing recorder and summary.

## Relationships

```d2
runner: Check runner
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
```

```d2
me: Check execution
spec: Spec core
me -> spec
```

Workers, Validation and the Operation providers use this Module; it knows none of them. They rely on
the [check result](#concept.checks.check-result), the stale-measurement rule, and the boundary
refusing to run rather than running a check unconfined.

<a id="uses-spec"></a>

**Spec core** loads the configuration and
[registry](../../spec-tooling/spec/module.md#concept.spec.registry), from which the check service
takes each Module's checks and resolves its `ImplementationScope` — a [boundary
set](../../spec-tooling/spec/module.md#concept.spec.boundary-set) whose digest is part of what a
check measures; changed paths map the same way. It also supplies safe relative-path rules for
inputs; an invalid or unreadable path fails the run before any command starts.
