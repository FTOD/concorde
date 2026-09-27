# Operations scenarios

Concrete situations that show the [requirements](requirements.md) of [Operations](module.md). What
every run does, whatever its definition, is shown by the [Execution scenarios](../scenarios.md);
how an Operation runs its workers is in [How an Operation runs its workers](workers.md).

## Worker-backed runs

### scenario.operations.worker-ok — A worker-backed run succeeds

- GIVEN a bound workspace `severity` of `module.issues`
- WHEN the task level runs `concorde run implement` in it
- THEN the run computes the implement grant from the workspace's Specs and launches one worker through Workers
- AND the audit is clean and every configured check passes
- AND the result has status `ok`, the worker's result in `worker` and the grant, audit and checks in `host_evidence`
- AND the result is printed and saved in the run store of the binding's records directory
- AND the command exits with status 0

### scenario.operations.worker-model — A worker runs with the worktree's model for its id

- GIVEN a task worktree whose worker model configuration chooses Claude Code, a default model and a level, and a model for `implement`'s worker `worker`
- WHEN the task level runs `concorde run implement` in the task worktree
- THEN the run launches `claude -p` with the worker's model and the default's level as `--effort`
- AND the run record and the result's `worker-model` host evidence name the backend, the worker id, the model and the level
- BUT a change made afterwards to the primary worktree's configuration does not change what the task's next worker runs on

### scenario.operations.worker-backend-configured — Workers run on pi, whatever the main session

- GIVEN a Claude Code main session, pi installed, and a task worktree whose worker model configuration gives `implement`'s worker a pi model and puts another Operation's worker on Claude Code
- WHEN the task level runs `implement` and then that Operation in the task worktree
- THEN the run launches `implement`'s worker with `pi -p` and that model, under the same grant a Claude Code worker would get, and the run record and `worker-model` evidence name `pi` as Concorde's default worker backend
- AND it launches the other Operation's worker with `claude -p`, naming the entry of its worker id that chose it

### scenario.operations.worker-model-unavailable — A run whose worker backend or model cannot be settled fails before launch

- GIVEN a task whose worktree's worker model configuration is not valid JSON, or chooses nothing on a machine without pi
- WHEN the task level runs `concorde run implement` in the task worktree and the run reaches the worker step
- THEN no worker starts and the result is `failed` with `worker_model_unavailable`
- AND its cause is the `component` link of Workers' model configuration with `config_invalid` or `backend_missing`, naming the file, or that the worker runs on pi as Concorde's default worker backend, the command looked for and how to choose Claude Code for it

### scenario.operations.worker-blocked — A blocked worker escalates

- GIVEN a worker that returns status `blocked` because the Spec lacks a promise
- WHEN its Operation ends
- THEN the result has status `blocked`
- AND its error is a chain of the Operation's link, Workers' link and the worker's own link with its detail, options and recommendation unchanged
- AND the Operation's link gives `decision` as its reason and offers the worker's options
- AND the worker's statements appear only in `worker` and in the worker's link, never in `host_evidence`
- AND the command exits with status 1

### scenario.operations.checks-exhausted — Checks still failing after the last round

- GIVEN a worker whose change leaves a configured check failing after every resume round
- WHEN the rounds are used up
- THEN the result has status `failed` even though the worker reported `ok`
- AND its host evidence names the check, its exit code, its log and the rounds used
- AND its error chain runs from the Operation's link (`decision`) through Workers' link (`exhausted`) to the check's link with its exit code and the end of its log

### scenario.operations.spec-error — A Spec tooling error keeps its reason and causes

- GIVEN a run whose grant Spec core refuses with its own error, which has a cause
- WHEN the Operation ends
- THEN the Operation's link has that error as a `component` cause with its code and message
- AND the cause's explanation is the error's reason, its option is the error's remediation, and the error's own cause is nested below it

### scenario.operations.audit-violation — A write outside the grant fails the run

- GIVEN a worker that changed a file outside its grant's writable paths
- WHEN the run audits the workspace
- THEN the result has status `failed` with the violation as `audit` evidence
- AND its error's top link gives `permission` as the reason and names the file
- AND no configured check is run for that worker
