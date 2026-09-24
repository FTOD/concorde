# Tasks contracts

The exact record, commands and record updates of [Tasks](module.md). The obligations they serve are
in the [requirements](requirements.md).

## Task record

```concorde-contract
{
  "id": "contract.tasks.record",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "id",
      "goal",
      "modules",
      "branch",
      "worktree",
      "base_commit",
      "state",
      "created_at",
      "updated_at",
      "runs",
      "deliveries",
      "escalations",
      "closed"
    ],
    "properties": {
      "id": {
        "type": "string",
        "pattern": "^[a-z0-9][a-z0-9-]{0,47}$"
      },
      "goal": {
        "type": "string",
        "minLength": 1
      },
      "modules": {
        "type": "array",
        "minItems": 1,
        "uniqueItems": true,
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "branch": {
        "type": "string",
        "pattern": "^concorde/[a-z0-9][a-z0-9-]{0,47}$"
      },
      "worktree": {
        "type": "string",
        "pattern": "^/"
      },
      "base_commit": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "state": {
        "enum": [
          "open",
          "active",
          "delivered",
          "merged",
          "abandoned"
        ]
      },
      "created_at": {
        "type": "string",
        "minLength": 1
      },
      "updated_at": {
        "type": "string",
        "minLength": 1
      },
      "runs": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/run"
        }
      },
      "deliveries": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/delivery"
        }
      },
      "escalations": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/escalation"
        }
      },
      "closed": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "$ref": "#/$defs/closed"
          }
        ]
      }
    },
    "$defs": {
      "run": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "run_id",
          "operation",
          "modules",
          "writes",
          "status",
          "host_pid",
          "started_at",
          "finished_at"
        ],
        "properties": {
          "run_id": {
            "type": "string",
            "minLength": 1
          },
          "operation": {
            "type": "string",
            "minLength": 1
          },
          "modules": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "writes": {
            "type": "boolean"
          },
          "status": {
            "enum": [
              "running",
              "ok",
              "blocked",
              "failed",
              "interrupted"
            ]
          },
          "host_pid": {
            "type": "integer",
            "minimum": 1
          },
          "started_at": {
            "type": "string",
            "minLength": 1
          },
          "finished_at": {
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
      "delivery": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "run_id",
          "commit",
          "bundle",
          "readiness_run",
          "at"
        ],
        "properties": {
          "run_id": {
            "type": "string",
            "minLength": 1
          },
          "commit": {
            "type": "string",
            "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
          },
          "bundle": {
            "type": "string",
            "minLength": 1
          },
          "readiness_run": {
            "type": "string",
            "minLength": 1
          },
          "at": {
            "type": "string",
            "minLength": 1
          }
        }
      },
      "closed": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "state",
          "at",
          "primary_commit",
          "worktree_removed"
        ],
        "properties": {
          "state": {
            "enum": [
              "merged",
              "abandoned"
            ]
          },
          "at": {
            "type": "string",
            "minLength": 1
          },
          "primary_commit": {
            "type": "string",
            "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
          },
          "worktree_removed": {
            "type": "boolean"
          }
        }
      },
      "escalation": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "at",
          "error"
        ],
        "properties": {
          "at": {
            "type": "string",
            "minLength": 1
          },
          "error": {
            "$ref": "#/$defs/error"
          }
        }
      },
      "error": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "level",
          "actor",
          "code",
          "detail",
          "evidence",
          "attempts",
          "unhandled",
          "options",
          "recommendation",
          "causes"
        ],
        "properties": {
          "level": {
            "enum": [
              "main-agent",
              "operation",
              "harness",
              "worker",
              "check",
              "component"
            ]
          },
          "actor": {
            "type": "string",
            "minLength": 1
          },
          "code": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*$"
          },
          "detail": {
            "type": "string",
            "minLength": 1
          },
          "evidence": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/evidence"
            }
          },
          "attempts": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "unhandled": {
            "$ref": "#/$defs/unhandled"
          },
          "options": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "recommendation": {
            "type": "string"
          },
          "causes": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/error"
            }
          }
        }
      },
      "evidence": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "kind",
          "ref",
          "detail"
        ],
        "properties": {
          "kind": {
            "type": "string",
            "minLength": 1
          },
          "ref": {
            "type": "string"
          },
          "detail": {
            "type": "string"
          }
        }
      },
      "unhandled": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "reason",
          "explanation"
        ],
        "properties": {
          "reason": {
            "enum": [
              "permission",
              "decision",
              "scope",
              "capability",
              "exhausted",
              "environment",
              "input"
            ]
          },
          "explanation": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "semantics": "The task record stored as .concorde/tasks/<id>.json in the primary worktree, written only by the Task store. id is chosen by the main agent and never reused; branch is concorde/<id>; worktree is the absolute path of the task's linked worktree; base_commit is the commit the branch was created from. modules starts with the Modules named at open and grows by every Module a run names; every entry was a registered Module when added. state follows open -> active -> delivered -> merged | abandoned, where delivered returns to active when a run with writes true starts, and open, active and delivered may become abandoned. runs lists every Operation run in start order: status running while the host works, then the Operation result status, or interrupted when the host process host_pid ended without finishing the run; writes tells whether the Operation may change the worktree. deliveries lists every delivery in order, with the delivery commit on the task branch, the project-relative path of the committed evidence bundle and the validate run whose readiness it consumed. escalations lists, in order, every error chain the main agent escalated to the developer with concorde task escalate, each with its time and the main agent's link, a contract.concorde.error link of level main-agent whose causes are the escalated errors; $defs error, evidence and unhandled are that contract's definitions. closed is null until the task is closed; it then records the final state, the head of the primary branch at closing and whether the worktree was removed. Timestamps are RFC 3339 in UTC.",
  "example": {
    "id": "severity",
    "goal": "let Issue reports carry a severity",
    "modules": [
      "module.issues"
    ],
    "branch": "concorde/severity",
    "worktree": "/home/dev/project.tasks/severity",
    "base_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "state": "delivered",
    "created_at": "2026-09-24T09:00:00Z",
    "updated_at": "2026-09-24T10:40:00Z",
    "runs": [
      {
        "run_id": "r-20260924T090100-understand-3f2a9c01",
        "operation": "understand",
        "modules": [
          "module.issues"
        ],
        "writes": false,
        "status": "ok",
        "host_pid": 41021,
        "started_at": "2026-09-24T09:01:00Z",
        "finished_at": "2026-09-24T09:04:00Z"
      },
      {
        "run_id": "r-20260924T103000-validate-9b1c0d2e",
        "operation": "validate",
        "modules": [
          "module.issues"
        ],
        "writes": false,
        "status": "ok",
        "host_pid": 41877,
        "started_at": "2026-09-24T10:30:00Z",
        "finished_at": "2026-09-24T10:33:00Z"
      },
      {
        "run_id": "r-20260924T103800-delivery-77d0e4f5",
        "operation": "delivery",
        "modules": [
          "module.issues"
        ],
        "writes": false,
        "status": "ok",
        "host_pid": 41990,
        "started_at": "2026-09-24T10:38:00Z",
        "finished_at": "2026-09-24T10:40:00Z"
      }
    ],
    "deliveries": [
      {
        "run_id": "r-20260924T103800-delivery-77d0e4f5",
        "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
        "bundle": ".concorde/evidence/severity/1.json",
        "readiness_run": "r-20260924T103000-validate-9b1c0d2e",
        "at": "2026-09-24T10:40:00Z"
      }
    ],
    "escalations": [],
    "closed": null
  }
}
```

