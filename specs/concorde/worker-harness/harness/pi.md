# pi harness mechanics

The exact extension the Harness generates to apply a harness to a pi worker, the only agent that
runs on pi: the worker's [permission extension](../../glossary.json#concept.permission-extension) with
its read and write tables, sandbox, limits and tool sets. The [entry](module.md)
explains why a harness is applied this way; the [Claude Code mechanics](claude-code.md) state what
the Claude Code backend generates, and [the pi run mechanics](../workers/pi.md) of Workers
how a pi worker is launched with it.

## Permission extension

The [runtime directory](../../glossary.json#concept.runtime-directory)'s `control/permission.ts` is the host's source of the extension with one JSON
policy embedded. The
policy holds, as absolute paths, the task worktree, the grant's `rw`, `ro` and `names` lists, the
host-only directories (`control/`, `config/`), the worker's own directories (`work/`, `home/`,
`tmp/`) of the runtime directory, the runtime paths, the Git administrative paths and the primary
worktree Workers hands over, the user's real home directory, the sandbox's filesystem
configuration, the programs `rg` and `fd`, the limits and the
[worker result](../../glossary.json#concept.worker-result) schema. The extension registers exactly
these tools, replacing pi's built-ins of the same name:

| Tool | Behaviour |
| --- | --- |
| `read` | Checks the path with the read table below, then runs pi's own `read` |
| `write`, `edit` | Check the path with the write table below, then run pi's own tool |
| `grep` | Runs `rg` inside the sandbox; files the sandbox hides do not exist for it |
| `find` | Runs `fd` inside the sandbox |
| `ls` | Lists a directory inside the sandbox |
| `bash` | Runs the command inside the sandbox |
| `concorde_result` | Takes the worker result as its argument and ends the run |

A path argument is resolved the way pi resolves it: Unicode spaces become plain spaces, one leading
`@` is removed, a leading `~` becomes the worker's `HOME`, a `file://` URL becomes its path, and the
result is resolved against the working directory. Every failure inside a check denies the call with
the reason `Concorde grant: the extension could not decide: <message>`; pi itself also blocks a
tool whose handler throws.

pi validates the argument of `concorde_result` against the embedded schema before the tool runs:
an invalid one comes back to the worker as an error result and the session goes on, so the worker
can call it again; a valid one ends the run, provided no other tool called in the same assistant
message declines to end it. What the result means, and every check beyond its shape, is Workers'
([the pi run mechanics](../workers/pi.md)).

### Read table

A read is allowed only when both the resolved path and, if it exists, its symbolic-link-free real
path are allowed. The rows overlap, so they are tried from the top and the first that matches a
path decides it:

| Path | Decision | Reason given to the worker |
| --- | --- | --- |
| a Git administrative path or below one, or a `.git` entry of the task worktree at any depth or below one | deny | Git metadata is not available to workers |
| a `rw` or `ro` path of the task worktree | allow | — |
| a `names` path | deny | only the path's name is visible to this task |
| another path in the task worktree | deny | the path is not in this task's grant |
| `control/` or `config/` of the runtime directory | deny | the path belongs to the host |
| the runtime directory's `work/`, `home/` or `tmp/`, or a runtime path | allow | — |
| another path inside the user's home or the primary worktree | deny | the path is outside this task's boundary |
| any other path | allow | — |

The last row keeps system directories readable, as on the Claude Code backend.

### Write table

A write or edit is judged on the resolved path with its directories' symbolic links resolved and a
final symbolic link judged by its own name, exactly as
[the write hook](claude-code.md#write-hook) judges it, with
the same rows, decisions and reasons, including the `.git` row, and also denies a Git
administrative path with the `.git` row's reason.

### Sandbox

`bash`, `grep`, `find` and `ls` run their command through `@anthropic-ai/sandbox-runtime`, the
engine Claude Code's own sandbox uses. The extension initializes it once per process with no allowed
network domain and a strict allowlist, and passes the filesystem configuration with every command:
`denyRead` the task worktree, the user's home, the primary worktree, every Git administrative path
and the runtime directory's `control/` and `config/`;
`allowRead` each `ro` and `rw` path, the runtime paths, the worker's own directories and the sandbox-runtime's own
helper programs; `allowWrite` each `rw` path and the worker's own directories. These are the lists of
the Claude Code backend's [sandbox](claude-code.md#worker-settings), computed by the same code. The
extension resets the sandbox when the session ends, so the process exits.

### Limits

pi has no turn or budget limit of its own. The extension counts completed turns and adds up the
cost each assistant message reports; when either exceeds `max_turns` or `max_budget_usd`, it
appends a session entry of the custom type `concorde-limit` naming the limit and the value reached,
and aborts the run.

## Tool sets

| [Task type](../../glossary.json#concept.task-type) | `--tools` |
| --- | --- |
| `understand`, `review-spec`, `review-code`, `test`, `review-architecture` | `read,grep,find,ls,concorde_result` |
| `specify`, `code-to-spec` | `read,grep,find,ls,edit,write,concorde_result` |
| `implement` | `read,grep,find,ls,edit,write,bash,concorde_result` |

A task type that writes no set, and a grant with no writable path whatever its task type, get the
first row's set, as on Claude Code.
