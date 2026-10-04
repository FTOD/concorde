# Decision log: fix-open-execution

Goal: Fix the open Issues of the execution part (runner, Operations and Commands frameworks, Check execution)

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

### Your 28 Issues

- I-517f519d71d65d4283ce6ed460eba515 (medium, preferred-fix, module.execution): Unexpected exceptions outside a step escape result composition
- I-c5823f430bbd5d1b94b347e7ba1eb4a1 (medium, preferred-fix, module.execution): Cancellation handling ends before checkout removal and result publication
- I-2f6e27e808e5528ab8088fd1b667b3d9 (medium, preferred-fix, module.execution): The invalid-result replacement is not itself revalidated
- I-3fd2e54f066b5c7bb42b5cbd6c7751ec (medium, preferred-fix, module.execution): The idle check misses unbound runs started in other unbound linked worktrees
- I-54b3c9fd911e56a0824fddb63697f006 (medium, preferred-fix, module.execution): Runtime linking skips supported paths and required evidence
- I-895323853c265361a5881fc7efdb300b (medium, preferred-fix, module.execution): Submodule sparse settings are not preserved faithfully
- I-39a2cd0401b1586d827cd2329be98277 (medium, preferred-fix, module.execution): Detached setup failures bypass structured record-failure handling
- I-eef9c7aaf3425f289774660dc575b967 (medium, preferred-fix, module.checks): Input deletion during a check raises instead of reporting stale_evidence
- I-e1bff8bc0cc25440a7f358ff40f02913 (medium, obvious-fix, module.execution): Failed submodule population leaves partial inputs visible
- I-cc9ab3d84f065dc082d9c758505a0858 (low, preferred-fix, module.execution): Run error details leave the run, workspace and Modules to the actor and envelope
- I-368b89b492185810b20240bd4c88b008 (low, preferred-fix, module.checks): A cancelled configured check leaves no log and a running trace node
- I-ceb6cfd5235c5396b4e05a172259ea85 (low, obvious-fix, module.execution): Running progress files omit summary instead of holding null
- I-47713e8bcb615d738767274d82a33d50 (low, obvious-fix, module.checks): run_checks finds a later Module's missing input only after earlier commands ran
- I-5e0652b1bc885c33ada6eb0a221746fc (low, obvious-fix, module.checks): A non-iterable argv raises TypeError before argv validation
- I-93c3bfae77cc5eb196265a51063a7e06 (low, obvious-fix, module.checks): Environment names with a trailing newline are accepted
- I-0a6d5b689aef5d1abc81d6ce318f05cb (low, obvious-fix, module.checks): A relative trace_directory yields a relative log path
- I-f7aaa027a8fb5e3486aba556717c48d4 (low, obvious-fix, module.checks): Timeout failure links omit the promised exit code
- I-8c736127e9a75171be9d846f6bfd1132 (low, obvious-fix, module.checks): execute_check raises FileNotFoundError for a missing project root
- I-b147d2d96f235042839d807bd26d3b7a (low, obvious-fix, module.checks): tempfile.gettempdir() failure escapes the scratch selection
- I-b4fe5ad37c4557809f5e6d9c99e7ee4a (low, obvious-fix, module.execution): Detached-run test removes its project while the refused runner may still write
- I-72b32bfd02fa5d618d07d67164af5f36 (low, obvious-fix, module.execution): Unbound checkout cleanup does not say what happens when the direct-removal fallback also fails
- I-a6f3475b51a355ebb6bda7cd2b51cd8f (low, obvious-fix, module.execution): req.execution.trace-node's statement omits the lobby its own explanation names
- I-1f0d13decc13596fb9aea906b6d99388 (low, obvious-fix, module.execution): req.execution.result-printed and the exit-status sentence leave out the record-failure cases
- I-63a5e814bb9b550a8a823b68022e2020 (low, obvious-fix, module.execution): The run-result example's task-validation output lacks Validation's workflow object
- I-700bdd87297c5404889d1faf21b3d780 (low, suggestion, module.execution): No focused test that a stopping step prevents later steps
- I-d36535ca18055e82b2e6f4761fac44fa (low, suggestion, module.checks): A span finished after its trace was flushed mutates and re-emits the flushed record
- I-b77b34b5e8a9556e843d27d0a08bd9c7 (low, suggestion, module.execution): Say how a later run treats a saved result of an older run-result version
- I-6c7a7ad94e2e52159963f4de5cc4081d (low, suggestion, module.execution): Separate provider examples from the generic run-result contract

