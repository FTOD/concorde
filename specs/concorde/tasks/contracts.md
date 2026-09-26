# Tasks contracts

The exact record, commands and record updates of [Tasks](module.md). The obligations they serve are
in the [requirements](requirements.md).

## Task record

```concorde-contract
{
  "id": "contract.tasks.record",
  "version": 7,
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
      "sessions",
      "workflow",
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
          "closed",
          "failed"
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
      "sessions": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/session"
        }
      },
      "workflow": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "$ref": "#/$defs/workflow"
          }
        ]
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
          "outcome",
          "note",
          "errors",
          "at",
          "primary_commit",
          "worktree_removed"
        ],
        "properties": {
          "state": {
            "enum": [
              "closed",
              "failed"
            ]
          },
          "outcome": {
            "enum": [
              "merged",
              "completed",
              "failed"
            ]
          },
          "note": {
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
          "errors": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/error"
            }
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
              "task-session",
              "workflow",
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
      },
      "workflow": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "name",
          "steps",
          "reports"
        ],
        "properties": {
          "name": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9-]*$"
          },
          "steps": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "key",
                "operation",
                "run_id",
                "mode",
                "answers",
                "error",
                "superseded",
                "at"
              ],
              "properties": {
                "key": {
                  "type": "string",
                  "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
                },
                "operation": {
                  "type": "string",
                  "pattern": "^[a-z][a-z_]*$"
                },
                "run_id": {
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
                "mode": {
                  "enum": [
                    "interactive",
                    "no-ask"
                  ]
                },
                "answers": {
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
                "error": {
                  "anyOf": [
                    {
                      "type": "null"
                    },
                    {
                      "$ref": "#/$defs/error"
                    }
                  ]
                },
                "superseded": {
                  "type": "boolean"
                },
                "at": {
                  "type": "string",
                  "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
                }
              }
            }
          },
          "reports": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "status",
                "path",
                "at"
              ],
              "properties": {
                "status": {
                  "enum": [
                    "ok",
                    "awaiting_decision",
                    "blocked",
                    "failed"
                  ]
                },
                "path": {
                  "type": "string",
                  "minLength": 1
                },
                "at": {
                  "type": "string",
                  "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
                }
              }
            }
          }
        }
      },
      "claude_session": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "program",
          "id",
          "name",
          "main",
          "settings",
          "started_at"
        ],
        "properties": {
          "program": {
            "const": "claude"
          },
          "id": {
            "type": "string",
            "minLength": 1
          },
          "name": {
            "type": "string",
            "minLength": 1
          },
          "main": {
            "type": "string",
            "minLength": 1
          },
          "settings": {
            "type": "string",
            "pattern": "^/"
          },
          "started_at": {
            "type": "string",
            "minLength": 1
          }
        }
      },
      "pi_session": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "program",
          "id",
          "name",
          "main",
          "directory",
          "model",
          "started_at",
          "rounds"
        ],
        "properties": {
          "program": {
            "const": "pi"
          },
          "id": {
            "type": "string",
            "minLength": 1
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
          "directory": {
            "type": "string",
            "pattern": "^/"
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
          "started_at": {
            "type": "string",
            "minLength": 1
          },
          "rounds": {
            "type": "array",
            "minItems": 1,
            "items": {
              "$ref": "#/$defs/round"
            }
          }
        }
      },
      "round": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "round",
          "prompt",
          "status",
          "supervisor_pid",
          "started_at",
          "ended_at",
          "report",
          "error",
          "events",
          "stderr"
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
            "type": "string"
          },
          "status": {
            "enum": [
              "running",
              "delivered",
              "escalated",
              "failed",
              "stopped"
            ]
          },
          "supervisor_pid": {
            "type": "integer",
            "minimum": 1
          },
          "started_at": {
            "type": "string",
            "minLength": 1
          },
          "ended_at": {
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
          "report": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "object"
              }
            ]
          },
          "error": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "$ref": "#/$defs/error"
              }
            ]
          },
          "events": {
            "type": "string",
            "pattern": "^/"
          },
          "stderr": {
            "type": "string",
            "pattern": "^/"
          }
        }
      },
      "session": {
        "oneOf": [
          {
            "$ref": "#/$defs/claude_session"
          },
          {
            "$ref": "#/$defs/pi_session"
          }
        ]
      }
    }
  },
  "semantics": "The task record stored as .concorde/tasks/<id>.json in the primary worktree, written only by the Task store. id is chosen by the main agent and never reused; branch is concorde/<id>; worktree is the absolute path of the task's linked worktree; base_commit is the commit the branch was created from. modules starts with the Modules named at open and grows by every Module a run names; every entry was a registered Module when added. state follows open -> active -> delivered -> closed, where delivered returns to active when a run with writes true starts; a delivered task becomes closed when it is merged, and open, active and delivered may become closed when the task reached its goal without merging, or failed when it did not. runs lists every Operation run in start order: status running while the host works, then the Operation result status, or interrupted when the host process host_pid ended without finishing the run; writes tells whether the Operation may change the worktree. deliveries lists every delivery in order, with the delivery commit on the task branch, the project-relative path of the committed evidence bundle and the run that decided the delivered readiness, which is the delivery run itself. escalations lists, in order, every error chain escalated with concorde task escalate, each with its time and the escalating session's link, a contract.concorde.error link whose causes are the escalated errors: of level task-session when a task session escalated to the main agent, of level main-agent when the main agent escalated to the developer; sessions lists, in order, every task session started for the task with concorde task session: the background session identity Claude Code reported, its name task-<id>, the main agent's session it reports to, the absolute path of its settings file and its start time; $defs error, evidence and unhandled are that contract's definitions. closed is null until the task ends; it then records the final state (closed or failed), the outcome (merged or completed for closed, failed for failed), the note (null for merged unless given, what the task achieved for completed, why it failed for failed), the error chains that caused a failure exactly as their writers wrote them (empty when no error caused it, and for closed), the head of the primary branch at closing and whether the worktree was removed. workflow is null until the first workflow step of the task is recorded; then it names the workflow, lists each step with its key, Operation, run (null for a step whose run could not start, with its error), mode, answers file, whether a later rerun superseded it, and time, in the order recorded; a key's current step is its latest entry not superseded, and each report with its status, result path and time. Timestamps are RFC 3339 in UTC. sessions lists the task sessions started for the task: a claude session is one background Claude Code session with its identity, name, the main agent's session name and settings file; a pi session is a sequence of rounds on one pi session file under directory, with the main agent's session name when given and the model when --model named one. Each round has its number, whether its prompt was the task or the main agent's answer (with the answer), its status (running until the supervisor records delivered, escalated, failed or stopped), the supervisor's process, its start and end, the session report it received (null when none), the error link of a failed round (null otherwise) and the paths of pi's event stream and standard error.",
  "example": {
    "id": "severity",
    "goal": "let Issue reports carry a severity",
    "modules": [
      "module.issues"
    ],
    "branch": "concorde/severity",
    "worktree": "/home/dev/project/.claude/worktrees/severity",
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
        "readiness_run": "r-20260924T103800-delivery-77d0e4f5",
        "at": "2026-09-24T10:40:00Z"
      }
    ],
    "escalations": [],
    "sessions": [
      {
        "program": "claude",
        "id": "33afbc14",
        "name": "task-severity",
        "main": "concorde-7d",
        "settings": "/home/dev/project/.concorde/tasks/severity.session/settings.json",
        "started_at": "2026-09-24T09:00:30Z"
      }
    ],
    "workflow": null,
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
known tasks; for a dirty worktree, the uncommitted paths; for a busy merge lock, its holder), and
whose reason is `environment` for `git_failed`, `worktree_failed`, `record_conflict`,
`record_unreadable`, `merge_busy` and `rollback_failed`, `decision` for `dirty_worktree`,
`not_merged`, `primary_dirty`, `merge_conflict` and `check_failed`, and `input` otherwise. A
refusal changes nothing and exits with status 1, apart from what `merge` states below; a malformed
command line prints the same shape with the code `invalid_command` and exits with status 2.

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task open <task-id> --goal <text> --modules <id>[,<id>…] [--base <ref>] [--path <dir>]` | Holding the merge lock, creates branch `concorde/<task-id>` at `--base` (default: the primary worktree's `HEAD`), adds a worktree for it at `--path` (default: `.claude/worktrees/<task-id>` of the primary worktree, which Git must ignore there), writes the record in state `open` with no sessions, and the decision log | The new record |
| `concorde task list [--state <state>]` | None | An array of records, oldest first |
| `concorde task show <task-id>` | None | `{"record": <record>, "decision_log": "<absolute path>"}` |
| `concorde task session <task-id> …` | Starts, answers or stops a task session; see [Task session](../agents/task-session/contracts.md#commands) | As stated there |
| `concorde task merge <task-id> [--check <command>]… [--wait <seconds>]` | Holding the merge lock: checks that the task is delivered, that its latest delivery commit is the head of its branch and that its worktree is clean, and that the primary worktree is on a branch with no uncommitted or untracked path; runs `git merge --no-edit concorde/<task-id>` in the primary worktree; runs each check there, appending its output to `.concorde/tasks/<task-id>.merge.log`; then closes the task as `close --merged` does. The default check is `concorde validate` of the merged primary worktree, run by the same Python with the running package on its path; each `--check` is split into words as a shell would and run without a shell, and any `--check` replaces the default; a check still running after 1800 seconds is stopped and counts as failed. A conflict aborts the merge; a check that exits non-zero or cannot run, or checks that leave an uncommitted path, reset the primary branch to the commit the merge started from with `git reset --keep`, so a refusal again leaves the primary branch where it was. `--wait` (default 300) bounds how long to wait for the lock | `{"record": <record>, "merge": {"before": "<commit>", "after": "<commit>", "checks": [{"argv": ["<word>", …], "exit_code": 0, "seconds": <number>}], "waited_seconds": <number>, "log": "<absolute path>"}}` |
| `concorde task close <task-id> --merged [--note <text>]` | Holding the merge lock, checks the merge, removes the worktree, sets state `closed` with outcome `merged` | The updated record |
| `concorde task close <task-id> --completed --note <text> [--force]` | For a task that reached its goal without merging, holding the merge lock: removes the worktree, discarding uncommitted changes only with `--force`, sets state `closed` with outcome `completed` and the note | The updated record |
| `concorde task close <task-id> --failed --reason <text> ((--run <run-id> \| --error-file <path>)… \| --no-error) [--force]` | For a task that did not reach its goal, holding the merge lock: removes the worktree, discarding uncommitted changes only with `--force`, sets state `failed` with the reason as note and, as errors, the `error` of each named run of the task and each error read from a file, unchanged; `--no-error` declares that no error caused the failure | The updated record |
| `concorde task escalate <task-id> [--by main-agent\|task-session] (--run <run-id> \| --error-file <path> \| --escalation <n>)… --code <code> --detail <text> --reason <reason> --explanation <text> [--attempt <text>]… [--option <text>]… [--recommendation <text>]` | Builds the escalating session's link, of level `main-agent` (the default, actor `main agent (task <task-id>)`) or `task-session` (actor `task session (task <task-id>)`), whose causes are the `error` of each named run of the task, each error read from a file (a link, or a JSON value whose `error` is one) and the error of each named earlier escalation of the task (numbered from 1 in record order), appends it to the record's `escalations` and appends it to the decision log, rendered and as JSON, under a heading naming the receiver: the main agent for `task-session`, the developer for `main-agent` | `{"escalated": <link>, "number": <its number in the record, from 1>, "decision_log": "<absolute path>", "rendered": "<the chain as indented text>"}` |

The decision log that `open` creates contains exactly a level-1 heading `Decision log: <task-id>`
and a paragraph `Goal: <goal>`.

The merge lock is an exclusive `flock` on `.concorde/tasks/merge.lock` of the primary worktree. The
process running `open`, `close` or `merge` takes it before reading anything it acts on, holds it
for the whole command and releases it when it ends; the kernel releases it when the process dies,
however it dies. While holding it, the process keeps in the file one JSON object
`{"command": "<open|close|merge>", "task": "<task-id>", "pid": <pid>, "since": "<RFC 3339 time>"}`.
Only a process that failed to take the lock reads that object, so an object left by a dead holder
is overwritten by the next holder and never reported. `open` and `close` wait for the lock as long
as `merge` does by default.

`merge` refuses before merging whatever `close --merged` would refuse apart from containment, so
closing after the checks passed fails only for an environment error such as `worktree_failed`. That
refusal leaves the merge and its checked commit in place, names the merge commit and says that
`concorde task close <task-id> --merged` finishes the task.

| Error code | Raised when |
| --- | --- |
| `not_primary` | `open`, `close`, `merge` or `session` runs outside the primary worktree. |
| `worktree_not_ignored` | The worktree path lies inside the primary worktree and Git does not ignore it there; the message names the path and how to ignore it. |
| `invalid_input` | A goal or Module list is missing or repeats a Module, or `close` names not exactly one of `--merged`, `--completed` and `--failed`, `--completed` lacks `--note`, `--failed` lacks `--reason`, `--failed` names both or neither of an error source (`--run`, `--error-file`) and `--no-error`, an option belongs to another outcome, or `--force` accompanies `--merged`, or a `--check` is empty or cannot be split into words, or `--wait` is negative, or `session` combines `--answer` and `--stop`, gives `--answer` or `--stop` for a Claude Code session, or starts a Claude Code session without `--main`. |
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
| `dirty_worktree` | The worktree has uncommitted changes and the command is `--merged`, or `--completed` or `--failed` without `--force`. |
| `task_closed` | A run is begun, or a session started, for a task that is closed or failed. |
| `task_busy` | A run is begun while another run of the task is still running. |
| `record_conflict` | The record changed concurrently three times in a row. |
| `record_unreadable` | The task record on disk cannot be read as JSON. |
| `git_failed` | A Git command Tasks needs failed; the message names the command, its exit status and its output. |
| `unknown_run` | `escalate` names a run that is not a run of the task, or whose result cannot be read. |
| `unknown_escalation` | `escalate` names an escalation number the task does not have. |
| `merge_busy` | The merge lock stayed held for the whole wait; the message names the holder's command, task, process and start time. |
| `primary_dirty` | `merge` finds an uncommitted or untracked path in the primary worktree, or its `HEAD` detached; the message names the paths or the detached commit. |
| `merge_conflict` | `git merge` stopped with conflicts; the merge was aborted, and the message names the conflicting paths. |
| `check_failed` | A post-merge check exited non-zero or could not run, or the checks left uncommitted paths; the primary branch was reset to the commit before the merge, and the message names the check, its exit status, the log and the end of its output. |
| `rollback_failed` | After a conflict or a failed check, Git refused to abort the merge or reset the primary branch; the message carries the original failure, Git's output and the commit the primary branch is at, and the primary worktree is left as Git left it. |
| `nothing_to_escalate` | `escalate` names no run, file or escalation, or a run that ended without an error. |
| `invalid_error` | An escalated file or escalation is not an error link, or the escalating session's link does not satisfy the error contract. |
| `workflow_conflict` | A workflow step names a workflow other than the one the record already names. |
| `step_conflict` | A workflow step key is already recorded for another Operation. |
| `no_workflow` | A workflow report is recorded for a task whose record names no workflow. |
| `invalid_command` | The command line is malformed. |

## Record updates

The Operation host changes records only through the first three updates, Workflows only through the two workflow updates, and task sessions only through the last three. Each is one read, a check of
its preconditions and one file transaction bound to the digest of the bytes read.

| Update | Preconditions | Effect |
| --- | --- | --- |
| Begin run (`task`, `run_id`, `operation`, `modules`, `writes`, `host_pid`, `check_modules`) | The task exists, its state is `open`, `active` or `delivered`, every Module is registered in the task worktree unless `check_modules` is false (for an Operation that diagnoses the Specs itself), and no run is `running` whose `host_pid` is still alive; `running` entries whose process ended are first set to `interrupted`. Otherwise `unknown_task`, `task_closed`, `unknown_module`, `specs_unloadable` or `task_busy`, each with a message naming the task, Module, file or run concerned. | Appends the run as `running`, adds new Modules to `modules`, moves `open` to `active`, and moves `delivered` to `active` when `writes` is true. |
| Finish run (`task`, `run_id`, `status`) | The run exists and is `running`. | Sets the run's status and `finished_at`. |
| Record delivery (`task`, `run_id`, `commit`, `bundle`, `readiness_run`) | The run exists and is `running`, and the state is `active` or `delivered`. | Appends the delivery and sets the state to `delivered`. |
| Record workflow step (`task`, `workflow`, `key`, `base_key`, `operation`, `run_id`, `mode`, `answers`, `error`) | The task exists and is not `closed` or `failed`; the record names no workflow or the same one; the key is recorded for no other Operation. Otherwise `unknown_task`, `task_closed`, `workflow_conflict` or `step_conflict`, naming the recorded workflow or Operation. | Names the workflow when none was named; when a current step has the same base key, marks it and every step recorded after it superseded; appends the step. |
| Record workflow report (`task`, `status`, `path`, `log_text`) | The task exists and names a workflow. Otherwise `unknown_task` or `no_workflow`. | Appends the report and appends `log_text` to the decision log. |
| Record session (`task`, `session`) | The task is `open`, `active` or `delivered`. Otherwise `unknown_task` or `task_closed`. | Appends the session. |
| Begin round (`task`, `session_id`, `round`) | The task's session with that identity is a pi session whose rounds are all ended. Otherwise `no_session` or `session_busy`. | Appends the round as `running`. |
| Finish round (`task`, `session_id`, `round`, `status`, `report`, `error`) | The round exists and is `running`. | Sets the round's status, `ended_at`, report and error. |
