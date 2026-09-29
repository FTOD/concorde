# Task sessions contracts

The exact commands and session trace node of [Task sessions](module.md). The obligations they serve
are in the [requirements](requirements.md).

## Session trace

Every [task session](../../glossary.json#concept.task-session) is a
[trace node](../../glossary.json#concept.trace-node) of kind `session` below its task's node, as
[Tracing](../../tracing/contracts.md#contract.tracing.node) defines it; its content is this value.

```concorde-contract
{
  "id": "contract.task-session.session-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "name",
      "main",
      "model",
      "reported_id"
    ],
    "properties": {
      "name": {
        "type": "string",
        "minLength": 1
      },
      "main": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string",
            "minLength": 1
          }
        ]
      },
      "model": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string",
            "minLength": 1
          }
        ]
      },
      "reported_id": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string",
            "minLength": 1
          }
        ]
      }
    }
  },
  "semantics": "The data of the typed value concorde-session-trace, the content of a task session's trace node sessions/<session id>/ of the task. name is the session's name task-<task-id>, main the main agent's session named with --main, which the task session reports to, model the model named with --model or null, and reported_id the identity Claude Code reported for the started background session, by which Concorde names it to Claude Code. The node's identity is the session identity, its start when the session started and its status unknown, since Concorde never observes a session's end; its metadata are the task and the model. The session's transcript is copied into the node when its task ends, before the task's folder moves to the history: Claude Code's conversation file as transcript.jsonl, listed among the node's artifacts as transcript with its digest, and the folder Claude Code keeps beside it, when there is one, as transcript/; a session whose transcript could not be kept has neither. A behaviour or field change increments the version.",
  "example": {
    "name": "task-severity",
    "main": "concorde-7d",
    "model": null,
    "reported_id": "33afbc14"
  }
}
```

## Commands

`concorde task session` is one of the `concorde task` commands: it runs in the primary worktree,
prints one JSON value and refuses in the shape, with the actor and exit statuses, that the
[Tasks commands](../tasks/contracts.md#commands) state. Besides the codes shared by every
`concorde task` command, such as `not_primary`, `unknown_task`, `task_closed` and `invalid_input`,
its refusals use these:

| Error code | Raised when |
| --- | --- |
| `missing_worktree` | `session` names a task whose worktree no longer exists. |
| `session_failed` | `session` could not start Claude Code, Claude Code exited without reporting a started background session (its output is in the message), or the task-session guidance is missing from the package. |
| `session_stop_failed` | `concorde task close` without a merge could not confirm a Claude Code task session of the task stopped: `claude stop <id>` could not run, or exited non-zero without answering `No job matching`; the message names the session, Claude Code's answer, the worktree the close would have removed and `claude stop <id>`, and the task is unchanged. |

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task session <task-id> --main <session> [--model <model>] [--dry-run]` | Starts a background Claude Code task session (`invalid_input` without `--main`): writes `.concorde/tasks/<task-id>/runtime/settings.json` and its [write hook](../../glossary.json#concept.write-hook), starts `claude --bg --name task-<task-id> --settings <file> --permission-mode auto [--model <model>]` in the task worktree with the rendered task-session guidance and the task's identity, goal, Modules, [decision log](../../glossary.json#concept.decision-log) and `--main` as first prompt, and records the started session as the node `sessions/<session id>/` of the task's trace. `--dry-run` writes the boundary and starts nothing | The recorded session, or with `--dry-run` `{"command": "<shell command without the prompt>", "cwd": "<task worktree>", "settings": "<path>"}` |

### At the end of a task

`concorde task close` and `concorde task merge`, which [Tasks](../tasks/contracts.md#commands) runs,
hand the task's task sessions, every node `sessions/<id>/`, to
[Task sessions](module.md#ending-claude-sessions). Each is named to Claude Code by its `reported_id`:

| When | What runs | When it fails |
| --- | --- | --- |
| A close without a merge, before anything else of the close | `claude stop <id>` for each session; exit 0, or `No job matching`, counts as stopped | The close is refused with `session_stop_failed` |
| Every close, just before the task's folder moves to the history | The only `<id>*.jsonl` of `projects/<worktree path, each character that is no letter or digit as ->/` of `$CLAUDE_CONFIG_DIR` (default `~/.claude`), else of any folder of `projects/`, is copied to the session's node as `transcript.jsonl`, and the folder of the same name without `.jsonl`, when present, as `transcript/` | A warning; the session is not removed |
| Every close, once the task is closed | `claude rm <id>` for each session whose transcript was kept; exit 0, or `No job matching`, counts as removed | A warning |

Each warning is one string in the command's `warnings`, naming the session's id and name, the task,
the whole reason (where the transcript was looked for, or the command with its exit code and Claude
Code's answer), where the transcript is kept when it was, and `claude rm <id>` to remove the
session by hand.
