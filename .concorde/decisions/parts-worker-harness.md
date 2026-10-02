# Decision log: parts-worker-harness

Goal: Make the worker harness part depend on the kernel alone, launching a worker from a grant, instructions, resolved configuration and a round-validation callback given as data, and move the standard worker sequence into Method so that Execution launches no worker

## Brief (main agent, 2026-10-03)

### Context shared by the code tasks

The developer decided (2026-10-03) to split Concorde into independently installable parts: any
part, or any subset, can be installed into a project and works without the parts it does not depend
on. Everything happens on the integration branch `parts-split` (the primary worktree is on it; tasks
merge there, never into `main`). Done so far: `parts-spec` (the Specs describe the nine parts and
their directions: root `specs/concorde/module.md` "The parts", `req.concorde.part-dependencies`,
`part-alone`, `absent-part-stated`), `parts-layout` (one directory per part under `src/concorde/`
and `tests/concorde/development/test_part_dependencies.py`, whose `KNOWN_EXCEPTIONS` lists every
import still breaking the directions, grouped by the code task that removes it; the test fails on a
new violation and on a stale exception) and `parts-kernel` (the kernel library in
`src/concorde/kernel/`: typed values, contract-schema checking, file transactions, digests,
workspace binding, delivery commits, workspace and merge locks, registered trace roots). Read their
decision logs in `.concorde/decisions/`. Remaining code tasks: issues and worker harness (in
parallel), then execution, workflow, method, coordination, distribution.

**How an optional integration works (main agent's decision, 2026-10-03).** A part never imports the
Python code of a part it does not depend on, not even guarded by `ImportError`: that is what
`req.concorde.part-dependencies` says ("import code of ... only the parts it depends on"). An
optional integration reaches the other part only through what that part publishes as a contract:
its `concorde` command (JSON in and out, as its Spec defines), or a file format its Spec defines,
read (never written) by the relying part. Whether the other part is installed is told by the host
or the format itself: the `concorde` command refuses a command of an absent part with a stable code
naming the part (`req.distribution.absent-part-named`; until the distribution task builds the
dispatcher, treat "command not available" the same way), and an absent format's files simply do not
exist. The relying part then skips the feature with a plain statement naming the missing part
(`req.concorde.absent-part-stated`). A process that holds a lock the other part's command needs
hands it on as Tracing's "Handing a lock on" describes. The parts-layout test's allowance of
`method -> issues` imports is withdrawn accordingly: remove it from the test when your task removes
the last such import (the issues task does).

**Rules for every code task.** Rapid-iteration rule: no compatibility re-exports, shims, transitional
adapters or dual paths; refactor boldly. Keep record formats the Specs did not change readable, since
the primary worktree's existing `.concorde/` records (tasks, history, Issues, locks) must still read
after the merge. Remove every exception your task makes stale and add none (moving one to another
group is fine when its remaining reason belongs to another task). If a Spec is wrong or silent in a
detail the code needs, fix the Spec in your task and record why; escalate only a conflict with the
developer's decisions above. Verify with `build --check`, `spec-validation`, the full suite
(`.venv/bin/python -m pytest`) and smoke runs of the commands you touched from the task worktree,
then `task-validation` and `delivery`, and report.

### What this task does (worker harness)

Read `specs/concorde/worker-harness/` (module "What a launch is given", "A launch from start to
end"; Workers' launch.md and contracts.md, especially the grant input contract and round
validation; Harness) and Method's standard worker sequence (`specs/concorde/method/module.md` and
`req.method.*`, e.g. `grant-as-data`, `workspace-specs`, `models-placed-first`,
`glossary-by-entry`) first.

- **The worker harness part depends on the kernel alone.** Remove the `worker harness` group of
  `KNOWN_EXCEPTIONS`: it receives the grant as data in its own grant input format (`rw`, `ro`,
  `names`, context identity, task type) instead of importing `spec.grants`; the caller's task
  instructions (including any glossary text, which Method now composes) instead of
  `spec.glossary`; a round-validation callback instead of importing `execution.checks`; the
  Operations and worker ids the caller declares instead of `execution.operations.catalog`; its own
  errors instead of `spec.repository_base`. The glossary ownership audit (`audit.py ->
  spec.glossary`) is Spec-aware and moves to Method's round validation or Method's own audit, as the
  Specs say.
