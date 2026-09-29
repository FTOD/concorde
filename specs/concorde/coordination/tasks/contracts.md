# Tasks contracts

The exact record, trace, commands and record updates of [Tasks](module.md). The obligations they serve are
in the [requirements](requirements.md).

## Task record

```concorde-contract
{
  "id": "contract.tasks.record",
  "version": 12,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "id",
      "goal",
      "modules",
      "branch",
      "worktree",
      "base_commit",
      "state",
      "created_at",
      "updated_at",
      "merging",
      "closed"
    ],
    "properties": {
      "schema_version": {
        "const": 2
      },
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
          "worktree_removed",
          "history"
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
          },
          "history": {
            "type": "string",
            "pattern": "^[a-z0-9][a-z0-9-]{0,47}(\\.[0-9]+)?$"
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
      }
    }
  },
  "semantics": "The task record task.json in the task's folder .concorde/tasks/<id>/ of the primary worktree, written only by the Task store while it holds the task's lock; closing the task moves it, with the whole folder, to .concorde/history/<history>/. It holds only what the task commands need to act on the task; the task's history, its state changes, escalations, task sessions, rounds and merge attempts, is its trace (contract.tasks.task-trace and the nodes below the task's node). schema_version is 2. id is chosen by the main agent and names the task's workspace: the open wrote the workspace binding (contract.execution.workspace-binding) of the worktree with id as its workspace and the task folder's workspace/ as its workspace folder, and the task's workspace lock and delivery commits are found by that name. branch is concorde/<id>; worktree is the absolute real path of the task's linked worktree; base_commit is the commit the branch was created from. goal and modules are those named at open, each registered in the primary worktree then, and never change, whatever the task branch later does to its registry; a run leaves out a Module the task worktree does not register. The Modules a run worked on are in its run result, not here. The file stores state open until the task ends and then closed or failed, and merging while concorde task merge has, or may have, put a merge of the task into the primary branch that its checks have not decided; it keeps no runs, deliveries or workflow steps, which the workspace folder and the task branch's delivery commits hold. merging is null unless the state is merging; it then records the primary branch's commit before the merge, the delivery commit the merge checked and merges (checked), the primary branch's name, the commit the merge produced (null until git merge has returned), the checks the merge runs, each an argument vector, its start time and the process of the merging command. concorde task open, list and show print the record with state replaced by the derived task state: merging, closed or failed as stored; otherwise delivered when the branch head is a delivery commit of the workspace that verifies against its evidence bundle, as Delivery defines (contract.delivery.evidence-bundle), and the worktree is clean, active when the workspace has a run in its workspace folder, the branch moved past base_commit or the worktree has uncommitted changes, and open before any of these. closed is null until the task ends; it then records the final state (closed or failed), the outcome (merged or completed for closed, failed for failed), the note (null for merged unless given, what the task achieved for completed, why it failed for failed), the error chains that caused a failure exactly as their writers wrote them (empty when no error caused it, and for closed), the head of the primary branch at closing, whether the worktree was removed and the history key the folder moved to. Timestamps are RFC 3339 in UTC. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 2,
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
    "merging": null,
    "closed": null
  }
}
```

## Task trace

