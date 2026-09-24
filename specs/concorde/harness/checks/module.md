# Check execution

## Purpose

Check execution runs a project's configured checks, such as its test suite or a linter, outside
every worker, so that they can read the task worktree but cannot change any of its files. Workers
rely on it between resume rounds, and Operations such as validation, implementation and code review
rely on it for check results they can present as evidence. Every run gets a fresh writable scratch
directory outside the project, its whole process tree is ended before the result returns, and each
configured check's outcome becomes a check result bound to the digest of what it measured. The
operating-system boundary restricts file writes only: it is deliberately not a read, network,
host-socket or credential policy. Check execution never decides whether a passing check means the
code is correct, and it does not decide which Modules a task changed. The command runner and its
timing spans exist; the service that selects and runs a Module's configured checks is still to be
written.

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

The check service, which is not written yet, is called by an Operation host or by Workers with a
worktree, the Modules whose checks to run (or the changed paths, which it maps to the Modules whose
boundary sets contain them) and a directory for logs, usually the run directory of the calling run.
For each selected Module it measures a digest of the Module's implementation files, the check
definitions, every file under their `inputs` and the boundary policy; runs each check in order
inside the boundary; saves each log in the caller's directory; and returns one **check result** per
check: `passed`, `failed` or `timeout`, the exit code, the measured digest and the log's path and
digest. If the measured digest differs after the run, the call fails with `stale_evidence`, because
the result would vouch for input that changed. A stored check result stays valid only while a fresh
measurement equals its digest. The exact declaration and records are in
[the check service](service.md).

<a id="concept.checks.read-only-boundary"></a><a id="concept.checks.scratch"></a>

Inside the **read-only check boundary** any attempt to create, change, rename or delete a file fails
at the system call. A command writes only to its **check scratch**, which `TMPDIR`,
`XDG_CACHE_HOME`, `CONCORDE_CHECK_TMPDIR` and `CONCORDE_CHECK_REPORT_DIR` point into; each run gets a
new one. A check that hard-codes a cache or report path inside the project fails and must be pointed
at the scratch; a tool that rewrites sources, such as a formatter in fix mode, is implementation work
and does not belong in a check. When the boundary cannot be established (only Linux with a
root-owned system bubblewrap and the needed namespaces is supported) the command does not start and
the run is refused with a sandbox error; there is no fallback to an ordinary subprocess. The exact
environment and mounts are in [the boundary](boundary.md).

<a id="concept.checks.diagnostic-span"></a>

The runner marks sandbox setup and each command as a **diagnostic span**. Spans are kept only inside
a trace the caller opened, or written to a directory named by `CONCORDE_DIAGNOSTIC_TIMING_DIR`; they
never change a run's outcome. The span record and the timing summary are in
[the timing spans](timing.md).

## Design

The one enforced guarantee is that a run cannot write any file outside its scratch, and that no
process outlives it. Reads, the network, host sockets and the environment with its credentials are
deliberately not limited, because configured checks are commands the project itself chose and their
evidence is only worth having if they could not change what they measured. The reasons and the full
list of what is left out are in [the design topic](design.md).

<a id="realization.checks.runner"></a>

The **check runner** has three parts. The executor mounts the host filesystem recursively read-only
with only the scratch writable, and holds a process file descriptor so it can end every descendant
before removing the scratch. The timing recorder keeps diagnostic spans of its work. The check
service selects the configured checks of the Modules it is given, measures their
input before and after the run, turning a concurrent change into `stale_evidence` rather than false
evidence, and owns the check result so that no consumer runs checks another way.

<a id="realization.checks.tests"></a>

The **check tests** run real sandboxed processes and fail rather than skip where the platform cannot
enforce the boundary; they show what the boundary blocks, not that a project's checks are adequate.
They also exercise the timing recorder and the timing summary.

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

Workers, Validation and the Operation providers use this Module; it knows none of them. They rely
on the [check result](#concept.checks.check-result), on the stale-measurement rule, and on the
boundary refusing to run rather than running a check unconfined.

<a id="uses-spec"></a>

The **Spec core** loads the configuration and the
[registry](../../spec-tooling/spec/module.md#concept.spec.registry), from which the check service
takes the configured checks of each Module and resolves the Module's `ImplementationScope`, one of
the [boundary sets](../../spec-tooling/spec/module.md#concept.spec.boundary-set), whose digest is
part of what a configured check measures. Changed paths are mapped to Modules through the same
boundary sets. The Spec core also supplies the safe relative-path rules for check inputs. An invalid
or unreadable input path fails the run before any command starts.