- **The standard worker sequence moves into Method**: computing and freezing the grant through Spec
  core, projecting it into the worker harness's input format, composing the instructions, resolving
  and admitting the worker's configuration, the round validation with configured checks, and the
  launch. Execution no longer launches workers: remove the `execution` exceptions on
  `worker_harness.*` (`execution/context.py`, `execution/operations/admission.py`,
  `execution/checkout.py` — the runtime paths are given to it — and `execution/checks/checks.py ->
  worker_harness.runs`) by moving that code to Method or giving Execution what it needs as data.
  Execution's remaining Spec reads and its catalogs stay for the execution task.
- **A contract test** that the grant Spec core computes, projected by Method, satisfies the worker
  harness's grant input format (Kernel/Worker harness Specs mention it), since the spec part keeps
  its own copy of the formats.
- Worker records (run record, progress file, round nodes) keep their formats unless the Specs
  changed them.

Bound Modules: Worker harness, Harness, Workers, and Method where the sequence lands. The issues task
runs in parallel on `issues/` and moves `execution/operations/review_issues.py` into Method; if your
changes meet theirs in one file, keep yours minimal there.

## Task session decisions (2026-10-03)

- **Round validation interface.** `worker_harness.workers` takes `round_validation(worktree,
  round_folder) -> RoundValidation(evidence, repair, failure, violation, unavailable)` with
  `Refusal(code, detail, causes)`, exactly the fields of launch.md "Round validation". Reason: the
  Spec names these fields; dataclasses keep the harness free of any caller type.
- **A round validation that raises** ends the run `failed` with a new code
  `validation_unavailable` (reason `capability`), added to launch.md's Errors and Rounds tables.
  Reason: the Spec was silent; the old code silently accepted the round ("not run"), which would let
  a broken caller pass unvalidated work.
