# Worker run scenarios

The testable situations of one worker run. The [entry](module.md) explains the run, and
[the run mechanics](launch.md) give the exact settings, rounds and records.

## A normal run

### scenario.workers.fenced-run — An implement worker changes only its writable files

- GIVEN a worktree and an `implement` grant with a `rw` source file, a pending `rw` file, `ro` Specs and a `names` file of another [Module](../../glossary.json#concept.module)
- WHEN the host runs a worker that edits the source file, writes the pending file, changes nothing else and ends with a valid `ok` result
- THEN both changes reach the worktree
- AND the audit is clean, the [configured checks](../../glossary.json#concept.configured-check) run on the worktree, and when they pass the run ends `ok`
- AND the [run record](../../glossary.json#concept.run-record) holds the grant's [context identity](../../glossary.json#concept.context-identity), the settings and brief digests, the tool set, the transcript path and the [worker result](../../glossary.json#concept.worker-result) verbatim, and the round's node below it its audit, [check results](../../glossary.json#concept.check-result), standard error and the tokens, cost and turns the agent program reported

### scenario.workers.pending-precreated — Pending files exist before launch and vanish if unused

- GIVEN a grant whose `rw` list names two files that do not exist yet
- WHEN the host prepares the run
- THEN both files exist and are empty before the worker starts
- AND after the run the one the worker left empty and unchanged is removed again
- BUT the one the worker wrote stays

### scenario.workers.no-ambient-instructions — The brief is the only instruction

- GIVEN a `CLAUDE.md` in the worktree and in the working directory, and user settings, skills and MCP servers in the user's Claude Code configuration
- WHEN the host launches a worker
- THEN none of them reaches the worker
- AND the worker's environment holds only the listed variables, with `HOME`, `CLAUDE_CONFIG_DIR` and `TMPDIR` inside its [runtime directory](../../glossary.json#concept.runtime-directory)

### scenario.workers.session-proxy — A worker started in a task session uses the session's proxy

- GIVEN a host environment whose `HTTP_PROXY`, `HTTPS_PROXY`, `http_proxy` and `https_proxy` name a proxy on `localhost` and whose `NO_PROXY` lists `localhost`, `127.0.0.1`, `::1` and a private address range, as a [task session](../../glossary.json#concept.task-session)'s sandbox sets them
- WHEN the host launches a worker, on the pi backend or the Claude Code backend
- THEN the worker's environment holds the same four proxy variables
- AND its `NO_PROXY` still lists the private range but no loopback entry
- AND it holds no other proxy variable, such as `ALL_PROXY`

### scenario.workers.own-proxy — A proxy elsewhere keeps loopback direct, and no proxy passes nothing

- GIVEN a host environment whose `HTTPS_PROXY` names a proxy on another host and whose `NO_PROXY` lists `localhost` and a domain
- WHEN the host launches a worker
- THEN the worker's environment holds that `HTTPS_PROXY` and the same `NO_PROXY`
- BUT when the host's environment sets no proxy, the worker's environment holds no proxy variable and no `NO_PROXY`, even when the host sets `NO_PROXY`

### scenario.workers.brief-terms — The brief carries the definitions of the worker's terms

- GIVEN a grant whose terms hold the glossary entries the bound Modules' documents link
- WHEN the host launches the worker
- THEN the brief lists each term with its identity, owner and definition
- AND when the glossary is writable it says that only the bound Modules' entries may change
- BUT it lists no entry outside the grant's terms

## The boundary

### scenario.workers.undeclared-write-denied — A new undeclared file cannot be written

- GIVEN a running worker
- WHEN it uses Write on a path in the worktree that is in no grant list
- THEN the [write hook](../../glossary.json#concept.write-hook) denies it with a reason saying the path is not in this task's grant, that a file no Module declares must first be declared pending through a `specify` task and that a file another Module declares needs that Module bound
- AND the file does not appear in the worktree

### scenario.workers.ro-edit-denied — A read-only file cannot be edited

- GIVEN a running worker whose grant makes a [Spec](../../glossary.json#concept.spec) file `ro`
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
- BUT the file never reaches the worktree and the audit sees no change

### scenario.workers.run-directory-denied — A run the deny rules would disable is refused

- GIVEN a grant and a primary worktree whose generated [deny rules](../../glossary.json#concept.deny-rules) would cover the run's working, home or temporary directory
- WHEN the host is asked to start the worker
- THEN it refuses before launch with `run_directory_denied`
- AND it still writes the run record

### scenario.workers.malformed-grant-refused — A malformed grant is refused before launch

- GIVEN a grant whose entries are not a list, or with an entry that is not an object, has no path, an absolute path or one leaving the task worktree through `..`, or a level other than `rw`, `ro` and `names`
- WHEN the host is asked to start the worker, or generates its settings
- THEN settings generation raises `grant_malformed` naming the entry and what is wrong with it
- AND the host refuses before launch with `grant_malformed` and the reason `input`, generating no settings or write hook
- AND it still writes the run record

## Audit and deletions

### scenario.workers.audit-violation — A write outside `rw` fails the run

- GIVEN a worker round after which a file outside the grant's `rw` list has changed in the worktree
- WHEN the host audits the worktree
- THEN the run ends `failed` with `audit_violation` and every violating path as host evidence
- AND no configured check runs and no [resume round](../../glossary.json#concept.resume-round) follows
- BUT the host neither reverts nor commits the change

### scenario.workers.glossary-entries — A worker changes only its Modules' glossary entries

- GIVEN a `specify` worker bound to Module A, whose grant makes the project glossary writable
- WHEN the worker changes the glossary entry of a concept A owns
- THEN the audit accepts the change
- BUT when it changes an entry Module B owns, the run ends `failed` with `audit_violation`, naming the glossary, the entry and its owner before and after as the violation

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

- GIVEN a worker that changes nothing outside its `rw` list and ends `blocked` because its Module's Spec does not state a promise it needs
- WHEN the host finishes the round
- THEN the audit still runs and is clean
- BUT no configured check runs, no resume round follows, and the run ends `blocked` with the worker result verbatim
- AND the run's error is Workers' `worker_blocked` link, of level `workers`, whose one cause is the worker's own error, unchanged, with the level `worker`

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
- AND its [progress file](../../glossary.json#concept.progress-file) is `finished` with status `failed`
- AND the interruption travels on to the launcher

### scenario.workers.invalid-result — A worker without a valid result has failed

- GIVEN a worker that exits without a structured result that satisfies the worker result schema
- WHEN the host reads its output
- THEN the run ends `failed` with `worker_result_invalid` and the schema violation or the worker's final text in its error
- AND the round's standard error is its `stderr.log` and the transcript path is in the run record
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
- THEN the edit reaches the worktree, the audit is clean and the run ends `ok` with the worker result verbatim
- AND the run record holds the session identifier, the transcript path and the tool set of the pi backend

### scenario.workers.pi-file-tools-denied — pi file tools explain every denial

- GIVEN a running pi worker
- WHEN it reads a `names` file, an ungranted file, `.git` or a file of its runtime directory's `config/`, or writes a `ro` file or an undeclared file
- THEN each call is denied with the reason the Harness's read or write table gives, prefixed `Concorde grant:`
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

### scenario.workers.pi-settings-independent — A pi worker takes nothing from the user's pi settings

- GIVEN the user's pi settings choosing a default provider, model and thinking level, enabled models, per-model thinking levels, packages and other settings, and then a settings file pi would refuse
- AND a [worker configuration](../../glossary.json#concept.worker-configuration) that chooses a model and a level for a pi worker
- WHEN the host prepares the worker's runtime directory and launches it
- THEN its generated pi settings hold only `defaultProjectTrust` `never`, in both cases, and the run is not refused
- AND the worker is launched with the configured model and level as `--model` and `--thinking`
- AND its pi configuration directory holds copies of the user's `auth.json` and `models.json`

### scenario.workers.pi-limit — A pi run over its turn limit stops

- GIVEN a pi worker whose turns exceed `max_turns`
- WHEN the [permission extension](../../glossary.json#concept.permission-extension) counts the turn
- THEN it aborts the run and records the limit reached
- AND the run ends `failed` with `worker_limit_reached`

## Worker models

### scenario.workers.backend-from-client — The main session's program is read from the environment

- GIVEN a command started from a Claude Code session, one started from a pi session whose Concorde extension set `CONCORDE_CLIENT=pi`, and one started from neither
- WHEN each reads the main session's program, as a [task session](../../glossary.json#concept.task-session) does
- THEN the first reads `claude` from `CLAUDECODE=1` and the second `pi` from `CONCORDE_CLIENT`
- AND the third is refused with `client_unknown`, naming every variable it looked at and how to set one
- BUT a `CONCORDE_CLIENT` naming neither program is refused with `invalid_client`

### scenario.workers.backend-configured — Workers run on pi unless their configuration chooses Claude Code

- GIVEN a command started from a Claude Code session, both programs installed, and a [worker configuration](../../glossary.json#concept.worker-configuration) whose default gives a pi model and which puts `spec_review`'s worker `checker` on `claude` with a Claude Code model and a level
- WHEN the choices of `spec_review`'s `reviewer` and `checker` are resolved
- THEN the reviewer runs on pi with the default's model
- AND the checker runs on `claude` with the model and level of its own entry

### scenario.workers.backend-default — Without a configuration entry a worker runs on pi

- GIVEN a command started from a Claude Code session and a worker configuration whose default names only a model
- WHEN the choice of `implement`'s worker is resolved
- THEN it runs on `pi`, from Concorde's default [worker backend](../../glossary.json#concept.worker-backend), not from the main session's program

### scenario.workers.backend-missing — A worker whose backend is not installed is refused

- GIVEN a command started from a Claude Code session, a worker configuration that puts `spec_review`'s worker `checker` on `claude`, and no `pi` command installed
- WHEN the choices of `implement`'s worker and of `spec_review`'s `checker` are resolved
- THEN the worker that runs on pi is refused with `backend_missing`, naming the worker, the source of its backend, the command it looked for and how to choose Claude Code for it
- AND it never runs on Claude Code instead
- BUT the checker, on `claude`, still resolves

### scenario.workers.models-listed — The installed program's models are the candidates

- GIVEN pi listing two models with credentials, one of them without reasoning, and Claude Code whose user settings name a model and whose environment pins another
- WHEN Workers lists the candidates of each backend
- THEN the pi listing names both as `provider/model`, the reasoning one with pi's thinking levels and the other with only `off`, and is marked complete
- AND the Claude Code listing names the aliases, the settings' model and the pinned model with Claude Code's effort levels, is marked incomplete and says why
- BUT a backend whose program is not installed is refused with `backend_missing`

### scenario.workers.model-resolution — The most specific entry wins, field by field

- GIVEN a configuration with a default model and level, a model for `spec_panel`'s default, a model for its worker `reviewer2` and a level for its worker `chair`
- WHEN the choices of `reviewer1`, `reviewer2`, `chair` and `implement`'s `worker` are resolved
- THEN `reviewer1` gets the [Operation](../../glossary.json#concept.operation)'s model and the default level, `reviewer2` its own model, the `chair` the Operation's model and its own level, and `implement` the default, each naming the entry it came from

### scenario.workers.model-levels — A model's own level applies when the entry that chose it sets none

- GIVEN `enabled_models` giving two models a level of their own and a third none, a default naming the first model without a level, a level for `spec_panel`'s default, and `spec_panel` workers naming the second model without a level, the second model with a level, and the third model
- WHEN the choices are resolved
- THEN a worker on the default gets its model's own level, and a worker with no entry of its own in `spec_panel` the Operation's level
- AND a worker whose entry names the second model without a level gets that model's own level, and one whose entry sets a level its own
- AND the worker on the third model keeps the Operation's level, and a worker with no level anywhere gets none, which leaves its program's built-in default
- BUT a model's own level of neither backend, or one the backend of a worker taking it does not have, is refused with `config_invalid`

### scenario.workers.model-unresolved — A worker whose configuration names no model is refused

- GIVEN a worker configuration whose default sets only a level, which names a model for `spec_review`'s default and puts `spec_panel`'s `chair` on `claude` without a model
- WHEN the choices of `spec_review`'s `checker`, `implement`'s worker and `spec_panel`'s `chair` are resolved
- THEN the checker gets the model of its Operation's default
- AND `implement`'s worker and the chair are refused with `model_unresolved`, naming the worker, every entry its model may come from and how to set one, and saying that no program's or developer's default model is used

### scenario.workers.model-refused — Validation admits custom models but rejects invalid entries

- GIVEN a configuration with a custom model absent from discovery
- WHEN the shared validator checks it without installed backends or credentials
- THEN the custom model is accepted
- BUT invalid structure, unknown Operation or worker names, malformed `enabled_models` entries and reasoning outside the effective backend's vocabulary are refused with `config_invalid`

### scenario.workers.model-not-enabled — A model outside the enabled models is refused

- GIVEN a worker configuration whose `enabled_models` admits two models
- WHEN the default, an Operation's default or a worker's entry names a third model
- THEN the whole configuration is refused with `model_not_enabled`, naming the entry, the model, the enabled models and how to repair it
- BUT a configuration without `enabled_models`, or with an empty one, is refused with `config_invalid` saying that the list is required

### scenario.workers.config-missing — A worktree without a worker configuration runs no worker

- GIVEN a worktree without `.concorde/workers.json`
- WHEN Workers reads the worker configuration for a launch
- THEN it is refused with `config_missing`, naming the file, what it must hold and that it must be committed
- AND it says that a worker's model is never taken from the developer's own pi or Claude Code settings

### scenario.workers.model-config-invalid — An unreadable configuration is reported, never ignored

- GIVEN a worktree whose `.concorde/workers.json` is not valid JSON or has a field the schema does not know
- WHEN Workers reads it
- THEN it is refused with `config_invalid`, naming the file and what is wrong with it
- AND a file of another schema version is refused the same way, naming the version it expects

### scenario.workers.limits-configured — Limits and runtime paths come from the worker configuration

- GIVEN a worktree whose `.concorde/workers.json` sets neither `limits` nor `runtime`, and then one that sets `limits.max_turns` and `limits.rounds` and a `runtime` list
- WHEN Workers reads the limits and runtime paths of a launch
- THEN the first gets the default limits and the runtime paths `.venv` and `node_modules`
- AND the second gets its own `max_turns`, `rounds` and runtime paths, with the default for every limit it does not set

### scenario.workers.retired-configuration — The untracked configuration of earlier versions is refused, not ignored

- GIVEN a worktree that has the untracked `.concorde/worker-models.json` of earlier versions and no `.concorde/workers.json`
- WHEN Workers reads the worker configuration
- THEN it is refused with `config_invalid`, naming both files and saying to move the models into `.concorde/workers.json`, commit it and delete the old file
- BUT once `.concorde/workers.json` exists, it is the configuration read

## Discovering models

### scenario.workers.models-standalone — Discovery works outside a worktree

- GIVEN a directory outside Git with configured agent programs
- WHEN `python3 scripts/available_models.py --backend pi` or `--backend claude` runs, with optional `--json`
- THEN it lists configured candidates with sources and reasoning levels, explaining that no inference API access was probed
- AND pi uses its credentialed listing while Claude's aliases and settings-derived list is explicitly incomplete
- BUT a missing program or failed listing returns a discovery error without gating custom/offline configuration

## What a run leaves

### scenario.workers.trace-left — A worker run leaves its trace and no credentials

- GIVEN an Operation run whose worker needs two rounds, the first failing a configured check, on a backend whose configuration holds a credential copy
- WHEN the run ends
- THEN the run's node holds `workers/<run-id>/` with `trace.json`, `status.json`, `grant.json`, `brief.md`, `transcript.jsonl` and `rounds/1/` and `rounds/2/`, each round with its own `trace.json`, `stderr.log` and check nodes
- AND each round's usage holds the tokens, cost and turns the agent program reported for it
- AND the runtime directory, with the credential copy, no longer exists
- AND the worker run's `trace.json` was already there, `running`, while the worker ran
