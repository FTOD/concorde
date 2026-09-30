# Decision log: main-session-rebind

Goal: Keep task-session reports reachable when the main agent's session name changes: record reports and escalations in the task record before messaging, let the main agent rebind a task to its new session name (command and MCP tool) with the task session re-reading the current main before each report and waiting for a rebind when delivery fails, and have the main agent reconcile its tasks after a restart

## Brief (main agent, 2026-09-30)

**Defect.** `concorde task session <task> --main <name>` freezes the main agent's Claude Code
session name into the task session's first prompt and the task record. A Claude Code session's
name (and its ListAgents ref) does not survive the main session restarting or being resumed:
observed today, main `concorde-d1 [8da772]` came back as `Tasks plan review operation [be81ec]`.
Task `plan-review-docs` delivered, its SendMessage to `concorde-d1` failed with "No agent named
'concorde-d1' is reachable", and its report stayed only in its decision log; nothing woke the main
agent. Task `native-session-records` (main `concorde-63`, gone) sat delivered and unmerged for the
same reason. The only-owner-woken rule means no other session notices either. Evidence:
`.concorde/decisions/` log of `plan-review-docs` (its last bullet), and its task record's
`sessions[].main`.

**Developer's decisions** (all three parts):

1. **Reports are durable.** A task session records its report (delivery report, or the batch of
   escalations with their question) in the task record first, e.g. a `concorde task report`
   command, and only then messages the main agent: SendMessage is only the wake-up, and a failed
   send loses nothing. The main agent can read a task's unanswered reports from `task show` /
   the MCP server.
2. **Rebinding the main.** A command, e.g. `concorde task main <task> --main <new name>`, and the
   matching project MCP server tool, change the task's main session name in the record (keep the
   history of earlier names in the record/trace). The task session reads the current main from
   `concorde task show` before every report instead of from its first prompt; when SendMessage
   fails it waits, with `concorde task wait` in background Bash (a new wait condition such as the
   main being rebound), and sends again to the new name.
3. **Reconcile after a restart.** The main-session guidance tells the main agent: when ListAgents
   reports a name different from the one it gave its tasks (for example after a resume), list the
   tasks whose main is its former name, rebind each to its current name, and read their
   unanswered reports before anything else.

**Left to the task session:** command and field names, the record's schema change (rapid
iteration: no compatibility needed, but tasks open across the change must not break), the wait
condition, how a report is marked answered, scenarios and tests. Keep one word per meaning (the
glossary's terms: main agent, task session, task record, decision log); a new glossary entry only
if it meets the admission rule. If the fix needs a change outside the bound Modules (e.g.
Tracing), escalate first.

## Task session: design decisions (2026-09-30)

Taken without the developer, within what the brief left to the session:

- **Where the main lives.** The task record gains `main`, the main agent's session its task
  sessions report to now (record `schema_version` 3, contract.tasks.record v15). `task session
  --main` sets it, and the new `concorde task rebind <task> --main <name>` changes it; the task's
  trace node keeps every name as `mains` ([{main, at}], contract.tasks.task-trace v2), and each
  session node keeps the `main` it was started for. Reason: the record is what the task commands
  act on, and `task list` prints records, so a main agent finds the tasks of its former name with
  `task list --main <former>` (new filter); the history of names is trace, as the Spec's split
  between record and trace requires. A record written before the change (schema_version 2, no
  `main`) is read with `main` taken from its latest session node, so tasks open across the
  change keep working.
- **Reports.** New `concorde task report <task> --text <report> [--escalation <n>]…`, run by the
  task session before every message to the main agent: it appends the report to `reports` of
  the task's trace node (numbered from 1, with the time, the escalations it carries, the main it
  was addressed to and `answer` null) and to the decision log, and prints the report with the
  record's current `main`, the session to message. Reports live in the trace, beside the
  escalations, not in task.json: the Spec keeps the record small and the history in the trace;
  `task show` lists them. The brief's "task record" is read in the loose sense the skill already
  uses for escalations.
- **Answered.** New `concorde task answer <task> --report <n>… --text <answer>` (main agent):
  records the answer on each named report and appends it to the decision log; a report whose
  `answer` is null is unanswered. `task show` gives `reports`, each with its `answer`.
- **Wait for a rebind.** New wait `concorde task wait <task> --rebound <name>`: returns once the
  record's `main` is not `<name>`, with the new `main`; watches the task folder's `task.json`
  through inotify, no polling; a task that ended ends the wait with `wait_unreachable`.
  `register_wait` gains `rebound` (with `task`).
