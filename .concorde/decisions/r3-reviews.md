# Decision log: r3-reviews

Goal: Fix the remaining open Issues of Spec review, Code review, Project review and Method (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (25, listed in `resolves`; 5 of them decision-needed), all medium or
low, found by project_review r-20261008T063808-project_review-9851e69f or reported since. Read each
with `concorde issues show`.

By tier:
- **decision-needed**: read them all first and escalate them **together in one report, early**,
  each with what you found, the options and your recommendation (say which options change a
  promise users rely on or an earlier developer decision). The main agent settles those within its
  authority and takes the rest to the developer in one batch. Continue with the rest meanwhile.
  An Issue the developer is asked about may stay open: you may deliver without it; the main agent
  reopens it after the merge if needed.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it is wrong or costs more than it is worth; then say why in the
  log and your report, and the main agent closes it as not-actionable.
- An Issue that no longer holds (many Modules changed in rounds 1-2), is a duplicate or is already
  fixed: say so with evidence; it stays in `resolves` and the merge closes it.
- Medium first, then low. A fix needing a change outside the task's Modules: escalate, unless it is
  a small mechanical follow-on (a link, a fixture, a registry refresh).

Eleven other round-3 tasks (r3-*) run in parallel on other Modules. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-13T11:34:08Z

- **task-session** task session (task r3-reviews): `issue_decision_needed`
  I-20920b23da03573bb1c5354c2472ca03 (project_review, medium): when Git cannot list the tracked files, project_review examines no unowned file but its report still says deterministic.complete true, unowned [] and the verdict may be accepted, so the caller cannot tell a failed listing from a clean one. Today the run only adds host evidence ('the tracked files could not be listed') and carries their Issues (see also I-d7d4e73c, which I fix). Checks that cannot run already make deterministic.complete false and the Modules incomplete.
  Not handled here (decision): Choosing how an unexamined part shows in the report changes the observable report contract (contract.project-review.report), which the Issue's tier reserves above the task.
  Options: A: treat a failed listing like checks that could not run: deterministic.complete false, the root Module (owner of unowned files) and the project incomplete, with a stop link naming the Git error; add a scenario. Changes a report field's semantics only on this failure path; no earlier developer decision touched.; B: keep complete true and add an explicit field (e.g. deterministic.unowned_examined false) so the result is an explicitly partial success; verdict unaffected.
  Recommendation: A: one rule for every deterministic part that could not run, and the verdict never reads accepted when ownership was not examined.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-reviews)",
  "code": "issue_decision_needed",
  "detail": "I-20920b23da03573bb1c5354c2472ca03 (project_review, medium): when Git cannot list the tracked files, project_review examines no unowned file but its report still says deterministic.complete true, unowned [] and the verdict may be accepted, so the caller cannot tell a failed listing from a clean one. Today the run only adds host evidence ('the tracked files could not be listed') and carries their Issues (see also I-d7d4e73c, which I fix). Checks that cannot run already make deterministic.complete false and the Modules incomplete.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing how an unexamined part shows in the report changes the observable report contract (contract.project-review.report), which the Issue's tier reserves above the task."
  },
  "options": [
    "A: treat a failed listing like checks that could not run: deterministic.complete false, the root Module (owner of unowned files) and the project incomplete, with a stop link naming the Git error; add a scenario. Changes a report field's semantics only on this failure path; no earlier developer decision touched.",
    "B: keep complete true and add an explicit field (e.g. deterministic.unowned_examined false) so the result is an explicitly partial success; verdict unaffected."
  ],
  "recommendation": "A: one rule for every deterministic part that could not run, and the verdict never reads accepted when ownership was not examined.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:28Z

