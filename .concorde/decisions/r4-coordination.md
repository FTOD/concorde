# Decision log: r4-coordination

Goal: Fix the critical and high open Issues of Tasks, Coordination, Task session and Main session found by the fourth project_review

## Task brief (main agent, 2026-10-17)

Round 4. The fourth project_review (r-20261013T165054-project_review-b4db00b2, unbound; reports
under `.concorde/unbound/r-20261013T165054-project_review-b4db00b2/` of the primary worktree) left
734 open Issues after rounds 1-3 had brought them to 4: most new findings are stricter standards
rather than new defects. The developer decided (2026-10-17): **each round fixes only critical and
high Issues**, medium and low wait until real use runs into them, and project_review is tuned so
its Issues stay actionable (task r4-review-tuning). This task resolves the critical and high Issues
of its Modules listed in `resolves`. Read each with `concorde issues show`. Other open Issues of
these Modules are out of scope: do not fix them unless a fix in scope needs it.

By tier: **decision-needed** — read them first and escalate them all together in one report,
early, each with what you found, the options and your recommendation, saying which options change
a promise users rely on or an earlier developer decision; continue with the rest meanwhile.
**preferred-fix** — fix as you judge best and report the choice. **obvious-fix** — fix. Critical
first. An Issue that no longer holds or is a duplicate: say so with evidence; it stays in
`resolves`. A fix needing a change outside the task's Modules: escalate unless it is a small
mechanical follow-on. Eight other round-4 tasks (r4-*) run in parallel on other Modules. Deliver
with `task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-17T04:41:02Z

- **task-session** task session (task r4-coordination): `owner_continuity_undefined`
  Issue I-73dcba12527c542093aa0dc167d4881e (decision-needed, high, module.main-session; Tasks concerned). req.main-session.session-start-compare tells the main agent to treat a task's main that is neither its current name nor a session ListAgents lists as its own former name, and req.main-session.reconcile-rebind then rebinds it. Since several main sessions may work on one project, a fresh main agent can adopt the tasks of another main agent whose session is merely absent (ended, or not listed), and two resumed sessions can race to rebind the same tasks. Found: the task record stores only names (main, mains); Concorde already reads CLAUDE_CODE_SESSION_ID for lock holder lines (Tracing contracts), so the main agent's Claude Code session id is available to every concorde command it runs. A Claude Code resume or compaction keeps the session id (assumption to confirm: a fresh session or --fork-session gets a new one).
  Not handled here (decision): Choosing how a main agent proves it is a task's former owner, and when it may adopt an absent owner's tasks, changes the reconciliation promise of Main session (req.main-session.session-start-compare, reconcile-rebind) that the main agent relies on after every restart, and adds a Tasks record field.
  Options: A: record the main agent's Claude Code session id with its name (task session --main, task rebind, from CLAUDE_CODE_SESSION_ID) in the task record; the session-start hook marks a task whose recorded id equals the starting session's id as its own; the main agent rebinds only those automatically; a task whose owner is absent and whose id differs or is missing is listed as an orphan, adopted only when the developer says so. Changes the promise and adds a record field.; B: drop automatic adoption: whenever the hook lists tasks whose main is neither the current name nor a listed session, the main agent asks the developer which of those owners it continues before rebinding any. Promise change only, no code; one developer question after every restart.; C: keep the current rule and only state its limit: correct only while one main agent works on the project at a time. No change of behaviour; leaves the risk the Issue names.
  Recommendation: A, with B's question as its fallback for tasks without a matching id. It keeps the common restart/resume/compaction path automatic and never silently takes another main agent's tasks.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-coordination)",
  "code": "owner_continuity_undefined",
  "detail": "Issue I-73dcba12527c542093aa0dc167d4881e (decision-needed, high, module.main-session; Tasks concerned). req.main-session.session-start-compare tells the main agent to treat a task's main that is neither its current name nor a session ListAgents lists as its own former name, and req.main-session.reconcile-rebind then rebinds it. Since several main sessions may work on one project, a fresh main agent can adopt the tasks of another main agent whose session is merely absent (ended, or not listed), and two resumed sessions can race to rebind the same tasks. Found: the task record stores only names (main, mains); Concorde already reads CLAUDE_CODE_SESSION_ID for lock holder lines (Tracing contracts), so the main agent's Claude Code session id is available to every concorde command it runs. A Claude Code resume or compaction keeps the session id (assumption to confirm: a fresh session or --fork-session gets a new one).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing how a main agent proves it is a task's former owner, and when it may adopt an absent owner's tasks, changes the reconciliation promise of Main session (req.main-session.session-start-compare, reconcile-rebind) that the main agent relies on after every restart, and adds a Tasks record field."
  },
  "options": [
    "A: record the main agent's Claude Code session id with its name (task session --main, task rebind, from CLAUDE_CODE_SESSION_ID) in the task record; the session-start hook marks a task whose recorded id equals the starting session's id as its own; the main agent rebinds only those automatically; a task whose owner is absent and whose id differs or is missing is listed as an orphan, adopted only when the developer says so. Changes the promise and adds a record field.",
    "B: drop automatic adoption: whenever the hook lists tasks whose main is neither the current name nor a listed session, the main agent asks the developer which of those owners it continues before rebinding any. Promise change only, no code; one developer question after every restart.",
    "C: keep the current rule and only state its limit: correct only while one main agent works on the project at a time. No change of behaviour; leaves the risk the Issue names."
  ],
  "recommendation": "A, with B's question as its fallback for tasks without a matching id. It keeps the common restart/resume/compaction path automatic and never silently takes another main agent's tasks.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:41:10Z

- **task-session** task session (task r4-coordination): `session_output_undefined`
  Issue I-d5ffbb3f9cc75cd8a4542a9dc339a558 (decision-needed, high, module.task-session; Tasks concerned). The commands table of Task session's contracts says concorde task session prints 'The recorded session' without its shape; Tasks' command row delegates back to it. Found in src/concorde/coordination/tasks/session.py start(): the command prints the dict it recorded, {"id", "reported_id", "session_id", "name", "main", "model", "settings", "started_at"} (id = reported_id = Claude Code's short identity; session_id the full id or null), with no wrapper; other task commands such as show and merge print {"record": ...} wrappers.
  Not handled here (decision): The reviewer and the brief class choosing the success shape as defining a public promise of a command the main agent reads.
  Options: A: specify the object the command prints today, field by field, with a complete example; no code change.; B: print {"record": <task record>, "session": <that object>} like the other task commands that change a record; code and test change.; C: print the session's trace node record (trace.json of sessions/<id>/), reusing contract.task-session.session-trace; code change, larger output.
  Recommendation: A: it promises what consumers already receive, and its fields (reported_id for claude stop/rm, session_id, main) are what the main agent needs.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-coordination)",
  "code": "session_output_undefined",
  "detail": "Issue I-d5ffbb3f9cc75cd8a4542a9dc339a558 (decision-needed, high, module.task-session; Tasks concerned). The commands table of Task session's contracts says concorde task session prints 'The recorded session' without its shape; Tasks' command row delegates back to it. Found in src/concorde/coordination/tasks/session.py start(): the command prints the dict it recorded, {\"id\", \"reported_id\", \"session_id\", \"name\", \"main\", \"model\", \"settings\", \"started_at\"} (id = reported_id = Claude Code's short identity; session_id the full id or null), with no wrapper; other task commands such as show and merge print {\"record\": ...} wrappers.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The reviewer and the brief class choosing the success shape as defining a public promise of a command the main agent reads."
  },
  "options": [
    "A: specify the object the command prints today, field by field, with a complete example; no code change.",
    "B: print {\"record\": <task record>, \"session\": <that object>} like the other task commands that change a record; code and test change.",
    "C: print the session's trace node record (trace.json of sessions/<id>/), reusing contract.task-session.session-trace; code change, larger output."
  ],
  "recommendation": "A: it promises what consumers already receive, and its fields (reported_id for claude stop/rm, session_id, main) are what the main agent needs.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-17T04:41:17Z

Report 1 (early, as the brief asks): the two decision-needed Issues of this task, escalations 1 and 2. I continue with the six preferred-fix Issues meanwhile.

Escalation 1 — I-73dcba12 (high, Main session/Tasks): restart reconciliation treats any absent task owner as the session's own former name, so a fresh main agent can adopt another main agent's tasks. Options: A record the main agent's Claude Code session id (CLAUDE_CODE_SESSION_ID) beside its name and rebind automatically only tasks with a matching id, asking the developer for the rest; B always ask the developer before rebinding tasks of an absent owner; C keep the rule and state it holds for one main agent at a time. Recommendation A (with B as fallback). A and B change the reconciliation promise main agents rely on after every restart; A also adds a task record field.

Escalation 2 — I-d5ffbb3f (high, Task session): the success output of concorde task session is unspecified. Options: A specify today's printed object {id, reported_id, session_id, name, main, model, settings, started_at} with an example (no code change); B wrap as {record, session}; C print the trace node record. Recommendation A. B and C change the output consumers get today.

Rendered chains: see escalations 1 and 2 in the task record (concorde task show r4-coordination).

It carries escalation(s) 1, 2.

## Answer to report(s) 1 of the task session, 2026-10-17T04:41:44Z

Escalations 1-2 (main agent): 1 A with B's fallback — record the main agent's Claude Code session id beside its name (task session --main, task rebind); the session-start hook marks as the starting session's own the tasks whose recorded id equals its CLAUDE_CODE_SESSION_ID, and the main agent rebinds only those automatically; tasks of an absent owner with another or no id are listed as orphans and adopted only when the developer says so (one question listing them all). First verify on this machine that a resume and a compaction keep CLAUDE_CODE_SESSION_ID and that a fresh session or --fork-session gets a new one; if a resume does not keep it, use B alone and say so. This refines the developer's 2026-10-08 rename-hook decision and protects other main sessions' tasks. 2 A — specify the existing output object field by field with an example.

## Task session decisions (2026-10-17)

- Escalations 1 and 2 answered by the main agent (1: A with B as fallback; 2: A).
- Verified for escalation 1 with a headless haiku probe in a scratch directory (SessionStart hook
  logging its input and environment): a fresh start gets a new id; `--resume <id>` keeps it
  (hook source `resume`); `/compact` keeps it (hook source `compact`); `--fork-session` gives a new
  id (source `fork`); hook `session_id` always equals `CLAUDE_CODE_SESSION_ID`. The docs add that
  `/clear` gives a new id. So option A stands; `/clear`, a fork and a fresh session fall to B.
- I-d93f92e4 (delivery on a branch a check selected): fixed by rechecking the task branch and its
  head after each check, before staging and after the commit (`wrong_branch`), rather than only
  re-pointing the branch, since a check that moved the head was not what the checks judged.
- I-ed7bdc1b (timed-out checks leave children): each check runs as its own process group, killed
  whole when it ends however it ends (also after a normal exit, as Checks' own executor does), and
  waited for up to 10 s; output goes to a file so a daemon holding the pipe cannot hang the check.
  Chosen over a PID namespace (Checks' approach) as the smaller change Tasks needs; `setsid`
  escapes are stated as a limit.
- I-a082885 (concurrent session starts): the whole start holds the task's existing lock rather
  than a new lock kind, so no Tracing lock table change is needed; a second start waits and is
  refused with `session_running`.
- I-dae88571 (inherited sandbox): settings set `sandbox.enabled: false`; a start refuses with
  `session_failed` when readable managed settings turn the sandbox on (rather than only stating a
  prerequisite), since a session that believes itself unsandboxed but is not fails obscurely.
- I-9f0bc89a, I-b8e522ca: Main session's design text now states the hook's exact reach and the
  limits of the merge's detection, and `uses` Validation and Delivery with their promises.
- I-d5ffbb3f (escalation 2, A): the contract now lists the printed object field by field with an
  example; a test pins the exact keys.
- I-73dcba12 (escalation 1, A with B): task record version 6 adds `main_session` and a `session`
  per `mains` entry, taken from `CLAUDE_CODE_SESSION_ID` by `task session` and `task rebind` (the
  MCP `task_rebind` uses the id its server was started with; a stale one can only make the main
  agent ask the developer, never adopt wrongly). The hook reads `session_id` from its input and
  marks tasks `(this session)`; the guidance rebinds only those and asks the developer once about
  unmarked tasks of absent owners. Records of version 5 read with null ids, so every task opened
  before this merge counts as unmarked once: the main agent's first restart after the merge asks
  the developer about them. The step `task list --main <former>` was replaced by taking the marked
  tasks (fallback when the hook fails: `task list` filtered by `main_session` against
  `$CLAUDE_CODE_SESSION_ID`).
- docs/README.md and docs/using-concorde.md (no owning Module) updated as a small mechanical
  follow-on of the reconciliation change.
- Full suite on the final input (e5d52bd10): 1597 passed, 6 skipped.
- task-validation r-20261017T050749-task_validation-0a4b1f34: blocked. Its one finding,
  check.views.repository-regressions, failed because `npm ci` in the check's scratch hit ENOSPC:
  the machine's root filesystem was full (other sessions' /tmp/concorde-check-* and other files),
  not a result of this task's change. Re-run once space is free.
- task-validation r-20261017T051413-task_validation-1cd5d903: blocked. check.views.repository-regressions
  passed this time; check.checks.runtime failed with ENOSPC in its scratch
  (`/tmp/concorde-check-*/tmp/.../project`), the root filesystem again full. Environment, not the
  change. One more attempt.
- task-validation r-20261017T052406-task_validation-39ccbee9: ok, ready.

## Report 2 to the main agent (Review流程), 2026-10-17T05:42:43Z

Report 2: r4-coordination delivered at b482aa51cf556b6fafec942b28797575e3859755 (delivery run r-20261017T053323-delivery-006cad2e; task-validation r-20261017T052406-task_validation-39ccbee9 ready; full suite on the final input 1597 passed, 6 skipped). All 8 Issues in resolves are fixed; none is a duplicate or no longer holds.

Fixes by Issue:
- I-d93f92e4 (preferred-fix): task deliver re-checks the task branch and its head after each check, before staging and after the commit; a check or hook that leaves the branch is refused with wrong_branch and nothing lands on the task branch. Chosen over silently re-pointing, since a moved head is not what the checks judged.
- I-ed7bdc1b (preferred-fix): each merge/deliver check runs as its own process group, killed whole when it ends (also after a normal exit, as Checks does) and waited for up to 10 s; output goes to a file so a daemon holding a pipe cannot hang it. Limit stated: a setsid escape is not stopped.
- I-a082885 (preferred-fix): task session holds the task's existing lock from the working-session check to the record, so two concurrent starts launch one session; the second gets session_running. No new lock kind, so Tracing's lock table is unchanged.
- I-dae88571 (preferred-fix): task-session settings set sandbox.enabled false; a start refuses with session_failed when readable managed settings turn the sandbox on (an explicit refusal rather than a stated prerequisite).
- I-9f0bc89a (preferred-fix): Main session's design text now says exactly which tools the hook restricts, that shell and MCP writes rest on the guidance, and that the merge's detection proves nothing.
- I-b8e522ca (preferred-fix): Main session uses module.validation and module.delivery with their readiness, delivery-commit and failure promises, and links them (registry rewritten).
- I-d5ffbb3f (escalation 2, A): the success output of task session is specified field by field with an example.
- I-73dcba12 (escalation 1, A with B fallback): verified first with a headless haiku probe that a resume and a compaction keep CLAUDE_CODE_SESSION_ID and that a fresh session and --fork-session get a new one (the docs add /clear). Task record version 6 keeps main_session and a session per mains entry; the session-start hook marks tasks (this session); the guidance rebinds only those and asks the developer once, in one question listing them all, about the unmarked tasks of absent owners.

Still open / for you to know:
- Every task opened before this merge has no recorded session id, so at the main agent's first restart after the merge, all of them show as unmarked and the guidance asks the developer about them once. Rebinding them records the id from then on.
- The MCP task_rebind records the session id the MCP server was started with, which Claude Code docs say may be the startup id after --continue; a stale id can only cause a developer question, never a wrong adoption.
- docs/README.md and docs/using-concorde.md (no owning Module) were updated as a small follow-on.
- Environment: the root filesystem was almost full during my run (down to 0.8-3 GB free). Two task-validation runs were blocked by ENOSPC in check scratch directories (check.views.repository-regressions, check.checks.runtime), not by this change; the third run was ready. Other r4 tasks may hit the same.
- Decisions are in the decision log.

## Closed: merged, 2026-10-23T09:01:02Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b482aa51cf556b6fafec942b28797575e3859755 into main and closed it as merged. Nobody answers a report after that.
