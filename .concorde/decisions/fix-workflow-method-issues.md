# Decision log: fix-workflow-method-issues

Goal: Fix the parts refactor's regressions in the workflow, method and issues parts found by the overall review, and make reviews keep a reviewer's findings when one location or an empty earlier is wrong

## Brief (main agent, 2026-10-03)

### Context

The developer split Concorde into independently installable parts on the integration branch
`parts-split` (primary worktree on it; `main` untouched; decision logs of parts-spec ...
parts-install in `.concorde/decisions/`). Before fast-forwarding `main` to it, the developer had the
whole change reviewed: task `parts-review` (`.concorde/decisions/parts-review.md`) Module-reviewed
every changed Module, verified every finding against code, Spec and `main`, and classified 49 Issues
as regressions of the refactor (11 medium, none high or critical) and about 211 as pre-existing. The
developer decided (2026-10-03): **fix every regression on `parts-split`, plus the two defects that
make reviews unreliable, then merge**; pre-existing Issues wait until after the merge. Four fix
tasks run in parallel, one per group of parts: `fix-spec-root`, `fix-kernel-execution`,
`fix-workflow-method-issues`, `fix-coordination-distribution`.

### Rules

- The Issues this task resolves are on it (`--resolves`); the merge closes them. Read each with
  `concorde issues show` (its latest report is the verified one; parts-review corrected tiers and
  severities). Fix each in the Specs, code and tests as its report says, unless the decision below
  says otherwise. If one turns out not to hold, close it yourself with `not-actionable` and the
  reason, and record why; if fixing one needs a decision with major impact, escalate it.
- Stay in your group's files as far as the fix allows; another task may meet you in a shared file
  (registrations, guidance composition, `tests/concorde/development/`), so keep such edits small. If
  the merge conflicts, the main agent will ask you to merge `parts-split` in.
- Introduce no new regression: every part must still work installed with only its dependencies
  (`tests/concorde/acceptance/test_parts.py`), the part-dependency test must pass, and guidance
  must read correctly whichever parts are installed. Rapid-iteration rule: no shims or dual paths.
- Verify with `build --check`, `spec-validation`, the full suite and smoke runs of what you touched,
  then `task-validation` and `delivery`, and report.

### Your group: workflow, method, issues, and review reliability

Decided by the main agent:
- I-5c805131 together with the pre-existing I-5badf523: the brownfield workflow describes created
  Modules in the order of the uses graph condensed into strongly connected groups: groups in
  topological order (providers first), the Modules of one group in scaffold order. State it in
  `req.method.brownfield-providers-first` (and Method's brownfield text) and implement it in
  `brownfield.js`.
- I-85a1e885: a new finding may carry `earlier` as an empty string, which the host treats as no
  earlier Issue (spec_review, spec_panel and code_review alike); keep a non-empty `earlier` checked.
- I-82b9bb29: a reviewer whose findings cite a location or basis that does not hold is resumed once
  through its round validation with the unresolved citations to correct; whatever still does not
  hold after the rounds drops only the findings concerned, each recorded as rejected with the
  reason, never the reviewer's other findings. Apply it to code_review and spec_review/spec_panel
  where they share the rule, and update their requirements and scenarios.

## Task session decisions (2026-10-03)

Commits on `concorde/fix-workflow-method-issues`: 32358f05, ec7a57ff, 868f0088, 33787991.

- I-c66d7124 (obvious-fix): a superseded step's row no longer reads its run's workflow object
  (`report.Row(..., superseded=True)`), so a malformed object of a superseded run cannot fail the
  report. Regression test supersedes it with a restart label, since the bad run ended `ok`.
- I-60bd5fea (obvious-fix): corrected the sentence of `contract.workflows.step-output` to the object
  shape `{"answers": [...]}` that code and its consumer already use. No version bump: no behaviour
  or field changed, only the wording now matches it.
- I-cfb021e5, I-31e529e2 (preferred-fix: describe Method in terms of bound workspaces and qualify
  task wording by the coordination part, as the report suggested), I-01f76edf: guidance of the
  workflow, method and issues parts now says what happens without the coordination part (nothing
  binds a worktree; only reading Operations run unbound; without it only another Issue write holds
  the merge lock, so `merge_busy` is written again shortly after).
- I-3ad5326c: `issues check` names a record reached through a symbolic link as not a regular
  record, and also catches the Kernel's `KernelError` around reading a record, so one entry never
  aborts the check.
- I-1b9c2a57: an Issue write whose file transaction failed and could not restore a record is now
  refused `recovery_failed` (told by the record file still holding the text this write published),
  and every Issue refusal's link now carries its causes as links (the Kernel's refusal as actor
  `Kernel (file transaction)`, the operating system's errors below it). New scenario
  `scenario.issues.command-restore-refused`.
- I-f95c7f1a (preferred-fix: "select the latest round that actually ran checks"): `implement`'s
  `checks` come from the last round whose evidence holds check results; a later round that could
  not validate hides nothing.
- I-5c805131 + I-5badf523, as the brief decided: `providersFirst` condenses the uses among created
  Modules into strongly connected groups (Tarjan). Tie-break I chose, now in
  `req.method.brownfield-providers-first`: each time, of the groups whose used groups are all
  described, the one whose first Module the scaffold lists first. New scenario
  `scenario.method.brownfield-mutual-uses`.
- I-815fbe1b: two `specify` tests through Method's `run_worker` (blocked worker changing a foreign
  entry; proposed deletion of the glossary), new scenario `scenario.method.glossary-after-run`;
  checked that both fail when the post-run audit is removed.
