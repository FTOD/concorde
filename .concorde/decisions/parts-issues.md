# Decision log: parts-issues

Goal: Make the issues part depend on the kernel alone, with Spec core's registry and Tasks' unfinished merges as optional integrations through their formats, and move the reviews' Issue reporting into Method as an optional integration through the issues command

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

### What this task does (issues)

Read `specs/concorde/issues/` (module "Uses" of Spec core and Tasks as optional integrations,
requirements on owners and on unfinished merges, interface) first.

- **The issues part depends on the kernel alone.** Remove the `issues` group of `KNOWN_EXCEPTIONS`
  (`issues/command.py -> spec.repository`, `issues/store.py -> coordination.tasks.store`,
  `issues/store.py -> spec.repository`): use the kernel's library for digests, locks and the like.
- **Spec core's registry as an optional integration**, as the Issues Spec states: where the spec
  part is installed, owners are checked against the primary worktree's registry, a `null` owner falls
  to the root, the context digest is the registry's and the store check fails an open Issue with an
  unregistered owner; where it is not, a Module is a plain label (a `null` owner refused with
  `no_reporting_module`). Reach the registry through its format (Spec core defines the registry
  mirror) or the spec part's command, never by importing Spec core; record which and why.
- **Tasks' unfinished merges as an optional integration**: the store refuses writes with
  `merge_incomplete` while a task's merge is unfinished only where the coordination part is
  installed, learning it through Tasks' published format (the task records' `merging` state) or a
  coordination command, never by importing Tasks; the merge itself, which holds the merge lock and
  closes the Issues its task resolved, must still be able to write (today it calls the store
  in-process; the coordination task will switch it to the issues command with the lock handed on,
  so keep or provide what that needs, e.g. a way for a command run under a handed-on merge lock to
  write).
- **Reviews report Issues through the issues command.** `execution/operations/review_issues.py`
  is Method's work (the review Operations use it): move it into `src/concorde/method/` and make it
  reach Issues only through the issues command (`concorde issues report|list|show|close ...`, JSON),
  skipping with a statement naming the missing part when the issues part is absent, in which case
  the findings stay in the run result (`req.method.issues-optional` and the review Modules' text).
  Remove its two `execution` exceptions and withdraw the test's `method -> issues` allowance.
- Leave Coordination's own imports of Issues (`coordination/tasks/*.py -> issues.*`) to the
  coordination task, but do not break them.

Bound Modules: Issues, and Method's review Modules where `review_issues` lands. The worker harness
task runs in parallel on `worker_harness/`, `execution/context.py`, `execution/operations/admission.py`
and Method's Operations' worker launch calls; if your changes meet theirs in one file, keep yours
minimal there.

## Task session decisions (2026-10-03)

1. **Spec core's registry reached through its format.** The issues part reads the registry mirror
   `.concorde/specs.json` (Spec core's published format) directly, never the spec part's code or
   command: reading one JSON file needs no process, and the file itself tells whether the spec part
   is installed. Rule: the spec part counts as installed for a worktree exactly when its
   `.concorde/specs.json` exists; an existing file that does not read is still
   `unreadable_registry`. Without it a Module is a plain label, a `null` owner is refused with
   `no_reporting_module` naming the missing spec part, the context digest is that of no bytes, and
   `check` judges no owner and adds one note naming the missing spec part
   (req.concorde.absent-part-stated).
2. **Tasks' unfinished merges reached through its format.** The store reads Tasks' task records
   (`.concorde/tasks/*/task.json`, contract.tasks.task-record: `state` and `merging`) itself and
   builds `merge_incomplete`'s account of the merge from `merging` (task, process, start, checked
   commit, branch, commit before, merge commit, where HEAD is now, `--resume`/`--abort`). No
   `.concorde/tasks/` folder means the coordination part is absent and no write waits. A task
   record that does not read as JSON is skipped: it cannot be told `merging`, and blocking every
   Issue write on another part's unreadable record would make Issues fail for that part.
3. **Primary worktree found through Git** (Kernel's `layout.primary_worktree` and
   `git rev-parse --show-toplevel`), no longer through Tasks.
4. **`IssueError` becomes Issues' own exception**, no longer a subclass of Spec tooling's
   `SpecError`, keeping the same interface (code, message, path, field, reason, remediation, causes,
   `where()`).
5. **Merges writing under a handed-on lock need nothing new.** The Kernel's `merge_lock` already
   adopts a merge lock handed on through `CONCORDE_INHERITED_LOCKS`, so a `concorde issues close`
   started by a merge holding the lock writes without waiting; the library's `locked=True` stays for
   in-process callers until the coordination task switches.
6. **Operations report through the command with their own provenance.** The bookkeeping command
   gains `report --file <report.json> --provenance <provenance.json>`: the report is recorded with
   the provenance its caller vouches for, exactly as the store's library `report_issue` does today
   (form checked; owner and evidence not checked against the primary worktree, since a review may
   report on a Module its task adds and on a deleted changed path). This is the only way a part
   that may not import Issues can keep an Operation's provenance; `--task` is refused beside it.
7. **Method reaches Issues only through `concorde issues`** (`list`, `show`, `report`), run as the
   started worktree's own `concorde` (Workflows' `concorde_command`, which Method may import), JSON
   in and out; `review_issues` moves to `src/concorde/method/review_issues.py` and the review
   modules stop importing `issues.*` (tiers and severities become Method's own constants of the
   report contract). The issues part counts as absent when `concorde` refuses `issues` as a command
   it does not offer: today argparse's `invalid choice: 'issues'`; once Distribution's dispatcher
   exists, its absent-part refusal (assumed code `part_not_installed`; the distribution task should
   align it). Absent: no earlier Issues (`earlier_issues` null), findings keep `issue` null, the
   summary states the findings were not recorded as Issues because the issues part is not installed.
