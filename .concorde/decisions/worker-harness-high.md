# Decision log: worker-harness-high

Goal: Fix the high Issues of Harness and Workers (stop surviving command descendants before removing their registration; give the Harness library a documented calling contract; WorkerRequest defaults to Claude Code instead of pi) and their other obvious-fix Issues

## Task brief (main agent, 2026-10-29)

**Origin.** Project review r-20261029T060905-project_review-fa4731e2 (unbound, commit 8a5ed4245, verdict changes_required) left 2 critical and 10 high Issues open. The developer chose to fix every critical and high Issue first, in five parallel tasks split by Module, each also fixing the obvious-fix Issues of its own Modules. Read the review's findings for your Modules in `.concorde/unbound/r-20261029T060905-project_review-fa4731e2/result.json` (`output.modules[]`, the panel and code_review reviews) when an Issue's text is not enough.

**Issues this task resolves (17, all in the task's resolves):**

- I-3010f3e4783d5dc1bb6324c6bfd3fe5b (module.harness, high, preferred-fix): The Harness library has no documented calling contract
- I-e39d17a05e0d52509e0b371c86abac88 (module.harness, high, preferred-fix): Stop surviving command descendants before removing their registration
- I-1ebbd1dcbacf5cfe8a8dc4502ed06770 (module.workers, high, obvious-fix): WorkerRequest defaults to Claude Code instead of pi
- I-6a09876757eb57ffafb38b3fd244b1f8 (module.harness, medium, obvious-fix): The home-directory deny rule omits the run's tmp exception
- I-8dbee097fd6556b7ae01db4734d614d3 (module.harness, medium, obvious-fix): Missing entries has two incompatible refusal codes
- I-bfbf64d198f45badadbfd5f1205ce752 (module.harness, medium, obvious-fix): The canonical write-hook output omits the promised denial prefix
- I-f39183ac312556c3a72c87a9984a69ac (module.harness, medium, obvious-fix): Stop ripgrep when the requested match count is reached
- I-14afc69e0e045b158e1bde17a5aae5fe (module.workers, medium, obvious-fix): The resumed-cost requirement drops the decreasing-total exception
- I-2b7b1db2a0465eb5903316c2fa6f3885 (module.workers, medium, obvious-fix): The overlap requirement omits equality and resolved-path checks
- I-378f6481cf0a5fcfb9d9fa4320036475 (module.workers, medium, obvious-fix): An unavailable audit produces a returned record that breaks its schema
- I-6bec26f9817c51069b63bd95e3c56899 (module.workers, medium, obvious-fix): Partial pi usage fabricates zero values for unreported metrics
- I-6f47f94d60c555579395c74a6df4fe31 (module.workers, medium, obvious-fix): The unmapped-model sentence does not state a coherent outcome
- I-767e2b706457500d8fc7a7458879b602 (module.workers, medium, obvious-fix): The runtime-directory definition omits its documented fallback
- I-d2b9a0c474975a7ba9870f3e3d3d7af4 (module.workers, medium, obvious-fix): Model preflight incorrectly treats general as having no workers
- I-f8780fd1bc5351c5bd34bf04973e97ac (module.workers, medium, obvious-fix): Missing-backend refusals omit the attempted command and concrete fallback configuration
- I-f8cf229a3ed2546ba676c28124ff1697 (module.workers, medium, obvious-fix): Runtime-path contract disagrees with the tool allowance and path base
- I-38c9aab90ee65dd0bedcb7cd97802955 (module.workers, low, obvious-fix): Retry recording combines two independent obligations

**How to handle them (the main agent's decisions).**
- Critical and high first. Show each with a test that fails on the old code.
- Fix obvious-fix Issues directly. For a preferred-fix Issue, take the clearly better fix and report it. None of these Issues is decision-needed. If one turns out to need a decision beyond your Modules or beyond the Issue's evident intent, escalate it rather than guess.
- An Issue that turns out to be already fixed, not a real problem, or a duplicate of another open Issue: say so with your evidence in your report. Do not close it yourself. The main agent closes it, or the merge closes it as resolved.
- Leave the other open Issues of your Modules (preferred-fix and decision-needed medium or low) alone, unless a fix here resolves one as a side effect: then name it in your report.
- Add or change Specs first where a fix changes a promise. Keep within your Modules. Escalate a change any other Module would have to make.

**Parallel tasks.** Four other tasks run at the same time. Do not touch their Modules:
- swe-cases-critical: module.swe-bench-cases
- coordination-high: module.tasks, module.task-session
- checks-execution-high: module.checks, module.execution
- specmcp-workflows-high: module.spec-mcp, module.workflows

**Specific to this task.** For I-1ebbd1dc, pi is the default worker backend, as the glossary's 'Worker backend' says. Make the default pi without changing what an explicit worker configuration chooses.

**Verification.** Run Concorde's full suite, `build --check` and `spec-validation`. Then run `task-validation` and `delivery` from the task worktree, and report.

**Environment notes.**
- uv, node/npm (Node 24, npm 11), pi, rg, fd and d2 are under `/home/scratch.zbai_gpu/opt`.
- The system bubblewrap is 0.4.0 and works.
- Every worker runs on pi: claude-opus-5-5 and gpt-6.1-sol.
- Keep large files off `$HOME` (5 GB quota).

**Left to the session.** The mechanisms, internal structure, test design and Spec wording.

## Task session decisions (2026-10-29)

- **I-e39d17a0 (preferred-fix), fix chosen.** Of the two repairs the Issue offers, the extension now kills what is left of a command's process group in its `close` handler and removes the registration only then; a group it cannot kill (any error but `ESRCH`) keeps its registration for the host's round-end kill. Reason: it stops the background process at once rather than at round end, and it keeps the host's kill as the fallback. Spec: Harness `pi.md#sandbox` and Workers `pi.md` say so; new `req.workers.pi-command-group-stopped` and `scenario.workers.pi-command-group-stopped`, verified by a bash probe of the generated extension (fails on the old extension: the `sleep` survived). Commit 7f… (see branch log).
- **I-1ebbd1dc.** `WorkerRequest.backend` defaults to `pi`; the Claude Code test fixture names `backend: claude` explicitly. New `scenario.workers.request-backend-default`, whose test fails on the old default.
- **I-3010f3e4 (preferred-fix), fix chosen.** A new Harness implementation document `harness/library.md` states the exact calling contract (entry points, inputs, return values, effects, failures, repeat behaviour, and the pi policy fields Workers embeds); the entry gains "Calling the Harness" with the entry-point table and the worked example's call followed to its returned settings. Reason: the Protocol puts actual public entry points in module reading and exact APIs in implementation reading. Workers now includes `document.harness.library`. Repeat behaviour is stated as it is: equal inputs over an unchanged file tree give equal values; the deny rules follow the file tree at the moment of the call. A test checks that generation writes nothing, repeats, and follows a later directory.
- **Internal structure.** pi's tool set table moved from `pi_backend.py` into the Harness's `settings.py` as `PI_TOOL_SETS` (`pi_backend.TOOL_SETS` stays an alias), so the Harness chooses every tool set as its Spec says.
- **I-8dbee097.** `grant_view` now raises `grant_unavailable` for a grant that is no object or has no `entries`, matching the grant input contract; `grant_malformed` stays for malformed entries. The entry separates the two codes. Workers already checked these before calling the Harness, so no run's outcome changes.
- **I-bfbf64d1, I-6a098767, I-f39183ac.** Write hook denials specified with exact texts and one exact output example (a test matches it); the deny table's home/primary row exempts `tmp/`; pi's grep stops at the limit-th match plus that match's own context lines (as pi's own grep stops at that match), with a probe test that fails on the old reader.
- Correction to the entry above: the I-e39d17a0 fix is commit d939ee84b; the others are c7cd2fead (I-1ebbd1dc), c210c7098 (I-3010f3e4, I-8dbee097) and f567efedb (I-bfbf64d1, I-6a098767, I-f39183ac).
- **Workers batch, commit 3f1b58d0a.** The ten Workers obvious-fix Issues fixed as their suggested repairs say. Decisions taken: (1) `contract.workers.worker-configuration` goes from version 10 to 11, as I-f8cf229a asks; no code is tied to that version. (2) `contract.workers.worker-round-trace` stays at version 7 although its semantics now state the decreasing-total exception (I-14afc69e): the code always applied it, so no stored record changes shape or meaning, and a bump would force a new typed-value registration of every stored round trace. (3) For I-6bec26f9 a new `req.workers.pi-usage-as-reported` and `scenario.workers.pi-partial-usage` make the existing module promise ("records only what the agent program reported") decidable; the pi agent info's `cost` is null too when pi reported none. (4) For I-d2b9a0c4 only Workers' copy is fixed; End-to-end testing's identical sentence belongs to module.e2e, outside this task, so I recorded it as I-1a30c7315759552fa86ec50cfdd6f8ff (obvious-fix, medium) rather than editing it. (5) For I-f8780fd1 the refusal names the command it looked for (the override's value, or the name on PATH with the variable unset) and the exact `operations.<op>.workers.<worker>.backend` entry for the other backend, with a reminder that its model needs a map id there.
- **Full suite, first run: 1 failed.** `tests/concorde/execution/test_runner.py::RunnerTests::test_a_worker_whose_backend_or_model_cannot_be_settled_fails_before_launch` (module.execution, which the parallel task checks-execution-high owns) asserted the old `backend_missing` phrase `edit its backend in .concorde/workers.json`. Decision: rather than edit another Module's test, the refusal keeps that phrase and adds the exact entry after it (commit a417f888b). Rerun on the final input: spec-validation success, build --check no differences, full suite 1666 passed, 6 skipped.

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T09:24:11Z

