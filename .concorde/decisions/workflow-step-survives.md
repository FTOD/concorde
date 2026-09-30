# Decision log: workflow-step-survives

Goal: A workflow step's run must survive the step agent's Bash call inside a task session's sandbox: today the detached runner started by 'concorde workflow step --wait 100' in a foreground Bash call is killed when that call returns, so any step longer than one call is lost (step_lost / host_ended)

## Brief (main agent, 2026-10-01)

**Defect, seen in an end-to-end run** (SWE-bench psf__requests-5414, test project
/tmp/concorde-e2e/requests-5414, installed from main 9b81045d). The task session of the test
project's task `adopt` ran the `brownfield` workflow as Claude Code workflow. Its first attempt
lost the survey step: `step_lost` / `host_ended` with empty host output (workflow report 1). The
step agent runs `concorde workflow step … --wait 100` in a **foreground** Bash call; the step's
runner is a detached run, but inside the task session's sandbox (bwrap `--new-session
--die-with-parent`) it is killed when that Bash call returns, while the worker was still reading.
The task session worked around it by driving every step itself with `concorde workflow step …
--wait 3000` in background Bash. So under a task session's sandbox, no workflow step longer than
one Bash call can finish. End-to-end driver and headless runs have no such sandbox, which is why
tests never saw it. Evidence (read-only): /tmp/concorde-e2e/requests-5414/.concorde/history/adopt/decisions.md, /tmp/concorde-e2e/requests-5414/.concorde/history/adopt/workspace/workflow/reports/1.json
and 1.md, /tmp/concorde-e2e/requests-5414/.concorde/history/adopt/trace.json, and the task session transcript under /tmp/concorde-e2e/requests-5414/.concorde/history/adopt/sessions/.

**Developer's decision:** fix it. First reproduce it (a task session sandbox with a step longer
than the step agent's call) and establish the exact mechanism before choosing the fix.

**Left to you** (escalate if the choice changes what a Module promises beyond these three Modules,
or loosens a boundary): where the run's life must be anchored, for example a runner that is
started outside the Bash sandbox (the project MCP server already starts `task merge` as its own
process), the step agent using background Bash, or the sandbox letting a detached run outlive its
call. Do not loosen the session boundary's write limits. Add a test that fails without the fix.

## Task session (2026-10-01)

- **Reproduced.** In this task session's own sandbox, a scratch bound workspace (the
  `BrownfieldProject` fixture) whose `task-validation` runs a 40-second configured check: a
  foreground Bash call `concorde workflow step --json '{…"key":"validate","argv":["task-validation"]}' --wait 3`
  printed `running` for run `r-20260930T180133-task_validation-11dbd524`; the next Bash call asking
  for the same key printed `lost`, `step_lost` / `host_ended`, output "(nothing)" — the e2e defect.
- **Mechanism.** Every sandboxed Bash call of a Claude Code session runs in a PID namespace of its
  own (`/proc/self/status` NSpid; PID 1 is the sandbox's `apply-seccomp` wrapper under bwrap). When
  the call's shell ends, PID 1 exits and the kernel SIGKILLs every process of the namespace. The
  detached runner's `start_new_session` only gives it a new session and process group, which never
  leave the PID namespace, so it dies with the call, killed without a word (empty `host.out`). Probe:
  `setsid nohup sh -c 'sleep 5; touch marker' &` in one call never wrote the marker. The same holds
  for any process started from a sandboxed call; AF_UNIX sockets are refused too (seccomp), so no
  sandboxed command can hand work to a process outside. A background Bash call keeps its namespace
  until its command ends; probe: a subagent that started `sleep 40; touch marker` with
  `run_in_background` and returned at once — the marker was written 40 s later, and the subagent was
  woken again when the command ended.

## Escalated to the main agent, 2026-09-30T18:03:54Z

- **task-session** task session (task workflow-step-survives): `run_anchor_choice`
  Reproduced and explained (decision log): every sandboxed Bash call of a Claude Code session is its own PID namespace, so the detached runner that 'concorde workflow step' starts from a step agent's foreground call is SIGKILLed when the call returns; setsid cannot leave the namespace and AF_UNIX sockets are refused, so no sandboxed command can hand the run to anything outside. Only two anchors outlive the call: (A) a process outside the sandbox, i.e. the project MCP server: a new tool workflow_step(request, wait) that runs the worktree's own 'concorde workflow step --json <request> --wait 100' as its own child, so the runner it detaches lives until it ends, whatever happens to Bash calls or even the session; step agents call that tool with the request as a JSON object instead of retyping a shell command. Needs: the tool in module.main-session, each such call served on its own thread (the server now answers calls one at a time and a call waits up to 100 s), claude.js and the Workflows requirements on step agents changed, and Task sessions' Spec saying that workflow runs run outside the session's Bash sandbox, as the main agent's runs do (workers keep their grant boundary, checks their read-only check boundary). (B) background Bash, within my three Modules: the first relay of a step starts 'concorde workflow step --json <request> --hold' with run_in_background and a 2 h timeout, which starts the run and lives until it ends holding a per-step lock, then runs a foreground '--wait 100 --no-start' call and relays it; later relays only wait; a waiter finding the key unrecorded with no live holder answers a new state so the script asks the starter again. Limits of B: a two-command choreography for a haiku relay (a live run already showed one inventing an outcome around background commands), a run longer than 2 h (Claude Code's background limit) or a stopped session kills the run, and each step agent is woken again when its hold ends. Either way Execution's Spec will state that a detached run outlives its command only when the command's process namespace does.
  Not handled here (decision): Option A adds a tool to the project MCP server (module.main-session, outside this task's Modules) and moves workflow runs outside the task session's Bash sandbox, which the brief reserves for escalation; option B is within my authority but, I judge, clearly weaker, so I do not take it without asking.
  Options: A: project MCP server tool workflow_step starts and awaits steps outside the sandbox (task extended to module.main-session); B: step agents anchor each run in a background Bash call (--hold / --no-start), within the three Modules
  Recommendation: A: one structured tool call per relay (no shell quoting to mistype), no 2 h or session-life limit on a run, and it is the developer's 2026-09-29 direction that the server starts long work as detached processes; add module.main-session to the task

```json
{
  "level": "task-session",
  "actor": "task session (task workflow-step-survives)",
  "code": "run_anchor_choice",
  "detail": "Reproduced and explained (decision log): every sandboxed Bash call of a Claude Code session is its own PID namespace, so the detached runner that 'concorde workflow step' starts from a step agent's foreground call is SIGKILLed when the call returns; setsid cannot leave the namespace and AF_UNIX sockets are refused, so no sandboxed command can hand the run to anything outside. Only two anchors outlive the call: (A) a process outside the sandbox, i.e. the project MCP server: a new tool workflow_step(request, wait) that runs the worktree's own 'concorde workflow step --json <request> --wait 100' as its own child, so the runner it detaches lives until it ends, whatever happens to Bash calls or even the session; step agents call that tool with the request as a JSON object instead of retyping a shell command. Needs: the tool in module.main-session, each such call served on its own thread (the server now answers calls one at a time and a call waits up to 100 s), claude.js and the Workflows requirements on step agents changed, and Task sessions' Spec saying that workflow runs run outside the session's Bash sandbox, as the main agent's runs do (workers keep their grant boundary, checks their read-only check boundary). (B) background Bash, within my three Modules: the first relay of a step starts 'concorde workflow step --json <request> --hold' with run_in_background and a 2 h timeout, which starts the run and lives until it ends holding a per-step lock, then runs a foreground '--wait 100 --no-start' call and relays it; later relays only wait; a waiter finding the key unrecorded with no live holder answers a new state so the script asks the starter again. Limits of B: a two-command choreography for a haiku relay (a live run already showed one inventing an outcome around background commands), a run longer than 2 h (Claude Code's background limit) or a stopped session kills the run, and each step agent is woken again when its hold ends. Either way Execution's Spec will state that a detached run outlives its command only when the command's process namespace does.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Option A adds a tool to the project MCP server (module.main-session, outside this task's Modules) and moves workflow runs outside the task session's Bash sandbox, which the brief reserves for escalation; option B is within my authority but, I judge, clearly weaker, so I do not take it without asking."
  },
  "options": [
    "A: project MCP server tool workflow_step starts and awaits steps outside the sandbox (task extended to module.main-session)",
    "B: step agents anchor each run in a background Bash call (--hold / --no-start), within the three Modules"
  ],
  "recommendation": "A: one structured tool call per relay (no shell quoting to mistype), no 2 h or session-life limit on a run, and it is the developer's 2026-09-29 direction that the server starts long work as detached processes; add module.main-session to the task",
  "causes": []
}
```

## Report 1 to the main agent (Tasks plan review operation), 2026-09-30T18:04:06Z

Task workflow-step-survives: reproduced and explained; one decision needed before the fix (escalation 1).

Reproduced in this task session's own sandbox with a scratch bound workspace whose task-validation runs a 40 s check: a foreground 'concorde workflow step … --wait 3' printed running, the next call printed lost, step_lost / host_ended, output '(nothing)', the e2e defect exactly.

Mechanism: each sandboxed Bash call of a Claude Code session is its own PID namespace (PID 1 is the sandbox's apply-seccomp wrapper). When the call ends, PID 1 exits and the kernel SIGKILLs everything in the namespace; the runner's setsid (start_new_session) does not leave the namespace, hence the silent death. AF_UNIX sockets are refused too, so no sandboxed command can hand the run to a process outside. A subagent's background Bash call does keep its namespace until its command ends (probe: marker written 40 s after the subagent returned; the subagent was woken again at the end).

Escalation 1 (run_anchor_choice):
- task-session: run_anchor_choice. Where to anchor a workflow step's run. A (recommended): a project MCP server tool workflow_step that runs the worktree's own 'concorde workflow step --json <request> --wait 100' outside the sandbox, so the detached runner lives until it ends; step agents call the tool with the request object. It touches module.main-session (outside my Modules; calls served on their own threads) and moves workflow runs outside the task session's Bash sandbox, as the main agent's runs are (workers keep their grant boundary, checks their read-only check boundary). B: within my Modules, step agents anchor each run in a background Bash call ('--hold' plus foreground '--no-start' waits); weaker: a two-command choreography for a haiku relay, runs die after Claude Code's 2 h background limit or when the session stops, and each step agent is woken again when its hold ends. Either way Execution's Spec will state the namespace limit of detached runs. If A: please add module.main-session to the task.

Decisions I took: reproduced in a scratch fixture under $TMPDIR rather than in this task's own workflow record, so the task's trace holds no fake step. Nothing else is open.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-09-30T18:11:17Z

Escalation 1 (run_anchor_choice), settled by the developer: option A. Add a project MCP server tool workflow_step that runs the task worktree's own 'concorde workflow step' outside the task session's Bash sandbox, so the detached runner lives until its run ends; step agents call that tool. module.main-session is added to this task's scope (the task record's Modules cannot change after open; this answer and the decision log are the authority). The developer asks that the Specs say this clearly: (1) Execution: a detached run lives only as long as the PID namespace it was started in, and why a sandboxed Bash call's namespace ends with the call; (2) Task sessions / session boundary: that the boundary guards against mistakes, that workflow runs of a task session are started through the project MCP server outside its Bash sandbox, as the main agent's runs are, and what still bounds them (the runner works only on the bound workspace; workers keep their grant, checks their read-only check boundary), and that this rests on guidance, like task_merge and task_escalate, not on the boundary; (3) Main session: the workflow_step tool, which worktree's concorde it runs and that it refuses a worktree without a workspace binding. Keep option B's findings (background Bash keeps its namespace until its command ends) in the Spec as the rejected alternative with its reasons.

## Task session (2026-10-01), after the answer to report 1

- Answer received (main agent, the developer's choice): option A. The project MCP server gets a tool
  `workflow_step` that runs the task worktree's own `concorde workflow step` outside the task
  session's Bash sandbox; step agents call it with the request. module.main-session joins this
  task's scope by that answer (the record's Modules stay as opened). The Specs must say clearly:
  Execution, that a detached run lives only as long as the PID namespace it started in and why a
  sandboxed Bash call's namespace ends with the call; Task sessions, that workflow runs start
  through the project MCP server outside the Bash sandbox as the main agent's runs do, what still
  bounds them, and that this rests on guidance like `task_merge` and `task_escalate`; Main session,
  the tool, which worktree's `concorde` it runs, and its refusal of a worktree without a workspace
  binding; and option B kept as the rejected alternative with its reasons.
- Decision (task session): `workflow_step` takes `request` and `wait` (0–100, default 100) and no
  worktree argument: it works on the session's worktree, the Git worktree of `CLAUDE_PROJECT_DIR`
  or the server's working directory (a task worktree for a task session), so a step agent has
  nothing to find out and the tool reaches no other workspace. It runs that worktree's own
  `concorde` (`.concorde/bin/concorde`, else `scripts/concorde.py`, as `workflow step` already
  chooses) and returns the printed outcome unchanged; an object without `key` whose `error` is a
  link (e.g. `invalid_request`) is returned as the tool's refusal with that link unchanged;
  no JSON → `step_failed`. Its calls are served on threads of their own (the server answered calls
  one at a time); every other tool stays in order. Reason: least surface, errors stay whole.
- Decision (task session): the report relay stays a Bash `concorde workflow report` call: it starts
  no run and returns at once, so the sandbox does not matter to it.
- Decision (task session), consequences outside the four Modules, taken because the answer's choice
  forces them and each only follows it: Distribution's installer allows `mcp__concorde__workflow_step`
  instead of `Bash(.concorde/bin/concorde workflow step:*)` (a later install removes the recorded
  old rule as it does for every rule it no longer ships); End-to-end testing's headless run grants
  that tool and passes the project MCP server with `--mcp-config` (an untrusted project's
  `.mcp.json` entry is not loaded), and its driver's stand-in plays the tool with the command it
  runs. Their Specs (distribution/module.md, e2e/module.md, e2e/requirements.md) say so.
- Decision (task session): the task-session guidance (prompts/main-session/task-session.md, Main
  session's) now says `workflow_step` belongs to the workflows' step agents and that a task session
  runs its own runs in background Bash, never with `--detach`, since a detached run dies with the
  Bash call; the Task sessions Spec states the path rests on that guidance.
- Decision (task session): Workflows now declares `uses` module.main-session (relies on
  concept.project-mcp-server); registry refreshed.
- Tests: tests/concorde/project_mcp (a step started through the server outlives the call, the
  server and the session; other calls answered meanwhile; `unbound_worktree`, the step command's
  own refusal, `invalid_input` for wait > 100 — fails without the tool), tests/concorde/workflows
  (step agents call the tool, never Bash; a step detached inside a bwrap PID namespace is lost with
  `step_lost`/`host_ended` — the mechanism, skipped where bwrap cannot make a namespace).
- Not verified live: a real Claude Code workflow run in a task session calling the tool (no
  Workflow-tool run in this task); the e2e headless run's `--mcp-config` is unit-tested only.

## Report 2 to the main agent (Tasks plan review operation), 2026-09-30T18:36:25Z

Task workflow-step-survives delivered: delivery commit 6294e31d (run r-20260930T183016-delivery-e5994f88) on concorde/workflow-step-survives, after task-validation r-20260930T182427-task_validation-b5d37d4d ready. Option A as answered.

What changed:
- Main session: the project MCP server has workflow_step(request, wait 0-100, default 100). It runs the session's worktree's own 'concorde workflow step --json <request> --wait <wait>' as its own child, outside the Bash sandbox, so the detached runner lives until its run ends. The session's worktree is the Git worktree of CLAUDE_PROJECT_DIR, else the server's working directory. Refusals: unbound_worktree (no usable workspace binding), step_failed (no JSON), or the step command's own link unchanged. workflow_step calls are served on threads of their own. The task-session guidance says the tool belongs to the workflows' step agents, and that a task session runs its own runs in background Bash, never with --detach.
- Workflows: step agents in claude.js call mcp__concorde__workflow_step with the request as an object, never Bash; the report relay stays Bash. New requirement req.workflows.steps-through-server and scenario scenario.workflows.step-outlives-call. Workflows uses module.main-session, and the registry is refreshed. The Spec keeps option B as the rejected alternative with its reasons.
- Execution: a detached run lives only as long as the PID namespace it started in, and why a sandboxed Bash call's namespace ends with the call (scenario.execution.detached-namespace).
- Task sessions: workflow runs start through the server outside the Bash sandbox. The Spec says what still bounds them and that this rests on guidance, like task_merge and task_escalate.
- Consequences I took outside the four Modules, because the answer forces them: the installer allows mcp__concorde__workflow_step instead of 'Bash(.concorde/bin/concorde workflow step:*)'. The e2e headless run grants that tool and passes the server with --mcp-config, since an untrusted project's .mcp.json is not loaded. The e2e driver's stand-in plays the tool with the command the tool runs. The Distribution and E2E Specs say so.

Tests:
- A step started through the real stdio server outlives the call, the server and the session, and other calls are answered meanwhile. This test fails without the tool.
- The refusals are tested.
- Step agents call the tool, never Bash.
- A step detached inside a bwrap PID namespace is lost with step_lost/host_ended. This test pins the mechanism.
- Full suite: 839 passed, 4 skipped. spec-validation: 0 findings. build --check: clean.

Other decisions: reproduced in a scratch fixture, not this task's own workflow record; the tool takes no worktree argument, so it reaches only the session's own workspace. Details are in the decision log.

Open, for the developer: none blocking. Not verified live: a real Claude Code workflow run in a task session calling the tool, and the e2e headless run with --mcp-config (unit-tested only). A develop-install e2e run would confirm both. Projects take the installer's new permission rule with 'concorde update'.

## Closed: merged, 2026-09-30T18:36:43Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 6294e31d2321a59ec684f38c380e44edd2aabf43 into main and closed it as merged. Nobody answers a report after that.
