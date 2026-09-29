# Main session contracts

The exact session, tools and events of the
[project MCP server](../../glossary.json#concept.project-mcp-server), described in the
[Main session](module.md#the-project-mcp-server). Every tool is a presentation of a command
that already exists; where a row says "as" a command, the result and every refusal are that
command's when it waits for no lock, as [Tasks](../tasks/contracts.md#commands) and
[Tracing](../../tracing/contracts.md) define them. `run_result`, `workflow_report` and `locks`
present records no command prints in that shape: their rows define their results, and their
refusals are the codes below. `task_merge` and `register_wait` answer at once with the start and the
registration defined [below](#starting-a-merge): the merge's own result and refusals, and the
wait's answer, are the commands' and arrive later.

## Session

The server is started as `concorde project-mcp [--name <name>]` (default name `concorde`) and speaks
MCP over standard input and output, newline-delimited JSON-RPC 2.0, answering `initialize`, `ping`,
`tools/list` and `tools/call`. It answers `initialize` with the client's protocol version when it
is one of `2025-06-18`, `2025-03-26` and `2024-11-05`, and with `2025-06-18` otherwise, and declares
the capabilities `{"tools": {"listChanged": false}, "experimental": {"claude/channel": {}}}` and
instructions naming its tools and events.

At start it finds the **project**: the primary worktree of the Git repository that
`CLAUDE_PROJECT_DIR` lies in, or its working directory when that variable is unset, found through
Git's common directory as every `concorde task` command finds it. Every call reads the task
records, traces and locks of that primary worktree afresh. Outside a Git repository every call is
refused with `no_project`.

It takes the **session** it serves from `CLAUDE_CODE_SESSION_ID`, the identity Claude Code gives
the processes of a session, and writes it into the holder line of every lock it takes.

It decides once whether the session **listens to it as a channel**: `CONCORDE_CHANNEL` `1` or `0`
when set; otherwise whether one of its ancestor processes, up to eight levels up, has its standard
input on a terminal and a command line with an entry `server:<name>` among the words after
`--dangerously-load-development-channels` or `--channels` and before the next option. The terminal
is required because only an interactive session is woken by channel events: a `claude --bg` session
started with the flag was never woken in a probe on 2026-09-29 (Claude Code 2.1.284), and `claude -p`
registers no channel. Claude Code tells a server neither whether it loaded it as
a channel nor whether a notification was delivered, so this is the server's only knowledge of it;
an organization policy that disables channels leaves it believing it has one.

Every tool returns one text content item holding one JSON value. A refusal sets `isError: true`
and its value is `{"error": <link>}`, a link of the
[error contract](../../tracing/contracts.md#contract.tracing.error): the link of the component that
refused, unchanged, which is `Tasks (concorde task <command>)` for a refusal of Tasks, or the
server's own `component` link of actor `Concorde project MCP server (<tool>)`:

| Code | Reason | When |
| --- | --- | --- |
| `no_project` | `environment` | the server found no Git repository at start |
| `invalid_input` | `input` | the tool is unknown, or its arguments do not satisfy its input schema or name a combination it does not take; the detail names the argument |
| `workspace_busy`, `merge_busy` | `environment` | `task_merge` found the lock held; the detail names the lock file and the holder's command, process, start time, session and task, and the evidence of kind `lock` carries the holder line as JSON |
| `start_failed` | `environment` | the operating system refused to start the merge process; both locks were released |
| `unknown_run` | `input` | `run_result` names a run no reader finds |
| `no_report` | `input` | `workflow_report` finds no saved [workflow result](../../glossary.json#concept.workflow-result), or not the one named |
| any Tasks or Tracing code | as there | the command the tool presents refused, such as `unknown_task`, `merge_busy` from `task_open` or `workspace_busy` from `task_close` |
| any other code | `environment` | an unexpected error of the server, as a link built from the exception |

## Tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `task_list` | optional `state`, one of the task states | as `concorde task list [--state]` |
| `task_show` | `task` | as `concorde task show` |
| `trace_show` | `node`: a task, history key, run or worker run identity or a node's folder; optional `depth` ≥ 0 | as `concorde trace show <node> --depth <depth>` from the primary worktree |
| `run_result` | `run`: a run identity | `{"run", "running": false, "result": <run result>}` when no runner holds the run's [run lock](../../glossary.json#concept.run-lock) and its result is saved; otherwise `{"run", "running", "result": null, "progress": <run progress file or null>}`, where `running` is `true` while its runner holds the run lock and `false` for a run whose runner ended without writing a result |
| `workflow_report` | `task`; optional `number` ≥ 1 | `{"task", "number", "path", "report": <[workflow result](../../glossary.json#concept.workflow-result)>}`, the latest saved one when no number is given |
| `locks` | none | `{"merge": <holder line or null>, "workspaces": {"<task>": <holder line or null>}}` for the merge lock and the workspace lock of every task that has not ended |
| `task_open` | `task`, `goal`, `modules` (nonempty), optional `base` | as `concorde task open`, taking the merge lock without waiting |
| `task_escalate` | `task`, `code`, `detail`, `reason`, `explanation`; optional `by` (`main-agent`, the default, or `task-session`), `runs`, `error_files`, `escalations`, `attempts`, `options`, `recommendation` | as `concorde task escalate` with the matching options |
| `task_close` | `task`, `outcome` (`completed` or `failed`); `note` for completed; `reason` and either `runs`/`error_files` or `no_error` true for failed; optional `force` | as `concorde task close --completed` or `--failed`, taking the workspace and merge locks without waiting |
| `task_merge` | `task`; optional `checks`, or `resume` or `abort` true | the start below |
| `register_wait` | exactly one of `until` (with `task`), `run`, and `lock` (`merge`, or `workspace` with `task`) | the registration below |

A holder line is the object a lock file holds while it is held,
[Tracing's](../../tracing/contracts.md#locks) `{"holder", "pid", "since"}` with `session` and
`task` when they are known.

### Starting a merge

`task_merge` takes the task's [workspace lock](../../glossary.json#concept.workspace-lock) and then
the [merge lock](../../glossary.json#concept.merge-lock) with an exclusive `flock` that does not
wait, and writes into each a holder line naming `` `concorde task merge` of task <task>, started by
the project MCP server ``, its session and the task. A lock that is held refuses the call at once
with `workspace_busy` or `merge_busy`, after releasing a lock it had already taken. With both, it
starts `concorde task merge <task> --wait 0` with each `--check`, or with `--resume` or `--abort`,
as a process of its own session in the primary worktree, whose standard output and error go to
files of a private temporary directory of the server. The process inherits both locked descriptors
and finds them named in its environment variable `CONCORDE_INHERITED_LOCKS`, as
[Tracing](../../tracing/contracts.md#handing-a-lock-on) states; the server then closes its own
copies, so from then on the locks are released exactly when that process ends.

The result is returned at once:

```json
{
  "started": {"command": "concorde task merge <task> --wait 0 …", "pid": 4242,
              "output": "<file of its JSON output>", "messages": "<file of its standard error>"},
  "locks": {"workspace": "<lock file>", "merge": "<lock file>"},
  "wake": {"channel": true}
}
```

With a channel, the server sends a `merge_ended` event when the process ends. Without one, `wake`
is `{"channel": false, "command": "concorde task wait <task> --lock workspace", "explanation": …}`:
the command to run in background Bash, which returns when the merge released the task's workspace
lock, after which the output file holds the merge's JSON.

### Registering a wait

`register_wait` first checks whether what it waits for already happened: the task's derived state
is one of `until`, the run's runner holds no [run lock](../../glossary.json#concept.run-lock), or
nobody holds the lock. Then it answers `{"registered": false, "already": <answer>}`, the value the
matching `concorde task wait` would print, and registers nothing. `until` admits `delivered`,
`merging`, `closed` and `failed` only, the states a task reaches while its workspace lock is held.

Otherwise, without a channel, it answers
`{"registered": false, "channel": false, "command": "<concorde task wait …>", "explanation": …}`,
where the command is `concorde task wait <task> --until <state>[,<state>…]`,
`concorde task wait --run <run-id>` or `concorde task wait [<task>] --lock merge|workspace`. With a
channel it answers `{"registered": true, "wait": "<n>", "channel": true, "waits_for": "<what>"}` and
watches, as `concorde task wait` does, until it happens or ends another way; it never takes or
hands over a lock for the session.

## Channel events

Each event is a `notifications/claude/channel` notification with `content`, the text Claude
receives, and `meta`, whose keys become attributes of the `<channel source="concorde">` tag:

```concorde-contract
{
  "id": "contract.main-session.channel-event",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["content", "meta"],
    "properties": {
      "content": {"type": "string", "minLength": 1},
      "meta": {
        "type": "object",
        "required": ["event"],
        "additionalProperties": {"type": "string"},
        "properties": {
          "event": {"enum": ["wait_done", "wait_failed", "merge_ended"]},
          "kind": {"enum": ["task", "run", "lock"]},
          "wait": {"type": "string"},
          "task": {"type": "string"},
          "run": {"type": "string"},
          "lock": {"enum": ["merge", "workspace"]},
          "code": {"type": "string"},
          "exit_code": {"type": "string"},
          "status": {"enum": ["ok", "refused", "failed"]}
        }
      }
    }
  },
  "semantics": "One event of the project MCP server to the Claude Code session that runs it. wait_done: a registered wait is over; kind and wait name it, and content carries the answer concorde task wait would print. wait_failed: the wait ended without it, such as a task that ended in another state (code wait_unreachable); content carries the rendered error chain. merge_ended: the merge task_merge started ended; exit_code and status say how, and content carries its JSON output, cut after 6000 characters with the path of the whole.",
  "example": {
    "content": "Concorde: task retry becoming delivered happened (wait 1): {\"task\": \"retry\", \"state\": \"delivered\", \"waited_seconds\": 412.3}",
    "meta": {"event": "wait_done", "kind": "task", "task": "retry", "wait": "1"}
  }
}
```

<a id="channel-event-participation"></a>

**Participation.** The server provides this contract, version 1, to the external Claude Code
session it runs in. Claude Code delivers it only to a session started with the server as a
channel, and drops it silently otherwise.
