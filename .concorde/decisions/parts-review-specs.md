# Decision log: parts-review-specs

Goal: Re-run the Spec panels the overall review left incomplete over the parts' top Modules and the root, verify and classify every finding as regression of the parts refactor or pre-existing, and fix every regression

## Brief (main agent, 2026-10-03)

### Context

The developer split Concorde into independently installable parts on the integration branch
`parts-split` (primary worktree on it; `main` untouched; decision logs in `.concorde/decisions/`).
The developer then decided: review the whole change, fix every regression of the refactor on
`parts-split`, re-run the Spec panels that did not complete, and fast-forward `main` once no
regression is left; pre-existing Issues wait until after the merge. Done so far: `parts-review`
(Module reviews of all 33 changed Modules' code, 49 regressions classified,
`.concorde/decisions/parts-review.md`) and four fix tasks (`fix-spec-root`,
`fix-kernel-execution`, `fix-workflow-method-issues`, `fix-coordination-distribution`), all
merged. An unbound `spec_panel` the main agent ran earlier
(`r-20261003T031022-spec_panel-14df7875`, `.concorde/unbound/` of the primary worktree) completed
only for the root: the other nine Modules' panels each lost one or two workers, to a blank
`earlier` (fixed since, I-85a1e885) or to the model gateway's `gateway_concurrency_limit` (too
many workers at once), and an incomplete panel reports nothing. Reviews now also get one resume
round for citations that do not hold (I-82b9bb29).

### What this task does

1. Prepare the worktree as usual.
2. Run `concorde run spec_panel` in this workspace over: module.concorde (re-checking the root,
   which fix-spec-root changed), module.spec-tooling, module.kernel, module.worker-harness,
   module.execution, module.workflows, module.issues, module.coordination, module.method,
   module.distribution. Use batches of about three Modules, one run at a time, to stay under the
   gateway's concurrency limit. If a panel still ends incomplete for a worker that failed, rerun
   that Module alone; if a defect of the review machinery causes it, record it as an Issue and
   say so.
3. Verify every finding against the Specs and the code, as `parts-review` did: close what does not
   hold (`not-actionable`, with the reason), merge duplicates, and correct inflated tier and
   severity. Classify each standing Issue as a regression of the parts refactor or pre-existing
   (check `main` at the matching paths; parts-layout's decision log maps old paths to new ones).
4. **Fix every regression in this task**, in Specs, and in code and tests where a Spec fix needs
   them, adding each to the task with `task resolve`. Leave pre-existing Issues open. A fix that
   needs a decision with major impact is escalated, together with any others.
5. The rules of the earlier fix tasks hold: every part must still work installed with only its
   dependencies (`tests/concorde/acceptance/test_parts.py`), the part-dependency check must pass,
   guidance must read correctly whichever parts are installed
   (`tests/concorde/distribution/test_guidance_parts.py`), no shims (rapid-iteration rule).
   Optionally, if it is a regression and quick, fix I-b4fe5ad3 (a teardown race in Execution's
   detached-run test).
6. Verify with `build --check`, `spec-validation`, the full suite, then `task-validation` and
   `delivery`, and report: regressions found and fixed, pre-existing Issues by severity, and
   anything systemic.

Model spend needs no permission; do not change the worker configuration.

## Task session (2026-10-03)

- Worktree prepared (init-references, uv sync, npm ci, build): ok.
- Panel batches, one run at a time (spec_panel runs its Modules' panels one after another, so at
  most 5 workers run at once): (1) concorde, spec-tooling, kernel; (2) worker-harness, execution,
  workflows; (3) issues, coordination, method; (4) distribution.
- I-b4fe5ad3 (detached-run test teardown race) is pre-existing: main's test has the same
  unawaited refused runner. Left open, as the brief makes it optional only for a regression.
- Run r-20261003T065334-spec_panel-d576a747 (batch 1: concorde, spec-tooling, kernel): ok,
  changes_required; 43 findings reported as Issues (root 15, spec-tooling 10, kernel 18; 27 blocking).
  Verification is delegated to subagents per Module (at most two while a panel runs), which close
  what does not hold, correct tier/severity and classify each as regression or pre-existing.
- Scratch files (findings per Module, verification prompt) live in the git-ignored
  `.generated/review/` of the worktree, since the session boundary refuses writes elsewhere.
- Verified module.concorde's 15 findings (subagent): 12 hold, all lowered to low; I-56415df0 closed
  not-actionable; I-dae2891e closed duplicate of I-a1a9a21a (Spec core's undeclared uses of the
  Kernel, left open by fix-spec-root as advisory). Regressions: I-9d93f40f, I-01f359e5, I-e0b923f2
  (mixed), I-990e4577, I-757b763a, I-b02818ae, I-989e99af, I-6821f759, I-02e786ab. Pre-existing:
  I-157f6dee, I-b26defe9, I-684059ec, I-a3522268 (suggestion).
- Verified spec-tooling's 10 findings myself: I-730f01c8 (parent declares no uses of Distribution
  although the root's req.concorde.part-dependencies names Distribution's host promises as a `uses`)
  and I-ce089a9c (grant "in a format the receiver owns" conflates Spec core's grant with Workers'
  grant input) are regressions; I-02c637e2 (init CLI file/envelope mapping, as on main) and
  I-71b30f64 (rollback exception, same sentence on main) pre-existing, both lowered to low; I-3e353c4f
  is the I-a1a9a21a reliance again; 5 suggestions (low) left as they are.
