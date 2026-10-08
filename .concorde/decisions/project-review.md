# Decision log: project-review

Goal: Add the project_review Operation: an unbound, read-only review of the whole project that runs deterministic project checks, one project-wide architecture review, a Spec panel of reviewers and chair per Module and a Module-scope code review per Module, skips Modules unchanged since their last review, reports findings as Issues and returns per-Module and project verdicts

## Task brief (main agent, 2026-10-07)

### Developer decisions this task carries out

The developer asked for a project-level review combining `spec_panel` and `code_review`, plus
whatever else is useful, and chose (2026-10-07):

1. **Form: an Operation `project_review`**, not a workflow. It runs **unbound** in the primary
   worktree (in its unbound checkout, like the other reading Operations) without a task, and may
   also run bound. It launches only reading workers and changes no Spec or code; it publishes
   Issues through the Issue store as the other reviews do (decision of 2026-10-02). It reuses the
   panel's and code review's host code (`spec_review/review.py`, `review_issues.py`, the panel
   graph, the code review brief) but never calls another Operation.
2. **Skip unchanged Modules.** A Module whose Specs (context identity) and code are unchanged since
   its last `project_review` is not reviewed again; its outcome comes from the Issues that stand.
   This needs a Git-tracked per-Module record of what was last judged (the developer's 2026-09-26
   "review memory" decision: tracked in Git, shared by every collaborator). A `--full` option forces
   a full review. The record must be written so an unbound run can publish it the way it publishes
   Issues (through a store commit under the merge lock), never by editing the examined checkout.
3. **Contents, all four extras chosen:**
   - **Project-wide architecture review once**: architects (default 2) plus a chair under
     `review-architecture` judge the whole project's architecture once. The per-Module panels in
     `project_review` have reviewers and chair but **no architects**.
   - **Per Module**: a Spec panel (reviewers + chair, defaults as `spec_panel`) and a Module-scope
     code review (`code_review --scope module` semantics).
   - **Every configured check** of every reviewed Module, through Check execution in its read-only
     check boundary; a failed check becomes a finding.
   - **Scenario test coverage**: scenarios no verification declaration names (deterministic).
   - **Unowned code**: implementation files bound to no Module (deterministic).
   - Whole-project `spec-validation` first; a structural error makes the affected Module
     `incomplete` as in the panel.
4. **Result**: per-Module outcome and verdict, one project verdict, and the Issues that stand
   summarized by severity and tier.

### Constraints and context

- `spec_review` was removed in task `remove-spec-review` (merged a0ad5a9e); `spec_panel` is the
  only Spec review Operation. Keep `spec_panel` and `code_review` working as they are.
- Cost matters: the project has 37 Modules. Run Modules' panels and code reviews in parallel with a
  concurrency limit rather than one after another; make the limit an argument with a sensible
  default. Give every worker its own worker id so `.concorde/workers.json` can configure each
  (e.g. `reviewer1..5`, `chair`, `architect1..2`, `arch_chair`, `code_reviewer` — naming is yours).
- Deterministic findings (coverage, unowned code, failed checks) are reported as Issues with a
  tier and severity the Spec states; choose sensible defaults and record them.
- Update the main-session guidance (`prompts/guidance/method/**`, the `concorde` skill sections on
  Unbound runs, Issues and Operations) and worker-id lists.

### Left for the session to decide

- Where the Operation lives: a new child Module of Method (e.g. `module.project-review`) or inside
  Spec review / Code review. A new Module is acceptable; create it with its Specs and registry
  entry.
- Exact arguments, output shape, contract versions, step table, the record's file format and
  location, default tier/severity of deterministic findings, the default concurrency.
- Whether to run a real live `project_review` on this checkout: allowed (model spend needs no
  permission), but at least run it on a small Module subset to observe it end to end, and record
  the run id and what you observed.

Escalate anything that would change what `spec_panel`, `code_review` or the Issue store promise to
their users. Deliver with `task-validation` then `delivery`; run the full suite once on the final
input.

## Task session: design decisions (2026-10-07)

Decided by the task session, within the task brief, without the developer:

1. **New Module `module.project-review`** ("Project review"), a child of Method, at
   `specs/concorde/method/project-review/`, code `src/concorde/method/project_review/`, tests
   `tests/concorde/project_review/`. Reason: the Operation composes Spec review and Code review
   and owns its own record and deterministic findings; putting it inside either would make one
   review Module own the other's work.
2. **Arguments**: `--modules` (default: every registered Module, bound or unbound), `--full`,
   `--parallel <1-8>` (Modules reviewed at once, default 4), `--reviewers <2-5>` (default 3),
   `--architects <0-2>` (default 2; 0 leaves the project-wide architecture review out).
   Worker ids: `reviewer1`…`reviewer5`, `chair`, `architect1`, `architect2`, `arch_chair`,
   `code_reviewer`.
