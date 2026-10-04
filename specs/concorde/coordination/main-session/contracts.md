# Main session contracts

Coordination registers the exact tools and events below with the
[project MCP server](../../glossary.json#concept.project-mcp-server), as described in the
[Main session](module.md#the-project-mcp-server). The server itself, its session and how it runs a
call belong to [Distribution](../../distribution/contracts.md#project-mcp-server)'s host. Every tool
is a presentation of a command that already exists. Where a row says "as" a command, the result and
every refusal are that command's when it waits for no lock. [Tasks](../tasks/contracts.md#commands)
and [Tracing](../../kernel/tracing/contracts.md) define them. `run_result` and `locks` present
records no command prints in that shape. Their rows define their results. Their refusals are the
codes below. `task_merge` and `register_wait` answer at once with the start and the registration
defined [below](#starting-a-merge). The merge's own result and refusals, and the wait's answer, are
the commands' and arrive later. The issues part registers the
[Issue](../../glossary.json#concept.issue) tools ([Issues](../../issues/interface.md#mcp-tools)).
The workflow part registers `workflow_step` and `workflow_report`
([Workflows](../../workflows/contracts.md#mcp-tools)).

## Session

Distribution's host runs every call of these tools as a fresh process of the primary worktree's
current Concorde. The host finds:

- The project.
- The session it serves.
- The session's worktree.

The host decides once whether the session listens to it as a channel
([Distribution](../../distribution/contracts.md#session)). Coordination's tools rely on that as
follows:

- Every call reads the primary worktree's [task records](../../glossary.json#concept.task-record)
  afresh. Every call also reads the primary worktree's traces and locks afresh.
- A tool writes the session the host serves, from `CLAUDE_CODE_SESSION_ID`, into the holder line of
  every lock the tool takes.
- An escalation `task_escalate` records without `by` is the session's. In a task worktree bound as a
  workspace, the level is `task-session`. Otherwise, the level is `main-agent`. An explicit `by`
  wins.
- Only when the host judged the session a channel, `task_merge` and `register_wait` wake the session
  with a [channel event](#channel-events). Otherwise, they return the `concorde task wait` command
  for the session's background Bash.

Every tool returns one text content item holding one JSON value. A refusal sets `isError: true`. Its
value is `{"error": <link>}`, a link of the
[error contract](../../kernel/tracing/contracts.md#contract.tracing.error). This is the unchanged
link of the component that refused. For a refusal of Tasks, the link is
`Tasks (concorde task <command>)`. Otherwise, it is the tool's own `component` link of actor
`Concorde project MCP server (<tool>)`. The host's own refusals, such as `call_failed` and
`no_project`, are [Distribution's](../../distribution/contracts.md#refusals-of-the-host). The tools'
own refusal codes are:

| Code | Reason | When |
| --- | --- | --- |
| `invalid_input` | `input` | the tool is unknown, or its arguments do not satisfy its input schema or name a combination it does not take; the detail names the argument |
| `workspace_busy`, `merge_busy` | `environment` | `task_merge` found the lock held; the detail names the lock file and the holder's command, process, start time, session and task, and the evidence of kind `lock` carries the holder line as JSON |
| `start_failed` | `environment` | the operating system refused to start `concorde task merge`; both locks were released |
| `unknown_run` | `input` | `run_result` names no run of Execution: an identity no reader finds, or the node of something else, such as a task or a worker run, which has no [run result](../../glossary.json#concept.run-result) |
| `part_missing` | `input` | `run_result`, or `register_wait` for a `run`, where the execution part is not installed; the detail names the part |
| any Tasks or Tracing code | as there | the command the tool presents refused, such as `unknown_task`, `merge_busy` from `task_open` or `workspace_busy` from `task_close` |
| any other code | `environment` | an unexpected error of the server, as a link built from the exception |

## Tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `task_list` | optional `state`, a nonempty array of task states, and `main`, a main agent's session | as `concorde task list [--state <state>,…] [--main]` |
| `task_show` | `task` | as `concorde task show` |
| `trace_show` | `node`: a task, history key, run or worker run identity or a node's folder; optional `depth` ≥ 0 | as `concorde trace show <node> --depth <depth>` from the primary worktree |
| `run_result` | `run`: a run identity; present where the execution part is installed | `{"run", "running": false, "result": <run result>}` when no runner holds the run's [run lock](../../glossary.json#concept.run-lock) and its result is saved; otherwise `{"run", "running", "result": null, "progress": <run progress file or null>}`, where `running` is `true` while its runner holds the run lock and `false` for a run whose runner ended without writing a result |
| `locks` | none | `{"merge": <holder line or null>, "workspaces": {"<task>": <holder line or null>}}` for the merge lock and the workspace lock of every task that has not ended |
| `task_open` | `task`, `goal`, `modules` (nonempty), optional `base` | as `concorde task open`, taking the merge lock without waiting |
| `task_escalate` | `task`, `code`, `detail`, `reason`, `explanation`; optional `by` (`main-agent` or `task-session`; without it, the calling session's level as [Session](#session) states), `runs`, `error_files`, `escalations`, `attempts`, `options`, `recommendation` | as `concorde task escalate` with the matching options, `--by` being the given or derived level |
| `task_rebind` | `task`, `main` | as `concorde task rebind <task> --main <main>` |
| `task_report` | `task`, `text`; optional `escalations`, numbers ≥ 1 | as `concorde task report` with `--escalation` for each |
| `task_answer` | `task`, `reports` (nonempty numbers ≥ 1), `text` | as `concorde task answer` with `--report` for each |
| `task_close` | `task`, `outcome` (`completed` or `failed`); `note` for completed; `reason` and either `runs`/`error_files` or `no_error` true for failed; optional `force` | as `concorde task close --completed` or `--failed`, taking the workspace and merge locks without waiting |
| `task_resolve` | `task`, `issues` (nonempty); present where the issues part is installed | as `concorde task resolve <task> <issue>…` |
| `task_merge` | `task`; optional `checks`, or `resume` or `abort` true | the start below |
| `register_wait` | exactly one of `until` (with `task`), `rebound` (a [main agent](../../glossary.json#concept.main-agent)'s session, with `task`), `run`, and `lock` (`merge`, or `workspace` with `task`) | the registration below |

A holder line is the object a lock file holds while it is held,
[Tracing's](../../kernel/tracing/contracts.md#locks) `{"holder", "pid", "since"}` with `session` and
`task` when they are known.

### Starting a merge

The host starts the call's process for `task_merge` in a process session of its own. Until that
process becomes the merge, its standard error goes to a file of a private temporary directory of the
server. With an exclusive `flock` that does not wait, that process takes these locks in order:

- The task's merge attempt lock ([Tasks](../tasks/contracts.md#commands)).
- The task's [workspace lock](../../glossary.json#concept.workspace-lock).
- The [merge lock](../../glossary.json#concept.merge-lock).

The process writes into each lock a holder line naming:

- `` `concorde task merge` of task <task>, started by the project MCP server ``.
- Its own process.
- The session.
- The task.

When a lock is held, the process releases the locks it already took and refuses the call at once.
The refusal is `merge_busy` for the attempt lock, which a merge of the task still running holds. For
the other locks, the refusal is `workspace_busy` or `merge_busy`. With all three locks, the process
makes the task's next merge attempt folder `merges/<n>/` in the task's folder. The value `n` is one
more than the task's attempts so far. The process prints the start below. It then replaces itself
with `concorde task merge <task> --wait 0` of the primary worktree, with each `--check`, or with
`--resume` or `--abort`. The merge's standard output goes to `output.json` in that folder. Its
standard error goes to `messages.log` in that folder. The process names that folder in
`CONCORDE_MERGE_ATTEMPT` so that the merge records its attempt's node there, refused or not. The
merge keeps the three locked descriptors, named in its environment variable
`CONCORDE_INHERITED_LOCKS` as [Tracing](../../kernel/tracing/contracts.md#handing-a-lock-on) states.
The server never holds any of the descriptors, so the locks are released exactly when the merge
ends. When the operating system refuses to run `concorde task merge`, the call's process does the
following:

- It removes the folder again.
- After the start, it prints a `start_failed` refusal.
- It exits, which releases the locks.

The call is refused with that refusal.

The result is returned at once:

```json
{
  "started": {"command": "concorde task merge <task> --wait 0 …", "pid": 4242,
              "attempt": "<the attempt's folder>",
              "output": "<attempt>/output.json", "messages": "<attempt>/messages.log"},
  "locks": {"attempt": "<lock file>", "workspace": "<lock file>", "merge": "<lock file>"},
  "wake": {"channel": true}
}
```

With a channel, when the process ends, the server sends a `merge_ended` event carrying the output
from the attempt's folder, wherever the close moved it. Without a channel, `wake` is
`{"channel": false, "command": "concorde task wait <task> --merge", "explanation": …}`. This gives
the command to run in background Bash. Once the merge ends and writes its whole answer, the command
returns, although the close removes the task's workspace lock before then. The command names:

- The attempt's node.
- Its `output.json`.
- Its `messages.log`.

These are in the task's folder or, once the merge closed the task, in the
[history](../../glossary.json#concept.history).

When a session loses the start's answer or the event, such as after a restart, the session finds the
merge again from the task:

- `task_show` gives the task's state and folder, current or in the history.
- `trace_show` of the task gives its merge attempts as the nodes `merges/<n>/`, each with its
  outcome and error.
- The attempt's `output.json` holds the merge's whole answer, with its warnings and refusal.

`concorde task wait <task> --merge` waits for a merge that still runs and names those files.

### Registering a wait

Where the execution part is not installed, `register_wait` for a `run` is first refused with
`part_missing`, as `concorde task wait --run` is. It then checks whether what it waits for already
happened by checking whether any of these conditions is true:

- The task's derived state is one of `until`.
- The task's record names a main agent's session other than `rebound`.
- The run's runner holds no [run lock](../../glossary.json#concept.run-lock).
- Nobody holds the lock.

If what it waits for already happened, it answers `{"registered": false, "already": <answer>}` and
registers nothing. The answer is the value the matching `concorde task wait` would print, with the
same fields and `waited_seconds` 0. `until` admits only these states:

- `delivered`
- `closed`
- `failed`

A task reaches these states while its workspace lock is held and keeps them once the lock is
released. `merging` is refused with `invalid_input`, as `concorde task wait` refuses it.

Otherwise, without a channel, it answers
`{"registered": false, "channel": false, "command": "<concorde task wait …>", "explanation": …}`.
The command is one of:

- `concorde task wait <task> --until <state>[,<state>…]`
- `concorde task wait <task> --rebound <session>`
- `concorde task wait --run <run-id>`
- `concorde task wait [<task>] --lock merge|workspace`

Otherwise, with a channel, it answers
`{"registered": true, "wait": "<n>", "channel": true, "waits_for": "<what>"}`. The `waits_for` of a
lock names the holder line the call saw. `register_wait` runs that same `concorde task wait` of the
primary worktree as a process until what it waits for happens or the process ends another way. The
process ends when the server ends. What that command prints becomes the event:

- Its answer becomes a `wait_done`.
- Its refusal becomes a `wait_failed`.
- No answer becomes a `wait_failed` with the server's `call_failed` link.

`register_wait` never takes or hands over a lock for the session.

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
  "semantics": "One event of the project MCP server to the Claude Code session that runs it. wait_done: a registered wait is over; kind (task for a state, rebound for a rebind, run or lock) and wait name it, and content carries the answer concorde task wait would print. wait_failed: the wait ended without it, such as a task that ended in another state (code wait_unreachable); content carries the rendered error chain. merge_ended: the merge task_merge started ended; exit_code and status say how, and content carries its JSON output from its attempt's output.json, cut after 6000 characters with the path of the whole.",
  "example": {
    "content": "Concorde: task retry becoming delivered happened (wait 1): {\"task\": \"retry\", \"state\": \"delivered\", \"waited_seconds\": 412.3}",
    "meta": {"event": "wait_done", "kind": "task", "task": "retry", "wait": "1"}
  }
}
```

<a id="channel-event-participation"></a>

**Participation.** The server provides this contract, version 2, to the external Claude Code
session it runs in. Only when a session starts with the server as a channel does Claude Code
deliver the contract to that session. Otherwise, Claude Code drops the contract silently.