- **task-session** task session (task r3-reviews): `issue_decision_needed`
  I-4c12272ea87a5b44a8ee92126c7ee8ff (code_review, medium): code-review/module.md and scenario.code-review.spec-challenge say a Spec challenge is 'usually decision-needed', while the same entry says the task escalates 'every Spec challenge' as decision-needed; the reviewer prompt (prompts/workers/review-code.md) and the task-session guidance also say 'usually'. No exception is defined and the host does not touch a finding's tier.
  Not handled here (decision): Whether a Spec challenge may ever be fixed inside a task decides who may change a Module's promise, a policy the Issue's tier reserves above the task.
  Options: A: every Spec challenge is decision-needed: the reviewer brief says so and the Operation records the tier decision-needed for every spec-challenge finding whatever the worker gave (host evidence notes a correction); entry, requirement, scenario and guidance say 'always'. Matches the rule that a promise change is decided above the task; changes no earlier developer decision.; B: keep 'usually' and define the exception: preferred-fix when another written promise (the Spec contradicting itself or a provider's contract) already settles the repair; the task handles it by tier like any Issue.
  Recommendation: A: simplest and safest; the main agent settles most such Issues itself anyway, and B leaves the worker to judge whether a promise change is already decided.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-reviews)",
  "code": "issue_decision_needed",
  "detail": "I-4c12272ea87a5b44a8ee92126c7ee8ff (code_review, medium): code-review/module.md and scenario.code-review.spec-challenge say a Spec challenge is 'usually decision-needed', while the same entry says the task escalates 'every Spec challenge' as decision-needed; the reviewer prompt (prompts/workers/review-code.md) and the task-session guidance also say 'usually'. No exception is defined and the host does not touch a finding's tier.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Whether a Spec challenge may ever be fixed inside a task decides who may change a Module's promise, a policy the Issue's tier reserves above the task."
  },
  "options": [
    "A: every Spec challenge is decision-needed: the reviewer brief says so and the Operation records the tier decision-needed for every spec-challenge finding whatever the worker gave (host evidence notes a correction); entry, requirement, scenario and guidance say 'always'. Matches the rule that a promise change is decided above the task; changes no earlier developer decision.",
    "B: keep 'usually' and define the exception: preferred-fix when another written promise (the Spec contradicting itself or a provider's contract) already settles the repair; the task handles it by tier like any Issue."
  ],
  "recommendation": "A: simplest and safest; the main agent settles most such Issues itself anyway, and B leaves the worker to judge whether a promise change is already decided.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:28Z

- **task-session** task session (task r3-reviews): `issue_decision_needed`
  I-5e812707a0055b72998ee147f536fc3e (spec_panel, medium, a spec-challenge): spec-review/panel.md host step 1 and its result-status table promise that an unknown named Module is 'incomplete' (panel_incomplete with the panel payload, the other Modules still paneled), but spec_panel uses Method's shared admission (src/concorde/method/specs.py admit_modules), which refuses the whole run with unknown_module before any step, as Execution's admission and every other Method Operation (code_review, project_review, ...) do. So today the run is refused and the incomplete branch in panel.py validate_modules is dead.
  Not handled here (decision): Either option changes a written promise of Spec review (the panel's per-Module outcome for an unknown Module) or makes spec_panel an exception to the common admission rule.
  Options: A: revise the panel's promise to what runs today: a named Module the workspace does not register refuses the run with unknown_module before any step, as for every Method Operation; drop the unknown case from step 1 and the status table, remove the dead branch, add a test. Changes a promise, but one no run has ever kept.; B: make spec_panel an exception to admission: register an admission that lets validate_modules mark an unknown Module incomplete and panel the others; document the exception in Spec review and Method.
  Recommendation: A: one admission rule for every Operation; a misspelled Module is a caller error better refused before any worker spends money; the implementation already behaves so.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-reviews)",
  "code": "issue_decision_needed",
  "detail": "I-5e812707a0055b72998ee147f536fc3e (spec_panel, medium, a spec-challenge): spec-review/panel.md host step 1 and its result-status table promise that an unknown named Module is 'incomplete' (panel_incomplete with the panel payload, the other Modules still paneled), but spec_panel uses Method's shared admission (src/concorde/method/specs.py admit_modules), which refuses the whole run with unknown_module before any step, as Execution's admission and every other Method Operation (code_review, project_review, ...) do. So today the run is refused and the incomplete branch in panel.py validate_modules is dead.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Either option changes a written promise of Spec review (the panel's per-Module outcome for an unknown Module) or makes spec_panel an exception to the common admission rule."
  },
  "options": [
    "A: revise the panel's promise to what runs today: a named Module the workspace does not register refuses the run with unknown_module before any step, as for every Method Operation; drop the unknown case from step 1 and the status table, remove the dead branch, add a test. Changes a promise, but one no run has ever kept.",
    "B: make spec_panel an exception to admission: register an admission that lets validate_modules mark an unknown Module incomplete and panel the others; document the exception in Spec review and Method."
  ],
  "recommendation": "A: one admission rule for every Operation; a misspelled Module is a caller error better refused before any worker spends money; the implementation already behaves so.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:34:29Z