- Systemic, decided: the root's req.concorde.part-dependencies says every part meets Distribution's
  host promises through a `uses`, yet six Modules that bind a part registration declare no `uses`
  of module.distribution (spec-tooling, kernel, execution, workers, issues, method; workflows and
  tasks do). I fix all six in this task (a `uses` of module.distribution relying on
  concept.part-registration, with a short explanation), and Spec core's uses of the Kernel's formats
  and Distribution's two records, since it is the same regression of the refactor.
- Verified module.kernel's 18 findings (subagent): 17 hold, nearly all lowered to low;
  I-d204c53f closed duplicate of I-faff9296; I-03327b5f (and spec-tooling's I-3e353c4f) closed
  duplicate of I-a1a9a21a. Regressions: I-207fb96d, I-aeb88198 (main's artifact API dropped from
  the Kernel contract), I-f6dc35e3, I-6ae317da, I-83605e4b, I-646d63ee, I-a3de3982, I-b8d80520,
  I-f267e676, I-3ad142f7 (.concorde-write- prefix dropped), I-44ceded9, I-815d1a96, I-b0c321d4.
  Pre-existing: I-bbd85366, I-5d5394cc, I-6552098a (module.tasks).
- Fixing is split by files so that two sessions never edit one file: a subagent fixes the Kernel's
  regressions (specs/concorde/kernel/, glossary concept.delivery-commit, Spec core's dialect
  sentence and typed_data.py), I fix the root, spec-tooling, the uses sweep and the rest; I review
  and commit every change myself.
- Commit 417a9007 fixes the root's, Coordination's/Issues' stale sentences and Spec tooling's
  regressions; resolves I-9d93f40f, I-01f359e5, I-989e99af, I-990e4577, I-757b763a, I-b02818ae,
  I-e0b923f2, I-6821f759, I-02e786ab, I-730f01c8, I-ce089a9c, I-a1a9a21a. Decisions: the
  dependency table moved into req.concorde.part-dependencies (the root's table keeps what each part
  holds; the test reads the requirement), Distribution's host loading is stated as the one way it
  reaches the parts' code; for I-e0b923f2 the root includes Tasks' requirements and entry rather
  than dropping its restatements, since both are cited for the self-validation and boundary account.
- Commit 43b3af0b (subagent's edits, reviewed): the Kernel's 13 regressions fixed; resolves
  I-207fb96d, I-aeb88198, I-f6dc35e3, I-6ae317da, I-83605e4b, I-646d63ee, I-a3de3982, I-b8d80520,
  I-f267e676, I-3ad142f7, I-44ceded9, I-815d1a96, I-b0c321d4. Decisions: new scenario ids for the
  split outcomes, each with its own test; the Kernel's `uses` of Distribution names what its
  registration really holds (guidance, `trace`, the locks ignore line; it registers no typed types).
- Run r-20261003T072416-spec_panel-aaa8ff2a (batch 2) ended `failed` / `incomplete`: worker-harness's
  panel completed (8 findings); every worker of the execution and workflows panels ended
  `audit_violation`, because I edited and committed in the worktree while the run ran, and the
  write audit counted those changes against the read-only workers. My error, not a Concorde defect
  (the audit compares the worktree, as specified). Decision: the worktree stays frozen while any
  run of it runs; the remaining six Modules (execution, workflows, issues, coordination, method,
  distribution) panel in one run now, verification (Issue writes only) goes on meanwhile, and
  fixes wait until the run ends.
- Verified worker-harness's 8 findings (subagent, read-only while the run ran): all hold, all
  regressions of the new parent entry; 5 lowered to low (I-60b2074b to suggestion). To fix after the
  run: I-a71e053e (uses of Distribution), I-eadbeb73, I-73b9e789, I-60b2074b, I-dea96686 (also
  Workers' "something to repair" sentence), I-a7f2c8fb, I-100377fd, I-1ab8f64c. Decision: the
  suggestion-tier regressions are fixed too, since they are cheap and the brief asks for every
  regression.
- Run r-20261003T074406-spec_panel-0a7388d8 (execution, workflows, issues, coordination, method,
  distribution): ok, changes_required; 94 findings (71 blocking) reported as Issues. Every panel of
  the ten Modules has now completed. Verification is delegated to one subagent per Module.
- Commit 41bda04d fixes worker-harness's 8 regressions (also Workers' "something to repair"
  sentence, which contradicted Method's round validation); all 8 added to the task.
- Verified execution's 14 findings (subagent): 13 hold, all lowered (I-e8c62cda stays medium);
  I-01f7fdc1 closed duplicate of I-2f6e27e8. Regressions: I-e8c62cda (Execution's "registered" run
  control for Tasks does not exist: Tasks reads the run store and signals runners itself),
  I-54395394, I-30e3930d, I-57069a74 (Spec-error translation and unbound_write described in
  Execution though Method owns them); mixed: I-754f9f09, I-e0703dda, I-28d04177, I-6c7a7ad9.
  Pre-existing: I-72b32bfd, I-a6f3475b, I-1f0d13de, I-b77b34b5, I-63a5e814. Decision: a mixed
  Issue is fixed whole when its pre-existing part is the same small edit (I-e0703dda, I-28d04177);
  I-6c7a7ad9 (suggestion, text unchanged from main) is left open. Fixes delegated to a subagent.
- Verified issues' 17 findings (subagent): all hold, 10 lowered. Regressions: I-17c0aa0b (medium:
  includes of Spec core's contracts dropped with no Kernel replacement), I-a109c348, I-8fb85b29
  (medium: the store passes over an unreadable task record, where main refused the write),
  I-b8f18c9d (medium, owner dogfooding: without the spec part `issues report --check` refuses
  Dogfooding's null-owner defect report), I-a2797ef1, I-d8b715d2, I-af605255; mixed: I-f3a3937b,
  I-e678f808, I-19101098, I-b2887883. Pre-existing: I-29056133, I-a7e1faf1, I-cabec454, I-a314ad1d,
  I-d7054aed, I-93d72982.
- I-8fb85b29 reverses a decision parts-issues' task session recorded (skip an unreadable task record
  so Issues does not fail for another part); restoring main's fail-closed refusal changes what Issues
  promises during a merge, so I escalate it rather than decide. The other regressions and the mixed
  ones (whole, where the pre-existing part is the same small edit) go to a fix subagent.

## Main agent's decision (2026-10-03), before the escalation arrived

- **I-8fb85b29 (Issue store and an unreadable task record): restore main's fail-closed refusal.**
  Where the coordination part is installed (its task records exist), an Issue write that finds a
  task record it cannot read refuses, naming that record, instead of passing over it. Reason: the
  merge lock and the `merge_incomplete` check exist so that no Issue commit lands between a merge
  commit and its checks; a record that cannot be read may be the merging task's, so the safe answer
  is to refuse and say which record to repair, as `main` did. This restores pre-refactor behaviour,
  which the developer's decision to fix every regression covers; parts-issues' choice to skip such a
  record is reversed. State it in Issues' requirement and interface, with a scenario and a test.
- Verified workflows' 22 findings (subagent; I-11482e72 by me): 4 closed duplicate (I-9c0d->I-a8a1,
  I-2844->I-4ce236, I-b531->I-56b26ba, I-eddf->I-c9732), most lowered. Regressions: I-4b30, I-a8a1
  (medium: the workflow contribution interface lives only in code), I-324f, and three Method children
  lacking `uses` of Workflows' step-output contract (I-100a adoption, I-6bbc scaffold, I-5ce3
  validation), I-cbbe (adoption); mixed I-919b. Pre-existing: I-de9a, I-8105, I-7b8a, I-db4c, I-48d1,
  I-c718 (decision-needed, medium), I-32c2 (decision-needed), I-ebfe, I-85b1, I-11482 (preferred-fix,
  low: a retried step's nodes share their step key as id, same on main).
- Verified coordination's 5 and method's 12 findings (subagent): I-3595e1d4 closed not-actionable.
  Regressions: I-18d2bdd5 (optional-integrations table lacks the worker harness), I-75bcb259 and
  I-77f3788b (medium: Method's uses of Issues and Spec core select no interface/contract),
  I-81ee0141, I-b5a231b7 (suggestion), I-15a21c72, I-94cc5f00 (suggestion), I-a4c359d8 (already
  fixed by 41bda04d). Pre-existing: I-18f7b9fd, I-aa144f57, I-900476aa, I-fbdad9e5, I-d1797c55,
  I-3e9dab61, I-306cc67a, I-32096c56.
- The main agent answered I-8fb85b29 (message, 2026-10-03): restore main's fail-closed refusal of
  an Issue write that cannot read a task record; added to the Issues fix subagent's assignment.
- Verified distribution's 24 findings (subagent): 22 hold, I-229378bf and I-32e4fc9e closed duplicate
  of I-0c234cd9 (medium: moving the project MCP server to Distribution dropped main's exact session
  contract). Regressions: I-0c234cd9, I-8b0df4fc (medium), I-22287e88, I-5de4e25d, I-cc08a1a3,
  I-ec8615a5, I-a0ff01d3, I-01528bbd, I-4a41cadd, I-1fcdfa04, I-3ea0a75f (callbacks raise
  tracebacks), I-6e1b449c (owner spec); mixed: I-c355a563, I-f3adf332, I-656c7179, I-19012008,
  I-c3b5a82f. Pre-existing: I-fde7a6ca, I-d8b60e43, I-d31fff34, I-1100d67b, I-efaedb06.
- Workflows fix subagent done (uncommitted until the other fixers finish, since all share the
  registry mirror): I-4b30, I-a8a1 (new "Contributing a workflow" contract section), I-919b (also
  `req.execution.run-lock-held`/`concept.run-lock`, which step.py's lost-step judgement relies on),
  I-324f, I-100a, I-6bbc, I-5ce3, I-cbbe. Its `#uses-workflows` paragraphs say the Method children
  build their output with Workflows' `step_output` helper (they import it: method -> workflow is an
  allowed dependency). I tightened the reviews-reported test to the note's real shape and fixed
  brownfield.md's "verdict and findings" the same way. Method's own fixes made by me: I-75bcb259,
  I-77f3788b, I-b5a231b7 (new req.method.issues-absent-stated), I-94cc5f00.
- Execution fix subagent done: I-e8c62cda (run control told as records Execution promises; new
  req.execution.run-lock-held replaces runs-reported), I-754f9f09 (runner.md "What a definition
  gives the runner"), I-54395394, I-30e3930d, I-e0703dda (requirements split; old ids kept where
  linked), I-57069a74 (Spec-error translation and `unbound_write` moved to Method:
  scenario.method.unbound-write), I-28d04177 (four new scenarios with tests).
- It found that an unexpected exception of a definition's admission or runtime-path resolver left a
  run with no result, against req.execution.one-result (new with the refactor's admission
  callback). Recorded as I-028e614e (obvious-fix, medium, regression) and fixed in runner.py: such
  an exception is a `failed` result with `host-error` evidence, as a step's (new
  scenario.execution.admission-error with a test).
- Issues fix subagent done: all 10 plus I-8fb85b29 (new environment code `unreadable_task_record`;
  fail closed where `.concorde/tasks/` exists). Method's last two fixed by me: I-81ee0141 (diagram
  edges through step 9), I-15a21c72 (new scenario.method.glossary-deletion-proposed).
- Distribution fix subagent done: all 17 regressions/mixed fixed (new project MCP server contract
  section, build-manifest contract, `part_failed` for failing idle_check/after_update callbacks).
  It noted main's session contract gave workflow_step calls wait+120 s while the code gives every
  call 300 s: main's code had the same 300 s, so the mismatch is pre-existing; the Spec now states
  the code's 300 s.
- Commits 49b28acc (Execution), 7007edc3 (Issues; its message lost the word "`--check`" to shell
  substitution, left since task sessions never rebase), c056630e (Workflows, Method), 97929ff8
  (Distribution). The 50 Issues they fix added to the task (85 in all).
- Full suite (pytest -n auto): 1081 passed, 1 failed, 5 skipped. The failure,
  tests/concorde/e2e/test_owners.py::test_a_run_refused_for_a_busy_workspace_stops_the_case_with_an_error
  (refusal reported in phase owned-by-claude instead of unowned), is the known flake I-566e82f1
  (fake concorde, code this task did not touch); the file passes alone. Rerunning the suite twice.
- Suite reruns: 1082 passed, 5 skipped, twice.
- task-validation: ok, ready, no blocking findings.
- Delivered as 2ba0f29d. Then, classifying spec-tooling's five suggestions for the report:
  I-78b3560a, I-9f262a85, I-3617d25e are pre-existing (same text on main); I-d2d4c645 and
  I-613177e9 concern the new Part entries text, so they are regressions: fixed in a commit after the
  delivery and added to the task, which is validated and delivered again.

## Report 1 to the main agent (项目架构分离建议), 2026-10-03T09:35:05Z

parts-review-specs delivered: delivery commit 6b2824c8 on concorde/parts-review-specs (an earlier delivery 2ba0f29d was followed by one more fix, then validated and delivered again). Verified: build --check, spec-validation (0 findings), full suite 1082 passed / 5 skipped (one run hit the known flake I-566e82f1 in tests/concorde/e2e/test_owners.py; two reruns green), part-dependency and parts acceptance tests, task-validation ready.

PANELS. All ten Modules' spec_panels completed in this workspace: r-20261003T065334-spec_panel-d576a747 (concorde, spec-tooling, kernel), r-20261003T072416-spec_panel-aaa8ff2a (worker-harness completed; execution and workflows ended audit_violation because I edited the worktree while it ran — my error, not a Concorde defect: the write audit attributes every worktree change to the run's workers, as specified), r-20261003T074406-spec_panel-0a7388d8 (execution, workflows, issues, coordination, method, distribution). 145 findings, every one verified against Specs, code and main (merge-base 5df929ef) by me or a verification subagent; about 12 closed duplicate/not-actionable; severity was inflated almost everywhere (only a handful stand at medium after verification, none high).

