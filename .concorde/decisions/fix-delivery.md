# Decision log: fix-delivery

Goal: Fix every open Issue of Delivery found by the first full project_review, first the critical one: staging can commit content that readiness never validated

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) to fix the project's known open Issues. This task resolves every
open Issue owned by its Modules (listed in the task record's `resolves`), found by the first full
project_review, r-20261008T024839-project_review-a7857ff6 (unbound). Read each with
`concorde issues show`; the review's panel and code-review reports are in
`.concorde/unbound/r-20261008T024839-project_review-a7857ff6/` of the primary worktree.

How to handle them, by tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest while
  waiting. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it turns out wrong; then leave it open and say why in the log.
- Fix by **severity**, critical and high first.
- An Issue that turns out not to hold, or that is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix that needs a change outside the task's Modules: escalate it rather than widening the task,
  unless it is a small mechanical follow-on (a link, a test fixture).

Other tasks running in parallel: worker-transient-retry (workers, project-review, method),
main-rename-hook (main-session, coordination, tasks) and the other Issue-fixing tasks of today
(views, dogfood/e2e, task-session, operations/commands, delivery). Deliver with `task-validation`
then `delivery`; run the full suite once on the final input.

## Task session decisions (2026-10-08)

- No Issue of the task is `decision-needed`; nothing escalated. All four hold at the base
  5fe565a4: each new regression in `tests/concorde/delivery/test_delivery.py` fails on the old
  `command.py` (4 failed) and passes on the fix.
- **I-95b5d191 (critical, preferred-fix)**: chosen fix — after `git write-tree`, compare the staged
  tree with the readiness measurement: each examined path must be staged with its mode and, passed
  through the smudge filters a checkout applies (`git cat-file --filters`), the digest readiness
  recorded; every other path must be staged as the base holds it (`git diff-tree base staged`).
  Mismatch: `failed`, new code `staged_unvalidated`, reason `decision`, index given back as
  req.delivery.atomic requires. Why checkout semantics rather than raw blob equality: raw equality
  would refuse every Git LFS or line-ending-converting repository although a checkout gives back
  the validated bytes; a clean filter that rewrites content (the Issue's case) is still refused.
  The executable bit is ignored when `core.fileMode` is false, as Git ignores it. Raw blobs are read
  in one `cat-file --batch`; the filtered read runs per path only when the raw digest differs.
  Spec: new req.delivery.staged-validated, scenarios staged-unvalidated and staged-filtered, step 9
  and the result table in module.md, one sentence in contracts.md.
- **I-4c792555 (high, preferred-fix)**: scenario sections now come from Spec core's
  `parse_reading` (levels 2–5, fences excluded); a section runs to the next heading outside a fence.
  Only scenarios Spec core registers for that document count, so a non-Spec `.md` cannot add ids.
- **I-7c6c648e (high, preferred-fix)**: verified scenarios are now the declarations
  `scan_declarations` reads from every Module's bound files, not the CONCORDE-COVERAGE-001 warnings
  (which skip Modules without files). Spec: req.delivery.scenarios-verified says the rule holds
  whichever Module owns the scenario; new scenario.delivery.unrealized-scenarios.
- **I-52fe4d34 (medium, obvious-fix)**: the gate decodes each recorded path with `real_path`
  before realization matching and Git/file access; messages show the recorded form.
- Commit 370312a0 on concorde/fix-delivery.
- Non-ok result: delivery run r-20261008T063747-delivery-9a1d44da ended `blocked`, `not_ready`,
  its only blocking finding check.tasks.tests: the known teardown race of
  test_a_run_waiting_for_a_closing_tasks_workspace_is_refused_outside_it (OSError Errno 39 on
  `.concorde`). Not caused by this task (it touches only Delivery); task-validation passed on the
  same input, the full suite passed, the test alone passed 6/6. Appended this observation to the
  open Issue I-067df4e5 (module.tasks, now medium: it can block an unrelated delivery) and ran
  delivery again unchanged.

## Report 1 to the main agent (Review流程), 2026-10-08T07:00:25Z

fix-delivery delivered: delivery commit 347790ca677f91352452d0eaee72c4649d436d09 on concorde/fix-delivery (run r-20261008T065129-delivery-7df650be, ok), on top of the fix step 370312a0. Resolves all four Issues on the task (already in `resolves`): I-95b5d191, I-4c792555, I-7c6c648e, I-52fe4d34. None was decision-needed, so nothing was escalated. All four held at base 5fe565a4: each new regression fails on the old command.py (4 failed) and passes on the fix. Full suite: 1322 passed, 5 skipped. task-validation: ready.

Fixes and choices:
- I-95b5d191 (critical, preferred-fix): after `git write-tree`, Delivery compares the staged tree with the readiness measurement. Each examined path must be staged with its mode, and with the digest readiness recorded once passed through the smudge filters a checkout applies. Every other path must be staged as the base holds it. A mismatch fails with the new code `staged_unvalidated` (reason decision) and gives the index back. Why checkout semantics rather than raw blob equality: raw equality would refuse every Git LFS or autocrlf repository, although a checkout gives back the validated bytes. The Issue's case, a clean filter that rewrites content, is still refused. The exec bit is ignored when core.fileMode=false, as Git ignores it. Spec: new req.delivery.staged-validated; scenarios staged-unvalidated and staged-filtered; module.md step 9 and result table; one sentence in contracts.md.
- I-4c792555 (high, preferred-fix): scenarios are now found with Spec core's parse_reading, at heading levels 2–5 and never inside fences. Only scenarios Spec core registers for that document count.
- I-7c6c648e (high, preferred-fix): verified scenarios now come from scan_declarations over every Module's bound files, not from the CONCORDE-COVERAGE-001 warnings, which skip Modules without files. req.delivery.scenarios-verified now says the rule holds whichever Module owns the scenario; new scenario.delivery.unrealized-scenarios.
- I-52fe4d34 (medium, obvious-fix): recorded paths are decoded with real_path before realization matching and Git/file access.

Non-ok result: the first delivery (r-20261008T063747-delivery-9a1d44da) ended blocked/not_ready on check.tasks.tests. The cause was the known teardown race in test_a_run_waiting_for_a_closing_tasks_workspace_is_refused_outside_it, unrelated to this task; the test alone passed 6/6. I appended this to the open Issue I-067df4e5 (module.tasks) and raised it to medium, since it can block an unrelated delivery. Then I reran delivery unchanged and it succeeded.

Open: nothing for this task. Merge with task merge as usual.

## Closed: merged, 2026-10-08T07:00:37Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 347790ca677f91352452d0eaee72c4649d436d09 into main and closed it as merged. Nobody answers a report after that.
