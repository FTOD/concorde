# Decision log: worker-transient-retry

Goal: Workers retries a worker round that a transient model-service error ended, a bounded number of times with backoff, and project_review lowers its default parallelism

## Task brief (main agent, 2026-10-08)

Resolves I-558971fc. The first full project_review, r-20261008T024839-project_review-a7857ff6
(default --parallel 4, about 16 concurrent pi workers on one provider), had 52 pi runs end with
"gateway_concurrency_limit: Concurrency limit exceeded for user, please retry later"; Workers does
not retry a failed pi process, so 48 review parts ended incomplete.

Decided by the main agent:
- Workers retries a worker round that a **transient model-service error** ended (concurrency or
  rate limit, overload, an explicit retry-later), on both backends where the program reports it,
  a bounded number of times with backoff (exponential with jitter; defaults yours, configurable in
  the worker configuration's `limits` if that fits), recording every attempt in the run record.
  Any other error still fails at once. Retry resumes or restarts the round as is safe: a round that
  wrote files must not be replayed blindly (the write audit must stay exact).
- project_review's default `--parallel` is lowered (2 suggested; yours to choose with a reason).

Read the transcripts under `.concorde/unbound/r-20261008T024839-project_review-a7857ff6/workers/`
for the exact error shape. Deliver with `task-validation` then `delivery`; run the full suite once
on the final input.

## Task session decisions (2026-10-08)

Evidence read: r-20261008T024839-project_review-a7857ff6 has 57 pi worker runs that ended with
stop reason `error`: 51 `gateway_concurrency_limit: Concurrency limit exceeded for user, please
retry later`, 5 `Upstream HTTP/2 stream failed`, 1 `Request timed out.`. 24 of them failed on the
first model call (no tool call yet); the others failed mid-session after 1 to 45 tool results, so
a retry must continue the session, not replay the brief. pi's own agent-level retry (enabled by
default, 3 attempts) did not fire for the concurrency error: its classifier
(`isRetryableAssistantError`) matches neither "concurrency limit" nor "please retry later".

1. **A retry is a round of its own** (prompt kind `retry`), with its own node, standard error,
   usage and audit, so every attempt is recorded. It continues the round's session (pi: the run's
   fixed session id; Claude Code: the session the round named) with a short continuation prompt.
   Only when no session exists and the worktree is unchanged since the snapshot does it relaunch
   with the brief. The audit stays exact because it always compares against the run's single
   snapshot; a round whose audit found a violation, or whose worker returned a valid result, is
   never retried.
2. **Transient = the agent program reported a model-service error matching a fixed classifier**:
   concurrency/rate limit, too many requests, 429, overload/high demand, 5xx and service
   unavailable, an explicit retry-later/try-again, and transport drops of the model call (upstream
   or stream failure, connection reset/refused, timed out). Quota, billing and usage-limit errors
   are excluded. I included transport drops and timeouts because they are transient failures of
   reaching the model service and were 6 of the 57 failures; Workers' own round timeout
   (`worker_timeout`) is never retried.
3. **Budget**: `limits.retries` (default 5) retry rounds per run, separate from the resume
   `rounds`; delay before the k-th retry is `limits.retry_delay_seconds` (default 15) × 2^(k−1),
   jittered uniformly to between half and all of it (worst-case wait ≈ 7.75 min, enough for
   concurrency slots of minute-long review workers to free). When the retries are used up the run
   fails with the backend's failure code and reason `exhausted`.
4. Round trace contract → version 5 (prompt `retry`, new `transient` field); returned run record →
   version 4; progress file gains phase `waiting`.
5. project_review default `--parallel` 4 → 2: each Module review runs about four workers at once,
   so 2 halves the ~16 concurrent workers that overran the gateway, and Workers' retry absorbs
   what remains.

## Escalated to the main agent, 2026-10-08T05:35:52Z

- **task-session** task session (task worker-transient-retry): `limits_passthrough_outside_modules`
  Workers now retries rounds that transient model-service errors ended (WorkerRequest.retries, default 5; WorkerRequest.retry_delay, default 15 s). The worker configuration reader (module.workers) accepts and defaults limits.retries and limits.retry_delay_seconds, and Workers' Specs document them. But the only caller that turns the configuration's limits into a WorkerRequest is Method's standard worker sequence, src/concorde/method/workers.py lines 657-660 (rounds/timeout/max_turns/max_budget_usd are passed one by one), and its Spec specs/concorde/method/workers.md#worker-limits lists the limits. Both belong to module.method, outside this task's Modules (module.workers, module.project-review). Without that pass-through, retries work with the defaults but a project cannot change them in .concorde/workers.json. The change is two keyword arguments (retries=bounds['retries'], retry_delay=float(bounds['retry_delay_seconds'])) and two list items in method/workers.md.
  Not handled here (decision): the brief asks for configurability in limits 'if that fits', but completing it changes module.method's code and Spec, which lies outside the task's Modules
  Options: allow this task to make the two-line pass-through in src/concorde/method/workers.py and the two list items in specs/concorde/method/workers.md (add module.method to the task or accept the out-of-Module change); deliver without it: Workers retries with fixed defaults (5 retries, 15 s base), and the pass-through becomes a later task for module.method
  Recommendation: allow the pass-through in this task: it is mechanical, keeps the configuration contract honest (the reader accepts limits.retries, so it should take effect), and avoids a follow-up task

