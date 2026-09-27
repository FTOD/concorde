# Tasks contracts

The exact record, commands and record updates of [Tasks](module.md). The obligations they serve are
in the [requirements](requirements.md).

## Task record

```concorde-contract
{
  "id": "contract.tasks.record",
  "version": 9,
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
      "escalations",
      "sessions",
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
              "command",
              "workers",
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
  "semantics": "The task record stored as .concorde/tasks/<id>.json in the primary worktree, written only by the Task store. id is chosen by the main agent and never reused, and names the task's workspace: the open wrote the workspace binding (contract.execution.workspace-binding) of the worktree with id as its workspace, and the task's runs, workspace lock and delivery commits are found by that name. branch is concorde/<id>; worktree is the absolute real path of the task's linked worktree; base_commit is the commit the branch was created from. goal and modules are those named at open and never change; every Module was registered at open, so an entry the task worktree's registry no longer registers was removed or renamed on the task branch. The Modules a run worked on are in its run result, not here. The file stores state open until the task ends and then closed or failed; it keeps no runs, deliveries or workflow steps, which the run store and the task branch's delivery commits hold. concorde task open, list and show print the record with state replaced by the derived task state: closed or failed as stored; otherwise delivered when the branch head is a delivery commit of the workspace and the worktree is clean, active when the workspace has a run in the run store, the branch moved past base_commit or the worktree has uncommitted changes, and open before any of these. escalations lists, in order, every error chain escalated with concorde task escalate, each with its time and the escalating session's link, a contract.concorde.error link whose causes are the escalated errors: of level task-session when a task session escalated to the main agent, of level main-agent when the main agent escalated to the developer; $defs error, evidence and unhandled are that contract's definitions. sessions lists, in order, the task sessions started for the task with concorde task session: a claude session is one background Claude Code session with the identity Claude Code reported, its name task-<id>, the main agent's session it reports to, the absolute path of its settings file and its start time; a pi session is a sequence of rounds on one pi session file under directory, with the main agent's session name when given and the model when --model named one. Each round has its number, whether its prompt was the task or the main agent's answer (with the answer), its status (running until the supervisor records delivered, escalated, failed or stopped), the supervisor's process, its start and end, the session report it received (null when none), the error link of a failed round (null otherwise) and the paths of pi's event stream and standard error. closed is null until the task ends; it then records the final state (closed or failed), the outcome (merged or completed for closed, failed for failed), the note (null for merged unless given, what the task achieved for completed, why it failed for failed), the error chains that caused a failure exactly as their writers wrote them (empty when no error caused it, and for closed), the head of the primary branch at closing and whether the worktree was removed. Timestamps are RFC 3339 in UTC. A behaviour or field change increments the version.",
  "example": {
    "id": "severity",
    "goal": "let Issue reports carry a severity",
    "modules": [
      "module.issues"
    ],
    "branch": "concorde/severity",
    "worktree": "/home/dev/project/.claude/worktrees/severity",
    "base_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "state": "open",
    "created_at": "2026-09-24T09:00:00Z",
    "updated_at": "2026-09-24T09:00:30Z",
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
    "closed": null
  }
}
```

## Commands