3. **Skip rule**: per Module, the panel is skipped when the Module's `review-spec` context
   identity equals the recorded one; the code review is skipped when both its `review-code`
   context identity and the digest of its bound files' paths and bytes equal the recorded ones.
   The architecture review is skipped when the `review-architecture` context identity over every
   Module equals the recorded one. `--full` reviews everything. Skipping needs the issues part
   (a skipped Module's outcome comes from its standing Issues); without it nothing is skipped and
   no record is written. Reason: content identities make the record safe wherever it was judged,
   and splitting panel and code review lets a code-only change skip the panel.
4. **Record**: `.concorde/reviews/record.json` on the primary branch, one JSON file
   (`{schema_version, architecture, modules: {<id>: {panel, code_review}}}`), read from the
   primary worktree's last commit, published by the host under the merge lock as its own commit
   (`git commit --only`), refused while a task merge is unfinished (read through Tasks' task
   record contract, as Issues does) or while the file holds an uncommitted change. Only parts
   that completed and whose Issues were all written are recorded.
5. **Earlier Issues are shared with the standalone reviews by provenance phase**: project_review
   reports with `phase` `spec-panel`, `code-review`, `architecture`, `check`, `coverage`,
   `unowned`. `spec_panel`'s earlier Issues now also include project_review's `spec-panel` and
   `architecture` reports; `code_review`'s include project_review's `code-review` reports;
   project_review's per-Module panel reads `spec_panel` + `spec-panel`, its code review
   `code_review` + `code-review`, its architecture review only `architecture`. Their own reports
   keep phase `report`. Reason: otherwise a later spec_panel/code_review would report again what
   project_review recorded. This extends which Issues the two reviews offer as earlier; it changes
   no argument, output field or verdict rule of theirs. (Reported to the main agent.)
6. **Deterministic findings and their defaults**: a failed check `obvious-fix`/`high`, a timed-out
   check `decision-needed`/`medium` (one Issue per check, title by check id); scenarios no
   verification declaration names (Spec core's CONCORDE-COVERAGE-001 warnings) `obvious-fix`/
   `medium`, one Issue per Module; implementation files bound to no Module (tracked regular
   files outside Validation's accounted paths) `decision-needed`/`medium`, one Issue owned by the
   root Module. An open Issue of the same phase and title is appended to only when its text
   changed; one whose problem is gone is listed resolved, never closed.
7. **Checks run for every covered Module, skipped or not** (deterministic and cheap compared with
   the workers), so a skipped Module's tests still run.
8. **Outcome**: a Module is `incomplete` when a structural error, its panel or its code review
   stopped or its Issues could not be written; otherwise `changes_required` when an open
   review-made Issue (spec_panel, code_review or project_review) of a blocking tier stands for it
   after the run (minus those this run found resolved), else `accepted`. Project verdict: the
   highest Module outcome, `incomplete` too when the architecture review or a deterministic step
   could not complete.
9. **Thread safety**: `run_worker` gains an optional `records` list receiving the worker run
   record, so parallel code reviews no longer read the shared `ctx.worker`.
10. No `plan_review` run: the brief does not ask for one and the design follows the brief closely.

## Task session: implementation notes (2026-10-07)

- Report keys: within one run, a report of a phase other than `report` gets its key prefixed with
  the phase (`spec-panel/module.a/1`), since the first test run showed the store refusing the code
  review's `module.a/1` after the panel's (`issue_key_conflict`). Done centrally in
  `review_issues.report`; `spec_panel` and `code_review` keep their keys.
- Unowned files follow Validation's accounting rule for a changed path, so tracked symlinks count:
  on this checkout `.claude/skills/concorde` and `.claude/skills/concorde-development` are bound to
  no Module and will be one `decision-needed` Issue on `module.concorde`.
- Guidance: besides `prompts/guidance/method/**`, I added `project_review` to the lists in
  `prompts/guidance/execution/skill.md` (Unbound runs), `prompts/guidance/issues/skill.md` and
  `task-session.md` (reviews that report Issues) and `prompts/guidance/worker_harness/skill.md`
  (worker ids). These files belong to module.execution, module.issues and module.worker-harness,
  outside this task's Modules; I edited them because the task brief names exactly these sections,
  and each edit only adds `project_review` to an existing list.
- Spec review's and Code review's Specs now say which project_review phases count as earlier
  Issues, and that their host code serves one subject / one Module for Project review.
- tests/concorde/operations/test_catalog.py (module.operations) now lists project_review's provider; tests/concorde/main_session/test_guidance.py gains scenario.main-session.project-review. Added .concorde/checks/module.project-review.json running tests/concorde/project_review.

## Task session: live run 1 (2026-10-07)

`python3 scripts/concorde.py run project_review --modules module.project-review,module.scaffold
--architects 1 --reviewers 2`, bound in this task worktree: run
`r-20261006T193742-project_review-4cbffb26`, status `ok`, verdict `changes_required`, 10 worker
runs (architect1 + arch_chair on the whole project, reviewer1/2 + chair and code_reviewer per
Module), checks passed, 46 Issues stand (42 blocking), record committed on main as `794b8291`
(after the Issue commits). Deterministic: one unowned-file Issue on module.concorde
(`.claude/skills/*` symlinks), I-04b2460f56e15e09a2253c1831325d4a.

Observed: the Operation works end to end; the parallel panels and code reviews, the phases,
the key prefixes, the record commit and the standing summary all behave as designed. The reviews
found real problems in the new Module (33 Issues on module.project-review), 10 on module.scaffold,
and two on other Modules (I-98a4a639… on module.concorde, I-26297c83… on module.spec).

Three findings are conflicts with promises of other Modules, not mine to settle:
- I-5062a4e8… / I-2f1325fa…: the record commit is outside `req.execution.unbound-origin-untouched`,
  which lets an unbound run publish only Issues.
- I-b061cf15…: reading task records for an unfinished merge breaks `req.concorde.halves-apart`
  (no Operation reads a task record). I remove that read now, since a root requirement forbids it.
- I-98a4a639…: a fully skipped run launches no worker, against `req.concorde.operations-are-ai`.

## Task session: live run 2 and repairs (2026-10-07)

Commit d697ee74 repaired the first run's obvious/preferred findings (the task-record read removed,
leftover-record recovery, remembered resolutions, part-local setup failures, all deterministic
stops kept, Modules with unwritten deterministic problems incomplete, no false unowned resolution,
own coverage scan, covered-only standing in registry order, admission without the binding refusal,
Spec: work-stage checks, code digest, record handling, narrowed runs, providers declared).

Run 2: `project_review --modules module.project-review --architects 0 --reviewers 2`, run
`r-20261006T200244-project_review-9fa730ff`, `ok`, record commit `6b2736c0` on main. Its panel and
code reviewer resolved 12 earlier Issues (I-2293a17f, I-5570bd5d, I-982a7fd5, I-9bb314ac,
I-d67a4329, I-d83becc1, I-3bf12471, I-4abca839, I-a5327766, I-a808a1fc, I-b1596d99, I-b419f2d5),
appended to 7 and reported 2 new code findings. The next commit fixes those 9 (resolutions bound
to the offered revision, a refused revision lookup fails the record, the record checked on every
run, no-Issues fallback filtered, unwritten architecture findings make Modules incomplete, the code
digest defined in the record contract, scenario prerequisites).

## Escalated to the main agent, 2026-10-06T20:22:00Z

- **task-session** task session (task project-review): `record_outside_unbound_promise`
  project_review commits its review record .concorde/reviews/record.json on the primary branch under the merge lock, as the brief asks, but req.execution.unbound-origin-untouched lets an unbound run publish only Issues through the Issues store (Issues I-5062a4e82f3a52b8a0733511d521022a and I-2f1325faa4f45c8c9897a5fde725d8d0, decision-needed, high). The code and Project review's Spec already commit it; only Execution's requirement does not allow it.
  Not handled here (decision): the requirement belongs to module.execution, outside this task's Modules, and the developer chose the record's mechanism
  Options: widen req.execution.unbound-origin-untouched to the review record committed by project_review the same way as Issues (a follow-up task on module.execution); keep the record on a dedicated Git ref (refs/concorde/reviews) instead of a branch commit, which changes no worktree but needs explicit push/fetch to share; route the record through the Issues store
  Recommendation: widen Execution's requirement (option 1): it is the developer's 2026-10-07 direction and the Issues precedent; then close both Issues as resolved by that task

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "record_outside_unbound_promise",
  "detail": "project_review commits its review record .concorde/reviews/record.json on the primary branch under the merge lock, as the brief asks, but req.execution.unbound-origin-untouched lets an unbound run publish only Issues through the Issues store (Issues I-5062a4e82f3a52b8a0733511d521022a and I-2f1325faa4f45c8c9897a5fde725d8d0, decision-needed, high). The code and Project review's Spec already commit it; only Execution's requirement does not allow it.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the requirement belongs to module.execution, outside this task's Modules, and the developer chose the record's mechanism"
  },
  "options": [
    "widen req.execution.unbound-origin-untouched to the review record committed by project_review the same way as Issues (a follow-up task on module.execution)",
    "keep the record on a dedicated Git ref (refs/concorde/reviews) instead of a branch commit, which changes no worktree but needs explicit push/fetch to share",
    "route the record through the Issues store"
  ],
  "recommendation": "widen Execution's requirement (option 1): it is the developer's 2026-10-07 direction and the Issues precedent; then close both Issues as resolved by that task",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-06T20:22:01Z

- **task-session** task session (task project-review): `unfinished_merge_unguarded`
  Reading .concorde/tasks/*/task.json to refuse a record commit during an unfinished task merge broke req.concorde.halves-apart (Issue I-b061cf1528c45d2aa21ebb29ea17a961, decision-needed, high). I removed the read; the Spec now states the remaining risk: a record committed on top of a crashed, unfinished task merge keeps task merge --resume/--abort from finishing it (they refuse not_resumable). The run's own Issue writes still refuse an unfinished merge, which leaves those parts unrecorded.
  Not handled here (decision): how an Operation may learn of an unfinished merge without reading task records is a design question across Kernel, Tasks and Method
  Options: accept the documented risk; follow-up: the Kernel exposes an unfinished-merge marker that Tasks writes and any part may read, and the record honours it; publish the record through the Issues store, which already refuses during an unfinished merge
  Recommendation: accept the risk now (option 1) and open option 2 as a later task if the developer wants it; resolve I-b061 with this task, since the forbidden read is gone

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "unfinished_merge_unguarded",
  "detail": "Reading .concorde/tasks/*/task.json to refuse a record commit during an unfinished task merge broke req.concorde.halves-apart (Issue I-b061cf1528c45d2aa21ebb29ea17a961, decision-needed, high). I removed the read; the Spec now states the remaining risk: a record committed on top of a crashed, unfinished task merge keeps task merge --resume/--abort from finishing it (they refuse not_resumable). The run's own Issue writes still refuse an unfinished merge, which leaves those parts unrecorded.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "how an Operation may learn of an unfinished merge without reading task records is a design question across Kernel, Tasks and Method"
  },
  "options": [
    "accept the documented risk",
    "follow-up: the Kernel exposes an unfinished-merge marker that Tasks writes and any part may read, and the record honours it",
    "publish the record through the Issues store, which already refuses during an unfinished merge"
  ],
  "recommendation": "accept the risk now (option 1) and open option 2 as a later task if the developer wants it; resolve I-b061 with this task, since the forbidden read is gone",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-06T20:22:01Z