```json
{
  "level": "task-session",
  "actor": "task session (task worker-transient-retry)",
  "code": "limits_passthrough_outside_modules",
  "detail": "Workers now retries rounds that transient model-service errors ended (WorkerRequest.retries, default 5; WorkerRequest.retry_delay, default 15 s). The worker configuration reader (module.workers) accepts and defaults limits.retries and limits.retry_delay_seconds, and Workers' Specs document them. But the only caller that turns the configuration's limits into a WorkerRequest is Method's standard worker sequence, src/concorde/method/workers.py lines 657-660 (rounds/timeout/max_turns/max_budget_usd are passed one by one), and its Spec specs/concorde/method/workers.md#worker-limits lists the limits. Both belong to module.method, outside this task's Modules (module.workers, module.project-review). Without that pass-through, retries work with the defaults but a project cannot change them in .concorde/workers.json. The change is two keyword arguments (retries=bounds['retries'], retry_delay=float(bounds['retry_delay_seconds'])) and two list items in method/workers.md.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the brief asks for configurability in limits 'if that fits', but completing it changes module.method's code and Spec, which lies outside the task's Modules"
  },
  "options": [
    "allow this task to make the two-line pass-through in src/concorde/method/workers.py and the two list items in specs/concorde/method/workers.md (add module.method to the task or accept the out-of-Module change)",
    "deliver without it: Workers retries with fixed defaults (5 retries, 15 s base), and the pass-through becomes a later task for module.method"
  ],
  "recommendation": "allow the pass-through in this task: it is mechanical, keeps the configuration contract honest (the reader accepts limits.retries, so it should take effect), and avoids a follow-up task",
  "causes": []
}
```

## Report 1 to the main agent (concorde-d4), 2026-10-08T05:36:36Z

worker-transient-retry: implementation done and committed (8b877953, not yet delivered); one decision needed before delivery.

