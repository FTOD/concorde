# Decision log: fix-issues-module

Goal: Resolve the open non-decision Issues of module.issues

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-e52b8df822ac5f91aa84cfc8732d09a7 (module.issues, high, preferred-fix): Reconcile the caller-held-lock bypass with unfinished-merge exclusion
- I-222385f43b8650acab23bbfa11a56e3a (module.issues, medium, preferred-fix): Select the precise Spec core contracts Issues relies on
- I-7375a3de98945344b046fb28c9f6225f (module.issues, medium, preferred-fix): Specify Tasks' caller-held-lock closure entry
- I-1136a3627e545a59a2c9124aa6ed1df4 (module.issues, medium, preferred-fix): Select the Tasks contract behind unfinished-merge detection
- I-7107107984355df6b4cb695da8424c7a (module.issues, medium, obvious-fix): Declare Issues' reliance on Tracing's error contract
- I-7fdd0dc0d2e05caa9f195895089a4dec (module.issues, medium, obvious-fix): Separate combined requirements into individual obligations
- I-2370f887803255a4b48b5451191eef17 (module.issues, medium, obvious-fix): Correct the successful report scenario's repository prerequisite
- I-606348cd85165a61ade85f468789067e (module.issues, medium, obvious-fix): Bound lock release in the successful waiting scenario
- I-5fe1601cac87523b8bc09f7149f48db6 (module.issues, medium, obvious-fix): Split tier validation and compatibility into testable scenarios
- I-2477d511e763520eaf1dbc7055d7a522 (module.issues, low, suggestion): Align the lock scenario's diagnostic with the holder requirement
- I-43368318050559109cd5b465d0225965 (module.issues, low, suggestion): Clarify otherwise-valid arguments in negative disposition scenarios
- I-4e7c9ba401a758fa80df781e3c3f715f (module.issues, low, suggestion): Illustrate one Issue write and its failure exits

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

## Task session (2026-10-02)

- Worktree preparation: `init-references.py` first failed to fetch `references/sandbox-runtime`
  (network reset from github.com) yet later printed it as checked out while the submodule was
  empty at another commit; a manual `git fetch` of the pinned commit and `git submodule update`
  fixed it. The submodule is not part of any commit of this task.
- Checked every Issue of the brief against HEAD 3f370489: all twelve still stand; none closed as
  already resolved or duplicate.
- I-e52b8df8 (preferred-fix, high): chose the chair's fix, keeping the unfinished-merge check under
  a caller-held lock (`locked` now only skips taking and waiting for the merge lock), rather than
  handing that check to callers. Verified both `locked=True` callers in Tasks run with no task
  stored `merging` (`_recover_issues` after the merge's own check, `close_resolved` after the task
  is closed), so no Tasks change is needed. Code in `store._writing`, test, interface, scenario.
- I-7375a3de (preferred-fix): chose to specify the existing command library entry
  `concorde.issues.command.dispose(..., locked)` in the interface (new anchor
  `#disposing-under-a-held-lock`) and link it from the entry, rather than make Tasks call the store
  directly: Tasks already calls it and gets the command's refusal links.
- I-222385f4 (preferred-fix): added `contract.spec.error` to the Spec core `relies_on` and an
  `includes` of `document.spec.contracts` (canonical JSON, typed values, `apply_files`, which Issues
  calls directly and which are not node-identified); listing Spec core requirements instead would
  not select those library contracts.
- I-1136a362 (preferred-fix): selected `req.tasks.merging-recorded` and
  `req.tasks.merge-incomplete-refused`, the narrow promises behind the check and the
  `merge_incomplete` account, rather than the whole `contract.tasks.record`.
- I-71071079: declared `uses module.tracing` relying on `contract.tracing.error` with a
  `#uses-tracing` explanation; dropped the redundant `includes` of the Tracing contracts.
