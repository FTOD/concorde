# Task sessions contracts

The exact commands, [session report](../../glossary.json#concept.session-report) and session and
round trace nodes of [Task sessions](module.md). The obligations they serve are in the [requirements](requirements.md).

## Session report

The arguments of the `concorde_report` tool with which a pi
[task session](../../glossary.json#concept.task-session) ends a
[session round](../../glossary.json#concept.session-round).

```concorde-contract
{
  "id": "contract.task-session.report",
  "version": 3,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["status", "summary", "commit", "escalations", "decisions", "open"],
    "properties": {
      "status": {"type": "string", "enum": ["delivered", "escalated"]},
      "summary": {"type": "string", "minLength": 1},
      "commit": {
        "type": ["string", "null"],
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?(?![\\s\\S])"
      },
      "escalations": {
        "type": "array",
        "uniqueItems": true,
        "items": {"type": "integer", "minimum": 1}
      },
      "decisions": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "open": {"type": "array", "items": {"type": "string", "minLength": 1}}
    },
    "oneOf": [
      {
        "properties": {
          "status": {"const": "delivered"},
          "commit": {"type": "string"},
          "escalations": {"maxItems": 0}
        }
      },
      {
        "properties": {
          "status": {"const": "escalated"},
          "commit": {"type": "null"},
          "escalations": {"minItems": 1}
        }
      }
    ]
  },
  "semantics": "The arguments a pi task session passes to concorde_report to end a session round, which the supervisor records as the round's report. All six fields are required. status is delivered when delivery committed the task on its branch, with commit the full delivery commit and escalations an empty array, or escalated when the session cannot go further without the main agent, with commit null and escalations a nonempty unique array of positive numbers (from 1, in record order) of the escalations it recorded with concorde task escalate --by task-session, which carry the error chains. summary says what the round did; decisions lists each decision the session made without the main agent, with its reason; open lists what is still open. The supervisor records delivered only when the task branch holds commit as a delivery commit of the task's workspace, read from Git, that verifies against its evidence bundle as Delivery checks it (contract.delivery.evidence-bundle), and escalated only when the task's trace holds those task-session escalations, and a failed round otherwise. Version 3 governs admission of new tool reports only; already persisted reports of earlier versions remain unchanged and are not revalidated. Version 2 had the same fields and accepted a delivered report whose commit was a delivery commit by its subject and trailers alone, without verifying it against its evidence bundle. Version 1 required only the fields of its status: a delivered report had status, summary, commit, decisions and open, with no escalations, and an escalated report had status, summary, escalations, decisions and open, with no commit. A behaviour or field change increments the version.",
  "example": {
    "status": "escalated",
    "summary": "Implemented the severity levels; the Spec does not say whether warnings block delivery.",
    "commit": null,
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


## Session trace

Every task session is a [trace node](../../glossary.json#concept.trace-node) of kind `session` below its task's node, and
each round of a pi task session one of kind `round` below the session's, as
[Tracing](../../tracing/contracts.md#contract.tracing.node) defines them; their contents are these values.

```concorde-contract
{
  "id": "contract.task-session.session-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "program",
      "name",
      "main",
      "model",
      "reported_id"
    ],
    "properties": {
      "program": {
        "enum": [
          "claude",
          "pi"
        ]
      },
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
  "semantics": "The data of the typed value concorde-session-trace, the content of a task session's trace node sessions/<session id>/ of the task. program is the agent program, name the session's name task-<task-id>, main the main agent's session it reports to (null for a pi session started without --main), model the model named with --model or null, and reported_id the identity Claude Code reported for a started background session (null for pi, whose session identity is the node's). The node's identity is the session identity, its start when the session started and its status unknown, since Concorde never observes a session's end; its metadata are the task, the program and the model. A pi session's rounds are its children, rounds/<n>/, and its pi session files lie under pi/ as its transcript. A behaviour or field change increments the version.",
  "example": {
    "program": "claude",
    "name": "task-severity",
    "main": "concorde-7d",
    "model": null,
    "reported_id": "33afbc14"
  }
}
```

```concorde-contract
{
  "id": "contract.task-session.round-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "round",
      "prompt",
      "answer",
      "outcome",
      "supervisor_pid",
      "report"
    ],
    "properties": {
      "round": {
        "type": "integer",
        "minimum": 1
      },
      "prompt": {
        "enum": [
          "task",
          "answer"
        ]
      },
      "answer": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string"
          }
        ]
      },
      "outcome": {
        "enum": [
          "running",
          "delivered",
          "escalated",
          "failed",
          "stopped"
        ]
      },
      "supervisor_pid": {
        "type": "integer"
      },
      "report": {
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
  "semantics": "The data of the typed value concorde-round-trace, the content of one pi session round's trace node rounds/<n>/ of the session's node. round is its number from 1; prompt says whether its prompt was the task or the main agent's answer, answer is that answer or null; outcome is running until the supervisor records delivered, escalated, failed or stopped; supervisor_pid is the supervisor's process in its own PID namespace, only for display and for the settle of a round whose supervisor ended; report is the session report the round received, or null. The node's status is ok for delivered, blocked for escalated and failed for failed and stopped, with the outcome as its outcome and the round's error link as its error; its usage holds the tokens, cost and turns pi reported and the round's duration; its files are prompt.md, events.jsonl, stderr.log and supervisor.log. A behaviour or field change increments the version.",
  "example": {
    "round": 2,
    "prompt": "answer",
    "answer": "Merge main into the task branch and deliver again.",
    "outcome": "delivered",
    "supervisor_pid": 41233,
    "report": {
      "status": "delivered",
      "summary": "Merged main and delivered again.",
      "commit": "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432",
      "escalations": [],
      "decisions": [],
      "open": []
    }
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
| `session_failed` | `session` could not start Claude Code, Claude Code exited without reporting a started background session (its output is in the message), pi, `bwrap`, `socat` or the sandbox-runtime package is missing (each is named), the pi supervisor could not start, or the task-session guidance is missing from the package. |
| `client_unknown` | `session` cannot read the main session's program from the environment: `CONCORDE_CLIENT` is unset, `CLAUDECODE` is not 1 and no pi session variable is set; the message names each. |
| `session_busy` | `session` starts a pi session, or `--answer` a round, while a round of the task's pi session runs; the message names the round and its supervisor process. |
| `no_session` | `--answer`, `--wait` or `--stop` names a task that has no pi session. |
| `session_idle` | `--stop` names a task whose pi session has no running round. |

A pi round recorded `failed` carries, as its `error`, a link of one of these codes:

| Error code | Raised when |
| --- | --- |
| `session_no_report` | pi ended the round without calling `concorde_report`; the link names pi's exit code, stop reason and error message and the paths of the event stream and standard error. |
| `session_report_unverified` | the report does not follow the [session report](#contract.task-session.report) contract, names a commit that is no [delivery commit](../../glossary.json#concept.delivery-commit) of the task's workspace on its branch or that does not verify against its [evidence bundle](../../glossary.json#concept.evidence-bundle), as Delivery checks it, or names an escalation the task's [trace](../../glossary.json#concept.trace) does not hold at the level `task-session`; the link names each mismatch, and the round keeps the report. |
| `session_supervisor_lost` | the round's supervisor ended without recording the round; the round is recorded by the next start, `--answer`, `--stop` or `--wait` of that task, and the link names the supervisor's process and the round's logs. |

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task session <task-id> [--main <session>] [--model <model>] [--dry-run]` | Starts a task session on the main session's program. For Claude Code (`--main` required, `invalid_input` without it): writes `.concorde/tasks/<task-id>/runtime/settings.json` and its [write hook](../../glossary.json#concept.write-hook), starts `claude --bg --name task-<task-id> --settings <file> --permission-mode auto [--model <model>]` in the task worktree with the rendered task-session guidance and the task's identity, goal, Modules, [decision log](../../glossary.json#concept.decision-log) and `--main` as first prompt, and records the started session as the node `sessions/<session id>/` of the task's trace. For pi: writes `boundary.ts` and the path decisions it imports into that directory, starts the detached supervisor of round 1, which runs `pi -p --mode json --approve -e <boundary.ts> --session-dir <session node>/pi --session-id <session id> [--model <model>]` in the task worktree with the rendered pi task-session guidance and the task's identity, goal, Modules and decision log as prompt, and records the session's node with round 1 `running` as its node `rounds/1/`. `--dry-run` writes the boundary and starts nothing | The recorded session, or with `--dry-run` `{"command": "<shell command without the prompt>", "cwd": "<task worktree>", "settings": "<path>"}` (for pi, `"boundary"` instead of `"settings"`) |
| `concorde task session <task-id> --answer <text>` | pi only: starts the next round of the task's latest pi session on the same session file, with the answer as its prompt | The recorded session |
| `concorde task session <task-id> --stop` | pi only: asks the running round's supervisor to stop, which sends the round's pi process group SIGTERM and SIGKILL 3 seconds later, and records the round as `stopped`; waits up to 15 seconds for that record. When the round is not recorded in that time, the command records it `failed` with `session_supervisor_lost` if its supervisor has ended, and otherwise returns without waiting further while the supervisor goes on stopping the round; `concorde task show` shows the round once it is recorded | The recorded session, with the round as it stands when the command returns |
| `concorde task session <task-id> --wait [<seconds>]` | pi only: waits inside the command, rereading the session's round nodes, until no round of the task's latest pi session runs, recording a round whose supervisor ended as `failed` with `session_supervisor_lost`; with `<seconds>`, returns after that time even while the round runs | The recorded session, with its last round's outcome, or the round `running` when `<seconds>` passed first |
