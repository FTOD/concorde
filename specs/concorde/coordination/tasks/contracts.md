# Tasks contracts

The exact details of [Tasks](module.md) covered here are:

- The record.
- The trace.
- The commands.
- The record updates.

The obligations they serve are in the [requirements](requirements.md).

## Task record

```concorde-contract
{
  "id": "contract.tasks.record",
  "version": 17,
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
      "main",
      "mains",
      "reports",
      "resolves",
      "state",
      "created_at",
      "updated_at",
      "merging",
      "closed"
    ],
    "properties": {
      "schema_version": {
        "const": 5
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
      "mains": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "main",
            "at"
          ],
          "properties": {
            "main": {
              "type": "string",
              "minLength": 1
            },
            "at": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "reports": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/report"
        }
      },
      "resolves": {
        "type": "array",
        "uniqueItems": true,
        "items": {
          "type": "string",
          "pattern": "^I-[0-9a-f]{32}$"
        }
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
      "report": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "number",
          "at",
          "main",
          "text",
          "escalations",
          "answer"
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
          "text": {
            "type": "string",
            "minLength": 1
          },
          "escalations": {
            "type": "array",
            "items": {
              "type": "integer",
              "minimum": 1
            }
          },
          "answer": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "at",
                  "text",
                  "by"
                ],
                "properties": {
                  "at": {
                    "type": "string",
                    "minLength": 1
                  },
                  "text": {
                    "type": "string",
                    "minLength": 1
                  },
                  "by": {
                    "enum": [
                      "main-agent",
                      "merge",
                      "close"
                    ]
                  }
                }
              }
            ]
          }
        }
      },
      "merging": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "before",
          "checked",
          "branch",
          "after",
          "history",
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
          "history": {
            "type": "string",
            "minLength": 1
          },
          "checks": {
            "type": "array",
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
  "semantics": "The task record task.json in the task's folder .concorde/tasks/<id>/ of the primary worktree, written only by the Task store while it holds the task's lock; closing the task moves it, with the whole folder, to .concorde/history/<history>/. It holds only what the task commands need to act on the task; the task's history, its state changes, escalations, task sessions and merge attempts, is its trace (contract.tasks.task-trace and the nodes below the task's node). schema_version is 5; a record of schema_version 2, written before main, mains and reports existed, is read as version 5 whose mains are the distinct mains its task sessions' nodes name, in the order they started, each at its session's start, whose main is the last of them, or null without one, and whose reports are none, a record of schema_version 3, written before an answer said who gave it, is read as one whose every answer is by main-agent, and a record of schema_version 4 or earlier, written before resolves existed, resolves no Issue; each is written as version 5 by its next change. id is chosen by the main agent and names the task's workspace: the open wrote the workspace binding (contract.kernel.workspace-binding) of the worktree with id as its workspace and the task folder's workspace/ as its workspace folder, and the task's workspace lock and delivery commits are found by that name. branch is concorde/<id>; worktree is the absolute real path of the task's linked worktree; base_commit is the commit the branch was created from. main is the main agent's session the task's task sessions report to now: null at the open, set by concorde task session --main when it records a session and changed by concorde task rebind, never by anything else; concorde task report prints it as the session to message. mains lists every main agent's session named for the task, in order, each with the time it was named: the first a session start named, then each different one a later session start or concorde task rebind named; main is the last. reports lists, numbered from 1 in the order recorded, every report a task session recorded with concorde task report before messaging the main agent: its time, the main the record named then, to which the session sends it, the text, the numbers of the task's escalations it carries and its answer, null until it is answered and never replaced: by main-agent when concorde task answer records the main agent's answer with its time and text, or, for a report still unanswered when the task ends, by merge when concorde task merge closes the task and by close when concorde task close does, dated with the closing and saying how the task ended; a report whose answer is null is unanswered. The reports are kept here, beside the main they were sent to, because whether each is answered is what the task commands act on. resolves lists, in the order named, the open Issues of the project the task fixes, named by concorde task open --resolves and added by concorde task resolve, each an open Issue when named; once concorde task merge has merged the task and its checks passed, it closes each that is still open as resolved with the merge commit as evidence, and never changes this list. goal and modules are those named at open, each registered in the primary worktree then where the spec part is installed and a plain label otherwise, and never change, whatever the task branch later does to its registry; a run leaves out a Module the task worktree does not register. The Modules a run worked on are in its run result, not here. The file stores state open until the task ends and then closed or failed, and merging while concorde task merge has, or may have, put a merge of the task into the primary branch that its checks have not decided; it keeps no runs, deliveries or workflow steps, which the workspace folder and the task branch's delivery commits hold. merging is null unless the state is merging; it then records the primary branch's commit before the merge, the delivery commit the merge checked and merges (checked), the primary branch's name, the commit the merge produced (null until the merge commit exists), the history key the task will close under, which names the decision log .concorde/decisions/<history>.md the merge commit adds, the checks the merge runs, each an argument vector, empty for a merge that runs none, its start time, which also dates the task's closing, and the process of the merging command. concorde task open, list and show print the record with state replaced by the derived task state: merging, closed or failed as stored; otherwise delivered when the branch head is a delivery commit of the workspace that verifies, having exactly one parent as the Kernel's delivery commit convention defines, and the worktree is clean, active when the workspace has a run in its workspace folder, the branch moved past base_commit or the worktree has uncommitted changes, and open before any of these. closed is null until the task ends; it then records the final state (closed or failed), the outcome (merged or completed for closed, failed for failed), the note (null for merged unless given, what the task achieved for completed, why it failed for failed), the error chains that caused a failure exactly as their writers wrote them (empty when no error caused it, and for closed), the time of the closing (for a task that concorde task merge closes, the start time its merging recorded, which the closing its merge commit's copy of the decision log holds already names), the head of the primary branch at closing, whether the worktree was removed and the history key the folder moved to, which also names the decision log .concorde/decisions/<history>.md committed on the primary branch. Timestamps are RFC 3339 in UTC. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 5,
    "id": "severity",
    "goal": "let Issue reports carry a severity",
    "modules": [
      "module.issues"
    ],
    "branch": "concorde/severity",
    "worktree": "/home/dev/project/.claude/worktrees/severity",
    "base_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "main": "concorde-8e",
    "mains": [
      {
        "main": "concorde-7d",
        "at": "2026-09-24T09:00:20Z"
      },
      {
        "main": "concorde-8e",
        "at": "2026-09-24T11:40:00Z"
      }
    ],
    "reports": [
      {
        "number": 1,
        "at": "2026-09-24T11:30:00Z",
        "main": "concorde-7d",
        "text": "Delivered at 4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9; my decisions are in the decision log.",
        "escalations": [],
        "answer": {
          "at": "2026-09-24T11:45:00Z",
          "text": "Merging it now.",
          "by": "main-agent"
        }
      }
    ],
    "resolves": [
      "I-0123456789abcdef0123456789abcdef"
    ],
    "state": "open",
    "created_at": "2026-09-24T09:00:00Z",
    "updated_at": "2026-09-24T11:45:00Z",
    "merging": null,
    "closed": null
  }
}
```

