# pi harness mechanics

The exact extensions the Harness generates to apply a harness to a pi agent: the worker's
permission extension with its read and write tables, sandbox, limits and tool sets, and the
task session's boundary extension. The [entry](module.md) explains why a harness is applied this
way; the [Claude Code mechanics](claude-code.md) state what the Claude Code backend generates, and
[the pi run mechanics](../agents/workers/pi.md) of Workers how a pi worker is launched with it.

## Permission extension

`control/permission.ts` is the host's source of the extension with one JSON policy embedded. The
policy holds, as absolute paths, the task worktree, the grant's `rw`, `ro` and `names` lists, the
host-only directories (`control/`, `config/`), the run's own directories (`work/`, `home/`,
`TMPDIR`), the runtime paths, the user's real home directory, the sandbox's filesystem
configuration, the programs `rg` and `fd`, the limits and the worker result schema. The extension
registers exactly these tools, replacing pi's built-ins of the same name:

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

### Read table

A read is allowed only when both the resolved path and, if it exists, its symbolic-link-free real
path are allowed:

| Path | Decision | Reason given to the worker |
| --- | --- | --- |
| the task worktree's `.git` or below it | deny | Git metadata is not available to workers |
| a `rw` or `ro` path of the task worktree | allow | — |
| a `names` path | deny | only the path's name is visible to this task |
| another path in the task worktree | deny | the path is not in this task's grant |
| `control/` or `config/` of the run | deny | the path belongs to the host |
| the run's `work/`, `home/` or `TMPDIR`, or a runtime path | allow | — |
| another path inside the user's home | deny | the path is outside this task's boundary |
| any other path | allow | — |

The last row keeps system directories readable, as on the Claude Code backend.

### Write table

A write or edit is judged on the resolved path with its directories' symbolic links resolved and a
final symbolic link judged by its own name, exactly as [the write
hook](claude-code.md#write-hook) judges it, with the same decisions and reasons.

### Sandbox

`bash`, `grep`, `find` and `ls` run their command through `@anthropic-ai/sandbox-runtime`, the
engine Claude Code's own sandbox uses. The extension initializes it once per process with no
allowed network domain and a strict allowlist, and passes the filesystem configuration with every
command: `denyRead` the task worktree, the user's home and the run's `control/` and `config/`;
`allowRead` each `ro` and `rw` path, the runtime paths, the run's own directories and the
sandbox-runtime's own helper programs; `allowWrite` each `rw` path and the run's own directories.
These are the lists of the Claude Code backend's [sandbox](claude-code.md#worker-settings), computed by
the same code. The extension resets the sandbox when the session ends, so the process exits.

### Limits

pi has no turn or budget limit of its own. The extension counts completed turns and adds up the
cost each assistant message reports; when either exceeds `max_turns` or `max_budget_usd`, it
appends a session entry of the custom type `concorde-limit` naming the limit and the value reached,
and aborts the run.

## Tool sets

| Task type | `--tools` |
| --- | --- |
| `understand`, `review-spec`, `review-code`, `test` | `read,grep,find,ls,concorde_result` |
| `specify`, `code-to-spec` | `read,grep,find,ls,edit,write,concorde_result` |
| `implement` | `read,grep,find,ls,edit,write,bash,concorde_result` |

A grant with no writable path gets the first row's set whatever its task type, as on Claude Code.

## Session boundary extension

A pi task session's boundary is `.concorde/tasks/<task>.session/boundary.ts`, the source
`pi_session.ts` with the session's policy embedded, beside `pi_session_policy.ts` and the
`pi_policy.ts` it imports. The policy holds, as absolute paths, the task worktree, the decision
log, the writable paths of the shell, the private temporary directory and the session report
schema. Unlike the worker's extension it intercepts pi's tools instead of replacing them, so the
developer's own extensions keep theirs:

| Tool | Behaviour |
| --- | --- |
| `write`, `edit` | Blocked, with a reason naming the task worktree, unless the path, resolved as pi resolves it, is inside the task worktree or is the decision log |
| `bash` | Rewritten to run inside sandbox-runtime, writing only the policy's writable paths and the temporary directory, with every network host allowed |
| `concorde_report` | Takes the [session report](../agents/task-session/contracts.md#contract.task-session.report) and ends the round |

Every other tool is left as the developer's configuration gives it.
