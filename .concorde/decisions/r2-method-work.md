# Decision log: r2-method-work

Goal: Fix the critical, high and obvious-fix open Issues of Implementation, Understanding, General work, Validation and Delivery found by the complete project_review

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 23 Issues in its `resolves`,
owned by its Modules, found by the complete project_review
r-20261008T063808-project_review-9851e69f (unbound; reports under
`.concorde/unbound/r-20261008T063808-project_review-9851e69f/` of the primary worktree) or
earlier. Read each with `concorde issues show`. Other open Issues of these Modules are out of
scope: do not fix them, even when nearby, unless a fix in scope needs it.

By tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest
  meanwhile. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- Work critical first, then high.
- An Issue that does not hold, is a duplicate or is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix needing a change outside the task's Modules: escalate, unless it is a small mechanical
  follow-on (a link, a fixture, a registry refresh).

Eleven other round-2 tasks run in parallel, each on other Modules (r2-*). If a merge conflict
comes back, the main agent asks you to merge the primary branch in. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-08T13:39:38Z

- **task-session** task session (task r2-method-work): `reviewer_grant_snapshot`
  I-6357fa3c (decision-needed, high, module.general-work): which snapshot gives the general reviewer's grant after a Spec-writing worker. The entry (The review) says the reviewer 'runs under the same task type's grant with every writable level lowered to read' and 'therefore reads what the worker could read'. The code (general_work/operation.py review() -> method/workers.py run_worker) recomputes the grant from the worktree's Specs as the worker left them, so a specify worker that changes a declaration or breaks a Spec document changes the reviewer's readable set or makes the reviewer fail grant_unavailable before review. The preferred-fix Issue I-df0eb0fa asks for the frozen grant; it depends on this decision, so I hold it until the answer. Spec core says 'the grant of the next worker is computed from the changed Specs', which is the general rule for successive workers.
  Not handled here (decision): the brief reserves decision-needed Issues; the choice changes General work's access promise and how it relates to Spec core's next-worker rule
  Options: A: reuse the worker's frozen grant (same context identity) with writes lowered for the reviewer; state in General work that the reviewer is the exception to Spec core's next-worker rule; add a declaration-changing scenario (fixes I-df0eb0fa too); B: keep recomputing from the changed Specs; reword the entry so the reviewer reads what the changed Specs grant, and state that unloadable Specs fail grant_unavailable before review
  Recommendation: A: the reviewer judges the worker's result, so it must see exactly what the worker saw; a broken Spec is then reported by the reviewer instead of ending the run without review. The change stays inside General work and Method's worker sequence (run_worker gains an optional given grant)

