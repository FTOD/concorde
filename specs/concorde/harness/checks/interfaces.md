# Check execution interfaces

The exact calls, environment, limits and records of Check execution. The obligations they serve
are in [requirements](requirements.md).

## Running one command

```python
execute_check(project_root: Path, argv: Sequence[str], *, timeout: float,
              environment: Mapping[str, str], private_tmp: bool = False,
              evidence: Callable[[Path | None, CheckResult | None, BaseException | None], None] | None = None,
              cancel_event: threading.Event | None = None) -> CheckResult
CheckResult(stdout: bytes, stderr: bytes, returncode: int, timed_out: bool = False,
            stdout_bytes: int | None = None, stderr_bytes: int | None = None)
```

`execute_check` in `src/concorde/harness/check_executor.py` is trusted Host code; no argument comes
from a registry, a task or a model except the command itself. It refuses, with
`CheckSandboxError(RuntimeError)`, an empty command, a project that is not a directory, a
nonpositive or nonfinite timeout, a platform other than Linux, a project at `/` or under `/proc`,
`/dev` or `/sys`, a tester run whose project is `/tmp` itself, a missing root-owned system
bubblewrap, missing namespace or process file descriptor support, a failed sandbox setup, and the
absence of any writable temporary directory outside the project. The error carries the diagnostic
output as bytes for the Host. A command that never received a trusted successful start is an
isolation error, not a failed check.

| Outcome | Result |
| --- | --- |
| Exit | `returncode` is the exit status, or `128 + signal` for a signal |
| Timeout (sandbox setup included) | `timed_out=True`, `returncode=-1`, captured partial output |
| Cancellation (`cancel_event` set, or interrupt) | `CheckCancelled(KeyboardInterrupt)` after cleanup, carrying the drained output and observed byte counts |

`evidence`, when given, is called after every descendant has ended and the pipes are drained but
before the scratch is removed, with the scratch path and the result or exception. Only the tester
bridge passes it. With `evidence`, each output stream keeps only its last 2 MiB while counting all
bytes.

`CHECK_POLICY = "project-read-only-v1"` names the default boundary and
`TESTER_CHECK_POLICY = "tester-private-tmp-v1"` the tester profile selected by `private_tmp=True`.
The policy name is part of every configured check's measured digest.

## Scratch and environment

The scratch is created below the first of the process temporary directory, an inherited
`CONCORDE_CHECK_TMPDIR`, `/tmp` and `/var/tmp` that lies outside the project, and holds `tmp/`,
`cache/`, `reports/` and `shm/` (plus `private-tmp/` and `host-tmp/` for a tester). The command's
environment is the caller's `environment` with these values set:

| Variable | Value |
| --- | --- |
| `TMPDIR`, `TMP`, `TEMP` | `<scratch>/tmp` |
| `XDG_CACHE_HOME` | `<scratch>/cache` |
| `npm_config_cache` | `<scratch>/cache/npm` |
| `CONCORDE_CHECK_TMPDIR` | `<scratch>` |
| `CONCORDE_CHECK_REPORT_DIR` | `<scratch>/reports` |
| `PYTHONDONTWRITEBYTECODE` | `1` (avoids routine cache writes; it is not the boundary) |
| `CONCORDE_TEST_HOST_TMP` | `<scratch>/host-tmp`, tester profile only |

## The Linux boundary

The runner starts bubblewrap with a fixed system search path and a minimal loader environment,
passing the command's environment through an anonymous descriptor rather than its command line. It
unshares user, PID and IPC namespaces, drops all capabilities, dies with the Host, binds the host
filesystem recursively read-only, replaces `/proc` with the sandbox's PID view and `/dev` with a
minimal private one, and binds only the scratch writable at its own path; shared memory is backed
by the scratch. System file owners unmapped in a nested check's namespace are admitted only on
those read-only mounts. The Host closes inherited descriptors, gives the command a null standard
input and reads both pipes; bubblewrap's own metadata descriptors are closed before the command
runs. The command stays stopped until the Host holds a process file descriptor for the namespace's
first process; at the end the Host kills the namespace and waits for it before removing the
scratch. The network namespace is shared.

