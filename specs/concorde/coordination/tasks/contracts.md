# Tasks contracts

The exact record, commands and record updates of [Tasks](module.md). The obligations they serve are
in the [requirements](requirements.md).

## Task record

```concorde-contract
{
  "id": "contract.tasks.record",
  "version": 10,
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
      "merging",
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
          "merging",
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
      "merging": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "$ref": "#/$defs/merging"
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
      "merging": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "before",
          "checked",
          "branch",
          "after",
          "checks",
          "since",
          "pid"
        ],
        "properties": {
          "before": {
            "type": "string",
            "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
          },
          "checked": {
            "type": "string",
            "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
          },
          "branch": {
            "type": "string",
            "minLength": 1
          },
          "after": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "string",
                "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
              }
            ]
          },
          "checks": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string"
              }
            }
          },
          "since": {
            "type": "string",
            "minLength": 1
          },
          "pid": {
            "type": "integer",
            "minimum": 1
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
  "semantics": "The task record stored as .concorde/tasks/<id>.json in the primary worktree, written only by the Task store. id is chosen by the main agent and never reused, and names the task's workspace: the open wrote the workspace binding (contract.execution.workspace-binding) of the worktree with id as its workspace, and the task's runs, workspace lock and delivery commits are found by that name. branch is concorde/<id>; worktree is the absolute real path of the task's linked worktree; base_commit is the commit the branch was created from. goal and modules are those named at open, each registered in the primary worktree then, and never change, whatever the task branch later does to its registry; a run leaves out a Module the task worktree does not register. The Modules a run worked on are in its run result, not here. The file stores state open until the task ends and then closed or failed, and merging while concorde task merge has, or may have, put a merge of the task into the primary branch that its checks have not decided; it keeps no runs, deliveries or workflow steps, which the run store and the task branch's delivery commits hold. merging is null unless the state is merging; it then records the primary branch's commit before the merge, the delivery commit the merge checked and merges (checked), the primary branch's name, the commit the merge produced (null until git merge has returned), the checks the merge runs, each an argument vector, its start time and the process of the merging command. concorde task open, list and show print the record with state replaced by the derived task state: merging, closed or failed as stored; otherwise delivered when the branch head is a delivery commit of the workspace and the worktree is clean, active when the workspace has a run in the run store, the branch moved past base_commit or the worktree has uncommitted changes, and open before any of these. escalations lists, in order, every error chain escalated with concorde task escalate, each with its time and the escalating session's link, a contract.concorde.error link whose causes are the escalated errors: of level task-session when a task session escalated to the main agent, of level main-agent when the main agent escalated to the developer; $defs error, evidence and unhandled are that contract's definitions. sessions lists, in order, the task sessions started for the task with concorde task session: a claude session is one background Claude Code session with the identity Claude Code reported, its name task-<id>, the main agent's session it reports to, the absolute path of its settings file and its start time; a pi session is a sequence of rounds on one pi session file under directory, with the main agent's session name when given and the model when --model named one. Each round has its number, whether its prompt was the task or the main agent's answer (with the answer), its status (running until the supervisor records delivered, escalated, failed or stopped), the supervisor's process, its start and end, the session report it received (null when none), the error link of a failed round (null otherwise) and the paths of pi's event stream and standard error. closed is null until the task ends; it then records the final state (closed or failed), the outcome (merged or completed for closed, failed for failed), the note (null for merged unless given, what the task achieved for completed, why it failed for failed), the error chains that caused a failure exactly as their writers wrote them (empty when no error caused it, and for closed), the head of the primary branch at closing and whether the worktree was removed. Timestamps are RFC 3339 in UTC. A behaviour or field change increments the version.",
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
    "merging": null,
    "closed": null
  }
}
```

## Commands

