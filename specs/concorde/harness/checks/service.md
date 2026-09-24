# The check service

The exact declaration of configured checks, the call that runs them and the check result, and the
requirements and scenarios they serve. The [entry](module.md#concept.checks.configured-check)
explains why it is shaped this way; [the boundary](boundary.md) gives the runner it uses.

## Declaring a configured check

The project configuration lists checks under `checks`. Each has:

| Field | Meaning |
| --- | --- |
| `id` | The check's identity, unique in the project |
| `module` | The Module the check belongs to |
| `argv` | The command as an argument list; a first element `{python}` is replaced by the host's interpreter |
| `timeout_seconds` | A positive time limit |
| `inputs` | Project-relative files or directories the result depends on, beyond the Module's own implementation files |

The Spec core validates `id`, `module` and `inputs` when it loads the configuration; the service
validates `argv` and `timeout_seconds` when it runs the check. `PYTHONPATH` points at the Framework's
`src/`. An input that is missing, a symbolic link or not a regular file stops the run before any
command and names the check, its Module and the path.

## Running checks

`run_checks(worktree, *, modules=None, changed=None, log_directory)` in
`src/concorde/harness/checks.py`:

1. selects the Modules: those named in `modules`, or else every Module whose `ImplementationScope`
   or `SpecScope` in `worktree` contains a path in `changed`;
2. for each selected Module, computes `check_revision`: the digest of the Module's implementation
   digest, each of its checks' definitions, the digest of every file below their inputs, and
   `CHECK_POLICY`;
3. runs each of the Module's checks in order through `execute_check` with `worktree` as project root
   and the default boundary;
4. writes `<stdout>\n<stderr>` to `<log_directory>/<check id>.log`, also when the boundary refused the
   command, and then fails a refused run with `check_sandbox_unavailable`;
5. computes `check_revision` again and fails the whole call with `stale_evidence` when it differs;
6. returns one check result per check, in configuration order.

A selected Module without configured checks contributes no result; the caller decides whether that
is acceptable.

### Check result

| Field | Meaning |
| --- | --- |
| `check_id` | The configured check |
| `module` | The Module the check belongs to |
| `status` | `passed` (exit code 0), `failed` (any other exit code) or `timeout` |
| `exit_code` | The exit status, `-1` on timeout |
| `source_digest` | The `check_revision` measured before the run |
| `log` | The log's path |
| `log_digest` | The digest of the saved log |

A consumer decides whether a stored check result is still current by recomputing `check_revision`
for the same Module and comparing it with `source_digest`.

### A check that did not pass as an error link

`check_error(result)` turns a check result whose status is not `passed` into the check's link of
the Framework's [error chain](../../contracts.md#contract.concorde.error), so every consumer reports
a failing check the same way: the level `check`, the check's identity as actor, the code
`check_failed` or `check_timed_out`, a detail naming the Module, the exit code, the log path and the
last 3,000 bytes of the log, the log as evidence, and the reason `capability`, because a check only
measures the code it runs against.

## Requirements

### req.checks.measured-input-unchanged — A check cannot vouch for input that changed

A configured check run SHALL fail with `stale_evidence` when the implementation files or check
inputs it measured differ after the run from before it.

### req.checks.logs-where-asked — Check output stays with the caller's run

The check service SHALL write every configured check's log only into the log directory its caller
named.

### req.checks.failure-link — A failing check explains itself

The check service SHALL describe a check result that did not pass, when a consumer reports it as an error, with its Module, exit code, log path and the end of its log.

### req.checks.no-status-without-run — A refused check has no status

The check service SHALL NOT return a check result for a check whose command the boundary refused to
start.

## Scenarios

### scenario.checks.service-run — The checks of changed Modules run and are logged

- GIVEN a worktree whose Module A has one configured check and Module B none
- WHEN the service runs with a changed path of A's realization or A's Spec
- THEN it selects A, runs its check read-only and returns one result with its status, exit code, source digest and log path
- AND the log is written into the caller's log directory
- BUT asked for Module B it returns no result

### scenario.checks.service-read-only — A check cannot change the worktree

- GIVEN a configured check that tries to write a file of the worktree
- WHEN the service runs it
- THEN the write fails as a read-only file system and the check's result is `failed`
- AND the file is unchanged

### scenario.checks.service-stale — Input that changes during the run is stale

- GIVEN a check whose Module's implementation file changes while the check runs
- WHEN the service measures the check revision again
- THEN the call fails with `stale_evidence` and returns no result

### scenario.checks.service-refused — A refused check has no status

- GIVEN a host where the read-only boundary cannot start the check's command
- WHEN the service runs the check
- THEN the call fails with `check_sandbox_unavailable`
- AND the log holds what the boundary reported
- BUT no check result is returned

### scenario.checks.service-input-missing — A missing input stops the run

- GIVEN a configured check whose declared input does not exist
- WHEN the service is asked to run it
- THEN the call fails naming the check, its Module and the path before any command runs