- **MCP tools.** `task_rebind`, `task_report`, `task_answer`; `task_list` gains `main`.
- **Not guarded by an unfinished merge.** `report`, `answer` and `rebind` change only the task's
  record and trace, never Git, and must work while a merge is unfinished, since a task session
  reports a `merge_incomplete` refusal with them and the main agent may reconcile before it
  resumes the merge; they are refused only for a task that ended (`task_closed`). `escalate`
  keeps its guard.
- **Who may run them.** `rebind` and `answer` run in the primary worktree only (main agent's);
  `report` runs in any worktree, like `escalate`.
- **No glossary entry** for "report": ordinary word. The definitions of `concept.task-record`
  (gains the main agent's session) and `concept.decision-log` (reports and answers appended),
  both owned by module.tasks, are updated.
- **No plan_review**: the brief does not ask for it and the developer's decisions fix the design.

## Task session: reports and names moved into the task record (2026-09-30)

Revises the "Reports" and "Where the main lives" entries above. I first put `mains` and
`reports` in the task's trace node (contract.tasks.task-trace v2). That breaks tasks open across
the change: a task worktree still on an earlier Concorde escalates with its own code, which writes
the task node as content version 1 and is refused (`content_invalid`) once the primary's new code
has written version-2 fields into that node (at a rebind or a session start). An earlier Concorde
carries unknown fields of task.json through unchanged, so `main`, `mains` and `reports` now all
live in the task record (schema_version 3, contract.tasks.record v15), and the task trace contract
is unchanged (v1). This is also the brief's own wording ("records its report ... in the task
record"). Reason in the Spec: whether a report is answered is state the task commands act on,
like the name it was sent to. `task show` prints them inside `record`; `rebind` prints
`{record, former}`. A v2 record is read with `mains` from its session nodes, `main` the latest of
them, and no reports.

Known transitional limit, not fixed: a task session started after this merges, for a task whose
branch predates it, gets the new guidance (rendered from the primary's package) but its worktree's
`concorde` lacks `task report` and `task wait --rebound`; the project MCP server's `task_report`
(served from the primary's package) still works for it. Tasks opened after the merge are
unaffected.

Open follow-up outside this task's Modules: the user documents (`docs/README.md` command table,
`docs/using-concorde.md` MCP tool list), owned by the root Module, do not yet mention
`task rebind`, `task report`, `task answer` and `task wait --rebound`.

## Report 1 to the main agent (Tasks plan review operation), 2026-09-30T12:19:50Z

Task main-session-rebind delivered: delivery commit 69a874e8cde640c09d2d8ef259a6e2ab01039a58 on concorde/main-session-rebind (task-validation ready, spec-validation clean, build --check clean, full suite 829 passed / 4 skipped). Merge with the development checks.

What it does: the task record (schema_version 3) names the main agent's session (`main`), every earlier name (`mains`) and the task sessions' reports with the main agent's answers (`reports`). New commands: `concorde task report <task> --text … [--escalation n]` (task session, records before messaging, prints the `main` to message), `concorde task answer <task> --report n… --text …` (main agent), `concorde task rebind <task> --main <name>` (main agent), `concorde task wait <task> --rebound <former>` (inotify on task.json, no polling), `concorde task list --main <name>`. MCP: task_rebind, task_report, task_answer, task_list `main`, register_wait `rebound`. Guidance: task sessions record every report then SendMessage to the printed main, and on a failed send wait with `--rebound` and resend; the main agent, when ListAgents shows a new name, runs `task list --main <former>`, rebinds each, reads unanswered reports first, and records answers with `task answer`. Specs of Tasks, Task sessions and Main session, plus the glossary entries task-record and decision-log (owned by module.tasks), updated.

Decisions I took (all in the decision log): names above; reports/mains in the task record, not the trace (a trace-content change would break `task escalate` from task worktrees still on the old Concorde); a v2 record is read with mains from its session nodes; report/answer/rebind are never refused for an unfinished merge (they touch no Git; a session reports a merge_incomplete with `task report`); rebind and answer are primary-only; answers are never replaced (`already_answered`); no plan_review; no new glossary term.

Still open: (1) user documents docs/README.md and docs/using-concorde.md (root Module, outside this task) do not yet list task report/answer/rebind/wait --rebound — a small follow-up task. (2) Transitional: a task session started after the merge for a task whose branch predates it gets the new guidance but its worktree CLI lacks `task report`/`--rebound`; the MCP `task_report` works for it. (3) Once merged, you can rebind your own open tasks: `concorde task rebind <task> --main "Tasks plan review operation"`.

## Closed: merged, 2026-09-30T12:20:10Z
