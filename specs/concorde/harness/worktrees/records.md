# Candidate worktrees records

The exact file formats, entry points and error codes of [Candidate worktrees](module.md). All
records are canonical JSON (sorted keys, compact separators) followed by a newline, and are written
atomically through a temporary file under the repository lock.

## Local paths

| Path | Where | Content |
| --- | --- | --- |
| `.concorde/status/<change_id>.json` | primary only | the change status |
| `.concorde/runs/<run_id>/run.json` | primary only | one run record |
| `.concorde/runs/<root_run_id>/builds/<digest>.json` | primary only | a copy of the build manifest a run used |
| `.concorde/runs/<root_run_id>/pi/<digest>.ts` | primary only | a copy of the Pi entry a run was selected through |
| `.concorde/runs/<run_id>/artifacts/<digest>/<path>` | primary only | a copy of an accepted artifact the run's envelope references |
| `.concorde/work/` | any worktree | scratch files of the current change; never evidence |
| `<git-dir>/concorde-incarnation` | Git administrative directory of each registered worktree | a canonical UUID, the worktree's incarnation token |

The Host appends the control paths `.concorde/status`, `.concorde/work` and `.concorde/runs` to the
repository's shared `info/exclude` file. The same list is removed from every deliverable snapshot.
A status or run write stops with `invalid_worktree_state` when Git tracks any file below
`.concorde/status` or `.concorde/runs`, and registering a change stops the same way when Git tracks
a file below `.concorde/work`.

## Change status

A change identity has the form `change.<uuid>` when the Host chooses it; a caller may supply another
valid identifier. Schema version 3 has exactly these fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | `3` |
| `revision` | integer, incremented by every successful write |
| `change_id` | the stable change identity |
| `mode` | `operation`, `maintenance` or `direct` |
| `path`, `branch` | the worktree the change belongs to and its current branch |
| `git_worktree_id` | `incarnation:<uuid>`, or null for an unversioned project |
| `primary_worktree`, `base_commit`, `base_branch` | where and from what the change was created |
| `candidate_worktree` | the linked worktree path, or null for a change in the primary |
| `target_id`, `target_hint`, `focus_id`, `task`, `constraints` | the recorded owner and intent; `target_hint` is the requested target before the first target is bound |
| `phase`, `status`, `outcome` | lifecycle position, for example `created` / `active` / null; `status` values used across Concorde include `active`, `blocked`, `failed`, `cancelled`, `limit_exhausted`, `delivering`, `cleanup_pending`, `delivered` and `merged` |
| `guidance` | map of files holding a Host guidance block to `{created: bool}` |
| `child` | null, or the Task subagent that owns the worktree: `{id, phase, fresh_context, fork_context}` with phase `maintenance`, `test` or `task` |
| `runs` | project-relative paths of the run records of this change |
| `cleanup` | `{status}` with `pending`, `retained`, `removed` or `not_needed` |
| `sections` | map of provider section name to that provider's typed value `{type_id, schema_version, data}` |

A provider declares a section with `declare_section(name, type_id)` before it writes it; the name
matches the identifier grammar and is declared once, and declaring it again with another type is
refused. A write validates every section it adds or changes against its declared type and refuses
an undeclared name; a section the write leaves unchanged was checked when it was written. The
sections in use are Planning's `planning` (plan, task and pending-gap records), Review's `review`
(review records), Validation's `validation` (evidence and the validated tree), Delivery's
`delivery` (delivery receipt and manual-merge record) and Issue solving's `issue-solving` (solve
states and the closing journal); their content is specified by those Modules. A provider reads and
writes only its own section, through its own code.

A change status is bound to the current worktree when its `path` is the worktree's resolved path,
its `git_worktree_id` equals the worktree's incarnation token, and its `primary_worktree` is the
current primary. A retained terminal candidate stays bound until its cleanup status is `removed`;
in the primary, a terminal change (`merged` or `delivered`) no longer binds.

## Run record

