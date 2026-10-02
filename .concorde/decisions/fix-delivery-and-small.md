# Decision log: fix-delivery-and-small

Goal: Make Delivery never leave a commit it rejected and re-validate on recovery, and resolve the small open Issues of adoption, spec-mcp and code-review

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-96365a61a2e15588803f3ebbb04828e4 (module.delivery, high, suggestion): A commit rejected by Delivery can still be recognized as delivered
- I-1bbc7a1b9f54586e9b656c37b901b70c (module.adoption, medium, obvious-fix): Adoption lets the main agent run its steps in a task worktree
- I-53fc26907f3b52b29765e7157746a4fd (module.spec-mcp, low, obvious-fix): Spec MCP's validate calls its answer the spec-validation command's envelope
- I-23765cae61e558529b5dfd5fe4a22f86 (module.code-review, low, suggestion): Code review and Spec review duplicate the earlier-Issue settling logic

Decisions:
- I-96365a61a2e15588803f3ebbb04828e4 (escalated by task fix-small-modules as
  delivery_recognition_change), main agent: keep the recognition rule (subject alone, glossary
  and contract unchanged). Delivery must not leave a commit it rejected: when it rejects its own
  commit (commit_unverified at step 9) it removes that commit, resetting the task branch to the
  validated parent while keeping the index and worktree as they were, and says so in the chain;
  and its recovery re-validates any head carrying the delivery subject instead of accepting it.
  module.delivery only; if Tasks would need a change, escalate.
- I-23765cae61e558529b5dfd5fe4a22f86 (suggestion, the shared earlier-Issue helper): module.spec-review
  and module.operations are bound to this task now, so judge it like any suggestion.

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

- Baseline: the full suite on the fresh worktree (HEAD 84994940) passed: 922 passed, 5 skipped,
  453 subtests passed. Nothing to record as a failure.
- I-53fc26907f3b52b29765e7157746a4fd (obvious-fix): Spec MCP's `validate` is now described as Spec
  core's validation result as `validate_repository` returns it, without the update findings the
  `spec-validation` command adds and never touching the update mark (contracts table, the
  load-failure requirement, scenario.spec-mcp.validate and the module text). The code already
  returned `validate_repository`'s result, so only the Spec changes.
- I-1bbc7a1b9f54586e9b656c37b901b70c (obvious-fix): Adoption now says the main agent opens the task
  and hands it to the task session, which runs the three steps in its task worktree; the main agent
  settles the decision points within its authority and puts the rest to the developer.
- I-96365a61a2e15588803f3ebbb04828e4 (decided by the main agent), carried out in module.delivery
  only (commit 0c94620d):
  - Removal: a delivery commit that does not verify in step 10 is taken off the bound branch with
    `git update-ref refs/heads/<branch> <validated head> <commit>` (compare-and-swap), which keeps
    the index and the worktree as the commit left them. My decision: Delivery removes it only when
    the validated head is the commit's only parent and the branch still points at it; otherwise
    (a post-commit hook that committed again on top, or Git refusing the move) it moves nothing
    and says the commit stays and why. Reason: a post-commit hook's commit is at HEAD, and a plain
    reset would have taken off a commit Delivery did not create (found by a test). The run's
    trace node keeps referencing the removed commit as `commit`, since the run created it.
  - Recovery: a delivery commit found at the head (one parent, nothing waiting) is now validated
    again by steps 3 to 6, the readiness and, unless `--adoption`, the scenario-test rule, exactly
    as new work; a new step 7 reports it `recovered` only then. My decision: a found head that
    does not validate ends `blocked` with `not_ready` or `unverified_scenarios`, like any delivery,
    with the note that the found commit is not reported, rather than `failed commit_unverified`,
    since the fix is the same as for any not-ready workspace (repair, deliver again on top).
  - Spec: steps renumbered to eleven; new req.delivery.rejected-removed and
    req.delivery.recovered-revalidated (req.delivery.recovered-verified, which Tasks relies on, is
    unchanged: the one-parent check); req.delivery.history-kept allows only the move back from its
    own rejected commit; scenario.delivery.hook-changed-commit updated, new
    scenario.delivery.recover-not-ready; contract.delivery.output bumped to version 6 (behaviour
    of `recovered` changed). The recognition rule (subject alone) and Tasks are unchanged.
- I-23765cae61e558529b5dfd5fe4a22f86 (suggestion): fixed, since it clearly removes about 150 lines
  of duplicated rules at small cost. The shared parts moved to `src/concorde/operations/review_issues.py`
  (module.operations, already bound by `src/concorde/operations/`): `earlier_issues` by Operations,
  `settle` with a `skipped` predicate and the unoffered reason, `report` with an Issue-report
  builder. `code_review/issues.py` and `spec_review/reporting.py` keep their public names as thin
  wrappers, so callers and tests are unchanged; Operations' realization paragraph and both reviews'
  `uses-operations` paragraphs now describe the shared helper (commit 5653dc69).

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T02:34:13Z

Task fix-delivery-and-small delivered: delivery commit 85261a175957693a6761c4eaa583fcfd0d95bfe0 on concorde/fix-delivery-and-small (run r-20261002T023142-delivery-d16cb1dd). No escalations.

Baseline: the full suite on the fresh worktree passed (922 passed, 5 skipped). Final: 924 passed, 5 skipped; build --check, spec-validation and task-validation (ready) all pass.

Fixed and added to the task with task resolve (the merge closes them):
- I-96365a61a2e15588803f3ebbb04828e4 (delivery; carried out as you decided, module.delivery only, Tasks and the recognition rule unchanged): (1) Delivery takes a delivery commit that fails verification off the bound branch with git update-ref back to the validated head, keeping the index and worktree, and says so in the chain. My decision: it does this only when the validated head is the commit's only parent and the branch still points at it. Otherwise (for example a post-commit hook that committed again on top, or Git refusing the move) it moves nothing and says the commit stays and why. A test showed that a plain reset would have removed the hook's commit too. (2) Recovery: a delivery commit found at the head (one parent, nothing waiting) is now validated again by the readiness steps and, unless --adoption, the scenario-test rule, before it is reported as recovered. My decision: a found head that does not validate ends blocked not_ready / unverified_scenarios, like any delivery, with a note that the found commit is not reported, rather than failed commit_unverified. Spec: eleven steps; new req.delivery.rejected-removed and req.delivery.recovered-revalidated; req.delivery.recovered-verified (which Tasks relies on) is unchanged; history-kept allows only the move back from its own rejected commit; new scenario.delivery.recover-not-ready; contract.delivery.output v6.
- I-1bbc7a1b9f54586e9b656c37b901b70c (adoption, obvious-fix): the task session runs the three steps in its task worktree; the main agent opens the task and settles the decision points within its authority.
- I-53fc26907f3b52b29765e7157746a4fd (spec-mcp, obvious-fix): validate is described as Spec core's validation result (validate_repository's), without the update findings and never touching the update mark; this is a Spec-only change because the code already did this.
- I-23765cae61e558529b5dfd5fe4a22f86 (suggestion, fixed): the shared earlier-Issue reading, settling and reporting moved to src/concorde/operations/review_issues.py. code_review/issues.py and spec_review/reporting.py are now thin wrappers with unchanged names. The Specs of Operations, code review and spec review describe the helper.

Closed as already resolved or duplicate: none. Suggestions left open: none. Nothing remains open.

## Closed: merged, 2026-10-02T02:34:39Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 85261a175957693a6761c4eaa583fcfd0d95bfe0 into main and closed it as merged. Nobody answers a report after that.
