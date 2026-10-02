# Decision log: fix-main-session

Goal: Resolve the open non-decision Issues of module.main-session

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-7fe8459978195e38822bdf5ecb616013 (module.main-session, high, preferred-fix): Separate implementation-file preparation from Spec-document creation
- I-102db6242fd75d79b536d89b44bc0370 (module.main-session, high, preferred-fix): Permit Distribution's shared runtime for installed-project tasks
- I-5e92991bb60258a48b3290526e2e5396 (module.main-session, medium, preferred-fix): Distinguish the task handoff from the worker Brief
- I-9b60bbbb59ab54158daee020004ef4c6 (module.main-session, medium, preferred-fix): Assign decision-log duties to the session making the decisions
- I-80e5031a21405b9ba36d68f418178397 (module.main-session, medium, preferred-fix): Select the provider interfaces the guidance and MCP response consume
- I-090fa0ce50c95fb8b79c0b94654c1d4b (module.main-session, medium, preferred-fix): Use a permitted task-run owner in the query scenario
- I-e164c52735a95ab2a123ccc50b4ae5be (module.main-session, medium, preferred-fix): Translate Spec-tooling errors before Framework escalation
- I-2ad52d3595785800ac9df74736f7f55f (module.main-session, medium, preferred-fix): Declare the direct Spec core command dependency
- I-b4278e59cb0f52dd99655870d16a2cec (module.main-session, medium, obvious-fix): Preserve the continuing-disagreement condition in the review scenario
- I-d2481f62ae30574fb6cdd31714c962a0 (module.main-session, medium, obvious-fix): Require a Claude ancestor for automatic channel detection
- I-98046a3e1fb5522e8abddae4c570b580 (module.main-session, low, obvious-fix): Separate independent duties in compound requirements
- I-cc310e52d0365e7b9d58f8f0a3dc2ccc (module.main-session, low, obvious-fix): Define escalation batching once and illustrate the workflow case
- I-4f42e7fb7aec5f84b0b080fa861c3f86 (module.main-session, low, suggestion): Complete the command-presentation tool inventory
- I-35501f4c32f056af818df380a2a10fd4 (module.main-session, low, suggestion): Use one definition of a run's owner
- I-316cd6a688615a6ab842fb8060a0293a (module.main-session, low, suggestion): Place execution-record constraints with their canonical owner

The developer asked the main agent (2026-10-02) to resolve every Issue that does not need the
developer. This task takes the open Issues listed above, none of them decision-needed (the main
agent triages those separately). For each Issue:

1. Read it with `python3 scripts/concorde.py issues show <id>` and check that it still stands at
   your HEAD: several tasks merged on 2026-10-01/02 (issue-write-recovery, mcp-fresh-code,
   run-lock-before-records, workflow-lock-before-records, lock-recovery-followups). One already
   fixed is closed with `concorde issues close <id> --reason resolved --note … --evidence <commit>`;
   a duplicate with `--reason duplicate --duplicate-of <id>`.
2. Fix it by its tier: `obvious-fix` alone; `preferred-fix` with the fix you judge best, which
   you report; `suggestion` only when it clearly improves the Specs or code at small cost,
   otherwise leave it open and say why in your report.
3. Add every Issue you fixed to this task with `python3 scripts/concorde.py task resolve <task>
   <id>…`, so the merge closes it. Never add one you did not fix.

Rules: change only the Modules this task binds. A fix another Module needs, or a fix that turns
out to need a decision (it would change what a Module promises its users, contradict an earlier
decision of the developer, discard work, or loosen a boundary), is escalated, all together at the
end, after everything else is done; a problem you find in another Module is recorded as an Issue
of that Module. Do not touch module.workers, module.harness, module.execution, module.e2e or
module.dogfood-scenarios: task worker-git-isolation is changing them. Other tasks run in
parallel on module.issues, module.main-session, module.distribution, module.concorde and a group
of small Modules; each keeps to its own. Verify with build --check, spec-validation and the full
suite, then task-validation and delivery, and report: what you fixed (with the fix chosen for
each preferred-fix), what you closed as already resolved or duplicate, the suggestions you left
open and why, and the escalations.

