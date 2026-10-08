# Decision log: kernel-merge-marker

Goal: The Kernel defines an unfinished-merge marker of the primary worktree that Tasks writes while a task merge is unfinished and any part may read, and project_review's record commit refuses while it is present

## Task brief (main agent, 2026-10-08)

The developer accepted on 2026-10-08 (task project-review, escalation 2) the risk that
project_review's review record, committed on the primary branch under the merge lock, can land on
top of a crashed, unfinished task merge and block `task merge --resume/--abort`, with a Kernel
marker "later". On 2026-10-08 the developer then decided to fix every known open Issue before the
first full `project_review`, so this task builds it. It resolves I-147773ef (module.kernel,
decision-needed, medium); the main agent decides the Issue's suggested repair:

- The Kernel defines an **unfinished-merge marker** of the primary worktree (for example a file
  beside `.concorde/locks/merge.lock`), with its format and reading rules, as a Kernel contract.
  `req.concorde.halves-apart` stays: no Operation reads a task record; the marker is Kernel state.
- Tasks writes the marker when a task merge has changed the primary branch and its checks have not
  decided yet, and removes it when the merge completes, is undone, resumed to an end or aborted.
  A crash leaves it, which is the point.
- Project review's record commit reads it and refuses while it is present (code and error to
  define), and its Spec's documented risk is replaced by that rule.
- Whether the Issues store switches from reading Tasks' published task-record format to the
  marker is yours to decide: do it if it simplifies and keeps the Issues store's promise; record
  the decision.

The 2026-10-08 Issues-store recovery and merge semantics (merge_incomplete, --resume, --abort)
must keep their current outcomes. Escalate anything that changes what `task merge` promises.
Deliver with `task-validation` then `delivery`; run the full suite once on the final input.

## Task session decisions (2026-10-08)

- **Marker location: `.concorde/unfinished-merge.json` of the primary worktree, Git-ignored,
  not inside `.concorde/locks/`.** Tracing's layout contract says `locks/` holds "every lock and
  nothing else", and module.tracing is not one of this task's Modules. The Kernel's registration
  adds the path to the `.gitignore` entries it declares (and this checkout's `.gitignore`), so the
  merge's `primary_dirty` audit never sees it.
- **Marker format: a Kernel contract `contract.kernel.unfinished-merge` (version 1)** with
  `part` (the part that wrote it, the only one that replaces or removes it), `by` (the command),
  `pid`, `since`, `branch`, `before`, `merging` (the commit merged in), `after` (the merge commit
  or null) and `finish` (the commands that finish it). Generic: the Kernel knows no task; Tasks
  fills it from its `merging` record. New glossary term "Unfinished-merge marker" owned by
  module.kernel.
- **Order that keeps the Issues and project_review guarantees:** Tasks writes the marker under the
  merge lock *before* it records the task `merging` (so before `git merge`), updates `after` once
  the merge commit exists, and removes it only *after* the task record no longer says `merging`
  (end_merge or the close). A crash in either window leaves a marker with no merging task, which
  blocks writes but never lets one land on an unfinished merge. Whenever Tasks takes the merge lock
  it first reconciles: no task stored merging → it removes a marker its part wrote; a task stored
  merging and no marker (only a merge left by Concorde before this change) → it writes it.
  `task merge` promises (merge_incomplete, --resume, --abort, their outcomes) stay unchanged.
- **Readers refuse while the marker is present or cannot be read**: a reader holds the merge lock,
  so the writer has ended (or handed the lock on after removing the marker). project_review's
  record commit refuses with `merge_incomplete` (reason environment), unreadable marker with
  `unreadable_merge_marker`; both surface as the run's `record_unpublished` as every record refusal
  does. The documented accepted risk in project-review/module.md is replaced by this rule.
- **The Issues store switches to the marker (decision left to the session by the brief).** Reason:
  it removes Issues' only use of Tasks (reading Tasks' published task-record format and rebuilding
  Tasks' account), gives Issues and project_review one Kernel reader, and keeps the promise
  `req.issues.no-write-during-merge` by the order above. `merge_incomplete` keeps its outcome; the
  environment code `unreadable_task_record` becomes `unreadable_merge_marker` (an unreadable task
  record no longer blocks an Issue write; Tasks still refuses its own commands on it). Accepted
  gap: a merge left unfinished by Concorde before this change has no marker until the next Tasks
  command that takes the merge lock reconciles it (rapid-iteration rule: no compatibility).
- **Not ok: the first full suite (2026-10-08) failed 2 tests** outside this task's Modules:
  `tests/concorde/code_review/test_code_review.py::test_a_refusal_of_the_issue_store_is_an_error_not_an_issue`
  and `tests/concorde/spec_review/test_panel.py::test_a_refused_report_stops_the_module_and_is_no_issue`.
  Both faked an unfinished merge with a `merging` task record, which the Issue store no longer
  reads. Decision: change only their fixture to write the Kernel's marker instead (same refusal,
  same assertions); a mechanical consequence of the Issues store's switch, no promise of
  code_review or spec_review changes.
