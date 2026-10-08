# Decision log: fix-task-session

Goal: Fix every open Issue of Task session found by the first full project_review

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) to fix the project's known open Issues. This task resolves every
open Issue owned by its Modules (listed in the task record's `resolves`), found by the first full
project_review, r-20261008T024839-project_review-a7857ff6 (unbound). Read each with
`concorde issues show`; the review's panel and code-review reports are in
`.concorde/unbound/r-20261008T024839-project_review-a7857ff6/` of the primary worktree.

How to handle them, by tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest while
  waiting. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it turns out wrong; then leave it open and say why in the log.
- Fix by **severity**, critical and high first.
- An Issue that turns out not to hold, or that is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix that needs a change outside the task's Modules: escalate it rather than widening the task,
  unless it is a small mechanical follow-on (a link, a test fixture).

Other tasks running in parallel: worker-transient-retry (workers, project-review, method),
main-rename-hook (main-session, coordination, tasks) and the other Issue-fixing tasks of today
(views, dogfood/e2e, task-session, operations/commands, delivery). Deliver with `task-validation`
then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-08T06:19:59Z

- **task-session** task session (task fix-task-session): `transcript_parse_policy`
  Issue I-17a4303c172050e2ae5b37609f925e7c (decision-needed, medium): session.py _records skips transcript lines that are not JSON objects and treats an OSError as an empty transcript; transcript_figures then writes usage as if complete, and the close removes the Claude session. The kept copy transcript.jsonl in the node holds every line byte for byte until retention removes it, so nothing is lost at removal, but after retention the node's figures carry no sign that some records were unreadable. A partial last line is a real case (a session killed mid-write). Reading the copy just written failing with OSError is a different case: the copy is not really kept.
  Not handled here (decision): Choosing whether partial figures are recorded, how incompleteness shows and whether the session is still removed changes contract.task-session.session-trace (a field and a version) and req.task-session.node-finished/removed.
  Options: A: document the current behaviour only: figures count the readable records; unreadable lines are skipped silently; the session is removed; B: skip unreadable lines but count them in the node's content (new field unreadable_lines, contract v3) and name the count in a close warning; still remove the session, since the kept copy holds every line; an OSError reading the kept copy counts as a transcript not kept (warning, session not removed); C: any unreadable line makes the figures null and the session is not removed, with a warning
  Recommendation: B: the figures stay useful, their incompleteness stays visible after retention, and removal loses nothing because the copy is verbatim

```json
{
  "level": "task-session",
  "actor": "task session (task fix-task-session)",
  "code": "transcript_parse_policy",
  "detail": "Issue I-17a4303c172050e2ae5b37609f925e7c (decision-needed, medium): session.py _records skips transcript lines that are not JSON objects and treats an OSError as an empty transcript; transcript_figures then writes usage as if complete, and the close removes the Claude session. The kept copy transcript.jsonl in the node holds every line byte for byte until retention removes it, so nothing is lost at removal, but after retention the node's figures carry no sign that some records were unreadable. A partial last line is a real case (a session killed mid-write). Reading the copy just written failing with OSError is a different case: the copy is not really kept.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing whether partial figures are recorded, how incompleteness shows and whether the session is still removed changes contract.task-session.session-trace (a field and a version) and req.task-session.node-finished/removed."
  },
  "options": [
    "A: document the current behaviour only: figures count the readable records; unreadable lines are skipped silently; the session is removed",
    "B: skip unreadable lines but count them in the node's content (new field unreadable_lines, contract v3) and name the count in a close warning; still remove the session, since the kept copy holds every line; an OSError reading the kept copy counts as a transcript not kept (warning, session not removed)",
    "C: any unreadable line makes the figures null and the session is not removed, with a warning"
  ],
  "recommendation": "B: the figures stay useful, their incompleteness stays visible after retention, and removal loses nothing because the copy is verbatim",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:20:13Z

- **task-session** task session (task fix-task-session): `repeated_session_start`
  Issue I-bccf738db20f5cafb713772936468bed (decision-needed, medium): the Spec does not say what a second 'concorde task session <task>' does. Today it always starts another 'claude --bg --name task-<task>' (Claude Code allows duplicate names; Concorde names sessions to Claude Code by reported_id), rewrites runtime/settings.json, write_hook.py and mcp.json (same task paths; MCP approvals as they stand now), records a second node sessions/<id>/ and makes the new --main the record's main. Nothing stops two sessions working in one task worktree at once, which breaks write audits and deliveries. Claude Code's 'claude agents --json --all' states seen on this machine are 'working' and 'done' (done = idle, waiting for a message).
  Not handled here (decision): The repeat policy is a promise of the session-start interface (a new refusal code or a documented duplicate start), so it changes what Task sessions promises.
  Options: A: document the current behaviour: every start starts and records another session and never reuses one; a caller retrying after an uncertain result checks 'task show' first; B: refuse with a new code session_running while 'claude agents --json --all' lists a recorded session of the task in state 'working', naming it and 'claude stop <id>'; allow a start when every recorded session is done, failed or no longer listed (so a stuck or ended session can be replaced); every started session still gets its own node and the latest --main becomes main; C: refuse whenever any recorded session of the task is still listed by Claude Code, in any state
  Recommendation: B: it prevents the real hazard (two sessions writing one worktree) while keeping a stalled or ended session replaceable without extra steps

```json
{
  "level": "task-session",
  "actor": "task session (task fix-task-session)",
  "code": "repeated_session_start",
  "detail": "Issue I-bccf738db20f5cafb713772936468bed (decision-needed, medium): the Spec does not say what a second 'concorde task session <task>' does. Today it always starts another 'claude --bg --name task-<task>' (Claude Code allows duplicate names; Concorde names sessions to Claude Code by reported_id), rewrites runtime/settings.json, write_hook.py and mcp.json (same task paths; MCP approvals as they stand now), records a second node sessions/<id>/ and makes the new --main the record's main. Nothing stops two sessions working in one task worktree at once, which breaks write audits and deliveries. Claude Code's 'claude agents --json --all' states seen on this machine are 'working' and 'done' (done = idle, waiting for a message).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The repeat policy is a promise of the session-start interface (a new refusal code or a documented duplicate start), so it changes what Task sessions promises."
  },
  "options": [
    "A: document the current behaviour: every start starts and records another session and never reuses one; a caller retrying after an uncertain result checks 'task show' first",
    "B: refuse with a new code session_running while 'claude agents --json --all' lists a recorded session of the task in state 'working', naming it and 'claude stop <id>'; allow a start when every recorded session is done, failed or no longer listed (so a stuck or ended session can be replaced); every started session still gets its own node and the latest --main becomes main",
    "C: refuse whenever any recorded session of the task is still listed by Claude Code, in any state"
  ],
  "recommendation": "B: it prevents the real hazard (two sessions writing one worktree) while keeping a stalled or ended session replaceable without extra steps",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T06:20:14Z

- **task-session** task session (task fix-task-session): `mcp_approval_authority`
  Issue I-bd492704e75651a6be8f9c8d0277193c (decision-needed, medium): req.task-session.mcp-approval and the command contract say a .mcp.json server is enabled when 'the primary worktree approved' it; module.md#project-mcp-approvals and session.py approval_sources judge every source of both worktrees (both worktrees' .claude/settings.json and settings.local.json, the user's and managed settings, and the primary worktree's entry of ~/.claude.json). Claude Code itself, for a session whose cwd is the task worktree, reads the task worktree's own project and local settings, not the primary's. The task worktree's tracked .claude/settings.json is the branch's copy of the primary's; its settings.local.json is untracked and usually absent.
  Not handled here (decision): Which worktree's approval governs a server is the approval policy that req.task-session.mcp-approval promises; aligning either side changes a promise or behaviour.
  Options: A: approvals of either worktree count (keep the code; reword the requirement, contract and scenario to 'the primary worktree or the task worktree approved', and add a scenario whose only approval is in the task worktree); B: only the primary worktree's approvals count (drop the task worktree's settings from approval_sources; keep the user's and managed settings, which apply to every worktree)
  Recommendation: A: Claude Code would itself honour the task worktree's approvals in that cwd, so disabling them would contradict what the developer approved there; the code already does this

```json
{
  "level": "task-session",
  "actor": "task session (task fix-task-session)",
  "code": "mcp_approval_authority",
  "detail": "Issue I-bd492704e75651a6be8f9c8d0277193c (decision-needed, medium): req.task-session.mcp-approval and the command contract say a .mcp.json server is enabled when 'the primary worktree approved' it; module.md#project-mcp-approvals and session.py approval_sources judge every source of both worktrees (both worktrees' .claude/settings.json and settings.local.json, the user's and managed settings, and the primary worktree's entry of ~/.claude.json). Claude Code itself, for a session whose cwd is the task worktree, reads the task worktree's own project and local settings, not the primary's. The task worktree's tracked .claude/settings.json is the branch's copy of the primary's; its settings.local.json is untracked and usually absent.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Which worktree's approval governs a server is the approval policy that req.task-session.mcp-approval promises; aligning either side changes a promise or behaviour."
  },
  "options": [
    "A: approvals of either worktree count (keep the code; reword the requirement, contract and scenario to 'the primary worktree or the task worktree approved', and add a scenario whose only approval is in the task worktree)",
    "B: only the primary worktree's approvals count (drop the task worktree's settings from approval_sources; keep the user's and managed settings, which apply to every worktree)"
  ],
  "recommendation": "A: Claude Code would itself honour the task worktree's approvals in that cwd, so disabling them would contradict what the developer approved there; the code already does this",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T06:20:22Z

Early escalation report of fix-task-session (task brief: decision-needed Issues first, together). Three decisions are needed; I continue meanwhile with the nine other Issues (obvious-fix, preferred-fix, suggestion), which do not depend on them.

- **task-session** task session (task fix-task-session): `transcript_parse_policy`
  Issue I-17a4303c172050e2ae5b37609f925e7c (decision-needed, medium): session.py _records skips transcript lines that are not JSON objects and treats an OSError as an empty transcript; transcript_figures then writes usage as if complete, and the close removes the Claude session. The kept copy transcript.jsonl in the node holds every line byte for byte until retention removes it, so nothing is lost at removal, but after retention the node's figures carry no sign that some records were unreadable. A partial last line is a real case (a session killed mid-write). Reading the copy just written failing with OSError is a different case: the copy is not really kept.
  Not handled here (decision): Choosing whether partial figures are recorded, how incompleteness shows and whether the session is still removed changes contract.task-session.session-trace (a field and a version) and req.task-session.node-finished/removed.
  Options: A: document the current behaviour only: figures count the readable records; unreadable lines are skipped silently; the session is removed; B: skip unreadable lines but count them in the node's content (new field unreadable_lines, contract v3) and name the count in a close warning; still remove the session, since the kept copy holds every line; an OSError reading the kept copy counts as a transcript not kept (warning, session not removed); C: any unreadable line makes the figures null and the session is not removed, with a warning
  Recommendation: B: the figures stay useful, their incompleteness stays visible after retention, and removal loses nothing because the copy is verbatim

- **task-session** task session (task fix-task-session): `repeated_session_start`
  Issue I-bccf738db20f5cafb713772936468bed (decision-needed, medium): the Spec does not say what a second 'concorde task session <task>' does. Today it always starts another 'claude --bg --name task-<task>' (Claude Code allows duplicate names; Concorde names sessions to Claude Code by reported_id), rewrites runtime/settings.json, write_hook.py and mcp.json (same task paths; MCP approvals as they stand now), records a second node sessions/<id>/ and makes the new --main the record's main. Nothing stops two sessions working in one task worktree at once, which breaks write audits and deliveries. Claude Code's 'claude agents --json --all' states seen on this machine are 'working' and 'done' (done = idle, waiting for a message).
  Not handled here (decision): The repeat policy is a promise of the session-start interface (a new refusal code or a documented duplicate start), so it changes what Task sessions promises.
  Options: A: document the current behaviour: every start starts and records another session and never reuses one; a caller retrying after an uncertain result checks 'task show' first; B: refuse with a new code session_running while 'claude agents --json --all' lists a recorded session of the task in state 'working', naming it and 'claude stop <id>'; allow a start when every recorded session is done, failed or no longer listed (so a stuck or ended session can be replaced); every started session still gets its own node and the latest --main becomes main; C: refuse whenever any recorded session of the task is still listed by Claude Code, in any state
  Recommendation: B: it prevents the real hazard (two sessions writing one worktree) while keeping a stalled or ended session replaceable without extra steps

- **task-session** task session (task fix-task-session): `mcp_approval_authority`
  Issue I-bd492704e75651a6be8f9c8d0277193c (decision-needed, medium): req.task-session.mcp-approval and the command contract say a .mcp.json server is enabled when 'the primary worktree approved' it; module.md#project-mcp-approvals and session.py approval_sources judge every source of both worktrees (both worktrees' .claude/settings.json and settings.local.json, the user's and managed settings, and the primary worktree's entry of ~/.claude.json). Claude Code itself, for a session whose cwd is the task worktree, reads the task worktree's own project and local settings, not the primary's. The task worktree's tracked .claude/settings.json is the branch's copy of the primary's; its settings.local.json is untracked and usually absent.
  Not handled here (decision): Which worktree's approval governs a server is the approval policy that req.task-session.mcp-approval promises; aligning either side changes a promise or behaviour.
  Options: A: approvals of either worktree count (keep the code; reword the requirement, contract and scenario to 'the primary worktree or the task worktree approved', and add a scenario whose only approval is in the task worktree); B: only the primary worktree's approvals count (drop the task worktree's settings from approval_sources; keep the user's and managed settings, which apply to every worktree)
  Recommendation: A: Claude Code would itself honour the task worktree's approvals in that cwd, so disabling them would contradict what the developer approved there; the code already does this

Answer each by escalation number (1 transcript parsing, 2 repeated starts, 3 MCP approval authority).

It carries escalation(s) 1, 2, 3.

## Answer to report(s) 1 of the task session, 2026-10-08T06:21:59Z

Escalation 1 transcript_parse_policy (main agent): B — skip unreadable lines but count them (unreadable_lines, contract v3), name the count in a close warning, still remove the session; an OSError reading the kept copy counts as a transcript not kept (warning, session not removed). Escalation 2 repeated_session_start (main agent): B — refuse with session_running while Claude Code lists a recorded session of the task as working, naming it and 'claude stop <id>'; allow a start when every recorded session is done, failed or gone; each start gets its own node and the latest --main becomes main. Escalation 3 mcp_approval_authority (developer, 2026-10-08): A — approvals of either worktree count; keep the code, reword the requirement, contract and scenario, add a scenario whose only approval is in the task worktree.

## Task session decisions (2026-10-08)

- Escalations 1-3 were answered with my recommendations (1 B, 2 B, 3 A); implemented as answered.
- I-d2d978c1 (obvious-fix, high): the code already wrote a usage object of null measurements; only
  the contract's and entry's wording changed. No contract version for this alone.
- I-c70993eb (preferred-fix, high): Tasks' contracts.md defines no promise identities, so
  `relies_on` cannot select its Commands or Record updates; chose an explicit `includes` of
  document.tasks.contracts with a reason naming both. Registry refreshed with `registry --write`.
- I-b93dc54f (obvious-fix, high): the requirement now refers to the contract's list of guarded
  tools instead of repeating a shorter one; entry and code docstrings name all four tools.
- I-ef3ccbd5 (obvious-fix): the best-effort keep is inside req.task-session.transcript-kept; the
  history prohibition is its own requirement, req.task-session.history-untouched;
  req.task-session.node-finished names when its values are unavailable.
- I-35871faf (preferred-fix): split every alternate outcome into a scenario with complete premises
  (start-failed, start-unrecorded, mcp-approve-all, mcp-unusable-file, cost-unaccounted,
  node-unlisted) rather than rewriting fixtures inside one scenario; the unusable-file scenario now
  keeps a valid file whose servers are still judged.
- I-ec868eb4 (preferred-fix): the clean-up of a failed keep returns what it could not remove and
  never raises; the warning keeps the copy's error and adds the clean-up's. Fault-injection test.
- I-07da60bc, I-87cf0e0e (preferred-fix): added tests for a saved hook after the task folder moved,
  malformed hook input, a stale cost account and a later account that restores the cost; added the
  scenario scenario.task-session.closed-log, which the contract already promised.
- I-ecd1c9f7 (suggestion): applied. The exact approval sources and name comparison moved to a new
  contracts section "Project MCP approvals"; the entry's "Finishing a session node" keeps the design
  reasons and links to the session-trace contract.
- Escalation 1 (B): the unreadable-lines warning is emitted after the task's folder moved, so it
  names the transcript's history path. A transcript or subagent transcript that cannot be read once
  copied counts as not kept.
- Escalation 2 (B): any listed state other than `done` or `failed` refuses, as the answer's "allow
  once every recorded session is done, failed or gone" says; when `claude agents --json --all`
  cannot be read and the task has a recorded session, the start is refused with `session_failed`
  (fail closed), since it cannot tell. The refusal comes before the boundary is written.
- Small mechanical follow-ons outside module.task-session, within the brief's allowance:
  store.py's registered session-trace schema (v3, `unreadable_lines`), cli.py's handling of
  `session_running` (reason `decision`) and Tasks' contracts list of `decision` codes.

## Report 2 to the main agent (Review流程), 2026-10-08T06:52:41Z

fix-task-session report 2: delivered. Delivery commit deafde07 (concorde: deliver fix-task-session) on concorde/fix-task-session, over 78f2b6cc. task-validation r-20261008T063259-task_validation-7e44fc8b ready; delivery r-20261008T064246-delivery-c3797723 ok; full suite 1327 passed, 5 skipped; spec-validation 0 errors (12 warnings, all pre-existing in other Modules).

Resolves all 12 Issues already listed in the task record (the merge closes them):
- I-b93dc54f (obvious, high): the requirement refers to the contract's four guarded tools; entry and docstrings aligned.
- I-c70993eb (preferred, high): chose an explicit includes of document.tasks.contracts (Tasks' contracts define no promise ids, so relies_on cannot select them).
- I-d2d978c1 (obvious, high): wording only; the code already wrote a usage object of null measurements.
- I-ef3ccbd5 (obvious): best-effort keep inside req.task-session.transcript-kept; new req.task-session.history-untouched; node-finished names unavailable values.
- I-35871faf (preferred): each alternate outcome is its own scenario with complete premises (start-failed, start-unrecorded, mcp-approve-all, mcp-unusable-file, cost-unaccounted, node-unlisted).
- I-ec868eb4 (preferred): the clean-up of a failed keep never raises; the warning keeps the copy's error and adds what could not be removed; fault-injection test (new scenario keep-failed).
- I-07da60bc, I-87cf0e0e (preferred): tests for a saved hook after the task folder moved (new scenario closed-log), malformed hook input, a stale cost account and a later account restoring it.
- I-ecd1c9f7 (suggestion): applied; exact approval sources and name comparison moved to a new contracts section "Project MCP approvals"; the entry keeps the design.
- I-17a4303c (your answer 1 B): session-trace contract v3 with unreadable_lines; the count is warned about (after the move, naming the history path) and the session still removed; a copy that cannot be read counts as not kept.
- I-bccf738d (your answer 2 B): new req.task-session.one-working and code session_running (reason decision); any listed state other than done/failed refuses, before the boundary is written; scenarios one-working and replace-ended.
- I-bd492704 (developer answer 3 A): requirement, contract and entry say either worktree's approval counts; new scenario mcp-task-approval.

Decisions I took (all in the decision log): when claude agents --json --all cannot be read and the task has a recorded session, the start is refused with session_failed (fail closed). Small mechanical follow-ons outside module.task-session, within the brief's allowance: store.py's registered session-trace schema (v3), cli.py's handling of session_running, and the Tasks contracts' list of decision codes (one line). These touch module.tasks files that main-rename-hook may also touch; a merge conflict there would be small.

Still open: nothing for the developer. Noted, not fixed: the not-kept warning names the node's pre-move folder under .concorde/tasks/ rather than its history path (pre-existing, low).

## Closed: merged, 2026-10-08T06:52:56Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit deafde07780e2257bce8df6f65c1ee66870c91f7 into main and closed it as merged. Nobody answers a report after that.