- **task-session** task session (task project-review): `skipped_run_launches_no_worker`
  A project_review run whose every Spec panel, code review and architecture review is skipped launches no worker, which req.concorde.operations-are-ai forbids for an Operation run that is not refused (Issue I-98a4a63901955d479af7655c270870ec on module.concorde, decision-needed, high). Such a run still runs the checks and returns outcomes from the standing Issues.
  Not handled here (decision): the requirement is the root Module's, outside this task
  Options: amend the root requirement: a run whose worker parts are all skipped because a record shows their inputs already judged is exempt; make project_review refuse with nothing_to_review when everything would be skipped; split the deterministic part into an execution command
  Recommendation: amend the root requirement (option 1) in a follow-up task on module.concorde; a fully skipped review is the cheap repeated review the developer asked for

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "skipped_run_launches_no_worker",
  "detail": "A project_review run whose every Spec panel, code review and architecture review is skipped launches no worker, which req.concorde.operations-are-ai forbids for an Operation run that is not refused (Issue I-98a4a63901955d479af7655c270870ec on module.concorde, decision-needed, high). Such a run still runs the checks and returns outcomes from the standing Issues.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the requirement is the root Module's, outside this task"
  },
  "options": [
    "amend the root requirement: a run whose worker parts are all skipped because a record shows their inputs already judged is exempt",
    "make project_review refuse with nothing_to_review when everything would be skipped",
    "split the deterministic part into an execution command"
  ],
  "recommendation": "amend the root requirement (option 1) in a follow-up task on module.concorde; a fully skipped review is the cheap repeated review the developer asked for",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-06T20:22:01Z