REGRESSIONS FOUND AND FIXED (89 Issues added to the task; the merge closes them):
- root: the dependency table moved into req.concorde.part-dependencies, which now states Distribution's host loading (registration entries, develop.check) as its one way to other parts' code; the part-dependency test reads it; merge-check, coordination-only delivery and Spec tooling wording; includes of Tasks' docs.
- systemic `uses` gap: req.concorde.part-dependencies says every part meets Distribution's host promises through a `uses`, but spec-tooling, Spec core, kernel, worker-harness, execution, issues and method declared none; all now do, and Spec core declares its format-only uses of the Kernel (I-a1a9a21a) and Distribution's two records; Distribution regained its uses of Execution and Tasks; Adoption/Scaffold/Validation declare their uses of Workflows' step-output convention.
- kernel (13): main's artifact API, the .concorde-write- temporary name and the refusal-location rule, all lost when the Kernel contract was written afresh, restored; delivery commit verification, glossary definition, split requirements, scenarios with matching tests, usage walkthrough; Spec core's registered dialect aligned (refuses $schema/$id, with a test).
- worker-harness (8): the new parent entry's failure categories, code-to-spec exception, glossary breach as violation (also in Workers), deletion ordering, diagram, purpose.
- execution (8): run control described as the records Execution promises (Tasks reads them and signals runners itself; the "registered" integration did not exist), the definition interface in runner.md, one obligation per requirement, Spec-error translation and unbound_write moved to Method; CODE FIX I-028e614e (new, medium): an unexpected exception in a definition's admission or runtime-path resolver left the run with NO result (against req.execution.one-result); it is now a failed result with host-error evidence, as a step's (new scenario and test).
- issues (11): includes of Kernel/Spec core contracts; scenarios conditioned on the spec part; CODE: `issues report --check` of a report with an origin resolves no reporting Module (Dogfooding's null-owner defect report was refused without the spec part, I-b8f18c9d); CODE, your decision on I-8fb85b29: an Issue write that cannot read a task record refuses with the new environment code `unreadable_task_record` (fails closed, as main did).
- workflows (8): how a workflow is started; a new "Contributing a workflow" contract section (registration, adapter API, script result: previously only in code, I-a8a130da medium); missing relies_on; the review-note scenario and its test.
- coordination (1), method (8): optional-integrations table (worker harness, reading Operations); Method selects Spec core's and Issues' interfaces (I-75bcb259, I-77f3788b, medium); requirement and scenario splits; flow diagram through step 9; brownfield walkthrough without Coordination.
- distribution (17): the project MCP server's session/call/host-refusal contract, dropped when the server moved from Main session, ported into Distribution's contracts with what the refactor added (I-0c234cd9, medium); build-manifest contract; CODE: a failing idle_check/after_update callback is refused with `part_failed` instead of a traceback (I-3ea0a75f); a wait ends with the server while long work goes on (I-8b0df4fc, medium); requirement/scenario wording and splits.

PRE-EXISTING (left open, 47): medium (1): I-c718ab75 (workflows, decision-needed: a run started but not recorded can be started again under the same key). Low (46), of which decision-needed: I-32c275f2 (workflows: a first step lost before any record makes the report refuse no_workflow). The others are low obvious-fix/preferred-fix/suggestion wording issues: concorde I-157f6dee I-684059ec I-a3522268 I-b26defe9; coordination I-18f7b9fd I-900476aa I-aa144f57; distribution I-1100d67b I-d31fff34 I-d8b60e43 I-efaedb06 I-fde7a6ca; execution I-1f0d13de I-63a5e814 I-6c7a7ad9 (mixed suggestion, text unchanged from main) I-72b32bfd I-a6f3475b I-b77b34b5; issues I-29056133 I-93d72982 I-a314ad1d I-a7e1faf1 I-cabec454 I-d7054aed; kernel I-5d5394cc I-bbd85366; method I-306cc67a I-32096c56 I-3e9dab61 I-d1797c55 I-fbdad9e5; spec-tooling I-02c637e2 I-3617d25e I-71b30f64 I-78b3560a I-9f262a85; tasks I-6552098a; workflows I-11482e72 I-48d13318 I-7b8ad4b4 I-81054821 I-85b11ef9 I-db4ce098 I-de9a2e37 I-ebfe7757. Main's session contract gave workflow_step calls wait+120 s while code gives every call 300 s, as main's code did: pre-existing, the Spec now states 300 s. I-b4fe5ad3 (detached-run test teardown race) is pre-existing and left open as the brief allowed.

SYSTEMIC
1. `uses` declarations did not follow the root's own rule that a part relying on another's format or Distribution's host promises declares a `uses`: now fixed in every part, but nothing checks it. A structural check (a Module binding a registration.json must use module.distribution) would keep it.
2. Contracts lost in moves: Spec core -> Kernel (artifact API, temp-file name, refusal location) and Main session -> Distribution (the whole MCP session contract). Precise text existed on main and the move kept only prose; the code still matched main.
3. Old text read against optional parts: requirements and scenarios that silently assumed every part installed (spec registry, coordination task records, Coordination in guidance/walkthroughs). Two of these were behaviour regressions (I-b8f18c9d, I-8fb85b29).
4. Moved code without moved Spec duties: Execution still described Spec-error translation, unbound_write and a Tasks integration that now live in Method/Coordination.
5. Process: a run's write audit blames its workers for any concurrent change in the worktree, so a task session must not edit its worktree while a run runs (it cost one panel batch here). The guidance says so for validation and delivery; it could say so for every run.

Decisions taken without the developer are in the decision log (scratch files in the git-ignored .generated/review/). One commit message (7007edc3) lost the word "`--check`" to shell substitution; left as is, since task sessions never rebase. Escalations: none open.
- Correction to report 1: the task resolves 87 Issues, not 89.

## Closed: merged, 2026-10-03T09:35:38Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 6b2824c81186b8aff264f2849fef43008ec8bc8c into parts-split and closed it as merged. Nobody answers a report after that.
