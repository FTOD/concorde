# Decision log: fix-e2e

Goal: Resolve the open Issues of module.e2e, carrying out the main agent's decision

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-e02daa2a3ee55b1d94e6b3cdea886916 (module.e2e, medium, decision-needed): A fresh workflow report does not establish invocation ownership
- I-d838bcb654245eb1ad36a501fdc8afbc (module.e2e, medium, preferred-fix): Select the providers for preparation's complete model validation
- I-cfd70194b5a15a18b75f9f3ef5bd3a3e (module.e2e, medium, preferred-fix): Complete the owners case's lock and queued-run timeout contract
- I-2c87aa59f17251a397956285c2fafb92 (module.e2e, medium, preferred-fix): Reconcile the setup restriction with repository preparation
- I-7feb14d947cd5c91b98f7f17e6e4dd8b (module.e2e, medium, obvious-fix): Declare preparation's dependency on Spec core initialization
- I-f9ff7a740a9e511a8ca350d7f442204a (module.e2e, medium, obvious-fix): Limit retry reuse to steps before the retried step
- I-418f27c901d65f488b2e99138d28db37 (module.e2e, medium, obvious-fix): Align the owners requirement with its defined observation interval
- I-300a5eb3b2e850209ab7dd89ed5c878f (module.e2e, low, obvious-fix): Separate tool authorization from MCP server provisioning
- I-986a03d86c675d94bd576315df2cc6c0 (module.e2e, low, suggestion): Show Tasks' role in the normal prepare and run path
- I-b6d5e9684a465333923471e760a791bf (module.e2e, low, suggestion): Connect owners to a prepared task in a worked example
- I-06571d66defd5a2cb7d66930f5386e19 (module.e2e, low, suggestion): Explain owners' model option and default
- I-bc1abc67bd405c88b126552edb8667f7 (module.e2e, low, suggestion): Make preparation refusals easier to identify
- I-2ce9be681beb53d491b663a019d60a8b (module.e2e, low, suggestion): Include Main session and Tasks in the provider overview
- I-a71a3629c5cb546c866283af8d8aeb53 (module.e2e, low, suggestion): Explain when to use trust and how to read its result
- I-6bd8a9b7a51d51d0a1db6934b6ecf3ef (module.e2e, low, suggestion): Link session statuses and prompt parts to their explanations
- I-0698d3d094a35238ba573d954ebd710e (module.e2e, low, suggestion): Keep verification declarations out of the entry
- I-158de9697304561c8bc9f053e22d6f9c (module.e2e, low, suggestion): Document CLI exit statuses alongside JSON outcomes
- I-20c4191e65db552a8279626dbcabf545 (module.e2e, low, suggestion): State the default workflow execution mode

Decisions (main agent, ordinary scope):
- I-e02daa2a3ee55b1d94e6b3cdea886916: state an exclusive-use prerequisite: a test project is
  driven by one `e2e run` at a time and nobody else reports a workflow there; align the entry, the
  requirement and the scenarios. No correlation id.

The developer asked the main agent (2026-10-02) to resolve every Issue that does not need the
developer. This task takes the open Issues listed above. The decision-needed ones among them are
already decided: their decisions are under "Decisions" below, and you carry them out as given.

Start with the full suite on your fresh worktree as a baseline: six tasks merged into main just
before this task opened, and only build and spec-validation ran on the merged result. Record any
failure in the decision log; fix it here when it lies in your Modules, otherwise record it as an
Issue of its Module.

For each Issue:
1. Read it with `python3 scripts/concorde.py issues show <id>` and check that it still stands at
   your HEAD. One already fixed is closed with `concorde issues close <id> --reason resolved
   --note … --evidence <commit>`; a duplicate with `--reason duplicate --duplicate-of <id>`.
2. Fix it by its tier: `obvious-fix` alone; `preferred-fix` with the fix you judge best, which you
   report; `suggestion` only when it clearly improves the Specs or code at small cost, otherwise
   leave it open and say why; `decision-needed` as decided below.
3. Add every Issue you fixed with `python3 scripts/concorde.py task resolve <task> <id>…`, so the
   merge closes it. Never add one you did not fix.

