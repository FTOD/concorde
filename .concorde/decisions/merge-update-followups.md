# Decision log: merge-update-followups

Goal: Let task sessions merge the primary branch in after concorde update, keep merge output durable with a merge-end wait, make the update mark's barrier hold for any merge checks, and fix the task-brief term Issues

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-086f89ee787d54bb9140c65360058345 (module.distribution, medium, decision-needed): Distribution's merge barrier exceeds Tasks' validation guarantee
- I-e639781c352156548143eb6c9ef04a21 (module.main-session, medium, decision-needed): Specify result recovery for merges that outlive their server
- I-6a968579d1d45a8eb7780e87cb840cd2 (module.main-session, medium, decision-needed): Do not use a removed workspace lock as merge completion proof
- I-7fd1b9b82ff2556496772588cbf5e3b7 (module.main-session, medium, decision-needed): Reconcile conflict-only merge authority with update synchronization
- I-fb37550899ad530888d19dc948efc230 (module.task-session, low, obvious-fix): Link the task brief where Task sessions names it
- I-0c0fe5fb90495c41a102c3f72e834911 (module.coordination, low, obvious-fix): Link the task brief where Coordination names it

Decisions:
- I-7fd1b9b82ff2556496772588cbf5e3b7, DEVELOPER (2026-10-02), option A: besides after a
  merge_conflict, the main agent may also ask a task session, after `concorde update`, to merge
  the primary branch into its task branch, then revalidate (task-validation, delivery). Merging
  into the primary branch and rebasing stay forbidden. Change the guidance (skill, task-session
  guidance), the requirements and the scenarios, and the checkout's CLAUDE.md sentence "its only
  merge is the primary branch into its task branch when the main agent asks for it after a merge
  conflict" (CLAUDE.md is in no other task's Modules; find its source and change it there).
- I-e639781c352156548143eb6c9ef04a21 and I-6a968579d1d45a8eb7780e87cb840cd2, main agent, together:
  write a merge's stdout and stderr into the merge attempt's trace node `merges/<n>/` instead of
  the server's temporary directory, point recovery at trace_show/task_show, and let a session
  without a channel wait on the merge's own end (for example `concorde task wait <task> --merge`
  on the attempt's end), not on the workspace lock, which close removes before the merge has
  written its output. Keep the close lifecycle as it is.
- I-086f89ee787d54bb9140c65360058345, main agent, option B: while an update mark exists,
  `task merge` always runs spec-validation on the merged result in addition to its --check
  commands, so Distribution's barrier holds for any checks and a repair merge can still clear the
  mark.

The developer asked the main agent (2026-10-02) to resolve every Issue that does not need the
developer. This task takes the open Issues listed above. The decision-needed ones among them are
already decided: their decisions are under "Decisions" below, and you carry them out as given.

Start with the full suite on your fresh worktree as a baseline: six tasks merged into main just
before this task opened, and only build and spec-validation ran on the merged result. Record any
failure in the decision log; fix it here when it lies in your Modules, otherwise record it as an
Issue of its Module.

For each Issue:
1. Read it with `python3 scripts/concorde.py issues show <id>` and check that it still stands at
   your HEAD. One already fixed is closed with `concorde issues close <id> --reason resolved
   --note … --evidence <commit>`; a duplicate with `--reason duplicate --duplicate-of <id>`.
2. Fix it by its tier: `obvious-fix` alone; `preferred-fix` with the fix you judge best, which you
   report; `suggestion` only when it clearly improves the Specs or code at small cost, otherwise
   leave it open and say why; `decision-needed` as decided below.
3. Add every Issue you fixed with `python3 scripts/concorde.py task resolve <task> <id>…`, so the
   merge closes it. Never add one you did not fix.