In the tester profile, `private-tmp/` is bound at `/tmp` and the host's existing `/tmp` is bound
read-only at `host-tmp/`. The top-level `/tmp` ancestors of the governing project, the executing
Framework and the Python prefixes are re-bound read-only at their own names; other old `/tmp` names
are hidden. No task input can add a mount.

## Configured checks

The project configuration lists checks under `checks`, each with `id`, `module` (the owning Module),
`argv`, `timeout_seconds` and `inputs` (project-relative files or directories). In `argv`, a first
element `{python}` is replaced by the Host's interpreter; `PYTHONPATH` points at the Framework's
`src/`.

`configured_checks(repository, target, invocation_id)` in `src/concorde/harness/checks.py` computes
`check_revision` (the digest of the Module's implementation digest, each check's definition and the
digest of every file below its inputs, and `CHECK_POLICY`), runs each of the Module's checks in
order, writes `<stdout>\n<stderr>` to `.concorde/runs/<invocation>/<check id>.log` in the primary
worktree, and returns one record per check:

| Field | Meaning |
| --- | --- |
| `check_id`, `target_id` | The check and its Module |
| `status` | `passed` (exit 0), `failed` or `timeout` |
| `exit_code` | The exit status, or `-1` on timeout |
| `source_digest` | The revision measured before the run |
| `log_digest` | The digest of the written log |

A sandbox refusal still writes the log, then fails with `check_sandbox_unavailable`. If
`check_revision` differs after the run, the call fails with `stale_evidence`. An unreadable input
path fails with the check's input error. `check_service(repository, target, invocation_id)` returns
the `run_checks` handler: it reloads the repository, runs `configured_checks` and adds each log's
last 20,000 bytes as `output_tail`.

## Tester commands and evidence

The tester extension `pi/extensions/concorde-tester.ts` registers `test_command` with parameters
`command` (at most 32,768 characters), optional `timeout` (1 to 3,600 seconds) and optional
`reports` (a unique list of at most sixteen names, each 1 to 240 characters). It refuses to run when
the session's runtime selection changed since load or the Framework's local Python runtime is
missing, then starts the Distribution-owned bridge, which verifies a bound selection and runs the
command as `/bin/bash -c <command>` through `execute_check` with `private_tmp=True`. Cancellation
waits for the bridge to be ready, then sends it SIGTERM; the bridge sets `cancel_event` and never
interrupts cleanup or export.

`CheckEvidence` in `src/concorde/harness/check_evidence.py` exports into
`.concorde/runs/tester-<32 hex digits>/` of the Git-identified primary worktree, using the primary
run writer (atomic, mode 0600, repository lock):

| Item | Rule |
| --- | --- |
| Report names | Canonical relative names below the reports directory; each opened only as a regular file with one link, through non-symlink directories, and rechecked for change |
| Report bounds | First 2 MiB of each report, 8 MiB in total, in request order |
| Output | The retained last 2 MiB of each stream, with its total observed byte count |
| Manifest | `schema_version` 1, execution and tool call identity, source worktree, command digest, timeout, requested reports, Python and runtime root, selection digests when bound, observed branch, commit and dirty tree, return code, timeout, cancellation, exception text, each artifact's digest, size, available and captured bytes and portion, errors, `artifacts_complete` and `complete` |

`artifacts_complete` holds when every requested artifact and observed output byte was exported;
`complete` additionally requires no timeout, no cancellation and a started command. A failed
artifact write keeps the others and is listed as an error; if the manifest itself cannot be
written, the response still carries the artifact references and the errors. Nothing else from the
scratch, the environment or the session is archived. The tool response carries the manifest's path,
digest and size, the execution identity, counts and truncation flags, and the last 20,000 bytes of
each stream; a reader verifies the manifest's digest and then each artifact's bytes.