Done (module.workers, module.project-review), worker and project_review tests 153 passed, spec-validation success, build --check clean:
- Workers retries a round that the agent program ended with a transient model-service error, as a retry round of its own (prompt kind `retry`) that continues the same session (pi: the run's fixed session id; Claude Code: --resume). Delay before the k-th retry: retry_delay_seconds x 2^(k-1), jittered to 50-100% (defaults: 5 retries, 15 s, so at most 15/30/60/120/240 s). Never retried: a round with an audit violation, a round with a valid worker result, Workers' own round timeout, limits, and any non-transient error (fails at once, reason environment). Retries used up: the backend's failure code with reason exhausted. Every attempt is recorded: each round node has `transient` {error, retried, delay_seconds} (round trace contract v5, returned run record v4) and the run's error lists each retry in attempts; progress phase `waiting` during the delay.
- Transient = concurrency/rate limit, too many requests, 429, overload/high demand, 5xx/service unavailable, explicit retry-later/try-again, and lost calls (upstream/stream failure, connection reset/refused, timed out); quota/billing/usage-limit errors excluded. pi's own built-in retry did not fire in the failed run because its classifier matches neither "Concurrency limit" nor "please retry later".
- project_review default --parallel 4 -> 2 (each Module review runs about four workers at once, so 2 halves the ~16 concurrent workers that overran the gateway; Workers' retry absorbs the rest).

Decisions I took (in the decision log): retry as its own round continuing the session (24 of the 57 failed runs had failed mid-session after up to 45 tool results, so replaying the brief was not an option); counting transport drops and timeouts as transient (6 of the 57 failures); the defaults above.

Escalation 1 (decision): making the new limits configurable needs a two-line pass-through in src/concorde/method/workers.py and two list items in specs/concorde/method/workers.md, both module.method's, outside this task's Modules. The configuration reader already accepts limits.retries and limits.retry_delay_seconds; without the pass-through the defaults apply. Options: (a) allow the pass-through in this task; (b) deliver without it and leave it to a later module.method task. Recommendation: (a).

- **task-session** task session (task worker-transient-retry): `limits_passthrough_outside_modules`
  Workers now retries rounds that transient model-service errors ended (WorkerRequest.retries, default 5; WorkerRequest.retry_delay, default 15 s). The worker configuration reader (module.workers) accepts and defaults limits.retries and limits.retry_delay_seconds, and Workers' Specs document them. But the only caller that turns the configuration's limits into a WorkerRequest is Method's standard worker sequence, src/concorde/method/workers.py lines 657-660, and its Spec specs/concorde/method/workers.md#worker-limits lists the limits. Both belong to module.method, outside this task's Modules. Without that pass-through, retries work with the defaults but a project cannot change them in .concorde/workers.json.
  Not handled here (decision): the brief asks for configurability in limits 'if that fits', but completing it changes module.method's code and Spec, which lies outside the task's Modules
  Recommendation: allow the pass-through in this task

After your answer I finish, run the full suite once, then task-validation and delivery.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-08T06:13:53Z

Escalation 1 (limits_passthrough_outside_modules), decided by the main agent: option (a). Add the two-line pass-through in src/concorde/method/workers.py and the two list items in specs/concorde/method/workers.md#worker-limits in this task; it completes the configurability the brief asked for and changes nothing else Method promises. Then run the full suite, task-validation and delivery. (The main session was restarted and is now named 'Review流程'; the task is rebound to it.)

Main agent's answer to report 1 (received 2026-10-08 from Review流程): escalation 1, option (a) —
add the limits pass-through in src/concorde/method/workers.py and the two items in
specs/concorde/method/workers.md#worker-limits in this task.

Task session: added `retries=bounds["retries"]` and `retry_delay=float(bounds["retry_delay_seconds"])`
to Method's WorkerRequest and the two limits to method/workers.md#worker-limits. No dedicated test
for the two keyword arguments: Method's step needs a full run context to reach them, and the reader's
limits (test_models) and Workers' use of them (test_pi, test_workers) are tested; the full suite
covers the step itself.

Full suite on the final input (task session): 1317 passed, 5 skipped, 1 failed:
tests/concorde/tasks/test_store.py::TaskStoreTests::test_a_run_waiting_for_a_closing_tasks_workspace_is_refused_outside_it
(OSError: [Errno 39] Directory not empty: '.concorde' in teardown). Unrelated to this task (module.tasks);
alone it failed 1 of 3 runs and passed 2. Recorded as Issue I-067df4e54ace576184a5f534e1d3d7f7
(obvious-fix, low): the test waits only for the detached runner's run lock, not for the process.

## Report 2 to the main agent (Review流程), 2026-10-08T06:37:28Z

worker-transient-retry delivered: delivery commit 9c056df7 (concorde: deliver worker-transient-retry), on top of 8b877953 (Workers retry + project_review --parallel 2) and 29190cc5 (Method pass-through, per your answer to report 1, option a).

- Workers retries a round that a transient model-service error ended (concurrency/rate limit, 429, overload, 5xx, retry-later, lost calls; quota/billing excluded) as a retry round continuing the same session, at most limits.retries (default 5) times per run, waiting limits.retry_delay_seconds (default 15) x 2^(k-1) jittered to 50-100%. Never retried: audit violations, rounds with a valid result, Workers' own timeout, limits, other errors. Each round node records {error, retried, delay_seconds}; failed runs list every retry in attempts.
- Method now passes limits.retries and limits.retry_delay_seconds to Workers; specs/concorde/method/workers.md lists them.
- project_review default --parallel 2.
- Resolves I-558971fc (already on the task).

Checks: task-validation ready; delivery ok. Full suite on the final input: 1317 passed, 5 skipped, 1 failed — tests/concorde/tasks/test_store.py::TaskStoreTests::test_a_run_waiting_for_a_closing_tasks_workspace_is_refused_outside_it (OSError Directory not empty: '.concorde' in teardown). Unrelated (module.tasks), intermittent: alone it failed 1 of 3 and passed 2. Recorded as Issue I-067df4e54ace576184a5f534e1d3d7f7 (obvious-fix, low): the test waits only for the detached runner's run lock, not for its process.

Decisions taken without the developer are in the decision log: retry as its own round continuing the session; transport drops and timeouts count as transient; defaults 5 retries / 15 s; --parallel 2; no dedicated test for Method's two-argument pass-through. Nothing open for the developer.

## Closed: merged, 2026-10-08T06:37:42Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 9c056df7e8989b65979fd0f948822b880273f680 into main and closed it as merged. Nobody answers a report after that.