- I-85a1e885, as the brief decided: the worker-facing finding schemas of spec_review, spec_panel
  and code_review accept any string `earlier`; the host drops an empty or blank one before anything
  else, and `settle` checks every other one as before. Payload schemas unchanged. New requirements
  `req.spec-review.blank-earlier`, `req.code-review.blank-earlier` and their scenarios.
- I-13e0c56b (preferred-fix as suggested): a Module review records whether its findings were
  settled (`settled`) independently of the issues part; the panel payload uses the settled findings
  then, and drops the chair's raw `earlier` claims for a Module never settled. I applied the same to
  spec_review, whose stopped Modules could leak a raw claim the same way.
- I-82b9bb29, first half, as the brief decided: a finding whose citation does not hold is rejected
  alone and listed with the reason under its Module's new `rejected` (code_review: Module, basis,
  location; spec_review/spec_panel: path outside the workspace); the reviewer's other findings are
  reported and the run ends `ok`. In a panel, a worker's such finding is kept unlabelled in its
  review's `rejected`, and a chair's merged such finding turns its labels into rejections with the
  host's reason, so accounting stays whole. A code_review finding about a Module the reviewer did
  not review is listed under the first Module it reviewed. Contracts bumped:
  `contract.code-review.review` 6, `contract.spec-review.payload` 7,
  `contract.spec-review.panel-payload` 6. The review-code prompt now says a bad citation costs that
  finding.
- I-82b9bb29, second half (the resume round), not done: it needs the worker harness to hand the
  round's worker result to the round validation, which is module.workers', outside this task's
  Modules. Escalated.

## Escalated to the main agent, 2026-10-03T06:31:51Z

- **task-session** task session (task fix-workflow-method-issues): `resume_needs_workers_change`
  I-82b9bb29's decision says a reviewer whose citations do not hold is resumed once through its round validation with the unresolved citations. Workers calls the round validation with only (worktree, round folder) (launch.md#round-validation, workers.py), never with the round's worker result, so Method cannot see the findings to check them. Everything else of I-82b9bb29 is done and committed (33787991): a bad citation now drops only that finding, listed under its Module's rejected with the reason, in code_review, spec_review and spec_panel. What remains needs Workers to hand the round's validated worker result to the round validation as a third argument: a small additive change of module.workers' launch.md and workers.py (one call site; Method's closure and one harness test lambda follow). Then code_review/spec_review/spec_panel launch reviewers with one resume round whose validation answers a repair listing the unresolved citations (no failure, so what still does not hold is rejected as now), and req.code-review.no-resume and code-review's 'One pass' text change to allow this one citation repair.
  Not handled here (decision): the change alters what module.workers promises its callers, a Module outside this task's Modules, and another fix task may be changing the worker harness
  Options: allow this task to make the additive Workers change and implement the resume round (about one more step); leave the resume round to a later task; deliver now with findings rejected alone; relaunch a fresh reviewer for the rejected findings instead of resuming (no Workers change, but a whole new context read)
  Recommendation: allow the additive Workers change in this task

