# Decision log: e2e-main-delegates

Goal: Headless end-to-end main sessions follow the rule that the main agent never works inside a task worktree: stop granting EnterWorktree and ExitWorktree, and make a headless main session able to hand its tasks to task sessions and be woken by their reports, or report why it cannot

## 2026-09-29 — main agent: brief

Background. Task `main-delegates-tasks` (merged at cc4a4924) made it a product rule that the main
agent never works inside a task worktree: every task that is not a small change is handed to a
task session, even a single task, and a task session never asks in place but escalates every
decision it needs together. End-to-end testing was out of that task's Modules and still reflects
the old rule:

- `specs/concorde/e2e/sessions/module.md` ("What the session is told") and `scripts/e2e/sessions.py`
  (`MAIN_AGENT_TOOLS`) grant a headless Claude Code main session EnterWorktree and ExitWorktree.
- The headless notes (`NOTE`, `PI_NOTE`) and the waking logic cover Operation runs only, not a
  task session's report.

The developer asked for this cleanup. Do:

1. Remove EnterWorktree and ExitWorktree from the tools granted to a headless Claude Code main
   session, in the Spec, its requirements (`req.headless-sessions.tools-granted`) and scenarios,
   the code and the tests.
2. Check what a headless main session now needs to follow the main-session guidance. With the old
   rule it worked the task itself; with the new rule it must start a task session
   (`concorde task session <task> --main <name>`, which needs ListAgents for its session name) and
   be woken by the session's SendMessage report (Claude Code), or use `concorde_task_session` and
   be woken by the end of the round (pi, through the run view, which may already work headless).
   Establish by reading the code and the host docs, and by a real headless run where that is
   cheap, whether `claude -p` can receive a cross-session message and whether the e2e tool's
   waking covers a task session. Look at the dogfood scenarios and `run --via claude` too:
   check whether a scenario's expected outcome assumes that the main agent works the task itself.
3. Make every change that is clearly within your Modules, such as granting the tools a delegating
   main agent needs, updating the headless notes and waking a session for a task session's report.
   If headless delegation cannot work in Claude Code without a design choice (for example letting
   headless e2e sessions keep working tasks themselves as a test-only exception, or waking on
   task-session rounds), do not pick one yourself. Gather every such question, each with its
   options, evidence and your recommendation, and escalate them together in one report.

The developer set the rule; do not revisit it.

## 2026-09-29 — task session: what was done and decided

Committed on `concorde/e2e-main-delegates` as 80afc638 (build --check, spec-validation and
`tests/concorde/e2e` pass):

- **Tools.** `MAIN_AGENT_TOOLS` no longer holds EnterWorktree and ExitWorktree; it now holds
  ListAgents (the session name `concorde task session --main` needs) and SendMessage (answering a
  task session). Spec: the module text, a new `req.headless-sessions.no-worktree-tools` (split off
  `req.headless-sessions.tools-granted`, since a requirement holds one SHALL), and the `command`
  scenario, verified by `test_the_command_tells_the_session_its_conditions_and_grants_its_tools`.
  Decision: I granted ListAgents and SendMessage now, although headless Claude Code delegation
  itself is escalated below, because every option for it needs them and granting them changes
  nothing else.
- **Waking for pi session rounds.** The driver now also treats as unsettled a session round of a
  pi task session begun since the session began that its task record holds `running` under a live
  supervisor, waits for it (same one-hour limit, `wait_exceeded` names the round's
  `<task>.session/status.json`), and wakes the session with the outcome the task record holds,
  worded like the run view's `sessionText`. New `req.headless-sessions.wake-task-session`,
  scenarios `unsettled-rounds` and `wake-task-session`, with tests; Headless sessions now declares
  `uses` of module.task-session (session round, session report) and module.tasks (task record).
  Decisions: rounds that ended during the main session's round are not woken for, as for runs
  (the run view would already have steered them into that round); the wait limit stays one hour
  for rounds too, although a real task session's round may take longer, since raising it is a
  separate choice nobody asked for.
- **`run --via claude`.** Its prompt called the session "Concorde's main agent ... working inside
  the worktree of the open task", which the rule forbids. Running a task's workflow is its task
  session's work, so the prompt, the e2e Spec (headless run, `scenario.e2e.headless`) and the
  docstrings now say the session works there as the task's task session. Decision: reworded only;
  the headless workflow run still gets the workflow's own tool list, and still gets no
  task-session guidance, since it only runs one workflow.