- Kernel spec wording: `req.kernel.marker-spans-merge` requires the marker to stay present from
  before the merge is recorded until after it is decided, written and removed only under the merge
  lock (not that one process holds the lock throughout, since `--resume`/`--abort` finish it in
  another process). Issues guidance (prompts/guidance/issues/skill.md) gained how to handle
  `merge_incomplete` and `unreadable_merge_marker`.

## Report 1 to the main agent (concorde-d4), 2026-10-08T02:47:53Z

Task kernel-merge-marker is delivered: delivery commit d9b76d0b91320616eb2facb0bb1c6835c69faf4c (run r-20261008T023908-delivery-ac5ba998). task-validation r-20261008T023045-task_validation-dd79e6df was ready with nothing blocking. The full suite passes on the final input: 1308 passed, 5 skipped. The task resolves I-147773ef (added with task resolve).

What it does:
- Kernel: a new glossary term "Unfinished-merge marker", stored as `.concorde/unfinished-merge.json` of the primary worktree. Git ignores it through the Kernel registration's gitignore and this checkout's .gitignore. Its contract is `contract.kernel.unfinished-merge` v1, with the fields part, by, pid, since, branch, before, merging, after and finish. `src/concorde/kernel/marker.py` reads, writes, removes and describes it. Reads refuse with `marker_unreadable` or `marker_invalid`. New requirements: `req.kernel.marker-spans-merge`, `marker-refuses-commits` and `marker-read-whole`. There are scenarios and tests for each.
- Tasks: the marker is written before the task is stored `merging`. It is rewritten with the merge commit, and removed after `end_merge` or after the merge's close clears `merging`. Whenever Tasks takes the merge lock, it reconciles the marker with its records. A Tasks marker with no merging task is removed. A merging task without a marker gets one. Another part's marker is left alone. There is a new code `marker_unwritable`, and nothing changes when it occurs. The outcomes of `merge_incomplete`, `--resume` and `--abort` are unchanged. New are `req.tasks.merge-marked`, `merge-marker-reconciled` and scenarios `merge-marker` and `merge-marker-reconciled`.
- project_review: the record commit reads the marker under the merge lock. It refuses with `merge_incomplete` (reason environment), or with `unreadable_merge_marker` when the marker cannot be read. Either way the run ends `record_unpublished`. The accepted-risk paragraph is replaced by this rule (`req.project-review.record-unfinished-merge`).

Decisions I took (all in the decision log):
1. The marker lives at `.concorde/unfinished-merge.json`, not in `locks/`. Tracing's layout says `locks/` holds "every lock and nothing else", and module.tracing is not one of this task's Modules.
2. Order: marker first, then the `merging` record, and the marker is removed last. A crash in either window leaves a marker that blocks writes but never lets one through. Tasks' next command under the merge lock removes a stale one.
3. The Issues store switched to the marker (the brief left this to me). Issues no longer reads Tasks' task records and drops its `uses` of module.tasks. `merge_incomplete` keeps its outcome. The code `unreadable_task_record` becomes `unreadable_merge_marker`. An unreadable task record no longer blocks Issue writes; Tasks still refuses its own commands on it. Accepted gap: a merge left unfinished by Concorde before this change has no marker until the next Tasks command that takes the merge lock (rapid-iteration rule).
4. Non-ok result: the first full run failed 2 tests in code_review and spec_review. They faked an unfinished merge with a merging task record. I changed only their fixtures to write the marker; no promise of those Modules changed.
5. The Issues guidance (prompts/guidance/issues/skill.md) now says how to handle `merge_incomplete` and `unreadable_merge_marker`.

Open: nothing for the developer. Merge with the usual checks.

## Closed: merged, 2026-10-08T02:48:06Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit d9b76d0b91320616eb2facb0bb1c6835c69faf4c into main and closed it as merged. Nobody answers a report after that.