- **task-session** task session (task project-review): `code_skip_scope`
  The code review is skipped when the Module's review-code context identity and the digest of its own bound files are unchanged, as the brief says. Reviewers ask whether a change of other Modules' code, which a code reviewer may read, should also make it run again (Issues I-5d33c8921e4e5b08b2270ce3281f3ab8 and I-5570bd5d427e5f3aa80841d118b3d84f, decision-needed, high; the run-3 panel found I-5570 resolved by the Spec's explicit statement).
  Not handled here (decision): it changes what the skip promises, which the developer set
  Options: keep: only the Module's own code and Specs decide; each other Module's change is judged by its own code review; add the code of every Module it uses to the digest, which reviews many more Modules again
  Recommendation: keep (option 1), as the Spec now says; close I-5d33 as not-actionable and resolve I-5570

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "code_skip_scope",
  "detail": "The code review is skipped when the Module's review-code context identity and the digest of its own bound files are unchanged, as the brief says. Reviewers ask whether a change of other Modules' code, which a code reviewer may read, should also make it run again (Issues I-5d33c8921e4e5b08b2270ce3281f3ab8 and I-5570bd5d427e5f3aa80841d118b3d84f, decision-needed, high; the run-3 panel found I-5570 resolved by the Spec's explicit statement).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "it changes what the skip promises, which the developer set"
  },
  "options": [
    "keep: only the Module's own code and Specs decide; each other Module's change is judged by its own code review",
    "add the code of every Module it uses to the digest, which reviews many more Modules again"
  ],
  "recommendation": "keep (option 1), as the Spec now says; close I-5d33 as not-actionable and resolve I-5570",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-06T20:22:01Z

- **task-session** task session (task project-review): `checks_work_stage`
  project_review runs the configured checks of the work stage, so a check marked "when": "readiness" does not run (Issue I-49a53a5fec0f59b0b3343064188cc0e2, decision-needed, medium). The Spec now says so.
  Not handled here (decision): running readiness-only checks would change Check execution's caller rule, outside this task
  Options: keep the work stage, as the Spec now says; let project_review pass the readiness stage, changing Check execution's rule
  Recommendation: keep (option 1) and close the Issue as resolved by this task

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "checks_work_stage",
  "detail": "project_review runs the configured checks of the work stage, so a check marked \"when\": \"readiness\" does not run (Issue I-49a53a5fec0f59b0b3343064188cc0e2, decision-needed, medium). The Spec now says so.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "running readiness-only checks would change Check execution's caller rule, outside this task"
  },
  "options": [
    "keep the work stage, as the Spec now says",
    "let project_review pass the readiness stage, changing Check execution's rule"
  ],
  "recommendation": "keep (option 1) and close the Issue as resolved by this task",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-06T20:22:01Z

- **task-session** task session (task project-review): `narrowed_verdict`
  With --modules, the verdict and the standing counts cover the named Modules only; an architecture finding about another Module stands for that Module and counts in the next run that covers it (Issues I-038e543918bd528cb12cb7a062c374db and I-9bb314ac6b8b5264a25fbeeafb88c505, decision-needed, medium; runs 2 and 3 found I-9bb3 resolved by the Spec).
  Not handled here (decision): it decides what a narrowed review's verdict means
  Options: keep: the verdict covers the named Modules; fold every architecture finding of the run into the verdict
  Recommendation: keep (option 1) and resolve both with this task

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "narrowed_verdict",
  "detail": "With --modules, the verdict and the standing counts cover the named Modules only; an architecture finding about another Module stands for that Module and counts in the next run that covers it (Issues I-038e543918bd528cb12cb7a062c374db and I-9bb314ac6b8b5264a25fbeeafb88c505, decision-needed, medium; runs 2 and 3 found I-9bb3 resolved by the Spec).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "it decides what a narrowed review's verdict means"
  },
  "options": [
    "keep: the verdict covers the named Modules",
    "fold every architecture finding of the run into the verdict"
  ],
  "recommendation": "keep (option 1) and resolve both with this task",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-06T20:22:02Z

- **task-session** task session (task project-review): `architecture_reuse`
  The architecture review offers only project_review's architecture-phase Issues as earlier Issues; spec_panel's architect findings cannot be told from its reviewer findings, since spec_panel reports all with phase report (Issues I-9f9902322d5c5c57ab7e8541f7605c15 decision-needed and I-8e98340f44ab5752a2fe699600151d5b preferred-fix, medium). The Spec documents the limitation; duplicates between spec_panel's architects and project_review's architecture review are possible.
  Not handled here (decision): the fix changes the provenance spec_panel promises for its reports
  Options: accept the documented limitation; spec_panel reports its architects' merged findings with phase architecture (a change of spec_panel's report provenance), so that project_review offers them
  Recommendation: option 2 in a follow-up task on module.spec-review; keep both Issues open until then

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "architecture_reuse",
  "detail": "The architecture review offers only project_review's architecture-phase Issues as earlier Issues; spec_panel's architect findings cannot be told from its reviewer findings, since spec_panel reports all with phase report (Issues I-9f9902322d5c5c57ab7e8541f7605c15 decision-needed and I-8e98340f44ab5752a2fe699600151d5b preferred-fix, medium). The Spec documents the limitation; duplicates between spec_panel's architects and project_review's architecture review are possible.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the fix changes the provenance spec_panel promises for its reports"
  },
  "options": [
    "accept the documented limitation",
    "spec_panel reports its architects' merged findings with phase architecture (a change of spec_panel's report provenance), so that project_review offers them"
  ],
  "recommendation": "option 2 in a follow-up task on module.spec-review; keep both Issues open until then",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-06T20:22:02Z