- **task-session** task session (task r3-reviews): `issue_decision_needed`
  I-bae9bb9b48d35315905f3807a98fe986 (Method, medium, spec-gap): Method's worker sequence (src/concorde/method/workers.py run_worker, interpreter_roots) adds to every worker's read-only runtime paths, besides the configured runtime paths, the directories the project interpreter needs: the interpreter's environment, the installation it resolves to, and each directory holding a symbolic link on the way, never /usr, the home itself or a directory holding the home. Workers' launch.md already says the caller lists what the interpreter needs among the runtime paths, but Method's workers.md does not state that it does so, which directories, the exclusions, or that the configured runtime paths neither replace nor limit them.
  Not handled here (decision): It concerns which host directories a worker may read outside its grant, i.e. the read boundary (security-adjacent), and documenting it makes the current automatic expansion a promise.
  Options: A: specify the current behaviour in Method's workers.md (worker limits / standard worker sequence), read-only, with its exclusions and its independence from the configured runtime paths, plus a requirement and a scenario backed by the existing interpreter_roots tests. No code change; no earlier developer decision touched.; B: drop the automatic expansion and require the developer to list the interpreter's directories under runtime in .concorde/workers.json; workers fail to run the project's Python until they do.
  Recommendation: A: workers must run the project's tests with its interpreter; the expansion is read-only, excludes the home and its ancestors, and Workers' Spec already expects the caller to list these directories.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-reviews)",
  "code": "issue_decision_needed",
  "detail": "I-bae9bb9b48d35315905f3807a98fe986 (Method, medium, spec-gap): Method's worker sequence (src/concorde/method/workers.py run_worker, interpreter_roots) adds to every worker's read-only runtime paths, besides the configured runtime paths, the directories the project interpreter needs: the interpreter's environment, the installation it resolves to, and each directory holding a symbolic link on the way, never /usr, the home itself or a directory holding the home. Workers' launch.md already says the caller lists what the interpreter needs among the runtime paths, but Method's workers.md does not state that it does so, which directories, the exclusions, or that the configured runtime paths neither replace nor limit them.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "It concerns which host directories a worker may read outside its grant, i.e. the read boundary (security-adjacent), and documenting it makes the current automatic expansion a promise."
  },
  "options": [
    "A: specify the current behaviour in Method's workers.md (worker limits / standard worker sequence), read-only, with its exclusions and its independence from the configured runtime paths, plus a requirement and a scenario backed by the existing interpreter_roots tests. No code change; no earlier developer decision touched.",
    "B: drop the automatic expansion and require the developer to list the interpreter's directories under runtime in .concorde/workers.json; workers fail to run the project's Python until they do."
  ],
  "recommendation": "A: workers must run the project's tests with its interpreter; the expansion is read-only, excludes the home and its ancestors, and Workers' Spec already expects the caller to list these directories.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:35:05Z

r3-reviews: early decision report. Four of the five decision-needed Issues need an answer (escalations 1-4, chains below, each a task-session link with no causes). The fifth, I-a650412e62fd566a96f64fe55cce2f54 (worker-record failure vs Tracing), no longer holds: commit d78a62134 (2026-10-08, after the reviewing run) rewrote panel.md host step 6 so that a refused trace write changes neither the Module outcome nor the status and is reported as trace-write evidence, matching Tracing and the code; scenario.method.trace-write-reported verifies it. It stays in resolves. I continue with the 20 other Issues meanwhile and will deliver with whatever answers have arrived; an unanswered Issue stays open.

Escalation 1: I-20920b23da03573bb1c5354c2472ca03 (project_review, medium): when Git cannot list the tracked files, project_review examines no unowned file but its report still says deterministic.complete true, unowned [] and the verdict may be accepted, so the caller cannot tell a failed listing from a clean one. Today the run only adds host evidence ('the tracked files could not be listed') and carries their Issues (see also I-d7d4e73c, which I fix). Checks that cannot run already make deterministic.complete false and the Modules incomplete.
  Question: which option?
  Options: A: treat a failed listing like checks that could not run: deterministic.complete false, the root Module (owner of unowned files) and the project incomplete, with a stop link naming the Git error; add a scenario. Changes a report field's semantics only on this failure path; no earlier developer decision touched. | B: keep complete true and add an explicit field (e.g. deterministic.unowned_examined false) so the result is an explicitly partial success; verdict unaffected.
  Recommendation: A: one rule for every deterministic part that could not run, and the verdict never reads accepted when ownership was not examined.
  Why not mine: Choosing how an unexamined part shows in the report changes the observable report contract (contract.project-review.report), which the Issue's tier reserves above the task.