## Task session decisions (2026-10-04)

All 28 Issues were fixed directly in code, Specs and tests (no Operation run). Choices made without
the developer, by Issue:

- I-c5823 (preferred-fix, cancellation window): one `_Signals` handler is installed for SIGINT/SIGTERM
  from the parse to the runner's exit. Armed (binding check to end of execution) it raises
  `Cancelled` once; otherwise it holds the signal: held during first-record creation, it cancels the
  run as soon as it is armed (no step runs); held after the execution, it changes nothing and the run
  finishes as composed. Chosen over re-delivering the signal after the finish, since the runner exits
  right after anyway and a result must always be written.
- I-517f (preferred-fix, exceptions outside steps): any non-refusal exception from the binding check to
  the execution becomes a `host_error` result whose cause's actor is `Execution runner (<command line>)`;
  a step returning neither Continue nor Stop is treated as raising; `node.update` between steps is
  best-effort like later progress writes (the node is written again after the result). Checkout
  removal errors become `checkout-not-removed` evidence.
- I-2f6e (preferred-fix): the invalid-result replacement keeps only contract-satisfying parts (drops
  malformed evidence items, a non-object worker, non-name Modules/worker runs, an invalid commit),
  keeps the earlier error as cause only if it is a well-formed link, and is validated again (a still
  invalid replacement raises, i.e. a runner defect is never hidden). A result whose error is not of
  the run's own level (`operation`/`command`) is now invalid.
- I-3fd2 (preferred-fix): the idle check reads the run locks of every worktree `git worktree list`
  names (primary first), not only the primary's.
- I-54b3 (preferred-fix): ignore status is asked before anything else; an ignored path below missing
  directories gets them created inside the checkout (never through a link leading out of it); an
  existing or escaping target is explained with `environment-not-linked`; a missing source is passed
  over silently.
- I-8953 (preferred-fix): sparse patterns are copied line by line through `sparse-checkout set --stdin`
  in the origin's own mode (`--cone` when `core.sparseCheckoutCone` is true, else `--no-cone`).
- I-e1bff: a submodule whose sparse setup or read-tree fails is removed at once and recreated empty;
  removal leftovers add `checkout-not-removed` evidence.
- I-72b3: `_remove` reports what the direct removal actually did (directory gone or what is left,
  prune exit) and names `git worktree remove --force <path>` / `git worktree prune` when something is
  left; Spec step 5 and req.execution.checkout-removed say so.
- I-39a2 (preferred-fix): `--detach` raises `run_unrecorded` (exit 1, stderr) when it cannot create the
  run folder or `host.out`, starting no runner; a Popen failure removes the folder and returns
  `detach_failed` with `host_pid` null.
- I-cc9ab (preferred-fix): of the two options I let the Spec accept the actor for run and workspace
  (it already names them per runner.md Errors) and made `RunContext.fail` end every detail with
  `(Modules: <ids>)` / `(Modules: none)`; req.execution.error-detail reworded accordingly.
- I-eef9 (preferred-fix): a re-measure that raises (`OSError`, `CheckError`) after the run is
  `stale_evidence`, and the node ends `stale_evidence`.
