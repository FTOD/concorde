# Decision log: reports-after-end

Goal: Settle task-session reports when a task ends (merge or close marks unanswered reports as handled by it), make the main agent's restart reconciliation list only active tasks, and document task report/answer/rebind, task wait --rebound, task list --main and the reconciliation in docs/README.md and docs/using-concorde.md

## Brief (main agent, 2026-09-30)

Follow-up of task `main-session-rebind` (merge d4e06d98). The developer decided all three points:

1. **A task's end settles its reports.** After `task merge main-session-rebind`, `concorde task
   answer main-session-rebind --report 1 …` was refused with `task_closed`, since the merge closed
   the task; its delivery report stays unanswered in the history forever. Make `task merge` (on
   success) and `task close` (`--completed` and `--failed`) mark every report still unanswered as
   handled by that end (e.g. an answer saying the task was merged at <commit> / closed with its
   outcome, recorded as by the merge or close, not by the main agent), in the record and the
   decision log.
2. **Reconciliation lists only active tasks.** The main-session guidance's restart steps
   (`prompts/main-session/skill.md` "List the tasks that still name your former name") use
   `concorde task list --main <former name>`, which also lists closed tasks; `task rebind` then
   refuses those with `task_closed` (`src/concorde/tasks/store.py` `rebind`) and their unanswered
   reports look pending. Change step 1 to list only active tasks (`--state active` together with
   `--main`; make sure the two filters combine, and the MCP `task_list` likewise), and check the
   other steps and the Specs describing them agree.
3. **User documents.** `docs/README.md` and `docs/using-concorde.md` do not describe `task report`,
   `task answer`, `task rebind`, `task wait --rebound`, `task list --main` or the main agent's
   reconciliation after its session name changes. Add them in the documents' existing style and
   depth, including point 1's behaviour; format with Prettier.

Not in scope (developer: not a big problem): old task branches whose CLI lacks `task report` /
`--rebound`.

Left to the task session: exact wording of the settling answer, field names, tests and scenarios.
Escalate a change outside `module.tasks`, `module.main-session` and `module.concorde`.

## Task session decisions, 2026-09-30

- **"Active" means not ended, not the derived state `active`.** `--state active` would leave out
  `open`, `delivered` and `merging` tasks, and a delivered task is exactly the one whose delivery
  report waits for the main agent. So `task list --state` now takes a comma-separated list of
  states (as `task wait --until` does) and the MCP `task_list` takes `state` as an array of
  states; the restart step lists `concorde task list --main <former> --state
  open,active,delivered,merging`. The two filters already combined in `store.list_tasks`.
- **Who answered.** Each report's `answer` gains `by`: `main-agent` (`task answer`), `merge`
  (`task merge` closing the task) or `close` (`task close`). The task record's `schema_version`
  becomes 4; a version-3 record is read as version 4 with `by: main-agent` on every answer, as the
  existing upgrade of version 2 does.
- **Settling text.** The merge's answer names the checked delivery commit and the primary branch
  (the merge commit's own hash cannot be in the log copy that commit adds); a close's names its
  outcome with its note or reason. The answer is dated with the closing, and the decision log
  holds it inside the closing entry, so the merge commit's copy of the log still equals the log
  the close leaves.

## Report 1 to the main agent (Tasks plan review operation), 2026-09-30T12:40:03Z

Task reports-after-end delivered at c566bd64f99bd3f55bf32ac0f14d6ae198a553ec (delivery run r-20260930T123844-delivery-a54d430a; task-validation ready, full test suite 832 passed, build --check and spec-validation ok). Merge with the usual --check build / spec-validation.

What changed:
1. A task's end settles its reports. `task merge` and `task close` (--merged, --completed, --failed) answer every report still unanswered, in the same record write that ends the task, with answer {at: closing time, text: how the task ended, by: "merge"|"close"}; `task answer` now records by: "main-agent". The closing entry of the decision log ends with "The <merge|close> answered report(s) <n>, ... of the task session, unanswered until then: <text>", and the merge commit's copy of the log already contains it (so the close commits nothing more). Task record schema_version 3 -> 4 (contract.tasks.record v16); a version-3 record is read with its answers by main-agent.
2. Reconciliation lists only tasks not ended. Step 1 of the skill's "When your session name changed" (and the CLAUDE.md block) is now `concorde task list --main <former name> --state open,active,delivered,merging`. `--state` now takes a comma-separated list of states (as `task wait --until` does); the MCP `task_list` takes `state` as an array. The filters already combined in store.list_tasks; a test now verifies it (scenario.tasks.list-not-ended).
3. docs/README.md and docs/using-concorde.md now describe task report/answer/rebind, task wait --rebound, task list --main --state, the reconciliation after a name change and the settling of reports at a task's end (Prettier-formatted).
Specs updated: Tasks (module, contracts, requirements req.tasks.end-settles-reports and req.tasks.list-filters-combine, scenarios close-settles-reports, merge-settles-reports, list-not-ended) and Main session (module, contracts task_list row, reconcile requirement and scenario).

Decisions I made on your behalf (in the decision log):
- "Only active tasks" read as "tasks not ended", not the derived state `active`: `--state active` would miss delivered tasks, exactly the ones whose delivery report waits. Hence multi-state `--state`.
- A `by` field on answers instead of text alone, with the record version bumped to 4 and version-3 records upgraded on read, which keeps open tasks and older history working.
- The merge's settling answer names the checked delivery commit and the primary branch, not the merge commit, because the merge commit's copy of the log cannot contain its own hash.

Nothing open. Reports already unanswered in the history (e.g. main-session-rebind's report 1) are not changed retroactively.

## Closed: merged, 2026-09-30T12:40:21Z