- **pi headless note.** Now says that a session round started with `concorde_task_session` keeps
  running like a `concorde_run` run and that the tool resumes the session with its outcome.
- **Dogfood scenarios.** The Spec now says the scenario session is woken for runs and session
  rounds. The scenario `write-hook-rw-directories` expects defect reports under
  `.concorde/runs/defects/`, a classification and `src/requests/models.py` unchanged in every
  worktree: nothing there assumes the main agent works the task itself (its prompt asks for the
  change "as a task" made by the implement Operation, which a task session does). But it runs on
  `client: claude`, so it depends on the escalated question below.

Not established:

- Whether a `claude -p` session can receive a cross-session message. A probe run from inside this
  task session's sandbox (`claude -p` with haiku calling ListAgents) answered only "No reachable
  agents." with no line naming the session, but the sandbox forbids writing `~/.claude/sessions`
  and `/run/user/1000/cc-socks` and hides the other sessions (`claude agents --json` printed `[]`
  here while ListAgents in this session lists three), so the probe is confounded. Claude Code
  2.1.284's bundled code registers print-mode sessions too, so outside a sandbox a `claude -p`
  round may have a derived name while it runs. Either way its process ends with its turn.
- Whether `pi -p` with pi-subagents installed drains the session rounds `concorde_task_session`
  started before it exits (the extension registers them as background work "which the drain of a
  `pi -p` session waits for"). If it does, the pi main session is woken in-process and the new
  wake is a fallback that finds nothing; if not, the new wake covers it. No real headless pi or
  Claude Code run was made: it needs a prepared, trusted test project and real model spend, and
  `claude -p` cannot write its session state from inside this sandbox.

## Escalated to the main agent, 2026-09-29T06:03:10Z

- **task-session** task session (task e2e-main-delegates): `headless_claude_delegation`
  A headless Claude Code main session (session start --client claude, and the dogfood scenario write-hook-rw-directories, which runs on client claude) cannot hand a task to a task session and be woken by its report, and making it able to needs a design choice. (1) A claude -p round's process ends with its turn (Headless sessions, 'Testing conditions stay in the tool'), while a Claude Code task session (claude --bg, started by concorde task session <task> --main <name>) works for minutes to hours and then reports with SendMessage addressed to that name: nothing is left to deliver it to, and a resumed round is a new process. (2) Nothing in Concorde's files tells the e2e tool that a Claude Code task session has reported: its task record entry holds program, id, name, main and settings only, unlike a pi session round, whose outcome the task record holds (the driver now wakes for those, committed 80afc638). (3) A claude -p probe run inside this task session's sandbox answered ListAgents with 'No reachable agents.' and no name for itself, so it had nothing to pass to --main; the sandbox forbids ~/.claude/sessions and /run/user/1000/cc-socks, so the probe is confounded, and Claude Code 2.1.284's bundled code does register print-mode sessions, which may get a derived name while they run. Done meanwhile: EnterWorktree and ExitWorktree are no longer granted, ListAgents and SendMessage are, pi session rounds wake a headless pi session, run --via claude works as the task's task session. The dogfood scenario's expected outcome does not assume the main agent works the task itself; only its client depends on this choice.
  Not handled here (decision): Each way to make it work changes how Headless sessions drives Claude Code or makes a test-only exception to the rule the developer set, which the brief reserves for the main agent and the developer; the choice also decides whether the Claude half of the driver is redesigned in this task or another.
  Options: A: run a headless Claude Code main session as a background session (claude --bg --name <e2e name>, tools granted, auto permission mode) instead of claude -p rounds; it then receives SendMessage and is woken by its own background Bash like an interactive session, and the driver follows it through claude agents --json, claude logs and its transcript, ending it once it is idle with no task session, run or background command of its own still going. Most faithful to what users get; replaces the Claude half of the driver (log reader, rounds, headless note); unknown yet whether claude agents --json shows enough to tell 'idle with nothing pending' and how cost is read.; B: keep claude -p rounds and extend the wake to Claude Code task sessions: the driver waits until a task session recorded in a task record is idle or gone (claude agents --json), reads the SendMessage it sent from its transcript and resumes the main session with it; the main answers with SendMessage, which reaches the idle task session. The task session's own SendMessage to the ended main session fails and it must carry on anyway; relies on Claude Code's transcript format; the --main name changes every round.; C: test-only exception: headless Claude Code main sessions work tasks themselves, with EnterWorktree and ExitWorktree granted again. Contradicts the rule and step 1 of the brief, and tests a behaviour no user gets.; D: headless Claude Code main sessions do not delegate for now: Headless sessions documents that they cannot (as the Spec now says), delegation is tested headless on pi only, and the dogfood scenario write-hook-rw-directories moves to client pi until A or B exists.
  Recommendation: D now, in this task (switch the dogfood scenario to client pi, deliver), and A as its own task on module.headless-sessions, since it replaces the Claude half of the driver and needs a first probe of claude --bg outside any sandbox; B couples the tool to Claude Code's transcript format and leaves the task session's report failing, C breaks the rule.

```json
{
  "level": "task-session",
  "actor": "task session (task e2e-main-delegates)",
  "code": "headless_claude_delegation",
  "detail": "A headless Claude Code main session (session start --client claude, and the dogfood scenario write-hook-rw-directories, which runs on client claude) cannot hand a task to a task session and be woken by its report, and making it able to needs a design choice. (1) A claude -p round's process ends with its turn (Headless sessions, 'Testing conditions stay in the tool'), while a Claude Code task session (claude --bg, started by concorde task session <task> --main <name>) works for minutes to hours and then reports with SendMessage addressed to that name: nothing is left to deliver it to, and a resumed round is a new process. (2) Nothing in Concorde's files tells the e2e tool that a Claude Code task session has reported: its task record entry holds program, id, name, main and settings only, unlike a pi session round, whose outcome the task record holds (the driver now wakes for those, committed 80afc638). (3) A claude -p probe run inside this task session's sandbox answered ListAgents with 'No reachable agents.' and no name for itself, so it had nothing to pass to --main; the sandbox forbids ~/.claude/sessions and /run/user/1000/cc-socks, so the probe is confounded, and Claude Code 2.1.284's bundled code does register print-mode sessions, which may get a derived name while they run. Done meanwhile: EnterWorktree and ExitWorktree are no longer granted, ListAgents and SendMessage are, pi session rounds wake a headless pi session, run --via claude works as the task's task session. The dogfood scenario's expected outcome does not assume the main agent works the task itself; only its client depends on this choice.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Each way to make it work changes how Headless sessions drives Claude Code or makes a test-only exception to the rule the developer set, which the brief reserves for the main agent and the developer; the choice also decides whether the Claude half of the driver is redesigned in this task or another."
  },
  "options": [
    "A: run a headless Claude Code main session as a background session (claude --bg --name <e2e name>, tools granted, auto permission mode) instead of claude -p rounds; it then receives SendMessage and is woken by its own background Bash like an interactive session, and the driver follows it through claude agents --json, claude logs and its transcript, ending it once it is idle with no task session, run or background command of its own still going. Most faithful to what users get; replaces the Claude half of the driver (log reader, rounds, headless note); unknown yet whether claude agents --json shows enough to tell 'idle with nothing pending' and how cost is read.",
    "B: keep claude -p rounds and extend the wake to Claude Code task sessions: the driver waits until a task session recorded in a task record is idle or gone (claude agents --json), reads the SendMessage it sent from its transcript and resumes the main session with it; the main answers with SendMessage, which reaches the idle task session. The task session's own SendMessage to the ended main session fails and it must carry on anyway; relies on Claude Code's transcript format; the --main name changes every round.",
    "C: test-only exception: headless Claude Code main sessions work tasks themselves, with EnterWorktree and ExitWorktree granted again. Contradicts the rule and step 1 of the brief, and tests a behaviour no user gets.",
    "D: headless Claude Code main sessions do not delegate for now: Headless sessions documents that they cannot (as the Spec now says), delegation is tested headless on pi only, and the dogfood scenario write-hook-rw-directories moves to client pi until A or B exists."
  ],
  "recommendation": "D now, in this task (switch the dogfood scenario to client pi, deliver), and A as its own task on module.headless-sessions, since it replaces the Claude half of the driver and needs a first probe of claude --bg outside any sandbox; B couples the tool to Claude Code's transcript format and leaves the task session's report failing, C breaks the rule.",
  "causes": []
}
```

## 2026-09-29 — task session: delivered and escalated

task-validation ended ok (ready); delivery ended ok: 742f1f257bfd9519a2a36dde987d5b1ce34af3b4 with .concorde/evidence/e2e-main-delegates/1.json. Escalation 1 (headless_claude_delegation) recorded and sent to the main agent.

## 2026-09-29 — main agent: escalation 1 (headless_claude_delegation) goes to the developer

The task session delivered (742f1f25) and escalated whether a headless Claude Code main session can
delegate at all (options A background session, B extend the claude -p wake, C test-only exception,
D document that it cannot and move the dogfood scenario to pi; recommended D now and A as its own
task). Option C would contradict the developer's rule, and choosing D removes Claude Code from the
headless delegation tests for now, which is a change of what Headless sessions promises; so the
main agent does not decide it and puts it to the developer. The merge waits for the answer, since D
would add the scenario switch to this task first.

## 2026-09-29 — developer's answer to escalation 1: option C

The developer chose C, a test-only exception: a headless Claude Code main session of the end-to-end
tool works its tasks itself, with EnterWorktree and ExitWorktree granted again. The main agent
recommended D with A as a later task; the developer chose C over them.

## 2026-09-29 — task session: option C carried out

Committed as the commit after 742f1f25 on `concorde/e2e-main-delegates` (build --check,
spec-validation and `tests/concorde/e2e` pass):

- `MAIN_AGENT_TOOLS` grants EnterWorktree and ExitWorktree again. The Claude headless note now
  says that a task session's SendMessage report would find no receiver, since the process ends
  with each turn, and that, as an exception for this headless test only, the session starts no task
  session but carries each task out inside its task worktree (EnterWorktree with its path, work,
  validate and deliver with that worktree's own concorde, ExitWorktree after delivery, then merge
  from the primary worktree).
- The Headless sessions Spec states the exception and its reason under "The Claude Code
  exception" and "Why Claude Code works its tasks itself", scoped to headless Claude Code main
  sessions; headless pi main sessions and headless workflow runs are named as outside it.
  `req.headless-sessions.claude-works-tasks` replaces `req.headless-sessions.no-worktree-tools`;
  the `command` scenario and its test check the grant, the note and that pi's note holds no such
  exception.
- Decision: ListAgents and SendMessage are no longer granted. A headless Claude Code main session
  under the exception starts and answers no task session, so it needs neither, and granting
  SendMessage would only invite an attempt to delegate that the note forbids.
- Kept as the main agent asked: the pi session-round wake, the `run --via claude` rewording, and
  the dogfood scenario on client claude.

## 2026-09-29 — developer's clarification of option C

The developer added that the headless main session is a situation of the tests alone, so Headless
sessions may give it its own additional prompt and its own procedure, beyond the short headless
note, rather than bending the product's main-session guidance.

## 2026-09-29 — task session: the test procedure of a headless Claude Code main session

Delivery 2 after option C: 8bf73932 (evidence 2.json). Then, for the developer's clarification:

- `MAIN_PROCEDURE` in `scripts/e2e/sessions.py` states the procedure: open the task, enter its
  worktree with EnterWorktree, work it running Concorde commands in the foreground, validate and
  deliver, leave with ExitWorktree with action "keep", merge from the primary worktree, and record
  in the decision log each decision it would otherwise ask about, since nobody answers. It says it
  overrides the concorde skill's "hand every task to a task session" rule for that test session
  only. It is appended after NOTE (joined by a blank line) to every round of a headless Claude
  Code main session; NOTE keeps only the reason and points to it.
- Decision: the procedure is a constant beside NOTE, not a prompt source rendered by the build.
  The e2e tool is never installed and nothing else renders or includes it, NOTE and PI_NOTE are
  constants there already, and a build output would couple a test tool to the build for no reader
  other than the driver.
- Decision: a headless workflow run (`run --via claude`) works as the task's task session, so it
  gets NOTE alone (`procedure=None`); `scenario.e2e.headless` and its test say so.
- Spec: "The Claude Code exception" in the Headless sessions module states the procedure with its
  reason; `req.headless-sessions.claude-works-tasks` requires it and
  `req.headless-sessions.guidance-untouched` now also covers it; the `command` scenario and its
  test check that the procedure states every step in order.

## 2026-09-29 — task session: delivered again

task-validation ended ok (ready); delivery ended ok: c467a90ab75c71ac7abdb112825a2245f3b1007d with .concorde/evidence/e2e-main-delegates/3.json. Reported to the main agent.

## Closed: merged, 2026-09-29T06:14:09Z
