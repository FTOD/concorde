# pi run mechanics

The files, command line, environment and permission extension of a worker run on the pi backend,
and the requirements they serve. Everything the two backends share — inputs, the run directory,
the audit, rounds, the run record and most error codes — is in [the run mechanics](launch.md); this
document states only what differs. The [entry](module.md#concept.workers.backend) explains why both
backends are compiled from the same grant.

## Run directory

The pi backend uses the run directory of [the run mechanics](launch.md#run-directory-layout) with
these differences:

| Path | Content | Worker access |
| --- | --- | --- |
| `control/permission.ts` | The permission extension with the run's policy embedded | none |
| `config/` | `PI_CODING_AGENT_DIR`: copies of the user's pi `auth.json` and `models.json`, a generated `settings.json`, and `sessions/` with the session transcript | none |

There is no `control/settings.json` and no `control/write_hook.py`: the permission extension replaces
both. The host copies `auth.json` and `models.json` from the user's pi configuration directory
(`PI_CODING_AGENT_DIR`, or `~/.pi/agent`) before the first round and writes
`{"defaultProjectTrust": "never"}` as `settings.json`, so no user package, extension, skill or
theme reaches the worker.

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
hook](launch.md#write-hook) judges it, with the same decisions and reasons.

### Sandbox

`bash`, `grep`, `find` and `ls` run their command through `@anthropic-ai/sandbox-runtime`, the
engine Claude Code's own sandbox uses. The extension initializes it once per process with no
allowed network domain and a strict allowlist, and passes the filesystem configuration with every
command: `denyRead` the task worktree, the user's home and the run's `control/` and `config/`;
`allowRead` each `ro` and `rw` path, the runtime paths, the run's own directories and the
sandbox-runtime's own helper programs; `allowWrite` each `rw` path and the run's own directories.
These are the lists of the Claude Code backend's [sandbox](launch.md#worker-settings), computed by
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

## Launch

The first round runs, with `work/` as working directory and the brief on standard input:

```text
pi -p --mode json --no-extensions -e <run>/control/permission.ts
   --no-context-files --no-skills --no-prompt-templates --tools <tool set>
   --session-dir <run>/config/sessions --session-id <run-id>
   [--model <model>] [--thinking <level>]
```

A resume round runs the same command, with the same session identifier, and the check failures on
standard input; pi continues the session with its context. The command is `pi`, or the value of
`CONCORDE_PI`.

The environment is cleared and then set to exactly:

| Variable | Value |
| --- | --- |
| `PATH`, `LANG` | the host's values |
| `HOME` | `<run>/home` |
| `TMPDIR` | the run's private temporary directory |
| `CLAUDE_CODE_TMPDIR` | the same directory, which sandbox-runtime passes to the commands it runs as their `TMPDIR`; without it they get `/tmp/claude`, which need not exist and is then not writable |
| `PI_CODING_AGENT_DIR` | `<run>/config` |
| `PI_OFFLINE`, `PI_SKIP_VERSION_CHECK` | `1` |
| `PI_TELEMETRY` | `0` |
| every variable whose name ends with `_API_KEY` | the host's value, only when the host has one |

The host reads the JSON event stream from standard output as it arrives. The `session` record gives
the session identifier; the transcript is the session file under `config/sessions/`. The worker
result is the `details` of the last `concorde_result` tool execution that did not end in an error.
Each `tool_execution_start` updates the run's [progress file](launch.md#progress-file).

## Prerequisites

Before generating anything the host looks for the `pi` command, `rg`, `fd` (also found as
`fdfind`), and the sandbox-runtime package: the directory named by `CONCORDE_SANDBOX_RUNTIME`, or
`.concorde/tools/pi-runtime/node_modules/@anthropic-ai/sandbox-runtime` in the primary worktree.
On Linux it also needs `bwrap` and `socat`. When any is missing the run ends `failed` with
`pi_runtime_missing` before launch, naming every missing program and how to provide it.

## Errors

The pi backend uses the codes of [the run mechanics](launch.md#errors) except `claude_failed` and
`run_directory_denied`, and adds:

| Code | Detail | Reason | Causes |
| --- | --- | --- | --- |
| `pi_runtime_missing` | every missing program or package and how to provide it | `environment` | none |
| `pi_failed` | the round and the error pi reported, or that it ended without a worker result | `environment` | the pi process's link |

`worker_limit_reached` is reported when a `concorde-limit` entry appears, with the limit and value
it names. The **pi process's link** has the level `component`, the actor `pi process (pi -p)`, and
states the exit status, the last assistant message's stop reason and error message, the number of
turns and the tail of standard error.

## Requirements

### req.workers.pi-same-grant — Both backends enforce the same grant

On the pi backend the host SHALL derive the permission extension's policy and sandbox lists from the frozen grant with the same code that derives the Claude Code backend's deny rules, write hook and sandbox.

### req.workers.pi-file-tools — pi file tools are checked before they act

The permission extension SHALL decide every `read`, `write` and `edit` call with the read and write tables of this document before pi's own tool runs, and deny with the table's reason.

### req.workers.pi-sandbox — pi commands run sandboxed without network

Every command the pi `bash`, `grep`, `find` or `ls` tool runs SHALL run inside the sandbox-runtime sandbox with the run's filesystem lists, no allowed network domain and a strict allowlist.

### req.workers.pi-only-extension — Nothing else configures a pi worker

The host SHALL start every pi round with extension discovery, context files, skills and prompt templates disabled, the permission extension as the only extension, and its own `PI_CODING_AGENT_DIR`.

### req.workers.pi-limits — pi runs stop at their limits

The permission extension SHALL abort a pi run whose completed turns exceed `max_turns` or whose reported cost exceeds `max_budget_usd`, and record which limit was reached.
