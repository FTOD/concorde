# Worker run scenarios

This document describes the testable situations of one worker run. The [entry](module.md) explains
the run. [The run mechanics](launch.md) give these exact details:

- settings
- rounds
- records

## A normal run

### scenario.workers.fenced-run — An implement worker changes only its writable files

- GIVEN a worker on the Claude Code backend and a worktree
- AND an `implement` grant with a `rw` source file
- AND the grant has a `rw` directory
- AND the grant has `ro` Specs
- AND since an `implement` worker reads the project's whole code, the grant has another
  [Module](../../glossary.json#concept.module)'s source file at `ro`
- WHEN the host runs a worker that edits the source file
- AND the worker creates a new file inside the directory
- AND the worker changes nothing else
- AND the worker ends with a valid `ok` result
- THEN both changes reach the worktree
- AND the audit is clean
- AND the caller's round validation runs the
  [configured checks](../../glossary.json#concept.configured-check) on the worktree, as Concorde's
  does
- AND when the checks pass, the run ends `ok`
- AND the [run record](../../glossary.json#concept.run-record) holds the grant's
  [context identity](../../glossary.json#concept.context-identity)
- AND the run record holds the settings and brief digests
- AND the run record holds the tool set
- AND the run record holds the transcript path
- AND the run record holds the [worker result](../../glossary.json#concept.worker-result) verbatim
- AND the round's node below the run record holds its audit
- AND the round's node holds the round validation's evidence with the
  [check results](../../glossary.json#concept.check-result)
- AND the round's node holds standard error
- AND the round's node holds the tokens the agent program reported
- AND the round's node holds the cost the agent program reported
- AND the round's node holds the turns the agent program reported

### scenario.workers.no-precreation — The host creates no file before launch

- GIVEN a grant whose `rw` list names a file and a directory
- WHEN the host prepares the run
- AND the worker changes nothing
- THEN the worktree after the run holds exactly the files it held before the run
- AND those files have the same content as before the run

### scenario.workers.no-ambient-instructions — The brief is the only instruction

- GIVEN a worker on the Claude Code backend
- AND a `CLAUDE.md` in the worktree and in the working directory
- AND user settings in the user's Claude Code configuration
- AND skills in the user's Claude Code configuration
- AND MCP servers in the user's Claude Code configuration
- WHEN the host launches a worker
- THEN none of those instructions or configuration reaches the worker
- AND the worker's environment holds only the listed variables
- AND `HOME` is inside its [runtime directory](../../glossary.json#concept.runtime-directory)
- AND `CLAUDE_CONFIG_DIR` is inside the worker's runtime directory
- AND `TMPDIR` is inside the worker's runtime directory

### scenario.workers.session-proxy — A worker started behind a loopback proxy uses that proxy

- GIVEN a host environment whose `HTTP_PROXY` names a proxy on `localhost`
- AND its `HTTPS_PROXY` names a proxy on `localhost`
- AND its `http_proxy` names a proxy on `localhost`
- AND its `https_proxy` names a proxy on `localhost`
- AND its `NO_PROXY` lists `localhost`
- AND its `NO_PROXY` lists `127.0.0.1`
- AND its `NO_PROXY` lists `::1`
- AND its `NO_PROXY` lists a private address range
- AND these values are as an enclosing loopback proxy, such as a sandboxed
  [main agent](../../glossary.json#concept.main-agent)'s session, sets them
- WHEN the host launches a worker, on the pi backend or the Claude Code backend
- THEN the worker's environment holds the same four proxy variables
- AND its `NO_PROXY` still lists the private range but no loopback entry
- AND the worker's environment holds no other proxy variable, such as `ALL_PROXY`

### scenario.workers.own-proxy — A proxy elsewhere keeps loopback direct

- GIVEN a host environment whose `HTTPS_PROXY` names a proxy on another host
- AND its `NO_PROXY` lists `localhost` and a domain
- WHEN the host launches a worker
- THEN the worker's environment holds that `HTTPS_PROXY` and the same `NO_PROXY`

### scenario.workers.no-proxy — Without a proxy on the host no proxy variable passes

- GIVEN a host environment that sets no proxy variable to a non-empty value but sets `NO_PROXY`
- WHEN the host launches a worker
- THEN the worker's environment holds no proxy variable and no `NO_PROXY`

### scenario.workers.brief-terms — The brief carries the definitions of the worker's terms

- GIVEN a `specify` grant that makes the project glossary writable
- AND the grant's terms hold the glossary entries the bound Modules' documents link
- WHEN the host launches the worker
- THEN the brief lists each term with its identity
- AND the brief lists each term with its owner
- AND the brief lists each term with its definition
- AND the brief says that only the bound Modules' entries of the glossary may change
- BUT the brief lists no entry outside the grant's terms

### scenario.workers.brief-result-paths — The brief asks for relative paths in the result

- GIVEN a worker of any [task type](../../glossary.json#concept.task-type) in the task worktree
- WHEN the host launches the worker
- THEN its brief names the task worktree's absolute path
- AND the brief tells the worker to give its tools absolute paths
- AND the brief tells the worker to write every path of the task worktree in its result relative to
  the worktree
- AND the brief tells the worker never to write those paths as absolute paths

### scenario.workers.brief-review-gaps — A Spec reviewer reports a gap and goes on

- GIVEN a worker of task type `review-spec` or `review-architecture`
- WHEN the host writes its brief
- THEN the brief tells the worker to report a promise the Spec does not state, or a document it
  lacks, as a finding
- AND the brief tells the worker to go on reviewing
- AND the brief tells the worker to return `blocked` only when it cannot review at all
- BUT a `specify`, `implement` or `test` worker is told to return `blocked` for a promise the Spec
  does not state

### scenario.workers.project-interpreter — The project's interpreter comes first and is named

- GIVEN a request naming the project's interpreter, such as the worktree's `.venv/bin/python`, on
  the Claude Code backend or the pi backend
- WHEN the host launches the worker
- THEN the worker's `PATH` starts with the interpreter's directory
- AND the host's own `PATH` follows the interpreter's directory in the worker's `PATH`
- AND the brief names the interpreter as the one to run the project's code and tests with
- BUT the host's own `PATH` is unchanged

### scenario.workers.runtime-paths-readable — Host material the caller lists is readable, never writable

- GIVEN a request whose runtime paths list a folder of check logs outside the worktree and a `.venv`
  inside it
- WHEN the host prepares the worker on the Claude Code backend
- THEN the Bash sandbox may read both
- AND the Bash sandbox may write neither
- AND no deny rule covers either
- AND on the pi backend, the permission extension lets `read` open the `.venv` inside the worktree
- AND on the pi backend, the permission extension lets a search open the `.venv` inside the
  worktree
- AND on the pi backend, the permission extension refuses a write to the `.venv`
- AND the grant the run record keeps is the request's grant
- AND that grant has the same context identity as the request's grant

## The boundary

### scenario.workers.undeclared-write-denied — A new undeclared file cannot be written

- GIVEN a running worker on the Claude Code backend
- WHEN it uses Write on a path in the worktree that is in no grant list
- THEN the [write hook](../../glossary.json#concept.write-hook) denies it with a reason saying the
  path is not in this task's grant
- AND the reason says that before a worker fills a new file outside the bound directories, the task
  level creates the file
- AND the reason says that before the worker fills that file, the task level binds the file to a
  Module
- AND the reason says that a file another Module binds needs that Module bound
- AND the file does not appear in the worktree

### scenario.workers.write-through-link — A write through a symbolic link is judged by its target

- GIVEN a worker whose worktree holds a `rw` directory with a symbolic link to a `ro` Spec
- AND that directory holds a symbolic link to a file outside the worktree
- AND that directory holds a symbolic link to an ungranted file
- AND outside `rw`, the worktree holds a link to a `rw` file
- WHEN the worker writes through each link, with the write hook on the Claude Code backend or the
  permission extension on pi
- THEN the writes through the three links in the `rw` directory are denied
- AND each reason names the target judged and the link
- AND the reason for the link to a file outside the worktree says the link leads outside the
  worktree
- AND the write through the link to the `rw` file is allowed

### scenario.workers.most-specific-entry — A file listed apart below a writable directory keeps its own level

- GIVEN a grant whose `rw` directory entry has below it a file listed at `ro` on its own, such as
  another Module's file
- AND that directory entry has below it a directory listed at `names`
- WHEN a worker writes that file, with the write hook on the Claude Code backend or the permission
  extension on pi, or changes it otherwise, or proposes its deletion
- THEN the write is denied as read-only
- AND a write below the `names` directory is denied as named only
- AND another file of the `rw` directory stays writable
- AND the deny rules forbid editing the file but not reading it
- AND a change to the file is an audit violation
- AND the file's proposed deletion is refused

### scenario.workers.ro-edit-denied — A read-only file cannot be edited

- GIVEN a running worker on the Claude Code backend whose grant makes a
  [Spec](../../glossary.json#concept.spec) file `ro`
- WHEN it uses Edit on that file
- THEN the edit is denied
- AND the file is unchanged
- BUT Read of the same file succeeds

### scenario.workers.read-denied — Withheld files cannot be read by file tools

- GIVEN a running worker on the Claude Code backend whose grant leaves a file out
- AND the grant makes another file `names`
- AND both files existed when the worker's deny rules were generated
- WHEN it uses Read on either file, or Grep over a directory that holds them
- THEN Read is denied with a generic permission message
- AND Grep returns matches only from files the grant makes readable
- BUT a file below a runtime path of the worker configuration inside the worktree, such as `.venv`,
  has no deny rule

### scenario.workers.bash-confined — Bash is confined by the sandbox

- GIVEN a running `implement` worker on the Claude Code backend
- WHEN it uses Bash to read an ungranted file, `.git` or the user's `~/.claude`, to write a `ro`
  file, to reach the network, or asks to run a command unsandboxed
- THEN the read finds no such file
- AND the write fails as a read-only file system
- AND the network request is refused
- AND the command still runs sandboxed
- BUT Bash can read `ro` files
- AND Bash can write `rw` files

### scenario.workers.bash-new-file-lost — A file Bash creates outside `rw` is lost

- GIVEN a running `implement` worker on the Claude Code backend
- WHEN it uses Bash to create a new file in a directory with no `rw` file
- THEN the command appears to succeed
- BUT the file never reaches the worktree
- AND the audit sees no change

### scenario.workers.run-directory-denied — A run the deny rules would disable is refused

- GIVEN a worker on the Claude Code backend and a grant
- AND a primary worktree whose generated [deny rules](../../glossary.json#concept.deny-rules) would
  cover the run's working, home or temporary directory
- WHEN the host is asked to start the worker
- THEN it refuses before launch with `run_directory_denied`
- AND it still writes the run record

### scenario.workers.misplaced-worktree-refused — A worker outside `.claude/worktrees/` is refused

- GIVEN a grant and a worktree that is the primary worktree itself, or a linked worktree of the same
  repository lying outside the primary worktree's `.claude/worktrees/`
- WHEN the host is asked to start a worker there
- THEN it refuses before launch with `worktree_misplaced` and the reason `environment`
- AND the refusal names the worktree and the primary worktree's `.claude/worktrees/`
- AND the host generates no settings
- AND the host generates no write hook
- AND the host generates no permission extension
- AND the host still writes the run record

### scenario.workers.git-hidden-outside-home — Every Git path is hidden wherever the repository lies

- GIVEN a primary worktree outside the user's home with a task worktree in its `.claude/worktrees/`
- AND a writable directory of the grant holds a nested repository whose `.git` file points to a Git
  directory elsewhere
- WHEN the host prepares a worker in the task worktree
- THEN the Git administrative paths the host hands the Harness are the primary worktree's `.git`,
  the task worktree's `.git` file, the nested `.git` file and the Git directory that file points to
- AND on the Claude Code backend, deny rules forbid Read and Edit of each Git administrative path
- AND on the Claude Code backend, deny rules forbid Read and Edit of every entry of the primary
  worktree that does not lead to the task worktree
- AND on the Claude Code backend, the task worktree's granted files stay readable
- AND the Bash sandbox denies reading the primary worktree and each Git path
- AND the Bash sandbox denies reading the nested `.git` although its writable directory is readable
- AND the write hook refuses the nested `.git` with "Git metadata is not available to workers"

### scenario.workers.every-task-type — A worker of a task type that writes nothing launches read-only

- GIVEN a `review-architecture` grant, whose task type reads every Module's Specs and writes nothing
- WHEN the host is asked to start its worker
- THEN the worker runs with the read-only tool set
- AND the worker ends `ok`

### scenario.workers.unknown-task-type-refused — A task type the Protocol does not define is refused

- GIVEN a complete grant and a request naming the task type `review-everything`, which the Protocol
  does not define
- WHEN the host is asked to start the worker
- THEN it refuses before launch with `grant_unavailable` and the reason `input`
- AND the refusal's detail names `review-everything`
- AND the refusal's detail says that a known task type is missing
- AND the host still writes the run record

### scenario.workers.malformed-grant-refused — A malformed grant is refused before launch

- GIVEN a grant whose entries are not a list, or with an entry that is not an object, has a field
  other than `path` and `level`, has no path, an absolute path or one leaving the task worktree
  through `..`, or a level other than `rw`, `ro` and `names`
- WHEN the host is asked to start the worker, or generates its settings
- THEN settings generation raises `grant_malformed` naming the entry and what is wrong with it
- AND the host refuses before launch with `grant_malformed` and the reason `input`
- AND the host generates no settings or write hook
- AND it still writes the run record

## Audit and deletions

### scenario.workers.audit-violation — A write outside `rw` fails the run

- GIVEN a worker round that ends within its timeout and limits with a valid
  [worker result](../../glossary.json#concept.worker-result)
- AND after the round ends, a file outside the grant's `rw` list shows a change in the worktree
- WHEN the host audits the worktree
- THEN the run ends `failed` with `audit_violation` and every violating path as host evidence
- AND no round validation runs
- AND no [resume round](../../glossary.json#concept.resume-round) follows
- AND when the worker result is a valid `ok` with null `error`, the run's error has no cause from
  the worker
- BUT the host neither reverts nor commits the change

### scenario.workers.audit-deleted — A deleted file is a violation named as deleted

- GIVEN a file in the grant's `rw` list was deleted from the worktree
- AND before the run, the file was tracked or untracked
- AND after the deletion, a worker round ends with a valid result
- WHEN the host audits the worktree
- THEN the round's audit lists the path in `changed`
- AND the audit lists the path followed by ` (deleted)` in `violations`
- AND the audit has the verdict `violation`
- AND the run ends `failed` with `audit_violation`

### scenario.workers.violation-and-timeout — A round that timed out still reports its writes outside `rw`

- GIVEN a worker round that writes a file outside the grant's `rw` list
- AND the round still runs at its timeout
- WHEN the deadline passes
- THEN the run ends `failed` with `worker_timeout`, the code of the earlier row of
  [the rounds](launch.md#rounds), rather than `audit_violation`
- AND the error's detail names the file written outside `rw`
- AND the round's audit records the file as a violation

### scenario.workers.violation-and-invalid-result — A write outside `rw` outranks an invalid result

- GIVEN a worker round that writes a file outside the grant's `rw` list
- AND after that write, its agent process ends normally, within its timeout and limits
- AND the agent process ends with no process error of its backend
- AND the agent process ends without a valid worker result
- WHEN the host reads its output
- AND the host audits the worktree
- THEN the run ends `failed` with `audit_violation` and the violating path as host evidence
- AND the error's detail says that the worker result was invalid
- AND the error has no cause from the worker

### scenario.workers.glossary-entries — A worker may change its own Modules' glossary entries

- GIVEN a `specify` worker bound to Module A, whose grant makes the project glossary writable
- AND a round validation that audits the glossary by entry, as Concorde's does
- WHEN the worker changes the glossary entry of a concept A owns, and nothing else
- AND the worker ends with a valid `ok` result
- THEN the audit accepts the change
- AND the round validation accepts the change
- AND the run ends `ok`

### scenario.workers.glossary-foreign-entry — Another Module's glossary entry is a violation

- GIVEN a `specify` worker bound to Module A, whose grant makes the project glossary writable
- AND a round validation that audits the glossary by entry, as Concorde's does
- WHEN the worker changes the glossary entry of a concept Module B owns
- THEN the round validation answers a violation
- AND the run ends `failed` with `audit_violation`
- AND the violation names the glossary
- AND the violation names the entry
- AND the violation names its owner before and after
- BUT no resume round follows

### scenario.workers.proposed-deletion — The host performs proposed deletions

- GIVEN a worker result whose `proposed_deletions` names one `rw` file and one `ro` file
- AND a clean audit
- WHEN the run ends
- THEN the host deletes the `rw` file
- AND the host refuses the `ro` file
- AND the host records the refusal

### scenario.workers.deletion-repeated-absent — A repeated target is deleted once and an absent one recorded

- GIVEN a clean audit
- AND a worker result whose `proposed_deletions` names one `rw` file twice, once relative to the
  worktree and once absolute
- AND the result's proposed deletions name one `rw` path that does not exist
- WHEN the run ends
- THEN the host deletes the file once
- AND the host records the file once in `deleted`
- AND it records the absent path in `deletions_absent`, never in `deletions_refused`
- AND the run ends `ok`

### scenario.workers.deletion-failed — A failed deletion fails the run after every other deletion

- GIVEN a clean audit
- AND a worker result whose `proposed_deletions` names a `rw` file whose deletion the operating
  system refuses, followed by another `rw` file
- WHEN the run ends
- THEN the host still deletes the second file
- AND the host records the second file in `deleted`
- AND the host records the first file in `deletions_failed`
- AND the run ends `failed` with `deletion_failed` and the reason `environment`
- AND the error's detail names the file the host could not delete with the error
- AND the error's detail names the file the host deleted
- BUT the deleted file is not restored

### scenario.workers.deletion-through-link-refused — A deletion through a directory link is refused

- GIVEN a clean audit
- AND a `rw` directory holding a symbolic link to a `ro` Spec directory
- AND the directory holds a symbolic link to a directory outside the worktree
- AND the directory holds a symbolic link to a `rw` file
- AND a worker result whose `proposed_deletions` names a file below each directory link and the file
  link itself
- WHEN the run ends
- THEN the host refuses both files reached through a directory link
- AND the host records both files in `deletions_refused`
- AND both files still exist
- AND the host removes the file link itself, never its target

### scenario.workers.deletions-whatever-the-outcome — Proposed deletions follow a clean last round whatever its outcome

- GIVEN a worker whose last round ends with a valid result proposing a `rw` file's deletion
- AND the last round's audit is clean
- WHEN its round validation fails the run with a repair left after the last round, or answers a
  violation instead
- THEN when the validation failed the run, the host deletes the file
- AND when the validation failed the run, the run ends `failed` with the code the validation named
- BUT when the validation answered a violation, the host deletes nothing

## Rounds

### scenario.workers.check-failure-resume — A failing check resumes the same worker

- GIVEN a worker on the Claude Code backend that ended `ok` with a clean audit
- AND a round validation that runs a configured check, as Concorde's does
- AND the configured check fails
- WHEN the host starts a resume round
- THEN it resumes the session with the repair the round validation reported
- AND the repair names the failing check's identity
- AND the repair gives the failing check's exit code
- AND the repair gives the failing check's log tail
- AND the next round continues from the new session identifier the resume returned
- AND when the checks then pass, the run ends `ok` with two rounds recorded

### scenario.workers.validation-reads-result — The round validation receives the round's result

- GIVEN a worker that ended `ok` with a clean audit
- AND a round validation
- WHEN the host calls the round validation
- THEN the host passes the worktree
- AND the host passes the round's node folder
- AND the host passes the round's worker result as the worker returned it

### scenario.workers.rounds-exhausted — Checks that keep failing end the run

- GIVEN a round validation that runs a configured check, as Concorde's does
- AND the configured check fails after every round
- AND the round validation asks a run whose checks still fail to end with `checks_failed`
- WHEN the configured number of resume rounds is used
- THEN the run ends `failed` with `checks_failed` and the last check results
- AND its error gives `exhausted` as the reason
- AND its error lists each round's failing checks as attempts
- AND its error has one cause per failing check with its exit code and the end of its log
- BUT no further round is started

### scenario.workers.blocked-not-resumed — A blocked worker goes to the main agent

- GIVEN a worker that changes nothing outside its `rw` list
- AND the worker ends `blocked` because its Module's Spec does not state a promise it needs
- WHEN the host finishes the round
- THEN the audit still runs
- AND the audit is clean
- BUT no round validation runs
- AND therefore no configured check runs
- AND no resume round follows
- AND the run ends `blocked` with the worker result verbatim
- AND the run's error is Workers' `worker_blocked` link, of level `workers`
- AND that link's one cause is the worker's own error, unchanged, with the level `worker`

## Host failures

### scenario.workers.timeout — A round past its deadline is killed

- GIVEN a worker still running at its round's timeout
- WHEN the deadline passes
- THEN the host kills the worker's whole process group
- AND the run ends `failed` with `worker_timeout` and a run record

### scenario.workers.interrupted-run — An interrupted run still ends

- GIVEN a worker run whose launcher is told the run identity as soon as the run exists
- WHEN before the run returns, it is interrupted from outside in a way its host can handle, such as
  a termination signal or the cancellation of the run that launched it
- THEN its run record ends `failed` with the error `interrupted`, of reason `environment`
- AND that error names the interruption
- AND its [progress file](../../glossary.json#concept.progress-file) is `finished` with status
  `failed`
- AND the interruption travels on to the launcher
- AND when the interruption comes while the worker of a round still runs, after its output named
  the session, the [run directory](../../glossary.json#concept.run-directory) keeps that session's
  transcript

### scenario.workers.invalid-result — A worker without a valid result has failed

- GIVEN a worker round whose agent process ends normally, within its timeout and limits
- AND the agent process ends with no process error of its backend
- AND the worker round changes nothing outside the grant's `rw` list
- AND the worker round ends without a structured result that satisfies the worker result schema:
  with none, with a status other than `ok`, `blocked` and `failed`, with a `blocked` or `failed`
  result without an error, or with an `ok` result with one
- WHEN the host reads its output
- THEN the run ends `failed` with `worker_result_invalid` and the schema violation or the worker's
  final text in its error
- AND the round's standard error is its `stderr.log`
- AND the transcript path is in the run record

### scenario.workers.claude-error — An error of Claude Code itself is reported with its cause

- GIVEN a worker whose Claude Code session ends with an error subtype, such as the turn limit,
  instead of a structured result
- WHEN the host reads its output
- THEN for a turn or budget limit, the run ends `failed` with `worker_limit_reached`
- AND otherwise, the run ends `failed` with `claude_failed`
- AND the error's cause is the Claude Code process's link with the subtype
- AND the cause gives the turn count
- AND the cause gives the cost
- AND the cause gives the final text
- AND the cause gives the tail of standard error

## The pi backend

### scenario.workers.pi-fenced-run — A pi worker is fenced by the same grant

- GIVEN a run whose worker runs on pi
- AND an `implement` grant with a `rw` source file
- AND the grant has `ro` Specs
- AND the grant has another Module's `ro` source file
- AND a file no grant list names
- WHEN the host runs a pi worker that reads the Specs
- AND the worker edits the source file
- AND the worker ends with `concorde_result`
- THEN the edit reaches the worktree
- AND the audit is clean
- AND the run ends `ok` with the worker result verbatim
- AND the run record holds the session identifier
- AND the run record holds the transcript path
- AND the run record holds the tool set of the pi backend

### scenario.workers.pi-file-tools-denied — pi file tools explain every denial

- GIVEN a running pi worker
- WHEN it reads a `names` file, an ungranted file, the task worktree's `.git`, a submodule's `.git`,
  a file of the common Git directory, a source file of the primary worktree outside the task
  worktree, with that primary worktree outside the user's home, a file of its runtime directory's
  `config/`, or a granted name that does not exist whose other spelling, such as its NFD form, is an
  ungranted file pi's `read` would open instead, or writes a `ro` file, an undeclared file or a
  submodule's `.git`
- THEN each call is denied with the reason the Harness's read or write table gives, prefixed
  `Concorde grant:`
- AND no file changes

### scenario.workers.pi-commands-sandboxed — pi commands see only the grant

- GIVEN a running pi `implement` worker
- WHEN it greps a directory holding ungranted files, or uses bash to read an ungranted file, to
  write a `ro` file or to reach the network
- THEN grep reports matches only from readable files
- AND the bash read finds no such file
- AND the write fails as a read-only file system
- AND the network request is refused
- BUT bash can read `ro` files
- AND bash can write `rw` files
- AND bash's temporary files go to the run's private `TMPDIR`
- AND bash can write that `TMPDIR`

### scenario.workers.pi-runtime-missing — A pi run without its runtime is refused

- GIVEN a run whose worker runs on pi, on a machine without the sandbox-runtime package
- WHEN the host is asked to start a worker
- THEN it refuses before launch with `pi_runtime_missing`, naming the missing package and how to
  install it
- AND it still writes the run record

### scenario.workers.pi-settings-independent — A pi worker takes nothing from the user's pi settings

- GIVEN a user's pi settings file that either chooses a default provider, model and thinking level,
  enabled models, per-model thinking levels, packages and other settings, or is one pi would refuse
- AND a [worker configuration](../../glossary.json#concept.worker-configuration) that chooses a
  model and a level for a pi worker
- WHEN the host prepares the worker's runtime directory
- AND the host launches the worker
- THEN its generated pi settings hold only `defaultProjectTrust` `never`
- AND the run is not refused
- AND the worker is launched with the local id the
  [model map](../../glossary.json#concept.model-map)
  gives the configured model, as `--model`
- AND the worker is launched with the configured level, as `--thinking`
- AND its pi configuration directory holds copies of the user's `auth.json` and `models.json`

### scenario.workers.pi-invalid-result-retried — pi refuses an invalid result and accepts a valid one

- GIVEN the permission extension of a pi worker, loaded with pi's own tool definitions
- WHEN pi validates a `concorde_result` call whose argument breaks the worker result schema
- AND pi then validates one whose argument satisfies the schema
- THEN the first call is refused before the tool runs, naming the field at fault
- AND the session can therefore go on
- AND the second call passes
- AND the tool asks pi to end the run

### scenario.workers.pi-budget-limit — A pi run over its budget stops

- GIVEN the permission extension of a pi worker whose `max_budget_usd` is set
- WHEN the costs its assistant messages report add up to more than that budget
- THEN the permission extension appends a `concorde-limit` entry naming the budget
- AND the entry names the cost reached
- AND the entry names the maximum
- AND the permission extension aborts the run once
- AND it blocks every later tool call, naming the budget limit
- BUT the cost of a message that is not the assistant's is not counted

### scenario.workers.pi-limit — A pi run over its turn limit stops

- GIVEN a pi worker whose turns exceed `max_turns`
- WHEN the [permission extension](../../glossary.json#concept.permission-extension) counts the turn
- THEN it aborts the run
- AND it records the limit reached
- AND the run ends `failed` with `worker_limit_reached`
- AND the error's cause is the pi process's link with the limit and the value reached
- AND the cause gives the reason `exhausted`
- AND the cause is never a Claude Code process's link

## Worker models

### scenario.workers.backend-configured — Workers run on pi unless their configuration chooses Claude Code

- GIVEN a command started from a Claude Code session
- AND both programs are installed
- AND a [worker configuration](../../glossary.json#concept.worker-configuration) whose default
  gives a pi model
- AND the configuration puts `spec_panel`'s worker `reviewer2` on `claude` with a Claude Code model
  and a level
- WHEN the choices of `spec_panel`'s `reviewer1` and `reviewer2` are resolved
- THEN `reviewer1` runs on pi with the default's model, as the local id the
  [model map](../../glossary.json#concept.model-map) gives it on pi
- AND the choice names that id and the map
- AND `reviewer2` runs on `claude` with the model and level of its own entry

### scenario.workers.backend-default — Without a configuration entry a worker runs on pi

- GIVEN a command started from a Claude Code session
- AND a worker configuration whose default names only a model
- WHEN the choice of `implement`'s worker is resolved
- THEN it runs on `pi`, from Concorde's default
  [worker backend](../../glossary.json#concept.worker-backend), not from the program of the
  [main agent](../../glossary.json#concept.main-agent)

### scenario.workers.backend-missing — A worker whose backend is not installed is refused

- GIVEN a command started from a Claude Code session
- AND a worker configuration that puts `spec_panel`'s worker `reviewer2` on `claude`
- AND no `pi` command is installed
- WHEN the choices of `implement`'s worker and of `spec_panel`'s `reviewer2` are resolved
- THEN the worker that runs on pi is refused with `backend_missing`
- AND the refusal names the worker
- AND the refusal names the source of its backend
- AND the refusal names the command it looked for
- AND the refusal names how to choose Claude Code for the worker
- AND the worker never runs on Claude Code instead
- BUT `reviewer2`, on `claude`, still resolves

### scenario.workers.models-listed — The installed program's models are the candidates

- GIVEN pi listing two models with credentials, one of them without reasoning
- AND Claude Code whose user settings name a model
- AND Claude Code's environment pins another model
- WHEN Workers lists the candidates of each backend
- THEN the pi listing names both as `provider/model`
- AND the pi listing names the reasoning one with pi's thinking levels
- AND the pi listing names the other with only `off`
- AND the pi listing is marked complete
- AND the Claude Code listing names the aliases with Claude Code's effort levels
- AND the Claude Code listing names the settings' model with Claude Code's effort levels
- AND the Claude Code listing names the pinned model with Claude Code's effort levels
- AND the Claude Code listing is marked incomplete
- AND the Claude Code listing says why

### scenario.workers.models-listed-mapped — The listing names the project model names the map gives

- GIVEN pi listing a model with credentials
- AND a [model map](../../glossary.json#concept.model-map) that maps one project model name to that
  model on pi
- AND the map maps another project model name to a pi id pi does not list
- WHEN Workers lists the candidates of pi
- THEN the listing names the first project model name for its candidate
- AND it names the other project model name with its unlisted id

### scenario.workers.models-listed-unmapped — Discovery without a model map still lists

- GIVEN pi listing a model with credentials
- AND no model map
- WHEN Workers lists the candidates of pi
- THEN the listing names the model
- AND the listing reports the map's refusal, without refusing the listing

### scenario.workers.models-backend-missing — Discovery refuses a program that is not installed

- GIVEN a backend whose program is not installed
- WHEN Workers lists the candidates of that backend
- THEN the listing is refused with `backend_missing`

### scenario.workers.model-resolution — The most specific entry wins, field by field

- GIVEN a configuration with a default model and level
- AND the configuration has a model for `spec_panel`'s default
- AND the configuration has a model for its worker `reviewer2`
- AND the configuration has a level for its worker `chair`
- WHEN the choice of `reviewer1` is resolved
- AND the choice of `reviewer2` is resolved
- AND the choice of `chair` is resolved
- AND the choice of `implement`'s `worker` is resolved
- THEN `reviewer1` gets the [Operation](../../glossary.json#concept.operation)'s model and the
  default level
- AND `reviewer2` gets its own model
- AND the `chair` gets the Operation's model and its own level
- AND `implement` gets the default
- AND each names the entry it came from

### scenario.workers.model-levels — A model's own level applies when the entry that chose it sets none

- GIVEN `enabled_models` giving two models a level of their own
- AND `enabled_models` gives a third model none
- AND a default naming the first model without a level
- AND a level for `spec_panel`'s default
- AND a `spec_panel` worker naming the second model without a level
- AND a `spec_panel` worker naming the second model with a level
- AND a `spec_panel` worker naming the third model
- WHEN the choices are resolved
- THEN a worker on the default gets its model's own level
- AND a worker with no entry of its own in `spec_panel` gets the Operation's level
- AND a worker whose entry names the second model without a level gets that model's own level
- AND a worker whose entry sets a level gets its own level
- AND the worker on the third model keeps the Operation's level
- AND a worker with no level anywhere gets none
- AND for that worker, its program's built-in default remains

### scenario.workers.model-level-refused — A model's own level its backend lacks is refused

- GIVEN `enabled_models` giving a model a level of neither backend, or a level the backend of a
  worker taking that model does not have
- WHEN the configuration is checked
- THEN it is refused with `config_invalid`

### scenario.workers.model-unresolved — A worker whose configuration names no model is refused

- GIVEN a worker configuration whose default sets only a level
- AND the configuration names a model for `general`'s default
- AND the configuration puts `spec_panel`'s `chair` on `claude` without a model
- WHEN the choice of `general`'s `reviewer` is resolved
- AND the choice of `implement`'s worker is resolved
- AND the choice of `spec_panel`'s `chair` is resolved
- THEN the reviewer gets the model of its Operation's default
- AND `implement`'s worker and the chair are refused with `model_unresolved`
- AND each refusal names the worker
- AND each refusal names every entry its model may come from, from its own entry to the default
- AND each refusal names how to set a model
- AND each refusal says that no program's or developer's default model is used

### scenario.workers.model-custom-accepted — Validation admits a custom model without discovery

- GIVEN a configuration whose enabled and default model is a custom project model name that no
  discovery lists
- WHEN the shared validator checks it without installed backends or credentials
- THEN the configuration is accepted
- AND a worker's choice names the custom model

### scenario.workers.model-refused — Validation refuses invalid entries

- GIVEN a configuration with invalid structure, an Operation or worker name its caller does not
  declare, a malformed `enabled_models` entry, an enabled model named by one program's id such as
  `local-openai/gpt-6` rather than a project model name, or a reasoning level outside the effective
  backend's vocabulary
- WHEN the shared validator checks it
- THEN it is refused with `config_invalid`

### scenario.workers.model-not-enabled — A model outside the enabled models is refused

- GIVEN a worker configuration whose `enabled_models` admits two models
- WHEN the default, an Operation's default or a worker's entry names a third model
- THEN the whole configuration is refused with `model_not_enabled`
- AND the refusal names the entry
- AND the refusal names the model
- AND the refusal names the enabled models
- AND the refusal names how to repair the configuration

### scenario.workers.enabled-models-required — A configuration without enabled models is refused

- GIVEN a worker configuration without `enabled_models`, or with an empty one
- WHEN the shared validator checks it
- THEN it is refused with `config_invalid` saying that the list is required

### scenario.workers.config-missing — A worktree without a worker configuration runs no worker

- GIVEN a worktree without `.concorde/workers.json`
- WHEN Workers reads the worker configuration for a launch
- THEN it is refused with `config_missing`
- AND the refusal names the file
- AND the refusal names what the file must hold
- AND the refusal says that the file must be committed
- AND it says that a worker's model is never taken from the developer's own pi or Claude Code
  settings

### scenario.workers.model-config-invalid — An unreadable configuration is reported, never ignored

- GIVEN a worktree whose `.concorde/workers.json` is not valid JSON, has a field the schema does not
  know or has a schema version other than 2, the one Workers reads, and 1, the retired one
- WHEN Workers reads it
- THEN it is refused with `config_invalid`, naming the file and what is wrong with it
- AND for another schema version, the refusal names the version Workers expects

### scenario.workers.model-config-v1 — A configuration of schema version 1 is refused with how to convert it

- GIVEN a worktree whose `.concorde/workers.json` has schema version 1, whose models are local ids
  such as `local-openai/gpt-6`
- WHEN Workers reads it
- THEN it is refused with `config_invalid`
- AND the refusal says to rename each model to a project model name
- AND the refusal says to set the version
- AND the refusal says to map each name in the model map

### scenario.workers.limits-default — Without limits a launch gets the default limits and runtime paths

- GIVEN a worktree whose `.concorde/workers.json` sets neither `limits` nor `runtime`
- WHEN Workers reads the limits and runtime paths of a launch
- THEN it gets the default limits and the runtime paths `.venv` and `node_modules`

### scenario.workers.limits-configured — Limits and runtime paths come from the worker configuration

- GIVEN a worktree whose `.concorde/workers.json` sets `limits.max_turns`
- AND the configuration sets `limits.rounds`
- AND the configuration sets a `runtime` list
- WHEN Workers reads the limits and runtime paths of a launch
- THEN it gets its own `max_turns`
- AND it gets its own `rounds`
- AND it gets its own runtime paths
- AND it gets the default for every limit it does not set

### scenario.workers.retired-configuration — The untracked configuration of earlier versions is refused, not ignored

- GIVEN a worktree that has the untracked `.concorde/worker-models.json` of earlier versions and no
  `.concorde/workers.json`
- WHEN Workers reads the worker configuration
- THEN it is refused with `config_invalid`, naming both files
- AND the refusal says to move the models into `.concorde/workers.json`
- AND the refusal says to commit it
- AND the refusal says to delete the old file

### scenario.workers.retired-configuration-beside — Beside a worker configuration the untracked file is not read

- GIVEN a worktree that has both the untracked `.concorde/worker-models.json` of earlier versions
  and `.concorde/workers.json`
- WHEN Workers reads the worker configuration
- THEN it reads `.concorde/workers.json`

## The model map

### scenario.workers.model-map-location — The model map is the named file, else the user's XDG configuration

- GIVEN an environment that names a model map in `CONCORDE_MODEL_MAP` by an absolute path, or names
  none and sets an absolute `XDG_CONFIG_HOME`, a relative one or none
- WHEN Workers finds the [model map](../../glossary.json#concept.model-map)
- THEN when the environment names a model map, it is the named file
- AND otherwise, for an absolute `XDG_CONFIG_HOME`, it is `concorde/models.json` of that directory
- AND otherwise, for a relative one or none, it is `~/.config/concorde/models.json`

### scenario.workers.model-map-relative — A model map named by a relative path is refused

- GIVEN an environment whose `CONCORDE_MODEL_MAP` is not an absolute path
- WHEN a worker is resolved
- THEN it is refused with `model_map_invalid`

### scenario.workers.model-map-resolved — A project model name resolves to its local id on the worker's backend

- GIVEN a worker configuration choosing the project model `gpt-6-astra` by default and
  `claude-opus-5-5` for `spec_panel`'s `reviewer1`
- AND a model map giving `gpt-6-astra` a pi id
- AND the map gives `claude-opus-5-5` ids on both programs
- AND the map gives ids for a model no project enables
- WHEN the choices of `implement`'s worker and `spec_panel`'s `reviewer1` are resolved
- THEN each runs on pi with its project model name
- AND each runs with its level
- AND each runs with the pi id of its model
- AND each names the map it came from

### scenario.workers.backend-switch — An entry choosing a backend inherits the model and level

- GIVEN a worker configuration whose default chooses a model and a level
- AND the configuration puts `spec_panel`'s `chair` on `claude` without a model or level
- AND a model map giving the default's model a pi id only
- WHEN the chair's choice is resolved
- THEN resolving the worker configuration chooses `claude` for the chair
- AND resolving the worker configuration gives the chair the default's model and level
- AND the chair's model and level each name the default as their source
- BUT since the map gives that model no Claude Code id, resolving the model map then refuses the
  chair with `model_unmapped` before any worker launches
- AND the refusal names the worker
- AND the refusal names its backend and model with their sources
- AND the refusal names the map
- AND the refusal names the programs the model is mapped for
- AND the refusal names the exact entry to add
- AND the refusal says that a project model name is never used as a local id

### scenario.workers.model-unmapped — A model the map gives no id for the worker's backend is refused

- GIVEN a model map that does not name the default's model
- WHEN a worker on that model is resolved
- THEN it is refused with `model_unmapped`, saying that the map does not name the model at all

### scenario.workers.model-map-checked — An Operation's workers are checked against the map in one refusal

- GIVEN a worker configuration
- AND a model map that lacks the ids of several models the workers of `spec_panel` would run on,
  on the backends that would run them
- AND the map lacks the id of a model only another Operation's worker takes
- WHEN the configuration reader checks the workers of `spec_panel` against the map, as the run of
  `spec_panel` asks before its first worker launches
- THEN one `model_unmapped` refusal names every model and backend the map lacks for `spec_panel`,
  with the workers that would take each
- AND the refusal names the map
- BUT the refusal names nothing of the other Operation
- AND once the map gives each its id, the check passes

### scenario.workers.refusal-reasons — Every refusal before a run has its fixed reason

- GIVEN the configuration reader has these refusals:
- AND `config_missing`
- AND `config_invalid`
- AND `model_not_enabled`
- AND `model_unresolved`
- AND `backend_missing`
- AND `model_map_missing`
- AND `model_map_invalid`
- AND `model_unmapped`
- WHEN each refusal's reason is looked up
- THEN the four refusals of the worker configuration give `input`
- AND the program's and the model map's refusals give `environment`

### scenario.workers.model-map-missing — A missing model map is refused, never ignored

- GIVEN no model map
- WHEN a worker is resolved
- THEN it is refused with `model_map_missing`
- AND the refusal names the file
- AND the refusal shows what the file holds
- AND the refusal says that the model map belongs to the machine
- AND the refusal says that the model map is never committed

### scenario.workers.model-map-invalid — An unreadable model map is refused, never ignored

- GIVEN a model map that is not valid JSON, has a duplicate key, another schema version, a model
  without an id, an unknown program or a name that is not a project model name
- WHEN a worker is resolved
- THEN it is refused with `model_map_invalid`, naming the file and what is wrong with it

## Discovering models

### scenario.workers.models-standalone — Discovery works outside a worktree

- GIVEN a directory outside Git with configured agent programs
- WHEN `python3 scripts/available_models.py --backend pi` or `--backend claude` runs, with optional
  `--json`
- THEN it lists configured candidates with sources and reasoning levels
- AND it explains that no inference API access was probed
- AND pi uses its credentialed listing
- AND Claude's aliases and settings-derived list is explicitly incomplete

### scenario.workers.models-standalone-missing — Discovery without the program reports an error and gates nothing

- GIVEN a directory outside Git and a backend whose program is missing or whose listing fails
- WHEN `python3 scripts/available_models.py --backend` names that backend, with `--json`
- THEN it exits with status 1 and a discovery error, such as `backend_missing`, naming the program
- AND since validation never runs discovery, no worker configuration depends on that error

## What a run leaves

### scenario.workers.cleanup-failed — A cleanup that failed fails the run

- GIVEN a worker run whose worker ends `ok`, or `blocked`
- WHEN the host cannot remove its runtime directory, or cannot keep its transcript
- THEN the run ends `failed` with `cleanup_failed` and the reason `environment`
- AND the error names what remains and the operating system's error
- AND for the `blocked` worker, the error's cause is the link the run would otherwise have ended
  with, `worker_blocked`
- AND a transcript that could not be kept is named by no record

### scenario.workers.trace-failure-reported — A refused trace write is reported, never silent

- GIVEN a worker run whose first round's `trace.json` the operating system refuses to write
- WHEN the worker ends `ok`, or `blocked`
- THEN the `ok` run still ends `ok`
- AND the `ok` run's returned record and its node's content list each refused write in
  `trace_failures`
- AND each listed write names the file
- AND each listed write names the moment
- AND each listed write names the error
- AND the `blocked` run's error carries each refused write as `trace-write` evidence

### scenario.workers.trace-left — A worker run leaves its trace and no credentials

- GIVEN an Operation run whose worker needs two rounds, the first failing a configured check
- AND the backend's configuration holds a credential copy
- WHEN the run ends
- THEN the run's node holds `workers/<run-id>/`
- AND that directory holds `trace.json`
- AND that directory holds `status.json`
- AND that directory holds `grant.json`
- AND that directory holds `brief.md`
- AND that directory holds `transcript.jsonl`
- AND that directory holds `rounds/1/`
- AND that directory holds `rounds/2/`
- AND each round has its own `trace.json`
- AND each round has its own `stderr.log`
- AND each round has the check nodes its round validation placed
- AND each round's usage holds the tokens the agent program reported for it
- AND each round's usage holds the cost the agent program reported for it
- AND each round's usage holds the turns the agent program reported for it
- AND on the Claude Code backend, when Claude Code did not give `permission_denials`, each round's
  content keeps null for the result envelope's `permission_denials`
- AND on the Claude Code backend, otherwise, each round's content keeps the result envelope's
  `permission_denials` as Claude Code gave it
- AND on the Claude Code backend, when Claude Code did not give `modelUsage`, each round's content
  keeps null for the result envelope's `modelUsage`
- AND on the Claude Code backend, otherwise, each round's content keeps the result envelope's
  `modelUsage` as Claude Code gave it
- AND on the Claude Code backend, when Claude Code did not give `duration_api_ms`, each round's
  content keeps null for the result envelope's `duration_api_ms`
- AND on the Claude Code backend, otherwise, each round's content keeps the result envelope's
  `duration_api_ms` as Claude Code gave it
- AND the runtime directory, with the credential copy, no longer exists
- AND while the worker ran, the worker run's `trace.json` was already there, `running`