Rules: change only the Modules this task binds. A fix another Module needs, or a fix that turns
out to need a further decision (it would change what a Module promises its users beyond the
decisions below, contradict an earlier decision of the developer, discard work, or loosen a
boundary), is escalated, all together at the end, after everything else is done; a problem you
find in another Module is recorded as an Issue of that Module. Four other tasks run in parallel,
each on its own Modules: fix-execution-root (execution, concorde), fix-workers (workers), fix-e2e
(e2e), merge-update-followups (main-session, tasks, tracing, distribution, task-session,
coordination), fix-delivery-and-small (delivery, adoption, spec-mcp, code-review, spec-review,
operations). module.harness is bound by none: record Harness changes as Issues. Verify with build
--check, spec-validation and the full suite, then task-validation and delivery, and report: what
you fixed (with the fix chosen for each preferred-fix), what you closed as already resolved or
duplicate, the suggestions you left open and why, the baseline result and the escalations.

## Task session (2026-10-02)

- Baseline at 84994940 after preparing the worktree: build ok, full suite `922 passed, 5 skipped,
  453 subtests passed`; no failure to record.
- Found while reading for I-cfd70194b5a15a18b75f9f3ef5bd3a3e: `scripts/e2e/owners.py` looks for the
  queued run only in the workspace folder and unbound runs, never in the lobby
  (`.concorde/lobby/<run-id>/`) where Execution keeps a bound run that waits with `--wait` for the
  workspace lock the case holds; with the real runner every phase would end in `live_timeout`.
  The owners stand-in wrote straight into the workspace folder, hiding it. Fixing it here (my
  Module); `scripts/e2e/sessions.py`'s `run_folders` (module.headless-sessions) misses the lobby
  too, which `watch` and a headless session's wakes use: recorded as an Issue of that Module, and
  `watch` adds the lobby itself.
- All 18 Issues still stood at 84994940; none was already resolved or a duplicate. Fixed all 18,
  the suggestions included, since each was a small, clear improvement of the entry
  (commits ed5d8266, 7bb37dfc); added them with `task resolve`.
- I-e02daa2a (decision-needed, as decided): stated the exclusive-use prerequisite (one `run` at a
  time, nobody else reports a workflow meanwhile, no correlation id) in the entry's "Running a
  workflow", in req.e2e.own-result's explanation, and in the GIVEN of scenario.e2e.stale-result and
  scenario.e2e.newest-result; the entry says a breach is not detected.
- I-d838bcb6 (preferred-fix), fix chosen: declare `uses module.workers` relying on the worker
  configuration, the model map, their two contracts and scenario.workers.model-map-checked, and
  `uses module.operations` relying on the Operation catalog; E2E enumerates no worker itself but
  hands its configuration to Workers' whole-configuration check and passes its refusal on. Better
  than restating Workers' rules in E2E. Workers' check has no invocation policy of its own
  (I-88e8ba4c, decision-needed, Workers): appended a report there naming E2E as its caller.
- I-cfd70194 (preferred-fix), fix chosen: the case takes the workspace lock as Execution's runs do
  and holds it at most its limit (600 s) after the launch, the launching turn and the run's arrival
  sharing that one deadline; the run is queued with `--wait` of twice the limit (1200 s), so its
  wait never expires while the case holds the lock; a run refused with `workspace_busy` anyway stops
  the case with `workspace_busy` naming its result. New req.e2e.owners-queue and
  scenario.e2e.owners-run-refused. Chosen over a single shared 600 s budget because the run's wait
  must outlast the hold with margin, and over judging a refused run because it did no work.
- I-2c87aa59 (preferred-fix), fix chosen: req.e2e.user-setup names Git (fetch, branch, commit)
  beside the installer and `concorde` command and restricts direct writes to the project's Concorde
  Specs and configuration; the interpreter reaches the configuration only as `concorde init
  --propose --python`, explained in the entry.
- I-7feb14d9: `uses module.spec` relying on req.spec.init-explicit-envelope plus `includes`
  document.spec.contracts for the Initialization section (it defines no node to rely on), as
  Distribution and Issues do.