## Addendum (main agent, 2026-10-02): decision-needed Issues decided by the main agent

The main agent triaged the decision-needed Issues and decided these within its authority (ordinary scope: each qualifies or documents a promise following existing decisions). Fix each with the decision given, then add it with `task resolve` like the others:

- I-458ad520e43b5386923805343c12630b (Recover answers recorded before a lost delivery): on reconciliation the main agent re-sends the latest recorded answer to each task session whose last report has an answer; a session treats an answer to a report it already acted on as a no-op, matched by report number. Guidance only, no schema change.
- I-3225882f1b8a5e168f0ab144a43f1e16 (Issue-system failure handling without a task): without a task the main agent shows the developer the whole error chain at once; the decision-log and escalation path applies only when a task exists. Add a scenario.

## Task session decisions (2026-10-02)

Every Issue of the brief and of the addendum still stood at 3f370489; none was closed as already
resolved or duplicate. All 17 are fixed in commits 125c9158 (Specs) and 6f72e888 (guidance, code,
tests) and added to the task with `task resolve`. Fixes chosen for the preferred-fix Issues:

- I-7fe84599 (Spec-document preparation): limited worker preparation and binding to new
  implementation files; the requirement, both guidance texts and the scenario now say a new Spec
  document is proposed by `specify` and created and registered in `owns` by the Operation, which
  refuses an existing path. Declared `uses module.specification` (created-documents).
