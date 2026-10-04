# pi run mechanics

This document states these details of a worker run on the pi backend:

- the files
- the command line
- the environment

It also states the requirements these details serve. The Harness generates the
[permission extension](../../glossary.json#concept.permission-extension) the worker loads.
The Harness states the extension in its [pi mechanics](../harness/pi.md).
[The run mechanics](launch.md) states everything the two backends share:

- inputs
- the [run directory](../../glossary.json#concept.run-directory) and
  [runtime directory](../../glossary.json#concept.runtime-directory)
- the audit
- rounds
- the [run record](../../glossary.json#concept.run-record)
- most error codes

This document states only what differs. The
[entry](module.md#two-backends-from-one-grant) explains what the two backends share.

## Run directory

The pi backend uses the run directory and the runtime directory of
[the run mechanics](launch.md#run-directory-and-runtime-directory). The runtime directory has these
differences:

| Path | Content | Worker access |
| --- | --- | --- |
| `control/permission.ts` | The permission extension with the run's policy embedded | none |
| `config/` | `PI_CODING_AGENT_DIR`: copies of the user's pi `auth.json` and `models.json`, a generated `settings.json` of Concorde's own, and `sessions/` with the session transcript | none |

There is no `control/settings.json` and no `control/write_hook.py`. The permission extension
replaces both. Before the first round, the host copies `auth.json` and `models.json` from the
user's pi configuration directory into the runtime directory. The configuration directory is
`PI_CODING_AGENT_DIR` (with a leading `~` expanded as pi does), or `~/.pi/agent`.
When the run ends, the copies are removed with the runtime directory. Before the first round,
the host also writes a `settings.json` of its own in the runtime directory.

The generated `settings.json` holds only `"defaultProjectTrust": "never"`. The user's own pi
`settings.json` is never read. The user's pi settings stay the developer's:

- the default provider
- the default model
- the default thinking level
- the enabled models
- the per-model thinking levels
- every other setting

No user item of the following kinds reaches the worker:

- package
- extension
- skill
- theme
- model filter

The worker's model and level come only from the
[worker configuration](../../glossary.json#concept.worker-configuration).
The [model map](../../glossary.json#concept.model-map) gives the model's pi id.
The model and level are passed with `--model` and `--thinking`
(see [choosing worker models](module.md#choosing-worker-models)). The copied `auth.json` and
`models.json` say how to reach a provider, never which model to use.

## Launch

The first round runs with the runtime directory's `work/` as working directory and the brief on
standard input:

```text
pi -p --mode json --no-extensions -e <runtime>/control/permission.ts
   --no-context-files --no-skills --no-prompt-templates --tools <tool set>
   --session-dir <runtime>/config/sessions --session-id <run-id>
   [--model <model>] [--thinking <level>]
```

A [resume round](../../glossary.json#concept.resume-round) runs the same command with the same
session identifier. The resume round takes the round validation's repair text on standard input.
In a resume round, pi continues the session with its context. The command is `pi`, or the value of
`CONCORDE_PI`.

The environment is cleared. It is then set to exactly these values:

| Variable | Value |
| --- | --- |
| `PATH` | the host's value, preceded by the project interpreter's directory when the request names one ([Reading beside the grant](launch.md#reading-beside-the-grant)) |
| `LANG` | the host's value |
| `HOME` | `<runtime>/home` |
| `TMPDIR` | `<runtime>/tmp` |
| `CLAUDE_CODE_TMPDIR` | the same directory, which sandbox-runtime passes to the commands it runs as their `TMPDIR`; without it they get `/tmp/claude`, which need not exist and is then not writable |
| `PI_CODING_AGENT_DIR` | `<runtime>/config` |
| `PI_OFFLINE`, `PI_SKIP_VERSION_CHECK` | `1` |
| `PI_TELEMETRY` | `0` |
| every variable whose name ends with `_API_KEY` | the host's value, only when the host has one |
| the [proxy variables](launch.md#proxy) | as that section derives them from the host's |

The host reads the JSON event stream from standard output as it arrives. The `session` record gives
the session identifier. The transcript is the session file under `config/sessions/`.
When the run ends, the transcript moves into the run directory as `transcript.jsonl`.
Each assistant `message_end` adds its reported tokens and cost to the round's usage.
The reported tokens have these fields:

- `input`
- `output`
- `cacheRead`
- `cacheWrite`

Each `turn_end` adds a turn. The worker result is the `details` of the last `concorde_result` tool
execution that did not end in an error. Each `tool_execution_start` updates the run's
[progress file](launch.md#progress-file).

## Prerequisites

Before generating anything, the host looks for these prerequisites:

- the `pi` command
- `rg`
- `fd` (also found as `fdfind`)
- the sandbox-runtime package

The package directory is the directory named by `CONCORDE_SANDBOX_RUNTIME`, or
`.concorde/tools/pi-runtime/node_modules/@anthropic-ai/sandbox-runtime` in the primary worktree.
On Linux, the host also needs `bwrap` and `socat`. When any prerequisite is missing, the run ends
`failed` with `pi_runtime_missing` before launch. The failure names every missing program and how
to provide it. Before the caller calls the host, the caller resolves the worker's backend. That
resolution already refuses a missing `pi` command with `backend_missing`. The caller therefore
normally receives that code.
For a run requested without that resolution, the host's own check covers a missing `pi` command.

## Errors

The pi backend uses the codes of [the run mechanics](launch.md#errors) except `claude_failed` and
`run_directory_denied`, and adds:

| Code | Detail | Reason | Causes |
| --- | --- | --- | --- |
| `pi_runtime_missing` | every missing program or package and how to provide it | `environment` | none |
| `pi_failed` | the round and the error pi reported: it ended without a [worker result](../../glossary.json#concept.worker-result) and with a non-zero exit status, without a session record, or with the stop reason `error` or `aborted` | `environment` | the pi process's link |

When a pi worker ends normally without a worker result, it ends `failed` with
`worker_result_invalid`, as on Claude Code. When the JSON event stream carries an `entry_appended`
record of the custom type `concorde-limit`, `worker_limit_reached` is reported. The report names the
limit and value the record names. This record is the session entry the permission extension appends
when it stops the run at a [limit](../harness/pi.md#limits).

The **pi process's link** has the level `component`. The link has the actor `pi process (pi -p)`.
The link states these details:

- the exit status
- the last assistant message's stop reason and error message
- the number of turns
- the tail of standard error

For a run the permission extension stopped at a limit, the link has the code `pi_limit_reached`
and the reason `exhausted`. For such a run, the link names these details:

- the limit
- the value reached
- the maximum allowed

Otherwise, the link has the code `pi_error` and the reason `environment`.

## Requirements

### req.workers.pi-same-grant — Both backends enforce the same grant

On the pi backend, the host SHALL derive the permission extension's policy and sandbox lists from
the frozen grant with the same code that derives these Claude Code backend components:

- [deny rules](../../glossary.json#concept.deny-rules)
- [write hook](../../glossary.json#concept.write-hook)
- sandbox

### req.workers.pi-file-tools — pi file tools are checked before they act

The permission extension SHALL decide every `read`, `write` and `edit` call with the Harness's [read table](../harness/pi.md#read-table) and [write table](../harness/pi.md#write-table) before pi's own tool runs.

### req.workers.pi-denial-reason — A denied pi file tool call gives the table's reason

A `read`, `write` or `edit` call the permission extension denies SHALL return the reason the deciding table gives for the denial.

### req.workers.pi-sandbox — pi commands run sandboxed without network

Every command the pi `bash`, `grep`, `find` or `ls` tool runs SHALL run inside the sandbox-runtime sandbox with the run's filesystem lists, no allowed network domain and a strict allowlist.

### req.workers.pi-only-extension — The permission extension is a pi worker's only extension

The host SHALL start every pi round with extension discovery disabled and the permission extension
as its only extension.

### req.workers.pi-no-context-files — A pi worker reads no context file

The host SHALL start every pi round with context files disabled.

### req.workers.pi-no-skills — A pi worker loads no skill

The host SHALL start every pi round with skills disabled.

### req.workers.pi-no-prompt-templates — A pi worker loads no prompt template

The host SHALL start every pi round with prompt templates disabled.

### req.workers.pi-own-config-dir — A pi worker has its own configuration directory

The host SHALL start every pi round with `PI_CODING_AGENT_DIR` set to the runtime directory's
`config/`.

### req.workers.pi-settings-generated — A pi worker's settings are Concorde's own

The host SHALL give every pi worker a generated `settings.json` of its own that holds only
`defaultProjectTrust` `never`.

### req.workers.pi-settings-independent — A pi worker takes nothing from the user's pi settings

The host SHALL NOT read the user's pi `settings.json`.

### req.workers.pi-config-copies — Only the pi files that say how to reach a provider are copied

The host SHALL copy from the user's pi configuration directory only `auth.json` and `models.json`.

### req.workers.pi-limits — pi runs stop at their limits

For a pi run whose completed turns exceed `max_turns`, or, when the worker configuration sets
`max_budget_usd`, whose reported cost exceeds it, the permission extension SHALL abort the run.

### req.workers.pi-limit-recorded — A pi run records the limit it reached

When the permission extension aborts a pi run at a limit, the permission extension SHALL record
which limit was reached and the value reached.
