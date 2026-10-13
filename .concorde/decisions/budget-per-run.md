# Decision log: budget-per-run

Goal: max_turns and max_budget_usd of the worker configuration bound a whole worker run: the host passes each round only the turns and budget still left

## Task brief (main agent, 2026-10-13)

Resolves I-b087813b (read it with `concorde issues show`). Today max_turns and max_budget_usd
bound each round (each `claude -p` gets the flags; pi's extension counters start at 0 per process),
so one worker run may spend (1 + resume rounds + transient retries) × the limit.

Developer decision (2026-10-13): **per run**. The host tracks the turns and cost every round of the
run used (from the run record's measured figures) and passes each new round only what is left;
when nothing is left, the run ends with the existing limit outcome (a refused or stopped round,
named as the run's limit) before launching another round. Applies to both backends, to resume
rounds and to transient retries. timeout stays per round unless you find that inconsistent; say
why either way. Update Workers' and Harness's Specs (requirement, the limits table, scenarios with
a two-round case) and the guidance text that describes limits; tests on both backends' argument
construction. If a backend cannot be told a fractional remaining budget exactly, state the
rounding (never above what is left). Deliver with task-validation then delivery; full suite once.

## Task session decisions (2026-10-13)

- **Measured cost of a resumed Claude Code round.** Claude Code 2.1.277+ restores a resumed
  session's saved totals, so a resumed round's `total_cost_usd` holds the session's earlier spend
  (docs: references/claude-code/agent-sdk/cost-tracking.md; confirmed live on 2.1.296 with the new
  live test: round 1 0.0160 USD, resumed round 2 reported 0.0229; `num_turns` 3 and 3, per call).
  Summing the reported figures would double-count. Decision: a round's usage `cost_usd` is its own
  cost: reported less the session's previous reported total when the stream's init record names a
  version ≥ 2.1.277; counted whole when the version is older/unknown or the reported total is below
  the earlier one (never counts less than spent). The reported total stays in the round content's
  `agent.claude.total_cost_usd`, and the version is kept as `agent.claude.claude_code_version`
  (contract.workers.worker-round-trace version 6 → 7). This also fixes the trace rollup, which
  double-counted resumed Claude Code rounds.
- **Rounding.** The budget left is rounded down to whole cents and passed as `%.2f`; less than a
  cent left is nothing left (also the configuration's minimum, and neither program accepts 0). Turns
  are whole numbers; `--max-turns 0` would mean unlimited on Claude Code, so a round never gets 0.
- **Nothing left.** No resume or retry round starts. After a retry-eligible error: `failed`
  `worker_limit_reached`, cause the agent process's link. After a repair that fails the run:
  `failed` `worker_limit_reached`, causes the round validation's links. After a repair that does not
  fail the run: `ok`, as when no rounds are left. The last round's node outcome is `limit_reached`.
- **pi transport.** The permission extension file stays identical for every round
  (req.workers.unchanged-across-rounds); the host passes the round's limits in the environment
  variable `CONCORDE_ROUND_LIMITS` (JSON). The extension applies the lower of that and the run's
  limits kept in its policy; a missing or malformed value allows nothing (fails closed). Chosen over
  regenerating the extension per round (would change the settings digest) and over a pi extension
  CLI flag (depends on pi's flag parsing).
- **timeout stays per round.** It guards against a hung round (kill of the process group); turns
  and budget measure model-service use that adds up across rounds, while the time between rounds
  (retry waits, round validation/checks) is not worker work; `rounds`/`retries` bound the number of
  rounds. Stated in launch.md#limits and req.workers.timeout-per-round.
- **Text outside the task's Modules.** The brief asked for the guidance text that describes limits:
  `prompts/guidance/worker_harness/skill.md` (owned by module.worker-harness) and one sentence in
  `docs/using-concorde.md` (module.concorde) now say the limits bound a whole run. Left unchanged:
  `specs/concorde/method/workers.md` (module.method), whose list is still correct.
- **Live tests run.** `CONCORDE_LIVE_CLAUDE=1` new test_a_resumed_round_counts_only_its_own_cost:
  ok. `CONCORDE_LIVE_PI=1` test_pi_live (2 tests, real pi reads CONCORDE_ROUND_LIMITS): ok, after a
  first attempt failed with `pi_runtime_missing` because CONCORDE_SANDBOX_RUNTIME was not set for the
  temporary fixture (environment, not a defect; rerun with it set).

## Report 1 to the main agent (Review流程), 2026-10-13T15:33:21Z

budget-per-run delivered: delivery commit 3d20d6b5d ("concorde: deliver budget-per-run") on concorde/budget-per-run, over b0799d07c. Resolves I-b087813b59bc5d4198229508545ddad0 (already in the task's resolves). task-validation r-20261013T151354-task_validation-39ae577e ready; delivery r-20261013T152334-delivery-a76f6f7d ok; full suite 1557 passed, 6 skipped; spec-validation success (5 pre-existing warnings in other Modules); build --check clean.

What changed: max_turns and max_budget_usd bound the whole worker run (first, resume and retry rounds together). Before each round Workers computes what the earlier rounds left from the rounds' usage: Claude Code gets it as --max-turns / --max-budget-usd, pi as the environment variable CONCORDE_ROUND_LIMITS, which the permission extension caps at the run's own limits in its policy (missing/malformed allows nothing). With no turn or less than a cent left, no further round starts: failed worker_limit_reached (cause: the agent process's link for a retry, the round validation's links for a repair), or ok for a repair that does not fail the run (as with no rounds left). Specs: launch.md new #limits section, rounds table, errors table, requirements req.workers.limits-per-run, limits-left-passed, limits-nothing-left, limits-nothing-left-outcome, round-own-cost, timeout-per-round; pi.md req.workers.pi-round-limits and env table; Harness pi.md limits and module.md tables; scenarios limits-per-run, limits-resumed-cost, limits-cumulative (two rounds each under the budget, together over), limits-nothing-left, pi-limits-per-run, pi-round-limits; tests on both backends' argument construction and the extension under Node.

Decisions I took (details in the decision log):
1. Rounding: budget left rounded down to whole cents, passed with two decimals; under a cent is nothing left. Never above what is left.
2. Resumed Claude Code cost: Claude Code 2.1.277+ reports a resumed session's restored earlier spend in total_cost_usd (verified live on 2.1.296: 0.0160 then 0.0229; num_turns per call). A round's usage cost is now its own: reported minus the session's previous total when the stream's init record names a version >= 2.1.277, else counted whole (never undercounts). Round content keeps total_cost_usd and adds claude_code_version; contract.workers.worker-round-trace version 6 -> 7. This also fixes the trace rollup, which double-counted resumed Claude Code rounds.
3. pi transport via env var so the extension file stays identical across rounds (req.workers.unchanged-across-rounds).
4. timeout_seconds stays per round: it guards a hung process; turns and budget measure model-service use that adds up, while the time between rounds (retry waits, checks) is no worker's work.
5. Outside the task's Modules, as the brief's "guidance text" asked: prompts/guidance/worker_harness/skill.md (module.worker-harness) and one sentence in docs/using-concorde.md (module.concorde). specs/concorde/method/workers.md (module.method) left unchanged; it is still correct.

Live runs: CONCORDE_LIVE_CLAUDE new resumed-cost test ok; CONCORDE_LIVE_PI both pi live tests ok (first attempt failed with pi_runtime_missing only because CONCORDE_SANDBOX_RUNTIME was unset for the temp fixture; recorded).

Open: nothing needs the developer. Ready for task merge.

## Closed: merged, 2026-10-13T15:33:47Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 3d20d6b5d3b6b3d8f19f18b566a104a052c88819 into main and closed it as merged. Nobody answers a report after that.
