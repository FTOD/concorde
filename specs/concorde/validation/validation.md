```concorde-document
{
  "id": "document.validation.validation",
  "owner": "module.validation",
  "main_visible": true
}
```

# Validation capability

## Usage & Contract

The [common invocation envelope](../development/interfaces.md#capability-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/review-and-gaps.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.

`concorde-validate` is public, deterministic and uses no Agent context selection. Its request
requires target_id and task, with optional run_checks and common identity fields. It runs on the
current admitted candidate, uses structural validation and configured checks, and returns the common
typed response with checks and current artifact identities. Its host-owned evidence writes do not
grant a check or Agent project writes. Omitting checks cannot fabricate passing evidence or satisfy
a gate whose configured checks remain missing or stale.

A directly authored Spec or manual candidate can run explicit validation without inventing a plan
or an attempt. With no authored target plans, validation runs every configured project check and
stores root validation evidence against the exact candidate tree. Existing authored plans and tasks
still require completion; this path cannot bypass unfinished work. Deterministic readiness does not
claim universal semantic completeness. The primary delivery request accepts the verified candidate.


Existing authored tasks must be complete and every already-required review must be current,
successful and nonblocking before readiness. Validation does not choose new review requirements,
run an Agent, repair a defect or deliver. A failed/missing/stale check or review blocks ready and
preserves the candidate. Repeating validation recomputes or verifies evidence against current bytes;
Spec and shared-file consumers each retain their own revision and evidence. Structural success and
scenario coverage do not establish semantic completeness.

## Architecture & Realization

### Configured check execution

Only the host admits configured argv, expands an initial `{python}` to its interpreter, and calls
Harness's `execute_check(project_root, argv, timeout=..., environment=...)`. The supplied environment
retains the host environment and sets `PYTHONPATH` to the package's `src`; Harness installs it only
inside the sandbox and directs temporary/cache/report paths to independent external scratch.
Checks may read project files. The operating system denies creation, modification, movement and
deletion by the check and its descendants, including transient writes that are later restored.
The rule covers listed and unlisted files, ignored caches, `.concorde/runs` and lifecycle records.

Harness returns byte `stdout`, byte `stderr`, integer `returncode` and boolean `timed_out` after
terminating the check's descendants. Development alone writes `stdout + b"\n" + stderr` to
`.concorde/runs/<invocation_id>/<check_id>.log`. No project log handle or lifecycle write grant enters
the sandbox. Public evidence contains exactly `check_id`, `target_id`, `status` (`passed`, `failed`
or `timeout`), `exit_code`, `source_digest` and `log_digest`; raw output remains private. Timeout
uses exit code -1. Other exit codes retain Harness's shell encoding; zero is passed and nonzero
is failed. Disposable report files stay outside the project and are removed after execution.

An unavailable backend, unsupported OS, failed sandbox setup or failed isolated launch raises
Harness's `CheckSandboxError`, carrying private diagnostic streams. The host saves that diagnostic
log, then raises `SpecError/check_sandbox_unavailable` naming the check and host log path, without
including raw diagnostics or recording passing evidence. It never runs a less restricted fallback.
Linux currently requires a system bubblewrap and working namespace/pidfd support; no other OS
backend is implemented. There is no task/configuration option to disable enforcement. Project cache
or report writers must migrate to the issued scratch paths, while source-formatting writes belong
to implementation. Finer read, network and credential policy is outside this interface's scope.

Before and after execution, check freshness covers registered commands and explicit inputs plus
the selected Module's implementation. The execution-policy identity `project-read-only-v1` also
participates in the digest, invalidating evidence from the former unrestricted runner. Candidate
tree and affected-Module revision comparisons remain additional defenses against concurrent
external changes; they do not supply the write boundary or claim semantic completeness.