Escalation 2: I-4c12272ea87a5b44a8ee92126c7ee8ff (code_review, medium): code-review/module.md and scenario.code-review.spec-challenge say a Spec challenge is 'usually decision-needed', while the same entry says the task escalates 'every Spec challenge' as decision-needed; the reviewer prompt (prompts/workers/review-code.md) and the task-session guidance also say 'usually'. No exception is defined and the host does not touch a finding's tier.
  Question: which option?
  Options: A: every Spec challenge is decision-needed: the reviewer brief says so and the Operation records the tier decision-needed for every spec-challenge finding whatever the worker gave (host evidence notes a correction); entry, requirement, scenario and guidance say 'always'. Matches the rule that a promise change is decided above the task; changes no earlier developer decision. | B: keep 'usually' and define the exception: preferred-fix when another written promise (the Spec contradicting itself or a provider's contract) already settles the repair; the task handles it by tier like any Issue.
  Recommendation: A: simplest and safest; the main agent settles most such Issues itself anyway, and B leaves the worker to judge whether a promise change is already decided.
  Why not mine: Whether a Spec challenge may ever be fixed inside a task decides who may change a Module's promise, a policy the Issue's tier reserves above the task.

Escalation 3: I-5e812707a0055b72998ee147f536fc3e (spec_panel, medium, a spec-challenge): spec-review/panel.md host step 1 and its result-status table promise that an unknown named Module is 'incomplete' (panel_incomplete with the panel payload, the other Modules still paneled), but spec_panel uses Method's shared admission (src/concorde/method/specs.py admit_modules), which refuses the whole run with unknown_module before any step, as Execution's admission and every other Method Operation (code_review, project_review, ...) do. So today the run is refused and the incomplete branch in panel.py validate_modules is dead.
  Question: which option?
  Options: A: revise the panel's promise to what runs today: a named Module the workspace does not register refuses the run with unknown_module before any step, as for every Method Operation; drop the unknown case from step 1 and the status table, remove the dead branch, add a test. Changes a promise, but one no run has ever kept. | B: make spec_panel an exception to admission: register an admission that lets validate_modules mark an unknown Module incomplete and panel the others; document the exception in Spec review and Method.
  Recommendation: A: one admission rule for every Operation; a misspelled Module is a caller error better refused before any worker spends money; the implementation already behaves so.
  Why not mine: Either option changes a written promise of Spec review (the panel's per-Module outcome for an unknown Module) or makes spec_panel an exception to the common admission rule.

Escalation 4: I-bae9bb9b48d35315905f3807a98fe986 (Method, medium, spec-gap): Method's worker sequence (src/concorde/method/workers.py run_worker, interpreter_roots) adds to every worker's read-only runtime paths, besides the configured runtime paths, the directories the project interpreter needs: the interpreter's environment, the installation it resolves to, and each directory holding a symbolic link on the way, never /usr, the home itself or a directory holding the home. Workers' launch.md already says the caller lists what the interpreter needs among the runtime paths, but Method's workers.md does not state that it does so, which directories, the exclusions, or that the configured runtime paths neither replace nor limit them.
  Question: which option?
  Options: A: specify the current behaviour in Method's workers.md (worker limits / standard worker sequence), read-only, with its exclusions and its independence from the configured runtime paths, plus a requirement and a scenario backed by the existing interpreter_roots tests. No code change; no earlier developer decision touched. | B: drop the automatic expansion and require the developer to list the interpreter's directories under runtime in .concorde/workers.json; workers fail to run the project's Python until they do.
  Recommendation: A: workers must run the project's tests with its interpreter; the expansion is read-only, excludes the home and its ancestors, and Workers' Spec already expects the caller to list these directories.
  Why not mine: It concerns which host directories a worker may read outside its grant, i.e. the read boundary (security-adjacent), and documenting it makes the current automatic expansion a promise.

It carries escalation(s) 1, 2, 3, 4.

## Answer to report(s) 1 of the task session, 2026-10-13T11:35:26Z

Escalations 1-3 (main agent), each your recommendation: 1 A — a failed tracked-file listing makes the deterministic part incomplete (complete false, root Module and project incomplete, a stop link, new scenario). 2 A — a Spec challenge is always decision-needed, set by the Operation. 3 A — specify today's refusal of the whole run with unknown_module and drop the dead branch. Escalation 4 (I-bae9bb9b, automatic read access to the project interpreter's directories) touches the read boundary: the main agent takes it to the developer with other round-3 decisions in one batch. Do not change that behaviour; deliver the rest without it. It stays in resolves; the main agent reopens it after the merge if the developer's answer needs work.

## Escalated to the main agent, 2026-10-13T11:53:39Z

- **task-session** task session (task r3-reviews): `cross_module_change`
  I-2ebd101b (Method, medium, preferred-fix) has two halves. The round-check half is fixed in Method (commit 100feeb79: round validation now translates a SpecError with spec_cause instead of Check execution's unexpected_error). The admission half cannot be fixed inside my Modules: Method's admission (src/concorde/method/specs.py _registered) raises Execution's Refused('specs_unloadable') with the Spec error only as text, because Refused (src/concorde/execution/context.py) has no causes and the runner's _refused (src/concorde/execution/runner.py) builds the admission's component link without causes; specs/concorde/execution/runner.md lists the refusal's details (code, message, actor, reason, explanation, options) without causes. Separately, after your answer to escalation 2, specs/concorde/coordination/main-session/module.md:791 (module.main-session, task r3-task-session-main) still says a Spec challenge is 'usually decision-needed'.
  Not handled here (decision): Both changes lie outside this task's Modules (module.execution, module.main-session), each owned by a parallel round-3 task, and the brief reserves such changes above the task unless they are mechanical.
  Options: A: let r3-reviews make the Execution change here: an optional causes list on Refused, nested under the admission's component link by _refused, one line in runner.md's refusal details, Method's admission passing spec_cause(error), plus a regression test. About 10 lines in Execution; may conflict with r3-execution's edits of runner.py/runner.md.; B: leave the admission half to r3-execution or a later task (I-2ebd101b stays open, or a new Issue of module.execution is recorded for it) and deliver the round-check half now.; For the main-session wording: C: I change 'usually' to 'always' in that one sentence as a mechanical follow-on; D: it goes to r3-task-session-main or a later task.
  Recommendation: B and D: the admission refusal already carries the Spec error's text, so this is a structure-only loss on a rare path, and editing two parallel tasks' Modules invites merge conflicts; I record an Issue of module.execution for the admission half if you agree, and the merge closes I-2ebd101b only if you keep it in resolves.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-reviews)",
  "code": "cross_module_change",
  "detail": "I-2ebd101b (Method, medium, preferred-fix) has two halves. The round-check half is fixed in Method (commit 100feeb79: round validation now translates a SpecError with spec_cause instead of Check execution's unexpected_error). The admission half cannot be fixed inside my Modules: Method's admission (src/concorde/method/specs.py _registered) raises Execution's Refused('specs_unloadable') with the Spec error only as text, because Refused (src/concorde/execution/context.py) has no causes and the runner's _refused (src/concorde/execution/runner.py) builds the admission's component link without causes; specs/concorde/execution/runner.md lists the refusal's details (code, message, actor, reason, explanation, options) without causes. Separately, after your answer to escalation 2, specs/concorde/coordination/main-session/module.md:791 (module.main-session, task r3-task-session-main) still says a Spec challenge is 'usually decision-needed'.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Both changes lie outside this task's Modules (module.execution, module.main-session), each owned by a parallel round-3 task, and the brief reserves such changes above the task unless they are mechanical."
  },
  "options": [
    "A: let r3-reviews make the Execution change here: an optional causes list on Refused, nested under the admission's component link by _refused, one line in runner.md's refusal details, Method's admission passing spec_cause(error), plus a regression test. About 10 lines in Execution; may conflict with r3-execution's edits of runner.py/runner.md.",
    "B: leave the admission half to r3-execution or a later task (I-2ebd101b stays open, or a new Issue of module.execution is recorded for it) and deliver the round-check half now.",
    "For the main-session wording: C: I change 'usually' to 'always' in that one sentence as a mechanical follow-on; D: it goes to r3-task-session-main or a later task."
  ],
  "recommendation": "B and D: the admission refusal already carries the Spec error's text, so this is a structure-only loss on a rare path, and editing two parallel tasks' Modules invites merge conflicts; I record an Issue of module.execution for the admission half if you agree, and the merge closes I-2ebd101b only if you keep it in resolves.",
  "causes": []
}
```

## Report 2 to the main agent (Review流程), 2026-10-13T11:53:47Z

r3-reviews report 2 (escalation 5): one cross-Module decision before delivery.

Applied your answers. Escalation 1 (I-20920b23) A in 8a95021e1. Escalation 2 (I-4c12272e) A in df267236a. Escalation 3 (I-5e812707) A in 820679f75. I-bae9bb9b is untouched. Fixed so far: I-2594773c, I-361f3f71, I-d7d4e73c, I-f1c29147, I-c38c7738, I-e8ffbdb7, I-670ec40d, I-db212d60, I-c9124e94, I-6a5abcb8, I-8f04036a, I-2b869ae5, I-89901d04 and I-c1a8609d. I-2ebd101b is half fixed.

Escalation 5: I-2ebd101b's admission half needs Execution's admission refusal (Refused) to carry causes. That is module.execution, which r3-execution is changing. Separately, main-session/module.md:791 still says a Spec challenge is 'usually decision-needed'.
Options: A, make the ~10-line Execution change here, which risks a conflict with r3-execution. B, leave the admission half to r3-execution or a later task and record an Execution Issue. C, I fix the main-session sentence. D, leave it to r3-task-session-main.
Recommendation: B and D. If B, tell me whether I-2ebd101b stays in resolves; I suggest keeping it open, which needs task_resolve to drop it, or you reopen it after the merge.

I continue with the six low suggestions meanwhile.

It carries escalation(s) 5.

## Task session decisions, 2026-10-13

- I-a650412e (worker-record failure vs Tracing) no longer holds: commit d78a62134 aligned panel.md
  host step 6 with Tracing before this task; it stays in `resolves`.
- I-2594773c (preferred-fix): a Spec panel finding's path now "holds" only as an existing file inside
  the workspace after following symbolic links, readable in the returning worker's own grant (`ro`,
  `rw` or its glossary); relative and absolute paths are judged alike. Chosen over a containment-only
  check because panel.md already promised "a document member in the grant". The panel payload
  contract goes to version 7 since a behaviour changed.
- I-361f3f71 (preferred-fix): Code review locations must resolve inside the project after following
  links, relative or absolute; a deleted changed path still resolves through its remaining
  directories.
- I-2ebd101b (preferred-fix): fixed the round-check half in Method (spec_cause instead of Check
  execution's service_error). The admission half needs Execution's Refused to carry causes, outside
  this task's Modules: escalated (escalation 5) with a main-session wording follow-on.
- I-d7d4e73c (preferred-fix): settle_and_report takes the phases that could not run and carries all
  their earlier Issues, resolving none.
- Escalation 1 answer (A) applied: `unowned_unavailable` stop; report contract version 2; new
  req.project-review.unowned-unlisted and req.project-review.deterministic-unexamined with scenarios.
- Escalation 2 answer (A) applied: the Operation sets `decision-needed` on every spec-challenge
  finding and reports a `challenge-tier` host evidence item for each correction; new
  req.code-review.challenge-decided-above.
- Escalation 3 answer (A) applied: removed the dead unknown-Module branch of validate_modules; new
  scenario.spec-review.unknown-module.
- I-6a5abcb8: the stopped-panel case became scenario.spec-review.panel-stopped-earlier (a chair
  report left unaccounted on every attempt), which the existing test verifies.
- I-f1c29147: check-repaired now establishes a code change that repairs the check (what its test
  does) rather than `--full`; narrowed and record-refused use `--full`, as their tests do;
  skipped-resolutions establishes another Module's code change.
- I-c38c7738: narrowed req.spec-review.one-pass to reviewers and architects and said so in the
  shared checklist prompt; the chair audits only.
- Low suggestions all applied (none judged wrong or too costly): I-1ca86997 and I-e8e2852b by moving
  each entry's Overview forward (Project review's details now under "Findings, the record and the
  verdict"); I-2dba0450, I-4bcdb7ff, I-db212d60, I-dff8ab63 as suggested.
- I-bae9bb9b left untouched, as the main agent asked; it stays in `resolves` for the main agent to
  reopen after the merge.

## Answer to report(s) 2 of the task session, 2026-10-13T14:42:47Z

Escalation 4 I-bae9bb9b (developer, 2026-10-13): A — keep workers' automatic read-only access to the project interpreter's directories and specify it exactly in Method's Spec (scope: environment, resolved installation, symlink directories on the way, never /usr or home ancestors), with a requirement and a scenario; do it in this task. Escalation 5 (main agent): B and D — leave the admission half of I-2ebd101b to a later Execution task (the main agent records the Issue and reopens I-2ebd101b after the merge); do not touch module.execution. The main-session sentence ('usually decision-needed') goes to a follow-up too (r3-task-session-main has delivered); do not change it here. Deliver the rest.

## Task session decisions after answer 2, 2026-10-13

- I-bae9bb9b (developer's answer A), commit after 24ec9c3bd: "The interpreter's directories" in
  Method's workers.md (under Worker limits) specifies the environment, the resolved installation and
  each directory holding a symbolic link on the way. It excludes `/usr`, the home and every
  directory holding it, and every directory that does not exist. The configured `runtime` paths
  neither replace nor limit them, and they are read only. New req.method.interpreter-readable and
  scenario.method.interpreter-readable. No behaviour change. The computation moved from
  `run_worker` into `runtime_readable` (src/concorde/method/workers.py) so a unit test can verify
  the scenario. That test sits beside the existing interpreter_roots test in
  tests/concorde/implementation/test_operations.py (module.implementation, Method's child), since
  Method has no test directory of its own. I judged this a small mechanical follow-on.
- I-2ebd101b admission half and the main-session "usually" sentence left alone, as answer 2 asked.

## Report 3 to the main agent (Review流程), 2026-10-13T15:07:40Z

r3-reviews report 3: delivered as b594b33043e34e8b96cf1f72f1099f8d7b4c9746 on concorde/r3-reviews. task-validation was ready with nothing blocking, and the full suite passed on the final input (1479 passed, 5 skipped).

Since report 2: I-bae9bb9b was done with the developer's answer A in 8abf96e64. Method's workers.md has a new section, 'The interpreter's directories', under Worker limits. It names three directories: the environment, the resolved installation and each directory holding a symbolic link on the way. It never adds /usr, the home, a directory holding the home or a directory that does not exist. The configured runtime paths neither replace nor limit these directories, and they are read only. New req.method.interpreter-readable and scenario.method.interpreter-readable. Behaviour is unchanged. The computation moved into runtime_readable so a unit test verifies the scenario. That test is in tests/concorde/implementation/test_operations.py, beside the existing interpreter_roots test, because Method has no test directory of its own. I judged this a mechanical follow-on.

All 25 Issues in resolves are handled. Fixed: I-2594773c, I-361f3f71, I-d7d4e73c, I-f1c29147, I-c38c7738, I-e8ffbdb7, I-670ec40d, I-db212d60, I-c9124e94, I-6a5abcb8, I-8f04036a, I-2b869ae5, I-89901d04, I-c1a8609d and I-bae9bb9b. Fixed with your answers: I-20920b23, I-4c12272e and I-5e812707. The six low suggestions were all applied: I-1ca86997, I-e8e2852b, I-2dba0450, I-4bcdb7ff, I-db212d60 and I-dff8ab63. I-a650412e no longer held: d78a62134 fixed it before this task. The preferred-fix choices are in the decision log.

Still open, as answer 2 asked: the admission half of I-2ebd101b. It needs Execution's Refused to carry causes. Only the round-check half is fixed here (100feeb79), so you record the Execution Issue and reopen I-2ebd101b after the merge. Also open: the 'usually decision-needed' sentence at specs/concorde/coordination/main-session/module.md:791, left for a follow-up. Nothing needs the developer.

## Closed: merged, 2026-10-13T15:07:57Z

The merge answered report(s) 3 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b594b33043e34e8b96cf1f72f1099f8d7b4c9746 into main and closed it as merged. Nobody answers a report after that.
