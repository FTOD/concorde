# Decision log: r2-worker-harness

Goal: Fix the critical, high and obvious-fix open Issues of Workers, Harness and Worker harness found by the complete project_review

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 16 Issues in its `resolves`,
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

## Task session decisions (2026-10-08)

None of the 16 Issues is `decision-needed`, so nothing was escalated. Every Issue held when read
against the base commit; none was a duplicate or already fixed. Two Issues are one gap seen twice
(I-3b723b40 by the architecture review, I-c4f45b0e by the Harness panel) and one fix resolves both.

Code (commit 6c20195f8):
- I-1503b903 (high, preferred-fix): `finish()` now looks up the transcript of the latest session
  whenever a session was named; when none is found it records a cleanup problem naming the session
  and the configuration directory, so the run ends `cleanup_failed` with the earlier link as cause
  (both backends tested with a new `no_transcript` fake option). Chosen over keeping an older
  session's transcript, which would mislabel it as the latest.
- I-e134cf3f (high, obvious-fix): `ClaudeStream.conclude` falls back to the session the stream
  announced. Found while testing: the single-line case was masked because `envelope_of` takes a
  lone JSON record (the init record) as the envelope; the unit test uses two lines so it fails
  without the fix. That `envelope_of` quirk is left as is (out of scope, harmless here).
- I-0f82d74b (medium, obvious-fix): failures of the final trace write are appended to the
  returned record's `trace_failures` and to a non-ok run's error evidence, without duplicates.
- I-53b6b957 (medium, obvious-fix): a final symbolic link (dangling or to a directory) is deleted
  as an entry; launch.md's table and scenario.workers.deletion-through-link-refused now say so.

Specs (commit 55f841ea5):
- I-047d9e04 (preferred-fix): req.workers.frozen-grant / unchanged-across-rounds list the parts
  per backend (worker settings + write hook on Claude Code, permission extension on pi, tool set
  and brief on both).
- I-393874353 (preferred-fix): new launch.md section "Calling Workers" naming the real entry points
  (`models.load`, `check_mapped`, `worker_choice`, `limits`, `runtime`, `WorkerRequest`,
  `run_worker`, `result_schema`), the `output_schema`/`started`/`round_validation` fields and one
  representative call; the entry links it. Documented the existing interface, invented none.
- I-51ab2a2e (preferred-fix): scenario.workers.brief-terms and brief-review-gaps now give
  caller-composed instructions and assert Workers keeps them unchanged and appends the boundary
  from the grant's lists only; the Inputs table and the entry no longer say the grant carries
  terms. The brief-review-gaps test now builds the brief through Workers.
- I-5685cfc4 (preferred-fix): "Reading beside the grant" scopes the exclusivity to the protected
  material and names the worker's scratch directories and system paths, linking the Harness tables.
- I-72bfd8b8 (obvious-fix): the entry describes each backend's environment list and links both
  tables.
- I-d8f20d28 (obvious-fix): req.workers.model-map-whole-operation refuses only when a mapping is
  missing; the entry says the check passes otherwise.
- I-a93b0fa5 (obvious-fix): split into req.workers.deletion-failure (continue) and the new
  req.workers.deletion-failure-reported (fail the run).
- I-9ba57660 (preferred-fix): the Worker harness entry explains resumes and transient retries as
  the two ways to another round, each with its limit, linking launch.md#retries.
- I-3b723b40 + I-c4f45b0e (preferred-fix): Harness now `uses` module.workers with `relies_on` the
  grant-input and worker-result contracts and the 14 requirements it already cited, selecting
  Workers' entry, contracts.md, launch.md and pi.md (verified with `grant`); the text says this is a
  Spec reliance, not a code dependency. Mutual uses is allowed by the Protocol. Registry refreshed.
- I-34ad0d2d (obvious-fix): the Harness's known limit now separates the sandbox engine's lists from
  the extension's whole policy.
- I-e103e686 (obvious-fix): the guidance names `$XDG_CONFIG_HOME/concorde/models.json`, its
  absolute-path condition and the precedence of an absolute `CONCORDE_MODEL_MAP`.

spec-validation: success, same 5 pre-existing warnings in these Modules, none new.

## Report 1 to the main agent (Review流程), 2026-10-08T14:15:29Z

r2-worker-harness delivered: delivery commit a8489f8aa (run r-20261008T140428-delivery-2108868a) on concorde/r2-worker-harness; task-validation r-20261008T135324-task_validation-86f24516 ready; full suite 1378 passed, 5 skipped; spec-validation success with no new warnings.

All 16 Issues in resolves are fixed; none was decision-needed, none failed to hold, none was a duplicate. No escalation.

Code (6c20195f8): I-1503b903 a named session whose transcript is missing now fails the run cleanup_failed (both backends tested); I-e134cf3f a Claude round without its envelope keeps the session its stream announced (unit test; the single-line case had been masked by envelope_of taking a lone init record as envelope, left as is); I-0f82d74b the final trace write's failure reaches a non-ok run's error evidence; I-53b6b957 dangling and directory symlinks are deleted as entries, targets untouched (launch.md table and scenario extended).

Specs (55f841ea5): I-047d9e04 frozen-grant/unchanged-across-rounds list parts per backend; I-393874353 new launch.md "Calling Workers" naming models.load/check_mapped/worker_choice/limits/runtime, WorkerRequest, run_worker, result_schema, the output_schema/started/round_validation fields and one call; I-51ab2a2e both brief scenarios now take caller-composed instructions (test for brief-review-gaps now builds the brief through Workers; also removed "terms the grant carries" from Inputs and the entry); I-5685cfc4 read exclusivity scoped to protected material, scratch dirs and system paths named; I-72bfd8b8 entry describes each backend's env list and links both tables; I-d8f20d28 model-map check refuses only when a mapping is missing; I-a93b0fa5 split into req.workers.deletion-failure and new req.workers.deletion-failure-reported; I-9ba57660 Worker harness entry explains resume vs transient retry with separate limits; I-3b723b40 + I-c4f45b0e (one gap) Harness now uses module.workers with relies_on the grant-input and worker-result contracts and the 14 requirements it cites (grant check confirms Workers' entry, contracts.md, launch.md, pi.md are now in Harness's Spec context; registry refreshed); I-34ad0d2d Harness known limit separates sandbox lists from the extension's policy; I-e103e686 guidance names $XDG_CONFIG_HOME/concorde/models.json and the CONCORDE_MODEL_MAP precedence.

Preferred-fix choices: missing transcript fails cleanup rather than keeping an older session's transcript; the calling interface documents existing entry points, invents none; Harness->Workers is a Spec-only uses (mutual uses is allowed by the Protocol).

Open: nothing for this task. Not in scope and not filed: envelope_of treats any single JSON line as the result envelope (harmless after this fix).

## Closed: merged, 2026-10-12T14:27:45Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit a8489f8aa5e88b77f2242142a1849abea7f01f20 into main and closed it as merged. Nobody answers a report after that.