```json
{
  "level": "task-session",
  "actor": "task session (task fix-workflow-method-issues)",
  "code": "resume_needs_workers_change",
  "detail": "I-82b9bb29's decision says a reviewer whose citations do not hold is resumed once through its round validation with the unresolved citations. Workers calls the round validation with only (worktree, round folder) (launch.md#round-validation, workers.py), never with the round's worker result, so Method cannot see the findings to check them. Everything else of I-82b9bb29 is done and committed (33787991): a bad citation now drops only that finding, listed under its Module's rejected with the reason, in code_review, spec_review and spec_panel. What remains needs Workers to hand the round's validated worker result to the round validation as a third argument: a small additive change of module.workers' launch.md and workers.py (one call site; Method's closure and one harness test lambda follow). Then code_review/spec_review/spec_panel launch reviewers with one resume round whose validation answers a repair listing the unresolved citations (no failure, so what still does not hold is rejected as now), and req.code-review.no-resume and code-review's 'One pass' text change to allow this one citation repair.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the change alters what module.workers promises its callers, a Module outside this task's Modules, and another fix task may be changing the worker harness"
  },
  "options": [
    "allow this task to make the additive Workers change and implement the resume round (about one more step)",
    "leave the resume round to a later task; deliver now with findings rejected alone",
    "relaunch a fresh reviewer for the rejected findings instead of resuming (no Workers change, but a whole new context read)"
  ],
  "recommendation": "allow the additive Workers change in this task",
  "causes": []
}
```

## Report 1 to the main agent (项目架构分离建议), 2026-10-03T06:32:07Z

Report 1 of fix-workflow-method-issues: 13 of 14 Issues fixed on the branch, not delivered yet; one decision escalated (#1).

Commits on concorde/fix-workflow-method-issues: 32358f05, ec7a57ff, 868f0088, 33787991, 3041bdb5. Verified: build --check ok, spec-validation 0 errors (2 warnings in distribution, not this task's), full suite 1037 passed / 5 skipped (test_parts and the part-dependency test included).

Fixed (to be resolved by the merge, already on the task): I-c66d7124 (a superseded step's malformed workflow object no longer fails the report), I-60bd5fea (contract wording now names the {"answers": [...]} object; no version bump since no behaviour changed), I-cfb021e5 / I-31e529e2 / I-01f76edf (workflow, method and issues guidance now say what happens without the coordination part), I-3ad5326c (issues check names a record reached through a symlink instead of aborting), I-1b9c2a57 (a refused restoration is recovery_failed; Issue refusal links now carry their causes, new scenario.issues.command-restore-refused), I-f95c7f1a (implement's checks come from the last round that ran checks), I-5c805131 + I-5badf523 (brownfield order condensed into strongly connected groups, as you decided), I-815fbe1b (tests of the post-run glossary audit), I-85a1e885 (a blank earlier means no earlier Issue in all three reviews, as you decided), I-13e0c56b (the panel keeps its settled findings without the issues part; raw earlier claims of unsettled Modules are dropped, in spec_review too).

Decisions I took without the developer (details in the decision log): brownfield tie-break = among groups whose providers are all described, the one whose first Module the scaffold lists first; for I-f95c7f1a, "ran checks" = the round's evidence holds check results; for I-82b9bb29 the new per-Module field is named `rejected` (code_review, spec_review) and per-worker `rejected` in the panel's reviews, while a chair's merged finding with a bad path turns its labels into rejections with the host's reason; a finding about an unreviewed Module is listed under the first reviewed Module; a run whose findings were rejected still ends ok. Contract versions bumped: contract.code-review.review 6, contract.spec-review.payload 7, contract.spec-review.panel-payload 6.

Open, escalation #1 (I-82b9bb29, second half): the resume round needs Workers to pass the round's worker result to the round validation, which only receives (worktree, round folder) today. That changes module.workers, outside this task's Modules.

- **task-session** task session (task fix-workflow-method-issues): `resume_needs_workers_change`
  I-82b9bb29's decision says a reviewer whose citations do not hold is resumed once through its round validation with the unresolved citations. Workers calls the round validation with only (worktree, round folder), never with the round's worker result, so Method cannot see the findings to check them. Everything else of I-82b9bb29 is done (33787991): a bad citation now drops only that finding, listed under rejected with the reason. What remains needs Workers to hand the round's validated worker result to the round validation as a third argument (a small additive change of module.workers' launch.md and workers.py), after which the reviews get one resume round whose repair lists the unresolved citations, and req.code-review.no-resume and code-review's "One pass" text change to allow it.
  Not handled here (decision): the change alters what module.workers promises its callers, a Module outside this task's Modules, and another fix task may be changing the worker harness
  Options: allow this task to make the additive Workers change and implement the resume round (about one more step); leave the resume round to a later task, deliver now with findings rejected alone; relaunch a fresh reviewer for the rejected findings instead of resuming (no Workers change, but a whole new context read)
  Recommendation: allow the additive Workers change in this task

Once answered I finish (or skip) the resume round, run task-validation and delivery, and report the delivery commit.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-03T06:32:37Z

Decided by the main agent: make the additive Workers change in this task. The round validation receives the round's validated worker result as a third argument; update module.workers' launch.md and workers.py, and every caller's round validation signature. Then implement the one resume round for unresolved citations and change req.code-review.no-resume and the 'One pass' text accordingly (spec_review likewise where it shares the rule). Reason: it is an additive change of an internal interface that changes no part direction, and fix-kernel-execution, the only other task in the worker harness, has merged. First merge the primary branch parts-split into your task branch: fix-coordination-distribution, fix-spec-root and fix-kernel-execution have merged since you started (fix-kernel-execution touched worker_harness/workers.py, method/registration.py and method/validation/command.py; fix-coordination-distribution touched prompts/guidance/issues/skill.md and prompts/guidance/workflows/skill.md, where your text wins on a conflict). Then run build --check, spec-validation and the full suite, task-validation and delivery, and report.

## Task session, after the answer to report 1 (2026-10-03)

- Merged parts-split into the task branch (55629708). Conflicts only in
  prompts/guidance/issues/skill.md and prompts/guidance/workflows/skill.md, resolved with this
  task's text as the answer said; tests/concorde/distribution/test_guidance_parts.py passes.
- Workers change as decided (d07c04d1): the round validation receives the round's validated
  worker result as its third argument (launch.md, workers.py); Method's step `validate` hook now
  takes that result; new scenario `scenario.workers.validation-reads-result`.
- I-82b9bb29 resume round (657dd461): code_review, spec_review and every spec_panel worker
  (reviewers, architects, chair) run with one resume round (`review_issues.CITATION_ROUNDS = 1`)
  whose validation answers a repair naming every citation that does not hold, with no failure, so
  whatever still does not hold after it is rejected alone as before. The repair asks for the whole
  result again, since the last round's result counts. The spec_review checker keeps no resume (it
  returns no paths). req.code-review.no-resume now allows only this resume; code-review's "One
  pass" text, step tables, spec-review/panel step tables and the review-code prompt say so. New
  scenarios `scenario.code-review.citation-resume`, `scenario.spec-review.citation-resume`.
