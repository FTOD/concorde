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

### scenario.e2e.worker-configuration — A test project gets a worker configuration

- GIVEN this checkout's own `.concorde/workers.json`
- WHEN the developer prepares a test project, with or without `--worker-model`
- THEN the project's committed `.concorde/workers.json` enables and chooses the given project model name for every worker, or holds this checkout's enabled models, defaults, [Operation](../glossary.json#concept.operation) entries and limits without its `runtime` paths
- AND the result names the enabled models
- BUT a model the developer's [model map](../glossary.json#concept.model-map) gives no id for a worker's program is refused with `model_unmapped` before anything is cloned

### scenario.e2e.default-root — Test projects live in the temporary directory

- GIVEN an environment without `CONCORDE_E2E_ROOT`
- WHEN the tool resolves the end-to-end root
- THEN it is `concorde-e2e` in the system's temporary directory, outside the developer's home

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
- AND the workflow's arguments, the restart label `2` of `scaffold` included, reach the session's prompt
- AND the prompt places the session in the task's worktree as the task's [task session](../glossary.json#concept.task-session) and has it report with `concorde workflow report`
- AND its appended system prompt is the headless note alone, without the test procedure of a headless main session
- BUT the workflow's arguments name no task

### scenario.e2e.stale-result — A result an earlier run saved is not the run's

- GIVEN a test project whose task's [workflow record](../glossary.json#concept.workflow-record) already holds a result an earlier run saved
- WHEN a `run` ends without its workflow saving a result
- THEN `run` fails with `no_result`, naming how many results the record held before and after the run
- BUT when the workflow saves results during the run, `run` prints the newest of them

### scenario.e2e.owners-case — Several live main sessions, and only the owner woken

- GIVEN a test project with a task `t1` with a worktree, and live sessions of two Claude Code main sessions in its primary worktree
- WHEN `owners` plays a run started by nobody's tool and a run the first session starts in background Bash
- THEN it ends `passed` when, for each run, only its owner was woken and every other session found the run ended with `concorde task show t1`
- AND it ends `failed`, naming the session, when a session was woken by a run it does not own
- BUT fewer than two sessions (`invalid_input`) or a task without a worktree (`no_task`) stop it before any session starts
