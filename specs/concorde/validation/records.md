# Validation records

This document gives the exact request, flow, evidence records and digests of
[Validation](module.md).

## Request

`concorde-validate` takes `target_id` and `task`, and optionally `focus_id`, `constraints`,
`change_id` and `run_checks` (boolean, default `true`). Its response is the common capability
response; `checks` holds the check results of this run and `outcome` is `failed`, `ready` or
`completed`.

## Flow

1. Unless another capability called it as part of its own work, validation records the change's
   phase as `validate` and invalidates any earlier ready state.
2. When the worktree has a change status record, it confirms pending realization entries whose
   files exist and reloads the Specs; the candidate's file tree is snapshotted after this step.
   It then validates the project's Specs for the target Module. On any error the candidate is marked
   `blocked` with outcome `invalid_spec` and the answer is `failed`; errors about check inputs are
   quoted in the answer.
3. It selects the checked Modules: every Module for a direct candidate, otherwise the target's
   affected Modules. For the Module the change is about these include every Module that owns a Spec
   document member or binds a file differing between the change's `base_commit` and the candidate's
   deliverable tree, which leaves out local control records and the worktree guidance. It records
   their Spec and implementation revisions.
4. With `run_checks`, it runs the configured checks of each checked Module.
5. For a planned target it stores the check results, the affected revisions, the Spec source digest
   and the Issue store revision in the target's state.
6. Any result other than `passed` marks the target `blocked` and answers `failed`.
7. It compares the candidate's file tree and the affected revisions with those before step 4. A
   difference stops with `stale_evidence`.
8. A direct candidate stores a `validation` record in the change and proceeds to readiness. A
   planned target proceeds to readiness when all its accepted tasks are complete; otherwise the
   answer is `completed` with the note that semantic completeness is not proven.
9. Readiness runs the completion check, confirms the tree is unchanged, sets the target and, unless
   called by another capability, the whole change to `ready`, and records the validated tree.

## Completion check

The completion check is the gate that Validation and Delivery share. It checks these conditions in
order and fails with the code of the first one that is not met:

| Condition | Code |
| --- | --- |
| every required review, with its consumers and components, is current | `review_required` |
| no open blocker exists for this Module and task scope | `spec_incomplete` |
| *direct candidate:* a `validation` record exists for this Module, focus, task and constraints | `stale_evidence` |
| *direct candidate:* Spec validation passes with the recorded source digest and Spec revision | `stale_evidence` |
| *direct candidate:* every configured check of the project passed for its current input digest | `stale_evidence` |
| *planned target:* the Module's Spec revision equals the one its plan was written for | `stale_context` |
| *planned target:* the task and constraints equal the planned ones | `incompatible_handoff` |
| *planned target:* every completed component's revisions are unchanged and it passes this check itself | `stale_evidence` or the component's code |
| *planned target:* accepted tasks exist and all are complete | `incomplete_change` |
| *planned target:* the implementation is unchanged since the tasks completed | `stale_evidence` |
| *planned target:* Spec validation passes with the recorded source digest | `stale_evidence` |
| *planned target:* every affected Module's revisions equal the recorded ones | `stale_evidence` |
| *planned target:* every check of the affected Modules passed for its current input digest | `stale_evidence` |

For a direct candidate the required checks are all configured checks of the project; for a planned
target they are the checks of its affected Modules, recomputed from the candidate's current files.

## Check result

Each configured check run produces one record:

| Field | Meaning |
| --- | --- |
| `check_id` | the configured check |
| `target_id` | the Module the check belongs to |
| `status` | `passed` (exit code 0), `failed` (any other exit code) or `timeout` |
| `exit_code` | the process exit code, `-1` on timeout |
| `source_digest` | the check input digest before the run |
| `log_digest` | digest of the saved log |

The log is `stdout`, a newline and `stderr`, saved by the Host at
`.concorde/runs/<invocation>/<check_id>.log`. When the check input digest differs after the run,
validation stops with `stale_evidence` because the check changed what it measured.

The check input digest covers, for the check's Module: the configuration of each of its checks, the
digest of every file under each explicit input path, the Module's implementation revision, and the
sandbox policy identity `project-read-only-v1`. An explicit input that is missing, a symbolic link
or not a regular file stops validation and names the check, its Module and the path.

The check configuration lists, per check, an identity, the Module it belongs to, the command as an
argument list, a timeout in seconds and the explicit input paths.
