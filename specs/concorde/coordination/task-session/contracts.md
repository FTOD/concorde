# Task sessions contracts

The exact commands and session trace node of [Task sessions](module.md). The obligations they serve
are in the [requirements](requirements.md).

## Session trace

Every [task session](../../glossary.json#concept.task-session) is a
[trace node](../../glossary.json#concept.trace-node) of kind `session` below its task's node, as
[Tracing](../../kernel/tracing/contracts.md#contract.tracing.node) defines it; its content is this value.

```concorde-contract
{
  "id": "contract.task-session.session-trace",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "name",
      "main",
      "model",
      "reported_id",
      "session_id",
      "claude_state",
      "models",
      "model_usage"
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
      },
      "session_id": {
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
      "claude_state": {
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
      "models": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object",
            "additionalProperties": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "tokens_in",
                "tokens_out",
                "tokens_cache_read",
                "tokens_cache_write",
                "messages"
              ],
              "properties": {
                "tokens_in": {
                  "type": "integer",
                  "minimum": 0
                },
                "tokens_out": {
                  "type": "integer",
                  "minimum": 0
                },
                "tokens_cache_read": {
                  "type": "integer",
                  "minimum": 0
                },
                "tokens_cache_write": {
                  "type": "integer",
                  "minimum": 0
                },
                "messages": {
                  "type": "integer",
                  "minimum": 0
                }
              }
            }
          }
        ]
      },
      "model_usage": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object"
          }
        ]
      }
    }
  },
  "semantics": "The data of the typed value concorde-session-trace, the content of a task session's trace node sessions/<session id>/ of the task. name is the session's name task-<task-id>, main the main agent's session named with --main, which the task session reported to when it started; the task record's main names the session it reports to now, which concorde task rebind may have changed since, model the model named with --model or null, and reported_id the short identity Claude Code reported for the started background session, by which Concorde names it to Claude Code. session_id is the session's full session id, the name of its transcript, as the sessionId of the session's entry in claude agents --json --all, recorded when the session starts or, failing that, when its task ends; null while Claude Code has not told it. The node's identity is the reported identity, its start when the session started, its status unknown and its end and usage null until its task ends, since Concorde does not see a session end. When the task ends, before the task's folder moves to the history, the node is finished from Claude Code's records: the session's transcript is copied into the node as transcript.jsonl, listed among the node's artifacts as transcript with its digest, and the folder Claude Code keeps beside it, when there is one, as transcript/; a session whose transcript could not be kept has neither. The node's usage then counts the tokens of the assistant records of that transcript and of the subagent transcripts in transcript/subagents/, each API message (message.id) once, its turns those messages and its duration the time from the earliest to the latest time the transcript's records carry; its cost_usd is the totalCostUSD of the transcript's last cost-state record when no assistant record follows it, otherwise null; its ended_at is that latest time. claude_state is the session's state in claude agents --json --all at that moment, or null when Claude Code no longer lists it; the node's status is ok for done, failed for failed and unknown otherwise, and its outcome is that state, null when there is none. models maps each model of those assistant records to its tokens and its messages, null when no transcript was kept; model_usage is the modelUsage of that cost-state record as Claude Code wrote it, with each model's cost, null when there is none. A session whose transcript was not kept keeps usage null and ended_at null. Its metadata are the task and the model. A behaviour or field change increments the version.",
  "example": {
    "name": "task-severity",
    "main": "concorde-7d",
    "model": null,
    "reported_id": "33afbc14",
    "session_id": "33afbc14-3ec3-4a74-b3d5-b2278eda5756",
    "claude_state": "done",
    "models": {
      "claude-opus-5-5": {
        "tokens_in": 1204,
        "tokens_out": 88210,
        "tokens_cache_read": 30512877,
        "tokens_cache_write": 412033,
        "messages": 391
      }
    },
    "model_usage": null
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
| `session_failed` | `session` could not start Claude Code, Claude Code exited without reporting a started background session (its output is in the message), or the composed task-session guidance `generated/guidance/task-session.md` is missing from the package. |
| `session_stop_failed` | `concorde task close` without a merge could not confirm a Claude Code task session of the task stopped: `claude stop <id>` could not run, or exited non-zero without answering `No job matching`; the message names the session, Claude Code's answer, the worktree the close would have removed and `claude stop <id>`, and the task is unchanged. |

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task session <task-id> --main <session> [--model <model>] [--dry-run]` | Starts a background Claude Code task session (`invalid_input` without `--main`): writes `.concorde/tasks/<task-id>/runtime/settings.json` and its hook ([settings](#task-session-settings)), the settings also holding `disabledMcpjsonServers`, `concorde` followed by every other server of the `.mcp.json` files the session loads that the primary worktree never approved, and `enabledMcpjsonServers`, every one it approved ([module](module.md#project-mcp-approvals)), and `runtime/mcp.json`, which configures the [project MCP server](../../glossary.json#concept.project-mcp-server) `concorde` as the running Python with the running package's `scripts/concorde.py project-mcp` and `CONCORDE_CHANNEL=0`, since a background session is never woken by channel events, starts `claude --bg --name task-<task-id> --settings <file> --mcp-config <runtime/mcp.json> --permission-mode auto [--model <model>]` in the task worktree with the composed task-session guidance and the task's identity, goal, [Modules](../../glossary.json#concept.module), [decision log](../../glossary.json#concept.decision-log) and `--main` as first prompt, and records the started session as the node `sessions/<session id>/` of the task's trace, with the full session id `claude agents --json --all` gives for it when it gives one, naming `--main` as the [task record](../../glossary.json#concept.task-record)'s `main` ([record updates](../tasks/contracts.md#record-updates)). `--dry-run` writes the boundary and starts nothing | The recorded session, or with `--dry-run` `{"command": "<shell command without the prompt>", "cwd": "<task worktree>", "settings": "<path>", "mcp_config": "<path>"}` |

### Task-session settings

A task session's settings, `.concorde/tasks/<task>/runtime/settings.json`, hold the hook of its
[session boundary](../../glossary.json#concept.session-boundary) and nothing that restricts the
session besides:

- a PreToolUse hook on Edit, Write, MultiEdit and NotebookEdit, `session_hook.py` copied beside the
  settings with the task worktree and [decision log](../../glossary.json#concept.decision-log)
  embedded, which allows a path inside the task worktree, or the decision log while its folder
  exists, and denies any other with a reason naming the task worktree, or naming the closed task
  for the decision log of a task whose folder has moved to the history; any failure denies;
- no `sandbox`: the session's Bash runs as the developer's own shell does, with every path,
  process, socket and host open to it;
- no `permissions.deny` entries: reads stay open.

What the settings carry besides is no part of the boundary: the
[approvals](module.md#project-mcp-approvals) that keep Claude Code from asking a background session
about a [project MCP server](../../glossary.json#concept.project-mcp-server).

### At the end of a task

`concorde task close` and `concorde task merge`, which [Tasks](../tasks/contracts.md#commands) runs,
hand the task's task sessions, every node `sessions/<id>/`, to
[Task sessions](module.md#ending-claude-sessions). Each is named to Claude Code by its `reported_id`:

| When | What runs | When it fails |
| --- | --- | --- |
| A close without a merge, before anything else of the close | `claude stop <id>` for each session; exit 0, or `No job matching`, counts as stopped | The close is refused with `session_stop_failed` |
| Every close, just before the task's folder moves to the history | `claude agents --json --all`, once for the close; the entry whose `id` is the session's `reported_id` gives its `sessionId`, `cwd` and `state`. The transcript `projects/<cwd, each character that is no letter or digit as ->/<session id>.jsonl` of `$CLAUDE_CONFIG_DIR` (default `~/.claude`), else `<session id>.jsonl` of any folder of `projects/`, is copied to the session's node as `transcript.jsonl`, and the folder of the same name without `.jsonl`, when present, as `transcript/`; the node is then finished as the [session trace](#contract.task-session.session-trace) says | A warning naming what Claude Code answered or where the transcript was looked for; the session is not removed. The node still receives the session id and status Claude Code told |
| Every close, once the task is closed | `claude rm <id>` for each session whose transcript was kept; exit 0, or `No job matching`, counts as removed | A warning |

Each warning is one string in the command's `warnings`, naming the session's id and name, the task,
the whole reason (where the transcript was looked for, or the command with its exit code and Claude
Code's answer), where the transcript is kept when it was, and `claude rm <id>` to remove the
session by hand.
