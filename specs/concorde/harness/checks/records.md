# Configured checks and tester evidence

The exact declarations, flow and records of configured checks and tester commands, and the
requirements and scenarios they serve. The [entry](module.md#concept.checks.configured-check)
explains why they are shaped this way; [the boundary](boundary.md) gives the runner they use.

## Declaring a configured check

The project configuration lists checks under `checks`. Each has:

| Field | Meaning |
| --- | --- |
| `id` | The check's identity, unique in the project |
| `module` | The Module the check belongs to |
| `argv` | The command as an argument list; a first element `{python}` is replaced by the Host's interpreter |
| `timeout_seconds` | A positive time limit |
| `inputs` | Project-relative files or directories the result depends on, beyond the Module's own implementation files |

`PYTHONPATH` points at the Framework's `src/`. An input that is missing, a symbolic link or not a
regular file stops the run before any command and names the check, its Module and the path.

## Running a Module's checks

`configured_checks(repository, target, invocation_id)` in `src/concorde/harness/checks.py`:

1. computes `check_revision`: the digest of the Module's implementation digest, each check's
   definition, the digest of every file below its inputs, and `CHECK_POLICY`;
2. runs each of the Module's checks in order through `execute_check` with the default boundary;
3. writes `<stdout>\n<stderr>` to `.concorde/runs/<invocation>/<check id>.log` in the primary
   worktree, also when the boundary refused the command, and then fails a refused run with
   `check_sandbox_unavailable`;
4. returns one check result per check;
5. computes `check_revision` again and fails the whole call with `stale_evidence` when it differs.

`check_service(repository, target, invocation_id)` returns the `run_checks` handler: it reloads the
repository, runs `configured_checks` and adds each log's last 20,000 bytes as `output_tail`.

### Check result

| Field | Meaning |
| --- | --- |
| `check_id` | The configured check |
| `target_id` | The Module the check belongs to |
| `status` | `passed` (exit code 0), `failed` (any other exit code) or `timeout` |
| `exit_code` | The exit status, `-1` on timeout |
| `source_digest` | The `check_revision` measured before the run |
| `log_digest` | The digest of the saved log |

A consumer decides whether a stored check result is still current by recomputing `check_revision`
for the same Module and comparing it with `source_digest`.

## Tester commands and evidence

The Pi session's bridge calls `execute_check` with `private_tmp=True`, `/bin/bash -c <command>` as
the command, the tester's worktree as project root and an `evidence` callback built from
`CheckEvidence`; it passes the command's `timeout` (1 to 3,600 seconds) and at most sixteen unique
report names of 1 to 240 characters. Cancellation sets `cancel_event` and never interrupts cleanup or
export.

`CheckEvidence` in `src/concorde/harness/check_evidence.py` exports into
`.concorde/runs/tester-<32 hex digits>/` of the Git-identified primary worktree, using the primary
run writer (atomic, mode 0600, repository lock):

| Item | Rule |
| --- | --- |
| Report names | Canonical relative names below the reports directory; each opened only as a regular file with one link, through non-symlink directories, and rechecked for change |
| Report bounds | First 2 MiB of each report, 8 MiB in total, in request order |
| Output | The retained last 2 MiB of each stream, with its total observed byte count |
| Manifest | `schema_version` 1, execution and tool call identity, source worktree, command digest, timeout, requested reports, Python and runtime root, selection digests when bound, observed branch, commit and dirty tree, return code, timeout, cancellation, exception text, each artifact's digest, size, available and captured bytes and portion, errors, `artifacts_complete` and `complete` |

`artifacts_complete` holds when every requested artifact and observed output byte was exported;
`complete` additionally requires no timeout, no cancellation and a started command. A failed
artifact write keeps the others and is listed as an error; if the manifest itself cannot be written,
the response still carries the artifact references and the errors. Nothing else from the scratch,
the environment or the session is archived. The response carries the manifest's path, digest and
size, the execution identity, counts and truncation flags, and the last 20,000 bytes of each stream;
a reader verifies the manifest's digest and then each artifact's bytes.

## Requirements

### req.checks.measured-input-unchanged — A check cannot vouch for input that changed

A configured check run SHALL fail with `stale_evidence` when the implementation files or check
inputs it measured differ after the run from before it.

### req.checks.logs-in-primary — Check output stays with the Host

The Host SHALL save every configured check's log only in the primary worktree's run directory of
the invocation that ran it.

An Agent sees at most the bounded tail that `run_checks` returns.

### req.checks.tester-evidence-honest — Tester evidence is complete only when it is

The Host SHALL mark tester evidence complete only when every requested report and every observed
output byte was exported and the command neither timed out, was cancelled nor failed to start.

## Scenarios

### Configured checks

#### scenario.checks.configured-run — Run a Module's checks and record their results

- GIVEN a Module with configured checks whose inputs are readable
- WHEN the Host runs its checks inside the boundary
- THEN each check's log is saved in the primary worktree's run directory
- AND the Host returns one check result per check with its status, exit code, measured digest and log digest

#### scenario.checks.stale-measurement — A check that changes its input fails

- GIVEN a Module with configured checks and the digest of its implementation files and check inputs
- WHEN the checks run and the digest differs afterwards
- THEN the run fails with `stale_evidence`
- BUT the logs already written stay in the primary worktree's run directory for inspection

#### scenario.checks.invalid-input — An unusable input stops the run

- GIVEN a configured check whose input path is missing, a symbolic link or not a regular file
- WHEN the Host would run the Module's checks
- THEN the run fails naming the check, its Module and the path
- BUT no command starts

#### scenario.checks.sandbox-refused — A refused boundary fails the configured run

- GIVEN a platform on which the boundary cannot be established
- WHEN the Host runs a Module's configured checks
- THEN it saves the refusal's diagnostics as the check's log and fails with `check_sandbox_unavailable`
- BUT no check result claims a status for that check

#### scenario.checks.run-checks-tool — An Agent sees check status and a log tail

- GIVEN an Agent call whose definition lists `run_checks`
- WHEN the Agent calls the tool
- THEN the Host runs every configured check of the selected Module inside the boundary
- AND the Agent receives each check result with the last 20,000 bytes of its log

### Tester evidence

#### scenario.checks.tester-evidence — Export a tester command's evidence before cleanup

- GIVEN a tester command with named reports and a primary worktree
- WHEN the command exits
- THEN the Host exports the bounded output and each named report that is a regular file below the reports directory to a new run directory in the primary worktree
- AND the manifest records digests, sizes and truncation, the command's digest, the worktree's branch, commit and dirty state and the runtime provenance, never the command text
- AND the export is marked complete when every requested report and output byte was exported

#### scenario.checks.tester-evidence-incomplete — An incomplete export is not success

- GIVEN a tester command whose report is missing, not a regular file, too large, or unwritable, or which timed out or was cancelled
- WHEN the Host exports its evidence
- THEN the manifest lists each error and truncation and is marked incomplete
- AND the tool fails even when the command exited with zero

#### scenario.checks.tester-no-primary — Without a primary worktree nothing is exported

- GIVEN a tester command run where no primary worktree can be identified
- WHEN the Host would export its evidence
- THEN the export fails with the command's original result attached
- BUT nothing is written anywhere else
