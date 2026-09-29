# Decision log: legacy-records-history

Goal: Add a one-off development script that moves this checkout's pre-tracing task records (the flat .concorde/tasks/<task>.json, .decisions.md, .merge.log and .session/ of 152 old tasks) into .concorde/history/ in the Tracing layout, and archives then removes the old .concorde/runs/ contents, so no record of an old task is lost
# legacy-records-history: brief (main agent, 2026-09-29)

## Developer's decision
`tracing` (merged at 74b9aff7) moved Concorde's records to one folder per task, with a history
under `.concorde/history/`. The new code reads only the new layout. The primary worktree still
holds the old records, all ignored by Git:
- `.concorde/tasks/`: about 76 MB, the flat `<task>.json`, `<task>.decisions.md`,
  `<task>.merge.log` and `<task>.session/` of 152 old tasks, plus `.lock` and `merge.lock`.
- `.concorde/runs/`: about 118 MB, 629 old run folders, `launch-*.log`, `issues.lock`, `locks/`
  and `tracing-bootstrap/`.

Of the options offered, the developer chose to **migrate into the history**:
- Move each old task, with its record, decision log, merge log and session material, into
  `.concorde/history/<task>/` in the Tracing layout, so that `concorde trace list --history` and
  retention see it.
- Pack the old run records and launch logs into an archive outside the repository, then delete
  them.

## What the task delivers
- A one-off development script, for example `scripts/development/migrate-legacy-records.py`. It
  takes the primary worktree's root and has a dry-run mode that prints every move, archive and
  removal before doing any of them.
- Tests on a fake old layout.

**Do not run it against the primary worktree's real `.concorde/`.** After the merge, the main agent
runs the dry run, checks it, and then runs it for real.

## Requirements
- Never lose a decision log or a task record. Move them; do not rewrite their content beyond what
  the history layout needs. Where the old record cannot be turned into the new trace node or record
  format faithfully, keep the old file verbatim inside the history folder and write a minimal node
  that points to it. Decide the exact mapping from the Tracing Spec.
- Skip new-layout task folders already present in `.concorde/tasks/`, such as this task's own
  `legacy-records-history/`.
- History keys follow the Tracing rule (`<task>` or `<task>.<n>`). Some old ids were opened more
  than once and some old tasks are still in state `failed` without being closed, such as
  `task-session-tool-args`. Move those too, with their state recorded.
- The run archive is a single compressed tar at a path the caller gives. The main agent will use
  `~/concorde-old-records-2026-09-29.tar.zst`, or `.tar.gz` if zstd is unavailable. Remove only
  what went into an archive that was verified, for example by listing it back.
- Do not touch `.concorde/locks/`, `.concorde/evidence/`, `.concorde/issues/` or any new-layout
  node.

## Left to the session
The script's name and place, whether and how a Module binds it (no unlisted-file warnings), the
old-to-new mapping, and whether the script is removed again in a later task. Record each choice
here.

## Task session decisions (2026-09-29)

- **Name and place.** `scripts/development/migrate-legacy-records.py <primary> --archive <path>
  [--dry-run]`, beside the other development scripts; it re-executes on the checkout's `.venv` like
  `scripts/concorde.py` and imports the Tracing library and the Task store, so every node it writes
  is checked by the same contracts and content types the live code uses. Tests:
  `tests/concorde/tracing/test_legacy_migration.py` (9 tests on a fake old layout).
- **Binding.** Module Tracing gains a realization `realization.tracing.legacy-migration` (entry: the
  script) with a paragraph under "The parts" in `specs/concorde/tracing/module.md`; the test file is
  covered by the existing `tests/concorde/tracing/` entry. `spec-validation` reports no finding.
- **Removal.** The script is one-off: the Spec paragraph says it is removed once the checkout's
  records are migrated. I recommend a later small task that deletes the script, its test and the
  realization after the main agent's real run.