- **task-session** task session (task project-review): `record_invalid_handling`
  A committed review record that is not valid makes the run skip nothing and end failed with record_unpublished (record_invalid); a valid record an interrupted write left uncommitted is put back; any other uncommitted change is refused (Issue I-2293a17feffd59119713a5d6673f12fd, decision-needed, medium; runs 2 and 3 found it resolved by the Spec).
  Not handled here (decision): the tier is decision-needed, which a task session never settles
  Options: keep this handling; repair an invalid record automatically
  Recommendation: keep (option 1) and resolve the Issue with this task

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "record_invalid_handling",
  "detail": "A committed review record that is not valid makes the run skip nothing and end failed with record_unpublished (record_invalid); a valid record an interrupted write left uncommitted is put back; any other uncommitted change is refused (Issue I-2293a17feffd59119713a5d6673f12fd, decision-needed, medium; runs 2 and 3 found it resolved by the Spec).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the tier is decision-needed, which a task session never settles"
  },
  "options": [
    "keep this handling",
    "repair an invalid record automatically"
  ],
  "recommendation": "keep (option 1) and resolve the Issue with this task",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-06T20:22:02Z

- **task-session** task session (task project-review): `code_digest_definition`
  contract.project-review.record now defines the code digest exactly: [path, sha256 of bytes] pairs of every existing regular bound file in path order, as the Kernel's canonical JSON (Python json.dumps with sort_keys, compact separators, ensure_ascii), digested as UTF-8, with two worked examples including a non-ASCII path, tested (Issue I-f89db32a64ee587dbf62339d81bd9c72, decision-needed, medium).
  Not handled here (decision): the tier is decision-needed, which a task session never settles
  Options: accept this definition; define the digest through a Spec core or Kernel contract instead
  Recommendation: accept (option 1) and resolve the Issue with this task

```json
{
  "level": "task-session",
  "actor": "task session (task project-review)",
  "code": "code_digest_definition",
  "detail": "contract.project-review.record now defines the code digest exactly: [path, sha256 of bytes] pairs of every existing regular bound file in path order, as the Kernel's canonical JSON (Python json.dumps with sort_keys, compact separators, ensure_ascii), digested as UTF-8, with two worked examples including a non-ASCII path, tested (Issue I-f89db32a64ee587dbf62339d81bd9c72, decision-needed, medium).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the tier is decision-needed, which a task session never settles"
  },
  "options": [
    "accept this definition",
    "define the digest through a Spec core or Kernel contract instead"
  ],
  "recommendation": "accept (option 1) and resolve the Issue with this task",
  "causes": []
}
```

## Task session: live run 3, Issues and escalations (2026-10-07)

Run 3: `project_review --modules module.project-review --architects 0 --reviewers 2`, run
`r-20261006T201155-project_review-dee010b9`, `ok`; the code reviewer found every earlier code
Issue resolved and reported nothing new; the panel resolved 7 more and appended 5 Spec wording
findings, which commit a4d2acf1 fixes (one revision rule for every resolution, the code digest's
serialization with a non-ASCII example, split no-Issues rules, title-based deterministic
resolution, scenario prerequisites and ordering). I stopped the live-review loop there: further
rounds were finding only finer wording on the same points.

Full suite on a4d2acf1: 1284 passed, 5 skipped.

Resolved through the task (`task resolve`), the obvious-fix/preferred-fix Issues this task fixed:
I-148d8bf7, I-2b2ca389, I-3586a10d, I-3bf12471, I-3fd5bc7d, I-4abca839, I-4fcdb149, I-64973138,
I-7116eb0a, I-73886020, I-7fad87eb, I-8c74b95c, I-982a7fd5, I-a5327766, I-a808a1fc, I-b1596d99,
I-b3e1467a, I-b419f2d5, I-bc477d40, I-d67a4329, I-d83becc1, I-df86fa6a, I-f84119e0.
Left open: I-8e98340f (preferred-fix, needs a spec_panel provenance change, escalated with
I-9f990232), I-983bb766 (suggestion), the decision-needed Issues below, and the Issues the review
filed on other Modules (10 on module.scaffold, I-26297c83 on module.spec, I-04b2460f unowned
`.claude/skills/*` on module.concorde, I-98a4a639 on module.concorde).

Escalations 1-9 recorded with `task escalate`: record vs Execution's unbound promise; the
unfinished-merge guard without task records; a fully skipped run vs req.concorde.operations-are-ai;
code-review skip scope; work-stage checks; narrowed verdict; architecture reuse of spec_panel
Issues; invalid-record handling; the code digest definition.

## Report 1 to the main agent (concorde-d4), 2026-10-06T20:39:18Z

project-review delivered: delivery commit 2f3b128d on concorde/project-review (task-validation ready; full suite 1284 passed, 5 skipped; spec-validation 0 errors, 12 pre-existing warnings).

What it adds: new child Module module.project-review (specs/concorde/method/project-review/, src/concorde/method/project_review/, tests/concorde/project_review/, prompts/workers/project-architecture.md, check check.project-review.tests). `concorde run project_review [--modules] [--full] [--parallel 1-8, default 4] [--reviewers 2-5] [--architects 0-2]`, unbound or bound, covers every registered Module by default: project spec-validation, work-stage checks of every covered Module, uncovered scenarios, tracked files bound to no Module, one project-wide architecture review (architect1/2 + arch_chair), and per Module a Spec panel without architects (reviewer1-5 + chair) and a Module-scope code review (code_reviewer), in parallel. Each part is skipped when its content identity equals the review record .concorde/reviews/record.json, committed alone on the primary branch under the merge lock; a skipped part keeps the resolutions it last found (bound to the Issue revision offered). Outcomes come from the open review-made Issues that stand; the result counts them by severity and tier. Reports carry provenance phases (spec-panel, code-review, architecture, check, coverage, unowned).

Decisions I took (details in the decision log): the new Module; arguments and worker ids; deterministic grades (failed check obvious-fix/high, timeout decision-needed/medium, uncovered scenarios obvious-fix/medium, unowned files decision-needed/medium on the root Module); checks run on every run; spec_panel's earlier Issues now include project_review's spec-panel and architecture reports, code_review's include its code-review reports (extension only, no output or verdict change); report keys of a non-`report` phase are prefixed with the phase; run_worker gains a `records` list; I edited the guidance lists in prompts/guidance/execution, issues and worker_harness and tests/concorde/operations/test_catalog.py (other Modules' files) because the brief named those sections.

