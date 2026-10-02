# Decision log: fix-execution-root

Goal: Resolve the open Issues of module.execution and the root Module, carrying out the developer's and the main agent's decisions

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-bf0b3e2374d35abf9d30f730b22e8887 (module.concorde, high, decision-needed): Unbound reviews have incompatible primary-worktree side-effect guarantees
- I-09f5bed334e85150ba1646248b9f1d1a (module.concorde, high, decision-needed): The root access guarantee exceeds the Claude Code boundary contract
- I-698f34eb0eca56ba91ff60945f6817ea (module.execution, high, decision-needed): Unbound review reporting conflicts with origin preservation
- I-8535d5a4f70653aa962afe48219ca1b9 (module.execution, high, preferred-fix): Checkout cleanup scenario incorrectly excludes unrelated worktrees
- I-4aa967cd8d53596c83945875e850e183 (module.execution, high, obvious-fix): Runner error translation contradicts Check execution's handoff
- I-9752bcb0746450758f40ae1b4542aaff (module.execution, high, obvious-fix): Run-result example contradicts Validation's readiness contract
- I-9f627db2c49253e4b5d8af29e8540c3e (module.execution, high, obvious-fix): Workspace-lock requirement omits admission from its protected interval
- I-cb8137a05bba5878bb5e24f2d52a1e27 (module.execution, high, obvious-fix): Unbound runtime paths are attributed to the wrong configuration
- I-69f1349d1cb154309a6ae170fd01204d (module.execution, medium, decision-needed): Runner persistence failures have no defined outcome
- I-6971544d13455a74be1c9546e70d2d2d (module.execution, medium, decision-needed): Detached startup leaves outcome precedence and failed-launch disposition undefined
- I-3ccfaa74984b5131afdbe9ca195e61c3 (module.execution, medium, decision-needed): Step outcomes lack final-result composition rules
- I-7a0c343c8a05532cb3faba2425d9e716 (module.execution, medium, preferred-fix): Saved run results need atomic publication semantics
- I-26ac3e461c8a55abaf78e0539962070d (module.execution, medium, preferred-fix): Waiting progress cannot represent every workspace-lock holder
- I-30b3cd2e488d5c6b99f026fab360af50 (module.execution, medium, preferred-fix): Execution's independence claim omits its workflow transport dependency
- I-de6c254d56745caba6d2cc2070c6bb23 (module.execution, medium, preferred-fix): Arbitrary workspace locations exceed the trace identity lookup promise
- I-7d5400085d3c58a78ee14241a3fc797a (module.execution, medium, preferred-fix): Detached-namespace scenario asserts an undefined workflow error outcome
- I-1807f41290ea59e4ada9ffe24e525027 (module.execution, medium, preferred-fix): Child collaboration explanations omit load-bearing handoffs
- I-1b505d2c972f5e37b8e29af3a1d765fe (module.execution, medium, obvious-fix): Unbound error actor inconsistently names worktree and origin
- I-02619bb6f9f854349cf9f6ff6bcac871 (module.execution, medium, obvious-fix): Entry overstates submodule availability in unbound checkouts
- I-b879de5d5cf15c6c81196d50c8506c5e (module.concorde, medium, obvious-fix): init-references reports a reference whose fetch failed as checked out
- I-7dcd834e148f5de08e52646d3d7ee724 (module.execution, low, obvious-fix): Trace-node requirement combines independent obligations
- I-47f3e6a4f61c5a828c707b964d45f853 (module.execution, low, obvious-fix): Workspace-wait requirement carries a separate progress obligation
- I-9fa4c9d88b4c5a6bbbb4b2ccbcb005dc (module.concorde, low, obvious-fix): Link the task brief where the root Module names it
- I-95a2956bac23594b984a39ad2a614ecc (module.execution, low, suggestion): Clarify the Git-administration exception to origin preservation
- I-7cacce603d8059b9a509bbc45814ad74 (module.execution, low, suggestion): Clarify the actor in the finalization sentence
- I-f669262daad05dffac15e34a6c73a970 (module.execution, low, suggestion): Introduce definition before describing the run lifecycle
- I-a82d3163e18b544497753211ca2f1e94 (module.execution, low, suggestion): Label the entry's command forms as abbreviated

Decisions:
- I-698f34eb0eca56ba91ff60945f6817ea and its duplicate I-bf0b3e2374d35abf9d30f730b22e8887,
  DEVELOPER (2026-10-02), option A: an unbound run may publish Issues, only through the Issues
  store, each as its own commit under the merge lock; the examined checkout, the Specs and the
  code stay untouched. Qualify req.execution.unbound-origin-untouched and the root's "changes
  nothing" (specs/concorde/module.md) to say exactly this. Close I-bf0b3e23 as a duplicate of
  I-698f34eb only if you fix both in one change; otherwise resolve both.