- I-300a5eb3: split into req.e2e.headless-granted and new req.e2e.headless-mcp; scenario.e2e.headless
  gains the MCP line its test already asserts.
- Recorded I-44783e3c (module.headless-sessions, obvious-fix, medium): sessions.py `run_folders`
  misses the lobby.
- spec-validation keeps one finding that predates this task and lies outside module.e2e:
  concept.task-brief is used by no Module other than module.main-session.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T02:32:24Z

fix-e2e delivered: 269cf89e on concorde/fix-e2e (steps ed5d8266, 7bb37dfc). No escalations.

Baseline at 84994940: build ok, full suite 922 passed / 5 skipped, no failure. Final: build --check ok, spec-validation success (one warning outside module.e2e that this task did not touch: concept.task-brief is used only by module.main-session), full suite 924 passed / 5 skipped, task-validation ready.

Fixed and added with task resolve: all 18 Issues. None was already resolved or a duplicate, and none was left open. Every suggestion was small and clearly improved the entry, so I took all of them.
- I-e02daa2a (decision-needed, carried out as decided): a test project is driven by one `e2e run` at a time and nobody else reports a workflow there. This is stated in the entry, in req.e2e.own-result and in the GIVEN of the stale-result and newest-result scenarios. No correlation id; the entry says a breach is not detected.
- I-d838bcb6 (preferred-fix). Fix chosen: declare `uses module.workers`, relying on the worker configuration, the model map, their contracts and scenario.workers.model-map-checked, and `uses module.operations`, relying on the Operation catalog. E2E enumerates no worker itself: it hands its configuration to Workers' whole-configuration check and passes the refusal on. This avoids restating Workers' rules in E2E.
- I-cfd70194 (preferred-fix). Fix chosen: the case takes the workspace lock as Execution's runs do. It holds the lock at most its 600 s limit after the launch, with one deadline shared by the launching turn and the run's arrival. The run is queued with `--wait` 1200 s (twice the limit), so its wait never expires while the case holds the lock. A run refused with workspace_busy anyway stops the case with workspace_busy. New req.e2e.owners-queue and scenario.e2e.owners-run-refused, with tests.
- I-2c87aa59 (preferred-fix). Fix chosen: req.e2e.user-setup names Git (fetch, branch, commit) beside the installer and the `concorde` command, and forbids only direct writes of the project's Concorde Specs and configuration. --python reaches the configuration only through `concorde init --propose --python`.
- Obvious fixes: I-7feb14d9 (uses module.spec plus includes document.spec.contracts for its Initialization section), I-f9ff7a74 (a retry reruns the retried step and every later step), I-418f27c9 (the owners requirement uses the judged interval and has a new title), I-300a5eb3 (split into req.e2e.headless-granted and req.e2e.headless-mcp).
- Suggestions: I-986a03d8, I-b6d5e968, I-06571d66, I-bc1abc67, I-2ce9be68, I-a71a3629, I-6bd8a9b7, I-0698d3d0, I-158de969, I-20c4191e. These add Tasks' setup role, an owners worked example, --claude-model, a list of refusals with their codes, the providers in the overview diagram, when to use trust and how to read its result, links to the session statuses, no verification claims in Files, exit statuses 0/1/2, and the --via claude default.

Defect found and fixed beyond the Issues: the owners case never looked in the run store's lobby, where Execution keeps a run waiting with --wait for the lock the case holds. With the real runner, every phase would have ended in live_timeout. The owners stand-in now waits in the lobby the way Execution's runs do, and `watch` lists runs waiting in the lobby.

Issues recorded for other Modules: I-44783e3c (module.headless-sessions, obvious-fix, medium): sessions.py run_folders also misses the lobby, so a headless session is not woken for a run it left queued. I also appended a report to I-88e8ba4c (module.workers, decision-needed) naming E2E's prepare as a caller of the whole-configuration check that this Issue may remove.

## Closed: merged, 2026-10-02T02:32:57Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 269cf89e9c33fa3f13a003c0ab2a5d274705f7ae into main and closed it as merged. Nobody answers a report after that.
