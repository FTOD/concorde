# Decision log: decision-logs-in-git

Goal: Drop the evidence bundle and keep each ended task's decision log in Git instead: delivery commits carry only their subject as the delivery marker, task merge (and close) commit the task's decision log to the primary branch, existing bundles are deleted and closed tasks' decision logs backfilled, and conversation records in the history get their own shorter retention

## Brief (main agent concorde-a2, 2026-09-30)

### Developer's decisions (agreed in the main session)

1. **Remove the evidence bundle entirely.** Nothing reads its content (runs, digests, checks,
   confirmations); task state derivation only needs to recognise a delivery commit, and the run
   digests point at `result.json` files that are untracked and removed by retention, so they
   cannot be verified later. `delivery` no longer writes `.concorde/evidence/<workspace>/<n>.json`.
2. **Delete every existing file under `.concorde/evidence/`** (162 folders on main) in this task.
3. **Keep each ended task's decision log in Git.** The decision log is the record worth keeping
   (decisions taken without the developer, escalations and answers, non-ok results with their
   error chains; a few KB per task), while session and worker transcripts are about 85% of the
   history and only local.
4. **Backfill**: commit the decision logs of every task already closed in the primary worktree's
   `.concorde/history/*/decisions.md` (read them from `/home/zhenyu/concorde/.concorde/history/`;
   about 169 files, 1.2 MB) into the same tracked location.
5. **Conversation records get their own, shorter retention** in the history (task session and
   worker `events.jsonl` / transcripts), configured in the Tracing configuration
   `.concorde/tracing.json`; everything else in the history keeps its current retention (kept by
   default). The developer took the main agent's proposal of 30 days as the example; use 30 days as
   the default.

### Decisions of the main agent (ordinary scope, recorded here)

- **Delivery marker**: a delivery commit is recognised by its subject `concorde: deliver
  <workspace>` alone. Drop the trailers `Concorde-Evidence`, `Concorde-Readiness` and
  `Concorde-Workspace` (the subject already names the workspace). `delivered` stays derived, never
  stored: the branch head is a delivery commit of the workspace with exactly one parent and the
  worktree is clean. Delivery's idempotent re-run (a head that already is its delivery commit)
  keeps working from the subject. The run window that only fed the bundle's `runs` goes away.
- **Where the decision log goes**: Coordination, not Delivery, commits it, since Delivery is an
  Execution command that knows nothing of tasks and the log lives in the primary worktree's task
  folder. `task merge` adds the task's decision log to the merge commit at a fixed tracked path,
  proposed `.concorde/decisions/<task>.md`, and gives the merge commit the trailer
  `Concorde-Task: <task>`. The relation delivery <-> log is then Git's own: the merge commit's
  second parent is the delivery commit and the same commit adds the log. If the merge is undone
  because a check fails, the log is not committed.
- **Tasks that end without a merge** (`task close --completed` / `--failed`) also commit their
  decision log on the primary branch, as a commit holding that file alone, under the merge lock,
  so every ended task's log is in Git (the backfill includes failed tasks too). If this turns out
  to conflict with a rule you find in the Specs (for instance about what may be committed on the
  primary branch outside a merge), escalate rather than decide.
- **File name collisions**: check whether a task id can be reused after its task was closed (the
  history key). If it can, choose a collision-free file name (for example the history key) and
  record why.
