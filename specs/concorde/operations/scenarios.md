# Operations scenarios

Concrete situations that show the [requirements](requirements.md) of [Operations](module.md). The
envelope is defined in the [contracts](contracts.md) and the runner in
[How the host runs an Operation](host.md).

## Worker-backed runs

### scenario.operations.worker-ok — A worker-backed run succeeds

- GIVEN an active task bound to `module.issues`
- WHEN the main agent runs `concorde run implement --task severity`
- THEN the host computes the implement grant from the task worktree's Specs and launches one worker through Workers
- AND the audit is clean and every configured check passes
- AND the result has status `ok`, the worker's result in `worker` and the grant, audit and checks in `host_evidence`
- AND the result is printed, saved in the run directory and the run is finished as `ok` in the task record
- AND the command exits with status 0

### scenario.operations.worker-model — A worker runs on the main session's program with the worktree's model

- GIVEN a Claude Code main session and a task worktree whose worker model configuration sets a Claude Code default model and level and an entry for the `implement` Operation with a model only
- WHEN the main agent runs `concorde run implement` for the task
- THEN the host launches `claude -p` with the Operation's model and the default's level as `--effort`
- AND the run record and the result's `worker-model` host evidence name the backend, the worker role, the model and the level
- BUT a change made afterwards to the primary worktree's configuration does not change what the task's next worker runs on

### scenario.operations.worker-model-unavailable — A run with no known main session program fails before launch

- GIVEN a task, and a `concorde run implement` started outside any Claude Code or pi session with `CONCORDE_CLIENT` unset, or a task worktree whose worker model configuration is not valid JSON
- WHEN the host reaches the worker step
- THEN no worker starts and the result is `failed` with `worker_model_unavailable`
- AND its cause is the `component` link of Workers' model configuration with `client_unknown` or `config_invalid`, naming the variables looked at or the file

### scenario.operations.progress-file — A run shows its progress

- GIVEN a worker-backed Operation run
- WHEN it runs and finishes
- THEN its `status.json` names the Operation, task, current step and host process while it runs
- AND once finished it holds the result's status and summary
- AND the worker run it launched records the same host process in its own progress file

### scenario.operations.worker-blocked — A blocked worker escalates

- GIVEN a worker that returns status `blocked` because the Spec lacks a promise
- WHEN its Operation ends
- THEN the result has status `blocked`
- AND its error is a chain of the Operation's link, the Workers harness's link and the worker's own link with its detail, options and recommendation unchanged
- AND the Operation's link gives `decision` as its reason and offers the worker's options
- AND the worker's statements appear only in `worker` and in the worker's link, never in `host_evidence`
- AND the command exits with status 1

### scenario.operations.checks-exhausted — Checks still failing after the last round

- GIVEN a worker whose change leaves a configured check failing after every resume round
- WHEN the rounds are used up
- THEN the result has status `failed` even though the worker reported `ok`
- AND its host evidence names the check, its exit code, its log and the rounds used
- AND its error chain runs from the Operation's link (`decision`) through the Workers harness's link (`exhausted`) to the check's link with its exit code and the end of its log

### scenario.operations.spec-error — A Spec tooling error keeps its reason and causes

- GIVEN a run whose grant Spec core refuses with its own error, which has a cause
- WHEN the Operation ends
- THEN the Operation's link has that error as a `component` cause with its code and message
- AND the cause's explanation is the error's reason, its option is the error's remediation, and the error's own cause is nested below it

### scenario.operations.audit-violation — A write outside the grant fails the run

- GIVEN a worker that changed a file outside its grant's writable paths
- WHEN the host audits the task worktree
- THEN the result has status `failed` with the violation as `audit` evidence
- AND its error's top link gives `permission` as the reason and names the file
- AND no configured check is run for that worker

## Runs without a task

### scenario.operations.no-task — A reading Operation runs without a task

- GIVEN a primary worktree with `module.a` and an open task `t1`
- WHEN the main agent runs `concorde run spec_review --modules module.a` without `--task`
- THEN the host launches the reviewer on the primary worktree, with the grant computed from its Specs
- AND the result has `task` null, is saved under the primary worktree's `.concorde/runs/`, and no task record changes
- AND a later run without a task may admit it with `--input`
- BUT `concorde run implement` without `--task` is a command-line error, since `implement` needs a task

### scenario.operations.no-task-primary-only — A run without a task is refused in a task worktree