- I-09f5bed334e85150ba1646248b9f1d1a, DEVELOPER (2026-10-02), option A (not the alternative of a
  read-time hook): narrow req.concorde.no-wider-than-type to the computed grant and name beside it
  the Claude Code limit that a file created after the deny rules were generated stays readable,
  linking the Harness's known limits. Add no new enforcement.
- I-69f1349d1cb154309a6ae170fd01204d, main agent: a failure to create the initial records refuses
  before any step runs, with a link on stderr and exit 1; a failure of the final writes prints the
  result and its error chain, exits 1, releases the locks and counts as a lost run; state both as
  exceptions to req.execution.one-result.
- I-6971544d13455a74be1c9546e70d2d2d, main agent: an existing progress file wins (the run is
  announced, then finished or lost); detach_failed only when no progress file appeared, in which
  case no step ran and the run's folder is removed.
- I-3ccfaa74984b5131afdbe9ca195e61c3, main agent: compose as the implementation does: each step's
  output merged key by key over the output so far, a later key replacing an earlier one; evidence
  appended in step order; a stopping step keeps the output so far; all steps continuing gives
  `ok` with the last step's summary, which a definition must supply.

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

- Baseline at HEAD 84994940 on the fresh worktree: `.venv/bin/python -m pytest -n auto` 922 passed,
  5 skipped, 453 subtests passed, no failure; build ran clean.
- Every Issue of the brief still stood at HEAD 84994940; all are fixed in commit 1dbd1569.
  I-bf0b3e23 was fixed in the same change as I-698f34eb and closed as its duplicate; the other 26
  are added to the task with `task resolve`, the four suggestions included (each was a small,
  clear improvement of the same documents).
