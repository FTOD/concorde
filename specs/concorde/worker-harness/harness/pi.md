# pi harness mechanics

This document describes the exact extension the Harness generates to apply a harness to a pi worker.
The pi worker is the only agent that runs on pi. The extension is the worker's
[permission extension](../../glossary.json#concept.permission-extension). It includes these components:

- Read and write tables.
- A sandbox.
- Limits.
- Tool sets.

The [entry](module.md) explains why a harness is applied this way. The
[Claude Code mechanics](claude-code.md) state what the Claude Code backend generates. Workers'
[pi run mechanics](../workers/pi.md) explain how a pi worker is launched with the extension.

## Permission extension

The [runtime directory](../../glossary.json#concept.runtime-directory)'s `control/permission.ts` is the
host's source of the extension. It embeds one JSON policy. The policy holds the following as absolute
paths:

- The task worktree.
- The grant's `rw` list.
- The grant's `ro` list.
- The grant's `names` list.
- The runtime directory's host-only directories (`control/`, `config/`).
- The worker's own directories in the runtime directory.
- The runtime paths Workers hands over.
- The Git administrative paths Workers hands over.
- The primary worktree Workers hands over.
- The user's real home directory.

The worker's own directories in the runtime directory are these:

- `work/`
- `home/`
- `tmp/`

The policy also holds these items:

- The sandbox's filesystem configuration.
- The programs `rg` and `fd`.
- The `groups` folder, where the extension registers each command's process group.
- The run's limits, `max_turns` and `max_budget_usd`.
- The [worker result](../../glossary.json#concept.worker-result) schema.

The extension registers exactly these tools, replacing pi's built-ins of the same name:

| Tool | Behaviour |
| --- | --- |
| `read` | Checks the path with the read table below, then runs pi's own `read`, whose file operations check again the exact path it opens |
| `write`, `edit` | Check the path with the write table below, then run pi's own tool |
| `grep` | Runs `rg` inside the sandbox; files the sandbox hides do not exist for it. It reads `rg`'s output line by line. It stops `rg` as soon as it has read the limit-th match and that match's own context lines, as pi's own `grep` stops at that match. A line too long to read whole is shown as such, and a line it cannot read is reported, so an incomplete reading never answers that nothing matched |
| `find` | Runs `fd` inside the sandbox |
| `ls` | Lists a directory inside the sandbox |
| `bash` | Runs the command inside the sandbox |
| `concorde_result` | Takes the worker result as its argument and ends the run |

A path argument is resolved the way pi resolves it:

- Unicode spaces become plain spaces.
- One leading `@` is removed.
- A leading `~` becomes the worker's `HOME`.
- A `file://` URL becomes its path.
- The result is resolved against the working directory.
- A trailing separator is removed, so a directory named as `dir/` is judged as `dir`.

When a name does not exist, pi's `read` may then open another spelling of that name, such as:

- Its NFD form.
- A narrow no-break space before `AM` or `PM`.
- A curly apostrophe.

The extension therefore gives pi's `read` file operations of its own. Before they open the path pi
chose, these operations check it with the read table. Every failure inside a check denies the call
with the reason `Concorde grant: the extension could not decide: <message>`. When a tool's handler
throws, pi itself also blocks the tool.

Before the tool runs, pi validates the argument of `concorde_result` against the embedded schema.
An invalid argument comes back to the worker as an error result. The session goes on. The worker
can therefore call the tool again. Provided no other tool called in the same assistant message
declines to end the run, a valid argument ends the run. Workers
([the pi run mechanics](../workers/pi.md)) defines what the result means. Workers also defines
every check beyond the result's shape.

### Read table

Only when both the resolved path and, if it exists, its symbolic-link-free real path are allowed
is a read allowed.

The rows overlap. They are tried from the top. The first row that matches a path decides it:

| Path | Decision | Reason given to the worker |
| --- | --- | --- |
| a Git administrative path or below one, or a `.git` entry of the task worktree at any depth or below one | deny | Git metadata is not available to workers |
| a runtime path or below one, inside the task worktree or outside it | allow | — |
| a `rw` or `ro` path of the task worktree | allow | — |
| a `names` path | deny | only the path's name is visible to this task |
| another path in the task worktree | deny | the path is not in this task's grant |
| `control/` or `config/` of the runtime directory | deny | the path belongs to the host |
| the runtime directory's `work/`, `home/` or `tmp/` | allow | — |
| another path inside the user's home or the primary worktree | deny | the path is outside this task's boundary |
| any other path | allow | — |

A path's level is that of the grant's most specific entry for it, as in
[the write hook](claude-code.md#write-hook). If the path has an exact entry, that entry is the most
specific. Else, the longest directory entry above the path is the most specific. The last row
keeps system directories readable, as on the Claude Code backend. A runtime path inside the task
worktree, such as `.venv` or `node_modules`, is readable to `read` as to the sandbox. The sandbox
lists the runtime path in `allowRead`. A search rooted at the runtime path, or at a directory
holding one, is allowed too, inside the task worktree or outside it, such as in the primary
worktree or the user's home. A search root in a Git administrative path or in the runtime
directory's `control/` or `config/` stays denied. The sandbox still hides everything below the
root that the read table denies.

### Write table

A write or edit is judged on the resolved path with every symbolic link resolved, the final one
included. Thus, the judgment is by the file it would change, exactly as
[the write hook](claude-code.md#write-hook) judges it. The judgment uses the same features:

- Rows, including the `.git` row.
- Decisions.
- Reasons.
- Naming of a link's target.

The write table also denies a Git administrative path with the `.git` row's reason.

### Sandbox

The following tools run their command through `@anthropic-ai/sandbox-runtime`:

- `bash`
- `grep`
- `find`
- `ls`

The extension's command engine is the engine Claude Code's own sandbox uses. The extension
initializes the engine once per process with no allowed network domain and a strict allowlist.
The extension passes the filesystem configuration with every command. Each command runs in a
process group of its own, so that the extension can stop the command with every process it started.
Before the command goes on, the extension registers the group as an empty file named by the group's
identifier in the policy's `groups` folder, `control/groups/` of the runtime directory. A command
ends when its shell exits and its output closes. A process the command started in the background
with its output redirected may still run then. So when the command ends, the extension kills every
process still in the group. Only then does it remove the file. A group the extension cannot kill
keeps its file. When the file cannot be written, the extension stops the command and refuses it. The reason is `Concorde grant: the command was not run: its process
group could not be registered for the host to stop: <error>`. Workers kills each registered group
when the round ends ([the pi run mechanics](../workers/pi.md#run-directory)).

`denyRead` lists these paths:

- The task worktree.
- The user's home.
- The primary worktree.
- Every Git administrative path.
- The runtime directory's `control/` and `config/`.
- Each path the grant lists apart at `names` below a `ro` or `rw` directory entry.

The last entry wins inside the wider `allowRead`, so Bash cannot read such a `names` path either.

`allowRead` lists these paths and programs:

- Each `ro` and `rw` path.
- The runtime paths.
- The worker's own directories.
- The sandbox-runtime's own helper programs.

`allowWrite` lists each `rw` path and the worker's own directories. `denyWrite` lists each path the
grant lists apart at `ro` or `names` below a `rw` directory entry. `denyWrite` wins inside the wider
`allowWrite`. Therefore, Bash cannot write those paths either. These are the lists of the Claude Code
backend's [sandbox](claude-code.md#worker-settings). The same code computes them. When the session
ends, the extension resets the sandbox. The process therefore exits.

### Limits

pi has no turn or budget limit of its own. The run's limits bound the whole worker run, so each
round may use only what the earlier rounds left ([Limits](../workers/launch.md#limits)). The host
passes that in the variable `CONCORDE_ROUND_LIMITS` as JSON, `{"maxTurns": <n>, "maxBudgetUsd": <x
or null>}`. The extension reads the variable when pi loads it. It applies the lower of each limit
there and the run's own limit in the policy. A round therefore never gets more than the run's
limits. The variable is malformed when it is no JSON object or lacks a valid limit. A valid turn
limit is a whole number of at least zero. A valid budget is null or a number of at least zero. When
the variable is missing or malformed, the extension allows no turn and no cost. The round then
stops at its first turn or at its first priced message.

The extension counts the round's completed turns. It also adds up the cost each assistant message
reports. When either exceeds the round's turns or budget, the extension appends a session entry of
the custom type `concorde-limit`. The entry names the limit, the value reached and the round's
maximum. The extension then aborts the run.

## Tool sets

| [Task type](../../glossary.json#concept.task-type) | `--tools` |
| --- | --- |
| `understand`, `review-spec`, `review-code`, `test`, `review-architecture` | `read,grep,find,ls,concorde_result` |
| `specify`, `code-to-spec` | `read,grep,find,ls,edit,write,concorde_result` |
| `implement` | `read,grep,find,ls,edit,write,bash,concorde_result` |

A task type that writes no set gets the first row's set, as on Claude Code.
Whatever its task type, a grant with no writable path also gets the first row's set.
