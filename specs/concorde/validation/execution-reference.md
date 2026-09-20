# Validation execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Validation Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term                                                      | Meaning / definition                             |
| --------------------------------------------------------- | ------------------------------------------------ |
| [Candidate](../module.md#terminology)                     | Defined in Concorde Framework.                   |
| [Evidence](../module.md#terminology)                      | Defined in Concorde Framework.                   |
| [Ready](../module.md#terminology)                         | Defined in Concorde Framework.                   |
| [Spec](../module.md#terminology)                          | Defined in Concorde Framework.                   |
| [Host](../module.md#terminology)                          | Defined in Concorde Framework.                   |
| [Module](../module.md#terminology)                        | Defined in Concorde Framework.                   |
| [Grant](../module.md#terminology)                         | Defined in Concorde Framework.                   |
| [Structural validation](../spec/structure.md#terminology) | Defined in What structural validation tells you. |
| [Semantic completeness](../spec/structure.md#terminology) | Defined in What structural validation tells you. |
| [Delivery](../module.md#terminology)                      | Defined in Concorde Framework.                   |
| [Graph](../module.md#terminology)                         | Defined in Concorde Framework.                   |

## Validation operation {#validation-validation-operation}

[Harness admission](../harness/admission.md) owns the entry. Its [common invocation envelope](../harness/admission.md#operation-execution-boundary),
[typed handoffs](../harness/admission.md#stage-handoffs) and
[gap rules](../issues/execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history) apply. Artifact references are host-issued paths
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

Unresolved same-scope contract blockers also prevent readiness. Historical author relations can be
released by current explicit contract reassessment; validation itself never clears them because
files changed or treats retired author/graph completion as executable work. Original observations
remain history and required review evidence remains independent.

Existing authored tasks must be complete and every already-required review must be current,
successful and nonblocking before readiness. Validation does not choose new review requirements,
run an Agent, repair a defect or deliver. A failed/missing/stale check or review blocks ready and
preserves the candidate. Repeating validation recomputes or verifies evidence against current bytes;
Spec and shared-file consumers each retain their own revision and evidence. Structural success and
scenario coverage do not establish semantic completeness.

### Design {#validation-design}

#### Configured check execution {#validation-configured-check-execution}

Only the host admits configured argv, expands an initial `{python}` to its interpreter, and calls
Harness's `execute_check(project_root, argv, timeout=..., environment=...)`. The supplied environment
retains the host environment and sets `PYTHONPATH` to the package's `src`; [Harness Module](../harness/module.md) installs it only
inside the sandbox and directs temporary/cache/report paths to independent external scratch.
Checks may read project files. The operating system denies creation, modification, movement and
deletion by the check and its descendants, including transient writes that are later restored.
The rule covers listed and unlisted files, ignored caches, `.concorde/runs` and lifecycle records.

Harness returns byte `stdout`, byte `stderr`, integer `returncode` and boolean `timed_out` after
terminating the check's descendants. [Harness admission](../harness/admission.md) alone writes `stdout + b"\n" + stderr` to
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

Before executing commands, structural validation preflights every registered explicit input for
existence and safe file/directory membership. An empty directory is valid; a missing input, symlink
(including a dangling link or one under a bytecode-excluded directory), or non-regular file blocks
validation. Directory revision membership excludes `__pycache__`, `.pyc` and `.pyo` as before; it does
not skip unsafe aliases. Both preflight findings and revision failures identify the owning
`check_id`, `target_id` and offending path. Missing inputs retain `missing_source`; canonical-path
and direct symlink admission retain `invalid_field`, and unsafe directory members use `unsafe_path`.
No missing-file placeholder or implicit optional-input policy is introduced.

Before and after execution, check freshness covers registered commands and explicit inputs plus
the selected Module's implementation. The execution-policy identity `project-read-only-v1` also
participates in the digest, invalidating evidence from the former unrestricted runner. Candidate
tree and affected-Module revision comparisons remain additional defenses against concurrent
external changes; they do not supply the write boundary or claim semantic completeness.

#### Implementation revisions and consumer evidence {#validation-implementation-revisions-and-consumer-evidence}

Implementation revisions hash each Module's declared entries together with the current digests of
the files they bind. Validation derives every listing Module from the reverse index, in which a
directory entry covers every path below it, runs their configured checks and records each
Module's contract and implementation revisions. Code review uses a separate Module-only contract
context for each consumer plus its authorized code. Required peer review artifacts are retained
with their own intent; later source, Spec or membership changes invalidate those results. A single
consumer's completion never establishes compatibility for every Module that lists the same shared
file.

## Realization and reuse limits

This provider belongs to Operations; Module parentage does not select its execution order. Its behavior is realized in
its own package `src/concorde/validation/` and the Harness check runner it shares, bound by its adapter entity together with its `operations/` declaration; this Spec boundary
creates no additional entry, worker grant or configurable arbitrary graph. Host admission, phase
artifacts and permissions remain mandatory. A new graph requires declared composition and an
implementation of its sequencing, artifact admission, recovery and completion policies before it
can execute. [Harness admission](../harness/admission.md) realizes the common entry and invocation
host, and [Operations](../operations/execution-reference.md#graphs-dispatch-graphs) the dispatch
that reaches this provider.