`open`, `close`, `merge` and `session` run only in the primary worktree. `list`, `show` and
`escalate` run in any worktree of the repository, so a task session escalates from its task
worktree; they find the primary worktree, and with it the records, through Git's common directory.
Every command prints one JSON value on standard output and exits with status 0 on success. A
refusal prints `{"error": <link>}`, where the link is a
[`component` link](../../contracts.md#contract.concorde.error) of the actor
`Tasks (concorde task <command>)` whose code is one of the error codes below or, for `session` and
the record updates, one of the [Task session codes](../task-session/contracts.md#commands), whose
detail names the
task, [Module](../../glossary.json#concept.module), path, run or Git command concerned with its
message (for an unknown task, the known tasks; for a dirty worktree, the uncommitted paths; for a
busy [merge lock](../../glossary.json#concept.merge-lock), its holder), and whose reason is
`environment` for `git_failed`, `worktree_failed`, `record_conflict`, `record_unreadable`,
`config_copy_failed`, `binding_failed`, `merge_busy`, `workspace_busy`, `rollback_failed` and the
session codes `session_failed` and `missing_worktree`, `decision` for `dirty_worktree`,
`not_merged`, `primary_dirty`, `merge_conflict`, `check_failed`, `merge_incomplete`,
`not_resumable`, `merge_diverged` and `session_busy`, and `input` otherwise. A
refusal exits with status 1 and changes nothing, apart from the refusals that
[req.tasks.refusal-inert](requirements.md#req.tasks.refusal-inert) names, each of which says what
it left behind: `open`'s `config_copy_failed` and `binding_failed`, and `merge`'s
`rollback_failed`, a `check_failed` whose checks created paths, and a close that failed after the
merge (below). A malformed command line prints the same shape with the code `invalid_command` and
exits with status 2.

While a task is stored as `merging` and no live process holds the merge lock, `open`, `merge`,
`close`, `session` and `escalate` refuse with `merge_incomplete` before they change anything:
`open`, `merge` and `close` once they hold the merge lock, `session` and `escalate` once they found
it free. Exempt are `merge --resume` and `merge --abort` of the merging task and
`session --stop`. While a live process holds the merge lock and a task is `merging`, `session` and
`escalate` of that task refuse with `merge_busy` at once, and those of other tasks are not refused
for it. `list` and `show` are never refused for a merge.

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task open <task-id> --goal <text> --modules <id>[,<id>…] [--base <ref>] [--path <dir>]` | Holding the merge lock, creates branch `concorde/<task-id>` at `--base` (default: the primary worktree's `HEAD`), adds a worktree for it at `--path` (default: `.claude/worktrees/<task-id>` of the primary worktree, which Git must ignore there), copies the primary worktree's [worker model configuration](../../glossary.json#concept.worker-model-configuration) into it when there is one, writes the worktree's [workspace binding](../../execution/contracts.md#contract.execution.workspace-binding) (workspace `<task-id>`, the worktree's real path as root, the branch, base commit, goal and Modules, and the primary worktree's `.concorde` as records directory), then the record in state `open` with no sessions, and the [decision log](../../glossary.json#concept.decision-log) | `{"record": <the new record>, "decision_log": "<absolute path>"}` |
| `concorde task list [--state <state>]` | None; `--state` filters on the derived state | An array of records with their derived state, oldest first |
| `concorde task show <task-id>` | None | `{"record": <record with its derived state>, "runs": [{"run_id": "<id>", "kind": "operation\|command", "name": "<Operation or command>", "modules": ["<id>", …], "status": "running\|lost\|ok\|blocked\|failed", "started_at": "<time>", "finished_at": "<time>\|null"}, …], "deliveries": [{"commit": "<commit>", "bundle": "<project-relative path>", "readiness_run": "<run id>"}, …], "busy": "<holder of the workspace lock>\|null", "decision_log": "<absolute path>"}` |
| `concorde task session <task-id> …` | Starts, answers or stops a [task session](../../glossary.json#concept.task-session); see [Task session](../task-session/contracts.md#commands) | As stated there |
| `concorde task merge <task-id> [--check <command>]… [--wait <seconds>]` | Waiting up to `--wait` seconds (default 300) for the task's [workspace lock](../../glossary.json#concept.workspace-lock) and then, with the rest of that time, for the merge lock, and holding both: checks that the task branch holds a [delivery commit](../../glossary.json#concept.delivery-commit) of the task's workspace, read from Git, that the latest one is the head of its branch and that its worktree is clean, and that the primary worktree is on a branch with no uncommitted or untracked path; stores the task as `merging` with the primary branch's name and commit, that head as the checked commit and the checks; runs `git merge --no-edit -m "Merge branch 'concorde/<task-id>' at <checked commit>" <checked commit>` in the primary worktree and records the resulting commit as `merging.after`; runs each check there, appending its output to `.concorde/tasks/<task-id>.merge.log`; then closes the task as `close --merged` does, clearing `merging`. The default check is `concorde spec-validation` of the merged primary worktree, run by the same Python with the running package on its path; each `--check` is split into words as a shell would and run without a shell, and any `--check` replaces the default; a check still running after 1800 seconds is stopped and counts as failed. A conflict aborts the merge; a check that exits non-zero or cannot run, or checks that leave an uncommitted path, reset the primary branch to the commit the merge started from with `git reset --keep`, so a refusal again leaves the primary branch where it was; the reset leaves the paths the checks created in the primary worktree, and the refusal names them. After a conflict or a reset the task is stored `open` again, with `merging` null. `--wait` (default 300) bounds how long to wait for both locks together; `waited_seconds` is how long it waited | `{"record": <record>, "merge": {"before": "<commit>", "after": "<commit>", "checks": [{"argv": ["<word>", …], "exit_code": 0, "seconds": <number>}], "waited_seconds": <number>, "log": "<absolute path>"}, "warnings": ["<text>", …]}`; `warnings` names the decision log when it is missing or holds exactly what `open` wrote, read before the close appends to it, and is empty otherwise |
| `concorde task merge <task-id> --resume [--wait <seconds>]` | For a `merging` task, holding both locks as a merge does: when the primary worktree is clean on the recorded branch and its head is the recorded merge commit (or, with none recorded, a merge commit whose parents are exactly the commit before and the checked commit, or the checked commit itself when the merge fast-forwarded), reruns the recorded checks there, appending to the merge log, then closes the task or resets the primary branch exactly as `merge` does after its checks | As `merge` |
| `concorde task merge <task-id> --abort [--wait <seconds>]` | For a `merging` task, holding both locks as a merge does: runs `git merge --abort` when a merge is in progress; when the primary worktree is on the recorded branch, resets it with `git reset --keep` to the commit before the merge if its head is the merge commit, leaves it if its head already is that commit, and stores the task `open` with `merging` null | `{"record": <record with its derived state>, "abort": {"before": "<commit>", "undone": "<merge commit reset away>\|null", "left": ["<path the reset left in the primary worktree>", …], "waited_seconds": <number>}}` |
| `concorde task close <task-id> --merged [--note <text>] [--wait <seconds>]` | Waiting up to `--wait` seconds (default 300) for the task's workspace lock and then for the merge lock, and holding both, checks the merge, removes the worktree, sets state `closed` with outcome `merged` and appends the outcome and any note to the decision log | The updated record |
| `concorde task close <task-id> --completed --note <text> [--force] [--wait <seconds>]` | For a task that reached its goal without merging, holding the workspace lock and then the merge lock, waited for as with `--merged`: removes the worktree, discarding uncommitted changes only with `--force`, sets state `closed` with outcome `completed` and the note, and appends the outcome and the note to the decision log | The updated record |
| `concorde task close <task-id> --failed --reason <text> ((--run <run-id> \| --error-file <path>)… \| --no-error) [--force] [--wait <seconds>]` | For a task that did not reach its goal, holding the workspace lock and then the merge lock, waited for as with `--merged`: removes the worktree, discarding uncommitted changes only with `--force`, sets state `failed` with the reason as note and, as errors, the `error` of each named run of the task's workspace, read from the [run store](../../glossary.json#concept.run-store), and each error read from a file, unchanged; `--no-error` declares that no error caused the failure; appends the outcome, the reason and the errors, rendered and as JSON, to the decision log | The updated record |
| `concorde task escalate <task-id> [--by main-agent\|task-session] (--run <run-id> \| --error-file <path> \| --escalation <n>)… --code <code> --detail <text> --reason <reason> --explanation <text> [--attempt <text>]… [--option <text>]… [--recommendation <text>]` | Builds the escalating session's link, of level `main-agent` (the default, actor `main agent (task <task-id>)`) or `task-session` (actor `task session (task <task-id>)`), whose causes are the `error` of each named run of the task's workspace, read from the run store, each error read from a file (a link, or a JSON value whose `error` is one) and the error of each named earlier escalation of the task (numbered from 1 in record order), appends it to the record's `escalations` and appends it to the decision log, rendered and as JSON, under a heading naming the receiver: the [main agent](../../glossary.json#concept.main-agent) for `task-session`, the developer for `main-agent` | `{"escalated": <link>, "number": <its number in the record, from 1>, "decision_log": "<absolute path>", "rendered": "<the chain as indented text>"}` |

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
closing after the checks passed fails only for an environment error such as `worktree_failed`, or
with `not_merged` or `dirty_worktree` when the task branch or worktree was changed by hand during
the merge. That refusal leaves the merge and its checked commit in place and the task `merging`,
names the merge commit and says that `concorde task merge <task-id> --resume` finishes the task
once the cause is fixed. A `rollback_failed` also leaves the task `merging`, and says that
`--abort` restores the primary branch.

The task's workspace lock is Execution's lock of the workspace named after the task
(`contract.execution.workspace-binding`); `merge` and `close` take it after the merge lock without
waiting and name themselves in it as `` `concorde task <command>` of task <task-id> ``.

| Error code | Raised when |
| --- | --- |
| `not_primary` | `open`, `close`, `merge` or `session` runs outside the primary worktree. |
| `worktree_not_ignored` | The worktree path lies inside the primary worktree and Git does not ignore it there; the message names the path and how to ignore it. |
| `invalid_input` | A goal or Module list is missing or repeats a Module, or `close` names not exactly one of `--merged`, `--completed` and `--failed`, `--completed` lacks `--note`, `--failed` lacks `--reason`, `--failed` names both or neither of an error source (`--run`, `--error-file`) and `--no-error`, an option belongs to another outcome, or `--force` accompanies `--merged`, or a `--check` is empty or cannot be split into words, or `--check` accompanies `--resume` or `--abort`, or `--wait` is negative, or `session` combines two of `--answer`, `--stop` and `--wait`, gives `--wait` a negative value, gives `--answer`, `--stop` or `--wait` for a Claude Code session or together with `--main`, `--model` or `--dry-run`, or starts a Claude Code session without `--main`. |
| `worktree_failed` | Git refused to add or remove the worktree; the message carries Git's error. |
| `config_copy_failed` | `open` added the worktree but the file system refused the copy of the worker model configuration; the message names the worktree and branch left behind and how to remove them. |
| `binding_failed` | `open` added the worktree but could not write its [workspace binding](../../glossary.json#concept.workspace-binding); the message names the file, the worktree and branch left behind and how to remove them. |
| `invalid_task_id` | The identity does not match the record's `id` pattern. |
| `task_exists` | A record with that identity exists, whatever its state. |
| `branch_exists` | The branch `concorde/<task-id>` already exists. |
| `path_exists` | The worktree path already exists. |
| `unknown_module` | A named Module is not in the registry. |
| `specs_unloadable` | The Specs needed to check Module identities cannot be loaded. |
| `unknown_task` | No record has that identity. |
| `invalid_transition` | `close` or `merge` names a task that is already `closed` or `failed`, or a merge would store `merging` for a task whose stored state is not `open`. |
| `not_merged` | `close --merged` or `merge` finds that the task branch holds no delivery commit of the task's workspace since the base commit or that its latest delivery commit is not the head of the branch, or `close --merged` finds that head not contained in the primary branch. |
| `dirty_worktree` | The worktree has uncommitted changes and the command is `--merged`, or `--completed` or `--failed` without `--force`. |
| `task_closed` | A session is started or recorded for a task that is closed or failed. |
| `record_conflict` | The record changed concurrently three times in a row. |
| `record_unreadable` | The [task record](../../glossary.json#concept.task-record) on disk cannot be read as JSON. |
| `git_failed` | A Git command Tasks needs failed; the message names the command, its exit status and its output. |
| `unknown_run` | `escalate` or `close --failed` names a run whose result cannot be read from the run store, or a run of another workspace or of none; the message names the workspace the run belongs to. |
| `unknown_escalation` | `escalate` names an escalation number the task does not have. |
| `merge_busy` | The merge lock stayed held for the whole wait, or `session` or `escalate` names the task a live merge is merging; the message names the holder's command, task, process and start time. |
| `workspace_busy` | `merge` or `close` found the task's workspace lock still held by a run after waiting `--wait` seconds; the message names the holder, the lock file and how long it waited. |
| `merge_incomplete` | A task is stored `merging` and no live process holds the merge lock; the message names the task, the process and time that began its merge, the checked commit, the primary branch with the commit before the merge and where its head is now, whether that is the merge commit, and the `--resume` and `--abort` commands. |
| `not_merging` | `merge --resume` or `--abort` names a task that is not `merging`; the message names its state. |
| `not_resumable` | `merge --resume` finds that the primary branch's head is not the merge commit; the message names the head and whether it is the commit before the merge, and that `--abort` is the way out. |
| `merge_diverged` | `merge --resume` or `--abort` finds the primary worktree on another branch or detached, or (`--abort`) its head neither the commit before the merge nor the merge commit; the message names the commits and says to restore the branch by hand. |
| `primary_dirty` | `merge` finds an uncommitted or untracked path in the primary worktree, or its `HEAD` detached; the message names the paths or the detached commit. |
| `merge_conflict` | `git merge` stopped with conflicts; the merge was aborted, and the message names the conflicting paths. |
| `check_failed` | A post-merge check, of a merge or of `--resume`, exited non-zero or could not run, or the checks left uncommitted paths; the primary branch was reset to the commit before the merge and the task is delivered again, and the message names the failing check, its exit status, the log and the end of its output, or the paths the checks left and the log, and any paths the checks created, which stay in the primary worktree. |
| `rollback_failed` | After a conflict or a failed check, or during `--abort`, Git refused to abort the merge or reset the primary branch; the message carries the original failure, Git's output and the commit the primary branch is at, the primary worktree is left as Git left it, and the task stays `merging`. |
| `nothing_to_escalate` | `escalate` names no run, file or escalation, or `escalate` or `close --failed` names a run that ended without an error. |
| `invalid_error` | An escalated file or escalation is not an error link, or the escalating session's link does not satisfy the error contract. |
| `invalid_command` | The command line is malformed. |

## Record updates

Nothing below the task level updates a record: runs, deliveries and workflows are recorded by
Execution, and Tasks reads them. Besides `open`, `merge`, `close` and `escalate`, a record changes
only through the three updates task sessions make; these are not refused for an unfinished merge,
so a running round's outcome is always recorded. Each is one read, a check of its preconditions and one
[file transaction](../../glossary.json#concept.file-transaction) bound to the digest of the bytes
read. Their refusals use the codes above and the
[Task session codes](../task-session/contracts.md#commands) `no_session`, `session_busy` and
`session_idle`.

| Update | Preconditions | Effect |
| --- | --- | --- |
| Record session (`task`, `session`) | The task is neither `closed` nor `failed`. Otherwise `unknown_task` or `task_closed`. | Appends the session. |
| Begin round (`task`, `session_id`, `round`) | The task's session with that identity is a pi session whose rounds are all ended. Otherwise `no_session` or `session_busy`. | Appends the round as `running`. |
| Finish round (`task`, `session_id`, `round`, `status`, `report`, `error`) | The task's session with that identity is a pi session whose round with that number is `running`. Otherwise `no_session` or `session_idle`. | Sets the round's status, `ended_at`, report and error. |