- Restored tests/concorde/tasks/test_store.py to parts-split's version after `ruff format` had
  reformatted it (b3b59820): not this task's file.

## Report 2 to the main agent (项目架构分离建议), 2026-10-03T06:51:40Z

Report 2 of fix-workflow-method-issues (answers report 1): delivered as fd962bac3c25 on concorde/fix-workflow-method-issues; all 14 Issues on the task are fixed.

Since report 1:
- Merged parts-split (55629708). Conflicts only in prompts/guidance/issues/skill.md and prompts/guidance/workflows/skill.md, kept this task's text as you said; tests/concorde/distribution/test_guidance_parts.py passes.
- Workers change as decided (d07c04d1): the round validation receives the round's validated worker result as a third argument (launch.md, workers.py, every caller); Method's step `validate` hook now takes that result. New scenario scenario.workers.validation-reads-result.
- I-82b9bb29 resume round (657dd461): code_review, spec_review and every spec_panel worker (reviewers, architects, chair) get one resume round whose repair names every citation that does not hold and asks for the whole result again; whatever still does not hold is rejected alone, as before. The spec_review checker gets no resume, since its result names no paths. req.code-review.no-resume now allows only this resume; code-review's "One pass" text, the review step tables and the review-code prompt say so. New scenarios scenario.code-review.citation-resume and scenario.spec-review.citation-resume.
- b3b59820 puts back tests/concorde/tasks/test_store.py as parts-split has it, after ruff format had reformatted it; it is not this task's file.

Verified on the final input: build --check succeeded, spec-validation shows 0 errors and 0 warnings, the full suite passed (1059 passed, 5 skipped), task-validation says ready, and delivery ok.

Issues the merge resolves: I-c66d7124, I-60bd5fea, I-cfb021e5, I-3ad5326c, I-01f76edf, I-1b9c2a57, I-f95c7f1a, I-31e529e2, I-13e0c56b, I-5c805131, I-815fbe1b, I-5badf523, I-85a1e885, I-82b9bb29.

Decisions I took without the developer are listed in report 1 and in the decision log; the new ones are the resume details above (one round, a repair that asks for the whole result again, no resume for the checker). Nothing is open.

## Closed: merged, 2026-10-03T06:51:53Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit fd962bac3c255f6e1e9673dcfc21e00ef4cb1a1d into parts-split and closed it as merged. Nobody answers a report after that.
