# Decision log: issue-write-recovery

Goal: Make Issue writes recoverable: keep git commit with hooks, and under the merge lock detect and repair records published but not committed, so receipts and visibility only follow committed records

## Brief (main agent, 2026-10-01)

Resolves Issue I-94d306a4621850719eef9ef7b2265bf7 ("Published but uncommitted Issues lack a
recovery contract", severity high, tier decision-needed). Read the Issue with
`python3 scripts/concorde.py issues show I-94d306a4621850719eef9ef7b2265bf7` first. The project
MCP server's Issue tools of the main session currently refuse every record with
`invalid_issue` (`severity: unknown field`), most likely a stale server process; use the
`issues` command of your worktree.

The developer's decisions:

- Keep the current write path: one `concorde issues` command per write, holding the merge lock
  for the whole write, publishing the record and committing it with `git commit --only` with the
  repository's author identity and hooks, returning only after the commit. Do not replace it with
  Git plumbing (`commit-tree`/`update-ref`), which would skip the hooks.
- Add residue detection and repair: a record file published in the primary worktree but not
  committed (a sync failure after publication, a failed restore, a killed or interrupted
  process) must be detected and repaired under the merge lock before any further Issue write
  acts, without touching unrelated changes of the primary worktree.

Left to the task session (record each choice here): what repair means for each residue state
(commit the residue if it is a valid record, or restore the committed version / remove a new
uncommitted file), whether reads and `list` report or hide uncommitted records, how an
identical retry establishes that its record is committed before returning the existing receipt,
how the unconditional "every refusal writes nothing" promise is qualified where restoration
cannot be guaranteed, the error codes, and the sync-failure and interruption scenarios and
tests. Work within module.issues. If the fix needs a change of another Module, such as Tasks'
`task merge` audit or the Spec core file transaction contract, escalate it with the rest
instead of changing it.

## Task session decisions (2026-10-01)

- **What a residue is.** A record file `I-<32 hex>.md` of the primary worktree's
  `.concorde/issues/` whose working-tree or staged state differs from its version in `HEAD`, and
  the file transaction's `.concorde-write-*` temporary files there. Detected with one
  `git status --ignored --untracked-files=all` over that directory, so staged, unstaged, untracked
  and ignored states all count. Hidden files such as `.gitignore` and other names are not records
  and are left alone.
- **Repair rolls back, never forward.** A residue is the store's own when its working-tree file is
  a valid record of its Issue whose committed version, when there is one, is a prefix (same
  reports and dispositions, then more): exactly what an unacknowledged store write publishes. Such
  a residue is put back to its committed version (`git checkout HEAD -- <path>`), or removed when
  `HEAD` has none (`git rm --cached` and unlink); temporaries are removed. Nothing is committed.
  Reason: a receipt is given only after the commit, so the residue was never acknowledged; the
  write that left it was refused or never answered. Rolling it forward would record a report
  whose writer was told it was refused, and a CLI retry (new invocation each run) would then
  create a duplicate Issue; rolling back makes every refused or interrupted write safe to repeat
  and keeps "a receipt means committed" the only way a report becomes recorded.
  Considered and rejected: committing a valid residue (the brief's first option).
- **Foreign changes are left alone.** A record change no store write leaves (a deleted committed
  record, an invalid or rewritten record, a staged change whose file equals `HEAD`) is not the
  store's to discard: repair leaves it, and only a write to that very Issue is refused, with the
  new code `uncommitted_change` (environment), naming the file and how to inspect and revert it.
  Writes to other Issues proceed. This keeps the developer's "without touching unrelated changes".
- **When repair runs.** Every write, under the merge lock (also when its caller holds it, as a
  task merge closing Issues does), after the unfinished-merge check and before it reads the
  record. A write that fails after publishing (directory sync, Git) puts its record back at once
  as before; when that putting back fails, it refuses with the new code `recovery_failed`
  (environment), saying the record stays uncommitted, invisible to reads, and that the next write
  or `recover` puts it back. Repair itself failing refuses the write with `recovery_failed` too.
- **New action `recover`** (`concorde issues recover`): holds the merge lock, repairs and prints
  `{"recovered": [{path, action}], "left": [{path, reason}]}`, so the main agent can clear a
  residue that makes the primary worktree dirty without making an Issue write. No MCP tool added
  (the server's tools belong to module.main-session).
- **Reads show only committed records.** `read_issue`, `list_issues` and `resolve_report` read
  the records of the primary worktree's `HEAD` commit through `git ls-tree` / `git cat-file
  --batch`, never the working-tree files; the revision is the digest of the committed bytes. So
  an uncommitted record, or the moment between publication and commit, is never visible, and a
  list is one consistent commit. `check` alone still reads the files of the worktree it runs in.
- **Identical retry.** The existing receipt is returned only when the committed record (read after
  repair, under the lock) holds the report, so the receipt names a committed report.
- **Refusal promise qualified.** "Every refusal writes nothing" becomes: commits nothing and leaves
  nothing a read shows; only when putting back fails, or the process is killed, may an uncommitted
  record stay in the primary worktree until the next write or `recover` puts it back.

- **Follow-ups outside module.issues, recorded as Issues, not changed here.** I-7f0b88c134525f939c7c2aed819e8984
  (module.tasks, preferred-fix, medium): `task merge` should run `recover_issues(primary, locked=True)`
  before its `primary_dirty` check. I-539ca8e057db5d859ff5995066608904 (module.main-session,
  preferred-fix, medium): the guidance and MCP tools should know `recover`, `recovery_failed` and
  `uncommitted_change`. Delivery does not depend on either; filed with this worktree's
  `issues` command (`--task issue-write-recovery`), since the brief reports the MCP Issue tools
  refuse `severity`.
- Verification: `spec-validation` success, `build --check` success, full suite 886 passed,
  4 skipped. Commit a91b6097.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T15:39:14Z

issue-write-recovery delivered: delivery commit f811750128d139f6c1a6040849092963b438202a on concorde/issue-write-recovery (work in a91b6097). Resolves I-94d306a4621850719eef9ef7b2265bf7 (already in the task's resolves). Verified: spec-validation success, build --check success, full suite 886 passed / 4 skipped, task-validation ok, delivery ok.

What changed (module.issues only; write path kept as you decided: one command per write, merge lock held throughout, git commit --only with author identity and hooks):
- Reads show only committed records: read_issue / list_issues / resolve_report read the primary worktree's HEAD through git ls-tree + cat-file --batch, never the files; revision = digest of the committed bytes. A record published but not committed, including during the publish-to-commit window, is never visible. check alone still reads files (read_record_file).
- Recovery before every write, under the merge lock (also when the caller already holds it, as a task merge does) and before the write reads its record: git status --ignored -uall over .concorde/issues/ finds record files differing from HEAD and .concorde-write-* temporaries. A record a write left behind (a valid record of its Issue that continues the committed one) is put back to HEAD (git checkout HEAD -- path), or removed when HEAD has none (git rm --cached + unlink); temporaries are removed. Recovery commits nothing and touches no other path.
- A write that fails after publication (directory sync, Git) puts its record back before refusing; when that also fails it refuses with the new code recovery_failed (environment), saying the record stays uncommitted and invisible until the next write or `concorde issues recover`.
- New action `concorde issues recover` -> {recovered:[{path,action}], left:[{path,reason}]}. No MCP tool.
- Identical retry: the earlier receipt is returned only when the committed record holds the report.
- Promise qualified: a refusal commits nothing and leaves nothing a read shows; only recovery_failed or a killed process can leave an uncommitted record, which the next write puts back. Store never deletes a committed record.
- New error codes: recovery_failed and uncommitted_change, both environment. New requirements committed-visible, uncommitted-recovered and foreign-change-kept; 8 new scenarios (sync failure, put-back failed, killed writes, foreign change, recover action, hidden uncommitted records) with tests.

Decisions I made without the developer (in the decision log):
1. Repair rolls back and never commits the leftover record. Committing it would record a report whose writer was told it was refused, and a CLI retry (new invocation each run) would then create a duplicate Issue. Rolling back keeps "receipt means committed" the only way a report gets recorded, and makes every refused or killed write safe to repeat. I rejected the brief's other option (commit a valid leftover).
2. A record change no write leaves (hand edit, invalid record, deleted committed record) is kept as it is. Only writes of that one Issue are refused, with uncommitted_change; writes of other Issues go on. This follows "don't touch unrelated changes".
3. Known edge: a record left uncommitted in some project by Concorde from before today's commit-on-write design would count as a leftover and be removed on the next write. I accepted this under the no-backward-compatibility rule; tell me if any develop-install project may still hold such records.

Open, outside module.issues. I filed these as Issues rather than escalating, because delivery does not depend on them:
- I-7f0b88c134525f939c7c2aed819e8984 (module.tasks, preferred-fix, medium): task merge should call recover_issues(primary, locked=True) before its primary_dirty check. Until then, a leftover from a killed Issue write blocks merges with primary_dirty, and the workaround is to run `concorde issues recover` in the primary worktree.
- I-539ca8e057db5d859ff5995066608904 (module.main-session, preferred-fix, medium): the main-session guidance and MCP tools should know about `recover`, recovery_failed and uncommitted_change.
I filed both with this worktree's issues command (--task), because the brief says the MCP Issue tools refuse severity. The command ran this branch's new write path against the real primary worktree, and the primary's Issue directory stayed clean.

## Closed: merged, 2026-10-01T15:39:51Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit f811750128d139f6c1a6040849092963b438202a into main and closed it as merged. Nobody answers a report after that.
