# Decision log: parts-coordination

Goal: Make the coordination part depend on the kernel alone, with runs, Issues, Spec checks, Method's delivery and Distribution's update mark as optional integrations through commands and formats, and add concorde task deliver for installations without Method

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

Since this context was first written, `parts-issues` merged too (the issues part imports only the
kernel; Method reaches Issues through `concorde issues`; the spec part counts as installed for a
worktree exactly when its `.concorde/specs.json` registry mirror exists; the Issue store reads Tasks'
task records for `merging` itself; `concorde issues report --provenance`). `parts-worker-harness`
runs in parallel with this task (on `worker_harness/`, `execution/` and Method's Operations).

### What this task does (coordination)

Read `specs/concorde/coordination/` (module "Optional integrations" table, Tasks' "Uses" of Kernel,
Tracing, Task sessions, Distribution, Execution, Delivery, Issues and Spec core, `task deliver`,
Merging; Task sessions; Main session) first.

- **The coordination part depends on the kernel alone.** Remove the `coordination` group of
  `KNOWN_EXCEPTIONS` and `coordination/tasks/merge.py -> distribution.install`:
  - *Execution*: read the run store, run results, run progress files and run locks through
    Execution's published formats (Tracing's node and lock contracts, Execution's run-result
    contract), never `execution.runs`; with no run store there are no runs (`task wait --run`
    refused with `part_missing`, a task never active through a run).
  - *Issues*: check the Issues a task resolves, recover Issue leftovers before the merge judges the
    primary worktree clean, and close the resolved Issues after the merge through the issues
    command (`concorde issues show|recover|close ...`, JSON), handing the held merge lock on as
    Tracing describes (the Kernel's `merge_lock` adopts a lock passed via
    `CONCORDE_INHERITED_LOCKS`); without the issues part, `--resolves`/`task resolve` refuse with
    `part_missing` and a merge closes none. Then drop the Issue store's in-process `locked=True`
    path if nothing else uses it.
  - *Spec core*: at `task open` check the Modules against the primary worktree's registry through
    the same rule Issues uses (installed iff `.concorde/specs.json` exists; read the mirror's
    format), else Modules are plain labels; a merge's default check and the check after an
    unvalidated update are `concorde spec-validation` only where the spec part is installed.
  - *Method*: `task deliver <task> [--check ...]` as the Tasks Spec defines it (runs only in the
    task's worktree, runs the given checks, makes the delivery commit by the Kernel's convention,
    traces `delivery`/`delivery-check` nodes), refused with `delivery_by_method` wherever the method
    part is installed; tell Method's presence through the host (whether `concorde delivery` is
    offered; until the distribution task's dispatcher exists, decide a simple, documented test and
    record it so the distribution task can align it).
  - *Distribution*: read the update mark `.concorde/update.json` through its format.
- **Absent-part code.** Coordination's own absent-part refusals use `part_missing` as its Spec says.
  The issues task assumed Distribution's dispatcher would refuse an absent part's command with
  `part_not_installed`; do not change Method's detection here, but record in this log which code you
  used so the distribution task makes one code for both.
- Keep the project MCP server's task tools working (they live in `distribution/project_mcp/` and
  import Tasks; that stays a distribution exception for the distribution task).
- The primary worktree runs this branch's code right after the merge, and its existing task
  records, history and locks must still read. The merge of this very task is done by the new code:
  test `task merge` (with `--check`, Issue closing via the command, `--resume`/`--abort`) and
  `task close` end to end in the suite.

Bound Modules: Coordination, Tasks, Task sessions (Main session only where its guidance or tools must
change).

## Task session decisions (2026-10-03)

