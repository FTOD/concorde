# Decision log: fix-open-workflows

Goal: Fix the open Issues of the workflow part (Workflows)

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

- I-f3ffb788 (200-call cap): keep the runaway guard and state it in req.workflows.script-repeats with what the step function reports when it is reached.
- I-c718ab75 (run started but not recorded): record the step as starting (key and node, no run yet) before the run is launched, and have the next call adopt the run found in that step's node instead of starting another; align module.md "The step command" and req.workflows.key-idempotent.
- I-32c275f2 (first step lost before any record): `concorde workflow report --workflow <name> --lost <key>` builds and saves a failed workflow result when no record exists; add the scenario.

### Your 20 Issues

- I-f3ffb78892b353d98f89ca7b31c656ad (medium, decision-needed, module.workflows): The script's 200-call cap is not in the Spec
- I-c718ab75f46f59f2aa46456b894183a5 (medium, decision-needed, module.workflows): A run started but not recorded can be started again under the same key
- I-c9732ed8ffd459b5b2346bd87996eed6 (medium, preferred-fix, module.workflows): Step calls can overrun --wait while the workflow lock is held or a launcher stalls
- I-56b26ba3dbc15185910e14cfddac0ca8 (medium, preferred-fix, module.workflows): A retried step that fails between two relays is started once more
- I-4ce236ae977c56e4aae5e2ea212a685f (medium, preferred-fix, module.workflows): Relay check compares only the base key and accepts finished outcomes without a run
- I-bf7b23f6d4735c9ca8597dbc1d12356d (medium, preferred-fix, module.workflows): Invalid command names create unreportable refused steps
- I-1e74d6d73b6c5bdababf730a4e2c2923 (medium, obvious-fix, module.workflows): Process-launch errors bypass refused-step recording
- I-32c275f261eb5730be39ac5cced576a6 (low, decision-needed, module.workflows): A first step lost before any record makes the report refuse no_workflow
- I-11482e726d435dbb808f778e1cb1a3d7 (low, preferred-fix, module.workflows): A retried step's nodes share one step key as their identity
- I-eda1d4e903725cccb72373fc5abd73db (low, obvious-fix, module.workflows): A wrongly shaped workflow record escapes record_unreadable
- I-4cd0caa850b251edb324e6483421b09b (low, obvious-fix, module.workflows): Finished step nodes store the run status, not the state, as outcome
- I-439dfebba1c45d6cba734a25f08aa676 (low, obvious-fix, module.workflows): A lost step's trace node carries a reduced step_lost link
- I-9d32dde972c9524aa2fe0dcd6e3b6199 (low, obvious-fix, module.workflows): Workflow link gives reason decision for a last step lost or refused
- I-de9a2e372a2a58e0a2c3a3c1d249a4dd (low, obvious-fix, module.workflows): The report's 'step the procedure stopped at' is not defined as the latest current step
- I-8105482148465ca4b32da2afa3e74e62 (low, obvious-fix, module.workflows): req.workflows.step-lock carries a second SHALL NOT in its explanation
- I-7b8ad4b40d32525482663089098bc019 (low, obvious-fix, module.workflows): The entry says the record names its mode once; record and result carry the latest step's mode
- I-ebfe7757e89c5342851b46181b70e705 (low, obvious-fix, module.workflows): req.workflows.answers-input does not say what happens without an ok run of the base key
- I-db4ce098991d56709832a2d75704a53f (low, suggestion, module.workflows): Clarify nullable run identity and result-path semantics
- I-48d13318ea9d5f1d83e11f41146560d0 (low, suggestion, module.workflows): Clarify the relay wording in the one-source explanation
- I-85b11ef92cb95027b5eb395079d48be2 (low, suggestion, module.workflows): Move the digest and step-folder encoding details out of the entry

## Task session decisions (2026-10-04)

All 20 Issues are handled in Specs, code and tests; no Operation was run.

