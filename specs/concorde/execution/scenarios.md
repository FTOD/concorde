# Execution scenarios

Concrete situations that show the [requirements](requirements.md) of [Execution](module.md). The
[run result](../glossary.json#concept.run-result) is defined in the [contracts](contracts.md), the
binding in the [Kernel's](../kernel/contracts.md#contract.kernel.workspace-binding) and the runner in
[How a run is executed](runner.md). The runs they start are of Method's Operations and commands,
which every Concorde installation of the method part registers.

## Bound and unbound runs

### scenario.execution.bound-run — A run works on the workspace its worktree binds

- GIVEN a task worktree whose binding names the workspace `severity`, the [Module](../glossary.json#concept.module) `module.issues`, its branch and base commit, the workspace folder `.concorde/tasks/severity/workspace/` of the primary worktree and that worktree's `.concorde`
- WHEN the task level runs `concorde run implement --goal "…"` in that worktree
- THEN the run works on `module.issues`, its steps computing the grant from that worktree's Specs
- AND its result names the workspace `severity` and is saved in its [trace node](../glossary.json#concept.trace-node) `runs/<run-id>/` of that workspace folder, whose `trace.json` names the workspace, the Module and the [Operation](../glossary.json#concept.operation)
- AND its run lock and the [workspace lock](../glossary.json#concept.workspace-lock) are files under the primary worktree's `.concorde/locks/`
- AND neither the binding nor any [task record](../glossary.json#concept.task-record) changes

### scenario.execution.binding-refused — A broken or copied binding is refused

- GIVEN a worktree whose `.concorde/workspace.json` is not valid JSON, breaks the binding contract, or names another worktree as its root
- WHEN a run is started there
- THEN no step runs and the result is `failed` with `refused` evidence naming `binding_unreadable`, `binding_invalid` or `binding_misplaced`
- AND the cause of its error is the `Execution (workspace binding)` link with that code and the file's path

### scenario.execution.binding-required — A run that needs a workspace is refused unbound

- GIVEN a worktree without a binding, such as the primary worktree
- WHEN the task level runs `concorde run implement` or `concorde delivery` there
- THEN no step runs and the result is `failed` with `workspace` null and `refused` evidence naming `binding_required`
- AND its options say to run it in a bound workspace such as a task worktree

### scenario.execution.unbound-run — A reading Operation runs unbound

- GIVEN a primary worktree with `module.a`
- WHEN the [main agent](../glossary.json#concept.main-agent) runs `concorde run spec_review --modules module.a` there
- THEN the reviewer runs in an [unbound checkout](../glossary.json#concept.unbound-checkout) of the primary worktree's `HEAD`, with the grant its steps compute from that checkout's Specs
- AND the result has `workspace` null, names that `HEAD` as `commit` and is saved in the trace node `.concorde/unbound/<run-id>/` of the primary worktree
- AND a later [unbound run](../glossary.json#concept.unbound-run) may admit it with `--input`

### scenario.execution.unbound-bound-input-refused — An unbound run refuses the output of a bound run

- GIVEN a primary worktree with `module.a` and a run of a task's workspace that ended `ok`
- WHEN the main agent runs `concorde run spec_review --modules module.a --input <that run>` in the primary worktree
- THEN the run is refused with `input_not_admissible` before any step, its error naming the run as one of that workspace, not of no workspace

### scenario.execution.unbound-checkout — A merge during an unbound run changes nothing it examines

- GIVEN a primary worktree at commit `C` with an uncommitted change, a `.venv` Git ignores and a submodule it has checked out sparsely
- WHEN an unbound `understand` run is started there and a main session commits a merge in the primary worktree while its worker works
- THEN the run's steps and worker work in a detached checkout of `C`, `.claude/worktrees/unbound-<run-id>` of the primary worktree, reading `C`'s files without the uncommitted change, the primary worktree's `.venv` through a link, and the submodule with the same sparse patterns
- AND the worker's audit of the checkout is clean, and its model is the one `C`'s committed [worker configuration](../glossary.json#concept.worker-configuration) chooses, not an uncommitted change of it
- AND the result is `ok`, names `C` as `commit`, has `checkout` evidence and is saved in the primary worktree's `.concorde/unbound/`
- AND the checkout is gone once the result is written, and the primary worktree keeps its uncommitted change, its `.venv` and the merge

### scenario.execution.unbound-checkout-removed — The checkout is removed when a step raises

- GIVEN a primary worktree at commit `C` and a task worktree registered in its repository
- WHEN a step of an unbound run started there raises an error
- THEN the result is `failed` with `host_error`, names `C` as `commit` and has `checkout` evidence
- AND the checkout is gone once the result is written, and the repository lists exactly the worktrees it listed before the run, the task worktree among them

### scenario.execution.unbound-no-commit — A worktree without a commit refuses an unbound run

- GIVEN a worktree whose `HEAD` names no commit
- WHEN an unbound run is started there
- THEN the run is refused with `checkout_unavailable`, reason `environment`, before any step or worker
- AND the result names no `commit` and is saved in the worktree's `.concorde/unbound/`

### scenario.execution.unbound-not-ignored — A primary worktree that does not ignore its worktrees refuses an unbound run

- GIVEN a primary worktree with a commit whose Git does not ignore `.claude/worktrees/`
- WHEN an unbound run is started there
- THEN the run is refused with `checkout_unavailable`, its cause naming the path Git does not ignore
- AND no `.claude/` directory is created and the repository lists no worktree but its own

### scenario.execution.command-run — An execution command is a run without a worker

- GIVEN a bound workspace
- WHEN the task level runs `concorde task-validation` there
- THEN the result has `kind` `command`, `worker` null, an empty `worker_runs` and Validation's readiness as `output`
- AND it is recorded in the [run store](../glossary.json#concept.run-store) like any Operation run, so a later [workflow step](../glossary.json#concept.workflow-step) or the task level can find it
- BUT `concorde run task-validation` is a command-line error naming `concorde task-validation`

## One run at a time

### scenario.execution.workspace-busy — A busy workspace refuses a second run

- GIVEN a bound workspace whose lock a running `implement` run holds
- WHEN a second run is started in the same workspace
- THEN no step of the second run runs and its result is `failed` with `refused` evidence naming `workspace_busy` and the run holding the lock
- AND its error gives `decision` as the reason, with the options to wait for the running run or cancel it
- AND once the first run has ended, a new run is admitted and finds the first run's result already written, since a run writes its result before it releases the lock

### scenario.execution.workspace-wait — A run started with --wait queues behind the running one

- GIVEN a bound workspace whose lock a running `implement` run holds
- WHEN `concorde delivery --wait 600` is started in the same workspace
- THEN its run progress file shows the step `workspace-lock` and names the `implement` run in `waiting_for`
- AND while it waits, its node, run progress file and, when detached, its runner's output lie in `lobby/<run-id>/` of the binding's `.concorde` and nothing of it lies in the workspace folder
- AND once the `implement` run releases the lock, the delivery's node moves to `runs/<run-id>/` of the workspace folder, and the delivery runs its steps and ends with its own result

### scenario.execution.workspace-wait-timeout — A run whose wait runs out is refused

- GIVEN a bound workspace whose lock a running `implement` run holds for longer than a second
- WHEN `concorde task-validation --wait 0.3` is started in the same workspace
- THEN once the 0.3 seconds have passed with the lock still held, the run is refused with `workspace_busy`, saying how long it waited and offering a longer `--wait <seconds>`
- AND it runs no step, and its node and result stay in `lobby/<run-id>/` of the binding's `.concorde`, nothing of it lying in the workspace folder

### scenario.execution.workspace-wait-merge — A run waiting behind a merge names the merge

- GIVEN a bound workspace whose lock `task merge` of its task holds
- WHEN a run is started there with `--wait 0.3`, and another with `--wait 600`
- THEN the first is refused with `workspace_busy`, its `refused` evidence naming the merge, its process and its task as the lock's holder line describes them
- AND while the second waits, its run progress file shows the step `workspace-lock` and names the merge in `waiting_for`, no run identity
- AND once the merge releases the lock, the second run does its own work

### scenario.execution.workspace-retired — A workspace closed while a run waits for it

- GIVEN a bound workspace whose lock `task close` holds, and a run started there with `--wait 600` that waits for that lock in the lobby
- WHEN the close removes the worktree with its binding, moves the workspace folder to the history and removes the workspace lock file while still holding it, then releases it
- THEN the waiting run is refused with `workspace_retired`, naming the removed lock file, its result and node in `lobby/<run-id>/`, and it runs no step
- AND the history the close moved holds nothing of that run, and nothing of it is written there afterwards
- AND a run whose binding is gone or names another workspace when it takes the lock is refused with `workspace_retired` the same way, naming what changed

### scenario.execution.removed-module — A Module the workspace removed is left out

- GIVEN a binding that names `module.a` and a Module the workspace has since removed or renamed
- WHEN a run of a definition that reads the Specs, as Method's do, is started without `--modules`
- THEN the run works on `module.a` only, and the result lists `module.a` as its Modules
- AND the result has `removed-module` evidence naming the removed Module
- AND the binding still names both Modules

### scenario.execution.modules-as-names — A definition that reads no Spec takes the Modules as names

- GIVEN a definition that admits no Modules itself, such as one of a part that reads no [Spec](../glossary.json#concept.spec)
- WHEN it runs in a bound workspace naming `module.nowhere` with `--modules`, and again without `--modules`
- THEN the runner reads no Spec: the first run works on `module.nowhere` and the second on every Module the binding names, registered or not

### scenario.execution.unknown-module-refused — A definition's admission refuses an unknown Module

- GIVEN a definition that admits its Modules itself through Method's admission, as Method's `implement` does, and a bound workspace whose Specs register `module.a` but not `module.nowhere`
- WHEN it runs there with `--modules module.a,module.nowhere`
- THEN no step runs and the result is `failed` with the runner's `refused` link
- AND the cause of that link is the admission's own `Method (Module admission)` link with the code `unknown_module`, naming `module.nowhere`

### scenario.execution.modules-removed — A binding whose Modules were all removed

- GIVEN a binding whose Modules the workspace has all removed or renamed
- WHEN a run of a definition that reads the Specs is started without `--modules`
- THEN it is refused with `modules_removed`, naming them and `--modules`
- AND the same run naming the current Modules with `--modules` proceeds

## Command lines, detaching and failures

### scenario.execution.bad-command — A malformed command line

- GIVEN a command line with an unknown Operation name, an unknown argument, or a directory outside every Git worktree
- WHEN `concorde run` or an [execution command](../glossary.json#concept.execution-command) is invoked
- THEN it exits with status 2
- AND standard error names what is wrong, such as the unknown Operation or argument
- AND no result is written and no trace node is created

### scenario.execution.progress-file — A run shows its progress

- GIVEN a worker-backed Operation run
- WHEN it runs and finishes
- THEN its `status.json` names the kind, the Operation, the workspace, the current step and the runner process while it runs
- AND once finished it holds the result's status and summary
- AND the worker run it launched records the run's identity in its own [progress file](../glossary.json#concept.progress-file)
- AND the run's [run lock](../glossary.json#concept.run-lock) `locks/runs/<run-id>.lock` is held from before its first `status.json` until after its result, and gone once the runner exited
- AND its `trace.json` says `running` from before its first step, and once finished holds its end, status, duration and each step with its timing

### scenario.execution.run-lock — A dead runner is told by its run lock

- GIVEN a run with a [run progress file](../glossary.json#concept.run-progress-file) still `running` and no result, whose runner ran in another PID namespace and recorded a process identifier that names a living, unrelated process where the run is observed
- WHEN an observer, such as the run state of a task or workflow step or the installer, asks whether it still runs
- THEN it is running only while its [run lock](../glossary.json#concept.run-lock) is held, from whichever PID namespace the observer looks
- AND once the runner ended without writing a result, the run is lost, whatever process now has the recorded identifier

### scenario.execution.host-error — A step raises an error

- GIVEN a step that raises an unexpected error
- WHEN the runner executes it
- THEN the result has status `failed` with `host-error` evidence naming the step and the error
- AND the cause of its error is a `component` link with the exception's type, message and output, where it was raised and the traceback's path

### scenario.execution.admission-error — A definition's admission raises an error

- GIVEN a definition whose admission of the Modules raises an unexpected error, not a refusal
- WHEN a run of it is started
- THEN the run ends with one result of status `failed`, with `host-error` evidence naming the admission and the error, and no step runs

### scenario.execution.detached — A run started detached

- GIVEN a bound workspace `severity`
- WHEN the task level runs `concorde run implement --detach` there
- THEN the command prints the run identity, the path of its future result and its lobby folder and exits with status 0 while the runner keeps running
- AND the run's [run progress file](../glossary.json#concept.run-progress-file) exists when the command exits, in the lobby or, once the run entered its workspace, in its node
- AND the runner writes the same [run result](../glossary.json#concept.run-result) and trace node as a run started without `--detach`, its output `host.out` moving with its node into the workspace folder

### scenario.execution.detached-busy — A detached run of a busy workspace is refused in the lobby

- GIVEN a bound workspace whose lock a running run holds
- WHEN the task level runs `concorde task-validation --detach` there
- THEN the command announces the run with exit status 0, as for a free workspace
- AND the run's `failed` result, naming the `workspace_busy` refusal, is written in the printed lobby folder, where every reader that looks the run up by its identity finds it, and nothing of it lies in the workspace folder

### scenario.execution.detached-namespace — A detached run dies with its PID namespace

- GIVEN a bound workspace whose `task-validation` still runs a while after it started
- WHEN a caller, such as a workflow step, starts it detached from a command run in a PID namespace of its own, as Claude Code's Bash sandbox runs each call, and that command returns once the run is announced
- THEN the runner is killed with the namespace, without a word: the run has no result, nobody holds its run lock and its runner's output is empty
- AND every observer that asks finds the run lost

### scenario.execution.detach-failed — A detached runner that never announces leaves nothing

- GIVEN a bound workspace
- WHEN a run is started with `--detach` and its runner writes no run progress file before it ends or the announcement wait runs out
- THEN the command ends the runner and exits with status 1, printing a `detach_failed` link that says no step ran
- AND nothing of the run remains: no lobby folder, no node, no result and no run lock file

### scenario.execution.run-unrecorded — A run whose first records cannot be created runs no step

- GIVEN a bound workspace whose run store refuses the run's first `trace.json`, such as on a read-only file system
- WHEN a run is started there
- THEN no step runs, no result is written and nothing is printed on standard output
- AND the command exits with status 1, its `run_unrecorded` link on standard error with the `Execution (run store)` link of the refusal as its cause
- AND no run lock is left and the workspace lock is free

### scenario.execution.result-unsaved — A result that cannot be saved is printed and the run is lost

- GIVEN a bound workspace whose run store fails when the run publishes its `result.json`, such as on a full file system
- WHEN a run is started there and its steps end `ok`
- THEN the command still prints the run's result on standard output and exits with status 1, its `result_unsaved` link on standard error with the `Execution (run store)` link of the failed write as its cause
- AND no `result.json` was written, the run's trace node still says `running`, both locks are free and every observer finds the run lost
- AND when only the final `trace.json` fails, the result is published and the trace node, still `running` with nobody holding its run lock, reads as lost

### scenario.execution.result-published-whole — An observer never reads part of a result

- GIVEN a run finishing while an observer, such as a workflow step, reads its `result.json` without holding any lock
- WHEN the runner publishes the result
- THEN the observer finds no `result.json` before the publication and the complete result after it, never part of one
- AND no other file of the publication is left in the run's folder

### scenario.execution.cancelled — The run is cancelled

- GIVEN a run whose worker is still working
- WHEN the runner receives `SIGTERM`
- THEN its running step ends every worker process it started through the worker harness
- AND the result has status `failed` with `cancelled` evidence and is written and printed
- AND the result's `worker_runs` and its `cancelled` link name the worker run, whose record ends `interrupted` and whose progress file is `finished`

### scenario.execution.inputs — An earlier result is admitted as material of the run

- GIVEN an `understand` run of the same workspace that ended `ok` with a plan
- WHEN `implement` is run with `--input` naming that run
- THEN the plan is admitted, with the name of the run that produced it, as material for the worker's brief
- BUT a run of another workspace, or one that did not end `ok`, is refused with `input_not_admissible`