1. **How Coordination tells a part is installed.** One rule per kind of reach, recorded in
   `src/concorde/coordination/tasks/parts.py`:
   - *spec*: installed for a worktree exactly when its registry mirror `.concorde/specs.json`
     exists (the rule parts-issues chose); `task open` reads the Modules from the primary
     worktree's mirror (`specs_unloadable` when it exists but does not read), and the merge's
     default check `concorde spec-validation`, and the one an unvalidated update adds, run only
     where it exists. Without it a merge given no `--check` runs none and warns so.
   - *execution, method, issues*: installed exactly when the worktree's own `concorde`
     (`.concorde/bin/concorde`, else `scripts/concorde.py`, else this package's `python -m
     concorde`) offers the command (`run`, `delivery`, `issues`). Absent means the answer is an
     error link whose code is `part_missing` or `part_not_installed`, or the output says
     `invalid choice: '<command>'` (today's dispatcher); any other answer, a refusal of the
     arguments included, means offered. `task deliver` and `task wait --run` ask with
     `concorde <command> --help`; the Issue calls learn it from the call itself.
   - **For the distribution task:** Coordination's own absent-part refusals use `part_missing`
     (as its Spec says); Method's `review_issues` assumed `part_not_installed` for the
     dispatcher's refusal. Coordination accepts both until the distribution task makes them one
     code. Note also that today an unknown top-level word falls to Spec tooling's parser and
     answers exit 3 with `invalid choice: '<word>'` in a JSON message, not exit 2 on stderr as
     `method/review_issues.py::_absent` expects; Coordination matches the text anywhere in the
     output. The distribution task should align Method's check too.
   - When `concorde` cannot be asked at all, `task deliver` and `wait --run` refuse with a new
     code `part_unknown` (environment), and `--resolves`/`resolve` with `issues_unavailable`.
2. **Runs read through Execution's formats** in `coordination/tasks/runs.py` on the Kernel's
   trace reader: the run-id pattern, the lobby folder, progress file, result and run lock. No run
   store means no runs; `store.workspace_store` (which returned Execution's `Store`) is replaced
   by `store.workspace_runs(primary, task, folder)`.
3. **Handing the merge lock to `concorde issues`.** The Kernel's lock library could adopt a
   handed lock but had no way for a holder that took it with `hold` to hand it on. I added
   `kernel.tracing.locks.handed_on(*paths)` (dup of the held descriptor, the
   `CONCORDE_INHERITED_LOCKS` entry and the `pass_fds`; the holder's line is rewritten after,
   since the receiver writes and then empties its own). It implements Tracing's existing "Handing
   a lock on" promise, so no Spec change; it is a small change outside the task's Modules
   (module.tracing), which the goal ("handing the held merge lock on as Tracing describes")
   needs. The merge runs `concorde issues recover` before judging the primary worktree and
   `concorde issues close <id> --reason resolved ...` per resolved Issue with the lock handed on.
4. **Issue store's `locked=True` dropped** (brief: "if nothing else uses it"): `_writing`,
   `report_issue`, `dispose_issue`, `recover_issues`, `archive_issues` and the command's
   `dispose` lose `locked`. Issues' interface, module and the scenario
   `scenario.issues.store-folders-locked` now say a held lock is handed on to `concorde issues`;
   its tests hand the lock on (in-process via `tests/concorde/support/handed_lock.py`, and the
   scenario's test through the real command). These are Spec edits outside the bound Modules that
   the brief's removal requires.
5. **`task deliver`** in `coordination/tasks/deliver.py`, its checks and the merge's sharing
   `coordination/tasks/checks.py`; its trace contents `concorde-delivery-trace` and
   `concorde-delivery-check-trace` (Tracing's kind table already names them) get contracts in
   Tasks' contracts. Its checks run in the task worktree with the caller's environment unchanged
   (the merge's checks put the running package on `PYTHONPATH` because its default check is
   `python -m concorde`; a delivery has no default check).
6. **Module identities are checked for their form at open, with or without the spec part.**
   Writing the test of a coordination-only project showed that a plain label such as `m` passed
   `open` and only failed at the workspace binding (whose contract admits only `module.<name>`),
   after the branch and worktree existed, refused as `binding_failed`. `open` now refuses such a
   label with `invalid_input` before creating anything; Tasks' module text, contracts and the
   scenario `scenario.tasks.coordination-alone` say so.
7. **New scenarios**, each verified by `tests/concorde/tasks/test_deliver.py`:
   `scenario.tasks.deliver`, `deliver-check-failed`, `deliver-recovered`, `deliver-refused` and
   `coordination-alone`. Tests simulate a missing part with a tracked `.concorde/bin/concorde`
   that refuses that part's commands with `part_missing` (`tests/concorde/support/installed_parts.py`)
   and remove the registry mirror for the spec part. `scenario.tasks.merge-issues-unavailable`
   now reads "a project whose `concorde issues` cannot run to an answer", since the merge no
   longer imports Issues.
8. **Left for other tasks:** the project MCP server's task tools (`distribution/project_mcp/`)
   still import Tasks, a distribution exception; they work unchanged. The task-session guidance
   (generated from Main session) still names only Method's `task-validation`/`delivery`; the
   Spec already says a task session delivers with `concorde task deliver` where Method is not
   installed, and composing guidance by installed part is the distribution task's.
9. **Verification:** part-dependency test passes with the `coordination` group and
   `coordination/tasks/merge.py -> distribution.install` removed; `build --check` ok;
   `spec-validation` ok (0 findings); full suite 994 passed, 5 skipped. Smoke runs from this
   worktree: `task show` (active, 0 runs), `task deliver` (refused `delivery_by_method`, Method
   being installed here), `task wait --run <unknown>` (`unknown_run`), `task list`. Commit
   014d0e87.

## Report 1 to the main agent (concorde-a2), 2026-10-02T22:04:30Z

parts-coordination is delivered: delivery commit e3c48dfe on concorde/parts-coordination (work commit 014d0e87). task-validation was ready. build --check and spec-validation pass with 0 findings. Full suite: 994 passed, 5 skipped.

What changed:
- The coordination part now imports only the kernel. I removed the `coordination` group of KNOWN_EXCEPTIONS and `coordination/tasks/merge.py -> distribution.install`. The project MCP server's imports of Tasks remain a distribution exception and work unchanged.
- Execution: runs are read through Execution's formats in coordination/tasks/runs.py, on the Kernel's trace reader (run id, lobby, status.json, result.json, run lock). With no run store there are no runs. `task wait --run` is refused with part_missing where the execution part is absent.
- Spec core: the spec part counts as installed iff `.concorde/specs.json` exists, the same rule Issues uses. `open` reads Modules from that registry mirror, and refuses with specs_unloadable when the file exists but does not read. The merge's default check, and the check added after an unvalidated update, are `spec-validation` only where the spec part is installed. Without it, a merge given no --check runs no check and warns that it ran none.
- Issues go through `concorde issues show|recover|close`, JSON in and out. Recover and close receive the held merge lock through CONCORDE_INHERITED_LOCKS. Without the issues part, --resolves and resolve are refused with part_missing, and a merge closes no Issues and recovers none. The Issue store's `locked=True` path is gone, and the Issues Spec text and tests now say the lock is handed on.
- Distribution's update mark is read through its file.
- New `concorde task deliver <task> [--check ...] [--wait]` (deliver.py, checks.py). It follows the Tasks contract: it refuses with delivery_by_method wherever `concorde delivery` is offered. It also refuses with not_task_worktree, task_closed, wrong_branch and workspace_busy. Checks run in the worktree, and the delivery commit follows the Kernel's convention; a head already delivered is reported as recovered. Each attempt is recorded as nodes deliveries/<n>/ with checks/<i>/ below it. New contracts: contract.tasks.delivery-trace and contract.tasks.delivery-check-trace.

Decisions I made (details in decision log items 1-9):
1. How a part is detected: the execution, method and issues parts are installed iff the worktree's own `concorde` offers `run`, `delivery` or `issues`. Absent means one of: an error link with code part_missing or part_not_installed, or `invalid choice: '<cmd>'` anywhere in the output. Probe: `concorde <cmd> --help`. When concorde cannot be asked at all, the refusal uses the new code part_unknown (and issues_unavailable for --resolves/resolve).
   FOR THE DISTRIBUTION TASK: Coordination refuses with part_missing, while Method's review_issues assumed part_not_installed. Pick one code. Also, today an unknown top-level word answers with exit 3 and a JSON message, not exit 2 on stderr as method/review_issues.py::_absent expects, so Method's absent check never matches today.
2. A change outside my bound Modules, needed by the goal: I added kernel.tracing.locks.handed_on(), which lets a process holding a lock taken with `hold` hand it to a child. This implements Tracing's existing "Handing a lock on" promise, so no Spec change, and it has a test.
3. I edited the Issues Spec (interface, module, scenario store-folders-locked) for the dropped `locked` path, as the brief's removal requires.
4. Defect found and fixed: without a registry, `open` accepted a label like `m`. It then failed at the binding (binding_failed) after the branch and worktree already existed. `open` now refuses a non-`module.<name>` label up front with invalid_input.
5. New scenarios, each with a test: tasks.deliver, deliver-check-failed, deliver-recovered, deliver-refused, coordination-alone. merge-issues-unavailable is reworded for the command.

Still open, nothing needing the developer:
- The generated task-session guidance still names only Method's delivery. Composing guidance per installed part is the distribution task's job.
- The merge of this task by the current primary code is safe: that code runs from a frozen snapshot and still uses in-process Issues. The new code is exercised end to end by the suite (merge with --check, Issue closing via the command, --resume and --abort, close).

Resolves no Issue.

## Closed: merged, 2026-10-02T22:04:53Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit e3c48dfe586893d5970c34f404a056368e6edf26 into parts-split and closed it as merged. Nobody answers a report after that.
