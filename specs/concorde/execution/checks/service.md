# The check service

This document gives the following exact declarations:

- the declaration of configured checks
- the call that runs them
- the [check result](../../glossary.json#concept.check-result)

It also gives the requirements and scenarios they serve. The
[entry](../../glossary.json#concept.configured-check) explains why the service is shaped this way.
[The boundary](boundary.md) gives the runner it uses.

## Declaring a configured check

<a id="checks-files"></a>

Each [Module](../../glossary.json#concept.module)'s checks are listed under `checks` in its own
**checks file**, `.concorde/checks/<module id>.json`. This is a Git-tracked file of Check execution's.
The file's name is the Module the checks belong to, so an entry has no `module` field. For Check execution, a Module identity is a label that names a checks file. Check execution never
checks it against a registry.
The configuration order of the checks is the byte order of the file names, then the order of the
entries in each file. A checks file is a JSON object with exactly one field, `checks`, a list of
entries. Each entry has the fields in this table:

| Field | Meaning |
| --- | --- |
| `id` | The check's identity, unique in the project |
| `argv` | The command as an argument list; an element `{python}` is replaced by the project's interpreter, and an element `{tests}` by the tests that declare they verify a scenario of the Modules being checked, which makes the check selective |
| `env` | Optional variables of the command, names to strings, such as `{"PYTHONPATH": "src"}` |
| `when` | Optional: `always` (the default) runs the check wherever checks run; `readiness` runs it only when readiness is decided, by `task-validation` and `delivery`, for a full suite too slow for every round |
| `timeout_seconds` | A positive, finite time limit |
| `inputs` | Project-relative files or directories the result depends on, beyond the Module's own implementation files |

Check execution validates every checks file it reads. When any of these conditions holds, Check
execution refuses the file or entry with `invalid_check`, naming the file and the entry:

- The file is not valid JSON. This includes a repeated field and these constants: `NaN` and
  `Infinity`.
- The file holds another field or an entry with a field the table does not name.
- The file's name is not a Module identity.
- An `id` is used twice in the project.
- An input is not a canonical project-relative path or escapes the worktree through a directory
  that is a symbolic link.

For a caller that wants the checks files judged before any check runs, `validate_checks(worktree)`
does the same alone. Method's `task-validation` does this. When `kinds` is `module`, a call of
`run_checks` narrowed to the ordinary checks reads only the checks files of the selected Modules.
The measurement after a check reads only the file of the check's own Module. Thus, a malformed
checks file of another Module never stops their checks. Only when both files are read is an `id`
used twice then found. `validate_checks` reads them all. Before it runs the first command, the
service validates these fields of every check it keeps:

- `argv`
- `env`
- `when`
- `timeout_seconds`

An input names a regular file or a directory. Below a directory, the service measures every regular
file outside `__pycache__` directories. When any of these conditions holds, an input stops the run
before any command:

- The input is missing.
- The input is itself a symbolic link.
- The input is neither a regular file nor a directory.

The stopped run names the following:

- the check
- its Module
- the path

A **selective** check is one whose `argv` holds `{tests}`. For the whole set of selected Modules,
such a check runs at most once per call, whichever Module it belongs to. When there are no tests,
the selective check is skipped. Otherwise, it runs with the tests its caller names. These are the
tests whose [verification declarations](../../glossary.json#concept.verification-declaration) name
a scenario of any of the selected Modules. Tests and scenarios are many-to-many. A Module's change
runs the tests verifying its scenarios, wherever their files are bound. Thus, the Module that owns
a test file only decides who may change it. A Python test is passed as `path::Class::name`. A
TypeScript test is passed by its file. The log of a selective check begins with the tests it
selected. Because the same check runs other tests for another selection, its measured digest also
covers the selected Modules and the selected tests.

The project's interpreter is the one the caller names. In Concorde, this is the project
configuration's `python`, which Method's steps pass. The service resolves that interpreter as
follows:

- An absolute path is used as it is.
- A relative path is resolved in the worktree the check runs in.
- When that worktree has none, a relative path is resolved in the primary worktree, since a task
  worktree rarely has an environment of its own.

The project's interpreter is never Concorde's interpreter, which runs in its own environment.
When a check uses `{python}` without one, or with one that is not an executable file there, the
check stops with `project_python_missing`. The error names every place looked at. A check runs
with these environment variables:

- the host's `PATH` and `LANG`
- the transport variables below when present
- its own `env`

No other host variable is inherited, so nothing of Concorde's runtime enters the check. A relative
`PYTHONPATH` such as `src` explicitly set in the check's `env` is resolved in the worktree the check
runs in. Thus, an installed copy of the project's code does not stand in for code under test.

| Inherited transport variables | Purpose |
| --- | --- |
| `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`, `http_proxy`, `https_proxy`, `all_proxy`, `no_proxy` | Preserve the enclosing host or sandbox's proxy route and bypass list |
| `SSL_CERT_FILE`, `SSL_CERT_DIR`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS` | Preserve standard TLS trust file and directory locations |

Names are matched exactly. Upper and lower case values remain independent, including empty
values. Each client applies its own precedence. The check's `env` overrides inherited values by
exact name, including with an empty string. As specified in [the boundary](boundary.md), the
executor then replaces these variables with its own scratch paths:

- temporary variables
- cache variables
- report variables

Runtime injection settings such as the following are not inherited:

- `PYTHONPATH`
- `PYTHONHOME`
- `VIRTUAL_ENV`
- `NODE_OPTIONS`
- Concorde or agent session variables

Transport values are passed as environment data, never added to the command line or diagnostic
messages.

## Running checks

`run_checks(worktree, *, modules, trace_directory, measured=None, tests=None, python=None,
stage="work", kinds="all")` in `src/concorde/execution/checks/checks.py` runs these steps:

1. The service takes the Modules to check from `modules`, as labels that select checks files.
  The caller decides which Modules a change concerns and which Modules use one of them. This
  decision needs the Specs. Through the Spec tooling, Method's steps select the Modules a change
  concerns together with every Module that uses one of them, directly or through further uses
  ([Method](../../method/module.md#the-standard-worker-sequence)). Thus, whenever code a Module
  uses changes, that Module's checks run.
2. The service goes through the configured checks in configuration order. Only when `stage` is
  `readiness`, the service keeps a check marked `"when": "readiness"`. `task-validation` and
  `delivery` pass this stage. Every other caller leaves the default `work`.
3. When its own Module is selected, the service keeps an ordinary check. When `tests` names some
  test for the selected Modules, the service keeps a selective check once. The caller computes
  `tests` from the tests'
  [verification declarations](../../glossary.json#concept.verification-declaration).
  `kinds` narrows the call to the ordinary checks (`module`) or to the selective ones (`selective`).
  Thus, a caller can run each Module's own checks separately and the selective checks once for the
  whole selection. A check whose `argv` is not a list is no selective check. Like every malformed
  `argv`, the service refuses it with `invalid_check`.
4. Before running any command, the service validates these fields of every kept check:

  - `argv`
  - `env`
  - `timeout_seconds`

  The service replaces `{python}` and `{tests}`. The service finds every declared input of every
  kept check. Whichever Module the kept check belongs to, any of these problems stops the call
  before the first command:

  - an invalid check
  - a missing interpreter
  - a missing input

5. For each kept check, the service computes its measured digest with `measured_digest`, in the
  same file. For an ordinary check, the digest is `check_revision` of the check's own Module.
  This is the digest of the following:

  - the files the caller names for that Module in `measured`, in Concorde its implementation files
  - each of its checks' definitions
  - the digest of every file below their inputs
  - `CHECK_POLICY`

  For a selective check, the measured digest is the digest of the following together:

  - that `check_revision`
  - the sorted selected Modules
  - the tests it selected
  - the digest of every file holding one of them

6. The service makes `trace_directory` absolute. The service performs these steps:

  - creates the check's [trace node](../../glossary.json#concept.trace-node)
    `<trace_directory>/<check id>/`
  - writes the node's `trace.json` with status `running`
  - runs the check through `execute_check` with `worktree` as project root and the default boundary
  - writes `<stdout>\n<stderr>` to `output.log` of the node, preceded for a selective check by the
    tests it selected
  - writes `trace.json` again with the check's end

  When the boundary refused the command, the log holds what the boundary reported. Under this
  condition, the node ends `failed` with the service's error. The call fails with
  `check_sandbox_unavailable`.

  Before the node ended, any of these events can end the call:

  - a cancellation
  - an interrupt
  - an unexpected error

  When one of these events ends the call before the node ended, the log holds the output the
  boundary drained. Under this condition, the node ends `failed` with the outcome and status
  `interrupted`. The error goes on to the caller unchanged.

  When the operating system refuses a write of `trace.json`, that write never changes the check
  or the call. The check result names the refused write in `trace_failures`. An error the call
  fails with names those of every check it ran ([Errors](#errors)).
7. The service computes the measured digest again, over the same named files and selected tests.
  When the digest differs or can no longer be computed, the service fails the whole call with
  `stale_evidence`. The digest can no longer be computed when a measured file, selected test file
  or input is gone or became a symbolic link.
8. The service returns one check result per check it ran, in configuration order.

A failure in any step ends the call without results, including those of checks that already ran.
A selected Module without configured checks contributes no result. The caller decides whether
that is acceptable.

### Check result

| Field | Meaning |
| --- | --- |
| `check_id` | The configured check |
| `module` | The Module the check belongs to |
| `status` | `passed` (exit code 0), `failed` (any other exit code) or `timeout` |
| `exit_code` | The exit status, `-1` on timeout |
| `source_digest` | The measured digest taken before the run |
| `log` | The absolute path of the check node's `output.log` |
| `log_digest` | The digest of the saved log |
| `trace_failures` | Each write of the check node's `trace.json` that the operating system refused, naming the node's file, the moment (`start` or `end`) and the error; empty when every write succeeded |

Every check the service runs is also a trace node of kind `check`, as
[Tracing](../../kernel/tracing/contracts.md#contract.tracing.node) defines it. Its content is this
value:

```concorde-contract
{
  "id": "contract.checks.check-trace",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "status",
      "exit_code",
      "source_digest",
      "argv",
      "selected_tests"
    ],
    "properties": {
      "status": {
        "enum": [
          "passed",
          "failed",
          "timeout",
          "refused",
          "interrupted"
        ]
      },
      "exit_code": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "integer"
          }
        ]
      },
      "source_digest": {
        "type": "string",
        "minLength": 1
      },
      "argv": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "selected_tests": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      }
    }
  },
  "semantics": "The data of the typed value concorde-check-trace, the content of one check's trace node. status is the check result's status, refused when the boundary refused to start the command, or interrupted when a cancellation, an interrupt or an unexpected error ended the call before the check ended; exit_code is its exit status, -1 on timeout, null when refused or interrupted; source_digest is the measured digest taken before the run; argv is the command as run; selected_tests are the tests a selective check selected, empty otherwise. The node's identity is the check identity, its metadata the check and its Module, its status ok for passed and failed otherwise, its outcome the check status, its usage the check's duration, and output.log its artifact with the log digest. A behaviour or field change increments the version.",
  "example": {
    "status": "failed",
    "exit_code": 1,
    "source_digest": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
    "argv": [
      ".venv/bin/python",
      "-m",
      "pytest",
      "tests/http"
    ],
    "selected_tests": []
  }
}
```

A consumer decides whether a stored check result is still current by recomputing `measured_digest`
for the same check. For a selective check, the consumer uses the same selected Modules too. The
consumer compares the recomputed digest with `source_digest`.

### Errors

Check execution raises its own `CheckError`. Its record carries these fields:

- a code
- a message
- a reason
- a location
- a remediation
- causes

The record uses these codes:

- `invalid_check`: a checks file or entry that breaks [the format](#checks-files), or a check with
  any of these defects:
  - no nonempty argv
  - no positive timeout
  - an `env` that is not an object of variable names to strings
  - a `when` other than `always` or `readiness`
- `check_input_missing`
- `project_python_missing`: a check uses `{python}` but the configuration names no project
  interpreter, or none that is an executable file where it was looked for
- `check_sandbox_unavailable`: the read-only boundary cannot be established
- `stale_evidence`: an input changed while the check ran
- `system_error`: an operating-system error

Each carries the following:

- a message naming the check or Module concerned
- the code's reason
- its location
- remediation
- causes

When a `CheckError` ends a call after checks ran, it also carries each refused trace write in
`trace_failures`. These are writes of those checks' nodes' `trace.json` that the operating system
refused. It carries them because the call returns no result that could name them. Check execution depends on no part but
the kernel, so its error type is its own. Since `service_error` makes the link, a caller never
needs to translate the error type.

### Check execution's error as a link

`service_error(error)` turns an error `run_checks` raised into this Module's own link of the
Framework's [error chain](../../kernel/tracing/contracts.md#contract.tracing.error). Every caller
keeps this link unchanged as a cause under its own link. These callers include:

- a run's stop for checks that could not run
- the round validation that runs a worker's checks
- Validation's blocking `check` finding and its `inputs_changed` stop

The link has the following:

- the level `component`
- the actor `Check execution`
- the error's code
- a detail with its message and location
- the location and each refused trace write of the error as `trace-write` evidence
- the code's reason as explanation
- its remediation as option and recommendation
- the error's own causes nested the same way

The link's unhandled reason depends on the code:

| Code | Reason |
| --- | --- |
| `check_sandbox_unavailable`, `stale_evidence` | `environment`: the host cannot establish the boundary, or something outside the service changed the input |
| `system_error`: an operating-system error | `environment` |
| any other exception the service did not expect | `capability` |
| every other code of `CheckError` | `input`: the checks files or the Modules named are wrong, and only whoever supplied them can correct them |

### A check that did not pass as an error link

`check_error(result)` turns a check result whose status is not `passed` into the check's link of
the Framework's [error chain](../../kernel/tracing/contracts.md#contract.tracing.error). Thus, every
consumer reports a failing check the same way. The link has the following:

- the level `check`
- the check's identity as actor
- the code `check_failed` or `check_timed_out`
- a detail naming the following:
  - the Module
  - the exit code (`-1` for a timeout)
  - the log path
  - the last 3,000 bytes of the log
- the log as evidence
- the reason `capability`

The reason is `capability` because a check only measures the code it runs against.

## Requirements

### req.checks.project-python — Checks run the project's interpreter, never Concorde's

The service SHALL replace `{python}` with the project's interpreter named by the configuration's
`python`.

### req.checks.no-concorde-runtime — A check inherits nothing of Concorde's runtime

The service SHALL NOT give a check any host environment variable other than these:

- `PATH`
- `LANG`
- the inherited transport variables

The check's own `env` and the scratch settings of [the boundary](boundary.md) are added to these.

### req.checks.measured-input-unchanged — A check cannot vouch for input that changed

When the implementation files, check inputs or selected tests it measured differ after the run
from before it, a configured check run SHALL fail with `stale_evidence`.

### req.checks.selection-measured — A selective result names its selection

The measured digest of a selective check SHALL cover the selected Modules and the digest of every
selected test file.

### req.checks.service-link — A service failure reaches the caller as this Module's link

The check service SHALL give every caller its failures as Check execution's own error link, which
the caller keeps as a cause under its own link.

### req.checks.logs-where-asked — Check output stays with the caller's run

The check service SHALL record every configured check it runs as a trace node, with its log, only
inside the trace directory its caller named.

### req.checks.failure-link — A failing check explains itself

When a consumer reports a check result that did not pass as an error, the check service SHALL
describe the result with the following:

- its Module
- its exit code
- its log path
- the end of its log

### req.checks.trace-write-reported — A refused trace write is in the check's result

The check service SHALL report every write of a check node's `trace.json` that the operating system refused, without changing the check's status or the call's outcome for it, in one of these places:

- that check's result
- the error of a call that returns no result

Tracing is best-effort for the check, never silent
([req.tracing.written-at-start](../../kernel/tracing/requirements.md#req.tracing.written-at-start)).

### req.checks.no-status-without-run — A refused check has no status

The check service SHALL NOT return a check result for a check whose command the boundary refused to
start.

## Scenarios

### scenario.checks.checks-files — Configured checks are read from one file per Module

- GIVEN a worktree whose `.concorde/checks/` holds `module.b.json` with two checks and `module.a.json` with one
- WHEN Check execution reads the configured checks
- THEN it holds the check of `module.a` first and then those of `module.b` in file order, each carrying the Module its file is named after
- AND a file named after a Module no registry registers is read like any other, since the identity is a label
- BUT a check entry with a `module` field or another field the format does not name is refused with `invalid_check`, naming the file and what to change
- AND so is an `id` another file already uses, or an input that is not a canonical project-relative path
- AND so is a file that is not valid JSON or holds another field, or a file not named `<module id>.json`

### scenario.checks.check-input-missing — A configured check names a missing input

- GIVEN a checks file whose [configured check](../../glossary.json#concept.configured-check) declares an input path that does not exist
- WHEN its caller has the checks files judged with `validate_checks` before any check runs
- THEN it is refused with `check_input_missing`, naming the check and the path
- AND no check runs

### scenario.checks.service-run — The checks of changed Modules run and are logged

- GIVEN a worktree whose Module A has one configured check and Module B none
- WHEN the service runs for the Modules a changed path of A's realization or A's [Spec](../../glossary.json#concept.spec) concerns, as its caller selects them
- THEN it runs A's check read-only and returns one result with its status, exit code, source digest and log path
- AND the check's trace node, with its `output.log`, is written into the caller's trace directory

### scenario.checks.service-trace-write — A refused trace write is in the check's result

- GIVEN a configured check whose trace node's `trace.json` the operating system refuses to write
- WHEN the service runs it
- THEN the check runs, its log is written and its result has the status its command gave
- AND the result's `trace_failures` names each refused write with the node's file, the moment and the error
- AND a check whose every write succeeded has empty `trace_failures`
- BUT when the call then fails, such as with `stale_evidence`, Check execution's link names each refused write of the checks it ran as `trace-write` evidence

### scenario.checks.service-no-checks — A Module without checks gets no result

- GIVEN a worktree whose Module B has no configured check
- WHEN the service runs for Module B
- THEN it returns no result

### scenario.checks.project-python — A check runs with the project's interpreter and its own env

- GIVEN a check `["{python}", "-c", …]` with `env` `{"MARK": "yes"}` and a configuration whose `python` is `env/bin/python`
- AND `env/bin/python` exists in the worktree
- WHEN the check runs
- THEN it runs with `env/bin/python`, sees `MARK` and has no `PYTHONPATH`

### scenario.checks.project-python-missing — A missing project interpreter stops the run

- GIVEN a check `["{python}", "-c", …]` and a configuration whose `python` is `env/bin/python`
- AND `env/bin/python` does not exist
- WHEN the check runs
- THEN the run stops with `project_python_missing` naming the path it looked at

### scenario.checks.project-python-primary — A task worktree uses the primary worktree's interpreter

- GIVEN a configuration whose `python` is `.venv/bin/python`, which the primary worktree has
- AND a task worktree without its own `.venv/bin/python`
- WHEN a check of the task worktree uses `{python}`
- THEN the primary worktree's interpreter is used

### scenario.checks.check-env-invalid — A check env with invalid names is refused

- GIVEN a check whose `env` has a name that is not a variable name, such as `not a name` or `MARK` followed by a newline
- WHEN the check runs
- THEN it is refused with `invalid_check`

### scenario.checks.transport-environment — A nested check keeps its transport configuration

- GIVEN a host with proxy and TLS trust-location variables and unrelated runtime variables
- WHEN the service runs a configured check inside another check boundary
- THEN it inherits only `PATH`, `LANG` and the named transport variables, with the check's own `env` taking precedence by exact name
- AND the check can reach a local proxy while project writes remain denied and its issued scratch remains writable
- BUT inherited runtime variables do not enter the command, and configured temporary or cache paths cannot replace the executor's scratch paths

### scenario.checks.selective — A selective check runs the tests that verify the checked Modules

- GIVEN a test in `src/a/` that declares it verifies a scenario of Module A, and a check whose argv holds `{tests}`
- WHEN the checks of Module A run
- THEN the selective check runs once with `src/a/test_answer.py::test_answer` in place of `{tests}`, its log naming the selected tests
- AND the selective check's measured digest for Module A differs from its measured digest for Modules A and B, and from its digest once the selected test file changes

### scenario.checks.selective-none — A selective check with nothing to select is skipped

- GIVEN a check whose argv holds `{tests}`, and no test that verifies a scenario of Module B
- WHEN the checks of Module B run
- THEN the selective check is skipped and returns no result

### scenario.checks.readiness-only — A readiness check runs only when readiness is decided

- GIVEN a check of Module A marked `"when": "readiness"`
- WHEN the checks of Module A run with a `stage` other than `readiness`
- THEN that check does not run and returns no result
- AND the same call with `stage` `readiness` runs it

### scenario.checks.service-read-only — A check cannot change the worktree

- GIVEN a configured check that tries to write a file of the worktree and exits with a nonzero code when the write fails
- WHEN the service runs it
- THEN the write fails as a read-only file system and the check's result is `failed`
- AND the file is unchanged

### scenario.checks.service-stale — Input that changes during the run is stale

- GIVEN a check whose Module's implementation file changes, or is deleted, while the check runs
- WHEN the service measures the check revision again
- THEN the call fails with `stale_evidence` and returns no result
- AND Check execution's link for it has the level `component`, the actor `Check execution`, the code `stale_evidence` and the reason `environment`

### scenario.checks.service-refused — A refused check has no status

- GIVEN a host where the read-only boundary cannot start the check's command
- WHEN the service runs the check
- THEN the call fails with `check_sandbox_unavailable`
- AND the log holds what the boundary reported
- AND a caller that cannot run its checks keeps Check execution's `check_sandbox_unavailable` link as a cause
- BUT no check result is returned

### scenario.checks.service-input-missing — A missing input stops the run

- GIVEN a configured check whose declared input does not exist
- WHEN the service is asked to run it, alone or after a kept check of another Module that comes first in configuration order
- THEN the call fails naming the check, its Module and the path before any command runs
