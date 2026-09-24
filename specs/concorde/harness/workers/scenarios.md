# Worker run scenarios

The testable situations of one worker run. The [entry](module.md) explains the run, and
[the run mechanics](launch.md) give the exact settings, rounds and records.

## A normal run

### scenario.workers.fenced-run — An implement worker changes only its writable files

- GIVEN a task worktree and an `implement` grant with a `rw` source file, a pending `rw` file, `ro` Specs and a `names` file of another Module
- WHEN the host runs a worker that edits the source file and writes the pending file
- THEN both changes reach the task worktree
- AND the audit is clean, the configured checks run on the task worktree and the run ends `ok`
- AND the run record holds the grant's context identity, the settings and brief digests, the tool set, the transcript path, the round with its audit and check results, and the worker result verbatim

### scenario.workers.pending-precreated — Pending files exist before launch and vanish if unused

- GIVEN a grant whose `rw` list names two files that do not exist yet
- WHEN the host prepares the run
- THEN both files exist and are empty before the worker starts
- AND after the run the one the worker left empty and unchanged is removed again
- BUT the one the worker wrote stays

### scenario.workers.no-ambient-instructions — The brief is the only instruction

- GIVEN a `CLAUDE.md` in the task worktree and in the working directory, and user settings, skills and MCP servers in the user's Claude Code configuration
- WHEN the host launches a worker
- THEN none of them reaches the worker
- AND the worker's environment holds only the listed variables, with `HOME`, `TMPDIR` and `CLAUDE_CONFIG_DIR` inside its run directory

## The boundary

### scenario.workers.undeclared-write-denied — A new undeclared file cannot be written

- GIVEN a running worker
- WHEN it uses Write on a path in the task worktree that is in no grant list
- THEN the write hook denies it with a reason saying the file must first be declared pending through a `specify` task
- AND the file does not appear in the task worktree

### scenario.workers.ro-edit-denied — A read-only file cannot be edited

- GIVEN a running worker whose grant makes a Spec file `ro`
- WHEN it uses Edit on that file
- THEN the edit is denied and the file is unchanged
- BUT Read of the same file succeeds

### scenario.workers.read-denied — Withheld files cannot be read by file tools

- GIVEN a running worker whose grant leaves a file out and makes another `names`
- WHEN it uses Read on either file, or Grep over a directory that holds them
- THEN Read is denied with a generic permission message
- AND Grep returns matches only from files the grant makes readable

### scenario.workers.bash-confined — Bash is confined by the sandbox

- GIVEN a running `implement` worker
- WHEN it uses Bash to read an ungranted file, `.git` or the user's `~/.claude`, to write a `ro` file, to reach the network, or asks to run a command unsandboxed
- THEN the read finds no such file, the write fails as a read-only file system, the network request is refused, and the command still runs sandboxed
- BUT Bash can read `ro` files and write `rw` files

### scenario.workers.bash-new-file-lost — A file Bash creates outside `rw` is lost

- GIVEN a running `implement` worker
- WHEN it uses Bash to create a new file in a directory with no `rw` file
- THEN the command appears to succeed
- BUT the file never reaches the task worktree and the audit sees no change

### scenario.workers.run-directory-denied — A run the deny rules would disable is refused

- GIVEN a grant and a primary worktree whose generated deny rules would cover the run's working, home or temporary directory
- WHEN the host is asked to start the worker
- THEN it refuses before launch with `run_directory_denied`
- AND it still writes the run record

## Audit and deletions

### scenario.workers.audit-violation — A write outside `rw` fails the run

- GIVEN a worker round after which a file outside the grant's `rw` list has changed in the task worktree
- WHEN the host audits the worktree
- THEN the run ends `failed` with `audit_violation` and every violating path as host evidence
- AND no configured check runs and no resume round follows
- BUT the host neither reverts nor commits the change

### scenario.workers.proposed-deletion — The host performs proposed deletions

- GIVEN a worker result whose `proposed_deletions` names one `rw` file and one `ro` file, and a clean audit
- WHEN the run ends
- THEN the host deletes the `rw` file
- AND refuses the `ro` file and records the refusal

## Rounds

