# Execution scenarios

Concrete situations that show the [requirements](requirements.md) of [Execution](module.md). The
[run result](../glossary.json#concept.run-result) and the binding are defined in the
[contracts](contracts.md) and the runner in [How a run is executed](runner.md).

## Bound and unbound runs

### scenario.execution.bound-run — A run works on the workspace its worktree binds

- GIVEN a task worktree whose binding names the workspace `severity`, the [Module](../glossary.json#concept.module) `module.issues`, its branch and base commit and the primary worktree's `.concorde` as its records directory
- WHEN the task level runs `concorde run implement --goal "…"` in that worktree
- THEN the run works on `module.issues` with the grant computed from that worktree's Specs
- AND its result names the workspace `severity` and is saved under the primary worktree's `.concorde/runs/`
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
- THEN the reviewer runs in an [unbound checkout](../glossary.json#concept.unbound-checkout) of the primary worktree's `HEAD`, with the grant computed from its Specs
- AND the result has `workspace` null, names that `HEAD` as `commit` and is saved under the primary worktree's `.concorde/runs/`
- AND a later [unbound run](../glossary.json#concept.unbound-run) may admit it with `--input`
- BUT an `--input` naming a run of a workspace is refused with `input_not_admissible`

### scenario.execution.unbound-checkout — A merge during an unbound run changes nothing it examines

- GIVEN a primary worktree at commit `C` with an uncommitted change, a `.venv` Git ignores and a submodule it has checked out sparsely
- WHEN an unbound `understand` run is started there and a main session commits a merge in the primary worktree while its worker works
- THEN the run's steps and worker work in a detached checkout of `C` in a private temporary directory, reading `C`'s files without the uncommitted change, the primary worktree's `.venv` through a link, and the submodule with the same sparse patterns
- AND the worker's audit of the checkout is clean, and its model is the one the primary worktree's [worker model configuration](../glossary.json#concept.worker-model-configuration) chooses
- AND the result is `ok`, names `C` as `commit`, has `checkout` evidence and is saved in the primary worktree's run store
- AND the checkout and its temporary directory are gone once the result is written, also when a step raised an error, and the primary worktree keeps its uncommitted change, its `.venv` and the merge
- BUT in a worktree whose `HEAD` names no commit the run is refused with `checkout_unavailable`, reason `environment`, and leaves nothing behind

### scenario.execution.unbound-read-only — An unbound run never launches a writing worker

- GIVEN an [Operation](../glossary.json#concept.operation) that allows unbound runs
- WHEN an unbound run of it asks for a `specify`, `implement` or `code-to-spec` worker without withholding every writable level of its grant
- THEN no worker starts and the result is `failed` with `unbound_write`, the refusal [How an Operation runs its workers](operations/workers.md) defines, its actor naming the run as unbound

### scenario.execution.command-run — An execution command is a run without a worker

- GIVEN a bound workspace
- WHEN the task level runs `concorde task-validation` there
- THEN the result has `kind` `command`, `worker` null, an empty `worker_runs` and Validation's readiness as `output`
- AND it is recorded in the [run store](../glossary.json#concept.run-store) like any Operation run, so a later `delivery` or [workflow step](../glossary.json#concept.workflow-step) can find it
- BUT `concorde run task-validation` is a command-line error naming `concorde task-validation`

## One run at a time

### scenario.execution.workspace-busy — A busy workspace refuses a second run

- GIVEN a bound workspace whose lock a running `implement` run holds
- WHEN a second run is started in the same workspace
- THEN no step of the second run runs and its result is `failed` with `refused` evidence naming `workspace_busy` and the run holding the lock
- AND its error gives `decision` as the reason, with the options to wait for the running run or cancel it
- AND once the first run has ended, a new run is admitted and finds the first run's result already written, since a run writes its result before it releases the lock

### scenario.execution.removed-module — A Module the workspace removed is left out

- GIVEN a binding that names `module.a` and a Module the workspace has since removed or renamed
- WHEN a run is started without `--modules`
- THEN the run works on `module.a` only, and the result lists `module.a` as its Modules
- AND the result has `removed-module` evidence naming the removed Module
- AND the binding still names both Modules

### scenario.execution.modules-removed — A binding whose Modules were all removed

- GIVEN a binding whose Modules the workspace has all removed or renamed
- WHEN a run is started without `--modules`
- THEN it is refused with `modules_removed`, naming them and `--modules`
- AND the same run naming the current Modules with `--modules` proceeds

## Command lines, detaching and failures

### scenario.execution.bad-command — A malformed command line

- GIVEN a command line with an unknown Operation name, an unknown argument, or a directory outside every Git worktree
- WHEN `concorde run` or an [execution command](../glossary.json#concept.execution-command) is invoked
- THEN it exits with status 2
- AND standard error names what is wrong, such as the unknown Operation or argument
- AND no result is written and no run's directory is created

### scenario.execution.progress-file — A run shows its progress

- GIVEN a worker-backed Operation run
- WHEN it runs and finishes
- THEN its `status.json` names the kind, the Operation, the workspace, the current step and the runner process while it runs
- AND once finished it holds the result's status and summary
- AND the worker run it launched records the same runner process in its own [progress file](../glossary.json#concept.progress-file)

### scenario.execution.host-error — A step raises an error

- GIVEN a step that raises an unexpected error
- WHEN the runner executes it
- THEN the result has status `failed` with `host-error` evidence naming the step and the error
- AND the cause of its error is a `component` link with the exception's type, message and output, where it was raised and the traceback's path

### scenario.execution.detached — A run started detached

- GIVEN a bound workspace `severity`
- WHEN the task level runs `concorde run implement --detach` there
- THEN the command prints the run identity and the path of its future result and exits with status 0 while the runner keeps running
- AND the run's [run progress file](../glossary.json#concept.run-progress-file) exists when the command exits
- AND the runner writes the same result and [run record](../glossary.json#concept.run-record) as a run started without `--detach`
- BUT a workspace already running something still gets a `failed` result naming the refusal, written where the printed path says

### scenario.execution.cancelled — The run is cancelled

- GIVEN a run whose worker is still working
- WHEN the runner receives `SIGTERM`
- THEN every worker process it started is ended
- AND the result has status `failed` with `cancelled` evidence and is written and printed
- AND the result's `worker_runs` and its `cancelled` link name the worker run, whose record ends `interrupted` and whose progress file is `finished`

### scenario.execution.inputs — An earlier result is admitted as material of the run

- GIVEN an `understand` run of the same workspace that ended `ok` with a plan
- WHEN `implement` is run with `--input` naming that run
- THEN the plan is admitted, with the name of the run that produced it, as material for the worker's brief
- BUT a run of another workspace, or one that did not end `ok`, is refused with `input_not_admissible`
