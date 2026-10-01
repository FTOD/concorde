# Main session contracts

The exact session, tools and events of the
[project MCP server](../../glossary.json#concept.project-mcp-server), described in the
[Main session](module.md#the-project-mcp-server). Every tool is a presentation of a command
that already exists; where a row says "as" a command, the result and every refusal are that
command's when it waits for no lock, as [Tasks](../tasks/contracts.md#commands),
[Tracing](../../tracing/contracts.md) and [Issues](../../issues/interface.md#bookkeeping-command)
define them. `run_result`, `workflow_report` and `locks`
present records no command prints in that shape: their rows define their results, and their
refusals are the codes below. `task_merge` and `register_wait` answer at once with the start and the
registration defined [below](#starting-a-merge): the merge's own result and refusals, and the
wait's answer, are the commands' and arrive later. `workflow_step` answers with what
`concorde workflow step` of the session's worktree printed, as defined
[below](#starting-a-workflow-step).

## Session

The server is started as `concorde project-mcp [--name <name>]` (default name `concorde`) and speaks
MCP over standard input and output, newline-delimited JSON-RPC 2.0, answering `initialize`, `ping`,
`tools/list` and `tools/call`. It answers `initialize` with the client's protocol version when it
is one of `2025-06-18`, `2025-03-26` and `2024-11-05`, and with `2025-06-18` otherwise, and declares
the capabilities `{"tools": {"listChanged": true}, "experimental": {"claude/channel": {}}}` and
instructions naming its tools and events.

At start it finds the **project**: the primary worktree of the Git repository that
`CLAUDE_PROJECT_DIR` lies in, or its working directory when that variable is unset, found through
Git's common directory as every `concorde task` command finds it. Every call reads the task
records, traces and locks of that primary worktree afresh. Outside a Git repository every call is
refused with `no_project`.

**Every call runs the current Concorde.** The server answers `tools/list` and every `tools/call`
with a process of its own per request, started with the primary worktree's `concorde` as it is at
that moment, its `.concorde/bin/concorde` or, in Concorde's source checkout, its
`scripts/concorde.py` with the server's Python, from the primary worktree, with the server's
environment: `concorde project-mcp --tools` prints the tools, and `concorde project-mcp --call
<tool>` answers one call. These two options are the server's own interface with the Concorde it
presents, not a command for anyone else. The call's process reads one JSON object on its standard
input, the call's `arguments` with the session's provenance (the primary worktree, the session's
worktree, the Claude Code session and whether it has a channel), and prints one JSON line on its
standard output, `{"value": <answer>}` or `{"error": <link>}`, each with `tools`, the digest of its
tools; the server returns that answer or refusal as the tool's. An ordinary call's process may take
300 seconds and a `workflow_step` call's its wait plus 120 seconds; one that exceeds it is stopped.
When an answer's `tools` differ from the tools the server last listed, it sends
`notifications/tools/list_changed`, and its next `tools/list` answers with the current tools. When
`concorde project-mcp --tools` gives no tools, the server lists its own.

It takes the **session** it serves from `CLAUDE_CODE_SESSION_ID`, the identity Claude Code gives
the processes of a session, and writes it into the holder line of every lock it takes. The
**session's worktree** is the Git worktree that `CLAUDE_PROJECT_DIR`, or else its working
directory, lies in: the folder the session started in, a task worktree for a
[task session](../../glossary.json#concept.task-session).

It answers the calls of `workflow_step`, which may wait up to 100 seconds, each on a thread of its
own, and every other call in the order it arrives, so a waiting step never holds up the session's
other calls.

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
refused, unchanged, which is `Tasks (concorde task <command>)` for a refusal of Tasks,
`Issues (concorde issues)` for a refusal of the Issues command, or the server's own `component` link of actor `Concorde project MCP server (<tool>)`:

| Code | Reason | When |
| --- | --- | --- |
| `no_project` | `environment` | the server found no Git repository at start |
| `invalid_input` | `input` | the tool is unknown, or its arguments do not satisfy its input schema or name a combination it does not take; the detail names the argument |
| `workspace_busy`, `merge_busy` | `environment` | `task_merge` found the lock held; the detail names the lock file and the holder's command, process, start time, session and task, and the evidence of kind `lock` carries the holder line as JSON |
| `call_failed` | `environment` | the process of a call exited, or was stopped after its time, without printing an answer; the detail names the command run in the primary worktree, its exit status and the end of what it printed |
| `start_failed` | `environment` | the operating system refused to start `concorde task merge`; both locks were released |
| `unbound_worktree` | `environment` | `workflow_step` in a session whose worktree has no usable [workspace binding](../../glossary.json#concept.workspace-binding), such as the primary worktree; the detail names the worktree and, for a binding that cannot be read, its code |
| `step_failed` | `environment` | `concorde workflow step` printed no JSON object, or gave no answer within its wait and 60 seconds more; the detail carries the command, its exit status and the end of its output |
| `unknown_run` | `input` | `run_result` names a run no reader finds |
| `no_report` | `input` | `workflow_report` finds no saved [workflow result](../../glossary.json#concept.workflow-result), or not the one named |
| any Tasks, Tracing or Issues code | as there | the command the tool presents refused, such as `unknown_task`, `merge_busy` from `task_open` or `workspace_busy` from `task_close` |
| any Workflows code | as there | `concorde workflow step` refused the request or the workspace with `{"error": <link>}` and no step outcome, such as `invalid_request`; that link unchanged |
| any other code | `environment` | an unexpected error of the server, as a link built from the exception |

## Tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `task_list` | optional `state`, a nonempty array of task states, and `main`, a main agent's session | as `concorde task list [--state <state>,…] [--main]` |
| `task_show` | `task` | as `concorde task show` |
| `trace_show` | `node`: a task, history key, run or worker run identity or a node's folder; optional `depth` ≥ 0 | as `concorde trace show <node> --depth <depth>` from the primary worktree |
| `run_result` | `run`: a run identity | `{"run", "running": false, "result": <run result>}` when no runner holds the run's [run lock](../../glossary.json#concept.run-lock) and its result is saved; otherwise `{"run", "running", "result": null, "progress": <run progress file or null>}`, where `running` is `true` while its runner holds the run lock and `false` for a run whose runner ended without writing a result |
| `workflow_report` | `task`; optional `number` ≥ 1 | `{"task", "number", "path", "report": <[workflow result](../../glossary.json#concept.workflow-result)>}`, the latest saved one when no number is given |
| `locks` | none | `{"merge": <holder line or null>, "workspaces": {"<task>": <holder line or null>}}` for the merge lock and the workspace lock of every task that has not ended |
| `task_open` | `task`, `goal`, `modules` (nonempty), optional `base` | as `concorde task open`, taking the merge lock without waiting |
| `task_escalate` | `task`, `code`, `detail`, `reason`, `explanation`; optional `by` (`main-agent`, the default, or `task-session`), `runs`, `error_files`, `escalations`, `attempts`, `options`, `recommendation` | as `concorde task escalate` with the matching options |
| `task_rebind` | `task`, `main` | as `concorde task rebind <task> --main <main>` |
| `task_report` | `task`, `text`; optional `escalations`, numbers ≥ 1 | as `concorde task report` with `--escalation` for each |
| `task_answer` | `task`, `reports` (nonempty numbers ≥ 1), `text` | as `concorde task answer` with `--report` for each |
| `task_close` | `task`, `outcome` (`completed` or `failed`); `note` for completed; `reason` and either `runs`/`error_files` or `no_error` true for failed; optional `force` | as `concorde task close --completed` or `--failed`, taking the workspace and merge locks without waiting |
| `task_resolve` | `task`, `issues` (nonempty) | as `concorde task resolve <task> <issue>…` |
| `issue_list` | optional `status` (`open` or `closed`), `module`, `tier` (nonempty list of tiers), `severity` (nonempty list of severities), `sort` (`severity`) | as `concorde issues list` with `--status`, `--module`, `--tier` and `--severity` for each, and `--sort` |
| `issue_show` | `issue` | as `concorde issues show <issue>` |
| `issue_check` | none | as `concorde issues check` in the primary worktree, without its exit status |
| `issue_report` | exactly one of `report`, a [report](../../issues/interface.md#contract.issues.report) as an object, and `file`, a report file's path relative to the session's worktree; optional `check` | as `concorde issues report --file <file> [--check]` run in the session's worktree, never waiting for the merge lock, with the session's provenance: `task-session` and its task in a task worktree bound as a workspace, `main-agent` without a task otherwise; a call naming both or neither of `report` and `file` is refused with `invalid_input` |
| `issue_close` | `issue`, `reason` (`resolved`, `duplicate` or `not-actionable`), `note`, `evidence` (nonempty); optional `duplicate_of` | as `concorde issues close`, never waiting for the merge lock, with the session as actor as for `issue_report` |
| `issue_reopen` | `issue`, `note`, `evidence` (nonempty) | as `concorde issues reopen`, never waiting for the merge lock, with the session as actor |
| `task_merge` | `task`; optional `checks`, or `resume` or `abort` true | the start below |
| `register_wait` | exactly one of `until` (with `task`), `rebound` (a [main agent](../../glossary.json#concept.main-agent)'s session, with `task`), `run`, and `lock` (`merge`, or `workspace` with `task`) | the registration below |
| `workflow_step` | `request`, a [step request](../../execution/workflows/contracts.md#contract.workflows.step-request) as an object; optional `wait`, whole seconds from 0 to 100 (default 100) | the [step outcome](../../execution/workflows/contracts.md#contract.workflows.step) below |

A holder line is the object a lock file holds while it is held,
[Tracing's](../../tracing/contracts.md#locks) `{"holder", "pid", "since"}` with `session` and
`task` when they are known.

### Starting a merge

The server starts the call's process for `task_merge` in a process session of its own, with its
standard error going to a file of a private temporary directory of the server. That process takes
the task's [workspace lock](../../glossary.json#concept.workspace-lock) and then the
[merge lock](../../glossary.json#concept.merge-lock) with an exclusive `flock` that does not wait,
and writes into each a holder line naming `` `concorde task merge` of task <task>, started by the
project MCP server ``, its own process, the session and the task. A lock that is held refuses the
call at once with `workspace_busy` or `merge_busy`, after releasing a lock it had already taken.
With both, it prints the start below and replaces itself with
`concorde task merge <task> --wait 0` of the primary worktree, with each `--check`, or with
`--resume` or `--abort`, whose standard output goes to another file of that directory. The merge
keeps both locked descriptors, named in its environment variable `CONCORDE_INHERITED_LOCKS` as
[Tracing](../../tracing/contracts.md#handing-a-lock-on) states, and the server never holds either,
so the locks are released exactly when the merge ends. When the operating system refuses to run
`concorde task merge`, the call's process prints a `start_failed` refusal after the start and
exits, which releases both locks, and the call is refused with it.

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

### Starting a workflow step

`workflow_step` works on the session's worktree. When that worktree has no workspace binding, or
one that cannot be read, it is refused with `unbound_worktree` and runs nothing. Otherwise it runs
that worktree's own `concorde`, its `.concorde/bin/concorde` or, in Concorde's source checkout,
its `scripts/concorde.py` with the server's Python, as
`concorde workflow step --json <request> --wait <wait>` from the worktree's root, as a child of the
call's process with the server's environment and no standard input, and waits for it at most
`wait` plus 60 seconds. The command is a process of the server's, so the
[detached run](../../glossary.json#concept.detached-run) it starts for a new step is a process of
its own and lives until its run ends, whatever becomes of the calls that asked for it or of the
session and its server.

The answer is the JSON object the command printed, unchanged, whatever its exit status: a
[step outcome](../../execution/workflows/contracts.md#contract.workflows.step), finished, running,
lost or refused. An object without a step outcome's `key` whose `error` is a link is the step
command's refusal and is returned as the tool's refusal, that link unchanged; output that is no
JSON object is refused with `step_failed`.

### Registering a wait

`register_wait` first checks whether what it waits for already happened: the task's derived state
is one of `until`, the task's record names a main agent's session other than `rebound`, the run's
runner holds no [run lock](../../glossary.json#concept.run-lock), or
nobody holds the lock. Then it answers `{"registered": false, "already": <answer>}`, the value the
matching `concorde task wait` would print, and registers nothing. `until` admits `delivered`,
`merging`, `closed` and `failed` only, the states a task reaches while its workspace lock is held.

Otherwise, without a channel, it answers
`{"registered": false, "channel": false, "command": "<concorde task wait …>", "explanation": …}`,
where the command is `concorde task wait <task> --until <state>[,<state>…]`,
`concorde task wait <task> --rebound <session>`, `concorde task wait --run <run-id>` or `concorde task wait [<task>] --lock merge|workspace`. With a
channel it answers `{"registered": true, "wait": "<n>", "channel": true, "waits_for": "<what>"}`,
where the `waits_for` of a lock names the holder line the call saw, and runs that same
`concorde task wait` of the primary worktree as a process that ends when the server ends, until it
happens or ends another way. What that command prints becomes the event: its answer a `wait_done`,
its refusal a `wait_failed`, and no answer a `wait_failed` with the server's `call_failed` link. It
never takes or hands over a lock for the session.

## Channel events

Each event is a `notifications/claude/channel` notification with `content`, the text Claude
receives, and `meta`, whose keys become attributes of the `<channel source="concorde">` tag:

```concorde-contract
{
  "id": "contract.main-session.channel-event",
  "version": 2,
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
          "kind": {"enum": ["task", "rebound", "run", "lock"]},
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
  "semantics": "One event of the project MCP server to the Claude Code session that runs it. wait_done: a registered wait is over; kind (task for a state, rebound for a rebind, run or lock) and wait name it, and content carries the answer concorde task wait would print. wait_failed: the wait ended without it, such as a task that ended in another state (code wait_unreachable); content carries the rendered error chain. merge_ended: the merge task_merge started ended; exit_code and status say how, and content carries its JSON output, cut after 6000 characters with the path of the whole.",
  "example": {
    "content": "Concorde: task retry becoming delivered happened (wait 1): {\"task\": \"retry\", \"state\": \"delivered\", \"waited_seconds\": 412.3}",
    "meta": {"event": "wait_done", "kind": "task", "task": "retry", "wait": "1"}
  }
}
```

<a id="channel-event-participation"></a>

**Participation.** The server provides this contract, version 2, to the external Claude Code
session it runs in. Claude Code delivers it only to a session started with the server as a
channel, and drops it silently otherwise.
