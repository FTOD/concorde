# Decision log: r4-workers

Goal: Fix the critical and high open Issues of Workers, Harness and Worker harness found by the fourth project_review

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

## Escalated to the main agent, 2026-10-17T04:36:37Z

- **task-session** task session (task r4-workers): `round_validation_contract`
  Issue I-b6db08680c2858808a3b648d8e249caa (decision-needed, high): launch.md 'Round validation' names the callback's answer fields (evidence, repair, failure, violation, unavailable) but no concrete Python representation, no signature and no handling of a malformed or conflicting answer. What the code already does (src/concorde/worker_harness/workers.py:218-244, 1280-1340): the callback is called as round_validation(worktree: Path, round_folder: Path, result: dict) and must return workers.RoundValidation(evidence: tuple of mappings = (), repair: str|None = None, failure: Refusal|None = None, violation: Refusal|None = None, unavailable: Refusal|None = None), where workers.Refusal(code: str, detail: str, causes: tuple of links = ()). A non-RoundValidation answer or a raised exception ends the run failed with validation_unavailable (reason capability). Conflicting fields are resolved silently by precedence unavailable > violation > repair; a failure without a repair is ignored; an evidence item that is not a mapping raises outside the guarded call and escapes run_worker uncaught (a robustness bug I will fix in either option). Method (src/concorde/method/workers.py:471-516) is the only caller and never combines fields. I can document either way; both need the Spec to name these two types and their fields (a new interface promise of module.workers), with clean, repair, violation and unavailable examples.
  Not handled here (decision): The Issue is decision-needed: choosing the public representation and the handling of an invalid answer adds interface promises of module.workers that callers rely on.
  Options: A: document the existing contract as it is (RoundValidation and Refusal dataclasses, precedence unavailable > violation > repair, failure ignored without repair); only a malformed answer (not a RoundValidation, evidence item not a mapping, a Refusal without code or detail) ends validation_unavailable. No behaviour change for any valid answer today.; B: document the same two types but make the answer strict: exactly one of repair, violation, unavailable or none of them; failure only with a repair; any other combination or malformed value ends the run failed with validation_unavailable, naming what is wrong. Changes behaviour only for combinations no caller makes today.
  Recommendation: B: one meaning per answer and an explicit refusal of anything else is the easier contract to state and to rely on; Method needs no change. Neither option changes a promise users rely on or an earlier developer decision.