- GIVEN an open task `t1` and its worktree
- WHEN the main agent runs `concorde run spec_review --modules module.a` without `--task` from inside `t1`'s worktree
- THEN no worker starts and the result is `failed` with `task_worktree_without_task`
- AND its detail names `t1`'s worktree and its recommendation is to run again with `--task t1`
- AND `t1`'s task record is unchanged

### scenario.operations.no-task-read-only — A run without a task never launches a writing worker

- GIVEN an Operation whose catalog entry makes the task optional
- WHEN a run of it without a task asks Workers for an `implement` or `specify` worker
- THEN no worker starts and the result is `failed` with `project_scope_write`, its actor naming the run as having no task
- AND an `--input` naming a run of a task is refused with `input_not_admissible`

### scenario.operations.configure-list — configure_workers lists the candidates and every worker's choice

- GIVEN a pi main session and a primary worktree without a worker model configuration
- WHEN the main agent runs `concorde run configure_workers` without a task
- THEN the result is `ok` with `task` null and no worker run
- AND its output lists the models pi offers, and for every Operation that launches workers each worker role with its effective model and level, `spec_review` with `reviewer` and `checker`
- AND no configuration file is written

### scenario.operations.configure-change — A change reaches only the named worktree

- GIVEN a primary worktree and an open task `t1` whose worktree has no worker model configuration
- WHEN `configure_workers` sets a default model and level, then a model and level for `spec_review`'s `checker`, without a task
- THEN the primary worktree's file holds both, the checker resolves its own entry and the reviewer the default
- AND `t1`'s worktree has no file until `configure_workers --task t1` sets a model there, which changes only that copy
- AND `--unset` of the checker's entry leaves only the default

### scenario.operations.configure-refused — A refused change leaves the file alone

- GIVEN a primary worktree
- WHEN `configure_workers` names an Operation that launches no worker, a role the Operation does not have, a model the program does not list, or runs outside any main session
- THEN the result is `failed` with `invalid_request` naming the admitted Operations or roles, or `configuration_refused` whose cause is Workers' `unknown_model` or `client_unknown` link
- AND the configuration file is unchanged

## Deterministic runs and refusals

### scenario.operations.deterministic — A deterministic Operation launches no worker

- GIVEN an active task
- WHEN the main agent runs `concorde run validate --task severity`
- THEN no worker is launched
- AND the result has `worker` null, an empty `worker_runs` and Validation's readiness as `output`

### scenario.operations.refused-task — A task that cannot accept a run

- GIVEN a task that is unknown, closed, failed or already running an Operation
- WHEN the main agent runs an Operation for it
- THEN no provider step runs
- AND the result has status `failed`, `refused` evidence with the reason and an error whose cause is the Tasks refusal, naming the known tasks or the running Operation
- AND the task record gains no run

### scenario.operations.bad-command — A malformed command line

- GIVEN a command line with an unknown Operation name or without `--task`
- WHEN `concorde run` is invoked
- THEN it exits with status 2
- AND standard error names what is wrong, such as the unknown Operation or the missing argument
- AND no result and no run directory are written

### scenario.operations.host-error — A host step raises an error

- GIVEN a provider step that raises an unexpected error
- WHEN the runner executes it
- THEN the result has status `failed` with `host-error` evidence naming the step and the error
- AND the cause of its error is a `component` link with the exception's type, message and output, where it was raised and the traceback's path
- AND the run is finished as `failed` in the task record

### scenario.operations.detached — A run started detached

- GIVEN an active task `severity`
- WHEN the main agent runs `concorde run implement --task severity --detach`
- THEN the command prints the run identity and the path of its future result and exits with status 0 while the host keeps running
- AND the run's progress file exists when the command exits
- AND the host writes the same result, run record and task record entry as a run started without `--detach`
- BUT a task already running an Operation still gets a `failed` result naming the refusal, written where the printed path says

### scenario.operations.cancelled — The run is cancelled

- GIVEN a run whose worker is still working
- WHEN the host receives `SIGTERM`
- THEN every worker process it started is ended
- AND the result has status `failed` with `cancelled` evidence and is written and printed

### scenario.operations.inputs — An earlier result is admitted as task material

- GIVEN an `understand` run of the same task that ended `ok` with a plan
- WHEN the main agent runs `implement` with `--input` naming that run
- THEN the plan is admitted as task material for the worker's brief
- BUT a run of another task, or one that did not end `ok`, is refused with `input_not_admissible`