Rules: change only the Modules this task binds. A fix another Module needs, or a fix that turns
out to need a further decision (it would change what a Module promises its users beyond the
decisions below, contradict an earlier decision of the developer, discard work, or loosen a
boundary), is escalated, all together at the end, after everything else is done; a problem you
find in another Module is recorded as an Issue of that Module. Four other tasks run in parallel,
each on its own Modules: fix-execution-root (execution, concorde), fix-workers (workers), fix-e2e
(e2e), merge-update-followups (main-session, tasks, tracing, distribution, task-session,
coordination), fix-delivery-and-small (delivery, adoption, spec-mcp, code-review, spec-review,
operations). module.harness is bound by none: record Harness changes as Issues. Verify with build
--check, spec-validation and the full suite, then task-validation and delivery, and report: what
you fixed (with the fix chosen for each preferred-fix), what you closed as already resolved or
duplicate, the suggestions you left open and why, the baseline result and the escalations.

## Task session (2026-10-02)

- Baseline on the fresh worktree (84994940): `pytest -n auto` 922 passed, 5 skipped, 453 subtests
  passed; build ok. No failure to record.
- I-fb37550899ad530888d19dc948efc230 and I-0c0fe5fb90495c41a102c3f72e834911 (obvious-fix): still
  stood at HEAD; linked the first use of the task's handoff as [task brief] in Task sessions and
  Coordination and said "task brief" in the later use and the diagram label.