```json
{
  "level": "task-session",
  "actor": "task session (task r4-workers)",
  "code": "round_validation_contract",
  "detail": "Issue I-b6db08680c2858808a3b648d8e249caa (decision-needed, high): launch.md 'Round validation' names the callback's answer fields (evidence, repair, failure, violation, unavailable) but no concrete Python representation, no signature and no handling of a malformed or conflicting answer. What the code already does (src/concorde/worker_harness/workers.py:218-244, 1280-1340): the callback is called as round_validation(worktree: Path, round_folder: Path, result: dict) and must return workers.RoundValidation(evidence: tuple of mappings = (), repair: str|None = None, failure: Refusal|None = None, violation: Refusal|None = None, unavailable: Refusal|None = None), where workers.Refusal(code: str, detail: str, causes: tuple of links = ()). A non-RoundValidation answer or a raised exception ends the run failed with validation_unavailable (reason capability). Conflicting fields are resolved silently by precedence unavailable > violation > repair; a failure without a repair is ignored; an evidence item that is not a mapping raises outside the guarded call and escapes run_worker uncaught (a robustness bug I will fix in either option). Method (src/concorde/method/workers.py:471-516) is the only caller and never combines fields. I can document either way; both need the Spec to name these two types and their fields (a new interface promise of module.workers), with clean, repair, violation and unavailable examples.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is decision-needed: choosing the public representation and the handling of an invalid answer adds interface promises of module.workers that callers rely on."
  },
  "options": [
    "A: document the existing contract as it is (RoundValidation and Refusal dataclasses, precedence unavailable > violation > repair, failure ignored without repair); only a malformed answer (not a RoundValidation, evidence item not a mapping, a Refusal without code or detail) ends validation_unavailable. No behaviour change for any valid answer today.",
    "B: document the same two types but make the answer strict: exactly one of repair, violation, unavailable or none of them; failure only with a repair; any other combination or malformed value ends the run failed with validation_unavailable, naming what is wrong. Changes behaviour only for combinations no caller makes today."
  ],
  "recommendation": "B: one meaning per answer and an explicit refusal of anything else is the easier contract to state and to rely on; Method needs no change. Neither option changes a promise users rely on or an earlier developer decision.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-17T04:36:43Z

Early escalation (task brief asks decision-needed Issues first). One decision-needed Issue: I-b6db08680c2858808a3b648d8e249caa, the round validation callback contract; escalation 1 carries what the code does, options A (document as is, tolerant precedence) and B (document the same types, strict: conflicting or malformed answers end validation_unavailable), recommendation B. Neither option changes a promise users rely on or an earlier developer decision. I continue meanwhile with the five preferred-fix Issues (I-330deb19 submodule audit, I-784183eb Git-path discovery errors, I-8d81a10b pi tool processes outliving the round, I-ac253e5b launch example limits, I-e5c7493f refused directory search, which is a trailing-slash bug in the pi extension's search decision).

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-17T04:37:00Z

Escalation 1 round_validation_contract (main agent): B — document RoundValidation and Refusal strictly: exactly one of repair, violation or unavailable, or none; failure only with a repair; any other answer, a non-mapping evidence item or a raised exception ends validation_unavailable naming what is wrong. Method is the only caller and never combines fields, so nothing relied on breaks; check Method's callers still pass under the strict rule.

## Task session decisions (2026-10-17)

- **I-e5c7493f (refused directory search), preferred-fix.** The cause was in the pi extension, not
  in the brief: Node's `path.normalize` keeps a trailing separator, so the search root
  `specs/concorde/worker-harness/harness/` became the relative path `…/harness/`, below which no
  entry starts with `…/harness//`. Fix: `normal()` in `pi_policy.ts` strips trailing separators for
  every read, write and search decision. Harness pi.md states the rule. Method's brief that tells
  a reviewer to stop after a refusal is left as it is, since it is outside this task's Modules and
  the refusal was wrong. Verified by a policy test and by the live pi test (`CONCORDE_LIVE_PI=1`),
  which now greps `specs/a/` whose one file is granted alone.
- **I-ac253e5b (launch example drops limits), preferred-fix.** The code (Method) already forwards
  every limit. Only the Spec example was incomplete. Fix: the example forwards all six limits, and a
  table maps each configured limit to its request field (`max_budget_usd=None` means no budget).
- **I-784183eb (Git-path discovery continues after errors), preferred-fix.** New refusal
  `git_paths_unavailable` (reason `environment`), raised before anything is generated, when
  `git rev-parse` fails or names fewer than 2 directories, a directory of the walk cannot be
  listed, a `.git` file cannot be read, or an existing `commondir` cannot be read. An absent
  `commondir` stays no failure. New requirement `req.workers.git-paths-complete` and scenario.
  Chosen over a warning because the requirement promises every Git path hidden.
- **I-330deb19 (submodules in the write audit), preferred-fix.** The audit now measures every
  nested repository inside, at any depth: initialized submodules (gitlinks with a `.git`) and
  untracked nested repositories that `git status` reports as a directory. Their files are keyed by
  their worktree-relative paths. Each nested repository's HEAD and index are compared too. A change
  is reported as `<path>: HEAD` or `<path>: index`. A submodule's own status record is no longer
  taken as a file, which removes the false `(deleted)`. An unborn HEAD is measured as `unborn`
  rather than failing the snapshot. Untracked nested repositories are included because they had
  the same gap.