## Task trace

The task trace contains these nodes:

- A task is a [trace node](../../glossary.json#concept.trace-node) of kind `task`.
- Each of the task's merge attempts is a node of kind `merge`. Its checks are `merge-check` nodes
  below the merge attempt's node.
- Each `task deliver` attempt is a node of kind `delivery`. Its checks are `delivery-check` nodes
  below the delivery attempt's node.

Tasks registers these kinds with Tracing, as
[Tracing](../../kernel/tracing/contracts.md#contract.tracing.node) defines them. Their contents are
these values. The nodes of the task's task sessions are
[Task sessions](../task-session/contracts.md#session-trace)'.

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
  "semantics": "The data of the typed value concorde-merge-trace, the content of one merge attempt's trace node merges/<n>/ of a task, n counting the task's attempts from 1: a concorde task merge, or its --resume or --abort. branch is the primary branch, before its commit before the merge (for an attempt refused before it began, the branch and commit it found), checked the delivery commit merged, after the merge commit once git merge returned (null before and when no merge was made), checks the argument vectors of the checks the attempt runs and waited_seconds how long it waited for its locks. The node's status is ok when the attempt closed the task as merged or, for --abort, restored the primary branch, and failed otherwise, with its outcome merged, contained (closed as merged with the checked commit already in the primary branch, after then being before), conflict, check_failed, rolled_back, rollback_failed, git_failed, aborted, interrupted or, for any other refusal, refused and the refusal's link as error; its metadata are the task, the branch and, once made, the merge commit as commit. Each check it ran is a merge-check node checks/<i>/ below it. A behaviour or field change increments the version.",
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

Each `concorde task deliver` attempt is a node `deliveries/<n>/` of the task, of kind `delivery`.
Each of the attempt's checks is a node `checks/<i>/` below the attempt's node, of kind
`delivery-check`:

```concorde-contract
{
  "id": "contract.tasks.delivery-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "branch",
      "before",
      "commit",
      "recovered",
      "checks",
      "waited_seconds"
    ],
    "properties": {
      "branch": {
        "type": "string",
        "minLength": 1
      },
      "before": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "commit": {
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
      "recovered": {
        "type": "boolean"
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
  "semantics": "The data of the typed value concorde-delivery-trace, the content of one concorde task deliver attempt's trace node deliveries/<n>/ of a task, n counting the task's attempts from 1, numbered while the attempt holds the task's workspace lock. branch is the task branch, before the head of the task worktree when the attempt began, commit the delivery commit it made or found at that head (null until then, and for an attempt refused before it), recovered true when it found the head already a delivery commit of the workspace that verifies, with a clean worktree, and committed nothing, checks the argument vectors of the --check commands it was given and waited_seconds how long it waited for the workspace lock. The node's status is ok when the attempt made or found a delivery commit, with its outcome delivered or recovered, the commit as metadata commit and among its references as commit or found_commit, and failed otherwise, with its outcome check_failed, git_failed or, for any other refusal, refused and the refusal's link as error; its metadata are the task, the branch and, once known, the commit. Each check it ran is a delivery-check node checks/<i>/ below it. A behaviour or field change increments the version.",
  "example": {
    "branch": "concorde/severity",
    "before": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "commit": "4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
    "recovered": false,
    "checks": [
      [
        "npm",
        "test"
      ]
    ],
    "waited_seconds": 0.0
  }
}
```

```concorde-contract
{
  "id": "contract.tasks.delivery-check-trace",
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
  "semantics": "The data of the typed value concorde-delivery-check-trace, the content of one check a concorde task deliver attempt ran in the task worktree, checks/<i>/ of the attempt's node, i counting from 1 in the order run. argv is the command as run and exit_code its exit status, null when it could not run or was stopped after 1800 seconds. The node's status is ok for exit status 0 and failed otherwise, its usage the check's duration, and output.log, the check's standard output and error, its artifact. A behaviour or field change increments the version.",
  "example": {
    "argv": [
      "npm",
      "test"
    ],
    "exit_code": 0
  }
}
```

## Commands

These commands run only in the primary worktree:

- `open`
- `close`
- `merge`
- `session`
- `rebind`
- `answer`

`deliver` runs only in the worktree of the task it names. These commands run in any worktree of the
repository, so a task session escalates and reports from its task worktree:

- `list`
- `show`
- `escalate`
- `report`
- `resolve`
- `wait`

Through Git's common directory, these commands find the primary worktree and, with it, the task
folders. Every command prints one JSON value on standard output. On success, every command exits
with status 0.

A refusal prints `{"error": <link>}`. The link is a
[`component` link](../../kernel/tracing/contracts.md#contract.tracing.error) of the actor
`Tasks (concorde task <command>)`. Its code is one of the error codes below. For `session` and the
record updates, its code may instead be one of the
[Task session codes](../task-session/contracts.md#commands). With its message, the detail names the
concerned item:

- The task.
- The [Module](../../glossary.json#concept.module).
- The path.
- The run.
- The Git command.

For an unknown task, the detail names the known tasks. For a dirty worktree, the detail names the
uncommitted paths. For a busy [merge lock](../../glossary.json#concept.merge-lock), the detail names
its holder. The reason is `environment` for these codes:

- `git_failed`
- `worktree_failed`
- `record_conflict`
- `record_unreadable`
- `record_unwritable`
- `decision_log_failed`
- `decision_log_uncommitted`
- `binding_failed`
- `merge_busy`
- `marker_unwritable`
- `workspace_busy`
- `rollback_failed`
- `wait_timeout`
- `wait_failed`
- `part_unknown`
- `issues_unavailable`
- The session codes `session_failed` and `missing_worktree`.

The reason is `decision` for these codes:

- `dirty_worktree`
- `not_merged`
- `delivery_unverified`
- `primary_dirty`
- `changed_outside`
- `merge_conflict`
- `check_failed`
- `merge_incomplete`
- `not_resumable`
- `merge_diverged`
- The session code `session_running`.

Otherwise, the reason is `input`. A refusal exits with status 1. Apart from the refusals that
[req.tasks.refusal-inert](requirements.md#req.tasks.refusal-inert) names, a refusal changes nothing.
Each exception says what it left behind:

- `open`'s `binding_failed`.
- `merge`'s `rollback_failed`.
- `merge`'s `check_failed` whose checks created paths.
- `merge`'s close that failed after the merge.
- The refusals of `close` and `escalate` after a step they could not undo (below).

A malformed command line prints the same shape with the code `invalid_command` and exits with status
2.

While a task is stored as `merging` and no live process holds the merge lock, these commands refuse
before they change anything:

- `open`
- `merge`
- `close`
- `session`
- `escalate`
- `resolve`

The refusal code is `merge_incomplete`. The commands refuse at these points:

- Once the command holds the merge lock, `open` refuses.
- Once the command holds the merge lock, `merge` refuses.
- Once the command holds the merge lock, `close` refuses.
- Once the command found the merge lock free, `session` refuses.
- Once the command found the merge lock free, `escalate` refuses.
- Once the command found the merge lock free, `resolve` refuses.

Exempt are `merge --resume` and `merge --abort` of the merging task. While a live process holds the
merge lock and a task is `merging`, these commands of that task refuse at once:

- `session`
- `escalate`
- `resolve`

The refusal code is `merge_busy`. Those commands of other tasks are not refused for that merge.
These commands are never refused for a merge:

- `list`
- `show`
- `rebind`
- `report`
- `answer`
- `wait`

They change at most a task's record, never Git. A report or a rebind is how a refusal such as
`merge_incomplete` reaches the main agent that must finish the merge.

<a id="parts-not-depended-on"></a>

**The parts Tasks does not depend on.** Tasks reaches every part but the Kernel only through these
interfaces:

- That part's `concorde` command, JSON in and out.
- A file format its [Spec](../../glossary.json#concept.spec) defines.

Tasks never reaches those parts through their code
([Coordination](../module.md#optional-integrations)). Tasks learns from those parts whether each
part is installed. For a worktree, the spec part is installed exactly when its registry mirror
`.concorde/specs.json` exists. For the Modules it admits, `open` reads that mirror.

The worktree's own `concorde` command is the first available of these:

- Its `.concorde/bin/concorde`.
- Else the checkout's `scripts/concorde.py`.
- Else the running package.

The execution, method and issues parts are installed exactly when that command offers their
respective commands:

- `run`
- `delivery`
- `issues`

The command offers each part's commands unless, asked for one, it refuses it as a command of a part
the project has not installed. As [Distribution](../../distribution/module.md#the-command-line)
does, that refusal prints `{"error": <link>}` whose code is `part_missing` and exits with status 1.
Any other answer, including a refusal of the arguments, means the command is offered.

`deliver` and `wait --run` ask with `concorde <command> --help`, which changes nothing.
`--resolves` and `resolve` read each Issue with
`concorde issues show <issue> --root <primary worktree>`. A merge puts back what Issue writes
left with `concorde issues recover --root <primary worktree>`. A merge closes each resolved Issue
with `concorde issues close <issue> --reason resolved --note <note> --evidence <item>… --root
<primary worktree>`. As
[Tracing](../../kernel/tracing/contracts.md#handing-a-lock-on) describes, the merge hands the merge
lock it holds on to each of these commands. The merge reads each command's answer or its
`{"error": <link>}`. Execution's runs are read through these interfaces:

- Its [run result](../../execution/contracts.md#contract.execution.run-result).
- Its [run progress file](../../glossary.json#concept.run-progress-file).
- Its [run store](../../glossary.json#concept.run-store)'s folders.
- Its [run lock](../../glossary.json#concept.run-lock).

Distribution's update mark is read through its file `.concorde/update.json`.

| Command | Effect | Output |
| --- | --- | --- |
| `concorde task open <task-id> --goal <text> --modules <id>[,<id>…] [--resolves <issue>[,<issue>…]] [--base <ref>]` | Holding the merge lock, refuses with `invalid_issue` a `--resolves` naming anything but distinct open Issues of the project, or with `part_missing` any `--resolves` where the issues part is not installed, and, where the spec part is installed, with `unknown_module` a Module the primary worktree's registry lacks, then creates branch `concorde/<task-id>` at `--base` (default: the primary worktree's `HEAD`), adds a worktree for it at `.claude/worktrees/<task-id>` of the primary worktree, which Git must ignore there, first runs Tracing's retention, then creates the task's folder `.concorde/tasks/<task-id>/` with its `workspace/`, writes the worktree's [workspace binding](../../kernel/contracts.md#contract.kernel.workspace-binding) (workspace `<task-id>`, the worktree's real path as root, the branch, base commit, goal and Modules, the task folder's `workspace/` as workspace folder and the primary worktree's `.concorde`), then the record `task.json` in state `open`, whose `resolves` lists the `--resolves` Issues, the task's trace node `trace.json` and the [decision log](../../glossary.json#concept.decision-log) `decisions.md` | `{"record": <the new record>, "decision_log": "<absolute path>"}` |
| `concorde task list [--state <state>[,<state>…]] [--main <session>]` | None; lists the current tasks and those in the history; `--state` keeps the tasks whose derived state is one of the named states, each one of `open`, `active`, `delivered`, `merging`, `closed` and `failed`, and `--main` those whose record names that main agent's session, both when both are given, so `--main <session> --state open,active,delivered,merging` lists the tasks not ended that still name that session | An array of records with their derived state, oldest first |
| `concorde task show <task-id>` | None; each delivery's `mismatches` lists how it fails Delivery's check, and is empty when it verifies | `{"record": <record with its derived state>, "runs": [{"run_id": "<id>", "kind": "operation\|command", "name": "<Operation or command>", "modules": ["<id>", …], "status": "running\|lost\|ok\|blocked\|failed", "started_at": "<time>", "finished_at": "<time>\|null"}, …], "deliveries": [{"commit": "<commit>", "mismatches": ["<how the commit fails to verify>", …]}, …], "sessions": [{"id": "<session id>", "name": "task-<task-id>", "main": "<main agent's session>\|null", "model": "<model>\|null", "reported_id": "<id Claude Code reported>\|null", "started_at": "<time>", "directory": "<absolute path of the session's trace node>"}, …], "escalations": [<the task trace's escalations>], "busy": "<holder of the workspace lock>\|null", "decision_log": "<absolute path>", "folder": "<absolute path of the task's folder, current or in the history>"}`; a task in the history is shown the same way, with `busy` null |
| `concorde task resolve <task-id> <issue>…` | Refused with `part_missing` where the issues part is not installed. For a current task that has not ended (`task_closed` otherwise) and is not being merged (`merge_busy`, `merge_incomplete`): refuses with `invalid_issue` unless every named [Issue](../../glossary.json#concept.issue) is an open Issue of the project, read from the primary worktree, and named once, then appends those not listed yet to the record's `resolves` | The updated record |
| `concorde task session <task-id> …` | Starts a [task session](../../glossary.json#concept.task-session) and names its `--main` as the task's main; see [Task session](../task-session/contracts.md#commands) | As stated there |
| `concorde task rebind <task-id> --main <session>` | For a task that has not ended (`task_closed` otherwise): stores `<session>` as the record's `main` and, when it differs from the former one, appends it with the time to the record's `mains`; run by the [main agent](../../glossary.json#concept.main-agent) once its own session name changed, such as after a resume | `{"record": <the updated record>, "former": "<the former main>"\|null}` |
| `concorde task merge <task-id> [--check <command>]… [--wait <seconds>]` | Waiting up to `--wait` seconds (default 300) for the task's merge attempt lock `locks/attempts/<task-id>.lock`, which it holds until it has written its answer and then removes, then, with the rest of that time, for the task's [workspace lock](../../glossary.json#concept.workspace-lock) and for the merge lock, and holding all three: checks that the task branch holds a [delivery commit](../../glossary.json#concept.delivery-commit) of the task's workspace, read from Git, that the latest one is the head of its branch and verifies, and that its worktree is clean, and that the primary worktree is on a branch with no uncommitted or untracked path; stores the task as `merging` with the primary branch's name and commit, that head as the checked commit, the history key the task will close under and the checks; runs `git merge --no-ff --no-commit <checked commit>` in the primary worktree, writes the task's decision log as it stands (empty when it is missing), followed by the closing its close will append, `## Closed: merged, <merging.since>` with the answer it gives the reports still unanswered (below), to `.concorde/decisions/<history key>.md` and stages it, and commits the merge with the message `Merge branch 'concorde/<task-id>' at <checked commit>`, a blank line and the trailer `Concorde-Task: <task-id>`, and records that commit as `merging.after`; when Git refuses that commit, it aborts the merge, removes the log's copy, stores the task `open` again and refuses with `git_failed`; runs each check there, keeping its output as `output.log` of the check's node below the attempt's node `merges/<n>/`; then closes the task as `close --merged` does under the recorded history key, with `merging.since` as the closing's time, clearing `merging`, and then, still holding the merge lock, where the issues part is installed, closes each Issue of the record's `resolves` still open with the Issues bookkeeping command as `resolved`, actor `main-agent`, the note `Fixed by task <task-id>, merged into the primary branch at <merge commit>.` and the evidence `merge commit <merge commit>` and `task <task-id>`, each closure the Issue store's own commit on the primary branch; the primary branch then already holds the task's decision log as the close leaves it, so that close commits nothing, unless the log changed after the merge commit, as it may before a `--resume`, when the close commits it again (below). The default check, where the spec part is installed, is `concorde spec-validation` of the merged primary worktree, run by the same Python with the running package on its path; where it is not, a merge given no `--check` runs no check and adds a warning saying so; each `--check` is split into words as a shell would and run without a shell, and any `--check` replaces the default, except while the primary worktree holds the mark `.concorde/update.json` of an update not validated since ([Distribution](../../distribution/requirements.md#req.distribution.update-unvalidated)): the default check then runs after the given ones unless they include it, where the spec part is installed, and is recorded among the attempt's checks, so `--resume` runs it again; a check still running after 1800 seconds is stopped and counts as failed. A conflict aborts the merge; a check that exits non-zero or cannot run, or checks that leave an uncommitted path, reset the primary branch to the commit the merge started from with `git reset --keep`, so a refusal again leaves the primary branch where it was; the reset leaves the paths the checks created in the primary worktree, and the refusal names them. After a conflict or a reset the task is stored `open` again, with `merging` null. `--wait` (default 300) bounds how long to wait for both locks together; `waited_seconds` is how long it waited | `{"record": <record>, "resolved": [{"issue_id": "<Issue>", "status": "closed", "revision": "<digest>"}, …], "merge": {"before": "<commit>", "after": "<commit>", "contained": <true when the primary branch already held the checked commit, so no merge commit was made and before and after are the same>, "checks": [{"argv": ["<word>", …], "exit_code": 0, "seconds": <number>}], "waited_seconds": <number>, "log": "<absolute path of the attempt's node>"}, "warnings": ["<text>", …]}`; `warnings` names the decision log when it is missing or holds exactly what `open` wrote, read before the close appends to it, and each Claude Code task session the close did not keep or remove as [Task sessions](../task-session/contracts.md#at-the-end-of-a-task) states, and each Issue of `resolves` the merge could not close, such as one closed meanwhile, and each write of the attempt's or a check's trace node that the file system refused, with the node's file and the error, which a refusal names in its detail instead, with the rendered [error chain](../../glossary.json#concept.error-chain) of the Issues command's refusal, and is empty otherwise; an Issue the merge could not close never makes it a refusal |
| `concorde task merge <task-id> --resume [--wait <seconds>]` | For a `merging` task, holding both locks as a merge does: when the primary worktree is clean on the recorded branch and its head is the recorded merge commit (or, with none recorded, a merge commit whose parents are exactly the commit before and the checked commit), reruns the recorded checks there, as a new attempt's node, then closes the task or resets the primary branch exactly as `merge` does after its checks | As `merge` |
| `concorde task merge <task-id> --abort [--wait <seconds>]` | For a `merging` task, holding both locks as a merge does: when the primary worktree is on the recorded branch, runs `git merge --abort` when the task's own merge is in progress there, of its checked commit into the commit before the merge, then resets it with `git reset --keep` to the commit before the merge if its head is the merge commit, leaves it if its head already is that commit, and stores the task `open` with `merging` null | `{"record": <record with its derived state>, "warnings": ["<each write of the attempt's trace node the file system refused>", …], "abort": {"before": "<commit>", "undone": "<merge commit reset away>\|null", "left": ["<path the reset left in the primary worktree>", …], "waited_seconds": <number>}}` |
| `concorde task deliver <task-id> [--check <command>]… [--wait <seconds>]` | Refused with `delivery_by_method`, naming `concorde delivery`, wherever the method part is installed. Otherwise, run in the task's worktree (`not_task_worktree` elsewhere) for a task that has not ended (`task_closed`) and whose worktree's head is on the task branch (`wrong_branch`), waiting up to `--wait` seconds (default 300) for the task's [workspace lock](../../glossary.json#concept.workspace-lock) and holding it, never taking again a lock file that a close removed while it waited (`task_closed`): checks these refusals again on the record read under the lock, so a close, merge or branch switch that came during the wait is refused as above; then, when the branch head already is a [delivery commit](../../glossary.json#concept.delivery-commit) of the task's workspace that verifies and the worktree is clean, reports it and commits nothing; otherwise runs each `--check` in the worktree in order, split into words as a shell would and run without a shell, each stopped after 1800 seconds and counted as failed, refusing with `check_failed` at the first that exits non-zero or cannot run, then stages every change Git does not ignore and commits it with the subject `concorde: deliver <task-id>`, a blank line and the task's goal, using the repository's configured author identity and hooks, even when nothing is staged; a commit that does not verify, its only parent the head it started from, is taken off the branch again with `git reset --soft` and refused with `git_failed`. Records the attempt as a node `deliveries/<n>/` of the task's trace, of kind `delivery`, with each check a node `checks/<n>/` below it of kind `delivery-check` keeping its `output.log`, and the commit it made (`commit`) or found (`found_commit`) among its references | `{"record": <record with its derived state>, "delivery": {"commit": "<commit>", "recovered": <true when it found the head delivered>, "checks": [{"argv": ["<word>", …], "exit_code": 0, "seconds": <number>}], "waited_seconds": <number>, "log": "<absolute path of the attempt's node>"}, "warnings": ["<text>", …]}`; `warnings` names each write of the attempt's or a check's trace node that the file system refused, with the node's file and the error, and is empty otherwise; a refusal names them in its detail the same way |
| `concorde task close <task-id> --merged [--note <text>] [--wait <seconds>]` | First runs Tracing's retention; waiting up to `--wait` seconds (default 300) for the task's workspace lock and then for the merge lock, and holding both, then waiting as long as it takes for the task's workflow lock and holding it too, checks the merge, removes the worktree, chooses the history key, the task's identity or `<task-id>.<n>` with the smallest `n` from 2 free both in the history and among the decision logs `.concorde/decisions/` of the primary worktree, sets state `closed` with outcome `merged` and, in the same write of the record, answers each report still unanswered as the task's end (below), appends the outcome and any note to the decision log, with those reports and their answer, ends the task's trace node, commits the log on the primary branch unless it already holds `.concorde/decisions/<history key>.md` (below), then, after [Task sessions](../task-session/contracts.md#at-the-end-of-a-task) copied the transcripts of the task's Claude Code task sessions into their nodes and finished those nodes from Claude Code's records, ends the task's latest merge attempt node `merges/<n>/` that still says it runs, `ok` with outcome `merged`, or `contained` when its merge commit is the commit it started from, when its content records a merge commit, and otherwise `failed` with outcome `interrupted`, moves the task's folder to `.concorde/history/<history key>/` and removes the task's task, workspace and workflow locks; once the task is closed, Task sessions removes those sessions from Claude's session list with `claude rm` | `{"record": <the updated record>, "warnings": ["<text>", …]}`; `warnings` names each Claude Code task session whose transcript could not be kept or that `claude rm` did not remove, and a refused write of the merge attempt's node it ended, with the node's file and the error, and is empty otherwise |
| `concorde task close <task-id> --completed --note <text> [--force] [--wait <seconds>]` | For a task that reached its goal without merging: first refuses, before stopping anything, with `merge_incomplete` while another task's merge is unfinished and no live process holds the merge lock, and with `dirty_worktree` when the worktree holds uncommitted changes and `--force` is not given; then stops each task session of the task with `claude stop`, refusing with `session_stop_failed` when one cannot be confirmed stopped, then, with `SIGTERM`, where the execution part is installed, each run of the task's workspace whose [run lock](../../glossary.json#concept.run-lock) a process of this machine holds, those waiting in Execution's lobby for its workspace lock included; then, holding the workspace lock and then the merge lock, waited for as with `--merged`: removes the worktree, discarding uncommitted changes only with `--force`, sets state `closed` with outcome `completed` and the note, answering each report still unanswered as with `--merged`, appends the outcome and the note to the decision log, with those reports and their answer, ends the trace node, commits the log as with `--merged`, keeps the transcripts, moves the folder to the history and removes the task sessions as with `--merged` | As with `--merged` |
| `concorde task close <task-id> --failed --reason <text> ((--run <run-id> \| --error-file <path>)… \| --no-error) [--force] [--wait <seconds>]` | For a task that did not reach its goal: refuses and then stops its task sessions and runs as `--completed` does, then, holding the workspace lock and then the merge lock, waited for as with `--merged`: removes the worktree, discarding uncommitted changes only with `--force`, sets state `failed` with the reason as note and, as errors, the `error` of each named run of the task's workspace, read from its workspace folder, and each error read from a file, unchanged; `--no-error` declares that no error caused the failure; answers each report still unanswered as with `--merged`; appends the outcome, the reason and the errors, rendered and as JSON, and those reports with their answer to the decision log, ends the trace node, commits the log as with `--merged`, keeps the transcripts, moves the folder to the history and removes the task sessions as with `--merged` | As with `--merged` |
| `concorde task escalate <task-id> [--by main-agent\|task-session] [--run <run-id> \| --error-file <path> \| --escalation <n>]… --code <code> --detail <text> --reason <reason> --explanation <text> [--attempt <text>]… [--option <text>]… [--recommendation <text>]` | For a current task that has not ended (`task_closed` otherwise): builds the escalating session's link, of level `main-agent` (the default, actor `main agent (task <task-id>)`) or `task-session` (actor `task session (task <task-id>)`), whose causes are the `error` of each named run of the task's workspace, read from the [run store](../../glossary.json#concept.run-store), each error read from a file (a link, or a JSON value whose `error` is one) and the error of each named earlier escalation of the task (numbered from 1 in record order), with no causes when it names none (a decision to escalate that no error carries), appends it to the escalations of the task's trace node and to the decision log, rendered and as JSON, under a heading naming the receiver: the [main agent](../../glossary.json#concept.main-agent) for `task-session`, the developer for `main-agent` | `{"escalated": <link>, "number": <its number in the task's trace, from 1>, "decision_log": "<absolute path>", "rendered": "<the chain as indented text>"}` |
| `concorde task report <task-id> --text <report> [--escalation <n>]…` | For a task that has not ended (`task_closed` otherwise): appends the report, numbered from 1, to the record's `reports`, with its time, the record's `main` at that moment, the text, the named escalations of the task (`unknown_escalation` for a number it does not have) and `answer` null, then to the decision log under the heading `## Report <n> to the main agent (<main>), <time>`, followed by the escalations it carries; the task session runs it before every message to the main agent | `{"report": <the report as recorded>, "main": "<the record's main, the session to message>"\|null, "decision_log": "<absolute path>"}` |
| `concorde task answer <task-id> --report <n>… --text <answer>` | For a task that has not ended: records `{"at", "text", "by": "main-agent"}` as the `answer` of each named report of the record, refusing a number it does not have (`unknown_report`) and a report already answered (`already_answered`), then appends the answer to the decision log under the heading `## Answer to report(s) <n>, … of the task session, <time>` | `{"answered": [<each report with its answer>], "decision_log": "<absolute path>"}` |
| `concorde task wait <task-id> --until <state>[,<state>…] [--timeout <seconds>]` | None; blocks until the task's derived state is one of the named states, which must be among `delivered`, `closed` and `failed` (`merging`, which lasts only while a merge holds the lock, is refused with `invalid_input` naming `--merge`), learning of each new holder of the task's workspace lock through the operating system's notification of changes to its lock file and blocking on the lock until that holder releases it, then reading the state again; answers at once when the state already is one of them | `{"task": "<task-id>", "state": "<state>", "waited_seconds": <number>}` |
| `concorde task wait <task-id> --rebound <session> [--timeout <seconds>]` | None; blocks until the task's record names a `main` other than `<session>`, learning of every write of the record, which replaces `task.json` in the task's folder, and of the folder's move to the history through the operating system's notification of changes to that folder, then reading the record again; answers at once when it already names another; a task that ended ends the wait with `wait_unreachable` | `{"task": "<task-id>", "main": "<the main it names now>"\|null, "former": "<session>", "waited_seconds": <number>}` |
| `concorde task wait --run <run-id> [--timeout <seconds>]` | Refused with `part_missing` where the execution part is not installed; otherwise none; blocks on the run's [run lock](../../glossary.json#concept.run-lock), shared, until its runner releases it, for a run of any task's workspace or an [unbound run](../../glossary.json#concept.unbound-run) a reader finds | `{"run": "<run-id>", "status": "<status of its result, or lost when it has none>", "result": "<absolute path of result.json>\|null", "waited_seconds": <number>}` |
| `concorde task wait [<task-id>] --lock merge\|workspace [--timeout <seconds>]` | None; blocks on the merge lock, or the workspace lock of the task named, shared, until no process holds it | `{"lock": "merge\|workspace", "task": "<task-id>\|null", "released": true, "held_by": <the holder line when the wait began, or null when the lock was free>, "waited_seconds": <number>}` |
| `concorde task wait <task-id> --merge [--timeout <seconds>]` | None; blocks on the task's merge attempt lock, shared, until no process holds it, a missing file being free, so it returns only once a merge of the task has written its whole answer, then finds the task's latest merge attempt `merges/<n>/` with the largest `n`, in the task's folder or the history | `{"task": "<task-id>", "attempt": {"number": <n>, "node": "<absolute path of the attempt's node>", "status": "<its node's status>"\|null, "outcome": "<its node's outcome>"\|null, "output": "<absolute path of output.json>"\|null, "messages": "<absolute path of messages.log>"\|null}\|null, "held_by": <the holder line when the wait began, or null>, "waited_seconds": <number>}`; `attempt` is null for a task that has no merge attempt, and `output` and `messages` are null for a merge the server did not start |

The decision log that `open` creates contains exactly a level-1 heading `Decision log: <task-id>`
and a paragraph `Goal: <goal>`.

<a id="settled-reports"></a>

The end of a task answers every report of its record still unanswered. This ensures that no report
of an ended task waits for an answer nobody may give any more. The close that stores the task
`closed` or `failed` gives each such report, in the same write, the answer
`{"at": <the closing's time>, "text": <how the task ended>, "by": "merge"|"close"}`. `by` is `merge`
when `concorde task merge` closes the task, and `close` when `concorde task close` does. The text is
`The task ended before the main agent answered: <how>. Nobody answers a report after that.`. The
value of `<how>` depends on the closing command:

- For a merge, ``concorde task
  merge` merged its delivery commit <checked commit> into <primary branch> and closed it as merged``.
- ``concorde task close
  --merged` closed it as merged, its delivery commit being in the primary branch`` for `close
  --merged`.
- ``concorde task close
  --<outcome>` closed it as <outcome>: <note>`` for `--completed` and `--failed`, with the note or
  reason.

When the end answered any report, the closing entry of the decision log ends, after the note and the
errors, with the paragraph
`The <merge|close> answered report(s) <n>, … of the task session, unanswered until then: <text>`.
For the reports unanswered when it commits, a merge writes that paragraph into the merge commit's
copy of the log. Thus, a report recorded after the merge commit changes the log, which the close
then commits again.

<a id="decision-log-commit"></a>

When the primary branch's `HEAD` lacks `.concorde/decisions/<history key>.md` with exactly the log's
bytes, a close commits the decision log as it stands once the closing is appended. The branch either
lacks the file or holds an earlier copy, such as a merge commit's copy of a log that changed
afterwards. The close writes the log there in the primary worktree and stages it with `git add -f`.
The close commits that path alone with `git commit --only`, which leaves every other staged or
unstaged change of the primary worktree as it was. The close uses these for the commit:

- The repository's author identity.
- The repository's commit hooks.
- The message:

```text
concorde: keep the decision log of <task-id>

Task <task-id> ended <outcome>.

Concorde-Task: <task-id>
```

When the primary worktree's `HEAD` is detached or Git refuses the commit, the close unstages and
removes the log's copy, or restores the copy `HEAD` holds. The close refuses with
`decision_log_uncommitted`. The following state remains:

- The record is already closed.
- The decision log holds the closing.
- The folder is still current.

When run again, the same close proceeds in this order:

- It commits the log.
- It keeps the transcripts.
- It moves the folder.

The merge lock is an exclusive `flock` on `.concorde/locks/merge.lock` of the primary worktree. The
process running these commands takes the lock before reading anything it acts on:

- `open`
- `close`
- `merge`

The process holds the lock for the whole command. When the process ends, the process releases the
lock. Every write of the project's [Issues](../../issues/interface.md#store-operations) does the
same. Each write commits on the primary branch, naming itself `an Issue write (<what it writes>)`.
When the process dies, however it dies, the operating system releases the lock. While holding the
lock, the process keeps in the file one JSON object `{"holder": "`concorde task
<open|close|merge>` of task <task-id>", "pid": <pid>, "since": "<RFC 3339 time>", "session": "<Claude Code session>", "task": "<task-id>"}`.
This object is the holder line of every lock under `.concorde/locks/`. The object contains `session`
only when the process's environment names one in `CLAUDE_CODE_SESSION_ID`.

After a merge starts with its locks inherited, as
[Tracing](../../kernel/tracing/contracts.md#handing-a-lock-on) states, the merge adopts them without
waiting. The merge writes its own holder line into each lock. When `CONCORDE_MERGE_ATTEMPT` names
the task's next attempt folder `merges/<n>/`, made for the merge and holding no node yet, the merge
removes the environment variable. Such a merge records its attempt's node there. That folder holds
the merge's standard output `output.json` and standard error `messages.log`. The node names those
files as its artifacts `output` and `messages` without a digest, since the merge completes them
after the node ends.

When any refusal of the table below refuses such a merge before its attempt began, the merge still
records the attempt there. The attempt is `failed` with the outcome `refused` and the refusal's link
as its error. The attempt records the primary worktree's branch (`HEAD` when detached) and commit as
it found them as `branch` and `before`. The attempt records `checked` and `after` as null.

Only a process that failed to take the lock reads that object. Thus, the next holder overwrites an
object left by a dead holder, and that object is never reported. `open` and `close` wait for the
lock as long as `merge` does by default.

Before merging, `merge` refuses whatever `close --merged` would refuse apart from containment. Thus,
after the checks passed, closing fails only in these cases:

- For an environment error such as `worktree_failed`, closing fails.
- If the task branch or worktree was changed by hand during the merge, closing fails with
  `not_merged` or `dirty_worktree`.

That refusal leaves these in place:

- The merge.
- Its checked commit.
- The task in state `merging`.

The refusal names the merge commit. The refusal says that, once the cause is fixed,
`concorde task merge <task-id> --resume` finishes the task. A `rollback_failed` also leaves the task
`merging`, and says that `--abort` restores the primary branch.

`close` runs its steps in this order:

- `git worktree remove`.
- The record update.
- The append of the closing to the decision log.
- The end of the trace node, which thus records the log's final digest.
- The move of the task's folder to the history.

When the close is forced or the worktree has submodules, removal uses `--force`, since Git removes a
worktree holding submodule checkouts only then. After a step, a refusal leaves what the steps before
it did. The close never runs `git submodule deinit`, which would unregister the submodules in the
configuration every worktree shares.

A `worktree_failed` from the removal says that the worktree is as Git left it and the record
unchanged. After the worktree was removed, these refusals of the record update name the removed
worktree and say the task keeps its state without it:

- `record_conflict`
- `record_unwritable`
- `unknown_task`

After the record update, any refusal names these details:

- The task's stored state.
- The task's outcome.
- The task's time.

Examples are a `decision_log_failed` or a `record_unwritable` of the trace node. Each refusal says
that, once the cause is fixed, running the same close again with the same options finishes it. When
the close is a merge's, the `merge` refusal also says this:

- While the task is still `merging`, `concorde task merge <task-id> --resume` finishes it.
- Once the record update stored the task closed as merged, `close --merged` finishes it.

The rerun skips a worktree that no longer exists and records `worktree_removed` false then. For a
task already stored `closed` or `failed` with the outcome it names, the rerun returns the record
unchanged. For that task, the rerun also does the following:

- When the decision log holds no line `## Closed: <outcome>, <closed.at>`, the rerun appends the
  closing the record holds.
- When the task's trace node has not ended, the rerun ends that node as the close that stored the
  task would have.

These commands hold the task's lock from the check that the task has not ended through their append
to the decision log:

- `escalate`
- `report`
- `answer`

A close holds the task's lock from its record update through the end of the trace node. Thus,
nothing is appended to a decision log after its closing. For a task that ended, `escalate` refuses
with `task_closed`.

`escalate` writes the record before it appends to the decision log. When the append fails, it
refuses with `decision_log_failed`. The refusal names these details:

- The escalation's number in the record.
- The decision log.
- The file system's error.
- The heading the entry would have had.

The refusal carries the rendered chain. The refusal says that escalating again would record the
chain twice, so the chain is appended by hand. `report` and `answer` likewise write the record
first. When the append fails, they refuse with `decision_log_failed`, naming the report and carrying
the entry to append by hand.

The task's workspace lock is the Kernel's lock of the workspace named after the task,
`.concorde/locks/workspaces/<task-id>.lock` (`contract.kernel.workspace-binding`). Before the merge
lock, `merge` and `close` take the workspace lock. They name themselves in the workspace lock as ``
`concorde task <command>` of task <task-id> ``.

The task's workflow lock, `.concorde/locks/workflows/<task-id>.lock`, is Workflows' lock of the
workspace's [workflow record](../../glossary.json#concept.workflow-record). Every close, including
the close that ends a merge, takes the workflow lock after the workspace and merge locks. The close
waits as long as it takes, since a [workflow step](../../glossary.json#concept.workflow-step) holds
the workflow lock only for writes that wait for no other lock. The close names itself in the
workflow lock the same way. The close holds the workflow lock until the task's folder moved.

Every change of the task's record and trace holds the task's lock,
`.concorde/locks/tasks/<task-id>.lock`, so that two processes never change a task at once. While
holding all three, the close that moves the task removes these locks:

- The task lock.
- The workspace lock.
- The workflow lock.

| Error code | Raised when |
| --- | --- |
| `not_primary` | `open`, `close`, `merge`, `session`, `rebind` or `answer` runs outside the primary worktree. |
| `worktree_not_ignored` | Git does not ignore the worktree path in the primary worktree; the message names the path and how to ignore it. |
| `invalid_input` | A goal or Module list is missing or repeats a Module, or names one that is no Module identity (`module.<name>`), checked whether or not the spec part is installed, or `close` names not exactly one of `--merged`, `--completed` and `--failed`, `--completed` lacks `--note`, `--failed` lacks `--reason`, `--failed` names both or neither of an error source (`--run`, `--error-file`) and `--no-error`, an option belongs to another outcome, or `--force` accompanies `--merged`, or a `--check` is empty or cannot be split into words, or `--check` accompanies `--resume` or `--abort`, or `--wait` is negative, or `session` starts a task session without `--main`, or `rebind` names an empty `--main`, `report` an empty `--text` or `answer` an empty `--text`, or `wait` names no target or more than one, `--rebound` without a task or with an empty session, `--until` without a task or with a state other than `delivered`, `closed` and `failed`, `--run` with a task, `--lock workspace` or `--merge` without one or `--lock merge` with one, or a negative `--timeout`. |
| `worktree_failed` | Git refused to add or remove the worktree; the message carries Git's error. |
| `binding_failed` | `open` added the worktree but could not write its [workspace binding](../../glossary.json#concept.workspace-binding); the message names the file, the worktree and branch left behind and how to remove them. |
| `invalid_task_id` | The identity does not match the record's `id` pattern. |
| `task_exists` | A current task with that identity exists, whatever its state. |
| `branch_exists` | The branch `concorde/<task-id>` already exists. |
| `path_exists` | The worktree path already exists. |
| `unknown_module` | Where the spec part is installed, a named Module is not in the registry. |
| `invalid_issue` | `open --resolves` or `resolve` names an Issue that is not an open Issue of the project, a malformed identity or an Issue twice; the message names each. |
| `specs_unloadable` | Where the spec part is installed, the registry mirror `.concorde/specs.json` of the primary worktree, which names the Modules a task may name, cannot be read. |
| `unknown_task` | No current task has that identity, nor, for `list` and `show`, the history. |
| `invalid_transition` | `close` or `merge` names a task that is already `closed` or `failed`, apart from the same close of a task whose decision log lacks its closing (above), or a merge would store `merging` for a task whose stored state is not `open`. |
| `not_merged` | `close --merged` or `merge` finds that the task branch holds no delivery commit of the task's workspace since the base commit or that its latest delivery commit is not the head of the branch, or `close --merged` finds that head not contained in the primary branch. |
| `delivery_unverified` | `close --merged` or `merge` finds that the branch head, the latest delivery commit of the task's workspace, does not verify: it has not exactly one parent; the message names the head and the mismatch. |
| `dirty_worktree` | The worktree has uncommitted changes and the command is `--merged`, or `--completed` or `--failed` without `--force`. |
| `task_closed` | A session is started or recorded, a main rebound, a report recorded, a report answered or an error escalated for a task that is closed or failed. |
| `record_conflict` | The record changed concurrently three times in a row. |
| `record_unreadable` | The [task record](../../glossary.json#concept.task-record) on disk cannot be read as JSON. |
| `record_unwritable` | The file system refused to write the task record or its trace node; the message names the record or node and the file system's error. From `open`, which refuses a task node it could not write, since that node holds the transitions and escalations later task commands read and change, the worktree, branch and task folder the open added are removed first, and the message says so or names each that could not be removed and how to remove it. |
| `decision_log_failed` | `close`, `escalate`, `report` or `answer` wrote the task record and the file system then refused the append to the [decision log](../../glossary.json#concept.decision-log), or a rerun of a close cannot read it; the message says what was written and how to finish (above). |
| `decision_log_uncommitted` | `close`, or the close a merge runs when the primary branch does not hold the log as it ended, could not commit the task's decision log on the primary branch: its `HEAD` is detached or Git refused the commit; the record is closed and the log holds the closing, the folder is still current, and the message names the log, its path in Git, Git's output and that the same close finishes (above). |
| `git_failed` | A Git command Tasks needs failed, such as the commit of a merge a hook refused; the message names the command, its exit status and its output, and for a merge that it was aborted and where the primary branch is. |
| `unknown_run` | `escalate` or `close --failed` names a run whose result cannot be read from the run store, or a run of another workspace or of none, or `wait --run` names a run no reader finds; the message names the workspace the run belongs to, or where it looked. |
| `unknown_escalation` | `escalate` or `report` names an escalation number the task's trace does not have. |
| `unknown_report` | `answer` names a report number the task's trace does not have. |
| `already_answered` | `answer` names a report that has an answer already; an answer is never replaced. |
| `merge_busy` | The merge lock stayed held for the whole wait, or `session` or `escalate` names the task a live merge is merging; the message names the holder's command, task, process and start time. |
| `session_stop_failed` | `close --completed` or `--failed` could not confirm a Claude Code task session of the task stopped with `claude stop`, before it changed the task; the message names the session, Claude Code's answer and the command to stop it ([Task sessions](../task-session/contracts.md#at-the-end-of-a-task)). |
| `workspace_busy` | `merge`, `close` or `deliver` found the task's workspace lock still held by a run after waiting `--wait` seconds; the message names the holder, the lock file and how long it waited. |
| `merge_incomplete` | A task is stored `merging` and no live process holds the merge lock; the message names the task, the process and time that began its merge, the checked commit, the primary branch with the commit before the merge and where its head is now, whether that is the merge commit, and the `--resume` and `--abort` commands. |
| `marker_unwritable` | `merge` could not write the Kernel's [unfinished-merge marker](../../glossary.json#concept.unfinished-merge-marker) before it stored the task `merging`; nothing was recorded or merged, and the message carries the Kernel's refusal. |
| `not_merging` | `merge --resume` or `--abort` names a task that is not `merging`; the message names its state. |
| `not_resumable` | `merge --resume` finds that the primary branch's head is not the merge commit; the message names the head and whether it is the commit before the merge, and that `--abort` is the way out. |
| `merge_diverged` | `merge --resume` or `--abort` finds the primary worktree on another branch or detached, or (`--abort`) its head neither the commit before the merge nor the merge commit, or a Git merge in progress there that is not the task's, all checked before anything is aborted; the message names the commits and says to restore the branch by hand. |
| `primary_dirty` | `merge` finds an uncommitted or untracked path in the primary worktree after putting back what Issue writes left there, or its `HEAD` detached; the message names the paths or the detached commit, says that a task changes nothing outside its worktree, and names each Issue record the recovery left as no Issue write's, or the recovery's failure. |
| `changed_outside` | `merge` finds an uncommitted or untracked path in the worktree of a task that has ended and whose worktree outlived it; the message names each worktree with its task and its paths. A worktree of a task that has delivered and waits is a warning of the merge instead, not a refusal. |
| `merge_conflict` | `git merge` stopped with conflicts; the merge was aborted, and the message names the conflicting paths. |
| `check_failed` | A check of `deliver` exited non-zero or could not run; nothing was committed, and the message names the check, its exit status, its log and the end of its output. Or a post-merge check, of a merge or of `--resume`, exited non-zero or could not run, or the checks left uncommitted paths; the primary branch was reset to the commit before the merge and the task is delivered again, and the message names the failing check, its exit status, the log and the end of its output, or the paths the checks left and the log, and any paths the checks created, which stay in the primary worktree. |
| `rollback_failed` | After a conflict or a failed check, or during `--abort`, Git refused to abort the merge or reset the primary branch; the message carries the original failure, Git's output and the commit the primary branch is at, the primary worktree is left as Git left it, and the task stays `merging`. |
| `nothing_to_escalate` | `escalate` or `close --failed` names a run that ended without an error. |
| `invalid_error` | An escalated file or escalation is not an error link, or the escalating session's link does not satisfy the error contract. |
| `wait_timeout` | `wait` did not see what it waits for within `--timeout` seconds; nothing changed. Reason `environment`. |
| `wait_unreachable` | `wait --until` finds the task ended `closed` or `failed` in a state it does not name, or `wait --rebound` finds the task ended; the message names that state. |
| `wait_failed` | The operating system refused to watch the directory of the task's workspace lock; the message carries its error. Reason `environment`. |
| `part_missing` | The command, or an option of it, needs a part that is not installed: `--resolves` and `resolve` the issues part, `wait --run` the execution part; the message names the part and that it is not installed. |
| `part_unknown` | `deliver` or `wait --run` could not ask the worktree's own `concorde` whether the part it needs is installed, since that command could not run to its end; the message names the command and how it failed. |
| `issues_unavailable` | `--resolves` or `resolve` could not read the Issues it names, since `concorde issues show` could not run to its end or answered no Issue record; nothing was recorded. |
| `delivery_by_method` | `deliver` runs where the method part is installed; the message names `concorde delivery`, which delivers a task there. |
| `not_task_worktree` | `deliver` runs outside the worktree of the task it names. |
| `wrong_branch` | `deliver` finds the task worktree's head detached or on another branch than the task's; the message names both. |
| `invalid_command` | The command line is malformed. |

## Record updates

Nothing below the task level updates a task. The following are recorded where they happen, in the
workspace folder and on the task branch:

- Runs.
- Deliveries.
- Workflows.

Tasks reads them. Besides the following commands, a task changes only through the update a task
session's start makes:

- `open`
- `merge`
- `close`
- `deliver`
- `escalate`
- `rebind`
- `report`
- `answer`
- `resolve`

That update writes a trace node below the task's node. The update holds the task's lock during these
actions:

- It reads.
- It checks its precondition.
- It writes.

Holding the lock keeps the precondition true for what the update writes. The update refuses with the
codes above.

| Update | Preconditions | Effect |
| --- | --- | --- |
| Record session (`task`, `session`) | The task is a current task neither `closed` nor `failed`. Otherwise `unknown_task` or `task_closed`. | Writes the session's node `sessions/<session id>/` and names the session's `main` as the record's `main`, as `rebind` does. |
