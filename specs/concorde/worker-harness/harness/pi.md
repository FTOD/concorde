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
- The limits.
- The [worker result](../../glossary.json#concept.worker-result) schema.

The extension registers exactly these tools, replacing pi's built-ins of the same name:

| Tool | Behaviour |
| --- | --- |
| `read` | Checks the path with the read table below, then runs pi's own `read`, whose file operations check again the exact path it opens |
| `write`, `edit` | Check the path with the write table below, then run pi's own tool |
| `grep` | Runs `rg` inside the sandbox; files the sandbox hides do not exist for it |
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
holding one, is allowed too.

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
The extension passes the filesystem configuration with every command.

`denyRead` lists these paths:

- The task worktree.
- The user's home.
- The primary worktree.
- Every Git administrative path.
- The runtime directory's `control/` and `config/`.
- Each path the grant lists apart at `names` below a `ro` or `rw` directory entry.

`denyRead` wins inside the wider `allowRead`. Therefore, Bash cannot read those paths either.

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

pi has no turn or budget limit of its own. The extension counts completed turns. It also adds up
the cost each assistant message reports. When either exceeds `max_turns` or `max_budget_usd`, the
extension appends a session entry of the custom type `concorde-limit`. The entry names the limit
and the value reached. The extension then aborts the run.

## Tool sets

| [Task type](../../glossary.json#concept.task-type) | `--tools` |
| --- | --- |
| `understand`, `review-spec`, `review-code`, `test`, `review-architecture` | `read,grep,find,ls,concorde_result` |
| `specify`, `code-to-spec` | `read,grep,find,ls,edit,write,concorde_result` |
| `implement` | `read,grep,find,ls,edit,write,bash,concorde_result` |

A task type that writes no set gets the first row's set, as on Claude Code.
Whatever its task type, a grant with no writable path also gets the first row's set.