- **I-8d81a10b (pi tool processes outlive the round), preferred-fix.** Chosen: explicit
  registration rather than a supervisor. The permission extension writes an empty file named by
  each tool command's process group id to `control/groups/` (a policy field) and removes it when
  the command ends. When a group cannot be registered, the command is stopped and refused. After
  killing pi's group at every round end, the host kills every registered group and clears the
  folder. This works on macOS and Linux and needs no new process. Known limit, not fixed: a
  command that leaves its own group (`setsid`) is still not reached on macOS. On Linux, bwrap's
  `--die-with-parent` and its PID namespace end it.
- **I-b6db0868 (round validation contract), decision-needed.** Escalated as escalation 1. The main
  agent chose option B (strict). It is implemented with `workers.answer_problem`: exactly one of
  repair, violation or unavailable, or none of them; failure only with a repair; no evidence with
  unavailable; typed fields. Anything else ends `validation_unavailable` (reason `capability`),
  naming what is wrong. Method's callers satisfy the rule: they never combine fields, and their
  causes are link dicts. The implementation, validation and general-work suites pass.

- **Non-ok result: task-validation r-20261017T045429-task_validation-a83ae55a ended `blocked`
  (`not_deliverable`).** Its one blocking finding is `check.views.repository-regressions` of
  module.views, exit 1. The log shows `ENOSPC: no space left on device` (definition-titles test) and
  a failed Docusaurus production build in the same run. `df` showed `/` at 100%, 2.0G available,
  on the disk the parallel r4 tasks share. This is an environment failure, not one of this task's
  changes. Every other check passed. The full pytest suite passed (1599 passed, 6 skipped).

## Report 2 to the main agent (Review流程), 2026-10-17T05:24:34Z

r4-workers delivered: delivery commit 32a21b9cd3a9377b5d177604d68e40c5f2c61174 (delivery run r-20261017T051434-delivery-2d8d945e). task-validation r-20261017T050347-task_validation-bb5d810a ok. Full pytest suite passed (1599 passed, 6 skipped). The live pi test (CONCORDE_LIVE_PI=1) passed. The task resolves all six Issues in resolves.
Fixes and choices:
- I-e5c7493f (preferred-fix): the cause was a trailing-slash bug in pi_policy.ts. Node's normalize keeps 'dir/', so a search root such as specs/x/ was judged as holding nothing readable. Fix: strip trailing separators for every read/write/search decision; the Harness pi.md states the rule. The live test now greps such a directory.
- I-ac253e5b (preferred-fix): the code already forwarded every limit. The Spec example now forwards all six, with a table from configured limit to request field.
- I-784183eb (preferred-fix): new refusal git_paths_unavailable (environment) before anything is generated, when rev-parse fails, a walked directory cannot be listed, or a .git or existing commondir file cannot be read. An absent commondir is still fine. New req.workers.git-paths-complete and scenario.
- I-330deb19 (preferred-fix): the audit now measures every nested repository inside, at any depth: initialized submodules and untracked nested repos. Files are keyed by worktree-relative path. Each nested repo's HEAD and index are compared (violations '<path>: HEAD' and '<path>: index'). The false '(deleted)' for a submodule is gone.
- I-8d81a10b (preferred-fix): chose explicit registration over a supervisor. The pi extension registers each tool command's process group in control/groups/. The host kills every registered group after killing pi's group at each round end. A command whose group cannot be registered is refused. Known limit left: a command that setsid's itself out of its group is still not reached on macOS.
- I-b6db0868 (decision-needed): implemented your option B. RoundValidation and Refusal are specified with types and examples. Any conflicting or malformed answer ends validation_unavailable (capability), naming what is wrong. Method's callers satisfy it.
Non-ok result: the first task-validation (r-20261017T045429-task_validation-a83ae55a) was blocked by check.views.repository-regressions failing with ENOSPC. The shared disk was at 100% with about 1 GB free. The retry passed. That is an environment risk for the other r4 tasks too.
Open: nothing for the developer. The task branch is not pushed; your task merge is local.

## Closed: merged, 2026-10-23T09:01:30Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 32a21b9cd3a9377b5d177604d68e40c5f2c61174 into main and closed it as merged. Nobody answers a report after that.