## Commands

Every command runs in the primary worktree, prints one JSON value on standard output and exits
with status 0 on success. A refusal prints `{"error": <link>}`, where the link is a
[`component` link](../contracts.md#contract.concorde.error) of the actor
`Tasks (concorde task <command>)` whose code is one of the error codes below, whose detail names
the task, Module, path, run or Git command concerned with its message (for an unknown task, the
known tasks; for a dirty worktree, the uncommitted paths), and whose reason is `environment` for
`git_failed`, `worktree_failed`, `record_conflict` and `record_unreadable`, `decision` for
`dirty_worktree` and `not_merged`, and `input` otherwise. A refusal changes nothing and exits with
status 1; a malformed command line prints the same shape with the code `invalid_command` and exits
with status 2.

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task open <task-id> --goal <text> --modules <id>[,<id>…] [--base <ref>] [--path <dir>]` | Creates branch `concorde/<task-id>` at `--base` (default: the primary worktree's `HEAD`), adds a worktree for it at `--path` (default: `<parent>/<primary>.tasks/<task-id>`), writes the record in state `open` and the decision log | The new record |
| `concorde task list [--state <state>]` | None | An array of records, oldest first |
| `concorde task show <task-id>` | None | `{"record": <record>, "decision_log": "<absolute path>"}` |
| `concorde task close <task-id> --merged` | Checks the merge, removes the worktree, sets state `merged` | The updated record |
| `concorde task close <task-id> --abandoned [--force]` | Removes the worktree, discarding uncommitted changes only with `--force`, sets state `abandoned` | The updated record |
| `concorde task escalate <task-id> (--run <run-id> \| --error-file <path>)… --code <code> --detail <text> --reason <reason> --explanation <text> [--attempt <text>]… [--option <text>]… [--recommendation <text>]` | Builds the main agent's link of level `main-agent` whose causes are the `error` of each named run of the task and each error read from a file (a link, or a JSON value whose `error` is one), appends it to the record's `escalations` and appends it to the decision log, rendered and as JSON | `{"escalated": <link>, "decision_log": "<absolute path>", "rendered": "<the chain as indented text>"}` |

The decision log that `open` creates contains exactly a level-1 heading `Decision log: <task-id>`
and a paragraph `Goal: <goal>`.

| Error code | Raised when |
| --- | --- |
| `not_primary` | The command runs outside the primary worktree. |
| `invalid_input` | A goal or Module list is missing or repeats a Module, or `close` names neither or both of `--merged` and `--abandoned`, or `--force` without `--abandoned`. |
| `worktree_failed` | Git refused to add or remove the worktree; the message carries Git's error. |
| `invalid_task_id` | The identity does not match the record's `id` pattern. |
| `task_exists` | A record with that identity exists, whatever its state. |
| `branch_exists` | The branch `concorde/<task-id>` already exists. |
| `path_exists` | The worktree path already exists. |
| `unknown_module` | A named Module is not in the registry. |
| `specs_unloadable` | The Specs needed to check Module identities cannot be loaded. |
| `unknown_task` | No record has that identity. |
| `invalid_transition` | The requested change is not allowed from the task's current state. |
| `not_merged` | `--merged` was requested but the task is not delivered, the latest delivery commit is not the head of the task branch, or that head is not contained in the primary branch. |
| `dirty_worktree` | The worktree has uncommitted changes and the command is `--merged`, or `--abandoned` without `--force`. |
| `task_closed` | A run is begun for a task that is merged or abandoned. |
| `task_busy` | A run is begun while another run of the task is still running. |
| `record_conflict` | The record changed concurrently three times in a row. |
| `record_unreadable` | The task record on disk cannot be read as JSON. |
| `git_failed` | A Git command Tasks needs failed; the message names the command, its exit status and its output. |
| `unknown_run` | `escalate` names a run that is not a run of the task, or whose result cannot be read. |
| `nothing_to_escalate` | `escalate` names no run and no file, or a run that ended without an error. |
| `invalid_error` | An escalated file is not an error link, or the main agent's link does not satisfy the error contract. |
| `invalid_command` | The command line is malformed. |

## Record updates

The Operation host changes records only through these three updates. Each is one read, a check of
its preconditions and one file transaction bound to the digest of the bytes read.

| Update | Preconditions | Effect |
| --- | --- | --- |
| Begin run (`task`, `run_id`, `operation`, `modules`, `writes`, `host_pid`, `check_modules`) | The task exists, its state is `open`, `active` or `delivered`, every Module is registered in the task worktree unless `check_modules` is false (for an Operation that diagnoses the Specs itself), and no run is `running` whose `host_pid` is still alive; `running` entries whose process ended are first set to `interrupted`. Otherwise `unknown_task`, `task_closed`, `unknown_module`, `specs_unloadable` or `task_busy`, each with a message naming the task, Module, file or run concerned. | Appends the run as `running`, adds new Modules to `modules`, moves `open` to `active`, and moves `delivered` to `active` when `writes` is true. |
| Finish run (`task`, `run_id`, `status`) | The run exists and is `running`. | Sets the run's status and `finished_at`. |
| Record delivery (`task`, `run_id`, `commit`, `bundle`, `readiness_run`) | The run exists and is `running`, and the state is `active` or `delivered`. | Appends the delivery and sets the state to `delivered`. |
