# Validation scenarios

These situations show how [Validation](module.md) behaves. The obligations they demonstrate are
defined once in [Validation requirements](requirements.md).

### scenario.validation.ready — A candidate that meets every gate becomes ready

- GIVEN a candidate whose accepted tasks are complete, or a direct candidate with no planned work
- AND every review the change requires is current
- WHEN the user session calls `concorde-validate` in the candidate's worktree
- THEN the Host validates the Specs and runs the configured checks of every affected Module in the sandbox
- AND records the evidence bound to the candidate's exact files
- AND answers with outcome `ready` and marks the candidate ready with its validated tree
- BUT the answer does not claim semantic completeness

### scenario.validation.blocked — A failed, missing or stale gate blocks readiness

- GIVEN a candidate whose configured check fails, whose recorded check result no longer matches its current files, whose required review is not current, or whose accepted tasks are unfinished
- WHEN readiness is evaluated
- THEN the candidate is not recorded ready
- AND the answer names the failing check or the unmet gate
- BUT the candidate's files stay unchanged for inspection

### scenario.validation.check-isolation — A check cannot write its inputs or the Host's records

- GIVEN a configured check and the current candidate
- WHEN validation runs the check
- THEN every write the check attempts in the project, including to the change status and run logs, is denied
- AND the Host outside the sandbox saves the private log and records `passed`, `failed` or `timeout` with the exit code and digests
- AND a changed check input, candidate tree or affected Module revision is still detected and rejected
- BUT when the sandbox cannot be set up, validation stops with `check_sandbox_unavailable` and records no passing result

### scenario.validation.pending-confirmed — Validation confirms created pending files first

- GIVEN a candidate whose Specs declare some realization entries as pending
- AND the change created the files of some of those entries
- WHEN `concorde-validate` runs in the candidate
- THEN the Host removes those entries from their `pending` lists before validating the Specs
- AND the entries whose files are still missing stay pending
- BUT no reading document changes and every entry stays bound
