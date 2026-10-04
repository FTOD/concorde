# Decision log: fix-open-method

Goal: Fix the open Issues of the method part (its Operations and execution commands)

## Brief (main agent, 2026-10-04)

### Context

The developer asked (2026-10-04) to try to resolve the project's open Issues, after the parts
refactor merged into `main` (decision logs of parts-*, fix-* and parts-review* in
`.concorde/decisions/`). Every open Issue was reviewed and classified then; none is high or
critical. Nine tasks run in parallel, one per part or group of parts: fix-open-spec,
fix-open-method, fix-open-execution, fix-open-coordination, fix-open-worker-harness,
fix-open-kernel, fix-open-workflows, fix-open-root-distribution, fix-open-issues-e2e.

### How to work

- Your Issues are listed below with severity and tier; read each with `concorde issues show`
  (the latest report is the verified one). Work on them most severe first.
- **obvious-fix and preferred-fix**: fix them (preferred-fix: record which fix you chose and why).
  **decision-needed**: the main agent's decisions are below; carry them out. **suggestion**: fix it
  when it is cheap and clearly improves the Spec or code; otherwise leave it open.
- After fixing an Issue, add it to this task with `concorde task resolve <task> <issue>`: the
  merge closes exactly the Issues the task resolves, so add none you did not fix. Close an Issue
  that does not hold yourself (`not-actionable`, with the reason) or as `duplicate`. If a fix needs
  a decision with major impact, or another group's files beyond a small edit, escalate it with any
  others together rather than deciding it.
- Work directly in the Specs, code and tests; no Operation or review is needed. Keep edits of files
  other groups may touch small (glossary, registry mirror, shared tests, guidance composition); on a
  merge conflict the main agent asks you to merge `main` in.
- Introduce no regression: every part still works installed with only its dependencies
  (`tests/concorde/acceptance/test_parts.py`), the part-dependency check passes, guidance reads
  correctly whichever parts are installed (`tests/concorde/distribution/test_guidance_parts.py`).
  Rapid-iteration rule: no shims or compatibility paths.
- Verify with `build --check`, `spec-validation` and the full suite, then `task-validation` and
  `delivery`, and report: resolved, closed as not holding, left open (and why).

### Decisions of the main agent for your decision-needed Issues

