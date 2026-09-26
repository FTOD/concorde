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

### scenario.workers.interrupted-run — An interrupted run still ends

- GIVEN a worker run whose launcher is told the run identity as soon as the run exists
- WHEN the run is interrupted from outside before it returns, such as by a signal
- THEN its run record ends `failed` with the error `interrupted`, of reason `environment`, naming the interruption
- AND its progress file is `finished` with status `failed`
- AND the interruption travels on to the launcher

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

- GIVEN a run started from a pi main session, and an `implement` grant with a `rw` source file, `ro` Specs, a `names` file and an ungranted file
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
- AND bash's temporary files go to the run's private `TMPDIR`, which it can write

### scenario.workers.pi-runtime-missing — A pi run without its runtime is refused

- GIVEN a run started from a pi main session on a machine without the sandbox-runtime package
- WHEN the host is asked to start a worker
- THEN it refuses before launch with `pi_runtime_missing`, naming the missing package and how to install it
- AND it still writes the run record

### scenario.workers.pi-limit — A pi run over its turn limit stops

- GIVEN a pi worker whose turns exceed `max_turns`
- WHEN the permission extension counts the turn
- THEN it aborts the run and records the limit reached
- AND the run ends `failed` with `worker_limit_reached`

## Worker models

### scenario.workers.backend-from-client — Workers run on the main session's program unless configured

- GIVEN a worktree whose worker model configuration has no `backend` section, and a command started from a Claude Code session, one started from a pi session whose Concorde extension set `CONCORDE_CLIENT=pi`, and one started from neither
- WHEN each resolves the worker backend
- THEN the first resolves `claude` from `CLAUDECODE=1` and the second `pi` from `CONCORDE_CLIENT`
- AND the third is refused with `client_unknown`, naming every variable it looked at and how to set one
- BUT a `CONCORDE_CLIENT` naming neither program is refused with `invalid_client`

### scenario.workers.backend-configured — The configuration may choose another program than the main session's

- GIVEN a command started from a Claude Code session, both programs installed, and a worker model configuration whose `backend` section chooses `pi` as its default and `claude` for `spec_review`'s `checker`
- WHEN the backends of `implement`'s worker and of `spec_review`'s `reviewer` and `checker` are resolved
- THEN `implement` and the reviewer resolve `pi` from `backend.default` and the checker `claude` from its role's entry, each naming the entry it came from
- AND each worker's model and level are resolved in the section of its own backend
- AND the same configuration resolved outside any main session gives the same backends, since a configured backend does not need the main session's program to be known
- BUT when the `pi` command is not installed, a worker whose resolved backend is `pi` is refused with `backend_missing`, naming the entry that chose `pi` and the command it looked for, and never runs on Claude Code instead

### scenario.workers.models-listed — The installed program's models are the candidates

- GIVEN pi listing two models with credentials, one of them without reasoning, and Claude Code whose user settings name a model and whose environment pins another
- WHEN Workers lists the candidates of each backend
- THEN the pi listing names both as `provider/model`, the reasoning one with pi's thinking levels and the other with only `off`, and is marked complete
- AND the Claude Code listing names the aliases, the settings' model and the pinned model with Claude Code's effort levels, is marked incomplete and says why
- BUT a backend whose program is not installed is refused with `backend_missing`

### scenario.workers.model-resolution — The most specific entry wins, field by field

- GIVEN a configuration with a default model and level, a model for `spec_review` and a level for its `checker` role
- WHEN the choices of `spec_review`'s checker and reviewer and of `implement`'s worker are resolved
- THEN the checker gets the Operation's model and its own level, the reviewer the Operation's model and the default level, and `implement` the default, each naming the entry it came from
- AND another backend's workers get the program's own default
- AND removing the checker's entry and then the Operation's leaves only the default

### scenario.workers.model-refused — A model or level the program does not offer is refused

- GIVEN pi listing its models
- WHEN a change names a model it does not list, or a level the chosen model does not offer
- THEN it is refused with `unknown_model` or `unknown_level`, naming the value and the models or levels that are listed
- BUT a caller that admits unlisted models may name one

### scenario.workers.model-config-invalid — An unreadable configuration is reported, never ignored

- GIVEN a worktree whose `.concorde/worker-models.json` is not valid JSON or has a field the schema does not know
- WHEN Workers reads it
- THEN it is refused with `config_invalid`, naming the file and what is wrong with it