8. **Where the moved code is bound.** `src/concorde/method/review_issues.py` is bound by a new
   realization of Method itself, `realization.method.review-issues` (the review Modules' code is
   in their own folders; this file is shared by Spec review and Code review). Operations' catalog
   text no longer lists `review_issues.py`. Tiers and severities that Method needs are Method's own
   constants of the report contract.
9. **Spec changes in this task.** Issues: the module, interface, requirements and scenarios say how
   each optional integration is reached and told installed (registry file; task records, now a
   declared reliance on `contract.tasks.record`), `report --provenance`, the check's note without
   the spec part, and that `IssueError` and the Kernel's error replace Spec tooling's types. Method:
   the root, Spec review and Code review say Issues are reached only through `concorde issues`;
   new scenarios `scenario.code-review.without-issues` and `scenario.spec-review.without-issues`,
   and Issues' `command-report-provenance`, `command-without-spec-part` and
   `store-without-coordination`, each verified by a test.
10. **Not ok result seen:** one full-suite run failed
    `tests/concorde/e2e/test_owners.py::OwnersCaseTests::test_a_run_refused_for_a_busy_workspace_stops_the_case_with_an_error`
    ("phase unowned" not in a `workspace_busy` detail naming phase owned-by-claude); it passed 3/3
    alone and touches no Issues or review code: a load-dependent flake of the e2e owners case.
- Recorded the e2e owners flake as Issue I-566e82f14dd05300856042bc9472f58b (module.e2e, decision-needed, low).

## Report 1 to the main agent (concorde-a2), 2026-10-02T21:37:21Z

parts-issues delivered: delivery commit 1a59e1d75b2a on concorde/parts-issues (work commit 0a8c9e4e). task-validation ready (14 checks passed); build --check, spec-validation ok; full suite 988 passed, 5 skipped.

Done:
- The issues part imports only the kernel. The `issues` group of KNOWN_EXCEPTIONS is removed, and so are the two `execution/operations/review_issues.py` exceptions. The test's `method -> issues` allowance is withdrawn (OPTIONAL_INTEGRATIONS is now empty).
- Spec core is reached through its registry file. The spec part counts as installed exactly when `.concorde/specs.json` exists, and one that does not read is `unreadable_registry`. Without it, an owner is a plain label, a null owner is refused with `no_reporting_module` (the message names the missing spec part), the context digest is that of no bytes, and `check` judges no owner and adds one note naming the missing spec part.
- Tasks is reached through the task record format. The store reads `.concorde/tasks/*/task.json` for state `merging` and builds `merge_incomplete`'s account from `merging`. With no tasks folder, no write waits. An unreadable record is passed over. The primary worktree is found via Git (the Kernel's `layout.primary_worktree`).
- `IssueError` is Issues' own (a ValueError with code/reason/remediation/where/record), no longer a SpecError.
- New command option `concorde issues report --file F --provenance P`. It records the provenance the caller vouches for, as the store's library does, and checks neither the owner against the primary registry nor the evidence: a review may report on a Module its task adds or on a deleted changed path. `--task` and `--check` are refused beside it.
- Method's `review_issues` moved to `src/concorde/method/review_issues.py`, bound by the new `realization.method.review-issues`. It reaches Issues only through `concorde issues list|show|report --provenance`, run as the started worktree's own `concorde`. When `concorde` does not offer `issues`, the reviews read no earlier Issues (`earlier_issues` null), findings keep `issue` null, the verdict comes from the findings, and the summary says the findings were not recorded as Issues.
- Merges under a handed-on lock: nothing new was needed. The Kernel's `merge_lock` already adopts a lock passed via CONCORDE_INHERITED_LOCKS, and `dispose(..., locked=True)` stays for the in-process caller until the coordination task switches. Coordination's imports of Issues still work.
- Specs updated: Issues module, interface, requirements and scenarios; Method root, Spec review and Code review. New scenarios (each verified by a test): issues command-report-provenance, command-without-spec-part, store-without-coordination; code-review.without-issues; spec-review.without-issues.

Decisions for the coordination/distribution tasks (details in the decision log, items 1-10):
- Method treats the issues part as absent on argparse's `invalid choice: 'issues'` or on an error link with code `part_not_installed`. That code is my assumption for Distribution's absent-part refusal, which no Spec names yet. The distribution task should adopt or rename it.

Issues: none resolved. Recorded I-566e82f14dd05300856042bc9472f58b (module.e2e, decision-needed, low): `tests/concorde/e2e/test_owners.py` busy-workspace test failed once under full-suite load and passed 3/3 alone. It is unrelated to this task.

Nothing open needs the developer.

## Closed: merged, 2026-10-02T21:37:36Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 1a59e1d75b2a1b859a8beda456de72da863126e1 into parts-split and closed it as merged. Nobody answers a report after that.