- I-7fdd0dc0: split `req.issues.report-checked` into `report-owner-registered`,
  `report-evidence-present` and `report-error-chain`; split `req.issues.merge-lock` from the new
  `req.issues.no-write-during-merge`; `req.issues.commit-alone` keeps commit isolation only.
- I-5fe1601c: split the tier scenario into five; did the same for the identically shaped severity
  scenario for consistency (same Module, same defect shape), with one test per scenario.
- I-606348cd + I-2477d511 (suggestion, cheap, taken): the waiting scenario's holder releases
  within the 300 s default; a new `scenario.issues.store-merge-busy` holds the refusal, naming the
  lock file and holder (test now writes a holder line and checks it).
- I-43368318 (suggestion, taken): one convention paragraph at the top of the scenarios.
- I-4e7c9ba4 (suggestion, taken): an illustrative d2 view of one write and its refusal exits in the
  store realization.
- I-2370f887: scenario now states a Git repository; `null` HEAD only when Git cannot name it.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T17:12:07Z

fix-issues-module delivered: delivery commit 339fb7db on concorde/fix-issues-module (work commit b5763d4c). Checked: build --check, spec-validation (no findings), full suite 904 passed / 4 skipped, task-validation ready with 13 checks and 0 warnings. No escalations.

All 12 Issues of the brief were still open at 3f370489. I fixed all 12 and added them with task resolve, so the merge closes them. None closed as already resolved or duplicate.

Preferred-fix, and the fix chosen for each:
- I-e52b8df8 (high): `locked` now skips only taking and waiting for the merge lock. A write is still refused with merge_incomplete while a task is stored merging (new req.issues.no-write-during-merge, scenario and test). I chose this over handing the check to callers. Both locked=True callers in Tasks already run when no task is merging (recovery runs after the merge's own check; close_resolved runs after the close), so no Tasks change was needed.
- I-7375a3de: specified the command library entry Tasks already calls, concorde.issues.command.dispose(..., locked), in interface.md#disposing-under-a-held-lock (arguments, attribution, return value, Refusal and its link), and linked it from the Module entry. I chose this over having Tasks call the store directly.
- I-222385f4: uses module.spec now relies on contract.spec.error, and the Module includes document.spec.contracts for canonical JSON, typed values and apply_files. Issues calls these directly and they have no node identities.
- I-1136a362: selected req.tasks.merging-recorded and req.tasks.merge-incomplete-refused, linked from #uses-tasks. These are narrower than selecting the whole contract.tasks.record.

Obvious-fix:
- I-71071079: declared uses module.tracing relying on contract.tracing.error (#uses-tracing) and dropped the redundant include.
- I-7fdd0dc0: report-checked is split into report-owner-registered, report-evidence-present and report-error-chain. merge-lock is split from no-write-during-merge. commit-alone now covers commit isolation only.
- I-2370f887: the report scenario now requires a Git repository; HEAD is null only when Git cannot name it.
- I-606348cd: the waiting scenario now has the holder release the lock within the 300 s default. The refusal is a new scenario, store-merge-busy.
- I-5fe1601c: the tier scenario is split into five, one test each. I split the severity scenario the same way, since it had the same defect.

Suggestions: I took all three because each was cheap.
- I-2477d511: store-merge-busy names the holder, and its test checks this.
- I-43368318: added an otherwise-valid-arguments convention at the top of scenarios.md.
- I-4e7c9ba4: added an illustrative d2 view of one write and its refusal exits.

New Issue: I-b879de5d (module.concorde, obvious-fix, medium). scripts/development/init-references.py leaves a half-made clone when a fetch fails, then reports it as "checked out @ <recorded commit>" while the reference is empty on another commit. It hit references/sandbox-runtime here, and I fixed it by hand; the submodule is in no commit.

Nothing is open for the developer. All decisions are in the decision log.

## Closed: merged, 2026-10-02T02:16:16Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 339fb7db237cb3d346c36ad3ba78cae14a8bd54a into main and closed it as merged. Nobody answers a report after that.
