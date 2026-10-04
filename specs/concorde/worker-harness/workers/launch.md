# Run mechanics

This document states the exact mechanics of one worker run and the requirements they serve. The
mechanics cover these parts of the run:

- files
- command lines
- environment
- audit
- rounds
- records

The following hold for both backends:

- inputs
- placement
- the [run directory](../../glossary.json#concept.run-directory)
- the [runtime directory](../../glossary.json#concept.runtime-directory)
- the [progress file](../../glossary.json#concept.progress-file)
- the audit
- rounds
- the run record
- errors

The launch below is the Claude Code backend's. [The pi run mechanics](pi.md) state what the pi
backend does instead. The Harness generates the following, which the run places in the runtime
directory's `control/`:

- the [worker settings](../../glossary.json#concept.worker-settings)
- the write hook
- the tool sets

The Harness's [Claude Code mechanics](../harness/claude-code.md) state these. The [entry](module.md)
explains why the run is shaped this way. [The worker result contract](contracts.md) fixes the
worker's answer.

## Inputs

A run is requested with:

| Input | Meaning |
| --- | --- |
| backend | `claude` or `pi`: the [worker backend](../../glossary.json#concept.worker-backend) the worker configuration chooses for the worker, pi when nothing chooses one |
| worktree | Absolute path of the Git worktree the worker works in, lying directly in `.claude/worktrees/` of its repository's primary worktree ([Placement](#placement)): in Concorde a bound workspace's worktree, or for an [unbound run](../../glossary.json#concept.unbound-run) its [unbound checkout](../../glossary.json#concept.unbound-checkout), which the caller passes like any worktree |
| parent | The [trace node](../../glossary.json#concept.trace-node) folder the caller gives, in Concorde the node of the run that asks for the worker, below which the worker run's node is created |
| [task type](../../glossary.json#concept.task-type) | One of the eight Protocol task types; it selects the tool set, the read-only one for a task type that writes nothing, such as `review-architecture` |
| grant | The frozen grant as data, in the worker harness's [grant input](contracts.md#grant-input): every path with its level `rw`, `ro` or `names`, relative to the worktree, and its [context identity](../../glossary.json#concept.context-identity); a grant with no `rw` path makes a worker that changes nothing, which is how a caller runs a reading worker |
| instructions | The caller's task-specific part of the brief: in Concorde, an [Operation](../../glossary.json#concept.operation)'s prompt with the definitions of the glossary terms its grant carries and the rules for a [Spec gap](../../glossary.json#concept.spec-gap), which Method composes |
| round validation | Optionally the caller's callback, called after every round whose worker ended `ok` with a clean audit ([Round validation](#round-validation)) |
| runtime paths | Extra absolute paths, outside the grant, that every tool of the worker may read and none may write, exactly as the caller lists them: the worker configuration's runtime paths that exist, such as `.venv` or `node_modules`, the directories the project interpreter needs, and the host material the caller admits for this run alone, such as the folder of the check logs its own run recorded ([Reading beside the grant](#reading-beside-the-grant)) |
| project interpreter | Optionally the absolute path of the project's own Python interpreter, which the caller resolved from the project's configuration as its checks run it; its directory comes first on the worker's `PATH` and the brief names it |
| limits | Timeout per round, the turn limit, the budget limit when the configuration sets one, and the number of [resume rounds](../../glossary.json#concept.resume-round) (default 3) |
| model | The project model name the run worktree's [worker configuration](../../glossary.json#concept.worker-configuration) chooses for the worker's id, which every Operation gives, recorded only |
| local model, model map | The model's local id on the backend, which the [model map](../../glossary.json#concept.model-map) gives it and which is passed with `--model`, and the path of that map, recorded only |
| operation, worker, modules | The Operation and the [worker id](../../glossary.json#concept.worker-id) the model was chosen for and the [Modules](../../glossary.json#concept.module) the job is about, labels the caller gives, recorded only |
| reasoning | Optionally the reasoning level from the same configuration, passed with `--effort` on the Claude Code backend and `--thinking` on the pi backend |

## Placement

Every worktree a worker runs in lies directly in `.claude/worktrees/` of its repository's primary
worktree. The primary worktree is the first worktree `git worktree list` names. In Concorde, the
worker runs in a task worktree `.claude/worktrees/<task>` or an
[unbound checkout](../../glossary.json#concept.unbound-checkout) `.claude/worktrees/unbound-<run-id>`.
Before it generates anything, the host checks this with read-only Git. With `worktree_misplaced`,
the host refuses any other placement, the primary worktree itself included. Once the placement
holds, the host collects the repository's **Git administrative paths**, as real paths:

| Path | Found by |
| --- | --- |
| the common Git directory, with its `worktrees/` and `modules/` | `git rev-parse --git-common-dir` in the worktree |
| the worktree's own Git directory | `git rev-parse --git-dir` in the worktree |
| every `.git` entry of the worktree, file or directory: its own and each submodule's or nested repository's | a walk of the worktree that enters no `.git`, no symbolic link and no runtime path |
| for each `.git` file, the Git directory its `gitdir:` line names and that directory's `commondir` | reading the file |

The host hands the Harness the primary worktree and these paths with the grant. Wherever the
repository lies, the Harness hides them from every tool
([Claude Code mechanics](../harness/claude-code.md#deny-rules),
[pi mechanics](../harness/pi.md#read-table)). Every worktree a worker runs in lies in the primary
worktree. Therefore, as it hides the user's home, the Harness also hides the primary worktree as a
whole, except for the following:

- the way to the worktree
- the runtime paths
- what the grant makes readable

## Reading beside the grant

The grant is the whole of what a worker may read of the project. The runtime paths are the only
other material it may read. Its caller alone decides the runtime paths. Workers hands them to the
Harness exactly as given, adding none and widening none. On both backends, the Harness makes each
readable, and none writable, to every tool ([Claude Code
mechanics](../harness/claude-code.md#deny-rules), [pi mechanics](../harness/pi.md#read-table)). The
runtime paths change neither the grant nor its context identity. They reach the generated worker
settings or permission extension. The run record keeps the digest of those settings or extension.

When a caller lets a worker read host material, it lists the folder that holds only that material.
The full logs of checks the caller's own run recorded are one example. The caller never lists
the trace node or task folder around the material. Since the brief lists only the grant, the
caller names the files its worker should read in its task instructions. The worker reads them at
their absolute paths, like any `ro` file.

The project interpreter is the one other thing a caller may give. On both backends, Workers puts
its directory first on every round's `PATH`, ahead of the host's own `PATH`. The brief also names
the project interpreter. Both make `python` the project's interpreter. The host's own environment is
never changed. Workers never resolves the interpreter itself. Running the interpreter needs its
environment and the installation it links to readable. The caller therefore lists them among the
runtime paths.

## Round validation

Whether a round left something to repair is the caller's judgement, not the worker harness's. The
worker harness does none of the following:

- run a check
- read a [Spec](../../glossary.json#concept.spec)
- know a glossary

A caller that has such a judgement passes a **round validation**, a callback. After every round
whose worker ended `ok` with a clean audit, the host calls the callback once with the following:

- the worktree
- the folder of the round's trace node
- the round's [worker result](../../glossary.json#concept.worker-result), valid against its schema

The caller may therefore judge what the worker returned as well as what it changed. The callback
answers with:

| Field | Meaning |
| --- | --- |
| evidence | The values to keep with the round as its evidence, in the caller's own shape, possibly none; nodes of its own, such as check nodes, it places below the round's folder, and a top-level string of an evidence value that is an absolute path below that folder is an artifact path, which the round's node keeps relative to its folder and the returned record absolute |
| repair | Nothing, or the text naming what the worker must repair, which becomes the next resume round's prompt |
| failure | With a repair, whether the run must end `failed` when no rounds are left for it, and then the code and the causes of Workers' link; without, a repair left over at the last round leaves the round's result for the caller to judge |
| violation | Instead of a repair, when the round did something its caller does not allow at all: the code and the causes of Workers' link, which ends the run `failed` at once, with no further round, as an audit violation does |
| unavailable | Instead of the fields above, when it could not validate at all: the code and the causes of Workers' link, which ends the run `failed` with no further round |

In Concorde, Method's round validation runs the
[configured checks](../../glossary.json#concept.configured-check) through Check execution. These
are the checks of the bound Modules and of every Module that uses one of them. Method's round
validation keeps their [check results](../../glossary.json#concept.check-result) as evidence. For a
failing check, Method's round validation names the following as the repair:

- its identity
- its status
- its exit code
- the last 20,000 bytes of its log

For a run whose checks still fail, it asks the run to end with `checks_failed` and one link per
failing check. When the checks cannot run, it answers `checks_unavailable` with Check execution's
link. Once the checks pass, a step's own validation adds what it finds to the repair. Such
validation includes the structural validation of a Spec-writing step.

Where the grant makes the project glossary writable, Method's round validation also audits the
glossary by entry. Every [Module](../../glossary.json#concept.module)'s concepts share that one
file. The audit covers these entries:

- entries the round added
- entries the round changed
- entries the round removed

When a Module outside the grant owns such an entry before or after the round, the round validation
answers a violation `audit_violation`. The violation names
`<glossary>#<concept> (owner before: <Module>, after: <Module>)` for every such entry
([How an Operation runs its workers](../../method/workers.md)).

## Run directory and runtime directory

A worker run keeps what analysis needs and what it only needs while it runs apart. Its **run
directory** is its [trace node](../../glossary.json#concept.trace-node) `workers/<run-id>/` inside
the trace node folder its caller gave. Thus, a worker run lies inside the run that launched it.
`<run-id>` is `w-<YYYYMMDD>T<HHMMSS>-<6 hex digits>`. The host chooses this unique identity.

| Path | Content | Worker access |
| --- | --- | --- |
| `trace.json` | The node's record, whose content is the [run record](../../glossary.json#concept.run-record) ([worker run trace](contracts.md#contract.workers.worker-run-trace)) | none |
| `status.json` | The progress file | none |
| `grant.json` | The frozen grant and its context identity | none |
| `brief.md` | The brief as sent | none |
| `transcript.jsonl` | The latest session's transcript, of the session the worker's output named last, even in a round interrupted before it returned, moved here from `config/` when the run ended | none |
| `rounds/<n>/` | Each round's node: `trace.json` ([worker round trace](contracts.md#contract.workers.worker-round-trace)), the round's standard error `stderr.log` and the nodes its round validation placed, such as Concorde's check nodes `checks/<check-id>/` | none |

Its **[runtime directory](../../glossary.json#concept.runtime-directory)** is a private directory
created for the run. Where `/tmp` is writable, the directory is `/tmp/concorde-<suffix>-<random>/`.
Where `/tmp` is not writable, as inside a check boundary, the directory is under the system
temporary directory. When the run ends, however it ends, the host removes the runtime directory
after moving the transcript into the run directory. The host removes the credential copies in
`config/` first, then the rest. The host opens up any directory the worker's own tools left
unwritable or unreadable. The host checks that the directory is gone.

If the host could not keep a transcript or remove a runtime directory, the run ends `failed` with
`cleanup_failed`. The error names what remains and why. Unless the host process itself is killed
outside its control, by `SIGKILL`, credentials therefore never outlive the run unnoticed. Such a
kill leaves the directory to the system's temporary-file cleaning, as
[the entry](module.md#where-a-runs-files-live) explains. The runtime directory holds:

| Path | Content | Worker access |
| --- | --- | --- |
| `control/settings.json` | The worker settings (Claude Code backend) | none |
| `control/write_hook.py` | The [write hook](../../glossary.json#concept.write-hook) with the task worktree and the grant's `rw`, `ro` and `names` lists embedded (Claude Code backend) | none |
| `control/result.schema.json` | The [worker result](../../glossary.json#concept.worker-result) schema | none |
| `config/` | The agent's own configuration directory: on the Claude Code backend `CLAUDE_CONFIG_DIR` with the credential copy, sessions and transcripts; on the pi backend see [pi](pi.md#run-directory) | none |
| `home/` | `HOME` | Bash read and write |
| `tmp/` | `TMPDIR` | Bash read and write |
| `work/` | The working directory | Bash read and write |

Claude Code's Bash sandbox creates Unix sockets below `TMPDIR`. A socket path must stay under the
operating system's 108-byte limit. A short directory directly under `/tmp` keeps the socket paths under that limit.

When any deny rule the host generated covers any of these directories, the host refuses to
launch:

- `work/`
- `home/`
- `tmp/`

## Progress file

`status.json` tells an observer what the run is doing while it runs. The run that launched it is
one such observer. The host rewrites it atomically at every phase change and at most once a second
for worker activity:

| Field | Content |
| --- | --- |
| `run_id`, `task_type`, `backend`, `worktree` | the run's identity, task type, backend and worktree |
| `operation_run_id` | the identity of the run that launched it, which its caller gives, by which an observer pairs the two; null when the caller gives none |
| `phase` | `preparing`, `worker`, `audit`, `validation` or `finished` |
| `round` | the current round, from 1 |
| `last_action` | the worker's latest tool call as `tool` and `target` (a path, pattern or the first line of a command, at most 200 characters) with its time, or null |
| `status` | null while running; the final status once `phase` is `finished` |
| `host_pid` | the process identifier, in its own PID namespace, of the process running the run: its caller's process, in Concorde the Execution runner of the run that launched it |
| `started_at`, `updated_at` | UTC times |

The phases follow the [rounds](#rounds). Every round runs the worker and then audits it. Only a
round whose worker ended `ok` with a clean audit goes on to the round validation or to a resume
round. When something outside ends the run and the host can handle it, any phase moves to
`finished` with `interrupted`.

```d2 illustrative
preparing
worker
audit
validation
finished
preparing -> worker: round 1
preparing -> finished: a refusal before launch
worker -> finished: the command could not be started
worker -> audit: the round ended
audit -> finished: timeout, limit, process failure, violation, invalid result, blocked or failed
audit -> validation: ok, clean, a round validation given
audit -> finished: "ok, clean, no round validation: status ok"
validation -> worker: a repair, rounds left
validation -> finished: "nothing to repair, or a repair left for the caller to judge: status ok"
validation -> finished: "a violation, a repair that fails the run with no rounds left, or validation unavailable: status failed"
```

It is an observation aid only: the run record, not the progress file, is the run's evidence.

## Launch

On the Claude Code backend, the first round runs the following command. The runtime directory's
`work/` is the working directory. The brief is on standard input:

```text
claude -p --settings <runtime>/control/settings.json --tools <tool set>
       --json-schema <worker result schema> --output-format stream-json --verbose
       --permission-mode bypassPermissions --allow-dangerously-skip-permissions
       --strict-mcp-config --max-turns <n> [--max-budget-usd <x>] [--model <model>]
       [--effort <level>]
```

Only when the worker configuration sets `max_budget_usd`, the host passes `--max-budget-usd`.
Without `--max-budget-usd`, the run has no budget limit.

A resume round runs the same command with `--resume <latest session id>` and the round validation's
repair text as the prompt.

The environment is cleared and then set to exactly:

| Variable | Value |
| --- | --- |
| `PATH` | the host's value, preceded by the project interpreter's directory when the request names one ([Reading beside the grant](#reading-beside-the-grant)) |
| `LANG` | the host's value |
| `HOME` | `<runtime>/home` |
| `TMPDIR` | `<runtime>/tmp` |
| `CLAUDE_CONFIG_DIR` | `<runtime>/config` |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS` | `1` |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` | `1` |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | `1` |
| `ANTHROPIC_API_KEY` | the host's value, only when the host has one |
| the [proxy variables](#proxy) | as that section derives them from the host's |

Before the first round the host copies the user's Claude Code credentials file into `config/`.

The process starts in a new process group. When the round ends for any reason, including a timeout,
the host kills the whole group. The host reads standard output as it arrives. Each tool use in an
assistant message updates the progress file. The final `result` record gives the following for the
round:

- the session identifier
- the exit status
- the tokens
- the cost
- the turns
- the schema-validated structured output

The host keeps the round's standard error, up to its last 80,000 bytes, as `stderr.log` of the
round's node. Thus, no round overwrites another's.

### Proxy

If the host uses a proxy, a worker's model calls leave through it. On both backends, the host
passes on each of these variables that its own environment sets to a non-empty value:

- `HTTP_PROXY`
- `HTTPS_PROXY`
- `http_proxy`
- `https_proxy`

Only when it passes at least one of them, the host also passes each of `NO_PROXY` and `no_proxy`
that its own environment sets. The host applies the following rules to those no-proxy lists:

- When every passed proxy names a loopback host, the host removes the loopback entries listed below.
- Otherwise, the host keeps the lists as they are, so a developer's own proxy elsewhere keeps sending
  loopback direct.
- When nothing is left in a list, the host does not pass it at all.

A loopback host is `localhost` or a loopback address, with or without a scheme. The host removes
these loopback entries under the first rule:

- `localhost`
- `127.0.0.1`
- `::1`
- `[::1]`

Other proxy variables, such as `ALL_PROXY`, never pass. The reason is where a worker runs: in the
network of whatever started it. That network's only way out may be a proxy on loopback. Examples
include a developer's own local model proxy or the sandbox proxy of a
[main agent](../../glossary.json#concept.main-agent) whose own session is sandboxed. Those
variables name the proxy on `localhost` while the no-proxy lists name loopback.

A worker that dropped that proxy could reach no model endpoint behind it. A worker that kept
loopback in its no-proxy lists could not reach an endpoint on `localhost` reachable only through
that proxy. When a worker starts with no proxy in its environment, it gets no proxy variable. The
worker runs exactly as without this rule. The proxy serves the worker's own process only. Its
tools run in their own sandbox without network
([req.workers.bash-sandbox](#req.workers.bash-sandbox),
[req.workers.pi-sandbox](pi.md#req.workers.pi-sandbox)). The sandbox's namespace cannot reach the
proxy.

## Audit

The audit attributes every change since its snapshot to the worker. Therefore, the caller keeps
every other writer away from the following:

- the worktree's files
- its `HEAD`
- its index
- its branch

This isolation lasts from before the snapshot until the run ends, its round validations and the
host's deletions included. Readers may go on
([The caller isolates the worktree](../module.md#the-caller-isolates-the-worktree)). In Concorde,
the [workspace lock](../../glossary.json#concept.workspace-lock) the launching run holds provides
this isolation. The host takes no lock of its own for this.

Before the first round, the host records a snapshot of the worktree. The snapshot holds the
following:

- `HEAD`, as the branch it names and its commit
- the index digest
- the digest of every tracked change and untracked file that already exists, including its content
  and, as Git sees it, its executable bit

After each round, the host runs read-only Git
(`git status --porcelain=v2 -z --untracked-files=all` and the digests of the listed files) and
compares with the snapshot. When Git no longer lists a file of the snapshot, the host measures the
file where it lies. If the file is equal to `HEAD` again, it changed. If the file is gone, as an
untracked file deleted is, it was deleted.

| Observation since the snapshot | Verdict |
| --- | --- |
| a changed or new file whose level is `rw` | allowed |
| a changed or new file of any other level, or of none | violation |
| a deleted file | violation |
| a changed `HEAD`, index or branch | violation |
| a change under a path Git ignores | not observed |

As the Harness reads it, a file's level is that of the grant's most specific entry for it. The
exact entry takes precedence. If there is no exact entry, the longest directory entry above the
file takes precedence. Therefore, a file the grant lists `ro` below a `rw` directory is not
writable. Proposed deletions read the level the same way.

Each round records its audit as an object with:

| Field | Content |
| --- | --- |
| `verdict` | `clean` when nothing is a violation, otherwise `violation` |
| `changed` | every path, relative to the worktree and in path order, whose file was created, changed or deleted since the snapshot |
| `violations` | each violation as one string, in path order after any Git state: `HEAD` for a `HEAD` that names another branch or commit and `index` for a changed index; the path of a file created or changed outside `rw`; and the path followed by ` (deleted)` for a deleted file |

A round whose audit did not run, such as one whose command could not be started, has `audit` null
in its node. The [returned run record](contracts.md#contract.workers.worker-run-record)'s example shows an
audit with violations.

### Proposed deletions

After the last round, when that round's audit was clean and its worker returned a valid
[worker result](../../glossary.json#concept.worker-result), the host performs the worker's
`proposed_deletions`. The host does this whatever the run's outcome otherwise, and alike for each
of these outcomes:

- an `ok` run
- a `blocked` or `failed` worker
- a round that timed out or whose agent process failed after the result
- a round validation that failed the run or could not validate

When the round validation answered a violation, the host performs none, since the caller does not
allow the round at all. When the run was interrupted, the host performs none. Interruption leaves
the worktree as the interruption found it.

As the brief asks of every path in its result, the worker writes each path relative to the
worktree. The host also accepts an absolute path. Once normalized, the host reads it as the same
path in the worktree. If a path normalizes to a path outside the worktree, the host refuses it.
The host judges each path with its directories' symbolic links resolved. Thus, a directory link
below a `rw` directory never lets the host delete a file elsewhere. The host removes a final
symbolic link itself, never its target. If an earlier entry already named a path, the host drops
an entry naming that path. The host then takes each remaining entry in order:

| The proposed path | Outcome | Recorded in |
| --- | --- | --- |
| outside the worktree, outside the `rw` list, or an existing entry that is not a file, such as a directory | refused, nothing changes | `deletions_refused`, as the worker gave it |
| in the `rw` list and absent from the worktree | nothing to do | `deletions_absent`, relative to the worktree |
| an existing file in the `rw` list | deleted | `deleted`, relative to the worktree |
| an existing file in the `rw` list whose deletion fails | left in place; the host goes on with the next | `deletions_failed`, relative to the worktree |

When a deletion failed, the run ends `failed` with `deletion_failed` whatever status it would
otherwise have had. Its error lists what was deleted and what was not. The link the run would
otherwise have ended with is the error's cause. The deletions that succeeded stay done. This
happens after the last round's validation. Therefore, the evidence that validation recorded
describes the worktree before these deletions.

## Rounds

| Worker result and audit | Round validation | Next |
| --- | --- | --- |
| the round timed out, or the agent process failed or reached a limit | not called | end `failed` with `worker_timeout`, `worker_limit_reached` or the backend's process failure code, naming any audit violation in its detail |
| audit violation, whatever the result | not called | end `failed` with `audit_violation` |
| invalid result, audit clean | not called | end `failed` with `worker_result_invalid` |
| `blocked` or `failed`, audit clean | not called | end with the worker's status and `worker_blocked` or `worker_failed` |
| `ok`, audit clean, no round validation given | — | end `ok` |
| `ok`, audit clean | raises instead of answering | end `failed` with `validation_unavailable` |
| `ok`, audit clean | answers unavailable | end `failed` with the code and causes it names, reason `environment` |
| `ok`, audit clean | answers a violation | end `failed` with the code and causes it names, reason `permission` |
| `ok`, audit clean | nothing to repair | end `ok` |
| `ok`, audit clean | a repair, rounds left | resume round |
| `ok`, audit clean | a repair that fails the run, no rounds left | end `failed` with the code and causes it names, reason `exhausted` |
| `ok`, audit clean | a repair that does not fail the run, no rounds left | end `ok`; the caller judges the result |

The rows are tried in this order. The resume prompt is the round validation's repair text.
Whatever ends its round, a valid worker result is kept as the run's `worker_result`. This includes
a timeout or a failed agent process. The worker's claim is evidence even when the run fails.

## Run record

The [run record](../../glossary.json#concept.run-record) is the worker run's `trace.json`. The host
writes it at these times:

- when the run directory is created, with status `running`
- again after every round, once that round's node is written
- finally when the run ends, whatever ends it

Its uniform fields are [Tracing](../../kernel/tracing/contracts.md#contract.tracing.node)'s. They
hold the following:

- the times
- the status
- the outcome
- Workers' error link
- the files of the run directory with their digests
- the metadata the node kinds table lists

The status is one of these values:

- `ok`
- `blocked`
- `failed`

When the configuration named one, and only then, the fields hold the project model name and
reasoning level. The outcome is the status, or `interrupted`. The record's content is the
[worker run trace](contracts.md#contract.workers.worker-run-trace).
That content also holds the model's local id and the model map it came from.

Each round's node is written when the round's worker launches and again after the round's audit
and validation. Its usage holds the following:

- the tokens the agent program reported for the round
- the cache reads and writes the agent program reported for the round
- the cost the agent program reported for the round
- the turns the agent program reported for the round
- the round's duration

Its content is the [worker round trace](contracts.md#contract.workers.worker-round-trace). The
trace's `agent` keeps what the agent program reported beyond those fields. On the Claude Code
backend, this is the following from the result envelope:

- its subtype
- its error flag
- its turn count
- its cost
- its `permission_denials`
- its `modelUsage`
- its `duration_api_ms`

For each field, when the envelope gave none, its value is null. Otherwise, its value is as the
envelope gave it. The `permission_denials` are the tool calls Claude Code refused under the worker
settings. They are evidence for telling a refused worker's
[boundary case](../../glossary.json#concept.boundary-case). The `modelUsage` gives the tokens and
cost of each model the round used. The `duration_api_ms` gives the time spent waiting for the
model. The nodes a round's validation placed, such as Concorde's check nodes, lie
below the round's node. Since its rounds hold what it consumed, a worker run's own usage records
nothing.

Tracing is best-effort for the work and never silent
([req.tracing.written-at-start](../../kernel/tracing/requirements.md#req.tracing.written-at-start)).
When the operating system refuses a write of the run's or a round's `trace.json`, neither the run
nor its status changes. The host lists every such failure as the run's `trace_failures`. Each
failure names the following:

- the file
- the moment
- the error

The returned record completes `trace_failures` with any failure of the final write itself. When
the run does not end `ok`, the host also lists every such failure as `trace-write` evidence of its
error.

Besides the files, the host returns the run record to its caller as the
[returned run record](contracts.md#contract.workers.worker-run-record). This is the run node's
content, with the ordered list of every round's content in place of the number of rounds. Thus,
the caller reads the audits and the round validation's evidence without reading the files. That
value is never stored. The trace nodes are the record that is kept.

## Errors

Every run that does not end `ok` has an `error`. Its top link holds the following:

- the level `workers`
- the actor `Workers run <run-id> (<task type> worker)`
- one of the codes below
- a detail that names the items listed below
- the reason Workers cannot handle the error

The detail names the following:

- the round
- the paths concerned
- the commands concerned
- the messages concerned

Its evidence names the worker run's node as `trace` evidence. The evidence uses the node's
identity with its folder in the detail. Once a session exists, the evidence also names the
transcript. Every code whose round had a write outside `rw` reports that write, even when the
round also timed out or failed otherwise.

| Code | Detail | Reason | Causes |
| --- | --- | --- | --- |
| `grant_unavailable` | which of the task type, grant, context identity or entries is missing | `input` | none |
| `grant_malformed` | the first grant entry that is not an object with a worktree-relative path and a level of `rw`, `ro` or `names`, and what is wrong with it | `input` | none |
| `worktree_misplaced` | the worktree, the primary worktree's `.claude/worktrees/` where it must lie directly, or what Git said when it found no primary worktree | `environment` | none |
| `run_directory_denied` | the deny rule that would cover the worker's own directories of the runtime directory | `environment` | none |
| `snapshot_failed` | the Git command that failed and its output | `environment` | none |
| `launch_failed` | the command that could not be started and the operating system's error | `environment` | none |
| `worker_timeout` | the round and the timeout | `exhausted` | none |
| `worker_limit_reached` | the round and the limit the agent program reported: on Claude Code its turn or budget subtype, on pi the limit and the value the permission extension names | `exhausted` | the agent process's link: the Claude Code process's link, or the pi process's link with that limit and value |
| `claude_failed` | the round and the error Claude Code reported, or that it printed no envelope (Claude Code backend) | `environment` | the Claude Code process's link |
| `pi_runtime_missing`, `pi_failed` | see [the pi run mechanics](pi.md#errors) | `environment` | the pi process's link for `pi_failed` |
| `worker_result_invalid` | the schema violation, or the worker's final text when it gave no structured result | `capability` | none |
| `audit_violation` | every violating path and the worker's own reported status, or that its result was invalid | `permission` | the worker's link, when its result was valid and carries an `error`; none for a valid `ok` result, whose `error` is null, or an invalid one |
| `worker_blocked`, `worker_failed` | the worker's code and detail | `capability` | the worker's link |
| the code the round validation names for a violation, in Concorde `audit_violation` for a glossary entry another Module owns | every violating entry the round validation names | `permission` | the links the round validation names, none in Concorde |
| the code the round validation names when it cannot validate, in Concorde `checks_unavailable` | the round and what the round validation reported | `environment` | the links the round validation names, in Concorde Check execution's |
| `validation_unavailable` | the round and the error the round validation raised instead of answering | `capability` | none |
| the code the round validation names for a repair that fails the run, in Concorde `checks_failed` | what still needs repair and the rounds used; `attempts` lists each round's repair | `exhausted` | the links the round validation names, in Concorde one per failing check, from Check execution |
| `deletion_failed` | every proposed deletion the host performed, every one that failed with the operating system's error, and those it refused or found already absent | `environment` | the link the run would otherwise have ended with, if any |
| `cleanup_failed` | the transcript the host could not keep and the runtime directory it could not remove, each with the operating system's error | `environment` | the link the run would otherwise have ended with, if any |
| `interrupted` | what ended the run from outside before it finished, such as a signal or the cancellation of the run that launched it | `environment` | none |

The **Claude Code process's link** has the level `component`. The link states the following:

- the envelope's subtype
- the error flag
- the turn count
- the cost
- the exit status
- the final text
- the reported errors
- the tail of standard error

For the `error_max_turns` and `error_max_budget_usd` subtypes, its reason is `exhausted`.
Otherwise, its reason is `environment`. The **worker's link** is the worker result's `error` with
the level `worker`. Its actor names the run and the latest session. The worker's link has no
causes. Workers copies it unchanged.

## Refusals before a run

When the caller asks, before it calls the host, the configuration reader settles a worker's
backend, model and level. At the same time, the reader checks the worker's program and the model
map. The caller declares
the Operations and worker ids it may launch. Against those declarations, the reader checks every
name of the configuration. The reader's refusals therefore come before any worker run exists. None
of the following is made for those refusals:

- a run directory
- a progress file
- a run record

Workers writes no error link of its own. Each refusal carries one of these codes and a message.
The message names the file concerned, the worker configuration or the model map. The message says
what is wrong and how to repair it:

| Code | What the message names | Reason |
| --- | --- | --- |
| `config_missing` | the missing `.concorde/workers.json`, what it must hold and that it must be committed | `input` |
| `config_invalid` | the file and its first problem, or the retired file and how to move it | `input` |
| `model_not_enabled` | the entry, the model, the enabled models and how to repair the entry | `input` |
| `model_unresolved` | the worker, every entry its model may come from and how to set one | `input` |
| `backend_missing` | the worker, its program, the source of its backend and how to choose the other program | `environment` |
| `model_map_missing` | the map's path and what it holds | `environment` |
| `model_map_invalid` | the map's path, or the relative path `CONCORDE_MODEL_MAP` gives, and what is wrong | `environment` |
| `model_unmapped` | the map, each worker with its backend and model and where each came from, and the exact entry to add | `environment` |

The caller that asked turns a refusal into a `component` link with the following:

- the actor `Workers (worker configuration)`
- the code
- the message as its detail
- the reason above
- no causes

The caller makes that link the cause of its own link. In Concorde, Method's steps name the
caller's link `worker_model_unavailable`.

## Requirements

### req.workers.frozen-grant — One grant for the whole run

The host SHALL generate the following from one frozen grant for a run:

- settings
- write hook
- tool set
- brief

### req.workers.grant-as-data — The grant comes from the request alone

The host SHALL take a worker's grant only from its request, in the shape of the [grant input](contracts.md#grant-input), never computing, widening or completing a grant from any other source.

### req.workers.validation-after-clean-round — The round validation follows every clean ok round

When a request gives a round validation, the host SHALL call it once after every round whose worker ended `ok` with a clean audit, and after no other round.

### req.workers.validation-recorded — The round validation's answer is recorded

The host SHALL keep the evidence and outcome the round validation returned in the node of the
round it validated.

### req.workers.every-task-type — A worker of every Protocol task type launches

The host SHALL launch a worker of each of the eight Protocol task types.

### req.workers.unknown-task-type — A task type the Protocol does not define is refused

Before launch, the host SHALL refuse a request naming a task type that is not one of the eight
Protocol task types.

### req.workers.malformed-grant — Nothing is generated from a malformed grant

Before it generates any settings, write hook or [permission extension](../../glossary.json#concept.permission-extension), the host SHALL refuse to launch a worker whose grant has a malformed entry.

An entry is malformed when it is not an object with both of these:

- a non-empty path relative to the task worktree
- a level of `rw`, `ro` or `names`

### req.workers.malformed-grant-named — A malformed grant's refusal names the entry

For a malformed grant, the host SHALL name the first malformed entry and what is wrong with it
in the refusal.

### req.workers.unchanged-across-rounds — The run's configuration never changes between rounds

For every round of the run, the host SHALL keep the following unchanged:

- the run's settings
- its write hook
- its tool set
- its brief

### req.workers.write-allowlist — Only `rw` paths are writable by file tools

On the Claude Code backend, the write hook SHALL deny every Edit or Write whose resolved target
is not in the grant's `rw` list.

The resolved target has every symbolic link resolved, the final one included.

A write is judged by the file it would change. Only when its target is `rw` too does a symbolic
link at a `rw` path let a write through. The judgement is tighter than a link's own name. The
[pi write table](../harness/pi.md#write-table) makes the same judgement.

### req.workers.read-denials — File tools cannot read what the grant withheld when the rules were generated

On the Claude Code backend, the [deny rules](../../glossary.json#concept.deny-rules) SHALL forbid Read, Glob and Grep on every worktree path that meets all of these conditions:

- The path exists when the host generates the deny rules.
- Its level is neither `ro` nor `rw`.
- It lies below none of the run's runtime paths.

Concorde's callers admit nothing else of the worktree beside the grant. A runtime path inside the
worktree, such as `.venv` or `node_modules`, is therefore one the tracked worker configuration
lists. Claude Code applies a Read denial to Bash too, and Bash must run the toolchain below the
runtime path. The Harness therefore leaves the runtime path readable
([Claude Code mechanics](../harness/claude-code.md#deny-rules)). The worker configuration's
`runtime` list therefore decides what a worker may read beside its grant. A change of that list is
a change of the worker configuration. It is reviewed and merged like any other change of the
project.

### req.workers.bash-sandbox — Bash runs sandboxed without network

On the Claude Code backend, every Bash command of a worker SHALL run in Claude Code's sandbox
with no allowed network domain.

### req.workers.bash-strict-network — An unlisted host is denied, never approved

On the Claude Code backend, the Bash sandbox SHALL use a strict network allowlist, so that a request to a host it does not list is denied rather than approved by the permission mode.

### req.workers.bash-no-unsandboxed — No Bash command runs outside the sandbox

On the Claude Code backend, the worker settings SHALL disable unsandboxed commands, so that a request to run a command outside the sandbox still runs it sandboxed.

### req.workers.working-directory — The worker never works in the worktree

A worker SHALL use its runtime directory's `work/` directory as its working directory.

Since the runtime directory is a private directory of its own under the system's temporary
directory, `work/` is never the worktree and lies outside the run directory.

### req.workers.working-directory-not-denied — A run the deny rules would disable is refused

When a deny rule the host generated covers any directory listed below, the host SHALL refuse to
launch a worker.

The directories are in the runtime directory:

- `work/`
- `home/`
- `tmp/`

### req.workers.tool-paths-absolute — Tools take absolute paths

The host SHALL tell every worker in its brief to give its tools absolute paths.

The working directory is not the worktree, so a tool needs the absolute path.

### req.workers.result-paths-relative — Results name paths relative to the worktree

The host SHALL tell every worker in its brief to write every path in the task worktree that its
result names relative to the worktree.

Every Operation's output names project paths relative to the worktree, so a result must not copy
the tools' form.

### req.workers.clean-environment — Nothing ambient reaches the worker

The host SHALL start every worker round with only the environment variables listed in [Launch](#launch), or on the pi backend in [the pi launch](pi.md#launch).

### req.workers.project-interpreter-first — The project's interpreter comes first on the worker's `PATH`

When the request names a project interpreter, the host SHALL start every worker round, on both backends, with that interpreter's directory first on `PATH`, followed by the host's own `PATH`.

### req.workers.project-interpreter-named — The brief names the project's interpreter

When the request names a project interpreter, the host SHALL name it in the brief as the
interpreter to run the project's code and tests with.

### req.workers.runtime-paths-exact — A worker reads beside its grant only what its caller lists

The host SHALL hand the Harness the request's runtime paths exactly as given, adding none, beside a grant and context identity left as the request gave them.

### req.workers.configured-model — A worker's model comes from its worker configuration alone

The configuration reader SHALL resolve every worker's model and reasoning level from the worktree's [worker configuration](../../glossary.json#concept.worker-configuration) alone, never from the developer's own agent settings.

### req.workers.model-unsettled-refused — A worker without a settled model is refused

When any of these conditions holds, the configuration reader SHALL refuse the worker before
launch:

- its worktree has no worker configuration
- its configuration names no model for it
- its configuration names a model outside `enabled_models`

### req.workers.model-map — A worker's local model id comes from the model map alone

The configuration reader SHALL pass a worker's program the local id that the [model map](../../glossary.json#concept.model-map) gives the worker's project model name on that program, never the project model name itself.

### req.workers.model-map-refused — A worker the model map cannot place is refused

When any of these conditions holds, the configuration reader SHALL refuse the worker before
launch:

- its model map is missing
- its model map is malformed
- its model map gives its model no id for its backend

### req.workers.model-map-named — A refusal of the model map names the map

In every refusal the model map causes, the configuration reader SHALL name the map's file.

### req.workers.model-map-entry — An unmapped model's refusal names the entry to add

When the map gives a worker's model no id for its backend, the configuration reader SHALL name
the exact entry to add to the map in the refusal.

### req.workers.model-map-whole-operation — An Operation's workers are checked against the map at once

When asked to check one Operation's workers against the model map, the configuration reader SHALL refuse with one `model_unmapped` that names all of these:

- every model and backend the map lacks for those workers
- the workers that would take each

### req.workers.refusal-reason — Every refusal before a run has its fixed reason

For every refusal of the configuration reader, the reader SHALL supply the following:

- the code that [Refusals before a run](#refusals-before-a-run) list for it
- the reason that section lists for it
- a message naming the file the refusal concerns

### req.workers.proxy-passed — A worker's model calls use the host's proxy

On both backends, the host SHALL pass on to every worker round exactly the proxy variables that
[Proxy](#proxy) derives from its own environment.

### req.workers.placement — A worker runs only inside `.claude/worktrees/`

Before it generates any settings, write hook or [permission extension](../../glossary.json#concept.permission-extension), the host SHALL refuse a worker whose worktree does not lie directly in `.claude/worktrees/` of its repository's primary worktree.

### req.workers.no-git — Workers never see Git

A worker SHALL have no access to Git metadata through any tool.

### req.workers.git-paths-denied — Every Git administrative path is hidden

On both backends, wherever the repository lies, the host SHALL deny every Git administrative path
that [Placement](#placement) lists to the worker's file tools and sandbox.

### req.workers.audit-every-round — Every round is audited

The host SHALL audit the worktree against the grant after every round and before its round
validation runs.

### req.workers.violation-ends-run — A violation is never retried

A run whose audit finds a violation SHALL end `failed` without another round.

### req.workers.rounds-for-checks-only — Rounds only repair what the round validation reports

Only when all of these conditions hold, the host SHALL resume a worker:

- the worker ended `ok`
- its audit was clean
- the caller's round validation reported something to repair

### req.workers.rounds-limited — A run has at most its configured resume rounds

The host SHALL start at most the configured number of resume rounds in one run.

### req.workers.latest-session — Resume from the newest session

Each resume round SHALL continue the run's latest session.

On the Claude Code backend, the latest session's identifier is the session identifier the
previous round returned. On the pi backend, the latest session's identifier is the session
identifier the run fixed at its first round.

### req.workers.claims-apart — Worker claims stay claims

The run record SHALL keep the worker result verbatim and separate from the evidence the host
observed itself.

### req.workers.error-chain — A failed run explains itself

Every run that does not end `ok` SHALL carry Workers' error link with the causes listed in
[Errors](#errors).

Those causes are the alternatives below:

- the worker's own error
- the agent process's link (Claude Code's or pi's)
- the links the round validation names

### req.workers.host-deletes — Only the host deletes

Only when all of these conditions hold, the host SHALL delete a file:

- the worker proposed the file
- the file, its directories' symbolic links resolved, is in the `rw` list
- the last round's audit was clean

### req.workers.deletions-whatever-outcome — Proposed deletions follow every clean last round

Whatever the run's outcome, the host SHALL perform the worker's proposed deletions when all of these conditions hold:

- The last round's audit was clean.
- The last round's worker returned a valid result.
- The round validation did not answer a violation.
- The run was not interrupted.

### req.workers.deletion-once — A repeated deletion is performed once

The host SHALL take a path the worker's `proposed_deletions` names more than once, relatively or
absolutely, as one proposed deletion.

### req.workers.deletion-absent — An absent target is recorded, not refused

When a proposed deletion in the `rw` list has a path that does not exist, the host SHALL record
that deletion as already absent.

### req.workers.deletion-failure — A failed deletion fails the run without stopping the others

When a proposed deletion fails, the host SHALL still attempt every other proposed deletion.

When a proposed deletion fails, the host SHALL end the run `failed` with `deletion_failed`, naming
what it deleted and what it did not.

### req.workers.no-precreation — The host creates no file for the worker

The host SHALL NOT create any file or directory in the worktree before or while the worker runs.

### req.workers.process-group — No worker process outlives its round

When a round ends, the host SHALL kill the worker's whole process group.

### req.workers.progress — A running run shows its progress

On both backends, the host SHALL keep a run's progress file current from preparation until the
run is finished.

### req.workers.recorded-at-start — A run is recorded before its launch

Before it launches the worker, the host SHALL write the run record of every run it was asked to
start, with status `running`.

### req.workers.always-recorded — Every run leaves a final record

Once the run's node exists, the host SHALL write the final run record of every run it was asked to start when the run ends, a run refused before launch included.

When a run's node could not be written, the host SHALL still remove its runtime directory.

### req.workers.transcript-kept — The transcript is kept before the runtime directory goes

Before it removes the run's runtime directory, the host SHALL move the latest session's transcript into the run directory, also when the run was interrupted while its last round ran.

### req.workers.cleanup-reported — A cleanup that failed fails the run

When the host cannot keep the transcript or remove the runtime directory, the run SHALL end `failed` with a `cleanup_failed` error that holds all of these:

- what remains
- the operating system's error
- as its cause, the link the run would otherwise have ended with

### req.workers.runtime-removed — Nothing but the trace outlives a worker

When a worker run ends, however it ends, the host SHALL remove its runtime directory with its credential copies, unless the host process itself is killed without a chance to act.

### req.workers.trace-failures-reported — A failed trace write is reported, never silent

The host SHALL report every refused write of the worker run's or a round's `trace.json`, without changing the run's status for it, in these places:

- the returned run record's `trace_failures`
- when the run does not end `ok`, the evidence of its error

### req.workers.stderr-per-round — Every round keeps its standard error

The host SHALL keep each round's standard error in that round's node, never overwriting an
earlier round's.