```json
{
  "level": "task-session",
  "actor": "task session (task r2-method-work)",
  "code": "reviewer_grant_snapshot",
  "detail": "I-6357fa3c (decision-needed, high, module.general-work): which snapshot gives the general reviewer's grant after a Spec-writing worker. The entry (The review) says the reviewer 'runs under the same task type's grant with every writable level lowered to read' and 'therefore reads what the worker could read'. The code (general_work/operation.py review() -> method/workers.py run_worker) recomputes the grant from the worktree's Specs as the worker left them, so a specify worker that changes a declaration or breaks a Spec document changes the reviewer's readable set or makes the reviewer fail grant_unavailable before review. The preferred-fix Issue I-df0eb0fa asks for the frozen grant; it depends on this decision, so I hold it until the answer. Spec core says 'the grant of the next worker is computed from the changed Specs', which is the general rule for successive workers.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the brief reserves decision-needed Issues; the choice changes General work's access promise and how it relates to Spec core's next-worker rule"
  },
  "options": [
    "A: reuse the worker's frozen grant (same context identity) with writes lowered for the reviewer; state in General work that the reviewer is the exception to Spec core's next-worker rule; add a declaration-changing scenario (fixes I-df0eb0fa too)",
    "B: keep recomputing from the changed Specs; reword the entry so the reviewer reads what the changed Specs grant, and state that unloadable Specs fail grant_unavailable before review"
  ],
  "recommendation": "A: the reviewer judges the worker's result, so it must see exactly what the worker saw; a broken Spec is then reported by the reviewer instead of ending the run without review. The change stays inside General work and Method's worker sequence (run_worker gains an optional given grant)",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T13:39:50Z

- **task-session** task session (task r2-method-work): `staged_content_promise`
  I-826ee364 (decision-needed, high, module.delivery): which staging transformations the exact-content promise permits. The task fix-delivery (merged 310fec4d5, after the review's head ce20cc7489) already answered it as a preferred-fix of I-95b5d191, without the developer: new req.delivery.staged-validated and step 9 compare the staged tree with the readiness measurement under checkout semantics. A clean filter a checkout reverses (Git LFS, line endings) passes; one that rewrites content fails staged_unvalidated; and 'when core.fileMode is false, Git ignores the executable bit, and so does this comparison'. So I-826ee364's design gap is closed except that last choice. The preferred-fix I-10dcd1ab (high, same Module) names exactly that remaining case: with core.fileMode=false, Validation measures the exec bit from the worktree (100755) while Git stages the index's mode (100644), and Delivery returns ok for a commit whose mode differs from what readiness examined. Its other cases (content rewritten by staging) are fixed and tested (test_staging_that_changes_validated_content_is_refused, test_staging_through_a_filter_a_checkout_reverses_is_delivered). I hold I-10dcd1ab until the answer.
  Not handled here (decision): the brief reserves decision-needed Issues; the answer fixes what Delivery's central exact-content promise means and may change Validation's input measurement
  Options: A: confirm fix-delivery's choice (checkout semantics, exec bit ignored without core.fileMode); I close the gap by noting it and report I-826ee364 and I-10dcd1ab as resolved by fix-delivery, the exec-bit case accepted as documented; B: Validation measures the mode Git stages: without core.fileMode, a tracked file's exec bit comes from the index (Git's own rule), a new file's from the worktree; Delivery then compares modes always, so the commit's mode is exactly the examined one (changes Validation's input-measurement contract, inside this task's Modules); C: compare modes strictly and refuse staged_unvalidated whenever the worktree exec bit differs from the staged mode, even without core.fileMode (refuses deliveries on filesystems without exec bits, where every file looks executable)
  Recommendation: B: it makes 'exactly what was validated' literal without refusing deliveries on filesystems that have no exec bit; the worktree exec bit carries no meaning once the repository turns core.fileMode off

```json
{
  "level": "task-session",
  "actor": "task session (task r2-method-work)",
  "code": "staged_content_promise",
  "detail": "I-826ee364 (decision-needed, high, module.delivery): which staging transformations the exact-content promise permits. The task fix-delivery (merged 310fec4d5, after the review's head ce20cc7489) already answered it as a preferred-fix of I-95b5d191, without the developer: new req.delivery.staged-validated and step 9 compare the staged tree with the readiness measurement under checkout semantics. A clean filter a checkout reverses (Git LFS, line endings) passes; one that rewrites content fails staged_unvalidated; and 'when core.fileMode is false, Git ignores the executable bit, and so does this comparison'. So I-826ee364's design gap is closed except that last choice. The preferred-fix I-10dcd1ab (high, same Module) names exactly that remaining case: with core.fileMode=false, Validation measures the exec bit from the worktree (100755) while Git stages the index's mode (100644), and Delivery returns ok for a commit whose mode differs from what readiness examined. Its other cases (content rewritten by staging) are fixed and tested (test_staging_that_changes_validated_content_is_refused, test_staging_through_a_filter_a_checkout_reverses_is_delivered). I hold I-10dcd1ab until the answer.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the brief reserves decision-needed Issues; the answer fixes what Delivery's central exact-content promise means and may change Validation's input measurement"
  },
  "options": [
    "A: confirm fix-delivery's choice (checkout semantics, exec bit ignored without core.fileMode); I close the gap by noting it and report I-826ee364 and I-10dcd1ab as resolved by fix-delivery, the exec-bit case accepted as documented",
    "B: Validation measures the mode Git stages: without core.fileMode, a tracked file's exec bit comes from the index (Git's own rule), a new file's from the worktree; Delivery then compares modes always, so the commit's mode is exactly the examined one (changes Validation's input-measurement contract, inside this task's Modules)",
    "C: compare modes strictly and refuse staged_unvalidated whenever the worktree exec bit differs from the staged mode, even without core.fileMode (refuses deliveries on filesystems without exec bits, where every file looks executable)"
  ],
  "recommendation": "B: it makes 'exactly what was validated' literal without refusing deliveries on filesystems that have no exec bit; the worktree exec bit carries no meaning once the repository turns core.fileMode off",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T13:40:56Z

