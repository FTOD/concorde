# Decision log: checks-validation-cleanup

Goal: Developer-approved panel-review decisions for Check execution, Validation and Execution: (validation F4b) include each changed path's Git file mode in the readiness input digest, bumping contract.validation.readiness; (checks F7) a selective check's measured digest includes the selected Module set and the digest of the selected test files; (checks F22) add a helper in checks.py that turns a CheckError into this Module's own error link (level, actor, code, reason specified in service.md) and make every caller (execution RunContext.checks_unavailable, Workers' round, Validation including stale_evidence) keep it as a cause; (checks F20) remove the unused evidence callback of execute_check together with the 2 MiB output limit it switches on; (checks F24) remove the timing library's leftover token counts, operation/invocation_id labels and always-null wall_seconds/server_thinking_seconds from timing.py and timing.md; (execution F7) state the property the runner really gives: the result is written inside the lock, so a run admitted after it finds the result written (fix runner.md, module.md, scenario.execution.workspace-busy and the code comment in runner.py). Specs and tests.

## 2026-09-29 — decisions taken without the developer (task session)

Source of the finding numbers: the spec_panel run r-20260928T052114-spec_panel-cd841742
(module.checks F7, F20, F22, F24; module.validation F4; module.execution F7).

1. **Validation F4b, how the mode enters the digest.** Options: (a) add a `mode` field to every
   `inputs.changed` entry, so the mode is part of the canonical object the input digest covers;
   (b) fold the mode into each path's `digest` string. Chose (a): the readiness then shows the
   measured mode, and the digest rule stays "sha256 of the content". The mode is Git's file mode
   as six octal digits (`100644`, `100755`, `120000` symbolic link, `160000` submodule), taken from
   the worktree with Git's own rule for regular files (the owner's execute bit), or null when the
   path is gone. Derived from `lstat` rather than `git diff --raw`, because untracked paths are
   measured too and Git reports no mode for them; one rule for every path keeps the measurement
   uniform. `contract.validation.readiness` goes from version 3 to 4.
2. **Checks F7, what a selective check's measured digest covers.** Besides its own Module's
   `check_revision`, the sorted selected Modules, the selected test identities and the digest of
   every selected test file. The test identities are included (not only the files) because they
   are the resolved selection the finding names; the same function is used for the before/after
   comparison, so a selected test file changing mid-run is `stale_evidence`. An ordinary check's
   measured digest stays exactly its Module's `check_revision`.
3. **Checks F22, shape of Check execution's own link.** Level `component`, actor
   `Check execution`, the error's own code, its message and location as detail, its code's reason
   as explanation and its remediation as option and recommendation, Spec-core causes nested.
   Unhandled reason: `environment` for `check_sandbox_unavailable`, `stale_evidence` and
   `system_error` (OSError), `capability` for `unexpected_error`, `input` for every other code
   (the check configuration or the named Modules are wrong and only their sender can fix them).
   Level `component` rather than `check`, because `check` is the level of one configured check's
   own link (`check_error`), and the service is a deterministic component the caller called.
   Helper name: `service_error(error)` in `src/concorde/harness/checks.py`.
4. **Checks F20, byte counts.** The `stdout_bytes`/`stderr_bytes` of `CheckResult`,
   `CheckCancelled` and `CheckSandboxError` existed only to count bytes the 2 MiB limit dropped;
   with the limit gone they always equal the stream lengths, so they are removed with it.
5. **Checks F24, which metadata keys go.** The counts `input_tokens`, `output_tokens`,
   `cache_read_tokens`, `cache_write_tokens` and the labels `operation`, `invocation_id` and
   `launch_invocation_id` (the same invocation-id leftover); the summary loses `wall_seconds` and
   `server_thinking_seconds`. The other counts and labels are left, as the approved decision names
   only these.
6. **Scope left out (Execution F7).** `specs/concorde/execution/workflows/module.md` ("a finished
   step always leaves the workspace free for the next") and `req.workflows.one-at-a-time` ("so a
   finished step always leaves the workspace free") repeat the inverted reasoning. They belong to
   module.workflows, outside this task's Modules, so they are unchanged and reported to the main
   agent as open. The Workflows behaviour itself is sound: a step waits for the lock to be free.
7. **Results.** Full suite on the final input: 664 passed, 4 skipped. `uvx` could not write its
   tool directory under the sandbox (read-only `~/.local/share/uv/tools`); ran it with
   `UV_TOOL_DIR` in the session's temporary directory instead. `ruff check` findings in the touched
   files are all pre-existing (compared against the base versions).

## Closed: merged, 2026-09-28T17:30:41Z
