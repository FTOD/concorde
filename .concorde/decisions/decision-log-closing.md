# Decision log: decision-log-closing

Goal: Make the decision log committed to the primary branch hold the task's closing entry, as the copy in the history does, and record an Issue that a task session reports to its main session by a session name that can change

## Brief (main agent ".concorde/evidence 目录用途", 2026-09-30)

Follow-up of `decision-logs-in-git` (merged as 954528e6). The developer asked for two things.

### 1. The committed decision log must hold the closing entry

Observed: `.concorde/decisions/decision-logs-in-git.md` on main lacks the last two lines of
`.concorde/history/decision-logs-in-git/decisions.md`, the closing entry
`## Closed: merged, 2026-09-29T17:15:29Z`. Cause: `task merge` adds the log to the merge commit
(`src/concorde/tasks/merge.py` `_merge`) before its checks run and before the close, and the close
appends the closing afterwards (`store.py` `_log_closing`) while `commit_decision_log` returns early
because the path is already in HEAD. A task closed without a merge is not affected.

The developer's decision: fix it, so that the committed log equals the log as the task ended.
Constraints from the earlier decisions (keep them):
- The merge commit still adds the task's decision log, so that the delivery <-> log relation stays
  Git's own (second parent = delivery commit, same commit adds the log, `Concorde-Task` trailer).
- A merge undone by a failed check commits no log; `merge_incomplete` / `--resume` / `--abort` stay
  correct.
- Prefer a design that adds no extra commit per merge; if the only sound design needs one (for
  instance a follow-up "keep the decision log" commit when the copy in HEAD differs), say why in
  this log. Escalate only if the choice changes a promise beyond this.
Update the Tasks Specs (module, contracts, requirements, scenarios) and the tests accordingly.
Do not rewrite or amend `.concorde/decisions/decision-logs-in-git.md` history; do update that
file's content on this branch so that it equals the history copy (the two closing lines), since
that is the observed instance.

### 2. Record an Issue (report only, no fix in this task)

The developer decided the defect is recorded as an Issue, not fixed now. Write the report and run
`python3 scripts/issues.py report --file <report> --task decision-log-closing` (the `concorde
issues` command of this worktree). Owner: `module.task-session`. Content, with the evidence:
- What: a task session reports to its main session with SendMessage to the name given by
  `concorde task session <task> --main <name>`, recorded in the task record. A main session's name
  can change: the main session of `decision-logs-in-git` was `concorde-a2` when it started the
  task session, was restarted (it re-read its instruction files) and then carried the automatic
  title ".concorde/evidence 目录用途"; its ListAgents short reference changed as well (ff9211 to
  645867). The delivered report failed with "No agent named 'concorde-a2' is reachable. Use
  ListAgents to see everyone you can message." The task session correctly did not guess another
  recipient and went idle; the developer noticed only because nothing came back.
- Why it matters: the delivery of a task can go unnoticed indefinitely; the owner-only wake rule
  depends on the recorded main session being reachable.
- Evidence: the task session transcript copied into
  `/home/zhenyu/concorde/.concorde/history/decision-logs-in-git/sessions/02bca2c4/` (the SendMessage
  call and its result near the end), the task record `.../history/decision-logs-in-git/task.json`
  (`sessions[].main` = `concorde-a2`) and its decision log entry "Main agent (2026-09-29T17:15Z):
  report not received; merge route".
- Possible directions, not decided: identify the main session by something stable (its Claude
  Code session id, or the project MCP server's registration), let the task session fall back to
  recording its report where the main agent looks (task record, `register_wait` on `delivered`
  already wakes the owner if it waits), or let the main session re-register its current name.
Close nothing; the Issue stays open.

### How to finish

Verify as `concorde-development` says, commit verified steps, append decisions and non-ok results
here, run `task-validation` and `delivery`, and message the main agent
".concorde/evidence 目录用途". If that name is not reachable, do not guess: record the report in
this log and stop; the main agent also waits on the task becoming `delivered`.

## Task session (2026-09-30): design of the closing in the committed log

- **Chosen design: the merge commit carries the closing in advance, no extra commit per merge.**
  `_merge` writes the log followed by `store.closing_entry(...)` for outcome `merged`, dated
  `merging.since` (the merge's recorded start), and the close run by the merge passes that same
  time as `closed.at` (`close_locked(..., at=merging["since"])`), so the close appends exactly the
  bytes the merge commit already holds. A merge undone by a failed check resets the copy away and
  the task log never got a closing; `--resume` reuses the recorded `since`, so it stays equal too.
  A missing log gives a copy holding the closing alone, as the close would create it.
- **Fallback: `commit_decision_log` now compares bytes.** It commits (`concorde: keep the decision
  log of <task>`, file alone) whenever HEAD does not hold the log byte for byte, not only when the
  file is absent. This only happens when the log changed between the merge commit and the close,
  e.g. an entry the main agent adds before `--resume`; then one extra commit is sound and needed.
  On a refused commit it restores HEAD's earlier copy instead of deleting the file.
- **Rejected:** amending the merge commit after the close (changes the commit the checks examined
  and `merging.after`); always a follow-up commit (a second commit per merge, which the brief
  asked to avoid); leaving the merge commit's copy without the closing (the defect).
- **Consequence, within Tasks:** a merged task's `closed.at` is the merge's start, not the end of
  its checks. The task trace node's `ended_at` stays the real end of the close, so the node never
  ends before its merge attempt node. Recorded in `contract.tasks.record` (version 13 -> 14),
  the merge row and the decision-log-commit paragraph of the contracts, `req.tasks.decision-log-committed`,
  module.md (with a "why" paragraph) and scenarios (`scenario.tasks.merge` sharpened, new
  `scenario.tasks.merge-log-changed`, verified by `test_a_log_changed_after_the_merge_commit_is_committed_again`).
- `.concorde/decisions/decision-logs-in-git.md` now equals the history copy (the two closing
  lines added); its earlier history is untouched.
- Commit 48c31807. Verified: `build --check` ok, `spec-validation` ok, full suite 785 passed,
  4 skipped.

## Task session (2026-09-30): the Issue

- Recorded `I-2dd7448eb4f552109bd560ae47b789c9` (owner `module.task-session`, type `limitation`,
  open), commit 728e9fce. Type `limitation` rather than `bug`: the task session behaved as its
  guidance says; the recorded name is what is insufficient.
- Correction to the brief's evidence: the history's `task.json` has no `sessions` field (null);
  the name `concorde-a2` is in the session's trace node `sessions/02bca2c4/trace.json`
  (`content.data.main`). The report cites that, and the transcript lines 1010/1011 (SendMessage
  and its result).
- The report's `evidence` paths must exist in the recording project (the task worktree), where the
  history is not, so its only evidence path is the committed `.concorde/decisions/decision-logs-in-git.md`;
  the history files are named by absolute path in the description rather than misusing `origin`.

## Task session (2026-09-30): delivered

- `task-validation` ready (no blocking findings, no warnings); `delivery` ok, delivery commit
  b7bde2b6 on `concorde/decision-log-closing`.