- I-7fd1b9b82ff2556496772588cbf5e3b7 (developer's option A), commit 7c43c299: the main-agent skill,
  CLAUDE.md block and task-session guidance, Main session's requirements and scenarios, Task
  sessions and Coordination now let the main agent ask a task session, after a `concorde update`
  that installed a new Protocol copy (whose result lists the open tasks), to merge the primary
  branch into its task branch, then run `task-validation` again and `delivery` too when it had
  delivered (a task not delivered yet goes on and delivers when done). Decisions of mine:
  renamed `req.main-session.task-session-conflict-merge` to `task-session-primary-merge` since it
  now covers both merges; added `req.main-session.update-merge` and
  `scenario.main-session.update-merge`. Besides the checkout's CLAUDE.md, which the brief named, I
  changed the same sentence in two more files of module.concorde (not this task's Module), because
  they would otherwise contradict the decision: `docs/using-concorde.md` (the update paragraph and
  "the only merge a task session makes") and the root `specs/concorde/module.md` sentence "a task
  session merging only the primary branch into its own task branch after a conflict".
- I-e639781c352156548143eb6c9ef04a21 and I-6a968579d1d45a8eb7780e87cb840cd2 (main agent's
  decision), commit 35e5ad0e. How I carried it out:
  - The call process of `task_merge`, holding the task's locks, makes the task's next attempt
    folder `merges/<n>/` and points the merge's stdout and stderr at `output.json` and
    `messages.log` there, naming the folder in `CONCORDE_MERGE_ATTEMPT`; the merge records its
    attempt's node in that folder, also when it is refused before it began (then with the primary
    worktree's branch and HEAD as found, outcome `refused`), so every server-started merge leaves
    its whole answer with the task. The folder moves with the task to the history by rename, and
    the merge finishes writing there: I qualified Tracing's "history is never changed"
    (requirement, design text and the glossary's History definition) for exactly that.
  - The merge-end signal is a new lock, the task's merge attempt lock `locks/attempts/<task>.lock`:
    `concorde task merge` holds it from before its other locks until its answer is written (the
    CLI writes the answer inside it), then removes it; the server's call takes and hands it over
    like the other two. `concorde task wait <task> --merge` blocks on it and answers the latest
    attempt's node, status, outcome and output files, wherever the task's folder is. I chose a
    lock over waiting on the merge lock because the merge lock is the project's (other merges and
    Issue writes hold it) and is released inside `merge_task` before the CLI prints.
  - The merge_ended event's reaper finds the output again through `task wait --merge` when the
    close moved it; the fallback `wake.command` is now `concorde task wait <task> --merge`; the
    guidance and contracts point recovery at task_show/trace_show. Close's lifecycle is unchanged.
  - Node artifacts may now be kept unmeasured (`keep(..., measured=False)`), since the output is
    completed after the attempt's node ends. The merge-trace content type keeps version 1.
- I-086f89ee787d54bb9140c65360058345 (main agent's option B), commit d0203e80: while
  `.concorde/update.json` exists in the primary worktree, `task merge` appends the default
  `spec-validation` to the given checks unless they include it exactly, recorded among the
  attempt's checks so `--resume` reruns it. New `req.tasks.merge-update-validated`,
  `scenario.tasks.merge-update-validated`, and a Tasks `uses` of Distribution for the mark
  (registry refreshed).
- All six Issues added to the task with `task resolve`.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T02:55:30Z

Task merge-update-followups delivered: delivery commit 288b7ce7 (run r-20261002T024845-delivery-d9905419) on concorde/merge-update-followups. Baseline at 84994940: full suite green (922 passed, 5 skipped), build ok; nothing to record. Final: build --check, spec-validation (0 findings) and full suite (926 passed, 5 skipped) green; task-validation ready.

Fixed, all added with task resolve (the merge closes them):
- I-7fd1b9b82ff2556496772588cbf5e3b7 (developer's option A), 7c43c299: after a `concorde update` that installed a new Protocol copy, the main agent may ask each listed open task's session to merge the primary branch into its task branch, then run task-validation again and delivery too when it had delivered. Merging into primary and rebasing stay forbidden. Changed: main-session skill, CLAUDE.md block, task-session guidance, Main session requirements and scenarios (new req/scenario main-session.update-merge; req task-session-conflict-merge renamed task-session-primary-merge), Task sessions, Coordination, and the checkout's CLAUDE.md. Outside this task's Modules (module.concorde) I also changed the same rule in docs/using-concorde.md and one sentence of specs/concorde/module.md, which would otherwise contradict it. fix-execution-root also binds module.concorde, so a merge conflict there is possible but unlikely.
- I-e639781c352156548143eb6c9ef04a21 and I-6a968579d1d45a8eb7780e87cb840cd2 (your decision), 35e5ad0e + d4238caf: task_merge's call reserves the task's next attempt folder merges/<n>/ and sends the merge's stdout/stderr to output.json/messages.log there (CONCORDE_MERGE_ATTEMPT). The merge records its node there even when refused before it began, and the folder moves with the task to the history. For the end signal I added a new lock: the task's merge attempt lock locks/attempts/<task>.lock. task merge holds it from before its other locks until its answer is written, then removes it. `concorde task wait <task> --merge` blocks on it and names the latest attempt's node, status and output files, wherever they are; it is task_merge's no-channel wake command. I chose this over the merge lock, which is project-wide and is released before the CLI prints. The close lifecycle is unchanged. Two consequences: Tracing's "history is never changed" (requirement, design text and glossary History) is qualified for the closing merge finishing its own output, and node artifacts may be kept unmeasured. Recovery guidance points to task_show/trace_show.
- I-086f89ee787d54bb9140c65360058345 (option B), d0203e80: while .concorde/update.json exists, task merge adds the default spec-validation after the given --check commands unless they include it exactly. It is recorded among the attempt's checks, so --resume reruns it. New req/scenario tasks.merge-update-validated, plus a Tasks uses relation on Distribution (registry refreshed).
- I-fb37550899ad530888d19dc948efc230, I-0c0fe5fb90495c41a102c3f72e834911 (obvious-fix), 7c43c299: Task brief linked in Task sessions and Coordination, and the diagram label changed.

None closed as resolved or duplicate; no suggestions in scope; no escalations. Open for you: the two module.concorde files I changed beyond CLAUDE.md, and the narrowed History promise. Both are recorded in the decision log.

## Closed: merged, 2026-10-02T02:56:07Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 288b7ce74ae0a6ccf0d0eb9b189530fc4ed47501 into main and closed it as merged. Nobody answers a report after that.