- **I-f3ffb788 (decision carried out):** req.workflows.script-repeats now states the 200-call cap and
  that the step function then resolves to the last outcome that said the run was running.
  Decision of my own: a call at the cap that brings no answer also resolves to that last running
  outcome instead of `null`, so one bad relay near the cap no longer reports the step lost (the
  issue's second impact); relay-asked-again names the cap as its second stop.
- **I-c718ab75 (decision carried out):** the step is recorded as starting (key, node, no run, no
  error) before the launch, and `set_run` writes the run or the refusal afterwards. A later call
  that finds a starting step adopts the run found in `run/` of its node. Decisions of my own for
  the case the brief left open, no run in the node: while a run of the workspace holds the
  workspace lock or waits in the lobby (Execution's `waiting_runs`), the call waits as for the
  workspace lock, since that run may be the step's; otherwise the run never started, so the call
  ends the starting node lost (`step_lost`) and starts the run anew under the same key, the new
  attempt superseding the starting one. The report treats a starting step the same way
  (running / lost). `step_unrecorded` now means "recorded as starting, run named, adopted next
  call"; the brownfield script's handling of it is unchanged and still correct. Residual window,
  accepted: a launcher orphaned in the half second before its runner takes its run lock.
- **I-c9732ed8 (preferred-fix chosen):** the workflow lock is taken within the remaining wait
  (`running`, no run, exit 3 when still held); polls never sleep past the deadline; the launch is
  not cut at the bound (a launcher ended halfway could leave a run its step cannot name) but is
  bounded at 90 s (`LAUNCH_WAIT`, Execution's 60 s announcement wait plus startup), after which it
  is ended and the step recorded refused. req.workflows.bounded-wait states "+ at most 90 s for the
  announcement of a run it starts". Rejected: cutting the launch at the deadline (would let a
  short `--wait` orphan runs and start duplicates).
- **I-56b26ba3 (preferred-fix chosen):** the script leaves `retry` out of every call after an outcome
  that names a run (new req.workflows.retry-once). A call that waited for the workspace lock names
  no run and keeps `retry`; after a relay miss `retry` is kept too, since dropping it could
  silently skip the retry. Rejected: a server-side retry token, which would change the request
  contract and the relaunch semantics of `args.retry`.
- **I-4ce236ae (preferred-fix chosen):** `checked()` compares the full key: base key plus `#label`
  exactly, plus `@` and eight hex digits by shape for an answered step (the script computes no
  SHA-256); state must be one of the four; no run only for `refused` or `running`.
- **I-bf7b23f6 (preferred-fix chosen):** `check_request` refuses an `argv[0]` not matching
  `^[a-z][a-z_-]*$` as `invalid_request` (exit 2) before anything is written; the schema dialect
  cannot constrain the first item, so the step-request semantics state it.
- **I-1e74d6d7:** an `OSError` (and the new launch timeout) becomes `step_refused` with a
  `run_not_started` cause and is recorded.
- **I-32c275f2 (decision carried out):** `concorde workflow report --workflow <name> [--mode <mode>]
  --lost <key>` builds and saves a failed result when no record exists, creating the workflow's
  node; new req.workflows.lost-first and scenario.workflows.lost-first. Decision of my own: also
  `--mode` (the script passes `args.mode`) so the result carries the right mode, and a
  `--workflow` naming another workflow than the recorded one is refused `workflow_conflict`.
  claude.js `report()` always passes `--workflow` and `--mode`; the installed permission prefix
  `Bash(.concorde/bin/concorde workflow report:*)` still matches.
- **I-11482e72 (preferred-fix):** a step node's id is its folder name `<n>-<key>`; small edit in
  Tracing's contract (node kinds row `step` and the id rule in contract.tracing.node semantics),
  the kernel group's file. Nothing in Concorde reads step node ids.
- **I-eda1d4e9:** `store.load` validates the record's content as the registered typed value; any
  wrong shape is `record_unreadable`.
- **I-4cd0caa8:** step node outcome is the state. **I-439dfebb:** the step node of a lost step gets
  the full `lost_link` (host output evidence, `host_ended` cause); the report now ends step nodes
  itself (moved out of `store.record_report`). **I-9d32dde9:** report reasons per error table
  (failed → decision, lost → environment, refused → input).
- **I-de9a2e37, I-7b8ad4b4, I-ebfe7757, I-81054821 (Spec):** status precedence defined by the latest
  current step; record names the workflow once and carries the latest step's mode;
  answers-input states "no --input without an ok run"; step-lock split, new
  req.workflows.workflow-lock-leaf.
- **Suggestions I-db4ce098, I-48d13318, I-85b11ef9:** fixed (cheap, in text being rewritten anyway):
  run_id/result_path semantics split with null cases and lobby/node locations; one-source wording;
  digest and folder encoding moved out of module.md to the requirement and workflow-trace contract.
- Contract versions bumped: step 7, step-request 7, result 9, workflow-trace 2, step-trace 2 (the
  registered typed values too). Rapid-iteration rule: a workflow record of version 1 in a
  workspace still running a workflow is unreadable after the merge (`record_unreadable`).

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:43:14Z

fix-open-workflows delivered: delivery commit ac0b9b55 (run r-20261004T023541-delivery-2fce4880) on concorde/fix-open-workflows, on top of 77aabe61. Checks: build --check, spec-validation (0 findings), full suite 1092 passed / 5 skipped, task-validation ready.

Resolved (all 20 added with task resolve; none closed, none left open):
- I-f3ffb788 (your decision): req.workflows.script-repeats states the 200-call cap and that the step then resolves to its last running outcome. My own addition: a call at the cap that brings no answer also resolves to that running outcome instead of null.
- I-c718ab75 (your decision): the step is recorded as starting (key, node, no run) before launch; set_run writes the run or refusal; a later call adopts the run in run/ of the step's node. My own choice for "no run in the node": wait while a run of the workspace holds the workspace lock or waits in the lobby; otherwise the run never started, so the node is ended lost and the run started anew (superseding). The report shows such a step as running or lost. step_unrecorded now leaves the step starting, so the next call adopts it. Small window accepted: a launcher orphaned in the half-second before its runner takes its run lock.
- I-32c275f2 (your decision): `workflow report --workflow <name> [--mode <m>] --lost <key>` builds and saves a failed result with no record (creating the workflow node). New req.workflows.lost-first and scenario.workflows.lost-first. My additions: --mode, and workflow_conflict when --workflow differs from the record. claude.js report() always passes both; the installed permission prefix still matches.
- Preferred fixes chosen: I-c9732ed8, bounded workflow-lock wait (running with no run when the bound ends), polls capped at the deadline, launch bounded at 90 s, then ended and recorded refused (bounded-wait says "+ at most 90 s for announcing a run it starts"). I rejected cutting the launch at the deadline because it would orphan or duplicate runs. I-56b26ba3, the script drops retry after an outcome names a run (new req.workflows.retry-once). I rejected a server-side retry token because it would change the request contract and the meaning of args.retry. I-4ce236ae, full key check (label exact, digest by shape, known state, no run only when refused or running). I-bf7b23f6, argv[0] name checked in check_request (invalid_request, exit 2, nothing written). I-11482e72, the step node id is now its folder name <n>-<key>.
- Obvious fixes: I-1e74d6d7 (OSError or timeout gives step_refused/run_not_started, recorded), I-eda1d4e9 (record validated as a typed value, so any wrong shape is record_unreadable), I-4cd0caa8 (node outcome = state), I-439dfebb (the lost node gets the full lost_link), I-9d32dde9 (report reasons follow the error table), I-de9a2e37, I-7b8ad4b4, I-ebfe7757, I-81054821 (new req.workflows.workflow-lock-leaf).
- Suggestions fixed because they were cheap: I-db4ce098, I-48d13318, I-85b11ef9.

Files outside module.workflows, all small edits: specs/concorde/kernel/tracing/contracts.md (the step row of the node-kinds table and the id rule, for I-11482e72) and tests/concorde/e2e/test_e2e.py (fixture schema_version 1 to 2).
Contract versions bumped: step 7, step-request 7, result 9, workflow-trace 2, step-trace 2 (the typed values too). Under the rapid-iteration rule, a version-1 workflow record of a workflow still running at merge time becomes record_unreadable.
Open: nothing needs the developer. All decisions are in the decision log.

## Closed: merged, 2026-10-04T02:43:41Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit ac0b9b55f768ca43b8a4fe395810616a63608dd9 into main and closed it as merged. Nobody answers a report after that.