Live runs: run 1 r-20261006T193742-project_review-4cbffb26 (module.project-review + module.scaffold, 1 architect): ok, 10 workers, 46 Issues, record commit 794b8291 on main. Runs 2 (r-20261006T200244-…-9fa730ff) and 3 (r-20261006T201155-…-dee010b9) on module.project-review alone settled the earlier Issues; I fixed what they found. Note: these runs committed Issues and the record (794b8291, 6b2736c0 and run 3's) on main, as Issue writes do. I resolved 23 obvious/preferred Issues through the task (task resolve); the merge closes them. Still open from the review: 10 Issues on module.scaffold (one critical: I-468535e4 planning can overwrite concurrent edits), I-26297c83 on module.spec, I-04b2460f (.claude/skills/* symlinks tracked but bound to no Module, module.concorde), I-8e98340f and I-983bb766 on module.project-review.

Escalations needing your answer (all recorded, numbers 1-9; recommendations in each):
1 the record commit is outside req.execution.unbound-origin-untouched (only Issues allowed) — recommend widening Execution's requirement in a follow-up task.
2 the unfinished-merge guard needed a task-record read, which req.concorde.halves-apart forbids; I removed it — recommend accepting the documented risk (a record committed on a crashed unfinished merge blocks --resume/--abort), optionally a Kernel marker later.
3 a fully skipped run launches no worker, against req.concorde.operations-are-ai (I-98a4a639, module.concorde) — recommend amending the root requirement.
4 code-review skip uses only the Module's own code and Specs (per brief) — recommend keep.
5 readiness-only checks are not run (work stage) — recommend keep.
6 with --modules the verdict covers only the named Modules — recommend keep.
7 architecture review cannot reuse spec_panel's architect Issues — recommend a follow-up where spec_panel reports architect findings with phase architecture.
8 invalid-record handling as specified — recommend keep.
9 the code digest definition in the record contract — recommend accept.
Worker models: project_review's workers use the default model unless .concorde/workers.json configures operations.project_review (you may want to mirror spec_panel's choices).

It carries escalation(s) 1, 2, 3, 4, 5, 6, 7, 8, 9.

## Escalated to the developer, 2026-10-06T20:40:08Z

