# Decision log: specmcp-workflows-high

Goal: Fix the high Issues of the Spec MCP server and Workflows (do not equate impact consumers with shared-file binders; silent-launch contracts contradict starting-step recovery) and their other obvious-fix Issues

## Task brief (main agent, 2026-10-29)

**Origin.** Project review r-20261029T060905-project_review-fa4731e2 (unbound, commit 8a5ed4245, verdict changes_required) left 2 critical and 10 high Issues open. The developer chose to fix every critical and high Issue first, in five parallel tasks split by Module, each also fixing the obvious-fix Issues of its own Modules. Read the review's findings for your Modules in `.concorde/unbound/r-20261029T060905-project_review-fa4731e2/result.json` (`output.modules[]`, the panel and code_review reviews) when an Issue's text is not enough.

**Issues this task resolves (10, all in the task's resolves):**

- I-203f283d696254cabcfff39d381b7d36 (module.spec-mcp, high, preferred-fix): Do not equate impact consumers with shared-file binders
- I-3929e4d7c6e85a9893c69dfe2fedb99a (module.workflows, high, obvious-fix): Silent-launch contracts contradict starting-step recovery
- I-6de929a94a70597abb0e8278fef53dcc (module.spec-mcp, medium, obvious-fix): Root-discovery EOF still dispatches queued requests
- I-9c87ec43579c5a828bc5cdfd10038d66 (module.spec-mcp, medium, obvious-fix): Spec MCP's planning example confuses impacted Modules with file binders
- I-dc7538b128e75fee99c68e7b60e9d44a (module.spec-mcp, medium, obvious-fix): Boundary does not validate the task_type enum before loading Specs
- I-f33e70ddcb2a579a918b9b312c61f2f9 (module.spec-mcp, medium, obvious-fix): Requests with an explicit null id are silently discarded
- I-558dfd3025d35bbd8b1b8ff43b19a0d1 (module.workflows, medium, obvious-fix): Step agent definition excludes report relays and launch allowance
- I-639c7115f18c58c1827a5c13c000036f (module.workflows, medium, obvious-fix): Workflows' brownfield scenarios consume an undeclared Method dependency
- I-6751975007a75d2aab8b70fcbe2cc749 (module.workflows, medium, obvious-fix): Validate step requests before resolving the workspace
- I-bfd209290adc51fea859a7b3fc7e1951 (module.workflows, medium, obvious-fix): Workflows leaves its reliance on Tasks' retirement protocol undeclared

**How to handle them (the main agent's decisions).**
- Critical and high first. Show each with a test that fails on the old code.
- Fix obvious-fix Issues directly. For a preferred-fix Issue, take the clearly better fix and report it. None of these Issues is decision-needed. If one turns out to need a decision beyond your Modules or beyond the Issue's evident intent, escalate it rather than guess.
- An Issue that turns out to be already fixed, not a real problem, or a duplicate of another open Issue: say so with your evidence in your report. Do not close it yourself. The main agent closes it, or the merge closes it as resolved.
- Leave the other open Issues of your Modules (preferred-fix and decision-needed medium or low) alone, unless a fix here resolves one as a side effect: then name it in your report.
- Add or change Specs first where a fix changes a promise. Keep within your Modules. Escalate a change any other Module would have to make.

**Parallel tasks.** Four other tasks run at the same time. Do not touch their Modules:
- swe-cases-critical: module.swe-bench-cases
- coordination-high: module.tasks, module.task-session
- worker-harness-high: module.harness, module.workers
- checks-execution-high: module.checks, module.execution

**Specific to this task.** The two Modules are independent. They share a task only to keep the number of parallel tasks small. Commit their fixes as separate steps.

**Verification.** Run Concorde's full suite, `build --check` and `spec-validation`. Then run `task-validation` and `delivery` from the task worktree, and report.

**Environment notes.**
- uv, node/npm (Node 24, npm 11), pi, rg, fd and d2 are under `/home/scratch.zbai_gpu/opt`.
- The system bubblewrap is 0.4.0 and works.
- Every worker runs on pi: claude-opus-5-5 and gpt-6.1-sol.
- Keep large files off `$HOME` (5 GB quota).

**Left to the session.** The mechanisms, internal structure, test design and Spec wording.

## Task session decisions (2026-10-29)

Worked directly (no Operations), as concorde-development allows when direct work is more reliable.
Every Issue below was checked against the code at the task's base before fixing; none was already
fixed, none is a duplicate of an Issue outside this task, none needed a decision.

**Spec MCP server (commit c4d63751d).**

- I-203f283d (high, preferred-fix) and I-9c87ec43 (medium, obvious-fix) are the same defect, found by
  the Spec panel and by the architecture review. One fix resolves both. Chosen fix, the one the
  Issue suggests: `module.md` "Using the server" now says `impact` names a file's binders and every
  Module that uses one of them; a user is concerned but does not share the file and need not be
  bound; only a second binder makes `boundary` refuse with `shared_file`; `module` tells which Module
  binds the file. Rejected alternative: a new `impact` field separating binders from users. That
  changes a tool result and Spec core's impact, beyond the Issue's intent and the task's Modules.
- I-6de929a9: input ending while waiting for `roots/list` now ends the session; the queued requests
  are dropped unanswered. The contract already said "the session ends"; I made explicit that the
  queued requests are never answered (contracts.md, Session) and added a BUT clause to
  `scenario.spec-mcp.roots-pending`.
- I-f33e70dd: a message is a request when its `id` member is present, `null` included. Contracts now
  say so; new scenario `scenario.spec-mcp.null-id`. Consequence: a `notifications/initialized`
  carrying an `id` is an unknown request (-32601) and resolves no root, as the contract's tables
  already imply.
- I-dc7538b1: `boundary` checks `task_type` against the enum it advertises before loading Specs.
  `scenario.spec-mcp.malformed-call` gains the unknown-task-type case, also with Specs that cannot
  load.
- Test design: the null-id test follows each null-id request with a numbered `ping`, so a regression
  fails at once instead of hanging the suite.

**Workflows (commit d03abf262).**

- I-3929e4d7 (high): Spec-only. The code (`step.py`, `LaunchUnanswered`) already leaves a silently
  launched step starting, as req.workflows.bounded-wait and scenario.workflows.launch-unanswered
  say; only contracts.md contradicted them. Fixed the `step_refused` row and the step outcome's
  `run_id`/`state` semantics. No test can fail on the old code, since no code was wrong; the
  existing launch-unanswered test covers the behaviour. I did not increment
  `contract.workflows.step`'s version (7): the behaviour and fields are unchanged, the text now
  matches the requirement it always had to meet.
- I-558dfd30: glossary `concept.step-agent` now covers both relays (one `workflow_step` call with a
  run wait of at most 100 seconds, or one `concorde workflow report`) without a hard total wait;
  module.md names the report's step agent.
- I-bfd20929, I-639c7115: added `uses` of module.tasks (relies_on req.tasks.close-when-ended,
  req.tasks.workflow-lock-last) and of module.method (relies_on concept.brownfield-workflow), each
  with a meaning paragraph saying it is reliance on a convention or procedure, not a part
  dependency. The include of `document.tasks.requirements` became redundant (spec-validation warned
  that the uses already selects it), so I removed it. The Method include of
  `document.method.brownfield` stays, since the uses does not select that document. These change
  only Workflows' own declarations; Tasks and Method are untouched.
- I-67519750: `concorde workflow step` checks its request before resolving the workspace. The
  contract now states that a malformed command line is answered before the binding is read;
  `scenario.workflows.unbound-refused` gains the BUT clause.

**Verification so far.** Each new test fails on the base code (5 tests; the null-id test now fails
in 2 s) and passes on the fix. Spec MCP and Workflows tests: 96 passed. `build --check` success.
`spec-validation` success with the 5 warnings the base already had (sentence length in Spec core's
scenarios, not these Modules).

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T09:16:20Z

specmcp-workflows-high delivered: commit dc00c4ef890e on concorde/specmcp-workflows-high (delivery run r-20261029T090642-delivery-83bbfe0a; task-validation r-20261029T085708-task_validation-dde49ba8 ready, no blocking findings). Two verified steps before it: c4d63751d (Spec MCP) and d03abf262 (Workflows).

Resolves all 10 Issues in the task's resolves. Each was real, none was already fixed or a duplicate of an Issue outside this task, none needed a decision:
- I-203f283d (high, preferred-fix) and I-9c87ec43 (medium): one defect, found twice. Chosen fix (the Issue's own): Spec MCP module.md "Using the server" now separates impact's users from file binders. A Module that only uses a binder is concerned but need not be bound. Only a second binder makes boundary refuse with shared_file. The module tool tells which Module binds the file. Rejected: a new impact field for binders, which would change a tool result and Spec core, beyond the task.
- I-3929e4d7 (high): Spec-only. The code already leaves a silently launched step starting (req.workflows.bounded-wait); only contracts.md contradicted it. Fixed the step_refused row and the step outcome's run_id/state semantics. contract.workflows.step stays version 7, since behaviour and fields are unchanged. No old-code-failing test is possible because no code was wrong; the existing launch-unanswered test covers it.
- I-6de929a9: input ending during root discovery now ends the session, and queued requests go unanswered.
- I-f33e70dd: an id member set to null now makes a request; it is answered with that null id. New scenario.spec-mcp.null-id.
- I-dc7538b1: boundary checks task_type against its enum before loading Specs.
- I-558dfd30: glossary concept.step-agent now covers both relays, a workflow_step call (run wait of at most 100 s) or a workflow report, and has no hard total wait.
- I-bfd20929, I-639c7115: Workflows now declares uses module.tasks (relies_on req.tasks.close-when-ended and req.tasks.workflow-lock-last) and uses module.method (relies_on concept.brownfield-workflow). Each is described as reliance on a convention or procedure, not a part dependency. Dropped the now-redundant include of document.tasks.requirements, which spec-validation flagged. Registry refreshed. Tasks and Method are untouched.
- I-67519750: workflow step checks its request before resolving the workspace. invalid_request now exits 2 in an unbound worktree too.

Verification: 5 new or extended tests fail on the base code and pass now. The null-id test fails fast instead of hanging. Full suite: 1663 passed, 6 skipped. build --check succeeds. spec-validation succeeds with the 5 warnings the base already had, all sentence-length warnings in Spec core's scenarios.

Side effects on other Issues: none known. Open: nothing. No escalations. The decisions are in the decision log.

## Closed: merged, 2026-10-29T09:17:00Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit dc00c4ef890e34f955aa013cda15fc528a59bf7b into main and closed it as merged. Nobody answers a report after that.