Every command runs in the primary worktree, prints one JSON value on standard output and exits
with status 0 on success. A refusal prints `{"error": <link>}`, where the link is a
[`component` link](../../contracts.md#contract.concorde.error) of the actor
`Tasks (concorde task <command>)` whose code is one of the error codes below, whose detail names
the task, Module, path, run or Git command concerned with its message (for an unknown task, the
known tasks; for a dirty worktree, the uncommitted paths; for a busy merge lock, its holder), and
whose reason is `environment` for `git_failed`, `worktree_failed`, `record_conflict`,
`record_unreadable`, `config_copy_failed`, `merge_busy`, `rollback_failed` and the session codes
`session_failed` and `missing_worktree`, `decision` for `dirty_worktree`, `not_merged`,
`primary_dirty`, `merge_conflict`, `check_failed` and `session_busy`, and `input` otherwise. A
refusal changes nothing and exits with status 1, apart from what `merge` states below; a malformed
command line prints the same shape with the code `invalid_command` and exits with status 2.

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task open <task-id> --goal <text> --modules <id>[,<id>…] [--base <ref>] [--path <dir>]` | Holding the merge lock, creates branch `concorde/<task-id>` at `--base` (default: the primary worktree's `HEAD`), adds a worktree for it at `--path` (default: `.claude/worktrees/<task-id>` of the primary worktree, which Git must ignore there), copies the primary worktree's worker model configuration into it when there is one, writes the worktree's [workspace binding](../../execution/contracts.md#contract.execution.workspace-binding) (workspace `<task-id>`, the worktree's real path as root, the branch, base commit, goal and Modules, and the primary worktree's `.concorde` as records directory), then the record in state `open` with no sessions, and the decision log | The new record |
| `concorde task list [--state <state>]` | None; `--state` filters on the derived state | An array of records with their derived state, oldest first |
| `concorde task show <task-id>` | None | `{"record": <record with its derived state>, "runs": [{"run_id": "<id>", "kind": "operation\|command", "name": "<Operation or command>", "modules": ["<id>", …], "status": "running\|lost\|ok\|blocked\|failed", "started_at": "<time>", "finished_at": "<time>\|null"}, …], "deliveries": [{"commit": "<commit>", "bundle": "<project-relative path>", "readiness_run": "<run id>"}, …], "busy": "<holder of the workspace lock>\|null", "decision_log": "<absolute path>"}` |
| `concorde task session <task-id> …` | Starts, answers or stops a task session; see [Task session](../task-session/contracts.md#commands) | As stated there |
| `concorde task merge <task-id> [--check <command>]… [--wait <seconds>]` | Holding the merge lock: checks that the task branch holds a delivery commit of the task's workspace, read from Git, that the latest one is the head of its branch and that its worktree is clean, and that the primary worktree is on a branch with no uncommitted or untracked path; runs `git merge --no-edit concorde/<task-id>` in the primary worktree; runs each check there, appending its output to `.concorde/tasks/<task-id>.merge.log`; then closes the task as `close --merged` does. The default check is `concorde spec-validation` of the merged primary worktree, run by the same Python with the running package on its path; each `--check` is split into words as a shell would and run without a shell, and any `--check` replaces the default; a check still running after 1800 seconds is stopped and counts as failed. A conflict aborts the merge; a check that exits non-zero or cannot run, or checks that leave an uncommitted path, reset the primary branch to the commit the merge started from with `git reset --keep`, so a refusal again leaves the primary branch where it was. `--wait` (default 300) bounds how long to wait for the lock | `{"record": <record>, "merge": {"before": "<commit>", "after": "<commit>", "checks": [{"argv": ["<word>", …], "exit_code": 0, "seconds": <number>}], "waited_seconds": <number>, "log": "<absolute path>"}}` |
| `concorde task close <task-id> --merged [--note <text>]` | Holding the merge lock, checks the merge, removes the worktree, sets state `closed` with outcome `merged` | The updated record |
| `concorde task close <task-id> --completed --note <text> [--force]` | For a task that reached its goal without merging, holding the merge lock: removes the worktree, discarding uncommitted changes only with `--force`, sets state `closed` with outcome `completed` and the note | The updated record |
| `concorde task close <task-id> --failed --reason <text> ((--run <run-id> \| --error-file <path>)… \| --no-error) [--force]` | For a task that did not reach its goal, holding the merge lock: removes the worktree, discarding uncommitted changes only with `--force`, sets state `failed` with the reason as note and, as errors, the `error` of each named run of the task's workspace, read from the run store, and each error read from a file, unchanged; `--no-error` declares that no error caused the failure | The updated record |
| `concorde task escalate <task-id> [--by main-agent\|task-session] (--run <run-id> \| --error-file <path> \| --escalation <n>)… --code <code> --detail <text> --reason <reason> --explanation <text> [--attempt <text>]… [--option <text>]… [--recommendation <text>]` | Builds the escalating session's link, of level `main-agent` (the default, actor `main agent (task <task-id>)`) or `task-session` (actor `task session (task <task-id>)`), whose causes are the `error` of each named run of the task's workspace, read from the run store, each error read from a file (a link, or a JSON value whose `error` is one) and the error of each named earlier escalation of the task (numbered from 1 in record order), appends it to the record's `escalations` and appends it to the decision log, rendered and as JSON, under a heading naming the receiver: the main agent for `task-session`, the developer for `main-agent` | `{"escalated": <link>, "number": <its number in the record, from 1>, "decision_log": "<absolute path>", "rendered": "<the chain as indented text>"}` |

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
| `config_copy_failed` | `open` added the worktree but the file system refused the copy of the worker model configuration; the message names the worktree and branch left behind and how to remove them. |
| `binding_failed` | `open` added the worktree but could not write its workspace binding; the message names the file, the worktree and branch left behind and how to remove them. |
| `invalid_task_id` | The identity does not match the record's `id` pattern. |
| `task_exists` | A record with that identity exists, whatever its state. |
| `branch_exists` | The branch `concorde/<task-id>` already exists. |
| `path_exists` | The worktree path already exists. |
| `unknown_module` | A named Module is not in the registry. |
| `specs_unloadable` | The Specs needed to check Module identities cannot be loaded. |
| `unknown_task` | No record has that identity. |
| `invalid_transition` | The requested change is not allowed from the task's current state. |
| `not_merged` | `--merged` or `merge` was requested but the task branch holds no delivery commit of the task's workspace since the base commit, its latest delivery commit is not the head of the branch, or that head is not contained in the primary branch. |
| `dirty_worktree` | The worktree has uncommitted changes and the command is `--merged`, or `--completed` or `--failed` without `--force`. |
| `task_closed` | A session is started or recorded for a task that is closed or failed. |
| `record_conflict` | The record changed concurrently three times in a row. |
| `record_unreadable` | The task record on disk cannot be read as JSON. |
| `git_failed` | A Git command Tasks needs failed; the message names the command, its exit status and its output. |
| `unknown_run` | `escalate` or `close --failed` names a run whose result cannot be read from the run store, or a run of another workspace or of none; the message names the workspace the run belongs to. |
| `unknown_escalation` | `escalate` names an escalation number the task does not have. |
| `merge_busy` | The merge lock stayed held for the whole wait; the message names the holder's command, task, process and start time. |
| `primary_dirty` | `merge` finds an uncommitted or untracked path in the primary worktree, or its `HEAD` detached; the message names the paths or the detached commit. |
| `merge_conflict` | `git merge` stopped with conflicts; the merge was aborted, and the message names the conflicting paths. |
| `check_failed` | A post-merge check exited non-zero or could not run, or the checks left uncommitted paths; the primary branch was reset to the commit before the merge, and the message names the check, its exit status, the log and the end of its output. |
| `rollback_failed` | After a conflict or a failed check, Git refused to abort the merge or reset the primary branch; the message carries the original failure, Git's output and the commit the primary branch is at, and the primary worktree is left as Git left it. |
| `nothing_to_escalate` | `escalate` names no run, file or escalation, or a run that ended without an error. |
| `invalid_error` | An escalated file or escalation is not an error link, or the escalating session's link does not satisfy the error contract. |
| `invalid_command` | The command line is malformed. |

## Record updates

Nothing below the task level updates a record: runs, deliveries and workflows are recorded by
Execution, and Tasks reads them. Besides `open`, `close` and `escalate`, a record changes only
through the three updates task sessions make. Each is one read, a check of its preconditions and
one file transaction bound to the digest of the bytes read.

| Update | Preconditions | Effect |
| --- | --- | --- |
| Record session (`task`, `session`) | The task is neither `closed` nor `failed`. Otherwise `unknown_task` or `task_closed`. | Appends the session. |
| Begin round (`task`, `session_id`, `round`) | The task's session with that identity is a pi session whose rounds are all ended. Otherwise `no_session` or `session_busy`. | Appends the round as `running`. |
| Finish round (`task`, `session_id`, `round`, `status`, `report`, `error`) | The round exists and is `running`. | Sets the round's status, `ended_at`, report and error. |
