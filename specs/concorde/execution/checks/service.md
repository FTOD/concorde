# The check service

The exact declaration of configured checks, the call that runs them and the
[check result](../../glossary.json#concept.check-result), and the requirements and scenarios they
serve. The [entry](../../glossary.json#concept.configured-check) explains why it is shaped this way;
[the boundary](boundary.md) gives the runner it uses.

## Declaring a configured check

<a id="checks-files"></a>

Each [Module](../../glossary.json#concept.module)'s checks are listed under `checks` in its own
**checks file**, `.concorde/checks/<module id>.json`, a Git-tracked file of Check execution's; the
file's name is the Module the checks belong to, so an entry has no `module` field. For Check
execution a Module identity is a label that names a checks file, never checked against a registry.
The configuration order of the checks is the byte order of the file names, then the order of the
entries in each file. A checks file is a JSON object with exactly one field, `checks`, a list of
entries; each entry has:

| Field | Meaning |
| --- | --- |
| `id` | The check's identity, unique in the project |
| `argv` | The command as an argument list; an element `{python}` is replaced by the project's interpreter, and an element `{tests}` by the tests that declare they verify a scenario of the Modules being checked, which makes the check selective |
| `env` | Optional variables of the command, names to strings, such as `{"PYTHONPATH": "src"}` |
| `when` | Optional: `always` (the default) runs the check wherever checks run; `readiness` runs it only when readiness is decided, by `task-validation` and `delivery`, for a full suite too slow for every round |
| `timeout_seconds` | A positive time limit |
| `inputs` | Project-relative files or directories the result depends on, beyond the Module's own implementation files |

Check execution validates every checks file whenever it reads the checks: a file that is not
valid JSON, holds another field or an entry with a field the table does not name, a file whose name
is not a Module identity, an `id` used twice in the project, an input that is not a canonical
project-relative path or one that escapes the worktree is refused with `invalid_check`, naming the
file and the entry; its `validate_checks(worktree)` does the same alone, for a caller that wants
the checks files judged before any check runs, as Method's `task-validation` does. The service
validates `argv`, `env`, `when` and `timeout_seconds` when it runs the check. An input names a
regular file or a directory; below a directory the service measures every regular file outside
`__pycache__` directories. An input that is missing, is itself a symbolic link or is neither a
regular file nor a directory stops the run before any command and names the check, its Module and
the path.

A **selective** check, one whose `argv` holds `{tests}`, runs at most once per call for the whole
set of selected Modules, whichever Module it belongs to, with the tests its caller names, those whose
[verification declarations](../../glossary.json#concept.verification-declaration) name a scenario of
any of them, and is skipped when there are none. Tests and scenarios are many-to-many: the tests a
Module's change runs are those verifying its scenarios, wherever their files are bound, so the
Module that owns a test file only decides who may change it. A Python test is passed as
`path::Class::name`, a TypeScript test by its file, and the log of a selective check begins with the
tests it selected. Because the same check runs other tests for another selection, its measured
digest also covers the selected Modules and the selected tests.

The project's interpreter is the one the caller names, in Concorde the project configuration's
`python`, which Method's steps pass: an absolute path as it is, a relative one in the worktree the
check runs in or, when that has none, in the primary worktree, since a
task worktree rarely has an environment of its own. It is never Concorde's interpreter, which runs
in its own environment. A check that uses `{python}` without one, or with one that is not an
executable file there, stops with `project_python_missing`, naming every place looked at. A check
runs with the host's `PATH` and `LANG`, the transport variables below when present, and its own
`env`. No other host variable is inherited, so nothing of Concorde's runtime enters the check: a
relative `PYTHONPATH` such as `src` explicitly set in the check's `env` is resolved in the worktree
the check runs in, so an installed copy of the project's code does not stand in for code under test.

| Inherited transport variables | Purpose |
| --- | --- |
| `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`, `http_proxy`, `https_proxy`, `all_proxy`, `no_proxy` | Preserve the enclosing host or sandbox's proxy route and bypass list |
| `SSL_CERT_FILE`, `SSL_CERT_DIR`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS` | Preserve standard TLS trust file and directory locations |

Names are matched exactly; upper and lower case values remain independent, including empty
values, and each client applies its own precedence. The check's `env` overrides inherited values
by exact name, including with an empty string. The executor then replaces temporary, cache and
report variables with its own scratch paths as specified in [the boundary](boundary.md). Runtime
injection settings such as `PYTHONPATH`, `PYTHONHOME`, `VIRTUAL_ENV`, `NODE_OPTIONS` and Concorde or
agent session variables are not inherited. Transport values are passed as environment data, never
added to the command line or diagnostic messages.

## Running checks

`run_checks(worktree, *, modules, trace_directory, measured=None, tests=None, python=None,
stage="work", kinds="all")` in `src/concorde/execution/checks/checks.py`:

1. takes the Modules to check from `modules`, as labels that select checks files. Which Modules a
   change concerns, and which Modules use one of them, is the caller's to decide, since it needs
   the Specs: Method's steps select the Modules a change concerns together with every Module that
   uses one of them, directly or through further uses, through the Spec tooling
   ([Method](../../method/module.md#the-standard-worker-sequence)), so a Module's checks run whenever
   code it uses changes;
2. goes through the configured checks in configuration order and keeps a check marked
   `"when": "readiness"` only when `stage` is `readiness`, which `task-validation` and `delivery`
   pass; every other caller leaves the default `work`;
3. keeps an ordinary check when its own Module is selected, and a selective check once, when
   `tests` names some test for the selected Modules, which the caller computes from the tests'
   [verification declarations](../../glossary.json#concept.verification-declaration); `kinds`
   narrows the call to the ordinary checks (`module`) or to the selective ones (`selective`), so
   that a caller can run each Module's own checks separately and the selective checks once for the
   whole selection;
4. for each kept check, computes its measured digest with `measured_digest`, in the same file. For
   an ordinary check it is `check_revision` of the check's own Module: the digest of the files the
   caller names for that Module in `measured`, in Concorde its implementation files, each of its
   checks' definitions, the digest of every file below their inputs, and `CHECK_POLICY`. For a
   selective check it is the digest of that `check_revision` together with the sorted selected
   Modules, the tests it selected and the digest of every file holding one of them;
5. creates the check's [trace node](../../glossary.json#concept.trace-node)
   `<trace_directory>/<check id>/`, writes its `trace.json` with status `running`, runs the check
   through `execute_check` with `worktree` as project root and the default boundary, writes
   `<stdout>\n<stderr>` to `output.log` of the node, preceded for a selective check by the tests it
   selected, and writes `trace.json` again with the check's end; when the boundary refused the
   command, the log holds what it reported, the node ends `failed` with the service's error and the
   call fails with `check_sandbox_unavailable`;
6. computes the measured digest again, over the same named files and selected tests, and fails the
   whole call with `stale_evidence` when it differs;
7. returns one check result per check it ran, in configuration order.

A failure in any step ends the call without results, including those of checks that already ran.
A selected Module without configured checks contributes no result; the caller decides whether that
is acceptable.

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

Every check the service runs is also a trace node of kind `check`, as
[Tracing](../../kernel/tracing/contracts.md#contract.tracing.node) defines it, whose content is this value:

```concorde-contract
{
  "id": "contract.checks.check-trace",
  "version": 1,
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
          "refused"
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
  "semantics": "The data of the typed value concorde-check-trace, the content of one check's trace node. status is the check result's status, or refused when the boundary refused to start the command; exit_code is its exit status, -1 on timeout, null when refused; source_digest is the measured digest taken before the run; argv is the command as run; selected_tests are the tests a selective check selected, empty otherwise. The node's identity is the check identity, its metadata the check and its Module, its status ok for passed and failed otherwise, its outcome the check status, its usage the check's duration, and output.log its artifact with the log digest. A behaviour or field change increments the version.",
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
for the same check and, for a selective check, the same selected Modules, and comparing it with
`source_digest`.

### Errors

Check execution raises its own `CheckError`, whose record carries a code, a message, a reason, a
location, a remediation and causes, with these codes: `invalid_check` (a checks file or entry that
breaks [the format](#checks-files), or a check without a nonempty argv or a positive timeout, with an
`env` that is not an object of variable names to strings, or with a `when` other than `always` or
`readiness`),
`check_input_missing`, `project_python_missing` (a check uses `{python}` but the configuration
names no project interpreter, or none that is an executable file where it was looked for),
`check_sandbox_unavailable` (the read-only boundary cannot be established), `stale_evidence` (an
input changed while the check ran) and `system_error` (an operating-system error). Each carries a
message naming the check or Module concerned, the code's reason, its location, remediation and
causes. Check execution depends on no part but the kernel, so its error type is its own; a caller
never needs to translate it, since `service_error` makes the link.

### Check execution's error as a link

`service_error(error)` turns an error `run_checks` raised into this Module's own link of the
Framework's [error chain](../../kernel/tracing/contracts.md#contract.tracing.error), which every caller keeps
unchanged as a cause under its own link: a run's stop for checks that could not run, the round
validation that runs a worker's checks, and Validation's blocking `check` finding and its
`inputs_changed` stop. The link has the level `component`, the actor `Check execution`, the error's
code, a detail with its message and location, the code's reason as explanation, its remediation as
option and recommendation, and the error's own causes nested the same way. Its unhandled reason
depends on the code:

| Code | Reason |
| --- | --- |
| `check_sandbox_unavailable`, `stale_evidence` | `environment`: the host cannot establish the boundary, or something outside the service changed the input |
| `system_error`: an operating-system error | `environment` |
| any other exception the service did not expect | `capability` |
| every other code of `CheckError` | `input`: the checks files or the Modules named are wrong, and only whoever supplied them can correct them |

### A check that did not pass as an error link

`check_error(result)` turns a check result whose status is not `passed` into the check's link of
the Framework's [error chain](../../kernel/tracing/contracts.md#contract.tracing.error), so every consumer reports
a failing check the same way: the level `check`, the check's identity as actor, the code
`check_failed` or `check_timed_out`, a detail naming the Module, the exit code, the log path and the
last 3,000 bytes of the log, the log as evidence, and the reason `capability`, because a check only
measures the code it runs against.

## Requirements

### req.checks.project-python — Checks run the project's interpreter, never Concorde's

The service SHALL replace `{python}` with the project's interpreter named by the configuration's
`python`.

### req.checks.no-concorde-runtime — A check inherits nothing of Concorde's runtime

The service SHALL NOT give a check any host environment variable other than `PATH`, `LANG` and the
inherited transport variables.

The check's own `env` and the scratch settings of [the boundary](boundary.md) are added to these.

### req.checks.measured-input-unchanged — A check cannot vouch for input that changed

A configured check run SHALL fail with `stale_evidence` when the implementation files, check
inputs or selected tests it measured differ after the run from before it.

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

The check service SHALL describe a check result that did not pass, when a consumer reports it as an error, with its Module, exit code, log path and the end of its log.

### req.checks.no-status-without-run — A refused check has no status

The check service SHALL NOT return a check result for a check whose command the boundary refused to
start.

## Scenarios

### scenario.checks.checks-files — Configured checks are read from one file per Module

- GIVEN a worktree whose `.concorde/checks/` holds `module.b.json` with two checks and `module.a.json` with one
- WHEN Check execution reads the configured checks
- THEN it holds the check of `module.a` first and then those of `module.b` in file order, each carrying the Module its file is named after
- AND a file named after a Module no registry registers is read like any other, since the identity is a label
- BUT a check entry with a `module` field or another field the format does not name, an `id` another file already uses, an input that is not a canonical project-relative path, a file that is not valid JSON or holds another field, or a file not named `<module id>.json` is refused with `invalid_check`, naming the file and what to change

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

- GIVEN a check whose `env` has a name that is not a variable name, such as `not a name`
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

- GIVEN a check whose Module's implementation file changes while the check runs
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
- WHEN the service is asked to run it
- THEN the call fails naming the check, its Module and the path before any command runs