- **task-session** task session (task r2-method-work): `checks_validation_outside_modules`
  I-8622d42f (preferred-fix, high, module.validation): Validation's step 6 promises that a malformed check blocks as one check finding even in a Module whose checks the run does not run, and delegates that to Check execution's validate_checks. validate_checks (src/concorde/execution/checks/checks.py:356) only reads the files and each check's inputs; argv, env, when and timeout_seconds are validated in run_checks only for the checks it keeps, so an unselected Module's check with timeout_seconds=0 or a non-object env passes readiness. Checks' own Spec (execution/checks/service.md 'For a caller that wants the checks files judged...') does not promise field validation from validate_checks. The fix belongs to module.checks (task r2-execution's Module): validate_checks also runs the existing field validators (_valid_argv, the when check, _timeout, environment) on every check, plus one sentence in service.md; Validation keeps its conversion to a check finding and gains a regression test.
  Not handled here (scope): the fix changes the code and promise of module.checks, which is outside this task's Modules and is being changed by r2-execution in parallel
  Options: A: I make the small change in checks.py validate_checks and service.md in this task, with the Validation regression (risk: merge conflict with r2-execution in checks.py); B: r2-execution makes the Checks change; I add only the Validation regression test once it is merged, or leave I-8622d42f open for it; C: Validation validates the fields itself without changing Checks (duplicates Checks' rules; not recommended)
  Recommendation: A: about ten lines reusing Checks' own validators; the conflict risk is small and the Issue is then closed by one task

```json
{
  "level": "task-session",
  "actor": "task session (task r2-method-work)",
  "code": "checks_validation_outside_modules",
  "detail": "I-8622d42f (preferred-fix, high, module.validation): Validation's step 6 promises that a malformed check blocks as one check finding even in a Module whose checks the run does not run, and delegates that to Check execution's validate_checks. validate_checks (src/concorde/execution/checks/checks.py:356) only reads the files and each check's inputs; argv, env, when and timeout_seconds are validated in run_checks only for the checks it keeps, so an unselected Module's check with timeout_seconds=0 or a non-object env passes readiness. Checks' own Spec (execution/checks/service.md 'For a caller that wants the checks files judged...') does not promise field validation from validate_checks. The fix belongs to module.checks (task r2-execution's Module): validate_checks also runs the existing field validators (_valid_argv, the when check, _timeout, environment) on every check, plus one sentence in service.md; Validation keeps its conversion to a check finding and gains a regression test.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "the fix changes the code and promise of module.checks, which is outside this task's Modules and is being changed by r2-execution in parallel"
  },
  "options": [
    "A: I make the small change in checks.py validate_checks and service.md in this task, with the Validation regression (risk: merge conflict with r2-execution in checks.py)",
    "B: r2-execution makes the Checks change; I add only the Validation regression test once it is merged, or leave I-8622d42f open for it",
    "C: Validation validates the fields itself without changing Checks (duplicates Checks' rules; not recommended)"
  ],
  "recommendation": "A: about ten lines reusing Checks' own validators; the conflict risk is small and the Issue is then closed by one task",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-08T13:40:56Z

- **task-session** task session (task r2-method-work): `method_uses_in_other_modules`
  I-c35c0aa3 (preferred-fix, high, owner module.implementation) and I-507f19a0 (preferred-fix, high, module.general-work): Method's worker-backed children rely on Method's standard worker sequence (method/module.md, requirements.md, workers.md) without declaring uses of module.method. The Protocol allows uses across hierarchy levels. My fix for a child: a uses of module.method with relies_on concept.standard-worker-sequence and the req.method.* promises of the sequence (workspace-specs, models-placed-first, grant-as-data, glossary-by-entry, gaps-never-repaired, trace-writes-reported), an includes of document.method.workers (it defines no identities, so relies_on cannot select it) with its reason, a #uses-method paragraph, and registry --write. I will do it for this task's three children: implementation, understanding, general-work. I-c35c0aa3 also names specification, adoption, code-review, spec-review and project-review, which are Modules of r2-adoption-specification and r2-reviews.
  Not handled here (scope): five of the eight affected children are other tasks' Modules, being changed in parallel
  Options: A: I fix my three children; the main agent asks r2-adoption-specification and r2-reviews to add the same uses to theirs (I can give them the exact JSON), and I-c35c0aa3 closes when all are merged; B: I fix all eight children in this task as a mechanical follow-on (metadata + one paragraph each; conflict risk with the two other tasks)
  Recommendation: A: each task keeps to its own Modules; the pattern is identical and small for the others

```json
{
  "level": "task-session",
  "actor": "task session (task r2-method-work)",
  "code": "method_uses_in_other_modules",
  "detail": "I-c35c0aa3 (preferred-fix, high, owner module.implementation) and I-507f19a0 (preferred-fix, high, module.general-work): Method's worker-backed children rely on Method's standard worker sequence (method/module.md, requirements.md, workers.md) without declaring uses of module.method. The Protocol allows uses across hierarchy levels. My fix for a child: a uses of module.method with relies_on concept.standard-worker-sequence and the req.method.* promises of the sequence (workspace-specs, models-placed-first, grant-as-data, glossary-by-entry, gaps-never-repaired, trace-writes-reported), an includes of document.method.workers (it defines no identities, so relies_on cannot select it) with its reason, a #uses-method paragraph, and registry --write. I will do it for this task's three children: implementation, understanding, general-work. I-c35c0aa3 also names specification, adoption, code-review, spec-review and project-review, which are Modules of r2-adoption-specification and r2-reviews.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "five of the eight affected children are other tasks' Modules, being changed in parallel"
  },
  "options": [
    "A: I fix my three children; the main agent asks r2-adoption-specification and r2-reviews to add the same uses to theirs (I can give them the exact JSON), and I-c35c0aa3 closes when all are merged",
    "B: I fix all eight children in this task as a mechanical follow-on (metadata + one paragraph each; conflict risk with the two other tasks)"
  ],
  "recommendation": "A: each task keeps to its own Modules; the pattern is identical and small for the others",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-08T13:41:24Z

r2-method-work: early escalations (4 decisions), work continues meanwhile.

1. reviewer_grant_snapshot — I-6357fa3c (decision-needed, high, General work). After a Spec-writing worker, which snapshot gives the general reviewer's grant? The entry says the reviewer runs under "the same task type's grant" with writes lowered and "reads what the worker could read"; the code recomputes the grant from the Specs as the worker left them (a changed declaration changes the reviewer's reads; a broken Spec ends the run grant_unavailable before review). Spec core's general rule: "the grant of the next worker is computed from the changed Specs". I-df0eb0fa (preferred-fix) asks for the frozen grant and waits on this answer.
   Options: A reuse the worker's frozen grant (same context identity), writes lowered; General work states the reviewer is the exception to Spec core's next-worker rule; declaration-changing scenario (also fixes I-df0eb0fa; run_worker in Method's workers.py gains an optional given grant). B keep recomputing; reword the entry and state grant_unavailable before review.
   Recommendation: A.

2. staged_content_promise — I-826ee364 (decision-needed, high, Delivery). Which staging transformations does the exact-content promise permit? Task fix-delivery (merged 310fec4d5, after the review's head) already settled it as a preferred-fix without the developer: req.delivery.staged-validated compares the staged tree with readiness under checkout semantics (filters a checkout reverses pass, content-rewriting clean filters fail staged_unvalidated), and "when core.fileMode is false, Git ignores the executable bit, and so does this comparison". The remaining gap is that last clause, which is exactly I-10dcd1ab's (preferred-fix, high) case: under core.fileMode=false Validation measures the exec bit from the worktree but Git stages the index's mode, and Delivery returns ok with a different mode. I-10dcd1ab waits on this answer.
   Options: A confirm fix-delivery's choice; both Issues are then resolved by fix-delivery. B Validation measures the mode Git stages (without core.fileMode a tracked file's exec bit comes from the index, a new file's from the worktree) and Delivery always compares modes (changes Validation's input-measurement contract, inside this task). C compare strictly and refuse (refuses deliveries on filesystems without exec bits).
   Recommendation: B.

3. checks_validation_outside_modules — I-8622d42f (preferred-fix, high, Validation). An unselected Module's malformed check (timeout_seconds=0, non-object env) passes readiness because Check execution's validate_checks validates no fields. The fix belongs to module.checks (r2-execution's Module): validate_checks runs Checks' existing field validators on every check, one sentence in execution/checks/service.md; Validation adds a regression.
   Options: A I make the ~10-line Checks change here (small conflict risk with r2-execution). B r2-execution makes it; I add only the Validation test or leave the Issue to it. C Validation duplicates Checks' field rules (not recommended).
   Recommendation: A.

4. method_uses_in_other_modules — I-c35c0aa3 (preferred-fix, high, owner Implementation) and I-507f19a0 (General work). Method's worker-backed children should declare uses of module.method (relies_on concept.standard-worker-sequence and the req.method.* promises of the sequence, plus includes of document.method.workers). I do it for implementation, understanding and general-work. I-c35c0aa3 also names specification, adoption, code-review, spec-review and project-review (Modules of r2-adoption-specification and r2-reviews).
   Options: A I fix my three; you ask those two tasks to add the same declaration (I can give the exact JSON); the Issue closes when all are merged. B I fix all eight here as a mechanical follow-on (conflict risk).
   Recommendation: A.

Found so far: I-e0a025f3 (scenario heading levels) and I-3e31becd (decode measurement paths) are already fixed by fix-delivery (merged 310fec4d5, after the review's head ce20cc7489): scenario_sections uses Spec core's parse_reading; require_verified_scenarios and the staged comparison use real_path; tests test_scenarios_at_every_heading_level_need_a_test and test_the_scenario_gate_decodes_paths_the_measurement_quotes. I will confirm both with a run of the tests and list them as resolved by fix-delivery in my final report.

It carries escalation(s) 1, 2, 3, 4.

## Task session decisions (2026-10-08)

- Escalated early (report 1): I-6357fa3c (reviewer grant snapshot; I-df0eb0fa held on it),
  I-826ee364 (staged-content promise; I-10dcd1ab's exec-bit remainder held on it), I-8622d42f (fix
  lies in module.checks), I-c35c0aa3 (five of eight children are other tasks' Modules).
- I-e0a025f3 and I-3e31becd do not hold any more: task fix-delivery (merged 310fec4d5, after the
  review's head ce20cc7489) fixed them as I-4c792555 and I-52fe4d34 (scenario_sections uses Spec
  core's parse_reading; the scenario gate decodes paths with real_path), with regressions.
- I-3edb843b (preferred-fix): fixed the Spec, not the code. Leaving out a binding's removed Module
  with removed-module evidence is deliberate (c7d81986e; Execution's runner step 4 and
  scenario.execution.removed-module; Method's Definitions realization): a binding cannot change, so
  a workspace that removes or renames a Module it works on could never deliver if a removed binding
  Module blocked. Validation's entry now says so, says a binding with no Module left is refused
  modules_removed, and keeps the structural finding for a Module --modules names. The reviewer's
  suggested repair (keep the whole selection) would have made such tasks undeliverable.
- I-287699fb: Git launch errors become MeasurementError git_failed inside measurement.git(), so
  every caller (measure, remeasure, current_branch, gitlink_commit) gets them; the branch check of
  both commands and Delivery's head lookup now report measurement_failed. Step 1 of the table names
  it.
- I-625347c9: an existing changed path with no Git file mode fails path_unreadable (no lstat
  change needed: mode None and lexists).
- I-ce0118c5: the ancestor-of-external exemption requires measured mode 160000; scenario line and
  test added for a file and a symbolic link in the submodule's place.
- I-eb76eec6: step 6 explained in two phases (ordinary checks per Module in identity order, then
  one selective call for the whole selection; no tests, nothing runs; a failed selective call blocks
  naming the whole selection); new scenario.validation.selective-check with a test.
- I-f7020366: plan_review's basis check adds every concept of SpecRepository.terms(module) of the
  bound Modules; the requirement and scenario now say a selected concept resolves wherever its
  explanation lies (the glossary's Spec context already includes the glossary entries of its terms,
  so this is a code fix plus clarification).
- I-c6363a70: req.understanding.task-worktree now names the worktree the run works on (workspace or
  unbound checkout); new scenario.understanding.unbound-committed-specs with a test that an
  uncommitted Spec document of the primary worktree is absent from an unbound run's brief.
- I-33ad078e: the exception became a third condition of the list. I-4ab08ea6: new
  req.understanding.plan-review-copy-reported.
- I-ced6eafd: the reviewer's brief now carries the workspace's goal and inputs_material(ctx), same
  as the worker's; new scenario.general-work.review-inputs (not reused rewrite) and prompt bullets.
- I-fa4c1a35: "modified or deleted" in the requirement (now a list), the entry's review list and
  step 4.
- I-507f19a0 / I-c35c0aa3 (my three children only, pending answer 4): uses module.method with
  relies_on concept.standard-worker-sequence and the six req.method.* sequence requirements (not
  the brownfield or issues ones), plus includes document.method.workers, since workers.md defines no
  identity relies_on could select; a #uses-method paragraph in each entry. Checked: the specify grant
  of module.general-work now reads method/module.md, requirements.md and workers.md, not brownfield.md.
- I-77ba2923: the requirement covers implement and test (both run the same checked Modules) and
  lists Check execution's work-stage rules by reference; the scenario's check is ordinary and the
  round clean and ok. I-e00a3aeb: clean audit added to the deletion scenario's GIVEN.
- I-02defd25: split into marked + empty-commit, rejected-removed + rejected-inspectable +
  rejected-reported, atomic + failed-worktree-kept + failed-paths-named; existing identities keep
  their main duty so the links from the root and other requirements stay right.

## Answer to report(s) 1 of the task session, 2026-10-12T14:26:33Z

Escalations 1-4 (main agent): 1 reviewer_grant_snapshot: A — reuse the worker's frozen grant, writes lowered; General work states the reviewer is the exception to Spec core's next-worker rule; resolves I-df0eb0fa too. 2 staged_content_promise: B — Validation measures the mode Git stages (core.fileMode false: a tracked file's exec bit from the index, a new file's from the worktree) and Delivery always compares modes; resolves I-826ee364 and I-10dcd1ab. 3 checks_validation_outside_modules: r2-execution already made validate_checks validate every check's fields (I-c621d7cc, delivered; it merges before you deliver). After the main agent's merges, merge the primary branch into your task branch, add only Validation's regression test and resolve I-8622d42f. 4 method_uses_in_other_modules: B after that merge — r2-adoption-specification and r2-reviews have delivered, so once the primary branch is merged in, add the uses-module.method declaration to all eight Modules here as a mechanical follow-on and resolve I-c35c0aa3 and I-507f19a0. I-e0a025f3 and I-3e31becd: list them as fixed by fix-delivery with evidence; the merge closes them. Wait for my message that the merges are done before merging the primary branch in.

## Main agent, 2026-10-12

The other round-2 tasks (r2-execution, r2-kernel-tracing, r2-worker-harness, r2-e2e,
r2-adoption-specification, r2-tasks, r2-task-session-main, r2-workflows-issues-root, r2-reviews,
r2-distribution) are merged into the primary branch. Merge the primary branch into this task
branch now, then carry out answers 3 and 4 of report 1.

## Task session decisions (2026-10-12, after answer 1)

- Merged main (all other round-2 tasks) into the task branch: no conflicts (5ad7d5db4).
- Answer 1 (A), I-6357fa3c and I-df0eb0fa: `run_worker` takes `frozen`, a grant an earlier worker
  of the same run received (given back through `grants`), and then computes none; `grant-frozen`
  evidence names its context identity. The general reviewer runs under the worker's grant with
  writes lowered. General work's entry, req.general-work.reviewer-reads-only and step 5 say so and
  name the exception to Spec core's next-worker rule; new scenario.general-work.reviewer-frozen-grant
  with a test (a specify worker breaks the bound Module's metadata; the reviewer still launches with
  the worker's context identity and reads the used Module's Spec). The test fails without the fix
  with grant_unavailable. Mechanical follow-on outside my Modules: one paragraph in Method's
  workers.md describing the reused grant (the code lives in method/workers.py, as the answer named).
- Answer 2 (B), I-826ee364 and I-10dcd1ab: deviation from the answer's parenthetical, which came
  from my escalation and was wrong about Git: with core.fileMode false Git stages a **new** file as
  100644, not with the worktree's exec bit (checked: `git add` of a new executable file under
  core.fileMode=false lists 100644; Git's ce_mode_from_stat "assume unexecutable regular file").
  The answer's intent is "Validation measures the mode Git stages", so the measurement follows
  Git's real rule: a regular index entry keeps its mode, any other regular file is 100644. Delivery
  now always compares modes. Readiness contract version 9 -> 10 (behaviour change of `mode`).
  New scenario.validation.untrusted-mode and scenario.delivery.untrusted-mode with tests.
  core.symlinks=false (a plain file staged as 120000) is left as it was: not in the Issues.
- Answer 3, I-8622d42f: regression test only (a malformed `timeout_seconds` or `env` of an
  unselected Module's check blocks as one `configured checks` finding; a valid one does not).
- Answer 4 (B), I-c35c0aa3 and I-507f19a0: the same uses of module.method (concept + six
  req.method.* sequence requirements) and include of document.method.workers for Specification,
  Adoption, Code review, Spec review and Project review, with a #uses-method paragraph each; Spec
  review's "Around it" list and checked d2 diagram gain Method. Removed the includes of
  document.method.module (code-review, spec-review, project-review) and document.method.requirements
  (spec-review), which CHK.includes.redundant reported once the uses selects them. Fixed the grammar
  of General work's #uses-method sentence.

## Report 2 to the main agent (Review流程), 2026-10-12T15:02:44Z

r2-method-work delivered: delivery commit c25d5466e on concorde/r2-method-work (main merged in at 5ad7d5db4, no conflicts). task-validation ready (28 checks passed); full suite 1454 passed, 5 skipped.

Resolves all 23 Issues of the task's resolves:
- Answer 1 (A) — I-6357fa3c, I-df0eb0fa: the general reviewer runs under the worker's frozen grant (same context identity, writes lowered). run_worker in method/workers.py takes `frozen`/`grants`; General work's entry, req.general-work.reviewer-reads-only and step 5 name the exception to Spec core's next-worker rule; new scenario.general-work.reviewer-frozen-grant (worker breaks the Module's metadata; reviewer still launches; the test fails without the fix with grant_unavailable). Follow-on outside my Modules: one paragraph in Method's workers.md on the reused grant.
- Answer 2 (B) — I-826ee364, I-10dcd1ab: Validation measures the mode Git stages; Delivery always compares modes. DEVIATION from the answer's parenthetical (which came from my escalation and was wrong): with core.fileMode=false Git stages a NEW file as 100644, not with the worktree's exec bit (verified with git add; Git's rule "assume unexecutable regular file"). So the measurement follows Git's real rule: a regular index entry keeps its mode, any other regular file is 100644. Readiness contract version 9 -> 10. New scenario.validation.untrusted-mode and scenario.delivery.untrusted-mode with tests. core.symlinks=false is unchanged (not in the Issues).
- Answer 3 — I-8622d42f: Validation regression only (a malformed timeout_seconds or env of an unselected Module's check blocks as one `configured checks` finding), on r2-execution's fix.
- Answer 4 (B) — I-c35c0aa3, I-507f19a0: all eight worker-backed children of Method declare uses of module.method (concept.standard-worker-sequence + the six req.method.* sequence requirements) and include document.method.workers, each with a #uses-method paragraph. CHK.includes.redundant then reported includes of document.method.module (code-review, spec-review, project-review) and document.method.requirements (spec-review), now selected by the uses, so I removed them. Spec review's "Around it" list and d2 diagram gain Method.
- I-e0a025f3, I-3e31becd: already fixed by fix-delivery (merged 310fec4d5): scenario_sections uses parse_reading, the scenario gate decodes paths with real_path; tests test_scenarios_at_every_heading_level_need_a_test and test_the_scenario_gate_decodes_paths_the_measurement_quotes pass.
- Earlier (2026-10-08 commits): I-02defd25, I-287699fb, I-33ad078e, I-3edb843b (Spec fixed, not code: dropping a removed binding Module is deliberate), I-4ab08ea6, I-625347c9, I-77ba2923, I-c6363a70, I-ce0118c5, I-ced6eafd, I-e00a3aeb, I-eb76eec6, I-f7020366, I-fa4c1a35, as the decision log details.

Open: nothing. Ready for task merge.

## Closed: merged, 2026-10-12T15:03:07Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit c25d5466e6688ea4786578d38c1eae40a441240d into main and closed it as merged. Nobody answers a report after that.
