# Check execution scenarios

Concrete situations for the [requirements](requirements.md) of Check execution.

## The read-only check boundary

### scenario.harness.check-read-only — A project change is refused at the system call

- GIVEN a command running inside the read-only check boundary
- WHEN it or a descendant tries to create, modify, delete or rename a project file, or to modify one and restore it
- THEN the operating system refuses the operation before any project byte or directory entry changes
- AND another path name, an inherited descriptor or a remount in a nested namespace does not make the project writable

### scenario.harness.check-scratch — A run can read its inputs and write disposable output

- GIVEN a command and an available temporary directory outside the project
- WHEN the Host runs it
- THEN project reads and writes to the issued temporary, cache and report directories succeed
- AND repeated runs receive separate scratch directories, each removed after its run
- AND an ambient temporary path inside the project never becomes a writable mount
- AND a tester command gets a private `/tmp` backed by its scratch and reads the host's existing `/tmp` only through its read-only view
- AND the project's and runtime's own paths under the host's `/tmp` stay readable at their names, while an ordinary configured check keeps the default boundary

### scenario.harness.check-result — Output and exit status return to the Host

- GIVEN a command that writes to standard output and standard error and exits with a given code
- WHEN its run finishes
- THEN the runner returns both byte streams and that exit code, with signal endings reported as 128 plus the signal
- AND large output on both pipes is drained without blocking the command
- AND no project log file is ever handed to the command

### scenario.harness.check-unavailable — Without the boundary nothing runs

- GIVEN an unsupported platform, a missing trusted bubblewrap, a denied namespace setup or an unsupported project location
- WHEN the Host asks to run a check or a tester command
- THEN the run is refused with a sandbox error carrying the Host-side diagnostics
- AND no ordinary subprocess runs the command instead

### scenario.harness.check-lifetime — Descendants end with their run

- GIVEN a command that starts detached descendants
- WHEN the initial command completes, fails or passes its deadline
- THEN the Host terminates every descendant before returning and only then removes the scratch
- AND a timeout returns the partial output marked as timed out instead of a successful result

## Configured checks

### scenario.checks.stale-measurement — A check that changes its input fails

- GIVEN a Module with configured checks and the digest of its implementation files and check inputs
- WHEN the checks run and the digest differs afterwards
- THEN the run fails with `stale_evidence`
- BUT the logs already written stay in the primary worktree's run directory for inspection

### scenario.checks.run-checks-tool — An Agent sees check status and a log tail

- GIVEN a programmer or code reviewer whose Agent has `run_checks`
- WHEN it calls the tool
- THEN the Host runs every configured check of the selected Module inside the boundary
- AND the Agent receives each check's identity, status, exit code and the last 20,000 bytes of its log
- BUT an unavailable boundary fails the tool call instead of running the checks another way

## Tester evidence

### scenario.checks.tester-evidence — Export a tester command's evidence before cleanup

- GIVEN a tester command with named reports and a primary worktree
- WHEN the command finishes, fails, times out or is cancelled
- THEN the Host exports the bounded output and each named report that is a regular file below the reports directory to a new run directory in the primary worktree, with a manifest recording digests, sizes, truncation and errors
- AND the manifest records the command's digest, the worktree's branch, commit and dirty state and the runtime provenance, never the command text
- AND the export is complete only when every requested report and output byte was exported and the command ran to an exit
- AND an incomplete export fails the tool even when the command exited with zero
- BUT a missing primary worktree fails the export instead of writing elsewhere
