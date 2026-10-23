# Decision log: r4-e2e-dist

Goal: Fix the critical and high open Issues of E2E, Headless sessions, SWE-bench cases, Dogfood scenarios, Dogfooding, Distribution, Workflows, Issues and the root Module found by the fourth project_review, the critical first (I-ca4dea00)

## Task brief (main agent, 2026-10-17)

Round 4. The fourth project_review (r-20261013T165054-project_review-b4db00b2, unbound; reports
under `.concorde/unbound/r-20261013T165054-project_review-b4db00b2/` of the primary worktree) left
734 open Issues after rounds 1-3 had brought them to 4: most new findings are stricter standards
rather than new defects. The developer decided (2026-10-17): **each round fixes only critical and
high Issues**, medium and low wait until real use runs into them, and project_review is tuned so
its Issues stay actionable (task r4-review-tuning). This task resolves the critical and high Issues
of its Modules listed in `resolves`. Read each with `concorde issues show`. Other open Issues of
these Modules are out of scope: do not fix them unless a fix in scope needs it.

By tier: **decision-needed** — read them first and escalate them all together in one report,
early, each with what you found, the options and your recommendation, saying which options change
a promise users rely on or an earlier developer decision; continue with the rest meanwhile.
**preferred-fix** — fix as you judge best and report the choice. **obvious-fix** — fix. Critical
first. An Issue that no longer holds or is a duplicate: say so with evidence; it stays in
`resolves`. A fix needing a change outside the task's Modules: escalate unless it is a small
mechanical follow-on. Eight other round-4 tasks (r4-*) run in parallel on other Modules. Deliver
with `task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-17T04:37:57Z

- **task-session** task session (task r4-e2e-dist): `issue_decision_needed`
  I-1052efa9 (module.dogfood-scenarios, high): the purpose promises the session "Does not change Concorde", but concorde_untouched checks only the clone, the framework copy's src/scripts/prompts/generated, the install receipt's bytes and the receipt's installed files OUTSIDE .concorde/. The receipt's files include .concorde/bin/concorde (the launcher), and the Protocol copy .concorde/protocol/ is also unchecked, so a session could change either and still pass. Code: scripts/e2e/dogfood.py installed_digests() filters to paths outside .concorde/.
  Not handled here (decision): The Issue is decision-needed: choosing the integrity scope changes what the evaluation promises.
  Options: A: widen the baselines to every file the receipt names, inside .concorde/ too, except the receipt's defaults (project-owned files such as .concorde/issues/.gitignore), plus the Protocol copy under .concorde/protocol/; mutable state (tasks, issues, runs, locks, history) stays excluded. This changes the dogfood.json record (version bump) and the concorde_untouched contract.; B: keep the check and narrow the purpose to 'does not change Concorde's sources, its receipt or the files it installed outside .concorde/'. No code change.
  Recommendation: A. It makes the check match the purpose; nobody relies on the narrower check (developer-only test tool), and no earlier developer decision is touched.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-e2e-dist)",
  "code": "issue_decision_needed",
  "detail": "I-1052efa9 (module.dogfood-scenarios, high): the purpose promises the session \"Does not change Concorde\", but concorde_untouched checks only the clone, the framework copy's src/scripts/prompts/generated, the install receipt's bytes and the receipt's installed files OUTSIDE .concorde/. The receipt's files include .concorde/bin/concorde (the launcher), and the Protocol copy .concorde/protocol/ is also unchecked, so a session could change either and still pass. Code: scripts/e2e/dogfood.py installed_digests() filters to paths outside .concorde/.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: choosing the integrity scope changes what the evaluation promises."
  },
  "options": [
    "A: widen the baselines to every file the receipt names, inside .concorde/ too, except the receipt's defaults (project-owned files such as .concorde/issues/.gitignore), plus the Protocol copy under .concorde/protocol/; mutable state (tasks, issues, runs, locks, history) stays excluded. This changes the dogfood.json record (version bump) and the concorde_untouched contract.",
    "B: keep the check and narrow the purpose to 'does not change Concorde's sources, its receipt or the files it installed outside .concorde/'. No code change."
  ],
  "recommendation": "A. It makes the check match the purpose; nobody relies on the narrower check (developer-only test tool), and no earlier developer decision is touched.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:37:57Z

- **task-session** task session (task r4-e2e-dist): `issue_decision_needed`
  I-4941e031 (module.swe-bench-cases, high): repair-specs says that when the first spec_panel's verdict is accepted, task-validation and delivery follow with no repair, then the task is merged. The task is fresh and nothing changes (Issues go to the primary worktree), so Delivery refuses with blocked/nothing_to_deliver and the repair stops with the task left open. scripts/e2e/cases.py:115 branches on the verdict.
  Not handled here (decision): The Issue is decision-needed: the accepted branch's promised workflow changes, and the fix touches Delivery or Tasks only through their existing commands.
  Options: A: on accepted, stop after the review: report the acceptance, close the unused task with task close (no validation, delivery or merge), and print the round as complete. Update the entry, diagram and scenario.repair-accepted.; B: keep validation and delivery, and document blocked/nothing_to_deliver as the expected end of an accepted round, the task left for the developer to close.; C: change Delivery to accept an empty change (outside this task's Modules; changes Delivery's promise).
  Recommendation: A. It changes only the case tool's own workflow (developer-only); B leaves an open task every time; C changes Delivery's promise that users rely on.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-e2e-dist)",
  "code": "issue_decision_needed",
  "detail": "I-4941e031 (module.swe-bench-cases, high): repair-specs says that when the first spec_panel's verdict is accepted, task-validation and delivery follow with no repair, then the task is merged. The task is fresh and nothing changes (Issues go to the primary worktree), so Delivery refuses with blocked/nothing_to_deliver and the repair stops with the task left open. scripts/e2e/cases.py:115 branches on the verdict.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: the accepted branch's promised workflow changes, and the fix touches Delivery or Tasks only through their existing commands."
  },
  "options": [
    "A: on accepted, stop after the review: report the acceptance, close the unused task with task close (no validation, delivery or merge), and print the round as complete. Update the entry, diagram and scenario.repair-accepted.",
    "B: keep validation and delivery, and document blocked/nothing_to_deliver as the expected end of an accepted round, the task left for the developer to close.",
    "C: change Delivery to accept an empty change (outside this task's Modules; changes Delivery's promise)."
  ],
  "recommendation": "A. It changes only the case tool's own workflow (developer-only); B leaves an open task every time; C changes Delivery's promise that users rely on.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:37:57Z

- **task-session** task session (task r4-e2e-dist): `issue_decision_needed`
  I-5434b8e8 (module.e2e, high): E2E's prepare says Workers' check of a whole configuration resolves the model of every worker of every Operation in the catalog. The code does exactly that (models.check_mapped(config, declared_workers()) with operation=None checks every declared worker of every Operation), but Workers' Spec documents only the per-Operation check (scenario.workers.model-map-checked) and says 'a worker without a model is left to its own resolution'. Also, an Operation such as `general` declares no worker ids, so its workers are not checked before launch.
  Not handled here (scope): The full fix needs a Workers Spec change (module.workers, owned by task r4-workers), and the choice of guarantee is decision-needed.
  Options: A: Workers' Spec states the whole-catalog mode its code already has (a requirement and scenario: without an Operation, every declared worker of every Operation is checked in one refusal); E2E narrows its wording to 'every worker id the catalog declares that has an effective model', and says that workers of Operations declaring no worker ids (general) and workers with no effective model are checked when they launch. No code change.; B: E2E only: narrow the guarantee as in A and cite the code, without a Workers Spec change (leaves the provider undocumented).; C: strengthen: E2E or Workers also resolves workers with no effective model and covers general's per-type workers (code change in Workers).
  Recommendation: A. It documents existing behaviour and narrows E2E to what is checked; the Workers part is a small follow-on that I can make here or that r4-workers can take. No user promise or developer decision changes.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-e2e-dist)",
  "code": "issue_decision_needed",
  "detail": "I-5434b8e8 (module.e2e, high): E2E's prepare says Workers' check of a whole configuration resolves the model of every worker of every Operation in the catalog. The code does exactly that (models.check_mapped(config, declared_workers()) with operation=None checks every declared worker of every Operation), but Workers' Spec documents only the per-Operation check (scenario.workers.model-map-checked) and says 'a worker without a model is left to its own resolution'. Also, an Operation such as `general` declares no worker ids, so its workers are not checked before launch.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "The full fix needs a Workers Spec change (module.workers, owned by task r4-workers), and the choice of guarantee is decision-needed."
  },
  "options": [
    "A: Workers' Spec states the whole-catalog mode its code already has (a requirement and scenario: without an Operation, every declared worker of every Operation is checked in one refusal); E2E narrows its wording to 'every worker id the catalog declares that has an effective model', and says that workers of Operations declaring no worker ids (general) and workers with no effective model are checked when they launch. No code change.",
    "B: E2E only: narrow the guarantee as in A and cite the code, without a Workers Spec change (leaves the provider undocumented).",
    "C: strengthen: E2E or Workers also resolves workers with no effective model and covers general's per-type workers (code change in Workers)."
  ],
  "recommendation": "A. It documents existing behaviour and narrows E2E to what is checked; the Workers part is a small follow-on that I can make here or that r4-workers can take. No user promise or developer decision changes.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:37:58Z

- **task-session** task session (task r4-e2e-dist): `issue_decision_needed`
  I-900c2f86 (module.distribution, high): the package descriptor concorde.json is the build's and installer's main input, but Distribution's Specs give only a descriptive inventory (name, version, licence, shipped roots, install locations, client, tools, develop.check, runtime.python), no complete input contract with field shapes, path semantics and refusals.
  Not handled here (decision): The Issue is decision-needed because accepted field shapes and compatibility must be stated rather than inferred.
  Options: A: add a contract contract.distribution.package-descriptor (JSON Schema plus semantics) written from what the build and installer accept today, with their refusals, and link the entry to it. No behaviour change; incompatible descriptor changes are governed by the contract's version.; B: add the contract and also tighten the readers to refuse unknown fields (behaviour change).; C: declare concorde.json internal to the Concorde checkout (only Concorde's own build reads it) and narrow the entry to say so, without a contract.
  Recommendation: A. It documents current behaviour without changing it; no user promise or developer decision changes. I can do it in this task.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-e2e-dist)",
  "code": "issue_decision_needed",
  "detail": "I-900c2f86 (module.distribution, high): the package descriptor concorde.json is the build's and installer's main input, but Distribution's Specs give only a descriptive inventory (name, version, licence, shipped roots, install locations, client, tools, develop.check, runtime.python), no complete input contract with field shapes, path semantics and refusals.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed because accepted field shapes and compatibility must be stated rather than inferred."
  },
  "options": [
    "A: add a contract contract.distribution.package-descriptor (JSON Schema plus semantics) written from what the build and installer accept today, with their refusals, and link the entry to it. No behaviour change; incompatible descriptor changes are governed by the contract's version.",
    "B: add the contract and also tighten the readers to refuse unknown fields (behaviour change).",
    "C: declare concorde.json internal to the Concorde checkout (only Concorde's own build reads it) and narrow the entry to say so, without a contract."
  ],
  "recommendation": "A. It documents current behaviour without changing it; no user promise or developer decision changes. I can do it in this task.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:37:58Z

- **task-session** task session (task r4-e2e-dist): `issue_decision_needed`
  I-9c3b5d18 (module.workflows, high): when a launcher (concorde run … --detach) gives no answer within 90 seconds, the step command ends it and records the step refused, and the entry concludes 'no run of a refused step starts later'. But Execution only promises to end the runner when it itself reports detach_failed; if the launcher is killed without answering, a detached runner may survive and do work that the step never names, and a retry repeats it. Code: src/concorde/workflows/step.py:305-310 (LAUNCH_WAIT=90).
  Not handled here (decision): The Issue is decision-needed: it is a choice between two designs of the step command's idempotent retry guarantee.
  Options: A: on a launcher timeout, leave the step starting (not refused) and return running; the next call's existing starting-step recovery adopts a run found in the step's node, waits while a run holds the workspace lock or the lobby, and otherwise ends the node lost and starts anew. This reuses the recovery the Spec already has for a killed step command.; B: keep 'refused', but before recording it confirm termination: kill the launcher's whole process group and refuse only after no run lies in the step's node and no run holds the workspace lock; otherwise adopt it.
  Recommendation: A. It reuses an existing, specified recovery path, needs the least new code, and changes only an internal outcome (refused becomes running for that rare case); no user promise or developer decision changes.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-e2e-dist)",
  "code": "issue_decision_needed",
  "detail": "I-9c3b5d18 (module.workflows, high): when a launcher (concorde run … --detach) gives no answer within 90 seconds, the step command ends it and records the step refused, and the entry concludes 'no run of a refused step starts later'. But Execution only promises to end the runner when it itself reports detach_failed; if the launcher is killed without answering, a detached runner may survive and do work that the step never names, and a retry repeats it. Code: src/concorde/workflows/step.py:305-310 (LAUNCH_WAIT=90).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: it is a choice between two designs of the step command's idempotent retry guarantee."
  },
  "options": [
    "A: on a launcher timeout, leave the step starting (not refused) and return running; the next call's existing starting-step recovery adopts a run found in the step's node, waits while a run holds the workspace lock or the lobby, and otherwise ends the node lost and starts anew. This reuses the recovery the Spec already has for a killed step command.",
    "B: keep 'refused', but before recording it confirm termination: kill the launcher's whole process group and refuse only after no run lies in the step's node and no run holds the workspace lock; otherwise adopt it."
  ],
  "recommendation": "A. It reuses an existing, specified recovery path, needs the least new code, and changes only an internal outcome (refused becomes running for that rare case); no user promise or developer decision changes.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:37:58Z

- **task-session** task session (task r4-e2e-dist): `issue_decision_needed`
  I-c17b0b67 (module.dogfooding, high): Dogfooding gives the main agent the duty to observe every run and report Concorde defects, but in the current working method task sessions start and observe the runs, and Dogfooding contributes no task-session guidance (generated/dogfooding has claude-md.md and skill.md only). So the session that sees a defect has no stated duty to recognize it, keep its evidence, not work around it and pass it up.
  Not handled here (decision): The Issue is decision-needed: assigning observation and reporting duties changes the actors' promises (and Main session's delegation).
  Options: A: Dogfooding contributes task-session guidance in a develop install: a task session that suspects a Concorde defect keeps the run's evidence and whole error chain, does not work around it, and escalates it to the main agent with the chain; the main agent classifies it (boundary case) and writes the defect report as now. Add a scenario of a defect first seen by a task session.; B: task sessions write defect reports themselves, the main agent only relays.; C: narrow Dogfooding to what the main agent sees through task sessions' ordinary reports and escalations, with no new task-session duty.
  Recommendation: A. It keeps the main agent the only defect reporter (as decided earlier) and closes the gap with a guidance block like Issues' task-session block. It adds a task-session duty but changes no earlier developer decision.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-e2e-dist)",
  "code": "issue_decision_needed",
  "detail": "I-c17b0b67 (module.dogfooding, high): Dogfooding gives the main agent the duty to observe every run and report Concorde defects, but in the current working method task sessions start and observe the runs, and Dogfooding contributes no task-session guidance (generated/dogfooding has claude-md.md and skill.md only). So the session that sees a defect has no stated duty to recognize it, keep its evidence, not work around it and pass it up.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: assigning observation and reporting duties changes the actors' promises (and Main session's delegation)."
  },
  "options": [
    "A: Dogfooding contributes task-session guidance in a develop install: a task session that suspects a Concorde defect keeps the run's evidence and whole error chain, does not work around it, and escalates it to the main agent with the chain; the main agent classifies it (boundary case) and writes the defect report as now. Add a scenario of a defect first seen by a task session.",
    "B: task sessions write defect reports themselves, the main agent only relays.",
    "C: narrow Dogfooding to what the main agent sees through task sessions' ordinary reports and escalations, with no new task-session duty."
  ],
  "recommendation": "A. It keeps the main agent the only defect reporter (as decided earlier) and closes the gap with a guidance block like Issues' task-session block. It adds a task-session duty but changes no earlier developer decision.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-17T04:37:58Z

- **task-session** task session (task r4-e2e-dist): `issue_decision_needed`
  I-deaf9296 (module.issues, high): Operation reporting deliberately accepts an owner that is not in the primary registry (a task's run may review a Module the task adds, e.g. brownfield scaffold then spec_panel before merge), but `concorde issues check` reports an error for any open Issue whose owner is not registered (interface.md 686-697). So an ordinary adoption review makes the primary Issue store fail its check until the task merges, and an abandoned task leaves the unknown owner forever.
  Not handled here (decision): The Issue is decision-needed: it changes the ownership contract of Issues; it also concerns Tasks (abandonment).
  Options: A: check reports an open Issue's unregistered owner as a warning, not an error, when its latest report's provenance names a workspace (change_id) of a task that is still open; once that task merges the owner is registered and the warning disappears; when the task is closed without merge, check reports it as an error naming the task, and the main agent closes such Issues not-actionable (or re-owns them).; B: check always reports an unregistered owner as a warning, never an error.; C: Operation reporting assigns a registered accountable owner (the nearest registered ancestor, else module.concorde) and keeps the new Module as provenance target_id; on merge the owner is not changed automatically.
  Recommendation: A. It keeps the store's integrity check strict for real errors while allowing the brownfield sequence; it needs no change in Tasks beyond reading open tasks. B is simplest if you prefer minimal change. C changes who owns review findings, which users read.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-e2e-dist)",
  "code": "issue_decision_needed",
  "detail": "I-deaf9296 (module.issues, high): Operation reporting deliberately accepts an owner that is not in the primary registry (a task's run may review a Module the task adds, e.g. brownfield scaffold then spec_panel before merge), but `concorde issues check` reports an error for any open Issue whose owner is not registered (interface.md 686-697). So an ordinary adoption review makes the primary Issue store fail its check until the task merges, and an abandoned task leaves the unknown owner forever.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: it changes the ownership contract of Issues; it also concerns Tasks (abandonment)."
  },
  "options": [
    "A: check reports an open Issue's unregistered owner as a warning, not an error, when its latest report's provenance names a workspace (change_id) of a task that is still open; once that task merges the owner is registered and the warning disappears; when the task is closed without merge, check reports it as an error naming the task, and the main agent closes such Issues not-actionable (or re-owns them).",
    "B: check always reports an unregistered owner as a warning, never an error.",
    "C: Operation reporting assigns a registered accountable owner (the nearest registered ancestor, else module.concorde) and keeps the new Module as provenance target_id; on merge the owner is not changed automatically."
  ],
  "recommendation": "A. It keeps the store's integrity check strict for real errors while allowing the brownfield sequence; it needs no change in Tasks beyond reading open tasks. B is simplest if you prefer minimal change. C changes who owns review findings, which users read.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-17T04:38:10Z

r4-e2e-dist: early escalation of all 7 decision-needed Issues, per the brief (I continue with the 8 fixable Issues meanwhile, critical I-ca4dea00 first).

1. I-1052efa9 (dogfood-scenarios) untouched check skips installed files inside .concorde/ (launcher, Protocol copy). Rec. A: widen baselines to every receipt file, inside .concorde/ too, minus defaults, plus the Protocol copy; record version bump.
2. I-4941e031 (swe-bench-cases) accepted review leaves nothing for Delivery. Rec. A: on accepted, stop after the review, close the unused task, report the round complete.
3. I-5434b8e8 (e2e) prepare promises a stronger model check than Workers documents. Rec. A: Workers' Spec states the whole-catalog check its code already has (small follow-on in module.workers, outside my Modules — say whether I may make it or leave it to r4-workers); E2E narrows to declared workers with an effective model. No code change.
4. I-900c2f86 (distribution) no package-descriptor contract. Rec. A: add contract.distribution.package-descriptor from what build and installer accept today; no behaviour change.
5. I-9c3b5d18 (workflows) launcher timeout recorded refused without knowing the runner ended. Rec. A: leave the step starting so the existing starting-step recovery adopts or relaunches.
6. I-c17b0b67 (dogfooding) no task-session duty for Concorde defects. Rec. A: Dogfooding contributes task-session guidance (keep evidence and whole chain, no workaround, escalate to main agent); main agent stays the only defect reporter; add a scenario.
7. I-deaf9296 (issues) check errors on owners only a task branch registers. Rec. A: warning while the provenance's task is open, error once it closed unmerged. B (always warning) if you prefer minimal.

None of the recommended options changes an earlier developer decision. Options that change a promise users rely on: #2 C (Delivery accepting empty change), #7 C (owners of review findings). The rendered chains are in escalations 1-7.

It carries escalation(s) 1, 2, 3, 4, 5, 6, 7.

## Answer to report(s) 1 of the task session, 2026-10-17T04:38:29Z

Escalations 1-7 (main agent), each your recommendation A: 1 widen the untouched baselines to every receipt file, .concorde/ included, minus defaults, plus the Protocol copy; record version bump. 2 on accepted, stop after the review, close the unused task, report the round complete. 3 E2E narrows to declared workers with an effective model; the Workers follow-on stating the whole-catalog check is allowed as a short addition in module.workers (r4-workers also edits Workers' Specs, so keep it to that statement; a merge conflict there is the main agent's to route). 4 add contract.distribution.package-descriptor from what build and installer accept today. 5 leave the step starting so starting-step recovery adopts or relaunches. 6 Dogfooding contributes task-session guidance (keep evidence and the whole chain, no workaround, escalate to the main agent), the main agent stays the only defect reporter; add a scenario. 7 A — warning while the provenance's task is open, error once it closed unmerged.

## Task session decisions (2026-10-17)

Decisions taken without the developer while carrying out the brief and the answered escalations:

- I-ca4dea00 (preferred-fix, critical): fixed by requiring clone-relative edit paths in the scenario
  file (no absolute path, no empty/./.. segment, `invalid_scenario`) and by resolving every edit,
  symbolic links included, before any write in `inject`, refusing one outside the clone with the
  existing code `fault_not_applicable` rather than a new code. Edits are all checked before any is
  written; several edits of one file apply in turn. Scenario contract version 1 -> 2.
- I-1052efa9 (A): `installed` now digests every regular file the receipt names except its
  `defaults`; directory entries (the framework copy `.concorde/framework/`, tool directories) are
  left to their own digests or out. A receipt `defaults` that is no list of paths reads as
  unreadable. Record contract version 1 -> 2; the record itself carries no version.
- I-b09d908c (obvious-fix): a task record must name its worktree by an absolute path; one helper
  `common.recorded_worktree` serves `run` and `owners`; the owners refusal now names the record.
- I-18384bb5 (obvious-fix): `--ignore-submodules=none` in the develop source status query.
- I-55f6db5b (obvious-fix): code was already right (contention = alive); only the entry was wrong.
  Added a unit test of the probe.
- I-c3be0985 (obvious-fix): code already matched the requirement; fixed both entry passages.
- I-4eaf962e (preferred-fix): the walkthrough follows the update result's `next` in order, the main
  agent committing the updated files on the primary branch first; the same step was added to
  Distribution's update guidance (`prompts/guidance/distribution/skill.md`), since it said nothing
  about committing.
- I-2dbb980b (preferred-fix): chose relies_on entries (contract.workflows.workflow-trace,
  contract.workflows.result, contract.execution.run-trace, contract.execution.run-result,
  req.execution.run-lock-held, contract.kernel.workspace-binding, contract.tasks.record) plus a
  document include of document.execution.runner for the run progress file's fields, rather than
  whole-document includes; the tracing lock-handing contract was not selected since E2E holds the
  workspace lock with a plain flock and hands none on.
- I-5434b8e8 (A): Workers follow-on kept to one statement in workers/module.md (no requirement or
  scenario added), as the answer asked.
- I-4941e031 (A): the accepted branch closes the task with `task close --completed --note` naming
  the review; the printed result gains `task_end` (`merged`, `closed`, `open`).
- I-c03e4b6c (preferred-fix): `_put_back_all` keeps the published counterpart of a committed record
  it could not restore and still puts back every other path; the refusal says the copy is kept.
- I-deaf9296 (A): an open task is one whose `tasks/<id>/task.json` lies in the `.concorde` the
  worktree's workspace binding names (the primary's), or the worktree's own without a binding, so
  the configured check `check.issues.store` run by task-validation in a task worktree sees the
  primary's open tasks. Tasks is an optional integration (file presence, like the registry for the
  spec part). The note/error texts name the task.
- I-9c3b5d18 (A): a launcher timeout raises `LaunchUnanswered`; the step stays starting and the
  call prints `running` with no run (exit 3). Remaining gap, stated nowhere new: a runner that has
  not reached the lobby yet when the next call looks can still be missed, as for a killed step
  command; Execution's own 60-second announcement wait bounds that window.
- I-c17b0b67 (A): new prompt `prompts/dogfooding/task-session.md`; `develop.check` returns a third
  section `task_session`; the installer appends it to the task-session prompt where coordination and
  issues are installed. New requirement req.dogfooding.task-session-escalates and scenario
  scenario.dogfooding.task-session-defect.
- I-900c2f86 (A): contract.distribution.package-descriptor; `required` holds only what every
  install reads (`version`, `runtime.python`); the other read fields (tools.d2, develop.check,
  package_roots) are optional with their refusals in the semantics; the rest is declared
  descriptive. The entry no longer claims `package_roots` decides what the installer ships (the
  parts' registrations do).

Non-ok results:

- One run of `pytest tests/concorde/issues` after the I-c03e4b6c commit reported "8 failed, 39
  passed" (47 tests instead of 120); three later runs of the same command passed 120/120 and the
  failure did not reproduce, so no cause was found. Recorded here as a possibly flaky collection.
- task-validation r-20261017T052111-task_validation-ff98875b ended `blocked`: check.tracing.tests
  failed once (test_locks.py::LockLineTests::test_a_held_lock_is_named_once_while_other_processes_churn_locks,
  holder_pids returned [] while the lock was held). The branch changes nothing of Kernel or
  Tracing; the full suite had passed. Reran with no change: r-20261017T053043-task_validation-8ca2c62c
  `ok`, ready. Reported as Issue I-25c91daf01e25806b2ab74e946e6bf18 (module.tracing,
  decision-needed, medium), not fixed here (outside the task's Modules).

## Report 2 to the main agent (Review流程), 2026-10-17T05:49:50Z

r4-e2e-dist delivered: delivery commit 81c05eb65260e461166aa148e6414c365e59166e on concorde/r4-e2e-dist (delivery run r-20261017T054034-delivery-bf518c52, task-validation r-20261017T053043-task_validation-8ca2c62c ready). The full suite passed once on the final input: 1601 passed, 6 skipped.

All 15 Issues in `resolves` are fixed, one commit each (none turned out stale or a duplicate):
- Critical I-ca4dea00 (preferred-fix): fault edits must name clone-relative paths. `inject` resolves each one, symbolic links included, and refuses one outside the clone with fault_not_applicable before writing any. Tests cover the symbolic link, absolute and `..` cases.
- Answered option A, as decided: I-1052efa9 (baselines cover every receipt file, `.concorde/` included, except defaults), I-4941e031 (an accepted first review runs `task close --completed`, and the output gains task_end), I-5434b8e8 (E2E narrowed; Workers got one statement only), I-900c2f86 (new contract.distribution.package-descriptor plus a test), I-9c3b5d18 (a silent launcher leaves the step starting), I-c17b0b67 (new prompts/dogfooding/task-session.md, which the installer appends to the task-session prompt; new requirement and scenario), I-deaf9296 (an unregistered owner is a note while the task in its change_id is open, found through the binding's .concorde, and an error naming the task once it has ended).
- Obvious-fix: I-b09d908c (a task record must name an absolute worktree), I-18384bb5 (--ignore-submodules=none), I-55f6db5b (entry wording only; the code was right), I-c3be0985 (entry wording only; the code was right).
- Preferred-fix, my choice: I-4eaf962e (the walkthrough follows the update result's `next`, committing first; I added the same step to Distribution's update guidance). I-2dbb980b (relies_on entries for the record and lock contracts plus an include of document.execution.runner, not whole documents). I-c03e4b6c (rollback keeps the published half when the committed record cannot be restored).

Outside my Modules: one statement in workers/module.md (allowed in your answer). .concorde/specs.json was regenerated for module.e2e and module.issues, so a conflict with other r4 tasks there is likely.

Non-ok results: the first task-validation (r-20261017T052111-task_validation-ff98875b) was blocked by an intermittent failure of check.tracing.tests (test_locks churn test). Nothing in Kernel or Tracing changed, and the unchanged rerun was ready. I recorded it as Issue I-25c91daf01e25806b2ab74e946e6bf18 (module.tracing, decision-needed, medium). One Issues test run collected only 47 tests with 8 failures; it did not reproduce in 3 reruns or the full suite.

Open: I-25c91daf (new) and a known remaining gap in I-9c3b5d18 (a runner that has not reached the lobby yet can still be missed, as for a killed step command). Every decision is in the decision log. I did not push the branch.

## Closed: merged, 2026-10-23T09:02:35Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 81c05eb65260e461166aa148e6414c365e59166e into main and closed it as merged. Nobody answers a report after that.
