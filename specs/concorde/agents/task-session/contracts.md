# Task session contracts

The exact commands and session report of [Task session](module.md). The obligations they serve
are in the [requirements](requirements.md).

## Session report

The arguments of the `concorde_report` tool with which a pi task session ends a [session round](module.md#concept.task-session.round).

```concorde-contract
{
  "id": "contract.task-session.report",
  "version": 1,
  "schema": {
    "oneOf": [
      {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "status",
          "summary",
          "commit",
          "decisions",
          "open"
        ],
        "properties": {
          "status": {
            "const": "delivered"
          },
          "summary": {
            "type": "string",
            "minLength": 1
          },
          "commit": {
            "type": "string",
            "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
          },
          "decisions": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "open": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "status",
          "summary",
          "escalations",
          "decisions",
          "open"
        ],
        "properties": {
          "status": {
            "const": "escalated"
          },
          "summary": {
            "type": "string",
            "minLength": 1
          },
          "escalations": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": true,
            "items": {
              "type": "integer",
              "minimum": 1
            }
          },
          "decisions": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "open": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      }
    ]
  },
  "semantics": "The arguments a pi task session passes to concorde_report to end a session round, which the supervisor records as the round's report. status is delivered when delivery committed the task on its branch, with commit the delivery commit, or escalated when the session cannot go further without the main agent, with escalations the numbers (from 1, in record order) of the escalations it recorded with concorde task escalate --by task-session, which carry the error chains. summary says what the round did; decisions lists each decision the session made without the main agent, with its reason; open lists what is still open. The supervisor records delivered or escalated only when the task record holds that delivery commit or those task-session escalations, and a failed round otherwise. A behaviour or field change increments the version.",
  "example": {
    "status": "escalated",
    "summary": "Implemented the severity levels; the Spec does not say whether warnings block delivery.",
    "escalations": [
      1
    ],
    "decisions": [
      "Named the enum Severity after the Spec's term, since the Module has no other enum."
    ],
    "open": [
      "Whether warnings block delivery."
    ]
  }
}
```


## Commands

`concorde task session` is one of the `concorde task` commands: it runs in the primary worktree,
prints one JSON value and refuses in the shape, with the actor and exit statuses, that the
[Tasks commands](../../tasks/contracts.md#commands) state. Besides the codes shared by every
`concorde task` command, such as `not_primary`, `unknown_task`, `task_closed` and `invalid_input`,
its refusals use these:

| Error code | Raised when |
| --- | --- |
| `missing_worktree` | `session` names a task whose worktree no longer exists. |
| `session_failed` | `session` could not start Claude Code, Claude Code exited without reporting a started background session (its output is in the message), pi, `bwrap`, `socat` or the sandbox-runtime package is missing (each is named), the pi supervisor could not start, or the task-session guidance is missing from the package. |
| `client_unknown` | `session` cannot read the main session's program from the environment: `CONCORDE_CLIENT` is unset, `CLAUDECODE` is not 1 and no pi session variable is set; the message names each. |
| `session_busy` | `session` starts a pi session, or `--answer` a round, while a round of the task's pi session runs; the message names the round and its supervisor process. |
| `no_session` | `--answer` names a task that has no pi session. |
| `session_idle` | `--stop` names a task whose pi session has no running round. |

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task session <task-id> [--main <session>] [--model <model>] [--dry-run]` | Starts a task session on the main session's program. For Claude Code (`--main` required): writes `.concorde/tasks/<task-id>.session/settings.json` and its write hook, starts `claude --bg --name task-<task-id> --settings <file> --permission-mode auto [--model <model>]` in the task worktree with the rendered task-session guidance and the task's identity, goal, Modules, decision log and `--main` as first prompt, and appends the started session to the record. For pi: writes `boundary.ts` and the path decisions it imports into that directory, starts the detached supervisor of round 1, which runs `pi -p --mode json --approve -e <boundary.ts> --session-dir <directory>/pi --session-id <session id> [--model <model>]` in the task worktree with the rendered pi task-session guidance and the task's identity, goal, Modules and decision log as prompt, and appends the session with round 1 `running` to the record. `--dry-run` writes the boundary and starts nothing | The recorded session, or with `--dry-run` `{"command": "<shell command without the prompt>", "cwd": "<task worktree>", "settings": "<path>"}` (for pi, `"boundary"` instead of `"settings"`) |
| `concorde task session <task-id> --answer <text>` | pi only: starts the next round of the task's latest pi session on the same session file, with the answer as its prompt | The recorded session |
| `concorde task session <task-id> --stop` | pi only: asks the running round's supervisor to stop, which sends the round's pi process group SIGTERM and SIGKILL 3 seconds later, and records the round as `stopped`; waits up to 15 seconds for that record | The recorded session |