- **main-agent** main agent (task project-review): `project_review_promise_conflicts`
  project_review is delivered (2f3b128d) and works end to end in three live runs. Three of its behaviours conflict with earlier developer decisions or root requirements: (1) its review record commit on the primary branch goes beyond the 2026-10-02 decision that an unbound run may publish only Issues; (2) without reading task records it cannot see an unfinished task merge, so a record commit on top of a crashed merge would make task merge --resume/--abort refuse until fixed by hand; (3) a run whose every worker part is skipped launches no worker, against the rule that an Operation involves an AI worker. Escalations 4-9 the main agent settles itself.
  Not handled here (decision): each changes a promise of the root Module or of Execution, or contradicts an earlier developer decision
  Options: 1: widen req.execution.unbound-origin-untouched to the review record (follow-up task); 2: accept the documented risk now; a Kernel unfinished-merge marker later; 3: amend req.concorde.operations-are-ai so a run whose worker parts are all skipped by the record is exempt
  Recommendation: options as listed for all three; each as a small follow-up task after merging project-review
  Caused by:
  - **task-session** task session (task project-review): `record_outside_unbound_promise`
    project_review commits its review record .concorde/reviews/record.json on the primary branch under the merge lock, as the brief asks, but req.execution.unbound-origin-untouched lets an unbound run publish only Issues through the Issues store (Issues I-5062a4e82f3a52b8a0733511d521022a and I-2f1325faa4f45c8c9897a5fde725d8d0, decision-needed, high). The code and Project review's Spec already commit it; only Execution's requirement does not allow it.
    Not handled here (decision): the requirement belongs to module.execution, outside this task's Modules, and the developer chose the record's mechanism
    Options: widen req.execution.unbound-origin-untouched to the review record committed by project_review the same way as Issues (a follow-up task on module.execution); keep the record on a dedicated Git ref (refs/concorde/reviews) instead of a branch commit, which changes no worktree but needs explicit push/fetch to share; route the record through the Issues store
    Recommendation: widen Execution's requirement (option 1): it is the developer's 2026-10-07 direction and the Issues precedent; then close both Issues as resolved by that task
  Caused by:
  - **task-session** task session (task project-review): `unfinished_merge_unguarded`
    Reading .concorde/tasks/*/task.json to refuse a record commit during an unfinished task merge broke req.concorde.halves-apart (Issue I-b061cf1528c45d2aa21ebb29ea17a961, decision-needed, high). I removed the read; the Spec now states the remaining risk: a record committed on top of a crashed, unfinished task merge keeps task merge --resume/--abort from finishing it (they refuse not_resumable). The run's own Issue writes still refuse an unfinished merge, which leaves those parts unrecorded.
    Not handled here (decision): how an Operation may learn of an unfinished merge without reading task records is a design question across Kernel, Tasks and Method
    Options: accept the documented risk; follow-up: the Kernel exposes an unfinished-merge marker that Tasks writes and any part may read, and the record honours it; publish the record through the Issues store, which already refuses during an unfinished merge
    Recommendation: accept the risk now (option 1) and open option 2 as a later task if the developer wants it; resolve I-b061 with this task, since the forbidden read is gone
  Caused by:
  - **task-session** task session (task project-review): `skipped_run_launches_no_worker`
    A project_review run whose every Spec panel, code review and architecture review is skipped launches no worker, which req.concorde.operations-are-ai forbids for an Operation run that is not refused (Issue I-98a4a63901955d479af7655c270870ec on module.concorde, decision-needed, high). Such a run still runs the checks and returns outcomes from the standing Issues.
    Not handled here (decision): the requirement is the root Module's, outside this task
    Options: amend the root requirement: a run whose worker parts are all skipped because a record shows their inputs already judged is exempt; make project_review refuse with nothing_to_review when everything would be skipped; split the deterministic part into an execution command
    Recommendation: amend the root requirement (option 1) in a follow-up task on module.concorde; a fully skipped review is the cheap repeated review the developer asked for

```json
{
  "level": "main-agent",
  "actor": "main agent (task project-review)",
  "code": "project_review_promise_conflicts",
  "detail": "project_review is delivered (2f3b128d) and works end to end in three live runs. Three of its behaviours conflict with earlier developer decisions or root requirements: (1) its review record commit on the primary branch goes beyond the 2026-10-02 decision that an unbound run may publish only Issues; (2) without reading task records it cannot see an unfinished task merge, so a record commit on top of a crashed merge would make task merge --resume/--abort refuse until fixed by hand; (3) a run whose every worker part is skipped launches no worker, against the rule that an Operation involves an AI worker. Escalations 4-9 the main agent settles itself.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "each changes a promise of the root Module or of Execution, or contradicts an earlier developer decision"
  },
  "options": [
    "1: widen req.execution.unbound-origin-untouched to the review record (follow-up task)",
    "2: accept the documented risk now; a Kernel unfinished-merge marker later",
    "3: amend req.concorde.operations-are-ai so a run whose worker parts are all skipped by the record is exempt"
  ],
  "recommendation": "options as listed for all three; each as a small follow-up task after merging project-review",
  "causes": [
    {
      "actor": "task session (task project-review)",
      "attempts": [],
      "causes": [],
      "code": "record_outside_unbound_promise",
      "detail": "project_review commits its review record .concorde/reviews/record.json on the primary branch under the merge lock, as the brief asks, but req.execution.unbound-origin-untouched lets an unbound run publish only Issues through the Issues store (Issues I-5062a4e82f3a52b8a0733511d521022a and I-2f1325faa4f45c8c9897a5fde725d8d0, decision-needed, high). The code and Project review's Spec already commit it; only Execution's requirement does not allow it.",
      "evidence": [],
      "level": "task-session",
      "options": [
        "widen req.execution.unbound-origin-untouched to the review record committed by project_review the same way as Issues (a follow-up task on module.execution)",
        "keep the record on a dedicated Git ref (refs/concorde/reviews) instead of a branch commit, which changes no worktree but needs explicit push/fetch to share",
        "route the record through the Issues store"
      ],
      "recommendation": "widen Execution's requirement (option 1): it is the developer's 2026-10-07 direction and the Issues precedent; then close both Issues as resolved by that task",
      "unhandled": {
        "explanation": "the requirement belongs to module.execution, outside this task's Modules, and the developer chose the record's mechanism",
        "reason": "decision"
      }
    },
    {
      "actor": "task session (task project-review)",
      "attempts": [],
      "causes": [],
      "code": "unfinished_merge_unguarded",
      "detail": "Reading .concorde/tasks/*/task.json to refuse a record commit during an unfinished task merge broke req.concorde.halves-apart (Issue I-b061cf1528c45d2aa21ebb29ea17a961, decision-needed, high). I removed the read; the Spec now states the remaining risk: a record committed on top of a crashed, unfinished task merge keeps task merge --resume/--abort from finishing it (they refuse not_resumable). The run's own Issue writes still refuse an unfinished merge, which leaves those parts unrecorded.",
      "evidence": [],
      "level": "task-session",
      "options": [
        "accept the documented risk",
        "follow-up: the Kernel exposes an unfinished-merge marker that Tasks writes and any part may read, and the record honours it",
        "publish the record through the Issues store, which already refuses during an unfinished merge"
      ],
      "recommendation": "accept the risk now (option 1) and open option 2 as a later task if the developer wants it; resolve I-b061 with this task, since the forbidden read is gone",
      "unhandled": {
        "explanation": "how an Operation may learn of an unfinished merge without reading task records is a design question across Kernel, Tasks and Method",
        "reason": "decision"
      }
    },
    {
      "actor": "task session (task project-review)",
      "attempts": [],
      "causes": [],
      "code": "skipped_run_launches_no_worker",
      "detail": "A project_review run whose every Spec panel, code review and architecture review is skipped launches no worker, which req.concorde.operations-are-ai forbids for an Operation run that is not refused (Issue I-98a4a63901955d479af7655c270870ec on module.concorde, decision-needed, high). Such a run still runs the checks and returns outcomes from the standing Issues.",
      "evidence": [],
      "level": "task-session",
      "options": [
        "amend the root requirement: a run whose worker parts are all skipped because a record shows their inputs already judged is exempt",
        "make project_review refuse with nothing_to_review when everything would be skipped",
        "split the deterministic part into an execution command"
      ],
      "recommendation": "amend the root requirement (option 1) in a follow-up task on module.concorde; a fully skipped review is the cheap repeated review the developer asked for",
      "unhandled": {
        "explanation": "the requirement is the root Module's, outside this task",
        "reason": "decision"
      }
    }
  ]
}
```

## Answer to report(s) 1 of the task session, 2026-10-08T01:02:44Z

Answers to report 1 and escalations 1-9 (developer settled 1-3 on 2026-10-08; the main agent settled 4-9):

1. record_outside_unbound_promise (developer): widen req.execution.unbound-origin-untouched so an unbound run may also publish project_review's review record, committed like Issues (its own commit under the merge lock), and qualify the root's "changes nothing" the same way if it names only Issues. Do it in THIS task (an edit of module.execution's requirement and any scenario that states it); then resolve I-5062a4e8 and I-2f1325fa through the task.
2. unfinished_merge_unguarded (developer): accept the documented risk now. Resolve I-b061cf15 through the task (the forbidden read is gone). Report a new Issue on module.kernel, tier decision-needed, severity medium: a Kernel unfinished-merge marker that Tasks writes and any part may read, so the review record (and other non-Issue commits) can refuse during an unfinished merge. Not built in this task.
3. skipped_run_launches_no_worker (developer, NOT the recommended option): project_review refuses with code `nothing_to_review` when, after applying the record, every worker part (every Module's panel and code review and the architecture review) would be skipped. The refusal happens before any step: it runs no check, no coverage or unowned scan, writes no Issue and no record. Its link says every covered part was already judged and names `--full` as the way to review anyway. Keep req.concorde.operations-are-ai unchanged. Update Project review's Spec (requirement, scenario, step table, result/refusal list), code, tests and guidance accordingly; resolve I-98a4a639 through the task.
4. code_skip_scope (main agent): keep option 1, only the Module's own code and Specs decide. Close I-5d33c892 as not-actionable with that reason; resolve I-5570bd5d through the task.
5. checks_work_stage (main agent): keep the work stage. Resolve I-49a53a5f through the task.
6. narrowed_verdict (main agent): keep, the verdict covers the named Modules. Resolve I-038e5439 and I-9bb314ac through the task.
7. architecture_reuse (main agent): option 2, but as a follow-up task on module.spec-review after this merges (spec_panel reports architect findings with phase architecture). Keep I-9f990232 and I-8e98340f open for that task.
8. record_invalid_handling (main agent): keep. Resolve I-2293a17f through the task.
9. code_digest_definition (main agent): accept. Resolve I-f89db32a through the task.

Then verify (build, spec-validation, full suite), task-validation, delivery, and report.

## Task session: acting on the answer to report 1 (2026-10-08)

Commit 3d15110b "Refuse a project_review with nothing to review; let unbound runs publish the record":

- Escalation 1: `req.execution.unbound-origin-untouched` and its explanations in
  `specs/concorde/execution/requirements.md`, `execution/module.md` and the root `module.md` now
  name project_review's review record beside the Issues, committed alone under the merge lock. No
  Execution scenario stated the Issues-only rule, so none changed.
- Escalation 3: decided by the task session, the refusal lives in project_review's admission,
  raised as Execution's `Refused`, so the run is `failed` with `refused` evidence and a
  `nothing_to_review` cause, and no step runs (not even Method's worker admission). The admission
  therefore does step 2's work (validation, identities, record, skips) and the `prepare` step
  returns what it found. Reason: the answer asks for a refusal before any step, and an admission
  refusal is the one shape `req.concorde.operations-are-ai` exempts and every other refusal uses.
  "Every worker part" is each covered Module's Spec panel and code review plus the architecture
  review unless `--architects 0` leaves it out; a part `not_run` for a structural error or a grant
  failure is not skipped, so such a run is not refused and still reports the error. New
  requirement `req.project-review.nothing-to-review`, scenario
  `scenario.project-review.nothing-to-review`; `scenario.project-review.skips-unchanged` now
  changes one Module's code so that one code review runs; the step table, "Running", "Why" and the
  method guidance say it. Tests that relied on a fully skipped run now change module.b's code first.
- Issues: resolved through the task I-5062a4e8, I-2f1325fa, I-b061cf15, I-98a4a639, I-5570bd5d,
  I-49a53a5f, I-038e5439, I-9bb314ac, I-2293a17f, I-f89db32a; closed I-5d33c892 as not-actionable
  with the main agent's reason; reported I-147773efe0985a81bc13ccef3568ca51 on module.kernel
  (decision-needed, medium): an unfinished-merge marker any part may read. I-9f990232 and
  I-8e98340f stay open for the follow-up task.

## Report 2 to the main agent (concorde-d4), 2026-10-08T01:28:26Z

project-review delivered again: delivery commit 99f384bb on concorde/project-review (over 3d15110b). Checks: task-validation r-20261008T011119-task_validation-52a96a4e ready with no blocking findings; delivery r-20261008T011941-delivery-496604bd ok; full suite 1285 passed, 5 skipped; spec-validation 0 errors and the same 12 warnings as before; build --check clean.

Acted on the answer to report 1:
1. req.execution.unbound-origin-untouched now lets an unbound run publish project_review's review record (.concorde/reviews/record.json) as well as Issues. The record is committed alone on the primary branch under the merge lock. Execution's module.md and the root module.md ("its only possible lasting changes") say the same. No Execution scenario stated the Issues-only rule, so no scenario changed.
2. Accepted risk is unchanged in the Spec. New Issue I-147773efe0985a81bc13ccef3568ca51 on module.kernel (decision-needed, medium) proposes an unfinished-merge marker that any part may read.
3. project_review now refuses with `nothing_to_review` when every covered Module's Spec panel and code review would be skipped, plus the architecture review unless `--architects 0` leaves it out. req.concorde.operations-are-ai is unchanged. The refusal is in the Operation's admission (Execution's Refused): status failed, `refused` evidence, a cause with code nothing_to_review whose detail names --full, and no step runs. So it runs no checks, no coverage or unowned scan, and writes no Issue and no record.
   - Decision I took: the admission now does step 2's work (validation, identities, record, skip decisions), and the prepare step returns what it found. A part not run because of a structural error or a grant failure does not count as skipped, so such a run is not refused and still reports the error.
   - Spec: new req.project-review.nothing-to-review and scenario.project-review.nothing-to-review. skips-unchanged now changes one Module's code, so only that Module's code review runs. The checks, coverage and unowned requirements now say "every run it does not refuse". The step table, "Running", "Why" and the method guidance are updated. Tests are updated to match.
4-9. Resolved through the task: I-5062a4e8, I-2f1325fa, I-b061cf15, I-98a4a639, I-5570bd5d, I-49a53a5f, I-038e5439, I-9bb314ac, I-2293a17f, I-f89db32a. Closed I-5d33c892 as not-actionable with your reason. I-9f990232 and I-8e98340f stay open for the spec-review follow-up.

The task now resolves 33 Issues, which the merge closes. Still open, all outside this task: 10 on module.scaffold (I-468535e4 is critical), I-26297c83 (module.spec), I-04b2460f (module.concorde, unowned .claude/skills symlinks), I-983bb766 (suggestion), I-9f990232, I-8e98340f, and the new I-14777 on module.kernel. Nothing escalated. Ready to merge.

## Closed: merged, 2026-10-08T01:28:36Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 99f384bb5dfe5df0ad521391ceb721798979f603 into main and closed it as merged. Nobody answers a report after that.
