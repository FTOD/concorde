# Decision log: review-root

Goal: Fix the spec review findings of the root Module (and Execution's lifecycle wording)

## Brief (main agent, 2026-09-30)

The developer asked for a spec review after `project-model-names` merged and said: fix the small
problems yourselves, and ask the developer only at the end about what needs their decision.

The unbound `spec_review` run `r-20260929T203136-spec_review-a3b63738` examined main at 14e573aa
and ended `changes_required`. Its result, with every finding's evidence and suggestion, is
`/home/zhenyu/concorde/.concorde/unbound/r-20260929T203136-spec_review-a3b63738/result.json`
(read-only for you); this task covers the findings of module.concorde, module.execution.

### What to do

- Fix every finding of these Modules, blocking and advisory, except those named below as the
  developer's. Typical fixes: split a requirement that holds several obligations into atomic
  requirements, one SHALL each; split a scenario that mixes situations into scenarios of one
  situation each; correct examples, diagrams and wording that contradict the provider's Spec or the
  code. When a scenario identity changes, update the tests whose verification declarations name it.
  Keep what the Modules promise unchanged unless the finding shows the promise is wrong; when the
  code and the Spec disagree, decide which is right from the other Specs and the developer's earlier
  decisions, and record the decision here.
- Findings that say a provider's contracts were not supplied: check whether the Module's
  declarations omit that contract and add it if so; otherwise report it as a possible spec_review
  defect with evidence. Do not change module.spec-review.
- A finding you judge wrong: do not change the Spec; record why here and in your report.
- Anything else you find that needs the developer (it changes a promise's meaning, the design, or an
  earlier developer decision): leave it unchanged and report it with options and a recommendation.
  Do not escalate and stop: deliver the rest and put every such question in your final report.

### Specific to this task

f.2: the developer already decided that the main agent delegates every task to a task session and never works in a task worktree; remove the remaining text that says otherwise. f.3: make the rationale claim only what the design does. f.8 (in specs/concorde/execution/module.md): align the lifecycle explanation with the lock explanation.

### Process

Create what Git ignores (`uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`). Format,
`build --check`, `spec-validation`, `registry --write` if a module block changes, the relevant tests
and once the full pytest suite on the final input. Then run `python3 scripts/concorde.py run
spec_review` once in the task worktree (bound; it reviews this task's Modules and updates their
review memory) and handle its findings the same way, without looping further. Then `task-validation`
and `delivery`, and report to the main agent with SendMessage: what you fixed, the findings you
judged wrong, and the open questions for the developer with options and recommendations.

## Task session (2026-09-30)

Fixes of the findings of `r-20260929T203136-spec_review-a3b63738` for module.concorde and module.execution, commit d6418a2d:

- **f.1** `req.concorde.agent-runtimes` now holds only the main-agent obligation and is renamed `req.concorde.main-agent-program` (no reference named the old id); worker program selection stays only in `req.concorde.worker-program`.
- **f.2** Root entry: "Agents at both ends" says the main agent hands every task to a task session, never works inside a task worktree and makes only an approved small change in the primary worktree; the Coordination child description no longer lets the main agent play the task level; the seam diagram's main-agent edge now shows unbound runs in the primary worktree. The root scenarios `adopt-brownfield`, `task-to-merge`, `parallel-tasks` and `error-chain-to-developer` name the task session as the actor of the task's runs. The root's own `README.md` and `docs/README.md` (root realizations) said the main agent may work inside a single task's worktree; corrected likewise, and `docs/README.md`'s nonexistent `validate` command is now `task-validation`.
- **f.3** The rationale now claims only that a worker's answer never reaches the task level unchecked; it states that the two Coordination agents exchange judgments directly, recorded in the decision log, and that what a task session changes is checked by `delivery` and merge checks. `README.md`'s "no model's answer reaches the next level unchecked" narrowed the same way.
- **f.4** `scenario.concorde.error-chain-to-developer` now has the task session escalate the run (`--by task-session`) and the main agent escalate that escalation (`--escalation 1`), expecting main-agent → task-session → Operation → Workers → worker; its test does both steps. Also corrected "recorded in the task record" to the task's trace node, which is where the Tasks contract (`task escalate`) keeps escalations and what the test already checked.
- **f.5** `scenario.concorde.parallel-tasks`: the tasks' Modules and the files they bind do not overlap, task sessions run `implement` (each ending `ok`), then `task-validation` and `delivery`; both are delivered and can be merged. The existing test already did exactly this.
- **f.6** Split into `references-registered-once` (all registered, lock held: checked out, config untouched), new `references-unregistered-refused` (one unregistered, lock held: stops before cloning any, registered or not) and new `references-registered-when-free` (the third existing test, which verified a situation the old scenario did not state). The code already registers before cloning any (decided in `init-references-lock`), so the Spec follows the code; the development skill's sentence "still checks out registered submodules but refuses to register a new one" was wrong for a mixture and now says it refuses before checking out any. Tests use two submodules so the refusal is shown to leave the registered one untouched too.
- **f.7** The five levels are introduced as the path of every change, followed by a short paragraph on unbound read-only runs (committed `HEAD` in a throwaway checkout), linking Execution; `req.concorde.grant-from-task-worktree` now names the source for both bound runs (workspace worktree) and unbound runs (unbound checkout), as the runner does. Id kept.
- **f.8** Execution's run lifecycle now says a run that takes the lock after it always finds the result written, and that seeing the result alone does not tell that the workspace is free.

No finding judged wrong; no finding said a provider's contracts were missing.

## Task session: bound spec review (2026-09-30)

Full pytest suite on d6418a2d: 788 passed, 4 skipped. The bound run `r-20260929T205612-spec_review-451c6b64` (ok, verdict `changes_required`, 7 blocking) reviewed both Modules after the first fixes; it recorded their review memory (`.concorde/reviews/spec/module.concorde.json`, `module.execution.json`, committed). Handled once, without a further review, in commit 7c7a0c3a:

- **concorde f.1 / execution f.1** Which worker configuration an unbound run uses: `runner.md` step 4 said the origin's, the scenario, Workers and Operations said the checkout's committed one. The code (`runner.py` swaps `context.worktree` to the checkout before `context.worker_model` loads `workers.json` from it) uses the checkout's, and "every input comes from the commit" is the design; so `runner.md`, Execution's entry and `req.concorde.worker-models-per-worktree` now say the checkout's committed configuration.
- **concorde f.2** `req.concorde.spec-gaps-stop` promised that a failed structural Spec check stops the Operation instead of resuming, and its prose that only configured-check failures are fed back. The developer reversed that rule on 2026-09-26 (Spec-writing workers may repair what the host's validation reports), Workers' resume round and glossary already say so. The SHALL now names only a Spec gap and a path outside the grant; the prose explains that a resume round carries configured-check failures and, once they pass, the step's own validation, such as structural errors a Spec-writing worker introduced. This narrows a root promise to match the developer's decision; reported to the main agent.
- **concorde f.3** Levels intro now says work is organized in five levels and uses only those it needs.
- **concorde f.4** (`specs/concorde/issues/module.md`, module.issues) and **f.5** (`specs/concorde/spec-tooling/module.md`, module.spec-tooling): outside this task's Modules; not changed, reported as follow-up.
- **execution f.2** `req.execution.one-result` now also excepts a runner killed by a signal it cannot handle (SIGKILL) before writing the result, naming the lost run; the entry's "a later run always finds the result" is qualified the same way.
- **execution f.3, f.4** Split into `req.execution.workspace-wait` + new `req.execution.workspace-wait-continues`, and `req.execution.unbound-checkout` + new `req.execution.unbound-origin-untouched`.
- **execution f.5** `scenario.execution.unbound-checkout` keeps the success case; new `scenario.execution.unbound-checkout-removed` (a step raises) and `scenario.execution.unbound-no-commit` (unborn HEAD), with the two existing tests' declarations moved to them.
- **execution f.6** Workspace lock held "from before its admission until after its result" in the entry and the glossary definition (matching `req.execution.workspace-lock`); an unbound run "takes no workspace lock" but its run lock.
- **execution f.7** Core concepts shortened: waiting, unbound-checkout details and observer rules moved to new subsections of "Running work" (Waiting for a busy workspace, Running unbound, Following a long run); concept anchors stay.
- **execution f.8, f.9** `req.execution.workspace-wait` links the run progress file; `req.execution.trace-node` says run progress file; `scenario.execution.detached` compares run result and trace node, not a run record.

## Task session: delivery (2026-09-30)

- `task-validation` `r-20260929T210640-task_validation-d370cf30`: ok, ready.
- `delivery` `r-20260929T211221-delivery-0e4bd24e`: **blocked** `not_ready`: `check.execution.tests` failed in `test_a_detached_run_is_announced_and_finishes_on_its_own` with `workspace_busy`: the test took the workspace lock as soon as the detached run's result existed, while the finished runner still held the lock (the fact Execution's f.8 fix states). A race in an existing test, not a behaviour change (it passed in both full suites). Fixed by waiting up to 30 s for the lock in that test (commit below), then delivering again.
  commit: 5b23e7c5 Execution tests: wait for the lock a finished detached runner may still hold
- `delivery` `r-20260929T211839-delivery-7f46fd13`: ok, delivery commit 2d440965 on `concorde/review-root`.

## Closed: merged, 2026-09-29T21:24:57Z
