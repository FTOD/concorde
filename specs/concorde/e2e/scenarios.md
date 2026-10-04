# End-to-end testing scenarios

Concrete situations that show the [requirements](requirements.md) of
[End-to-end testing](module.md).

### scenario.e2e.repositories — SWE-bench's repositories are listed

- GIVEN a checkout with `references/swe-bench/` checked out
- WHEN the developer lists the repositories
- THEN the list names SWE-bench's Python repositories, among them `psf/requests` and `pallets/flask`

### scenario.e2e.unknown-repository — A repository SWE-bench does not name is refused

- GIVEN a checkout with `references/swe-bench/` checked out
- WHEN the developer prepares a repository not on the list without `--any`
- THEN preparation is refused with `unknown_repository` naming the known ones

### scenario.e2e.worker-model — A test project runs every worker on the model given

- GIVEN a [model map](../glossary.json#concept.model-map) that gives the project model name `fast` an id for every worker's program
- WHEN the developer prepares a test project with `--worker-model fast`
- THEN the project's committed `.concorde/workers.json` enables `fast` alone and chooses it as the default of every worker
- AND the result names `fast` as the enabled model

### scenario.e2e.copied-configuration — A test project takes this checkout's worker configuration

- GIVEN this checkout's own `.concorde/workers.json` and a model map that resolves every model it names
- WHEN the developer prepares a test project without `--worker-model`
- THEN the project's committed `.concorde/workers.json` holds this checkout's enabled models, defaults, [Operation](../glossary.json#concept.operation) entries and limits, without its `runtime` paths
- AND the result names the enabled models

### scenario.e2e.unmapped-model — A model the model map cannot resolve is refused

- GIVEN a model map that gives the project model name `unmapped` no id for a worker's program
- WHEN the developer prepares a test project with `--worker-model unmapped`
- THEN preparation is refused with `model_unmapped`, naming the entry the map lacks
- AND nothing is cloned

### scenario.e2e.default-root — Test projects live in the temporary directory

- GIVEN an environment without `CONCORDE_E2E_ROOT`
- WHEN the tool resolves the end-to-end root and the directory of the test project `requests`
- THEN the root is `concorde-e2e` in the system's temporary directory and the project's directory `test-requests` there

### scenario.e2e.root-inside-checkout — A root inside the checkout is refused

- GIVEN `CONCORDE_E2E_ROOT` naming this checkout or a directory inside it, or no `CONCORDE_E2E_ROOT` and a system temporary directory inside this checkout
- WHEN the tool resolves the end-to-end root, as `prepare` does first
- THEN it refuses with `root_inside_checkout`, naming the root, the checkout and that Claude Code would load the checkout's `CLAUDE.md` into the test project's sessions
- AND `prepare` clones nothing
- BUT a `CONCORDE_E2E_ROOT` outside the checkout is the root

### scenario.e2e.relative-root — A relative root is resolved before preparation

- GIVEN a `CONCORDE_E2E_ROOT` that is a relative path, from a working directory outside this checkout
- WHEN the developer prepares a test project
- THEN the end-to-end root is that path resolved against the working directory, as an absolute path
- AND `prepare` works under that absolute root, so every command it runs in another directory finds the project

### scenario.e2e.trust — Trusting a test project

- GIVEN a [test project](../glossary.json#concept.test-project) whose repository root Claude Code does not trust, and a configuration with other settings
- WHEN the developer runs `trust` for a directory inside it
- THEN the configuration marks that repository root trusted, keeps every other setting, and a backup of the file exists

### scenario.e2e.trust-again — Trusting a trusted project changes nothing

- GIVEN a test project whose repository root `trust` already marked trusted
- WHEN the developer runs `trust` for it again
- THEN the configuration file is unchanged
- AND the result names no newly trusted root and names that root as already trusted

### scenario.e2e.headless — A headless run waits for its workflow without trust

- GIVEN an untrusted test project with an open task
- WHEN the developer starts a headless run of the [brownfield workflow](../glossary.json#concept.brownfield-workflow) with `--restart scaffold=2`
- THEN the `claude -p` session has `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` set to `0`
- AND its command line grants the workflow and its step and report commands
- AND its command line gives the session the [project MCP server](../glossary.json#concept.project-mcp-server), started as the installer registers it
- AND the workflow's arguments, the restart label `2` of `scaffold` included, reach the session's prompt
- AND the prompt places the session in the task's worktree as the task's [task session](../glossary.json#concept.task-session) and has it report with `concorde workflow report`
- AND its appended system prompt is the headless note alone, without the test procedure of a headless main session
- BUT the workflow's arguments name no task

### scenario.e2e.driver-paths — A driver run works in a project whose path holds spaces

- GIVEN a test project whose directory and task worktree have names holding spaces and a quote
- WHEN a driver run's [step agent](../glossary.json#concept.step-agent) plays a `workflow_step` call of the script
- THEN it runs the worktree's own `concorde workflow step` with the step's request and wait as separate arguments, in the worktree
- AND it answers what that command printed

This illustrates [the driver's real step commands](requirements.md#req.e2e.driver-real-steps).

### scenario.e2e.malformed-restart — A malformed restart is a usage error

- GIVEN a test project with an open task
- WHEN the developer runs `run` with `--restart scaffold`, which names no label
- THEN the tool prints its usage to standard error and exits 2
- AND no workflow runs

### scenario.e2e.runtime-failures — A failure at run time is printed as an error

- GIVEN a command that cannot be started, a task whose record is missing or names no worktree, this checkout's [worker configuration](../glossary.json#concept.worker-configuration) holding JSON that is no object, or a failure the tool did not foresee
- WHEN a command of the tool meets it
- THEN the tool prints `{"error": …}` with `command_failed`, `no_task`, `worker_configuration_unreadable` or `unexpected_error` and its traceback, and exits 1
- BUT it never ends in a traceback of its own

### scenario.e2e.stale-result — A result an earlier run saved is not the run's

- GIVEN a test project whose task's [workflow record](../glossary.json#concept.workflow-record) holds one result an earlier run saved, and in which nobody else reports a workflow while the run runs
- WHEN a `run` ends without its workflow saving a result
- THEN `run` fails with `no_result`, naming that the record held one result before the run and one after it
- AND the earlier run's result is not printed

### scenario.e2e.newest-result — A run prints the newest result it saved

- GIVEN a test project whose task's workflow record holds one result an earlier run saved, and in which nobody else reports a workflow while the run runs
- WHEN a `run` ends after its workflow saved two results
- THEN `run` prints the second of them

### scenario.e2e.owners-passed — Only the owner of each run is woken

- GIVEN a test project with a task `t1` with a worktree, and live sessions of two Claude Code main sessions in its primary worktree, each woken only by its own background commands
- WHEN `owners` plays a run started by nobody's tool and a run the first session starts in background Bash
- THEN it ends `passed`
- AND for the unowned run no session was woken, for the owned run only the first session was woken, and every session that does not own a run found it ended with `concorde task show t1`

### scenario.e2e.owners-unwanted-wake — A session woken by a run it does not own fails the case

- GIVEN a test project with a task `t1` with a worktree, and live sessions of two Claude Code main sessions in its primary worktree, each also woken by the end of every run
- WHEN `owners` plays its two runs
- THEN it ends `failed`, naming each session woken by a run it does not own in each phase
- AND the first session woken by its own run is no problem

### scenario.e2e.owner-not-woken — An owner not woken by its deadline fails the case

- GIVEN a test project with a task `t1` with a worktree, and live sessions of two Claude Code main sessions in its primary worktree, none ever woken by a background command
- WHEN `owners`, with `--wake 2` and `--grace 1`, plays a run the first session starts in background Bash and the run writes its result
- THEN the case observes the sessions for 3 seconds after the result, the sum of the two, and then judges the phase
- AND the case ends `failed`, naming that the owner `claude-1` was not woken when its run ended, and with no error

### scenario.e2e.owners-run-refused — A run refused for a busy workspace stops the case

- GIVEN a test project with a task `t1` with a worktree, and live sessions of two Claude Code main sessions in its primary worktree
- WHEN `owners` plays a run that waits in the lobby for the [workspace lock](../glossary.json#concept.workspace-lock) the case holds, and once the case released it is refused with `workspace_busy`, as when another run took the lock first and held it past the run's wait
- THEN the case stops with `workspace_busy`, naming the phase and the refused run's result in the lobby
- AND it judges no phase of that run

### scenario.e2e.owners-session-ended — A session that ends stops the case

- GIVEN a test project with a task `t1` with a worktree, and live sessions of two Claude Code main sessions in its primary worktree, the first of which ends right after it started a background command
- WHEN `owners` plays a run the first session starts in background Bash and the run writes its result
- THEN the case stops with `session_failed`, naming the session and the phase
- BUT it judges no phase of that run, so the ended owner is not reported as an owner that was not woken

### scenario.e2e.owners-too-few-sessions — The owners case needs two sessions

- GIVEN a test project with a task `t1` with a worktree
- WHEN `owners` is asked to keep fewer than two sessions
- THEN it stops with `invalid_input` before any session starts

### scenario.e2e.owners-no-task — The owners case needs a task with a worktree

- GIVEN a test project without a task `t9`, or whose [task record](../glossary.json#concept.task-record) names a worktree that does not exist
- WHEN `owners` is asked to play its runs on that task
- THEN it stops with `no_task` before any session starts
