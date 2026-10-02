# Decision log: fix-small-modules

Goal: Resolve the open non-decision Issues of the small Modules: implementation, code-review, spec, checks, workflows, dogfooding, tasks, delivery, validation, tracing

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-96365a61a2e15588803f3ebbb04828e4 (module.delivery, high, suggestion): A commit rejected by Delivery can still be recognized as delivered
- I-9278c203c8af5346b8deb20317447831 (module.implementation, high, suggestion): Implementation incorrectly makes the durable run directory writable
- I-cdf641f04c305727a70ed67bb9a25afe (module.validation, medium, obvious-fix): Validation attributes the sandbox's placeholder files to a task session
- I-cfd8b9fd2d4c5ef7b9470bcfee830d33 (module.tracing, medium, suggestion): Remove Tracing's obsolete worktree-local Issue-lock description
- I-40babde780df548ebc3f120a9b1f0e43 (module.dogfooding, medium, suggestion): Add the required Issue tier to Dogfooding's report example
- I-4656711beb3c5617b8718ad683e34593 (module.tasks, medium, suggestion): Task-level providers retain the obsolete direct-main-agent alternative
- I-71bbe9dd98ff5a82847520615bb3b180 (module.implementation, medium, suggestion): Implementation describes a narrower code-read boundary than its providers
- I-24eb49fcb6dd5b58aea8973377e81411 (module.spec, medium, suggestion): Validation equivalence claims omit Distribution's CLI behavior
- I-f5a63d97cc4e560482741adc19aef8c0 (module.implementation, medium, suggestion): Implementation describes a narrower read grant than Workers receives
- I-26e8ebfa889f53988e457edb1aa24aa9 (module.checks, medium, suggestion): Check execution calls full-log access undecided despite consumer promises
- I-3ea49a714b575c97b3eac86e6b678bd0 (module.workflows, medium, suggestion): module.workflows has no configured check, so no task-validation runs the Workflows tests
- I-23765cae61e558529b5dfd5fe4a22f86 (module.code-review, low, suggestion): Code review and Spec review duplicate the earlier-Issue settling logic

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

## Task session decisions (2026-10-02)

- I-71bbe9dd98ff5a82847520615bb3b180 and I-f5a63d97cc4e560482741adc19aef8c0 name the same passage of
  Implementation (implement/test read only names of other code); one edit fixes both: both task
  types read ProjectImplementation, implement writes only the bound Modules' implementation scope,
  linking Spec core's Grants. Both resolved by the task rather than one closed as duplicate, since
  each was reported from a different panel and both stand fixed.
- I-9278c203c8af5346b8deb20317447831: sandboxed commands write the grant's writable files and the
  runtime directory's work/, home/, tmp/, never the run directory, linking Workers' access tables
  (launch.md); Workers itself unchanged.
- I-cdf641f04c305727a70ed67bb9a25afe (obvious-fix): Validation names a sandboxed Claude Code
  session, such as a main agent's, and says a task session runs under no sandbox; rule unchanged.