- **Grant input enforced.** The harness refuses a grant carrying fields beyond `task_type`,
  `entries`, `context_identity`, or a `task_type` other than the request's, with `grant_malformed`.
  Reason: the contract has `additionalProperties: false`; refusing keeps Method from passing Spec
  core's richer grant by accident. The Modules a job is about became a request label `modules`
  (recorded in the run node's metadata as before); launch.md's Inputs table names it.
- **Artifact paths in round evidence**: a top-level string of an evidence value that is an absolute
  path below the round's folder is stored relative in the round node and made absolute again by
  `read_record` (launch.md evidence row says so). Reason: the contracts asked for it without saying
  how the harness tells an artifact path from other evidence.
- **Configuration reader takes the declared Operations** (`load`, `validate_config`,
  `worker_choice`, `check_mapped` all take `declared: {operation: worker ids}`); Method's
  `declared_workers()` builds it from Execution's Operation catalog.
- **Method's sequence lives in `src/concorde/method/workers.py`** (new realization
  `realization.method.workers`, titled "Standard sequence" to avoid an unlinked-term warning):
  admission step, `operation(...)` helper that puts the admission first and sets the runtime-path
  resolver for Operations that may run unbound (every Method Provider definition now uses it),
  grant projection, instruction composition (glossary terms and the Spec-gap rule moved out of the
  harness brief into the instructions), round validation (glossary by entry, configured checks,
  step's own validation), the glossary check after the worker run, and `absorb`.
  `execution/operations/admission.py` is removed; the catalog no longer prepends anything.
- **Execution**: `Provider.runtime_paths` resolver replaces the checkout's own read of the worker
  configuration; an invalid configuration now links nothing (the Spec's rule) instead of the
  defaults. `execution/checks/checks.py` uses `kernel.tracing.layout.primary_worktree`.
- **Specs touched outside the bound Modules**, only to say where code now lives: Execution's
  runner realization paragraph and Operations' catalog realization paragraph.
- **Round trace v4** implemented as the Spec already defined it (`evidence`, prompt
  `initial`/`repair`, progress phase `validation`). Older round nodes with `checks` are not read
  back by `read_record`; only tests read them (rapid-iteration rule).

## Report 1 to the main agent (concorde-a2), 2026-10-02T21:39:42Z

parts-worker-harness delivered: delivery commit e61dd7c4 on concorde/parts-worker-harness (work commit 972c950f). task-validation ready, no blocking findings.

What changed:
- The worker harness now imports the kernel alone; the `worker harness` group of KNOWN_EXCEPTIONS is gone, as are the execution exceptions on worker_harness.* (context.py, checkout.py, operations/admission.py, checks.py) and context.py's spec.grants/repository/repository_base. context.py keeps only spec.errors (spec_cause), left for the execution task.
- Harness API: WorkerRequest takes the grant input (task_type, entries, context_identity only), the caller's instructions, a `modules` label and `round_validation(worktree, round_folder) -> RoundValidation(evidence, repair, failure, violation, unavailable)`. The configuration reader (load/validate_config/worker_choice/check_mapped) takes the declared Operations and worker ids. Audit no longer knows the glossary. Round trace v4 (evidence, prompt initial/repair), progress phase `validation`, as the Spec already said.
- Method: new src/concorde/method/workers.py (realization.method.workers) with the whole standard worker sequence: admission step check_worker_models plus an `operation(...)` helper that every Method Provider definition now uses (admission first; runtime-path resolver for Operations that may run unbound), grant projection, instruction composition (glossary terms and Spec-gap rule moved from the harness brief), round validation (glossary by entry -> configured checks -> step's own validation), the glossary check after the run, absorb. execution/operations/admission.py is deleted; the catalog no longer prepends steps.
- Execution: Provider.runtime_paths resolver; open_checkout links only what it returns (an invalid worker configuration links nothing, per the Spec); checks.py uses kernel.tracing.layout.primary_worktree.
- Contract test tests/concorde/harness/workers/test_grant_input.py: Spec core's grant for every task type, projected by Method (also with writes withheld), satisfies contract.workers.grant-input; task types, read-only task types and levels match the Protocol's; a richer grant is refused with grant_malformed.

My decisions (details in the decision log):
1. A round validation that raises ends the run `failed` with a new code `validation_unavailable` (reason capability), added to launch.md. Before, such a round was silently accepted.
2. The harness refuses a grant with fields beyond the grant input, or for another task type, with grant_malformed.
3. An artifact path in round evidence is a top-level absolute path below the round folder: kept relative in the node, absolute in the returned record (launch.md evidence row says so now).
4. Spec edits outside the bound Modules, only to say where code lives: Execution's runner realization paragraph and the Operations catalog realization paragraph. I also removed the glossary entry from the returned-run-record example in contracts.md, since glossary violations now come from the round validation.

Verification: build --check clean, spec-validation success with no findings, full suite 985 passed / 5 skipped, live smoke run `run understand --modules module.workers` (pi worker) ended ok with grant.json holding only the three grant-input fields and the brief carrying Method's terms and Spec-gap rule. Old v3 round nodes in .concorde/history still read.

Open: nothing for the developer. Note for the issues task running in parallel: I did not touch execution/operations/review_issues.py. Issues resolved: none.

## Answer to report(s) 1 of the task session, 2026-10-02T21:40:24Z

Merge refused with merge_conflict: merging concorde/parts-worker-harness into parts-split conflicts in specs/concorde/execution/operations/module.md, specs/concorde/method/module.md, specs/concorde/method/module.md.json and tests/concorde/development/test_part_dependencies.py (parts-issues merged first: it moved review_issues into src/concorde/method/review_issues.py with realization.method.review-issues, withdrew the method->issues allowance and removed the issues group). Merge the primary branch parts-split into your task branch, resolve the conflicts keeping both tasks' changes (both realizations of Method, both sets of removed exceptions), run build --check, spec-validation and the full suite, then task-validation and delivery again, and report.

## Merge of parts-split (2026-10-03, task session)

- The main agent's merge failed with merge_conflict after parts-issues merged. Merged parts-split
  into concorde/parts-worker-harness, keeping both tasks: both Method realizations
  (`realization.method.workers`, `realization.method.review-issues`) and both Code paragraphs; the
  Operations catalog paragraph now names only `provider.py` as Method's code still there; both the
  `issues` and the `worker harness` groups of KNOWN_EXCEPTIONS are removed. build --check clean,
  spec-validation success, full suite 991 passed / 5 skipped.

## Report 2 to the main agent (concorde-a2), 2026-10-02T21:47:06Z

Report 2 (answers report 1's merge_conflict): parts-worker-harness delivered again: delivery commit 5ebbf191 on concorde/parts-worker-harness, after merging parts-split (merge commit 43c17c5f). Resolution keeps both tasks: Method's metadata defines both realization.method.workers and realization.method.review-issues and its Code section describes both; the Operations catalog paragraph now names only provider.py as Method code still in execution/operations (admission and review_issues are Method's own); KNOWN_EXCEPTIONS has neither the issues nor the worker harness group. Verified on the merge: build --check clean, spec-validation success with no findings, full suite 991 passed / 5 skipped, task-validation ready. Nothing open; no new decisions beyond the resolution, which is in the decision log.

## Closed: merged, 2026-10-02T21:47:15Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 5ebbf191e8ee6464af487bc323630aacc8769c6f into parts-split and closed it as merged. Nobody answers a report after that.