### scenario.workers.check-failure-resume — A failing check resumes the same worker

- GIVEN a worker that ended `ok` with a clean audit and a configured check that fails
- WHEN the host starts a resume round
- THEN it resumes the session with the failing check's identity, exit code and log tail
- AND the next round continues from the new session identifier the resume returned
- AND when the checks then pass the run ends `ok` with two rounds recorded

### scenario.workers.rounds-exhausted — Checks that keep failing end the run

- GIVEN a configured check that fails after every round
- WHEN the configured number of resume rounds has been used
- THEN the run ends `failed` with `checks_failed` and the last check results
- AND its error gives `exhausted` as the reason, lists each round's failing checks as attempts and has one cause per failing check with its exit code and the end of its log
- BUT no further round is started

### scenario.workers.blocked-not-resumed — A blocked worker goes to the main agent

- GIVEN a worker that ends `blocked` because its Module's Spec does not state a promise it needs
- WHEN the host finishes the round
- THEN the audit still runs
- BUT no configured check runs, no resume round follows, and the run ends `blocked` with the worker result verbatim
- AND the run's error is the harness's `worker_blocked` link whose one cause is the worker's own error, unchanged, with the level `worker`

## Host failures

### scenario.workers.timeout — A round past its deadline is killed

- GIVEN a worker still running at its round's timeout
- WHEN the deadline passes
- THEN the host kills the worker's whole process group
- AND the run ends `failed` with `worker_timeout` and a run record

### scenario.workers.invalid-result — A worker without a valid result has failed

- GIVEN a worker that exits without a structured result that satisfies the worker result schema
- WHEN the host reads its output
- THEN the run ends `failed` with `worker_result_invalid` and the schema violation or the worker's final text in its error
- AND the stderr tail and transcript path are in the run record
- AND a `blocked` or `failed` result without an error, or an `ok` result with one, is invalid too

### scenario.workers.claude-error — An error of Claude Code itself is reported with its cause

- GIVEN a worker whose Claude Code session ends with an error subtype, such as the turn limit, instead of a structured result
- WHEN the host reads its output
- THEN the run ends `failed` with `worker_limit_reached` for a turn or budget limit and `claude_failed` otherwise
- AND the error's cause is the Claude Code process's link with the subtype, the turn count, the cost, the final text and the tail of standard error

## The pi backend

### scenario.workers.pi-fenced-run — A pi worker is fenced by the same grant

- GIVEN a project whose configuration selects the pi backend, and an `implement` grant with a `rw` source file, `ro` Specs, a `names` file and an ungranted file
- WHEN the host runs a pi worker that reads the Specs, edits the source file and ends with `concorde_result`
- THEN the edit reaches the task worktree, the audit is clean and the run ends `ok` with the worker result verbatim
- AND the run record holds the session identifier, the transcript path and the tool set of the pi backend

### scenario.workers.pi-file-tools-denied — pi file tools explain every denial

- GIVEN a running pi worker
- WHEN it reads a `names` file, an ungranted file, `.git` or a file of the run's `config/`, or writes a `ro` file or an undeclared file
- THEN each call is denied with the reason the read or write table gives, prefixed `Concorde grant:`
- AND no file changes

### scenario.workers.pi-commands-sandboxed — pi commands see only the grant

- GIVEN a running pi `implement` worker
- WHEN it greps a directory holding ungranted files, or uses bash to read an ungranted file, to write a `ro` file or to reach the network
- THEN grep reports matches only from readable files, the bash read finds no such file, the write fails as a read-only file system and the network request is refused
- BUT bash can read `ro` files and write `rw` files

### scenario.workers.pi-runtime-missing — A pi run without its runtime is refused

- GIVEN a project that selects the pi backend on a machine without the sandbox-runtime package
- WHEN the host is asked to start a worker
- THEN it refuses before launch with `pi_runtime_missing`, naming the missing package and how to install it
- AND it still writes the run record

### scenario.workers.pi-limit — A pi run over its turn limit stops

- GIVEN a pi worker whose turns exceed `max_turns`
- WHEN the permission extension counts the turn
- THEN it aborts the run and records the limit reached
- AND the run ends `failed` with `worker_limit_reached`