- I-cfd8b9fd2d4c5ef7b9470bcfee830d33: Tracing's Layout keeps unbound runs and their run locks as the
  worktree-local exception (as runs.py's Store places them) and says every Issue write takes the
  primary worktree's merge lock.
- I-4656711beb3c5617b8718ad683e34593: corrected Tasks (decision log, Merging, Why it is built this
  way) and Delivery (generic "whoever works in the workspace, in Concorde the task session").
  Adoption's same stale sentence is outside the task's Modules: recorded as Issue
  I-1bbc7a1b9f54586e9b656c37b901b70c (module.adoption, obvious-fix).
- I-24eb49fcb6dd5b58aea8973377e81411: Spec core's validation result now says the command adds
  Distribution's update findings and removes the mark, while validate_repository and its other
  callers do not. Spec MCP's wording is outside the task: recorded as Issue
  I-53fc26907f3b52b29765e7157746a4fd (module.spec-mcp, obvious-fix).
- I-26e8ebfa889f53988e457edb1aa24aa9: Check execution no longer calls full-log access undecided;
  Workers' bounded tail is for resume rounds, test and code_review admit full logs. The tail size
  is no longer restated in Checks (Workers' own number).
- I-3ea49a714b575c97b3eac86e6b678bd0: added .concorde/checks/module.workflows.json
  (check.workflows.tests, pytest tests/concorde/workflows, inputs incl. scripts and specs since the
  tests run scripts/concorde.py and read contracts); 44 tests pass.
- I-40babde780df548ebc3f120a9b1f0e43 closed as resolved: c5386e50 already added tier and severity
  to Dogfooding's example and explanation.
- I-23765cae61e558529b5dfd5fe4a22f86 left open: the shared helper needs module.spec-review's
  src/concorde/spec_review/reporting.py and a shared place such as module.operations, neither
  bound to this task.
- I-96365a61a2e15588803f3ebbb04828e4 escalated: any fix changes the delivery commit's recognition
  rule, which the glossary defines ("by its subject alone") and Tasks relies on — a promise change.

## Escalated to the main agent, 2026-10-01T17:05:17Z

- **task-session** task session (task fix-small-modules): `delivery_recognition_change`
  I-96365a61a2e15588803f3ebbb04828e4 (module.delivery, high, suggestion) still stands at 340b7970: when Delivery's step 9 finds the commit's tree differs from the staged tree (a pre-commit hook re-staged content), it fails with commit_unverified but leaves the commit, which carries the delivery subject and one parent. A later `delivery` then reports it as recovered (ok), and Tasks (req.tasks.delivery-verified) shows it delivered and merges it, although its content was never validated. Any fix changes how a delivery commit is recognised, which the glossary defines ("marked as the delivery of the workspace by its subject alone") and contract.delivery and req.tasks.delivery-verified promise. Options: (A) Delivery writes the staged tree and validated parent into the commit message as trailers (e.g. `Concorde-Tree: <tree>`, `Concorde-Parent: <commit>`), and a delivery commit verifies only when its tree and parent match them; recovery and Tasks check the same from Git alone, so a hook-altered commit never counts as delivered. (B) Recovery at step 2 re-runs Validation's readiness on the head before reporting it; Tasks would still accept it, so only Delivery is covered. (C) Keep the rule and document the gap as accepted (the task level must repair a commit_unverified commit before running delivery again).
  Not handled here (decision): Each option changes or explicitly narrows what Delivery and Tasks promise and the glossary's definition of a delivery commit; the brief reserves promise changes for the developer or main agent.
  Options: A: tree and parent trailers verified by Delivery recovery and Tasks; B: recovery re-validates the head (Delivery only); C: keep the rule, document the gap
  Recommendation: A: cheap, checkable from Git alone by every reader, closes the gap for Delivery and Tasks together; could be its own task binding module.delivery, module.tasks and module.concorde (glossary).

```json
{
  "level": "task-session",
  "actor": "task session (task fix-small-modules)",
  "code": "delivery_recognition_change",
  "detail": "I-96365a61a2e15588803f3ebbb04828e4 (module.delivery, high, suggestion) still stands at 340b7970: when Delivery's step 9 finds the commit's tree differs from the staged tree (a pre-commit hook re-staged content), it fails with commit_unverified but leaves the commit, which carries the delivery subject and one parent. A later `delivery` then reports it as recovered (ok), and Tasks (req.tasks.delivery-verified) shows it delivered and merges it, although its content was never validated. Any fix changes how a delivery commit is recognised, which the glossary defines (\"marked as the delivery of the workspace by its subject alone\") and contract.delivery and req.tasks.delivery-verified promise. Options: (A) Delivery writes the staged tree and validated parent into the commit message as trailers (e.g. `Concorde-Tree: <tree>`, `Concorde-Parent: <commit>`), and a delivery commit verifies only when its tree and parent match them; recovery and Tasks check the same from Git alone, so a hook-altered commit never counts as delivered. (B) Recovery at step 2 re-runs Validation's readiness on the head before reporting it; Tasks would still accept it, so only Delivery is covered. (C) Keep the rule and document the gap as accepted (the task level must repair a commit_unverified commit before running delivery again).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Each option changes or explicitly narrows what Delivery and Tasks promise and the glossary's definition of a delivery commit; the brief reserves promise changes for the developer or main agent."
  },
  "options": [
    "A: tree and parent trailers verified by Delivery recovery and Tasks",
    "B: recovery re-validates the head (Delivery only)",
    "C: keep the rule, document the gap"
  ],
  "recommendation": "A: cheap, checkable from Git alone by every reader, closes the gap for Delivery and Tasks together; could be its own task binding module.delivery, module.tasks and module.concorde (glossary).",
  "causes": []
}
```
- task-validation r-20261001T170543-task_validation-34a6b4f0 was blocked: the new
  check.workflows.tests failed in the check boundary (StepTests.test_a_step_waiting_while_its_task_closes_is_refused:
  closing a task commits its decision log, and the boundary has no global Git identity). Fixed in
  the Workflows test support: BrownfieldProject configures a repository-local identity, as
  operation_project.py already does; the affected suites pass with GIT_CONFIG_GLOBAL=/dev/null.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T17:25:19Z

fix-small-modules delivered: commit 4167a9ee (delivery run r-20261001T171853-delivery-c47d4cb7, task-validation r-20261001T171242-task_validation-1273575f ready; build --check, spec-validation and the full suite (895 passed, 4 skipped) pass).

Fixed, added to the task with task resolve (the merge closes them):
- I-71bbe9dd98ff5a82847520615bb3b180 and I-f5a63d97cc4e560482741adc19aef8c0 (Implementation, same passage): implement and test both read ProjectImplementation; implement writes only the bound Modules' implementation scope; links Spec core's Grants.
- I-9278c203c8af5346b8deb20317447831 (Implementation): sandboxed commands write the grant's rw files and the runtime directory's work/, home/, tmp/, never the run directory; links Workers' access tables.
- I-cdf641f04c305727a70ed67bb9a25afe (Validation, obvious-fix): the /dev/null placeholders are attributed to a sandboxed Claude Code session such as a main agent's; a task session runs unsandboxed; rule unchanged.
- I-cfd8b9fd2d4c5ef7b9470bcfee830d33 (Tracing): Layout's worktree-local exception is now the unbound runs and their run locks; every Issue write takes the primary worktree's merge lock.
- I-4656711beb3c5617b8718ad683e34593 (Tasks): Tasks (decision log, Merging, rationale) and Delivery now name the task session as who works in a task worktree. Adoption's identical sentence is outside the task: recorded as I-1bbc7a1b9f54586e9b656c37b901b70c (module.adoption, obvious-fix, medium).
- I-24eb49fcb6dd5b58aea8973377e81411 (Spec): Spec core's validation result says the `spec-validation` command adds Distribution's update findings and removes the mark, while validate_repository and its other callers do not. Spec MCP's wording is outside the task: recorded as I-53fc26907f3b52b29765e7157746a4fd (module.spec-mcp, obvious-fix, low).
- I-26e8ebfa889f53988e457edb1aa24aa9 (Checks): no longer calls full-log access undecided; Workers' bounded tail is for resume rounds, test and code_review admit full logs.
- I-3ea49a714b575c97b3eac86e6b678bd0 (Workflows): added .concorde/checks/module.workflows.json (check.workflows.tests). Its first run in the check boundary failed (no global Git identity for a task close's commit in the brownfield test project); fixed by a repository-local identity in tests/concorde/support/brownfield_project.py, as operation_project.py does.

Closed as already resolved: I-40babde780df548ebc3f120a9b1f0e43 (Dogfooding), fixed by c5386e50.

Left open: I-23765cae61e558529b5dfd5fe4a22f86 (code-review, low suggestion): the shared earlier-Issue helper needs module.spec-review's reporting.py and a shared home such as module.operations, neither bound to this task.

Escalation 1 (decision), I-96365a61a2e15588803f3ebbb04828e4 (module.delivery, high): a commit Delivery rejected with commit_unverified at step 9 keeps the delivery subject and one parent, so a later delivery recovers it as ok and Tasks merges it. Any fix changes the delivery commit's recognition rule (glossary, contract.delivery, req.tasks.delivery-verified). Options: A trailers recording the staged tree and validated parent, checked by Delivery recovery and Tasks from Git alone; B recovery re-validates the head (Delivery only); C keep the rule and document the gap. Recommendation: A, as its own task binding module.delivery, module.tasks and module.concorde. The rest of this task does not depend on it.

It carries escalation(s) 1.

## Closed: merged, 2026-10-02T02:16:46Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 4167a9ee70eed95e6b227bf6fb4d43680cf0caa7 into main and closed it as merged. Nobody answers a report after that.