- I-368b (preferred-fix): Check execution cannot tell a caller's cancellation (Execution's `Cancelled`)
  from an unexpected error, so any exception escaping a check ends its node `failed` with outcome and
  content status `interrupted` (new enum value: contract.checks.check-trace bumped to version 2) and the
  drained output as log; the bubblewrap backend now also catches foreign interruptions, cleans up and
  re-raises them unchanged carrying `check_output` (KeyboardInterrupt still becomes CheckCancelled).
- I-47713 / I-5e06: `run_checks` judges every kept check (argv, env, timeout, `{python}`) and finds every
  kept check's inputs before the first command. New public `selective(check)` (a non-list argv is not
  selective); `src/concorde/method/checks.py` (module.method's file) uses it in place of the
  TypeError-prone expression: a two-line edit of another group's file, kept minimal.
- I-93c3, I-0a6d, I-f7aa, I-8c73, I-b147, I-ceb6, I-a6f3, I-1f0d, I-63a5, I-b4fe: the obvious fixes the
  Issues describe (fullmatch; absolute trace directory; `timed out (exit code -1)`; CheckSandboxError for
  an unresolvable project; gettempdir failure skips to the next candidate; null running summary; the
  lobby in req.execution.trace-node; the record-failure exit in req.execution.result-printed and
  module.md; the example's `workflow` object; detached tests wait for the run lock to go).
- Suggestions fixed because cheap: I-700b (stop-then-sentinel test), I-d36 (a flushed timing trace is
  sealed and its sink gets a copy), I-b77b (`--input` whose saved result breaks the current run result
  contract is refused with `input_not_admissible`; Spec states it), I-6c7a (contracts.md separates the
  runner's own evidence kinds from those definitions define, and calls the task-validation output an
  illustration). contract.execution.run-result stays version 3: only wording and the example changed.

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:35:31Z

fix-open-execution delivered: delivery commit c1269d26 on concorde/fix-open-execution (task-validation ready; full suite 1103 passed, 5 skipped; build --check and spec-validation pass).

Resolved: all 28 Issues, added to the task with task resolve. None closed as not holding, none left open.

Decisions I took (each with its reason is in the decision log):
- I-c5823: one SIGINT/SIGTERM handler from the parse to the runner's exit. A signal during first-record creation is held and cancels the run before its first step. A signal after the execution changes nothing, so checkout removal, composition and finish always complete.
- I-517f: any runner exception outside a step becomes a host_error result, with actor "Execution runner (<cmd>)". A step returning neither continue nor stop counts as raising. node.update between steps is best-effort.
- I-2f6e: the invalid-result replacement drops whatever breaks the contract (bad evidence items, non-object worker, …) and is validated again. A result whose error is not of the run's own level is now invalid.
- I-cc9ab: the Spec now lets the actor carry run and workspace. RunContext.fail ends every detail with "(Modules: …)".
- I-368b: Check execution cannot tell a cancellation from an error, so a check node ends with the new status "interrupted" (contract.checks.check-trace bumped to v2) and its drained log. The backend re-raises a foreign interruption unchanged, carrying check_output.
- I-3fd2: the idle check reads the run locks of every worktree git lists. I-8953: sparse patterns are copied line by line via --stdin, in the origin's cone or non-cone mode. I-54b3: nested ignored runtime paths get their parent directories created inside the checkout, and every path not linked is explained. I-39a2: --detach reports run_unrecorded for an unwritable store, and detach_failed (leaving nothing) when the runner cannot start.
- I-b77b, a suggestion I implemented: --input refuses a result that breaks the current run result contract. contract.execution.run-result stays at version 3, since only wording and the example changed.

Small cross-group edit: src/concorde/method/checks.py (module.method) now calls the new checks.selective() helper instead of the TypeError-prone expression. It is a two-line change.

Nothing is open, and no decision needs the developer.

## Closed: merged, 2026-10-04T02:35:51Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit c1269d269045f22824b2daaebb077ba4cd7675c9 into main and closed it as merged. Nobody answers a report after that.