- I-3ccfaa74 (main agent's decision "compose as the implementation does"): the implementation
  differs from the rules the decision lists. A "continue" carrying output replaces the output so
  far whole (steps may also set it in the run context); outputs are never merged key by key. When
  every step continues, the summary is the runner's own, `<name> finished for <Modules>.`, not the
  last step's (a "continue" carries no summary); a definition wanting its own summary ends with an
  `ok` stop, as the reviews and task-validation do. I followed "as the implementation does" and
  specified exactly that behaviour in runner.md "Composing the result", changing no code: making
  outputs merge and requiring every definition to supply a summary would change the code of
  Operations and Commands, outside this task. Evidence appended in step order and a stop keeping
  the output so far match the decision.
- I-69f1349d: carried out as decided, codes `run_unrecorded` and `result_unsaved` (component
  links of `Execution runner (<command line>)`, reason environment, cause the `Execution (run
  store)` link). The first run progress file now counts as an initial record: before, a failed
  write of it was ignored, so a run could take steps with no progress file and the I-6971
  decision ("detach_failed only when no progress file appeared, in which case no step ran") would
  not hold. When only the final trace.json fails after result.json was published, the result
  stands and the trace node, still running with no run lock held, reads as lost; this is how
  "counts as a lost run" is specified for that case. New requirements unrecorded-runs-nothing and
  unsaved-printed, scenarios run-unrecorded and result-unsaved, tests.
- I-6971544d: as decided; additionally the detaching command checks once more for the progress
  file after killing the runner (a file written meanwhile announces the run, consistent with
  "an existing progress file wins") and removes a run lock file the killed runner left. New
  requirement detach-failed-leaves-nothing, scenario detach-failed, test.
- Preferred fixes: I-8535d5a4 keeps pre-existing worktree registrations (the scenario and its
  test now include a task worktree) rather than narrowing the fixture. I-7a0c343c writes
  result.json under a temporary name in the run's folder and renames it into place;
  req.execution.result-atomic, scenario result-published-whole, test. I-26ac3e46 names the holder
  by Tracing's holder line (the code already did; the Spec said "the run"); new
  req.execution.waiting-progress (also the I-47f3e6a4 split), scenario workspace-wait-merge, test.
  I-30b3cd2e narrows the independence claim to the runner, run store and execution commands and
  explains Workflows' reliance on Main session's workflow_step, adding no uses relation.
  I-de6c254d qualifies lookup to Tracing's search roots with the node-path fallback, no new
  discovery. I-7d540008 states the Execution-owned consequences (no result, run lock unheld,
  lost) and gets an Execution test; the Workflows test that verifies it still does. I-1807f412
  explains the definition handoff, Workers' early identity and interruption, and Check
  execution's link at design level.
- I-4aa967cd: the same conflict held for Issues refusals (the store makes its own link, which
  reviews keep unchanged), so runner.md now exempts both Check execution and Issues from the Spec
  core translation.
- I-b879de5d: a reference counts as checked out only at the recorded commit; a clone elsewhere is
  completed in place (fetching the commit only when missing) and reported as `completed @ <commit>
  (was at <head>)`; `--check` reports it as not at the recorded commit. New scenario
  scenario.concorde.references-completed in development.md, test.
- Verified: build --check and spec-validation clean; full suite 930 passed, 5 skipped.
- Recorded I-1cb80f6b196b5245b747245ff8b87315 (module.workflows, obvious-fix, low): `step_lost`'s
  cause `host_ended`, emitted by workflows/step.py, is defined nowhere in Workflows' contracts.
  Not fixed here: module.workflows is not this task's Module.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T02:46:38Z

fix-execution-root delivered: delivery commit 75ed51aa (run r-20261002T024350-delivery-dc562a86) over fix commit 1dbd1569. No escalations.

Baseline (fresh worktree, HEAD 84994940): full suite 922 passed, 5 skipped, no failure. Final: build --check and spec-validation clean, full suite 930 passed, 5 skipped, task-validation ready.

Resolved by the task (26, added with task resolve): I-09f5bed3, I-698f34eb, I-8535d5a4, I-4aa967cd, I-9752bcb0, I-9f627db2, I-cb8137a0, I-69f1349d, I-6971544d, I-3ccfaa74, I-7a0c343c, I-26ac3e46, I-30b3cd2e, I-de6c254d, I-7d540008, I-1807f412, I-1b505d2c, I-02619bb6, I-b879de5d, I-7dcd834e, I-47f3e6a4, I-9fa4c9d8, and the four suggestions I-95a2956b, I-7cacce60, I-f669262d, I-a82d3163 (each a small, clear wording fix, so none left open).
Closed as duplicate: I-bf0b3e23 of I-698f34eb, fixed in the same commit.

Decisions carried out:
- I-698f34eb/I-bf0b3e23 (developer, A): req.execution.unbound-origin-untouched, the Execution entry and the root say an unbound run may publish Issues only through the Issues store, each its own commit under the merge lock; Git's checkout administration is named as outside the promise (I-95a2956b).
- I-09f5bed3 (developer, A): req.concorde.no-wider-than-type now bounds the computed grant and names the Claude Code late-created-file gap, linking the Harness's known limits; no new enforcement.
- I-69f1349d: run_unrecorded (no step, link on stderr, exit 1) and result_unsaved (result printed, chain on stderr, exit 1, locks released, run lost), both exceptions of req.execution.one-result; code and tests. Addition: the first run progress file now counts as an initial record (a failed write of it used to be ignored), otherwise the I-6971 rule "no progress file means no step ran" would not hold. When only the final trace.json fails, the published result stands and the node reads as lost.
- I-6971544d: an existing progress file wins; on detach_failed the run's folder and the leftover run lock file are removed. Also: after killing the runner the command checks once more, and a progress file written meanwhile still announces the run.
- I-3ccfaa74: your decision says "compose as the implementation does", but the implementation differs from the rules it lists. A "continue" with output replaces the output so far whole; nothing is merged key by key. When every step continues, the summary is the runner's own "<name> finished for <Modules>." ("continue" carries no summary). I followed "as the implementation does" and specified exactly that, changing no code. Merging outputs and requiring a summary from every definition would change Operations' and Commands' code, outside this task: open a task for it if you want those rules instead.

Preferred fixes chosen:
- I-8535d5a4: the scenario and test keep pre-existing worktree registrations, with a task worktree in the fixture.
- I-7a0c343c: result.json is written under a temporary name and renamed into place (req.execution.result-atomic, scenario result-published-whole).
- I-26ac3e46: waiting_for and the refusal name the holder by Tracing's holder line (the code already did this; the Spec said "the run"). New req.execution.waiting-progress, which is also the I-47f3e6a4 split, and scenario workspace-wait-merge.
- I-30b3cd2e: the independence claim is narrowed to the runner, run store and commands, and the entry explains Workflows' use of Main session's workflow_step; no uses relation added.
- I-de6c254d: identity lookup is qualified to Tracing's search roots, with the node-path fallback.
- I-7d540008: the scenario asserts Execution's own consequences and has a new Execution test.
- I-1807f412: the children's handoffs are explained.
- I-4aa967cd also covered Issues refusals, which carry their own link like Check execution's.
- I-b879de5d: a clone that is not at the recorded commit is completed in place; --check reports it.

New Issue for another Module: I-1cb80f6b (module.workflows, obvious-fix, low): step_lost's cause host_ended is defined nowhere in Workflows' contracts.

Still open: none from this task. Every decision is in the decision log.

## Closed: merged, 2026-10-02T02:47:06Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 75ed51aa9964a57670066ebcd0095c915d593115 into main and closed it as merged. Nobody answers a report after that.
