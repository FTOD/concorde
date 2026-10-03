# Worker run scenarios

The testable situations of one worker run. The [entry](module.md) explains the run, and
[the run mechanics](launch.md) give the exact settings, rounds and records.

## A normal run

### scenario.workers.fenced-run — An implement worker changes only its writable files

- GIVEN a worker on the Claude Code backend, a worktree and an `implement` grant with a `rw` source file, a `rw` directory, `ro` Specs and a source file of another [Module](../../glossary.json#concept.module), `ro` since an `implement` worker reads the project's whole code
- WHEN the host runs a worker that edits the source file, creates a new file inside the directory, changes nothing else and ends with a valid `ok` result
- THEN both changes reach the worktree
- AND the audit is clean, the caller's round validation runs the [configured checks](../../glossary.json#concept.configured-check) on the worktree, as Concorde's does, and when they pass the run ends `ok`
- AND the [run record](../../glossary.json#concept.run-record) holds the grant's [context identity](../../glossary.json#concept.context-identity), the settings and brief digests, the tool set, the transcript path and the [worker result](../../glossary.json#concept.worker-result) verbatim, and the round's node below it its audit, the round validation's evidence with the [check results](../../glossary.json#concept.check-result), standard error and the tokens, cost and turns the agent program reported

### scenario.workers.no-precreation — The host creates no file before launch

- GIVEN a grant whose `rw` list names a file and a directory
- WHEN the host prepares the run and the worker changes nothing
- THEN the worktree after the run holds exactly the files it held before the run, with the same content

### scenario.workers.no-ambient-instructions — The brief is the only instruction

- GIVEN a worker on the Claude Code backend, a `CLAUDE.md` in the worktree and in the working directory, and user settings, skills and MCP servers in the user's Claude Code configuration
- WHEN the host launches a worker
- THEN none of them reaches the worker
- AND the worker's environment holds only the listed variables, with `HOME`, `CLAUDE_CONFIG_DIR` and `TMPDIR` inside its [runtime directory](../../glossary.json#concept.runtime-directory)

### scenario.workers.session-proxy — A worker started behind a loopback proxy uses that proxy

- GIVEN a host environment whose `HTTP_PROXY`, `HTTPS_PROXY`, `http_proxy` and `https_proxy` name a proxy on `localhost` and whose `NO_PROXY` lists `localhost`, `127.0.0.1`, `::1` and a private address range, as an enclosing loopback proxy, such as a sandboxed [main agent](../../glossary.json#concept.main-agent)'s session, sets them
- WHEN the host launches a worker, on the pi backend or the Claude Code backend
- THEN the worker's environment holds the same four proxy variables
- AND its `NO_PROXY` still lists the private range but no loopback entry
- AND it holds no other proxy variable, such as `ALL_PROXY`

### scenario.workers.own-proxy — A proxy elsewhere keeps loopback direct

- GIVEN a host environment whose `HTTPS_PROXY` names a proxy on another host and whose `NO_PROXY` lists `localhost` and a domain
- WHEN the host launches a worker
- THEN the worker's environment holds that `HTTPS_PROXY` and the same `NO_PROXY`

### scenario.workers.no-proxy — Without a proxy on the host no proxy variable passes

- GIVEN a host environment that sets no proxy variable to a non-empty value but sets `NO_PROXY`
- WHEN the host launches a worker
- THEN the worker's environment holds no proxy variable and no `NO_PROXY`

### scenario.workers.brief-terms — The brief carries the definitions of the worker's terms

- GIVEN a `specify` grant that makes the project glossary writable and whose terms hold the glossary entries the bound Modules' documents link
- WHEN the host launches the worker
- THEN the brief lists each term with its identity, owner and definition
- AND it says that only the bound Modules' entries of the glossary may change
- BUT it lists no entry outside the grant's terms

### scenario.workers.brief-result-paths — The brief asks for relative paths in the result

- GIVEN a worker of any [task type](../../glossary.json#concept.task-type) in the task worktree
- WHEN the host launches the worker
- THEN its brief names the task worktree's absolute path and tells it to give its tools absolute paths
- AND it tells it to write every path of the task worktree in its result relative to the worktree, never as an absolute path

### scenario.workers.brief-review-gaps — A Spec reviewer reports a gap and goes on

- GIVEN a worker of task type `review-spec` or `review-architecture`
- WHEN the host writes its brief
- THEN the brief tells it to report a promise the Spec does not state, or a document it lacks, as a finding and to go on reviewing
- AND to return `blocked` only when it cannot review at all
- BUT a `specify`, `implement` or `test` worker is told to return `blocked` for a promise the Spec does not state

### scenario.workers.project-interpreter — The project's interpreter comes first and is named

- GIVEN a request naming the project's interpreter, such as the worktree's `.venv/bin/python`, on the Claude Code backend or the pi backend
- WHEN the host launches the worker
- THEN the worker's `PATH` starts with the interpreter's directory, followed by the host's own `PATH`
- AND the brief names the interpreter as the one to run the project's code and tests with
- BUT the host's own `PATH` is unchanged

### scenario.workers.runtime-paths-readable — Host material the caller lists is readable, never writable

- GIVEN a request whose runtime paths list a folder of check logs outside the worktree and a `.venv` inside it
- WHEN the host prepares the worker on the Claude Code backend
- THEN the Bash sandbox may read both and write neither, and no deny rule covers either
- AND the grant the run record keeps is the request's grant, with the same context identity

## The boundary

### scenario.workers.undeclared-write-denied — A new undeclared file cannot be written

- GIVEN a running worker on the Claude Code backend
- WHEN it uses Write on a path in the worktree that is in no grant list
- THEN the [write hook](../../glossary.json#concept.write-hook) denies it with a reason saying the path is not in this task's grant, that a new file outside the bound directories is created and bound to a Module by the task level before a worker fills it and that a file another Module binds needs that Module bound
- AND the file does not appear in the worktree

### scenario.workers.ro-edit-denied — A read-only file cannot be edited

- GIVEN a running worker on the Claude Code backend whose grant makes a [Spec](../../glossary.json#concept.spec) file `ro`
- WHEN it uses Edit on that file
- THEN the edit is denied and the file is unchanged
- BUT Read of the same file succeeds

### scenario.workers.read-denied — Withheld files cannot be read by file tools

- GIVEN a running worker on the Claude Code backend whose grant leaves a file out and makes another `names`, both existing when its deny rules were generated
- WHEN it uses Read on either file, or Grep over a directory that holds them
- THEN Read is denied with a generic permission message
- AND Grep returns matches only from files the grant makes readable
- BUT a file below a runtime path of the worker configuration inside the worktree, such as `.venv`, has no deny rule

### scenario.workers.bash-confined — Bash is confined by the sandbox

- GIVEN a running `implement` worker on the Claude Code backend
- WHEN it uses Bash to read an ungranted file, `.git` or the user's `~/.claude`, to write a `ro` file, to reach the network, or asks to run a command unsandboxed
- THEN the read finds no such file, the write fails as a read-only file system, the network request is refused, and the command still runs sandboxed
- BUT Bash can read `ro` files and write `rw` files

### scenario.workers.bash-new-file-lost — A file Bash creates outside `rw` is lost

- GIVEN a running `implement` worker on the Claude Code backend
- WHEN it uses Bash to create a new file in a directory with no `rw` file
- THEN the command appears to succeed
- BUT the file never reaches the worktree and the audit sees no change

### scenario.workers.run-directory-denied — A run the deny rules would disable is refused

- GIVEN a worker on the Claude Code backend, a grant and a primary worktree whose generated [deny rules](../../glossary.json#concept.deny-rules) would cover the run's working, home or temporary directory
- WHEN the host is asked to start the worker
- THEN it refuses before launch with `run_directory_denied`
- AND it still writes the run record

### scenario.workers.misplaced-worktree-refused — A worker outside `.claude/worktrees/` is refused

- GIVEN a grant and a worktree that is the primary worktree itself, or a linked worktree of the same repository lying outside the primary worktree's `.claude/worktrees/`
- WHEN the host is asked to start a worker there
- THEN it refuses before launch with `worktree_misplaced` and the reason `environment`, naming the worktree and the primary worktree's `.claude/worktrees/`
- AND it generates no settings, write hook or permission extension
- AND it still writes the run record

### scenario.workers.git-hidden-outside-home — Every Git path is hidden wherever the repository lies

- GIVEN a primary worktree outside the user's home with a task worktree in its `.claude/worktrees/`, and in a writable directory of the grant a nested repository whose `.git` file points to a Git directory elsewhere
- WHEN the host prepares a worker in the task worktree
- THEN the Git administrative paths it hands the Harness are the primary worktree's `.git`, the task worktree's `.git` file, the nested `.git` file and the Git directory it points to
- AND on the Claude Code backend deny rules forbid Read and Edit of each, and of every entry of the primary worktree that does not lead to the task worktree, while the task worktree's granted files stay readable
- AND the Bash sandbox denies reading the primary worktree and each Git path, the nested `.git` included although its writable directory is readable
- AND the write hook refuses the nested `.git` with "Git metadata is not available to workers"

### scenario.workers.every-task-type — A worker of a task type that writes nothing launches read-only

- GIVEN a `review-architecture` grant, whose task type reads every Module's Specs and writes nothing
- WHEN the host is asked to start its worker
- THEN the worker runs and ends `ok` with the read-only tool set

### scenario.workers.unknown-task-type-refused — A task type the Protocol does not define is refused

- GIVEN a complete grant and a request naming the task type `review-everything`, which the Protocol does not define
- WHEN the host is asked to start the worker
- THEN it refuses before launch with `grant_unavailable` and the reason `input`, its detail naming `review-everything` and saying that a known task type is missing
- AND it still writes the run record

### scenario.workers.malformed-grant-refused — A malformed grant is refused before launch

- GIVEN a grant whose entries are not a list, or with an entry that is not an object, has a field other than `path` and `level`, has no path, an absolute path or one leaving the task worktree through `..`, or a level other than `rw`, `ro` and `names`
- WHEN the host is asked to start the worker, or generates its settings
- THEN settings generation raises `grant_malformed` naming the entry and what is wrong with it
- AND the host refuses before launch with `grant_malformed` and the reason `input`, generating no settings or write hook
- AND it still writes the run record

## Audit and deletions

### scenario.workers.audit-violation — A write outside `rw` fails the run

- GIVEN a worker round that ends within its timeout and limits with a valid [worker result](../../glossary.json#concept.worker-result), after which a file outside the grant's `rw` list has changed in the worktree
- WHEN the host audits the worktree
- THEN the run ends `failed` with `audit_violation` and every violating path as host evidence
- AND no round validation runs and no [resume round](../../glossary.json#concept.resume-round) follows
- AND when the worker result is a valid `ok`, whose `error` is null, the error has no cause from the worker
- BUT the host neither reverts nor commits the change

### scenario.workers.audit-deleted — A deleted file is a violation named as deleted

- GIVEN a worker round that ends with a valid result after a tracked file in the grant's `rw` list was deleted from the worktree
- WHEN the host audits the worktree
- THEN the round's audit lists the path in `changed` and the path followed by ` (deleted)` in `violations`, with the verdict `violation`
- AND the run ends `failed` with `audit_violation`

### scenario.workers.violation-and-timeout — A round that timed out still reports its writes outside `rw`

- GIVEN a worker round that writes a file outside the grant's `rw` list and is still running at its timeout
- WHEN the deadline passes
- THEN the run ends `failed` with `worker_timeout`, the code of the earlier row of [the rounds](launch.md#rounds), rather than `audit_violation`
- AND the error's detail names the file written outside `rw`, and the round's audit records it as a violation

### scenario.workers.violation-and-invalid-result — A write outside `rw` outranks an invalid result

- GIVEN a worker round whose agent process ends normally, within its timeout and limits and with no process error of its backend, without a valid worker result, after writing a file outside the grant's `rw` list
- WHEN the host reads its output and audits the worktree
- THEN the run ends `failed` with `audit_violation` and the violating path as host evidence
- AND the error's detail says that the worker result was invalid, and the error has no cause from the worker

### scenario.workers.glossary-entries — A worker may change its own Modules' glossary entries

- GIVEN a `specify` worker bound to Module A, whose grant makes the project glossary writable, and a round validation that audits the glossary by entry, as Concorde's does
- WHEN the worker changes the glossary entry of a concept A owns, and nothing else, and ends with a valid `ok` result
- THEN the audit and the round validation accept the change and the run ends `ok`

### scenario.workers.glossary-foreign-entry — Another Module's glossary entry is a violation

- GIVEN a `specify` worker bound to Module A, whose grant makes the project glossary writable, and a round validation that audits the glossary by entry, as Concorde's does
- WHEN the worker changes the glossary entry of a concept Module B owns
- THEN the round validation answers a violation and the run ends `failed` with `audit_violation`, naming the glossary, the entry and its owner before and after as the violation
- BUT no resume round follows

### scenario.workers.proposed-deletion — The host performs proposed deletions

- GIVEN a worker result whose `proposed_deletions` names one `rw` file and one `ro` file, and a clean audit
- WHEN the run ends
- THEN the host deletes the `rw` file
- AND refuses the `ro` file and records the refusal

### scenario.workers.deletion-repeated-absent — A repeated target is deleted once and an absent one recorded

- GIVEN a clean audit and a worker result whose `proposed_deletions` names one `rw` file twice, once relative to the worktree and once absolute, and one `rw` path that does not exist
- WHEN the run ends
- THEN the host deletes the file once and records it once in `deleted`
- AND it records the absent path in `deletions_absent`, never in `deletions_refused`
- AND the run ends `ok`

### scenario.workers.deletion-failed — A failed deletion fails the run after every other deletion

- GIVEN a clean audit and a worker result whose `proposed_deletions` names a `rw` file whose deletion the operating system refuses, followed by another `rw` file
- WHEN the run ends
- THEN the host still deletes the second file and records it in `deleted`, and records the first in `deletions_failed`
- AND the run ends `failed` with `deletion_failed` and the reason `environment`, its detail naming the file it could not delete with the error and the file it deleted
- BUT the deleted file is not restored

## Rounds

### scenario.workers.check-failure-resume — A failing check resumes the same worker

- GIVEN a worker on the Claude Code backend that ended `ok` with a clean audit, and a round validation that runs a configured check, as Concorde's does, which fails
- WHEN the host starts a resume round
- THEN it resumes the session with the repair the round validation reported: the failing check's identity, exit code and log tail
- AND the next round continues from the new session identifier the resume returned
- AND when the checks then pass the run ends `ok` with two rounds recorded

### scenario.workers.rounds-exhausted — Checks that keep failing end the run

- GIVEN a round validation that runs a configured check, as Concorde's does, which fails after every round, and that asks a run whose checks still fail to end with `checks_failed`
- WHEN the configured number of resume rounds has been used
- THEN the run ends `failed` with `checks_failed` and the last check results
- AND its error gives `exhausted` as the reason, lists each round's failing checks as attempts and has one cause per failing check with its exit code and the end of its log
- BUT no further round is started

### scenario.workers.blocked-not-resumed — A blocked worker goes to the main agent

- GIVEN a worker that changes nothing outside its `rw` list and ends `blocked` because its Module's Spec does not state a promise it needs
- WHEN the host finishes the round
- THEN the audit still runs and is clean
- BUT no round validation runs, so no configured check runs, no resume round follows, and the run ends `blocked` with the worker result verbatim
- AND the run's error is Workers' `worker_blocked` link, of level `workers`, whose one cause is the worker's own error, unchanged, with the level `worker`

## Host failures

### scenario.workers.timeout — A round past its deadline is killed

- GIVEN a worker still running at its round's timeout
- WHEN the deadline passes
- THEN the host kills the worker's whole process group
- AND the run ends `failed` with `worker_timeout` and a run record

### scenario.workers.interrupted-run — An interrupted run still ends

- GIVEN a worker run whose launcher is told the run identity as soon as the run exists
- WHEN the run is interrupted from outside before it returns in a way its host can handle, such as by a termination signal or the cancellation of the run that launched it
- THEN its run record ends `failed` with the error `interrupted`, of reason `environment`, naming the interruption
- AND its [progress file](../../glossary.json#concept.progress-file) is `finished` with status `failed`
- AND the interruption travels on to the launcher

### scenario.workers.invalid-result — A worker without a valid result has failed

- GIVEN a worker round whose agent process ends normally, within its timeout and limits and with no process error of its backend, changes nothing outside the grant's `rw` list, and ends without a structured result that satisfies the worker result schema: with none, with a status other than `ok`, `blocked` and `failed`, with a `blocked` or `failed` result without an error, or with an `ok` result with one
- WHEN the host reads its output
- THEN the run ends `failed` with `worker_result_invalid` and the schema violation or the worker's final text in its error
- AND the round's standard error is its `stderr.log` and the transcript path is in the run record

### scenario.workers.claude-error — An error of Claude Code itself is reported with its cause

- GIVEN a worker whose Claude Code session ends with an error subtype, such as the turn limit, instead of a structured result
- WHEN the host reads its output
- THEN the run ends `failed` with `worker_limit_reached` for a turn or budget limit and `claude_failed` otherwise
- AND the error's cause is the Claude Code process's link with the subtype, the turn count, the cost, the final text and the tail of standard error

## The pi backend

### scenario.workers.pi-fenced-run — A pi worker is fenced by the same grant

- GIVEN a run whose worker runs on pi, and an `implement` grant with a `rw` source file, `ro` Specs, another Module's `ro` source file and a file no grant list names
- WHEN the host runs a pi worker that reads the Specs, edits the source file and ends with `concorde_result`
- THEN the edit reaches the worktree, the audit is clean and the run ends `ok` with the worker result verbatim
- AND the run record holds the session identifier, the transcript path and the tool set of the pi backend

### scenario.workers.pi-file-tools-denied — pi file tools explain every denial

- GIVEN a running pi worker
- WHEN it reads a `names` file, an ungranted file, the task worktree's `.git`, a submodule's `.git`, a file of the common Git directory, a source file of the primary worktree outside the task worktree, with that primary worktree outside the user's home, or a file of its runtime directory's `config/`, or writes a `ro` file, an undeclared file or a submodule's `.git`
- THEN each call is denied with the reason the Harness's read or write table gives, prefixed `Concorde grant:`
- AND no file changes

### scenario.workers.pi-commands-sandboxed — pi commands see only the grant

- GIVEN a running pi `implement` worker
- WHEN it greps a directory holding ungranted files, or uses bash to read an ungranted file, to write a `ro` file or to reach the network
- THEN grep reports matches only from readable files, the bash read finds no such file, the write fails as a read-only file system and the network request is refused
- BUT bash can read `ro` files and write `rw` files
- AND bash's temporary files go to the run's private `TMPDIR`, which it can write

### scenario.workers.pi-runtime-missing — A pi run without its runtime is refused

- GIVEN a run whose worker runs on pi, on a machine without the sandbox-runtime package
- WHEN the host is asked to start a worker
- THEN it refuses before launch with `pi_runtime_missing`, naming the missing package and how to install it
- AND it still writes the run record

### scenario.workers.pi-settings-independent — A pi worker takes nothing from the user's pi settings

- GIVEN a user's pi settings file that either chooses a default provider, model and thinking level, enabled models, per-model thinking levels, packages and other settings, or is one pi would refuse
- AND a [worker configuration](../../glossary.json#concept.worker-configuration) that chooses a model and a level for a pi worker
- WHEN the host prepares the worker's runtime directory and launches it
- THEN its generated pi settings hold only `defaultProjectTrust` `never`, and the run is not refused
- AND the worker is launched with the local id the [model map](../../glossary.json#concept.model-map) gives the configured model and with the configured level, as `--model` and `--thinking`
- AND its pi configuration directory holds copies of the user's `auth.json` and `models.json`

### scenario.workers.pi-limit — A pi run over its turn limit stops

- GIVEN a pi worker whose turns exceed `max_turns`
- WHEN the [permission extension](../../glossary.json#concept.permission-extension) counts the turn
- THEN it aborts the run and records the limit reached
- AND the run ends `failed` with `worker_limit_reached`
- AND the error's cause is the pi process's link with the limit and the value reached and the reason `exhausted`, never a Claude Code process's link

## Worker models

### scenario.workers.backend-configured — Workers run on pi unless their configuration chooses Claude Code

- GIVEN a command started from a Claude Code session, both programs installed, and a [worker configuration](../../glossary.json#concept.worker-configuration) whose default gives a pi model and which puts `spec_review`'s worker `checker` on `claude` with a Claude Code model and a level
- WHEN the choices of `spec_review`'s `reviewer` and `checker` are resolved
- THEN the reviewer runs on pi with the default's model, as the local id the [model map](../../glossary.json#concept.model-map) gives it on pi, and the choice names that id and the map
- AND the checker runs on `claude` with the model and level of its own entry

### scenario.workers.backend-default — Without a configuration entry a worker runs on pi

- GIVEN a command started from a Claude Code session and a worker configuration whose default names only a model
- WHEN the choice of `implement`'s worker is resolved
- THEN it runs on `pi`, from Concorde's default [worker backend](../../glossary.json#concept.worker-backend), not from the program of the [main agent](../../glossary.json#concept.main-agent)

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

### scenario.workers.models-listed-mapped — The listing names the project model names the map gives

- GIVEN pi listing a model with credentials, and a [model map](../../glossary.json#concept.model-map) that maps one project model name to that model on pi and another to a pi id pi does not list
- WHEN Workers lists the candidates of pi
- THEN the listing names the first project model name for its candidate
- AND it names the other project model name with its unlisted id

### scenario.workers.models-listed-unmapped — Discovery without a model map still lists

- GIVEN pi listing a model with credentials, and no model map
- WHEN Workers lists the candidates of pi
- THEN the listing names the model and reports the map's refusal, without refusing the listing

### scenario.workers.models-backend-missing — Discovery refuses a program that is not installed

- GIVEN a backend whose program is not installed
- WHEN Workers lists the candidates of that backend
- THEN the listing is refused with `backend_missing`

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

### scenario.workers.model-level-refused — A model's own level its backend lacks is refused

- GIVEN `enabled_models` giving a model a level of neither backend, or a level the backend of a worker taking that model does not have
- WHEN the configuration is checked
- THEN it is refused with `config_invalid`

### scenario.workers.model-unresolved — A worker whose configuration names no model is refused

- GIVEN a worker configuration whose default sets only a level, which names a model for `spec_review`'s default and puts `spec_panel`'s `chair` on `claude` without a model
- WHEN the choices of `spec_review`'s `checker`, `implement`'s worker and `spec_panel`'s `chair` are resolved
- THEN the checker gets the model of its Operation's default
- AND `implement`'s worker and the chair are refused with `model_unresolved`, naming the worker, every entry its model may come from, from its own entry to the default, and how to set one, and saying that no program's or developer's default model is used

### scenario.workers.model-custom-accepted — Validation admits a custom model without discovery

- GIVEN a configuration whose enabled and default model is a custom project model name that no discovery lists
- WHEN the shared validator checks it without installed backends or credentials
- THEN the configuration is accepted
- AND a worker's choice names the custom model

### scenario.workers.model-refused — Validation refuses invalid entries

- GIVEN a configuration with invalid structure, an Operation or worker name its caller does not declare, a malformed `enabled_models` entry, an enabled model named by one program's id such as `local-openai/gpt-6` rather than a project model name, or a reasoning level outside the effective backend's vocabulary
- WHEN the shared validator checks it
- THEN it is refused with `config_invalid`

### scenario.workers.model-not-enabled — A model outside the enabled models is refused

- GIVEN a worker configuration whose `enabled_models` admits two models
- WHEN the default, an Operation's default or a worker's entry names a third model
- THEN the whole configuration is refused with `model_not_enabled`, naming the entry, the model, the enabled models and how to repair it

### scenario.workers.enabled-models-required — A configuration without enabled models is refused

- GIVEN a worker configuration without `enabled_models`, or with an empty one
- WHEN the shared validator checks it
- THEN it is refused with `config_invalid` saying that the list is required

### scenario.workers.config-missing — A worktree without a worker configuration runs no worker

- GIVEN a worktree without `.concorde/workers.json`
- WHEN Workers reads the worker configuration for a launch
- THEN it is refused with `config_missing`, naming the file, what it must hold and that it must be committed
- AND it says that a worker's model is never taken from the developer's own pi or Claude Code settings

### scenario.workers.model-config-invalid — An unreadable configuration is reported, never ignored

- GIVEN a worktree whose `.concorde/workers.json` is not valid JSON, has a field the schema does not know or has a schema version other than 2, the one Workers reads, and 1, the retired one
- WHEN Workers reads it
- THEN it is refused with `config_invalid`, naming the file and what is wrong with it, and for another schema version the version it expects

### scenario.workers.model-config-v1 — A configuration of schema version 1 is refused with how to convert it

- GIVEN a worktree whose `.concorde/workers.json` has schema version 1, whose models are local ids such as `local-openai/gpt-6`
- WHEN Workers reads it
- THEN it is refused with `config_invalid`, saying to rename each model to a project model name, set the version and map each name in the model map

### scenario.workers.limits-default — Without limits a launch gets the default limits and runtime paths

- GIVEN a worktree whose `.concorde/workers.json` sets neither `limits` nor `runtime`
- WHEN Workers reads the limits and runtime paths of a launch
- THEN it gets the default limits and the runtime paths `.venv` and `node_modules`

### scenario.workers.limits-configured — Limits and runtime paths come from the worker configuration

- GIVEN a worktree whose `.concorde/workers.json` sets `limits.max_turns` and `limits.rounds` and a `runtime` list
- WHEN Workers reads the limits and runtime paths of a launch
- THEN it gets its own `max_turns`, `rounds` and runtime paths, with the default for every limit it does not set

### scenario.workers.retired-configuration — The untracked configuration of earlier versions is refused, not ignored

- GIVEN a worktree that has the untracked `.concorde/worker-models.json` of earlier versions and no `.concorde/workers.json`
- WHEN Workers reads the worker configuration
- THEN it is refused with `config_invalid`, naming both files and saying to move the models into `.concorde/workers.json`, commit it and delete the old file

### scenario.workers.retired-configuration-beside — Beside a worker configuration the untracked file is not read

- GIVEN a worktree that has both the untracked `.concorde/worker-models.json` of earlier versions and `.concorde/workers.json`
- WHEN Workers reads the worker configuration
- THEN it reads `.concorde/workers.json`

## The model map

### scenario.workers.model-map-location — The model map is the named file, else the user's XDG configuration

- GIVEN an environment that names a model map in `CONCORDE_MODEL_MAP` by an absolute path, or names none and sets an absolute `XDG_CONFIG_HOME`, a relative one or none
- WHEN Workers finds the [model map](../../glossary.json#concept.model-map)
- THEN it is the named file, else `concorde/models.json` of the absolute `XDG_CONFIG_HOME`, else, for a relative one or none, `~/.config/concorde/models.json`

### scenario.workers.model-map-relative — A model map named by a relative path is refused

- GIVEN an environment whose `CONCORDE_MODEL_MAP` is not an absolute path
- WHEN a worker is resolved
- THEN it is refused with `model_map_invalid`

### scenario.workers.model-map-resolved — A project model name resolves to its local id on the worker's backend

- GIVEN a worker configuration choosing the project model `gpt-6-astra` by default and `claude-opus-5-5` for `spec_panel`'s `reviewer1`, and a model map giving `gpt-6-astra` a pi id and `claude-opus-5-5` ids on both programs, besides a model no project enables
- WHEN the choices of `implement`'s worker and `spec_panel`'s `reviewer1` are resolved
- THEN each runs on pi with its project model name, its level and the pi id of its model, and names the map it came from

### scenario.workers.backend-switch — An entry choosing a backend inherits the model and level

- GIVEN a worker configuration whose default chooses a model and a level and which puts `spec_panel`'s `chair` on `claude` without a model or level, and a model map giving the default's model a pi id only
- WHEN the chair's choice is resolved
- THEN resolving the worker configuration chooses `claude` for the chair and gives it the default's model and level, each naming the default as its source
- BUT resolving the model map then refuses the chair with `model_unmapped` before any worker launches, since the map gives that model no Claude Code id, naming the worker, its backend and model with their sources, the map, the programs the model is mapped for and the exact entry to add, and saying that a project model name is never used as a local id

### scenario.workers.model-unmapped — A model the map gives no id for the worker's backend is refused

- GIVEN a model map that does not name the default's model
- WHEN a worker on that model is resolved
- THEN it is refused with `model_unmapped`, saying that the map does not name the model at all

### scenario.workers.model-map-checked — An Operation's workers are checked against the map in one refusal

- GIVEN a worker configuration and a model map that lacks the ids of several models the workers of `spec_panel` would run on, on the backends that would run them, and of a model only another Operation's worker takes
- WHEN the configuration reader checks the workers of `spec_panel` against the map, as that Operation's run asks before its first worker launches
- THEN one `model_unmapped` refusal names every model and backend the map lacks for `spec_panel`, with the workers that would take each, and the map
- BUT it names nothing of the other Operation
- AND once the map gives each its id, the check passes

### scenario.workers.refusal-reasons — Every refusal before a run has its fixed reason

- GIVEN each refusal of the configuration reader: `config_missing`, `config_invalid`, `model_not_enabled`, `model_unresolved`, `backend_missing`, `model_map_missing`, `model_map_invalid` and `model_unmapped`
- WHEN its reason is looked up
- THEN the four refusals of the worker configuration give `input` and the program's and the model map's give `environment`

### scenario.workers.model-map-missing — A missing model map is refused, never ignored

- GIVEN no model map
- WHEN a worker is resolved
- THEN it is refused with `model_map_missing`, naming the file, showing what it holds and saying that it belongs to the machine and is never committed

### scenario.workers.model-map-invalid — An unreadable model map is refused, never ignored

- GIVEN a model map that is not valid JSON, has a duplicate key, another schema version, a model without an id, an unknown program or a name that is not a project model name
- WHEN a worker is resolved
- THEN it is refused with `model_map_invalid`, naming the file and what is wrong with it

## Discovering models

### scenario.workers.models-standalone — Discovery works outside a worktree

- GIVEN a directory outside Git with configured agent programs
- WHEN `python3 scripts/available_models.py --backend pi` or `--backend claude` runs, with optional `--json`
- THEN it lists configured candidates with sources and reasoning levels, explaining that no inference API access was probed
- AND pi uses its credentialed listing while Claude's aliases and settings-derived list is explicitly incomplete

### scenario.workers.models-standalone-missing — Discovery without the program reports an error and gates nothing

- GIVEN a directory outside Git and a backend whose program is missing or whose listing fails
- WHEN `python3 scripts/available_models.py --backend` names that backend, with `--json`
- THEN it exits with status 1 and a discovery error, such as `backend_missing`, naming the program
- AND no worker configuration depends on that error, since validation never runs discovery

## What a run leaves

### scenario.workers.trace-left — A worker run leaves its trace and no credentials

- GIVEN an Operation run whose worker needs two rounds, the first failing a configured check, on a backend whose configuration holds a credential copy
- WHEN the run ends
- THEN the run's node holds `workers/<run-id>/` with `trace.json`, `status.json`, `grant.json`, `brief.md`, `transcript.jsonl` and `rounds/1/` and `rounds/2/`, each round with its own `trace.json`, `stderr.log` and the check nodes its round validation placed
- AND each round's usage holds the tokens, cost and turns the agent program reported for it
- AND on the Claude Code backend each round's content keeps the result envelope's `permission_denials`, `modelUsage` and `duration_api_ms` as Claude Code gave them, null for one it did not give
- AND the runtime directory, with the credential copy, no longer exists
- AND the worker run's `trace.json` was already there, `running`, while the worker ran