Schema version 3 has `schema_version`, `run_id`, `root_run_id` (the top-level invocation of nested
calls), `change_id`, `operation`, `source_worktree`, `branch`, `commit`, `input_tree` (the Git tree
of the worktree's current files as the deliverable snapshot computes it), `dirty_input_digest`,
`dirty`, `runtime` (`root`, `python`, `python_version`, `launcher_digest`), `build_artifact`,
`build_digest`, `pi_provenance` (the session selection the caller supplied, or null when unknown),
`relayed_run_id` (the run identity of the candidate's own run when this request was relayed, else
null), `status` (`started`, then the final result status), `result` (the complete result envelope)
and `artifacts` (for each `{id, path, digest}` value in the envelope, the archive path of its copy,
or `status: unavailable` when its bytes no longer matched).

A selected Pi entry is recorded as provenance only; it does not prove that the extension loaded or
that a model ran. A run record is evidence of what the Host admitted and returned, not of what a
model read.

## Workspace facts

`workspace_context(root)` returns the record that Task context freezes into every snapshot:

| Field | Meaning |
| --- | --- |
| `kind` | `primary`, `change` or `unversioned` |
| `current_worktree`, `current_branch` | the entry process's worktree |
| `primary_worktree`, `primary_branch` | the primary, or null |
| `change_id`, `phase`, `status`, `outcome` | of the change bound to the current worktree, or null |
| `active_worktrees` | every other live linked worktree: `path`, `branch`, `head`, `managed`, `locked`, `change_id`, `target_id`, `task` (first 300 characters), `phase`, `status` (`unmanaged` when no change is registered, `invalid` when its record is malformed), `outcome` |

`active_worktrees` is an observation: other worktrees may advance while a step runs.

## Entry points

| Function | Behaviour |
| --- | --- |
| `workspace_identity(root)` | returns the primary and current worktree records; refuses a directory inside a worktree that is not its root with `workspace_mismatch` |
| `create_worktree(root, task, package_root=)` | creates a candidate from the primary and registers its change; `maintenance` mode when the package is the project itself |
| `ensure_change(root, task=, change_id=, allow_primary=, mode=)` | registers a change for the current worktree once, under the lock |
| `read_change(root, required=)` | returns the change bound to this worktree, or refuses with `missing_change` when required |
| `resume_owner(state, task)` / `bind_owner(root, task)` | restore or bind the recorded owner |
| `progress(root, phase=, status=, outcome=)` | record the lifecycle position of the bound change; leaving `ready` withdraws its readiness |
| `declare_section(name, type_id)` | declare a provider section and its typed-value type |
| `section(state, name)` / `put_section(state, name, data)` | the `data` of a provider section of a read status, or place new `data` there for the next write |
| `snapshot_tree(root, state)` | the deliverable Git tree, computed in a private index |
| `write_status(root, value, create=)` | the revision-checked write |
| `record_run(host, operation=, result=, task=, relayed_run_id=)` | open or finish a run record; a mutating request is added to a change's `runs` when it names the change or carries its recorded intent |
| `coordinate_child(root, change_id, child_id=, phase=, release=)` | record or release the Task subagent that owns a change; primary only |
| `workspace_context(root)` | the workspace facts |
| `require_isolated_worktree(root, allow_primary_worktree=)` | the isolation check; failures raise a worktree boundary error |

## Error codes

| Code | Meaning |
| --- | --- |
| `primary_unavailable` | the primary worktree cannot be found or the workspace directory is missing |
| `workspace_mismatch` | wrong worktree, not a worktree root, another incarnation, a change identity owned elsewhere, or a worktree another Task subagent owns |
| `detached_worktree` | a candidate has no attached branch |
| `missing_change` | no managed change is bound to this worktree |
| `stale_status` | the status changed since it was read |
| `incompatible_handoff` | a request conflicts with the recorded owner or change identity |
| `invalid_worktree_state` | a malformed status, owner, incarnation token, guidance marker or provider section, or tracked control paths |
| `primary_session_required` | a coordination command was run outside the primary |
| `unknown_change` | a coordination command names no recorded change |
| `invalid_input` | an invalid change mode, owner binding or Task subagent identity or phase |
| `unsafe_path` | a run path outside `.concorde/runs/` or a path that escapes the worktree |