worker-harness-high delivered: delivery commit f8919a11e on concorde/worker-harness-high (delivery run r-20261029T091447-delivery-b2fec70a). task-validation r-20261029T090455-task_validation-fd8c8ce4: ready, no blocking findings, 28/28 configured checks passed. Also on the final input: spec-validation success (only the 5 old sentence-length warnings in spec-tooling/spec/scenarios.md), build --check no differences, full suite 1666 passed, 6 skipped.

All 17 Issues in the task's resolves are fixed (the merge closes them):
- High: I-e39d17a0 (d939ee84b) The pi extension's close handler now kills what is left of a command's process group before it removes the registration. A group it cannot kill keeps its registration for the host's round-end kill. Preferred fix chosen: kill-then-unregister, because the background process stops at once and the host's kill stays the fallback. New req.workers.pi-command-group-stopped plus scenario; the bash-probe test fails on the old extension.
- High: I-3010f3e4 (c210c7098) New Harness implementation document harness/library.md with the exact calling contract (entry points, inputs, returns, effects, failures, repeat behaviour, and the pi policy Workers embeds). The entry gains "Calling the Harness" with the entry-point table and the worked example's call followed to its returned settings. Preferred fix chosen: entry points in module reading and exact API in implementation reading, as the Protocol divides them. Workers now includes document.harness.library. pi's tool set table moved into the Harness (settings.PI_TOOL_SETS; pi_backend.TOOL_SETS stays an alias).
- High: I-1ebbd1dc (c7cd2fead) WorkerRequest.backend defaults to pi; an explicit backend is unchanged. Claude fixtures now name claude; new scenario.workers.request-backend-default, whose test fails on the old default.
- Harness obvious-fix: I-8dbee097 (grant_view raises grant_unavailable for a grant without entries; grant_malformed only for malformed entries), I-bfbf64d1 (exact write-hook denial texts plus one exact output example, matched by a test), I-6a098767 (the deny table exempts tmp/), I-f39183ac (grep stops at the limit-th match plus that match's own context lines, as pi's grep does; the test fails on the old reader).
- Workers obvious-fix (3f1b58d0a, a417f888b): I-14afc69e, I-2b7b1db2, I-378f6481, I-6bec26f9, I-6f47f94d, I-767e2b70 (glossary definition of Runtime directory updated), I-d2b9a0c4, I-f8780fd1, I-f8cf229a, I-38c9aab9 (new req.workers.retry-attempts). New req.workers.pi-usage-as-reported and scenario.workers.pi-partial-usage.

Decisions taken without the developer (all in the decision log):
1. contract.workers.worker-configuration goes from v10 to v11, as I-f8cf229a asks.
2. contract.workers.worker-round-trace stays at v7, although its semantics now state the decreasing-total exception. The code always applied it, and a bump would re-register the stored round-trace type.
3. The backend_missing refusal keeps the phrase "edit its backend in .concorde/workers.json" and adds the exact operations.<op>.workers.<worker>.backend entry after it. The reason: tests/concorde/execution/test_runner.py (module.execution, task checks-execution-high) pins that phrase, and I did not edit another Module's test.
4. For I-d2b9a0c4 I fixed only Workers' copy.

Still open, for you: End-to-end testing (module.e2e) repeats the same obsolete "general declares no worker ids" sentence in Preparing a test project. It is outside this task's Modules, so I recorded it as the new Issue I-1a30c7315759552fa86ec50cfdd6f8ff (module.e2e, obvious-fix, medium) for a later e2e task. Nothing else is open and no escalation is pending.

## Closed: merged, 2026-10-29T09:24:36Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit f8919a11e4fadd0f21fd31f22bc01536d5f8eba9 into main and closed it as merged. Nobody answers a report after that.