- I-102db624 (shared runtime): the requirement now asks for the task worktree's own `concorde`
  command, run from the task worktree, which reads that worktree's binding, Specs, Protocol copy and
  checks; which Framework code it runs is left to Distribution (shared installed runtime, a task
  reinstall, or the branch's code in the source checkout). Entry rationale and guidance aligned.
- I-5e92991b (brief vs Brief): added glossary concept `concept.task-brief` ("Task brief"), owned by
  module.main-session, contrasted with concept.brief; renamed in entry, requirements, scenarios and
  all three guidance texts. Other Modules still say "the task's brief" unlinked, so spec-validation
  warns CHK.concept.local on it until they link it: recorded as Issues I-fb375508 (task-session),
  I-0c0fe5fb (coordination), I-9fa4c9d8 (concorde), obvious-fix/low.
- I-9b60bbbb (decision-log duties): req.decision-log now covers the main agent's own decisions;
  new req.task-session-decision-log gives the task session its failed runs and own decisions;
  ordinary-decision scenario covers both; guidance aligned.
- I-80e50318 (provider interfaces): new uses of module.understanding (plan-review contract and
  iteration requirements), module.spec-review (payload contracts, reports-issues, never-disposes,
  review verdict) and module.code-review (review contract, module scope, findings, no closing);
  Execution's selection gained contract.execution.run-result and concept.run-progress-file. I added
  Code review beside the two the Issue named, since the guidance relies on it in the same way.
- I-090fa0ce (query scenario): the second main session starts a task session, which starts the run;
  neither main session is woken; the second hears in the report, the first asks with task show.
- I-e164c527 (Spec tooling errors): entry, new req.spec-tooling-errors, new scenario and both
  guidance texts explain that Spec tooling refuses with its own error record, that `task escalate`
  refuses it with invalid_error, and how to translate it into a `component` link (fields listed,
  causes translated the same way) saved for `--error-file`.
- I-2ad52d35 (Spec core dependency): declared `uses module.spec` (structural check, registry,
  contract.spec.error, registry-mirror-only) with a `#uses-spec` section.
- Addendum I-458ad520 (main agent's decision): new reqs answers-name-reports,
  task-session-answer-once and reconcile-resend-answer; skill step 4 re-sends the latest recorded
  answer; task-session guidance ignores an answer to a report already acted on.
- Addendum I-3225882f (main agent's decision): issues-own-failures split; new
  issues-failure-no-task and scenario issue-system-failure-no-task; skill says to show the whole
  chain at once without a task, opening a task only when the failure leads to work.

Obvious-fix and suggestion Issues: I-b4278e59 (still-rejects condition, plus the accepted
maintained finding in the scenario and the task-session text), I-d2481f62 (contract, scenario,
`server.py` and its test now require a program named `claude` or `claude.exe`), I-98046a3e (the
seven compound requirements split, original ids kept for the first duty), I-cc310e52 (removed
req.workflow-pause and req.task-session-workflow-pause, which batched-decisions/answers,
answer-once and task-session-workflow-failure already cover; "workflow result" used throughout).
The three suggestions were cheap and clear, so I fixed them: I-4f42e7fb (inventory lists
task_rebind, task_report, task_answer), I-35501f4c (single-owner uses the one owner definition),
I-316cd6a6 (owner-recorded-by-coordination now obliges the guidance and server, citing Execution's
run result contract).

Verification: build --check success, spec-validation success with the one CHK.concept.local warning
above, full suite 897 passed, 4 skipped.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T17:28:13Z

fix-main-session delivered: delivery commit 3ae57b97 on concorde/fix-main-session (Specs in 125c9158; guidance, code and tests in 6f72e888). task-validation was ready: 24 checks passed, 1 warning. Full suite: 897 passed, 4 skipped. build --check and spec-validation pass.

Fixed and added with task resolve: all 17 Issues, the 15 from the brief and the 2 from the addendum. None had already been fixed or duplicated another, so none was closed. No escalations.

Fix chosen for each preferred-fix Issue:
- I-7fe84599: worker preparation now covers only new implementation files. A new Spec document is proposed by specify and created and registered in owns by the Operation. Added a uses of module.specification.
- I-102db624: a task session runs the task worktree's own concorde command from that worktree. Which Framework code it runs is left to Distribution: the shared installed runtime, a task reinstall, or the branch's code in the source checkout.
- I-5e92991b: new glossary concept concept.task-brief ("Task brief"), owned by module.main-session and contrasted with concept.brief. "Task brief" is now used across the Specs and all three guidance texts.
- I-9b60bbbb: the main agent records its own decisions. New req.task-session-decision-log gives the task session its failed runs and its own decisions. The ordinary-decision scenario now covers both.
- I-80e50318: new uses of module.understanding, module.spec-review and module.code-review, and the Execution selection now includes contract.execution.run-result and concept.run-progress-file. I added Code review beside the two the Issue named, because the guidance relies on it the same way.
- I-090fa0ce: in the scenario, the task session now starts the run, so neither main session is woken by it.
- I-e164c527: new requirement, scenario and guidance text. Each says how to turn a Spec tooling error record into a component link and pass it with --error-file.
- I-2ad52d35: declared a uses of module.spec (structural check, registry, contract.spec.error).
- Addendum I-458ad520: every answer names the reports it answers. On reconciliation the latest recorded answer is sent again (skill step 4). A task session ignores an answer to a report it already acted on.
- Addendum I-3225882f: when an Issue-system failure has no task, the main agent shows the developer the whole chain at once. Added the issue-system-failure-no-task scenario.

Obvious-fix Issues:
- I-b4278e59: the scenario keeps the "still rejects" condition. An accepted maintained finding is revised instead.
- I-d2481f62: the contract, server.py and its test now require a program named claude or claude.exe.
- I-98046a3e: the seven compound requirements are split, keeping the original ids for their first duty.
- I-cc310e52: removed workflow-pause and task-session-workflow-pause, whose duties other requirements already state. "Workflow result" is now used throughout.

Suggestions, all fixed because each was cheap and clear:
- I-4f42e7fb: the tool inventory now lists all three missing tools.
- I-35501f4c: single-owner uses the one definition of owner.
- I-316cd6a6: the owner requirement now obliges the guidance and the server.

Still open: spec-validation warns CHK.concept.local on concept.task-brief, because no other Module links the term yet. I recorded obvious-fix/low Issues for the three Modules that still write "the task's brief": I-fb375508 (module.task-session), I-0c0fe5fb (module.coordination) and I-9fa4c9d8 (module.concorde). The warning disappears once one of them links the term. The details of every decision are in the decision log.

## Closed: merged, 2026-10-02T02:17:00Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 3ae57b97a248e6f7a76c9960da314038c889429c into main and closed it as merged. Nobody answers a report after that.