A task is a [trace node](../../glossary.json#concept.trace-node) of kind `task`, and each of its merge attempts one of kind
`merge` with its checks as `merge-check` nodes below it, as
[Tracing](../../tracing/contracts.md#contract.tracing.node) defines them; their contents are these values. The nodes of its task
sessions and their rounds are [Task sessions](../task-session/contracts.md#session-trace)'.

```concorde-contract
{
  "id": "contract.tasks.task-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "goal",
      "worktree",
      "transitions",
      "escalations",
      "closing"
    ],
    "properties": {
      "goal": {
        "type": "string",
        "minLength": 1
      },
      "worktree": {
        "type": "string",
        "minLength": 1
      },
      "transitions": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "state",
            "at"
          ],
          "properties": {
            "state": {
              "enum": [
                "open",
                "merging",
                "closed",
                "failed"
              ]
            },
            "at": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "escalations": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "number",
            "at",
            "by",
            "error"
          ],
          "properties": {
            "number": {
              "type": "integer",
              "minimum": 1
            },
            "at": {
              "type": "string",
              "minLength": 1
            },
            "by": {
              "enum": [
                "main-agent",
                "task-session"
              ]
            },
            "error": {
              "type": "object"
            }
          }
        }
      },
      "closing": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "outcome",
              "note",
              "errors",
              "primary_commit",
              "worktree_removed",
              "history"
            ],
            "properties": {
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
                  "type": "object"
                }
              },
              "primary_commit": {
                "type": "string",
                "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
              },
              "worktree_removed": {
                "type": "boolean"
              },
              "history": {
                "type": "string",
                "minLength": 1
              }
            }
          }
        ]
      }
    }
  },
  "semantics": "The data of the typed value concorde-task-trace, the content of a task's trace node, trace.json in the task's folder. goal is the task's goal and worktree the absolute path its worktree had. transitions lists every change of the task's stored state with its time, from open at the open. escalations lists, numbered from 1 in the order recorded, every error chain escalated with concorde task escalate: its time, whether the main agent or a task session escalated it, and the escalating session's link (contract.tracing.error) with the escalated errors as its causes. closing is null until the task ends; it then holds the outcome, the note, the error chains that caused a failure, the primary branch's head at closing, whether the worktree was removed and the history key. The node's identity is the task name, its start the open, its status running until the close ends it ok (merged or completed) or failed, with the outcome as outcome and, for a failure, the first error chain that caused it as error; its metadata are the task, its Modules, branch and base commit, the Concorde commit and the Protocol version. Its children are the sessions under sessions/, the merge attempts under merges/ and the workspace folder workspace/. A behaviour or field change increments the version.",
  "example": {
    "goal": "let Issue reports carry a severity",
    "worktree": "/home/dev/shop/.claude/worktrees/severity",
    "transitions": [
      {
        "state": "open",
        "at": "2026-09-24T09:00:00Z"
      },
      {
        "state": "merging",
        "at": "2026-09-24T11:00:00Z"
      },
      {
        "state": "closed",
        "at": "2026-09-24T11:01:10Z"
      }
    ],
    "escalations": [],
    "closing": {
      "outcome": "merged",
      "note": null,
      "errors": [],
      "primary_commit": "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432",
      "worktree_removed": true,
      "history": "severity"
    }
  }
}
```

```concorde-contract
{
  "id": "contract.tasks.merge-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "attempt",
      "branch",
      "before",
      "checked",
      "after",
      "checks",
      "waited_seconds"
    ],
    "properties": {
      "attempt": {
        "enum": [
          "merge",
          "resume",
          "abort"
        ]
      },
      "branch": {
        "type": "string",
        "minLength": 1
      },
      "before": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "checked": {
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
        "items": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "waited_seconds": {
        "type": "number",
        "minimum": 0
      }
    }
  },
  "semantics": "The data of the typed value concorde-merge-trace, the content of one merge attempt's trace node merges/<n>/ of a task, n counting the task's attempts from 1: a concorde task merge, or its --resume or --abort. branch is the primary branch, before its commit before the merge, checked the delivery commit merged, after the merge commit once git merge returned (null before and when no merge was made), checks the argument vectors of the checks the attempt runs and waited_seconds how long it waited for its locks. The node's status is ok when the attempt closed the task as merged or, for --abort, restored the primary branch, and failed otherwise, with its outcome merged, conflict, check_failed, rolled_back, rollback_failed, aborted or interrupted and the refusal's link as error; its metadata are the task, the branch and, once made, the merge commit as commit. Each check it ran is a merge-check node checks/<i>/ below it. A behaviour or field change increments the version.",
  "example": {
    "attempt": "merge",
    "branch": "main",
    "before": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "checked": "4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
    "after": "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432",
    "checks": [
      [
        "concorde",
        "spec-validation"
      ]
    ],
    "waited_seconds": 0.4
  }
}
```

```concorde-contract
{
  "id": "contract.tasks.merge-check-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "argv",
      "exit_code"
    ],
    "properties": {
      "argv": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "exit_code": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "integer"
          }
        ]
      }
    }
  },
  "semantics": "The data of the typed value concorde-merge-check-trace, the content of one check a merge attempt ran, checks/<i>/ of the attempt's node, i counting from 1 in the order run. argv is the command as run and exit_code its exit status, null when it could not run or was stopped after 1800 seconds. The node's status is ok for exit status 0 and failed otherwise, its usage the check's duration, and output.log, the check's standard output and error, its artifact. A behaviour or field change increments the version.",
  "example": {
    "argv": [
      "concorde",
      "spec-validation"
    ],
    "exit_code": 0
  }
}
```

## Commands

`open`, `close`, `merge` and `session` run only in the primary worktree. `list`, `show` and
`escalate` run in any worktree of the repository, so a task session escalates from its task
worktree; they find the primary worktree, and with it the task folders, through Git's common
directory.
Every command prints one JSON value on standard output and exits with status 0 on success. A
refusal prints `{"error": <link>}`, where the link is a
[`component` link](../../tracing/contracts.md#contract.tracing.error) of the actor
`Tasks (concorde task <command>)` whose code is one of the error codes below or, for `session` and
the record updates, one of the [Task session codes](../task-session/contracts.md#commands), whose
detail names the
task, [Module](../../glossary.json#concept.module), path, run or Git command concerned with its
message (for an unknown task, the known tasks; for a dirty worktree, the uncommitted paths; for a
busy [merge lock](../../glossary.json#concept.merge-lock), its holder), and whose reason is
`environment` for `git_failed`, `worktree_failed`, `record_conflict`, `record_unreadable`,
`record_unwritable`, `decision_log_failed`, `binding_failed`, `merge_busy`, `workspace_busy`, `rollback_failed` and the
session codes `session_failed` and `missing_worktree`, `decision` for `dirty_worktree`,
`not_merged`, `primary_dirty`, `merge_conflict`, `check_failed`, `merge_incomplete`,
`not_resumable`, `merge_diverged` and `session_busy`, and `input` otherwise. A
refusal exits with status 1 and changes nothing, apart from the refusals that
[req.tasks.refusal-inert](requirements.md#req.tasks.refusal-inert) names, each of which says what
it left behind: `open`'s `binding_failed`, and `merge`'s
`rollback_failed`, a `check_failed` whose checks created paths, and a close that failed after the
merge, and the refusals of `close` and `escalate` after a step they could not undo (below). A malformed command line prints the same shape with the code `invalid_command` and
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
| `concorde task open <task-id> --goal <text> --modules <id>[,<id>…] [--base <ref>] [--path <dir>]` | Holding the merge lock, creates branch `concorde/<task-id>` at `--base` (default: the primary worktree's `HEAD`), adds a worktree for it at `--path` (default: `.claude/worktrees/<task-id>` of the primary worktree, which Git must ignore there), first runs Tracing's retention, then creates the task's folder `.concorde/tasks/<task-id>/` with its `workspace/`, writes the worktree's [workspace binding](../../execution/contracts.md#contract.execution.workspace-binding) (workspace `<task-id>`, the worktree's real path as root, the branch, base commit, goal and Modules, the task folder's `workspace/` as workspace folder and the primary worktree's `.concorde`), then the record `task.json` in state `open`, the task's trace node `trace.json` and the [decision log](../../glossary.json#concept.decision-log) `decisions.md` | `{"record": <the new record>, "decision_log": "<absolute path>"}` |
| `concorde task list [--state <state>]` | None; lists the current tasks and those in the history; `--state` filters on the derived state | An array of records with their derived state, oldest first |
| `concorde task show <task-id>` | None; each delivery's `mismatches` lists how it disagrees with its [evidence bundle](../../glossary.json#concept.evidence-bundle) by Delivery's check, and is empty when it verifies | `{"record": <record with its derived state>, "runs": [{"run_id": "<id>", "kind": "operation\|command", "name": "<Operation or command>", "modules": ["<id>", …], "status": "running\|lost\|ok\|blocked\|failed", "started_at": "<time>", "finished_at": "<time>\|null"}, …], "deliveries": [{"commit": "<commit>", "bundle": "<project-relative path>", "readiness_run": "<run id>", "mismatches": ["<how the commit disagrees with its evidence bundle>", …]}, …], "sessions": [<each session node's content with its identity, status and times, a pi session with its rounds>, …], "escalations": [<the task trace's escalations>], "busy": "<holder of the workspace lock>\|null", "decision_log": "<absolute path>", "folder": "<absolute path of the task's folder, current or in the history>"}`; a task in the history is shown the same way, with `busy` null |
| `concorde task session <task-id> …` | Starts, answers or stops a [task session](../../glossary.json#concept.task-session); see [Task session](../task-session/contracts.md#commands) | As stated there |
| `concorde task merge <task-id> [--check <command>]… [--wait <seconds>]` | Waiting up to `--wait` seconds (default 300) for the task's [workspace lock](../../glossary.json#concept.workspace-lock) and then, with the rest of that time, for the merge lock, and holding both: checks that the task branch holds a [delivery commit](../../glossary.json#concept.delivery-commit) of the task's workspace, read from Git, that the latest one is the head of its branch and verifies against its [evidence bundle](../../glossary.json#concept.evidence-bundle), and that its worktree is clean, and that the primary worktree is on a branch with no uncommitted or untracked path; stores the task as `merging` with the primary branch's name and commit, that head as the checked commit and the checks; runs `git merge --no-edit -m "Merge branch 'concorde/<task-id>' at <checked commit>" <checked commit>` in the primary worktree and records the resulting commit as `merging.after`; runs each check there, keeping its output as `output.log` of the check's node below the attempt's node `merges/<n>/`; then closes the task as `close --merged` does, clearing `merging`. The default check is `concorde spec-validation` of the merged primary worktree, run by the same Python with the running package on its path; each `--check` is split into words as a shell would and run without a shell, and any `--check` replaces the default; a check still running after 1800 seconds is stopped and counts as failed. A conflict aborts the merge; a check that exits non-zero or cannot run, or checks that leave an uncommitted path, reset the primary branch to the commit the merge started from with `git reset --keep`, so a refusal again leaves the primary branch where it was; the reset leaves the paths the checks created in the primary worktree, and the refusal names them. After a conflict or a reset the task is stored `open` again, with `merging` null. `--wait` (default 300) bounds how long to wait for both locks together; `waited_seconds` is how long it waited | `{"record": <record>, "merge": {"before": "<commit>", "after": "<commit>", "checks": [{"argv": ["<word>", …], "exit_code": 0, "seconds": <number>}], "waited_seconds": <number>, "log": "<absolute path of the attempt's node>"}, "warnings": ["<text>", …]}`; `warnings` names the decision log when it is missing or holds exactly what `open` wrote, read before the close appends to it, and is empty otherwise |
| `concorde task merge <task-id> --resume [--wait <seconds>]` | For a `merging` task, holding both locks as a merge does: when the primary worktree is clean on the recorded branch and its head is the recorded merge commit (or, with none recorded, a merge commit whose parents are exactly the commit before and the checked commit, or the checked commit itself when the merge fast-forwarded), reruns the recorded checks there, as a new attempt's node, then closes the task or resets the primary branch exactly as `merge` does after its checks | As `merge` |
| `concorde task merge <task-id> --abort [--wait <seconds>]` | For a `merging` task, holding both locks as a merge does: runs `git merge --abort` when a merge is in progress; when the primary worktree is on the recorded branch, resets it with `git reset --keep` to the commit before the merge if its head is the merge commit, leaves it if its head already is that commit, and stores the task `open` with `merging` null | `{"record": <record with its derived state>, "abort": {"before": "<commit>", "undone": "<merge commit reset away>\|null", "left": ["<path the reset left in the primary worktree>", …], "waited_seconds": <number>}}` |
| `concorde task close <task-id> --merged [--note <text>] [--wait <seconds>]` | First runs Tracing's retention; waiting up to `--wait` seconds (default 300) for the task's workspace lock and then for the merge lock, and holding both, checks the merge, removes the worktree, sets state `closed` with outcome `merged`, ends the task's trace node, appends the outcome and any note to the decision log, then moves the task's folder to `.concorde/history/<history key>/` and removes the task's task, workspace and workflow locks | The updated record |
| `concorde task close <task-id> --completed --note <text> [--force] [--wait <seconds>]` | For a task that reached its goal without merging: first stops, with `SIGTERM`, each run of the task's workspace whose [run lock](../../glossary.json#concept.run-lock) a process of this machine holds, and a running round of the task's pi task session as `--stop` does; then, holding the workspace lock and then the merge lock, waited for as with `--merged`: removes the worktree, discarding uncommitted changes only with `--force`, sets state `closed` with outcome `completed` and the note, ends the trace node, appends the outcome and the note to the decision log and moves the folder to the history as with `--merged` | The updated record |
| `concorde task close <task-id> --failed --reason <text> ((--run <run-id> \| --error-file <path>)… \| --no-error) [--force] [--wait <seconds>]` | For a task that did not reach its goal: stops its runs and round as `--completed` does, then, holding the workspace lock and then the merge lock, waited for as with `--merged`: removes the worktree, discarding uncommitted changes only with `--force`, sets state `failed` with the reason as note and, as errors, the `error` of each named run of the task's workspace, read from its workspace folder, and each error read from a file, unchanged; `--no-error` declares that no error caused the failure; ends the trace node, appends the outcome, the reason and the errors, rendered and as JSON, to the decision log and moves the folder to the history | The updated record |
| `concorde task escalate <task-id> [--by main-agent\|task-session] [--run <run-id> \| --error-file <path> \| --escalation <n>]… --code <code> --detail <text> --reason <reason> --explanation <text> [--attempt <text>]… [--option <text>]… [--recommendation <text>]` | Builds the escalating session's link, of level `main-agent` (the default, actor `main agent (task <task-id>)`) or `task-session` (actor `task session (task <task-id>)`), whose causes are the `error` of each named run of the task's workspace, read from the [run store](../../glossary.json#concept.run-store), each error read from a file (a link, or a JSON value whose `error` is one) and the error of each named earlier escalation of the task (numbered from 1 in record order), with no causes when it names none (a decision to escalate that no error carries), appends it to the escalations of the task's trace node and to the decision log, rendered and as JSON, under a heading naming the receiver: the [main agent](../../glossary.json#concept.main-agent) for `task-session`, the developer for `main-agent` | `{"escalated": <link>, "number": <its number in the task's trace, from 1>, "decision_log": "<absolute path>", "rendered": "<the chain as indented text>"}` |

The decision log that `open` creates contains exactly a level-1 heading `Decision log: <task-id>`
and a paragraph `Goal: <goal>`.

The merge lock is an exclusive `flock` on `.concorde/locks/merge.lock` of the primary worktree. The
process running `open`, `close` or `merge` takes it before reading anything it acts on, holds it
for the whole command and releases it when it ends; the kernel releases it when the process dies,
however it dies. While holding it, the process keeps in the file one JSON object
`{"holder": "`concorde task <open|close|merge>` of task <task-id>", "pid": <pid>, "since": "<RFC 3339 time>"}`, the holder line of every lock under `.concorde/locks/`.
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

`close` runs its steps in order, `git submodule deinit --all` in a worktree with submodules,
`git worktree remove`, the record update, the end of the trace node, the append to the decision log
and the move of the task's folder to the history, and a refusal after a step leaves what the steps
before it did. A `worktree_failed` from the deinit or the removal
says that the submodules Git deinitialized stay so and that `git submodule update --init` in the
worktree restores them; a `record_conflict`, `record_unwritable` or `unknown_task` of the record
update after the worktree was removed names the removed worktree and says the task keeps its
state without it; a `decision_log_failed` names the task's stored state, outcome and time. Each
says that running the same close again, with the same options, finishes it once the cause is
fixed, and, when the close is a merge's, the `merge` refusal says that
`concorde task merge <task-id> --resume` does, unless it is `decision_log_failed`, after which the
task is closed as merged and the same `close --merged` finishes it. The rerun skips a worktree that
no longer exists, and records `worktree_removed` false then; run on a task already stored `closed`
or `failed` with the outcome it names, whose decision log holds no line
`## Closed: <outcome>, <closed.at>`, it appends the closing the record holds, as the close that
stored it would have, and returns the record unchanged.

`escalate` writes the record before it appends to the decision log. When the append fails, it
refuses with `decision_log_failed`, naming the escalation's number in the record, the decision
log, the file system's error and the heading the entry would have had, carrying the rendered
chain and saying that escalating again would record it twice, so the chain is appended by hand.

The task's workspace lock is Execution's lock of the workspace named after the task,
`.concorde/locks/workspaces/<task-id>.lock` (`contract.execution.workspace-binding`); `merge` and
`close` take it before the merge lock and name themselves in it as
`` `concorde task <command>` of task <task-id> ``. The task's lock, `.concorde/locks/tasks/<task-id>.lock`,
is held by every change of the task's record and trace, so that two processes never change a task
at once; the close that moves the task removes the task, workspace and workflow locks while it
holds the first two.

| Error code | Raised when |
| --- | --- |
| `not_primary` | `open`, `close`, `merge` or `session` runs outside the primary worktree. |
| `worktree_not_ignored` | The worktree path lies inside the primary worktree and Git does not ignore it there; the message names the path and how to ignore it. |
| `invalid_input` | A goal or Module list is missing or repeats a Module, or `close` names not exactly one of `--merged`, `--completed` and `--failed`, `--completed` lacks `--note`, `--failed` lacks `--reason`, `--failed` names both or neither of an error source (`--run`, `--error-file`) and `--no-error`, an option belongs to another outcome, or `--force` accompanies `--merged`, or a `--check` is empty or cannot be split into words, or `--check` accompanies `--resume` or `--abort`, or `--wait` is negative, or `session` combines two of `--answer`, `--stop` and `--wait`, gives `--wait` a negative value, gives `--answer`, `--stop` or `--wait` for a Claude Code session or together with `--main`, `--model` or `--dry-run`, or starts a Claude Code session without `--main`. |
| `worktree_failed` | Git refused to add or remove the worktree; the message carries Git's error. |
| `binding_failed` | `open` added the worktree but could not write its [workspace binding](../../glossary.json#concept.workspace-binding); the message names the file, the worktree and branch left behind and how to remove them. |
| `invalid_task_id` | The identity does not match the record's `id` pattern. |
| `task_exists` | A current task with that identity exists, whatever its state. |
| `branch_exists` | The branch `concorde/<task-id>` already exists. |
| `path_exists` | The worktree path already exists. |
| `unknown_module` | A named Module is not in the registry. |
| `specs_unloadable` | The Specs needed to check Module identities cannot be loaded. |
| `unknown_task` | No current task has that identity, nor, for `list` and `show`, the history. |
| `invalid_transition` | `close` or `merge` names a task that is already `closed` or `failed`, apart from the same close of a task whose decision log lacks its closing (above), or a merge would store `merging` for a task whose stored state is not `open`. |
| `not_merged` | `close --merged` or `merge` finds that the task branch holds no delivery commit of the task's workspace since the base commit or that its latest delivery commit is not the head of the branch, or `close --merged` finds that head not contained in the primary branch. |
| `delivery_unverified` | `close --merged` or `merge` finds that the branch head, the latest delivery commit of the task's workspace, does not verify against its evidence bundle: it has not exactly one parent equal to the bundle's `parent_commit`, does not add the bundle its `Concorde-Evidence` trailer names, or the bundle's readiness run is not its `Concorde-Readiness` trailer; the message names the head, the bundle and each mismatch. |
| `dirty_worktree` | The worktree has uncommitted changes and the command is `--merged`, or `--completed` or `--failed` without `--force`. |
| `task_closed` | A session is started or recorded, or a round of a pi task session begun, for a task that is closed or failed. |
| `record_conflict` | The record changed concurrently three times in a row. |
| `record_unreadable` | The [task record](../../glossary.json#concept.task-record) on disk cannot be read as JSON. |
| `record_unwritable` | The file system refused to write the task record; the message names the record and the file system's error. |
| `decision_log_failed` | `close` or `escalate` wrote the task record and the file system then refused the append to the [decision log](../../glossary.json#concept.decision-log), or a rerun of a close cannot read it; the message says what was written and how to finish (above). |
| `git_failed` | A Git command Tasks needs failed; the message names the command, its exit status and its output. |
| `unknown_run` | `escalate` or `close --failed` names a run whose result cannot be read from the run store, or a run of another workspace or of none; the message names the workspace the run belongs to. |
| `unknown_escalation` | `escalate` names an escalation number the task's trace does not have. |
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
| `nothing_to_escalate` | `escalate` or `close --failed` names a run that ended without an error. |
| `invalid_error` | An escalated file or escalation is not an error link, or the escalating session's link does not satisfy the error contract. |
| `invalid_command` | The command line is malformed. |

## Record updates

Nothing below the task level updates a task: runs, deliveries and workflows are recorded by
Execution, and Tasks reads them. Besides `open`, `merge`, `close` and `escalate`, a task changes
only through the three updates task sessions make, each of which writes trace nodes below the
task's node; these are not refused for an unfinished merge, so a running round's outcome is always
recorded. Each holds the task's lock while it reads, checks its preconditions and writes, so every
precondition holds for what it writes. Their refusals use the codes above and the
[Task session codes](../task-session/contracts.md#commands) `no_session`, `session_busy` and
`session_idle`.

| Update | Preconditions | Effect |
| --- | --- | --- |
| Record session (`task`, `session`) | The task is a current task neither `closed` nor `failed`. Otherwise `unknown_task` or `task_closed`. | Writes the session's node `sessions/<session id>/`. |
| Begin round (`task`, `session_id`, `round`) | The task is a current task neither `closed` nor `failed`, and its session with that identity is a pi session whose rounds are all ended. Otherwise `unknown_task`, `task_closed`, `no_session` or `session_busy`. | Writes the round's node `rounds/<n>/` of the session's node, `running`. |
| Finish round (`task`, `session_id`, `round`, `status`, `report`, `error`) | The task's session with that identity is a pi session whose round with that number is `running`, whatever the task's stored state. Otherwise `unknown_task`, `no_session` or `session_idle`. | Ends the round's node with its status, report and error. |