- **Mapping, per old task, into `.concorde/history/<key>/`:**
  - `task.json`: the old record in `contract.tasks.record` v12 (schema_version 2, the same fields,
    `merging` null, `closed.history` = key), validated against the contract read from the Spec;
    when it does not fit, no `task.json` is written and the old record stays only as
    `legacy/record.json`.
  - `trace.json`: task node, started at `created_at`, ended at `closed.at`, status ok (closed) or
    failed, outcome the old outcome, error the first closing error of a failure; metadata task,
    modules, branch, base_commit (no `concorde_commit`/`protocol_version`: nothing observed them,
    and the script's own commit would be a false fact); content transitions `open` at
    `created_at` and the final state at `closed.at` only (merging times were never stored; the
    merge log keeps them), escalations numbered from 1 with `by` = the level of the link on top,
    closing as stored plus the history key; references `commit` and `bundle` for each old delivery.
    When the full node does not fit, a minimal node (no content, pointing to `legacy/`) is written.
  - `decisions.md`: the decision log, byte for byte.
  - `sessions/<id>/`: a session node per recorded session, status `unknown` as the live code
    records it; a session without `program` (the 5 oldest, which carry a Claude `settings` path) is
    `claude`. For a task with exactly one pi session: its `status.json`, `pi/` session file, and
    `round-N.*` files as `rounds/N/{prompt.md,events.jsonl,stderr.log,supervisor.log}` with a round
    node each (status by the live `ROUND_STATUS`, error kept for blocked/failed rounds).
  - `legacy/record.json` (old record verbatim, which keeps the runs, deliveries and workflow steps
    the layout has no field for), `legacy/merge.log`, and `legacy/session/` for every other session
    file (the boundary configuration: `settings.json`, `write_hook.py`, `boundary.ts`,
    `pi_policy.ts`, `pi_session_policy.ts`, `transport-checks/`), each an artifact of the task node.
    I kept the boundary configuration instead of dropping it like a live close drops `runtime/`,
    since the brief says nothing of an old task may be lost.
- **Safety.** Copies go to `history/.migrating-<key>/`, are checked against their sources'
  digests, the folder is renamed to `history/<key>` and only then are the old files removed. A
  task whose old record already lies byte for byte in a history folder (an interrupted run) only
  has its old files removed, after checking all their content is there. The whole real run holds
  the merge lock (refuses `merge_busy`). Keys follow `<task>`/`<task>.<n>` against existing history
  folders, oldest task first. A task with no `closed.at` is left in place and reported. The
  archive holds `runs/*` plus the old locks `tasks/.lock` and `tasks/merge.lock` (so everything
  removed went into the archive); it refuses a held lock among them, an existing archive, an
  archive inside the primary worktree or an unknown suffix (`.tar.zst`/`.tzst`/`.tar.gz`/`.tgz`);
  it is verified with `tar -t` (every file and folder present) and `tar --compare` before removal.
- **Rehearsal (not the real `.concorde/`).** I copied the primary worktree's `tasks/`, `runs/` and
  `config.json` into my temporary directory and ran the script there: dry run with no fallback
  note (all 152 records and all their nodes fit the current formats), then the real run in 2 s:
  152 history folders, 631 entries archived (10.7 MB zstd) and verified, `runs/` removed; only
  `tasks/legacy-records-history/` skipped. `concorde trace list --history`, `task list`, `task show
  task-session-tool-args` (state failed) and `trace show ci-socat-dependency` read them; `trace
  prune --dry-run` removes nothing; every one of the 606 old files' content is present in its
  history folder. The copy was deleted afterwards.
- **Known limit.** If the history already holds a task of an old name when the main agent runs it,
  the old task gets `<name>.<n>` after it, so `found_folder` would treat the old one as the latest;
  history folders are never renamed, so I accept this (none exists now).

## Delivery (task session, 2026-09-29)

- `task-validation` r-20260929T102817-task_validation-08acbabc: ok, ready, no blocking finding or
  warning. Full suite before it: 795 passed, 4 skipped; `build --check` without difference.
- `delivery` r-20260929T103015-delivery-fd7e455c: ok, delivery commit
  c2d108b62159a4a8696abd96b415b092e5e9b3e1 with `.concorde/evidence/legacy-records-history/1.json`.
- The worktree shows untracked `.bashrc`, `.claude/agents` and similar entries: they are
  `/dev/null` character devices the session sandbox mounts, not files of the task; nothing
  committed them.

## Main agent (2026-09-29)
- Non-ok: the first `task merge legacy-records-history` refused with `primary_dirty` because the
  main agent wrote the merge output to `.concorde/merge-legacy.out` inside the primary worktree.
  The file was removed and the merge run again, with its output kept outside the repository.

## Closed: merged, 2026-09-29T10:33:05Z
