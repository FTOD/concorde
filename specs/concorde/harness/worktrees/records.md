# Candidate worktrees records

The exact file formats and entry points of [Candidate worktrees](module.md). All records are
canonical JSON (sorted keys, compact separators) followed by a newline, and are written atomically
through a temporary file under the repository lock.

## Local paths

| Path | Where | Content |
| --- | --- | --- |
| `.concorde/status/<change_id>.json` | primary only | the change status |
| `.concorde/status/migration.json` | primary only | the journal of an interrupted `migrate-status --apply` |
| `.concorde/runs/<run_id>/run.json` | primary only | one run record |
| `.concorde/runs/<root_run_id>/builds/<digest>.json` | primary only | a copy of the build manifest a run used |
| `.concorde/runs/<root_run_id>/pi/<digest>.ts` | primary only | a copy of the Pi entry a run was selected through |
| `.concorde/runs/legacy-migration/` | primary only | archived bytes of migrated earlier data |
| `.concorde/work/` | any worktree | scratch files of the current change; never evidence |
| `<git-dir>/concorde-incarnation` | Git administrative directory of each registered worktree | a canonical UUID, the worktree's incarnation token |

The host appends these control paths to the repository's shared `info/exclude` file:
`.concorde/worktree.json`, `.concorde/worktrees.json`, `.concorde/status`, `.concorde/work`,
`.concorde/deliveries`, `.concorde/runs`, `.concorde/topology-proposals` and
`.concorde/*.legacy-archive`. The same list is removed from every deliverable snapshot. A status or
run write stops with `invalid_worktree_state` when Git tracks any file below `.concorde/status` or
`.concorde/runs`.

## Change status

A change ID has the form `change.<uuid>` when the host chooses it; a caller may supply another valid
identifier. `change_id` may not be `migration`. Schema version 2 has these fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | `2` |
| `revision` | integer, incremented by every successful write |
| `change_id` | the stable change identity |
| `mode` | `operation`, `maintenance` or `direct` |
| `path`, `branch` | the worktree the change belongs to and its current branch |
| `git_worktree_id` | `incarnation:<uuid>`, or null for an unversioned project |
| `primary_worktree`, `base_commit`, `base_branch` | where and from what the change was created |
| `candidate_worktree` | the linked worktree path, or null for a change in the primary |
| `target_id`, `target_hint`, `focus_id`, `task`, `constraints` | the recorded owner and intent; `target_hint` is the requested target before the first target is bound |
| `phase`, `status`, `outcome` | lifecycle position, for example `created` / `active` / null |
| `blockers`, `issue_blockers` | open blockers, each an Issue receipt with its Module, phase, scope and blocked step |
| `targets` | per-Module progress, each with an `owner` (`change_id`, `git_worktree_id`) and its own `revision` |
| `guidance` | map of files holding a host guidance block to `{created: bool}` |
| `validated_tree`, `validation` | the snapshot tree and evidence of the last validation |
| `child` | null, or the Task subagent that owns the worktree: `{id, phase, fresh_context, fork_context}` |
| `runs` | project-relative paths of the run records of this change |
| `manual_merge` | null, or the observed ordinary-Git merge `{commit, ...}` |
| `delivery` | null, or the delivery record kept by Delivery |
| `cleanup` | `{status}` with `pending`, `retained`, `removed` or `not_needed` |

Schema-1 worktree records are refused with `unsupported_worktree_version`. A worktree that still
contains `.concorde/worktree.json` or legacy `.concorde/attempts/` data is refused with
`migration_required` or `legacy_attempt` until it is migrated or cleaned explicitly.

## Run record

Schema version 2 has `schema_version`, `run_id`, `root_run_id` (the top-level invocation of nested
calls), `change_id`, `operation`, `source_worktree`, `branch`, `commit`, `input_tree` (the Git tree
of the worktree's current files, without local control paths), `dirty_input_digest`, `dirty`,
`runtime` (`root`, `python`, `python_version`, `launcher_digest`), `build_artifact`, `build_digest`,
`pi_provenance` (the explicit session selection, or null when unknown), `status` (`started`, then
the final result status), `result` (the complete result envelope) and `artifacts` (archived copies
of accepted artifacts, or a marker that a referenced artifact had changed and was not copied).

A selected Pi entry is recorded as provenance only; it does not prove that the extension loaded or
that a model ran.

## Workspace facts

`workspace_context(root)` returns the record that Task context freezes into every snapshot:

| Field | Meaning |
| --- | --- |
| `kind` | `primary`, `change` or `unversioned` |
| `current_worktree`, `current_branch` | the entry process's worktree |
| `primary_worktree`, `primary_branch` | the primary, or null |
| `change_id`, `phase`, `status`, `outcome` | of the change bound to the current worktree, or null |
| `blockers` | open Issue blocker receipts of this change, limited to the selected Module and task scope |
| `components` | per-Module progress: `target_id`, `spec_status`, `implementation_status`, `outcome` |
| `active_worktrees` | every other live linked worktree: `path`, `branch`, `head`, `managed`, `locked`, `change_id`, `target_id`, `task` (first 300 characters), `phase`, `status`, `outcome` |

## Entry points

| Function | Behaviour |
| --- | --- |
| `workspace_identity(root)` | returns the primary and current worktree records; refuses a directory inside a worktree that is not its root with `workspace_mismatch` |
| `create_worktree(root, task, package_root=)` | creates a candidate from the primary and registers its change |
| `ensure_change(root, task=, change_id=, allow_primary=, mode=)` | registers a change for the current worktree once, under the lock |
| `read_change(root, required=)` | returns the change bound to this worktree incarnation, or refuses with `missing_change` when required |
| `resume_owner(state, task)` / `bind_owner(root, task)` | restore or bind the recorded owner |
| `progress(root, status=, outcome=, blockers=)` | record lifecycle progress |
| `snapshot_tree(root, state)` | the deliverable Git tree, computed in a private index |
| `write_status(root, value, create=)` | the revision-checked write |
| `record_run(host, operation=, result=, task=)` | start or finish a run record |
| `coordinate_child(root, change_id, child_id=, phase=, release=)` | record or release the Task subagent that owns a change; primary only, phase `maintenance`, `test` or `task` |
| `record_manual_merge(root, change_id, commit=, cleanup=)` | record an observed ordinary-Git merge and cleanup outcome |
| `migrate_legacy(root, apply=)` | preview or apply the import of earlier lifecycle data |
| `inspect_worktree(root)` / `require_isolated_worktree(root, allow_primary_worktree=)` | the isolation check; failures raise `WorktreeBoundaryError` |

## Error codes

| Code | Meaning |
| --- | --- |
| `primary_unavailable` | the primary worktree cannot be found or the workspace directory is missing |
| `workspace_mismatch` | wrong worktree, not a worktree root, another incarnation, or a change ID owned elsewhere |
| `detached_worktree` | a candidate has no attached branch |
| `missing_change` | no managed change is bound to this worktree |
| `stale_status` | the status changed since it was read |
| `incompatible_handoff` | a request conflicts with the recorded owner or change ID |
| `invalid_worktree_state` | a malformed status, owner, incarnation token or guidance marker |
| `unsupported_worktree_version` | schema-1 worktree data |
| `migration_required`, `migration_conflict`, `legacy_attempt` | earlier lifecycle data that needs explicit migration or cleanup |
| `primary_session_required` | a coordination command was run outside the primary |
| `unknown_change` | a coordination command names no recorded change |
| `stale_evidence` | a cleanup-only update without a recorded manual merge |