- I-d0783a18 (survey replay after a scaffold): revising a survey after its scaffold ran requires a fresh workspace; the brownfield workflow and the survey refuse a replay whose workspace already holds a scaffold's writes with a clear code naming that procedure, and the Specs say so. Nothing written is undone.
- I-3285d6a2 (failing commit hook's worktree edits): Delivery does not undo a hook's worktree edits, which the developer may want; narrow req.delivery.atomic and the undo message to what is restored (the index), and name the worktree files the hook changed.
- I-99d6b040 (test report failures): the Operation enforces it: its round validation checks that `failures` has exactly one entry per check that did not pass (the round validation now receives the worker result) and asks a repair otherwise; the contract says so.
- I-9ae5c4e3 (survey inventory cap): give the worker the complete inventory as a task-material file it reads, keep a summary in the brief, and keep req.adoption.inventory's promise.

### Your 47 Issues

- I-d0783a18e4cd5c98b80623a61a165ed6 (medium, decision-needed, module.method): Survey replay does not account for an earlier scaffold's writes
- I-3285d6a2f9085bdb8ba5f808316e5cf1 (medium, decision-needed, module.delivery): A failing commit hook's worktree edits stay, while Delivery says the workspace was restored
- I-285bb261e9d85e31a2b69724b0176ca4 (medium, preferred-fix, module.specification): Accepted nested document paths crash during creation
- I-49b0c36079fd5dcf8c05f1d0f0c791ed (medium, preferred-fix, module.adoption): Test-file write failures abort instead of reporting unlinked tests
- I-c8b66520d99d50f3aaaf60f2ef344452 (medium, preferred-fix, module.validation): Non-UTF-8 Git filenames crash input-digest serialization
- I-1157152150845e05a813f0bb363b1b63 (medium, preferred-fix, module.scaffold): Scaffold reports every file-transaction failure as stale_proposal with every file restored
- I-614b95e660185f73bb44dcccd89bd293 (medium, obvious-fix, module.specification): changed_documents omits the metadata files the host writes when it creates documents
- I-65081f1f1fa05bf18e3293a9fb952227 (medium, obvious-fix, module.code-review): Change-review diff treats readable paths as Git pathspecs
- I-01bf627643fa53909a5cecd789cded69 (medium, obvious-fix, module.delivery): The scenario-test gate splits Git's path output on whitespace
- I-cbf52cddfdf55d34ab86f2c3b9820315 (medium, obvious-fix, module.delivery): verify does not check the delivery commit's message, which a message hook may rewrite
- I-d9eae20f734f5343afdf69bc9b6e389b (medium, obvious-fix, module.scaffold): Scaffold narrows only the realizations declared in the parent's entry document
- I-99d6b040c8d9525fa2a0c1178d48a9e3 (low, decision-needed, module.implementation): test does not check that failures interpret exactly the failed checks
- I-9ae5c4e397a854e4b7dc4d623b901c41 (low, decision-needed, module.adoption): Survey inventory is truncated after 5,000 files
- I-58f586d8b5025141b03788cd7496f05e (low, preferred-fix, module.method): Worker-backed check evidence names the check id, not its command
- I-637bc0d535415c39a4360bc8cf85df85 (low, preferred-fix, module.understanding): plan_review answers are grouped accept-first instead of in the order given
- I-170f4020772c5e5fa335080cbd217a2c (low, preferred-fix, module.implementation): Code-change file lists misclassify a few edge cases
- I-0b41fb9fdd385cc79133245d0a3ce40e (low, preferred-fix, module.spec-review): Do not claim an earlier Issue append when reporting failed
- I-3840f31831775b51a47e0c3b7fe09a34 (low, preferred-fix, module.adoption): Open-question evidence bypasses path validation
- I-58356adab4575f82a23cdc9aa6962f96 (low, preferred-fix, module.adoption): Conditional Python test definitions cannot be linked
- I-ebade8a9e84f570c8d9af2a382252007 (low, preferred-fix, module.validation): A malformed checks file stops every selected Module's checks, not only its own
- I-01b790a76dfd59bcb693b2443a21e002 (low, preferred-fix, module.validation): A later check error drops the results of checks that already ran in the same call
- I-9e5ab1eda1a15f22896167c8eed997f1 (low, preferred-fix, module.delivery): After read-tree fails, undo skips the other parts, while the Spec and summary say they were attempted and restored
- I-f16cb9dc54f155aaad006a30c9db88f6 (low, preferred-fix, module.delivery): After a post-commit hook commits again, the trace and error name the hook's commit as the delivery commit
- I-7e9f5ccf20ee5ae58dd2e5e63eebdee9 (low, obvious-fix, module.understanding): plan_review accepts duplicate finding ids from its reviewer
- I-e9462e1bb2e75d558249b848bc96117e (low, obvious-fix, module.specification): Repeated document proposals in one batch are created twice
- I-a761737ac8305897bb5a9a8075675ef3 (low, obvious-fix, module.code-review): A change review stopping before its reviewers records path counts, not the diff's paths
- I-3bd54425ce945eb3850687eadcd3e108 (low, obvious-fix, module.spec-review): Accept chair reports that omit the optional rejection list
- I-d8351859f4d255ce8e1609eb5cba2a58 (low, obvious-fix, module.adoption): Test linking misses module-level verifies bindings
- I-1ba25d7a20fd5c4b8cbfb968f1bb5693 (low, obvious-fix, module.adoption): Survey accepts directories outside the parent's actual binding
- I-1d5615d7eb40539c805d99c1ebb98ada (low, obvious-fix, module.adoption): Repeated links in one result add duplicate decorators
- I-bd1831630f8c525f812878a9612e42a1 (low, obvious-fix, module.adoption): Test linking rewrites existing whitespace and line endings
- I-b033eaa212285e129343be5c6025ad6a (low, obvious-fix, module.validation): An OSError from Check execution ends task-validation as host_error instead of a check finding
- I-b202bd6a0a1053679b5729dddede995b (low, obvious-fix, module.validation): Gitlink digest ignores git rev-parse failure and can resolve the parent repository
- I-5e2637483954593a8980da358867399c (low, obvious-fix, module.validation): An unreadable changed file ends the run as host_error instead of measurement_failed
- I-1483cb93799f5227b76ec6a29ed7bd32 (low, obvious-fix, module.delivery): A refused update-ref is always explained as the branch no longer pointing at the commit
- I-8e90b58ab8e05d38821ee470a6aa9264 (low, obvious-fix, module.scaffold): A stale proposal's mismatches are not causes of its error
- I-fbdad9e5f3825fb69c23bfd745dac37a (low, obvious-fix, module.method): Method's status table maps from the worker result, missing a failed Workers run with an ok worker result
- I-d1797c558a4158798a799628d9e8ff7c (low, obvious-fix, module.method): Method's catalog says survey has 'Specs withheld' where only writes are withheld
- I-3e9dab61967b5c44addeed6739528553 (low, obvious-fix, module.method): scenario.method.worker-ok's premise covers only the bound Modules' checks
- I-306cc67a956559e1889b90cc181f4971 (low, obvious-fix, module.method): scenario.method.worker-backend-configured says 'a pi model' where backend comes from configuration or default
- I-22e56e1c469a5352a5499f8536f68f4c (low, suggestion, module.method): Separate run admission from the worker-step sequence terminology
- I-aef48abf03345b4fa667896f6a3bba80 (low, suggestion, module.method): Explain the brownfield delivery's adoption flag
- I-e5f20a5958d55b8ab6b14581c1645bdb (low, suggestion, module.method): Link the shared callback and work-level terminology at first use
- I-6a81c41849f9500cb9f60465242b9909 (low, suggestion, module.method): Attribute the claims/evidence rule to its canonical owner
- I-eeeca3618a6256b2ae92c7d23f121cec (low, suggestion, module.adoption): The Spec requires unsafe links when verifies is unavailable at use
- I-f1d8b66bb2c55d40807052d7fe6c5441 (low, suggestion, module.validation): Configuration digest follows a symlinked config.json instead of hashing its link text
- I-32096c560a4350f1b73eef3c2e8df5b7 (low, suggestion, module.method): Complete the launch-preparation refusal summary

## Task session (2026-10-04)

- Decision: the 47 Issues are worked in parallel by five subagents of this session in the task
  worktree, one per group of Modules with disjoint files (delivery; validation; adoption with the
  brownfield workflow, I-d0783a18 and I-aef48abf; specification with scaffold; code-review,
  spec-review, understanding and implementation), while the session itself fixes Method's own Spec
  Issues (module.md, workers.md, scenarios.md). Reason: the groups touch disjoint files and the
  Issues are independent; the session reviews every change, runs the full verification and commits.
- I-58f586d8 (preferred-fix): reworded the Spec (workers.md, module.md's Check execution) to name
  each check by its id with status, exit code and log, instead of carrying the argv into the check
  result. Reason: the check result belongs to Check execution (another part), the id identifies the
  configured command in the Module's checks file, and the check's trace node already records argv.
- I-e5f20a59 (suggestion): added the links at first use (round validation to Workers' launch.md,
  Spec tooling, Spec core, the levels of work); no new glossary concept for round validation, since
  its owner would be Workers (another task's Module) and the link already reaches its definition.
- I-22e56e1c (suggestion): admission is now described as the run-level prerequisite before the
  standard worker sequence (module.md list renumbered to four steps, glossary definition aligned).
- Specification/Scaffold (commit d2a29bb8): I-285bb261 (preferred-fix) allows nested document paths
  and links them with parent traversal, since admission already accepted them; I-e9462e1b rejects a
  path proposed twice (not deduplicated), keeping the rule that one refused proposal refuses the
  list; I-11571521 (preferred-fix) adds `write_failed` (environment), naming the files observed in
  the worktree still holding the scaffold's content, with req/scenario.scaffold.write-failed;
  stale-proposal mismatches become `proposal_mismatch` cause links.
- Validation (commit 3e199b03): I-c8b66520 (preferred-fix) records a path that is not valid UTF-8
  (or starts with `"`) in Git's quoted form with octal escapes, not as surrogate escapes, since
  every UTF-8 JSON writer downstream (traces, workflow store) would crash on lone surrogates;
  readiness contract bumped to version 8, scenario.validation.non-utf8-path added. I-ebade8a9
  needed a small change of Check execution (another part, task fix-open-execution):
  `configured_checks(worktree, modules)` and `run_checks(kinds="module")` read only the selected
  Modules' checks files (service.md one sentence). I-01b790a7 keeps the results of checks that ran
  before a later check error by reading their check trace nodes (contract.checks.check-trace), so
  Check execution's API stays unchanged. A gitlink that is no repository of its own is measured from
  the index's gitlink entry.
- Reviews/Understanding/Implementation: I-99d6b040 carried out as decided; the round validation
  already received the worker result (method/workers.py), so nothing changed there. The `test`
  Operation gives one resume round for its failures, matched by check id, and fails with the new
  `failures_unaccounted` (capability) when they still miss (req.implementation.test-failures-accounted,
  scenario.implementation.test-failures-unaccounted). I-0b41fb9f (preferred-fix) removes `earlier`
  and lists the offered Issue as carried. I-637bc0d5 (preferred-fix) keeps one ordered answers list
  via an argparse action. I-170f4020 (preferred-fix) computes the net change over the audit's
  changed paths and Workers' deletions, a dangling symlink counting as present.
- Delivery: I-3285d6a2 carried out as decided (index restored, worktree kept, every path whose mode
  or content differs from the readiness's measurement named; scenario.delivery.hook-edits-kept).
  I-cbf52cdd: verify checks the commit's subject only, not the whole message, so a commit-msg hook
  that adds a trailer (Gerrit's Change-Id) still delivers; only the subject marks a delivery.
  I-f16cb9dc (preferred-fix): the commit verified is the one `git commit` prints (core.abbrev=no),
  since Git prints it after the post-commit hook and routes hook stdout to stderr; reflog (may be
  off) and "first commit above the head" (an amending hook) were rejected. I-9e5ab1ed: the Spec and
  summary now say the rest of the undo was not attempted after read-tree failed.
- Adoption (commit 0508ba45): I-d0783a18 carried out as decided: a bound survey ends `failed` with
  `fresh_workspace_required` (scope) before any worker when the surveyed Module's entry metadata has
  a `contains` target or an `external` include its base-commit version lacks, the two additions a
  scaffold makes; chosen over run-store or workflow-record signals because it reads the workspace
  itself (a reverted scaffold no longer refuses) and ties the survey to no store layout. The
  brownfield workflow stops through the existing req.method.brownfield-stops; brownfield.md gives
  the fresh-workspace procedure. I-9ae5c4e3 carried out: `inventory.txt` in the run's trace node,
  readable by the worker, summarized in the brief. I-49b0c360 (preferred-fix): temp file plus
  os.replace, a non-writable file refused, per-file reasons. I-58356ada: the code on this branch
  already searched module-level control-flow bodies; the remaining gap (duplicate definitions
  refused without lines or a precise reason) is fixed, so it is resolved. One edit outside the
  group: a scaffold test that re-surveyed after its scaffold now surveys before it.

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:41:21Z

fix-open-method delivered: delivery commit 5c464365 on concorde/fix-open-method (verified commits 8e39ee49, d2a29bb8, 3e199b03, 5625ef71, 4eb8ae02, 0508ba45). Verification: build --check clean, spec-validation 0 errors/0 warnings, full suite 1118 passed / 5 skipped, task-validation ready, delivery ok.

Resolved (all 47, added with task resolve): every Issue of the brief. None closed as not holding, none left open. I-58356ada: the branch's code already searched module-level control-flow bodies; the remaining gap (duplicate definitions refused without lines or precise reason) is fixed, so it is resolved.

Decision-needed Issues carried out as decided: I-d0783a18 (bound survey refuses with fresh_workspace_required when the surveyed Module's entry metadata gained a contains target or external include since the base commit; brownfield.md gives the fresh-workspace procedure; nothing undone), I-3285d6a2 (index restored, worktree kept, every differing path named; req.delivery.atomic narrowed), I-99d6b040 (test's round validation checks failures one per failed check, one resume round, new code failures_unaccounted; the round validation already received the worker result, no harness change), I-9ae5c4e3 (complete inventory.txt readable by the survey worker, summary in brief).

Decisions taken on the task's behalf (all in the decision log): non-UTF-8 paths recorded in Git's quoted octal form (readiness contract v8) rather than surrogate escapes, since UTF-8 JSON writers downstream would crash; delivery verifies the commit's subject only, so a hook adding a Change-Id trailer still delivers; the commit verified is the one git commit prints (not reflog/HEAD); duplicate specify document proposals rejected not deduplicated; scaffold write failures get new code write_failed naming unrestored files; check evidence named by check id (Spec reworded) instead of carrying argv into Check execution's result.

Edits outside the method part, for merge awareness: src/concorde/execution/checks/checks.py (about 6 lines: configured_checks(worktree, modules) and run_checks kinds=module read only the selected Modules' checks files, for I-ebade8a9) and one sentence in specs/concorde/execution/checks/service.md — may conflict with fix-open-execution; specs/concorde/glossary.json (standard-worker-sequence definition); .concorde/specs.json (one relies_on line). Not changed: a stale docstring in src/concorde/worker_harness/settings.py still says the survey's grant has the Spec side withheld (worker-harness part's file).

Nothing open for the developer.

## Answer to report(s) 1 of the task session, 2026-10-04T02:41:50Z

Merge refused with merge_conflict in specs/concorde/execution/checks/service.md: fix-open-execution merged first and changed Check execution's text and code (checks.py's selective() helper, signal handling, check trace v2; it also edited method/checks.py to call checks.selective()). Merge main into concorde/fix-open-method, keep both changes (your per-Module reading of checks files and execution's helper), run build --check, spec-validation and the full suite, then task-validation and delivery again, and report.
- After the main agent's merge_conflict answer: merged main (merge 0b06734d); the conflict in
  specs/concorde/execution/checks/service.md keeps both texts (per-Module reading of checks files
  and execution's validation of every kept check before the first command). Since Check execution
  now validates every check up front, the later-check-error test fails the second check while it
  runs (an OSError) instead of through an invalid `when` (commit 56b87219). Delivered again as
  abe21679.

## Report 2 to the main agent (项目架构分离建议), 2026-10-04T02:58:54Z

fix-open-method delivered again after merging main (answer to report 1): delivery commit abe21679 on concorde/fix-open-method. Merge 0b06734d resolves the conflict in specs/concorde/execution/checks/service.md by keeping both texts: the per-Module reading of the checks files (kinds module) and execution's validation of every kept check before the first command; checks.py merged cleanly and keeps both execution's selective() helper and configured_checks(worktree, modules). One adaptation, commit 56b87219: since Check execution now validates every check before the first command, test_a_later_check_error_keeps_the_results_of_checks_that_ran makes the second check fail while it runs (an OSError) instead of through an invalid when; Validation's reading back of finished checks from their trace nodes works with check trace v2. Verification on the merged input: build --check clean, spec-validation 0 errors/0 warnings, full suite 1175 passed / 5 skipped, task-validation ready, delivery ok. Still resolves all 47 Issues; nothing open.

## Answer to report(s) 2 of the task session, 2026-10-04T02:59:18Z

Merge refused again with merge_conflict in specs/concorde/method/adoption/contracts.md and specs/concorde/method/scaffold/contracts.md: fix-open-spec, fix-open-coordination and fix-open-worker-harness merged since your last merge of main (fix-open-spec made one-line term-link edits and code spans in method documents for CHK.term.unlinked). Merge main into concorde/fix-open-method once more, keep both sides (its term links and code spans, your contract changes), run build --check, spec-validation (it must stay without CHK.term.unlinked warnings) and the full suite, then task-validation and delivery, and report. No other task is open now, so main will not move again before your merge.
- After the main agent's answer to report 2: merged main again (cf4a92e3); the conflicts in the
  adoption and scaffold contracts' error tables keep main's term links and this task's rows
  (fresh_workspace_required, the extended specs_unloadable and stale_proposal). The merged input
  had one CHK.term.unlinked warning in validation/contracts.md (this task's new paragraph), fixed by
  linking Specs (d8e62218). Delivered again as eef10f8c.

## Report 3 to the main agent (项目架构分离建议), 2026-10-04T03:15:34Z

fix-open-method delivered again after merging main (answer to report 2): delivery commit eef10f8c on concorde/fix-open-method. Merge cf4a92e3 keeps both sides in specs/concorde/method/adoption/contracts.md and scaffold/contracts.md: main's Specs term links and this task's error rows (fresh_workspace_required; specs_unloadable extended for the base-commit read; stale_proposal with proposal_mismatch causes). The merged input had one CHK.term.unlinked warning, in this task's new path-recording paragraph of validation/contracts.md, fixed by linking Specs (d8e62218). Verification on the merged input: build --check clean, spec-validation 0 errors/0 warnings, full suite 1243 passed / 5 skipped, task-validation ready, delivery ok. Still resolves all 47 Issues; nothing open.

## Closed: merged, 2026-10-04T03:15:46Z

The merge answered report(s) 3 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit eef10f8c9c6019425470a86cf21fbe5175caa9f8 into main and closed it as merged. Nobody answers a report after that.