- **Parallel task**: `drop-pi-subagents-reference` (another main session's) is open on
  `module.concorde` and `module.views`, but it touches `.gitmodules`, `specs/concorde/development.md`
  and the docsite repository test, not the glossary or `docs/`. The main agent judged the overlap
  harmless; a merge conflict, if any, is handled with the usual merge flow. Tasks closed on main
  after this task's base will not be in your backfill; the main agent adds them after the merge.

### Scope to cover (found by the main agent; check for more with grep)

- Specs: `specs/concorde/execution/commands/delivery/{module,contracts,requirements,scenarios}.md`,
  `specs/concorde/execution/commands/module.md`,
  `specs/concorde/coordination/tasks/{module,contracts,requirements,scenarios}.md` and
  `module.md.json`, `specs/concorde/tracing/{module,contracts,requirements,scenarios}.md`
  (including the retention paragraph that says the bundle outlives retention).
- Glossary `specs/concorde/glossary.json`: remove `concept.evidence-bundle`; update
  `concept.delivery-commit`, `concept.decision-log` (now committed when the task ends),
  `concept.history` and `concept.tracing`-related entries touched by the new retention; fix every
  `narrows`/`relates` pointing at the removed concept.
- Code: `src/concorde/delivery/bundle.py` and `command.py`, `src/concorde/tasks/store.py` and
  `cli.py`, the tracing retention code, their tests.
- Guidance and docs: `prompts/main-session/skill.md` and `prompts/main-session/task-session.md`
  ("commits the evidence on the task branch"), `docs/README.md`, `docs/using-concorde.md`.
- `.gitignore` must keep `.concorde/decisions/` tracked.

### Left for the session to decide

Internal structure, naming of functions and contracts, the exact contract version bumps, test
design, and whether to use Concorde Operations or work directly (direct work is fine). Escalate
anything that changes what a Module promises beyond the decisions above.

### How to finish

Verify as `concorde-development` says (build, build --check, spec-validation, relevant tests, the
full pytest suite once on the final input), commit verified steps, run `task-validation` and
`delivery` in this worktree, append every non-ok result and every decision you take to this log,
and message the main agent `concorde-a2` when delivered or when you need decisions.

## Decisions of the task session (2026-09-30)

- **Delivery commit verification.** With the bundle gone, a delivery commit "verifies" when it has
  exactly one parent (as the brief said). `recover-unverified` and `delivery-unverified` now use a
  merge commit given the delivery subject as the case that does not verify; a cherry-picked or
  reworded one-parent commit is no longer told apart, which the Delivery Spec now says openly
  ("the subject is a mark, not a proof").
- **Empty delivery commits.** When every step was committed and nothing is confirmed, the delivery
  commit changes no file; Delivery now commits with `--allow-empty` so the subject still marks the
  delivery. The output keeps `sequence` (its number among the workspace's deliveries) and drops
  `bundle`; `contract.delivery.output` v4. `req.delivery.evidence` became `req.delivery.marked`.
- **Module renamed.** `src/concorde/delivery/bundle.py` became `commits.py` (subject, message,
  reader, one-parent check). Delivery no longer reads the run store or Workers, so its `uses` of
  Workers and its reliance on `concept.run-store` were removed.
- **Trace relations.** `bundle` and `found_bundle` were removed from the node contract (v3);
  readers never validate old nodes, so history nodes that carry them still read.
- **Merge always makes a merge commit.** `task merge` runs `git merge --no-ff --no-commit`, writes
  the log to `.concorde/decisions/<history key>.md`, `git add -f`, and commits with
  `Merge branch 'concorde/<task>' at <commit>` + `Concorde-Task: <task>`. A refused commit aborts
  the merge, removes the copy and refuses `git_failed`. The fast-forward branch of
  `merge_commit()` was removed since it can no longer happen.
- **The merged log lacks its closing entry.** The merge commit carries the log as it stood when
  merged; the "## Closed: merged" line the close appends afterwards stays only in the history copy.
  Adding a second commit per merge for one timestamp line was not worth it.
- **Close commits the log alone** when the primary branch lacks the file (completed, failed, and
  `--merged` after a hand merge): `git add -f` + `git commit --only -- <path>`, so the primary
  worktree's own staged and unstaged changes are untouched. A detached HEAD or a Git refusal
  raises the new code `decision_log_uncommitted` (reason environment) after the record was closed
  and the log appended, leaving the folder current; the same close run again commits and finishes.
  I found no Spec rule against Tasks committing on the primary branch outside a merge (the
  main-agent rules restrict the main agent's own edits; Tasks already commits merges there), so I
  did not escalate this.
- **History keys can collide, so logs are named by history key.** Task ids can be reused once the
  branch is deleted, and retention may remove the earlier history folder while its log stays in
  Git. The history key is now free only when neither `history/<key>` nor
  `.concorde/decisions/<key>.md` (in the worktree or HEAD) exists (`layout.history_key(..., taken)`).
  The merge chooses the key before merging and stores it as `merging.history`
  (`contract.tasks.record` v13) so `--resume` closes under the key its merge commit used; a merging
  record without it falls back to computing the key.
- **Conversation retention.** `retention.conversation_days` in `.concorde/tracing.json`, optional
  (absent means the default 30), so existing configuration files stay valid;
  `contract.tracing.configuration` v2 keeps `schema_version` 1. Conversation records are every
  `transcript.jsonl`, `events.jsonl` and `transcript/` folder at any depth of a history folder;
  `req.tracing.history-unchanged` now allows retention to remove them, and a new
  `req.tracing.conversations-shorter` states the rule. Artifact entries of the trace nodes stay and
  may name a removed file.
- **New scenarios/tests:** `scenario.tasks.close-commits-log`, `scenario.tasks.merge-commit-refused`,
  and extended `merge`, `merge-check-failed`, `close-merged`, `history-key`, `tracing.prune`.

## Non-ok result: task-validation r-20260929T165421-task_validation-92017ff1 (blocked)

`not_deliverable` with two blocking findings: `check.tasks.tests` and `check.task-session.tests`
failed (11 and 1 tests) with `decision_log_uncommitted` ... `git commit exited 128 on master:
Author identity unknown`. The check sandbox has no Git identity, and `OperationProject`, unlike
the merge tests, set none, so every close in those tests could not commit its decision log.
Repaired in the fixture (repository-local `user.name`/`user.email`), verified with the full suite
under an empty HOME (784 passed, 4 skipped); the product behaviour is as specified (a close
without an identity refuses `decision_log_uncommitted` and can be run again).

## Delivered (task session)

`task-validation` r-20260929T170106-task_validation-8914f532 ok; `delivery`
r-20260929T170640-delivery-cd954c93 ok: delivery commit 849adf26 (sequence 1, no bundle, no
trailers, changes no file since every step was committed).

**Merging needs this branch's code.** The primary worktree's current Concorde recognises a delivery
commit only by its three trailers, so `python3 scripts/concorde.py task merge decision-logs-in-git`
(and the MCP server's `task_merge`, running the same old code) would refuse `not_merged`:
verified read-only, the old code shows the task `active` with no deliveries, while this branch's
code, run from the primary worktree, shows it `delivered`. Recommended: run the merge from the
primary worktree with a temporary copy of this branch's code (not the task worktree itself, which
the close removes while the merge runs):
`git archive concorde/decision-logs-in-git src scripts | tar -x -C <tmp>` then
`.venv/bin/python <tmp>/scripts/concorde.py task merge decision-logs-in-git --check "python3 scripts/concorde.py build" --check "python3 scripts/concorde.py spec-validation"`.
That merge also commits this task's own decision log as `.concorde/decisions/decision-logs-in-git.md`.

## Main agent (2026-09-29T17:15Z): report not received; merge route

- The task session's report (SendMessage to `concorde-a2`) failed: "No agent named 'concorde-a2'
  is reachable". The main session had been restarted and now carries the auto title
  ".concorde/evidence 目录用途", so the name recorded with `task session --main` no longer
  resolved. The session correctly did not guess another recipient. This is a Concorde defect
  (a task session reports to a main session by a name that can change); to be recorded as an Issue
  in a follow-up task.
- Merge route (decided without the developer, ordinary scope): as the session found, main's
  current code recognises a delivery commit only by the removed trailers, so the merge runs from
  the primary worktree with a temporary copy of this branch's `src` and `scripts`
  (`git archive concorde/decision-logs-in-git src scripts`), through `task merge` with the usual
  `--check` commands. Main moved to 1f061513 (drop-pi-subagents-reference merged) meanwhile; its
  decision log will be backfilled after this merge.
