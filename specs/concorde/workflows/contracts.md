# Workflows contracts

The exact shapes of [Workflows](module.md): what one step prints, the step request a
[step agent](../glossary.json#concept.step-agent) passes with `--json`, the step output
convention through which a run's output declares what a workflow must know, the
[workflow result](../glossary.json#concept.workflow-result), the MCP tools the workflow part
registers, the error codes of the workflow's own links, and the content of the workflow's and each
step's trace node. Error links
follow the Framework's
[error contract](../kernel/tracing/contracts.md#contract.tracing.error), copied here as `$defs`.

## Step outcome

Printed by `concorde workflow step`, from the workspace's
[workflow record](../glossary.json#concept.workflow-record) and the saved
[run result](../glossary.json#concept.run-result).

```concorde-contract
{
  "id": "contract.workflows.step",
  "version": 6,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "workflow",
      "workspace",
      "key",
      "name",
      "run_id",
      "state",
      "status",
      "summary",
      "result_path",
      "decision_points",
      "blocking",
      "data",
      "error"
    ],
    "properties": {
      "workflow": {
        "type": "string",
        "minLength": 1
      },
      "workspace": {
        "type": "string",
        "minLength": 1
      },
      "key": {
        "type": "string",
        "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
      },
      "name": {
        "type": "string",
        "pattern": "^[a-z][a-z_-]*$"
      },
      "run_id": {
        "anyOf": [
          {
            "type": "string",
            "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
          },
          {
            "type": "null"
          }
        ]
      },
      "state": {
        "enum": [
          "running",
          "finished",
          "lost",
          "refused"
        ]
      },
      "status": {
        "anyOf": [
          {
            "enum": [
              "ok",
              "blocked",
              "failed"
            ]
          },
          {
            "type": "null"
          }
        ]
      },
      "summary": {
        "anyOf": [
          {
            "type": "string",
            "minLength": 1
          },
          {
            "type": "null"
          }
        ]
      },
      "result_path": {
        "anyOf": [
          {
            "type": "string",
            "minLength": 1
          },
          {
            "type": "null"
          }
        ]
      },
      "decision_points": {
        "type": "integer",
        "minimum": 0
      },
      "blocking": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "code",
              "detail"
            ],
            "properties": {
              "code": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9_]*$"
              },
              "detail": {
                "type": "string",
                "minLength": 1
              }
            }
          }
        ]
      },
      "data": {
        "type": "object"
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
      }
    },
    "$defs": {
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
  "semantics": "The outcome of one workflow step in the bound workspace the step command runs in. workspace names that workspace as its binding does. key is the step key, including the restart label after # and the answers digest after @ when they were given. name is the Operation or execution command the step runs. run_id names the run recorded for the key, null for a refused step, except one whose run started before its workspace was retired, which names that run, and for a step that is still waiting for the workspace lock, and result_path the path in the run store where its run result is or will be saved. state is running while the run has no result and its runner lives, and also when the command's wait ended before the workspace lock was free, in which case nothing was started or recorded and asking again waits for the lock again; finished once it has a result, lost when it has neither a result nor a living runner, and refused when the run could not start, the workflow record refused the step or the workspace was retired while the command waited for its workflow lock, which nothing records; status and summary are the result's once finished and null otherwise. decision_points counts the decision points the finished run declared under the step output convention, leaving out those the step's own answers settle, and 0 otherwise. blocking is the run's declared blocking item, null when it declared none or has not finished, and data is the data object it declared, handed to the script unchanged and uninterpreted, {} when it declared none or has not finished; Workflows reads nothing else of a run's output. error is null for running and finished, and the workflow's link for lost and refused. A behaviour or field change increments the version.",
  "example": {
    "workflow": "brownfield",
    "workspace": "adopt",
    "key": "survey",
    "name": "survey",
    "run_id": "r-20260925T101500-survey-1a2b3c4d",
    "state": "finished",
    "status": "ok",
    "summary": "survey finished for module.shop.",
    "result_path": "/home/dev/shop/.concorde/tasks/adopt/workspace/workflow/steps/1-survey/run/result.json",
    "decision_points": 1,
    "blocking": null,
    "data": {},
    "error": null
  }
}
```

## Step request

What `concorde workflow step --json` takes, as the
[step agent](../glossary.json#concept.step-agent) passes it.

```concorde-contract
{
  "id": "contract.workflows.step-request",
  "version": 6,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "workflow",
      "mode",
      "key",
      "argv"
    ],
    "properties": {
      "workflow": {
        "type": "string",
        "minLength": 1
      },
      "mode": {
        "enum": [
          "interactive",
          "no-ask"
        ]
      },
      "key": {
        "type": "string",
        "pattern": "^[a-z][a-z0-9_:.-]*$"
      },
      "argv": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "answers": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "id",
                "question",
                "answer",
                "answered_by"
              ],
              "properties": {
                "id": {
                  "type": "string",
                  "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
                },
                "question": {
                  "type": "string",
                  "minLength": 1
                },
                "answer": {
                  "type": "string",
                  "minLength": 1
                },
                "answered_by": {
                  "enum": [
                    "main-agent",
                    "developer"
                  ]
                }
              }
            }
          }
        ]
      },
      "retry": {
        "type": "boolean"
      },
      "restart": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string",
            "pattern": "^[a-z0-9-]+$"
          }
        ]
      }
    }
  },
  "semantics": "One step request, with the meaning of the command line's options: the workflow, mode and base step key, argv as the name of an Operation or an execution command followed by its arguments, answers as the list of every answer given for this step so far or null, each in the shape of an answer of the step output convention ($defs.answer of contract.workflows.step-output), naming by id the decision point it settles, saying in answered_by whether the main agent or the developer settled it, retry to start a new run for a key whose current step did not end ok, and restart, a short generation label or null, to start the step again whatever its outcome: the label is part of the step key, so the restarted step supersedes the earlier one and every later step once, and a relaunch with the same label finds it again. The request names no workspace: the step runs in the workspace whose binding lies in the worktree the command starts in, and argv carries no workspace either. An Operation in argv is started as concorde run <argv> --detach and an execution command as concorde <argv> --detach. answers, retry and restart are optional and mean null, false and null when left out; the workflow scripts leave them out whenever they hold that value, so that a step agent that retypes the request has less to copy. A behaviour or field change increments the version.",
  "example": {
    "workflow": "brownfield",
    "mode": "interactive",
    "key": "survey",
    "argv": [
      "survey",
      "--modules",
      "module.shop"
    ],
    "answers": [
      {
        "id": "d.db-helper",
        "question": "Does the shared database helper get a Module of its own?",
        "answer": "a Module of its own",
        "answered_by": "main-agent"
      }
    ],
    "retry": false,
    "restart": null
  }
}
```

## Step output convention

What a run's output declares for a workflow. Any [Operation](../glossary.json#concept.operation) or
[execution command](../glossary.json#concept.execution-command) may fill it; Workflows reads nothing
else of a run's output, and the step command and the report read it from the saved
[run result](../glossary.json#concept.run-result)'s `output`. The producing Operation's or
command's own [Spec](../glossary.json#concept.spec) says which of its items it declares here.

```concorde-contract
{
  "id": "contract.workflows.step-output",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "decision_points",
      "decisions",
      "deviations",
      "notes",
      "blocking",
      "data"
    ],
    "properties": {
      "decision_points": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "kind",
            "question",
            "options",
            "recommendation"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
            },
            "kind": {
              "enum": [
                "decision",
                "question"
              ]
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "recommendation": {
              "type": "string",
              "minLength": 1
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            }
          }
        }
      },
      "decisions": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "question",
            "decision",
            "reason",
            "decided_by"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "decision": {
              "type": "string",
              "minLength": 1
            },
            "reason": {
              "type": "string",
              "minLength": 1
            },
            "decided_by": {
              "enum": [
                "worker",
                "main-agent",
                "developer"
              ]
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            }
          }
        }
      },
      "deviations": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "subject",
            "intended",
            "observed"
          ],
          "properties": {
            "subject": {
              "type": "string",
              "minLength": 1
            },
            "intended": {
              "type": "string",
              "minLength": 1
            },
            "observed": {
              "type": "string",
              "minLength": 1
            },
            "point": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            }
          }
        }
      },
      "notes": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "kind",
            "text",
            "data"
          ],
          "properties": {
            "kind": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*$"
            },
            "text": {
              "type": "string",
              "minLength": 1
            },
            "data": {
              "type": "object"
            }
          }
        }
      },
      "blocking": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "code",
              "detail"
            ],
            "properties": {
              "code": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9_]*$"
              },
              "detail": {
                "type": "string",
                "minLength": 1
              }
            }
          }
        ]
      },
      "data": {
        "type": "object"
      }
    },
    "$defs": {
      "answer": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "id",
          "question",
          "answer",
          "answered_by"
        ],
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
          },
          "question": {
            "type": "string",
            "minLength": 1
          },
          "answer": {
            "type": "string",
            "minLength": 1
          },
          "answered_by": {
            "enum": [
              "main-agent",
              "developer"
            ]
          }
        }
      }
    }
  },
  "semantics": "The workflow object, the top-level field workflow of a run's output, through which any Operation or execution command tells a workflow what it must know about the run without Workflows knowing that Operation or command; an output without it declares nothing and hands the script nothing. decision_points are the items the run leaves to be settled above the task before an interactive workflow goes on, each with an identity unique within the run, kind decision for a choice the run took or proposes and question for an open question it could not settle, the question, the options, the run's recommendation and optionally the Module it concerns; which of its items are decision points is the producing Operation's or command's decision, which its own Spec states. decisions are every decision the run took or followed, each with decided_by worker when the run took it itself and main-agent or developer when it follows an answer that one gave; a decision a workflow must stop for is listed both here and, with the same identity, among the decision points. deviations are the places where the run found its subject departing from what was intended, each optionally naming the decision point it concerns. notes are items for whoever reads the workflow result, which the report lists unchanged with their step and run, such as a review's verdict and findings or proposed checks, each with a kind the producing Operation or command names and a data object of its own. blocking, when not null, says that the procedure cannot go on from this run whatever its status, such as a task validation that found its workspace not ready; the report counts a last step that declared it blocked. data is handed unchanged to the workflow script in the step outcome, for the script to read the fields its procedure needs, such as the Modules a scaffold created. Answers a workflow passes to a run with --answers are a JSON list of $defs.answer, each naming by id the decision point it settles; a run that declares decision points takes them and lists the decisions that follow them with decided_by the answer's answered_by. A behaviour or field change increments the version.",
  "example": {
    "decision_points": [
      {
        "id": "d.db-helper",
        "kind": "decision",
        "question": "Does the shared database helper get a Module of its own?",
        "options": [
          "a Module of its own",
          "stay with the root"
        ],
        "recommendation": "stay with the root",
        "module": "module.shop"
      }
    ],
    "decisions": [
      {
        "id": "d.db-helper",
        "question": "Does the shared database helper get a Module of its own?",
        "options": [
          "a Module of its own",
          "stay with the root"
        ],
        "decision": "stay with the root",
        "reason": "it is 40 lines of connection setup with no behaviour of its own",
        "decided_by": "worker",
        "module": "module.shop"
      }
    ],
    "deviations": [],
    "notes": [
      {
        "kind": "proposed-check",
        "text": "pyproject.toml configures pytest for module.checkout",
        "data": {
          "id": "check.checkout.tests",
          "module": "module.checkout",
          "argv": [
            "{python}",
            "-m",
            "pytest",
            "tests/checkout"
          ],
          "timeout_seconds": 300,
          "inputs": [
            "src/checkout",
            "tests/checkout"
          ]
        }
      }
    ],
    "blocking": null,
    "data": {}
  }
}
```

## Workflow result

Printed by `concorde workflow report` and saved in the workflow's trace node, at
`<workspace folder>/workflow/reports/<n>.json` with its Markdown rendering at `<n>.md`.

```concorde-contract
{
  "id": "contract.workflows.result",
  "version": 8,
  "schema": {
    "$defs": {
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
    },
    "type": "object",
    "additionalProperties": false,
    "required": [
      "workflow",
      "workspace",
      "mode",
      "status",
      "summary",
      "steps",
      "superseded",
      "decisions",
      "decision_points",
      "deviations",
      "notes",
      "pending",
      "problems",
      "error",
      "reported_at"
    ],
    "properties": {
      "workflow": {
        "type": "string",
        "minLength": 1
      },
      "workspace": {
        "type": "string",
        "minLength": 1
      },
      "mode": {
        "enum": [
          "interactive",
          "no-ask"
        ]
      },
      "status": {
        "enum": [
          "ok",
          "awaiting_decision",
          "blocked",
          "failed",
          "running"
        ]
      },
      "summary": {
        "type": "string",
        "minLength": 1
      },
      "steps": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "key",
            "name",
            "modules",
            "run_id",
            "status",
            "summary"
          ],
          "properties": {
            "key": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
            },
            "name": {
              "type": "string",
              "pattern": "^[a-z][a-z_-]*$"
            },
            "modules": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
              }
            },
            "run_id": {
              "anyOf": [
                {
                  "type": "string",
                  "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
                },
                {
                  "type": "null"
                }
              ]
            },
            "status": {
              "enum": [
                "ok",
                "blocked",
                "failed",
                "running",
                "lost",
                "refused"
              ]
            },
            "summary": {
              "anyOf": [
                {
                  "type": "string",
                  "minLength": 1
                },
                {
                  "type": "null"
                }
              ]
            }
          }
        }
      },
      "superseded": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "key",
            "name",
            "modules",
            "run_id",
            "status",
            "summary"
          ],
          "properties": {
            "key": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
            },
            "name": {
              "type": "string",
              "pattern": "^[a-z][a-z_-]*$"
            },
            "modules": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
              }
            },
            "run_id": {
              "anyOf": [
                {
                  "type": "string",
                  "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
                },
                {
                  "type": "null"
                }
              ]
            },
            "status": {
              "enum": [
                "ok",
                "blocked",
                "failed",
                "running",
                "lost",
                "refused"
              ]
            },
            "summary": {
              "anyOf": [
                {
                  "type": "string",
                  "minLength": 1
                },
                {
                  "type": "null"
                }
              ]
            }
          }
        }
      },
      "decisions": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "id",
            "question",
            "decision",
            "reason",
            "decided_by"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
            },
            "run_id": {
              "type": "string",
              "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
            },
            "id": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "decision": {
              "type": "string",
              "minLength": 1
            },
            "reason": {
              "type": "string",
              "minLength": 1
            },
            "decided_by": {
              "enum": [
                "worker",
                "main-agent",
                "developer"
              ]
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            }
          }
        }
      },
      "decision_points": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "id",
            "kind",
            "question",
            "options",
            "recommendation"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
            },
            "run_id": {
              "type": "string",
              "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
            },
            "id": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
            },
            "kind": {
              "enum": [
                "decision",
                "question"
              ]
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "recommendation": {
              "type": "string",
              "minLength": 1
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            }
          }
        }
      },
      "deviations": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "subject",
            "intended",
            "observed"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
            },
            "run_id": {
              "type": "string",
              "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
            },
            "subject": {
              "type": "string",
              "minLength": 1
            },
            "intended": {
              "type": "string",
              "minLength": 1
            },
            "observed": {
              "type": "string",
              "minLength": 1
            },
            "point": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            }
          }
        }
      },
      "notes": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "kind",
            "text",
            "data"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
            },
            "run_id": {
              "type": "string",
              "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
            },
            "kind": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*$"
            },
            "text": {
              "type": "string",
              "minLength": 1
            },
            "data": {
              "type": "object"
            }
          }
        }
      },
      "pending": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "id",
            "kind",
            "question",
            "options",
            "recommendation"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
            },
            "run_id": {
              "type": "string",
              "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
            },
            "id": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9-]*\\.[a-z0-9-]+$"
            },
            "kind": {
              "enum": [
                "decision",
                "question"
              ]
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "recommendation": {
              "type": "string",
              "minLength": 1
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            }
          }
        }
      },
      "problems": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "status",
            "error"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:#[a-z0-9-]+)?(?:@[0-9a-f]{8})?$"
            },
            "run_id": {
              "anyOf": [
                {
                  "type": "string",
                  "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
                },
                {
                  "type": "null"
                }
              ]
            },
            "status": {
              "enum": [
                "blocked",
                "failed",
                "running",
                "lost",
                "refused"
              ]
            },
            "error": {
              "$ref": "#/$defs/error"
            }
          }
        }
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
      "reported_at": {
        "type": "string",
        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
      }
    }
  },
  "semantics": "The result of the workflow of one bound workspace, built from its workflow record and the saved run results. workspace names the workspace; mode is the mode of the latest recorded step. steps lists the current steps in the order recorded, each with the name of its Operation or execution command, its Modules, run and status: ok, blocked or failed from its result, running while its runner lives, lost without result or runner, refused without a run. superseded lists the steps a later rerun superseded, which contribute nothing else. decisions, decision_points, deviations and notes are every item of those kinds the finished current steps declared under the step output convention, exactly as their runs declared them, each with its step and run, in the order of the steps; so a decision says whether the worker took it or it follows an answer the main agent or the developer gave, and a note, such as a review's verdict or a proposed check, keeps the kind and data its run gave it. Workflows interprets none of them. pending lists the decision points of the last step an interactive run ended at that its answers did not settle, empty otherwise. problems lists every current step that did not end ok with its run's error chain unchanged, or the workflow's own link for a running, lost or refused step. status is running while a current step runs; otherwise failed when the procedure stopped at a failed, lost or refused step, blocked when it stopped at a blocked step or at a step that declared blocking, awaiting_decision when an interactive run ended at decision points, ok when its last step, as the part that registered the workflow names it, ended ok, and failed with the code incomplete when the recorded steps end before that last step, or no installed part registers the workflow, without any of these stops. error is null exactly when status is ok; otherwise it is the workflow's link, level workflow, whose causes are the errors of the steps that stopped it, unchanged, and whose evidence names a declared blocking item or every pending point. Each report is saved beside the workflow record as reports/<n>.json, with its Markdown rendering as reports/<n>.md. A behaviour or field change increments the version.",
  "example": {
    "workflow": "brownfield",
    "workspace": "adopt",
    "mode": "no-ask",
    "status": "ok",
    "summary": "workflow brownfield of workspace adopt is ok after survey ok, scaffold ok, describe:module.checkout ok, describe:module.inventory failed, describe:module.shop ok, spec_review ok, validate ok, delivery ok; 1 problem(s), 1 decision(s), 2 decision point(s), 0 deviation(s), 2 note(s)",
    "steps": [
      {
        "key": "survey",
        "name": "survey",
        "modules": [
          "module.shop"
        ],
        "run_id": "r-20260925T101500-survey-1a2b3c4d",
        "status": "ok",
        "summary": "survey finished for module.shop."
      },
      {
        "key": "scaffold",
        "name": "scaffold",
        "modules": [
          "module.shop"
        ],
        "run_id": "r-20260925T102000-scaffold-2b3c4d5e",
        "status": "ok",
        "summary": "scaffold finished for module.shop."
      },
      {
        "key": "describe:module.checkout",
        "name": "code_to_spec",
        "modules": [
          "module.checkout"
        ],
        "run_id": "r-20260925T103000-code_to_spec-5a6b7c8d",
        "status": "ok",
        "summary": "code_to_spec finished for module.checkout."
      },
      {
        "key": "describe:module.inventory",
        "name": "code_to_spec",
        "modules": [
          "module.inventory"
        ],
        "run_id": "r-20260925T104000-code_to_spec-9f8e7d6c",
        "status": "failed",
        "summary": "The worker run ended failed (worker_timeout)."
      },
      {
        "key": "describe:module.shop",
        "name": "code_to_spec",
        "modules": [
          "module.shop"
        ],
        "run_id": "r-20260925T104500-code_to_spec-3c4d5e6f",
        "status": "ok",
        "summary": "code_to_spec finished for module.shop."
      },
      {
        "key": "spec_review",
        "name": "spec_review",
        "modules": [
          "module.checkout",
          "module.inventory",
          "module.shop"
        ],
        "run_id": "r-20260925T105000-spec_review-1b2c3d4e",
        "status": "ok",
        "summary": "spec_review finished for module.checkout, module.inventory, module.shop."
      },
      {
        "key": "validate",
        "name": "task-validation",
        "modules": [
          "module.shop"
        ],
        "run_id": "r-20260925T105500-task_validation-4d5e6f7a",
        "status": "ok",
        "summary": "task-validation finished for module.shop."
      },
      {
        "key": "delivery",
        "name": "delivery",
        "modules": [
          "module.shop"
        ],
        "run_id": "r-20260925T110000-delivery-0a1b2c3d",
        "status": "ok",
        "summary": "delivery finished for module.shop."
      }
    ],
    "superseded": [],
    "decisions": [
      {
        "step": "survey",
        "run_id": "r-20260925T101500-survey-1a2b3c4d",
        "id": "d.db-helper",
        "question": "Does the shared database helper get a Module of its own?",
        "options": [
          "a Module of its own",
          "stay with the root"
        ],
        "decision": "stay with the root",
        "reason": "it is 40 lines of connection setup with no behaviour of its own",
        "decided_by": "worker",
        "module": "module.shop"
      }
    ],
    "decision_points": [
      {
        "step": "survey",
        "run_id": "r-20260925T101500-survey-1a2b3c4d",
        "id": "d.db-helper",
        "kind": "decision",
        "question": "Does the shared database helper get a Module of its own?",
        "options": [
          "a Module of its own",
          "stay with the root"
        ],
        "recommendation": "the worker chose 'stay with the root': it is 40 lines of connection setup with no behaviour of its own",
        "module": "module.shop"
      },
      {
        "step": "describe:module.checkout",
        "run_id": "r-20260925T103000-code_to_spec-5a6b7c8d",
        "id": "q.payment-retry",
        "kind": "question",
        "question": "retrying a declined payment: a declined payment is retried once after two seconds, but a timed-out one is not",
        "options": [
          "retry declined payments once, never timeouts",
          "retry both",
          "retry neither"
        ],
        "recommendation": "ask whether a timeout should be retried",
        "module": "module.checkout"
      }
    ],
    "deviations": [],
    "notes": [
      {
        "step": "survey",
        "run_id": "r-20260925T101500-survey-1a2b3c4d",
        "kind": "proposed-check",
        "text": "check.checkout.tests for module.checkout: pyproject.toml configures pytest",
        "data": {
          "id": "check.checkout.tests",
          "module": "module.checkout",
          "argv": [
            "{python}",
            "-m",
            "pytest",
            "tests/checkout"
          ],
          "timeout_seconds": 300,
          "inputs": [
            "src/checkout",
            "tests/checkout"
          ],
          "reason": "pyproject.toml configures pytest"
        }
      },
      {
        "step": "spec_review",
        "run_id": "r-20260925T105000-spec_review-1b2c3d4e",
        "kind": "review",
        "text": "spec_review verdict accepted: module.checkout accepted, module.inventory accepted, module.shop accepted",
        "data": {
          "verdict": "accepted",
          "modules": [
            {
              "module": "module.checkout",
              "outcome": "accepted",
              "blocking": 0
            },
            {
              "module": "module.inventory",
              "outcome": "accepted",
              "blocking": 0
            },
            {
              "module": "module.shop",
              "outcome": "accepted",
              "blocking": 0
            }
          ]
        }
      }
    ],
    "pending": [],
    "problems": [
      {
        "step": "describe:module.inventory",
        "run_id": "r-20260925T104000-code_to_spec-9f8e7d6c",
        "status": "failed",
        "error": {
          "level": "operation",
          "actor": "Operation code_to_spec r-20260925T104000-code_to_spec-9f8e7d6c (workspace adopt)",
          "code": "worker_timeout",
          "detail": "the code-to-spec worker run w-20260925T104001-code-to-spec-0f3b2a91 ended failed: worker_timeout: the worker did not finish within 1800 seconds",
          "evidence": [],
          "attempts": [],
          "unhandled": {
            "reason": "exhausted",
            "explanation": "the Operation passes the configured limits to Workers and does not raise them"
          },
          "options": [
            "raise limits.timeout_seconds in .concorde/workers.json",
            "run the Operation with a narrower goal"
          ],
          "recommendation": "raise limits.timeout_seconds in .concorde/workers.json",
          "causes": [
            {
              "level": "workers",
              "actor": "Workers run w-20260925T104001-code-to-spec-0f3b2a91 (code-to-spec worker)",
              "code": "worker_timeout",
              "detail": "the worker process was stopped after 1800 seconds without a result",
              "evidence": [
                {
                  "kind": "trace",
                  "ref": "w-20260925T104001-code-to-spec-0f3b2a91",
                  "detail": ""
                }
              ],
              "attempts": [],
              "unhandled": {
                "reason": "exhausted",
                "explanation": "Workers stops a worker at the configured timeout"
              },
              "options": [],
              "recommendation": "",
              "causes": []
            }
          ]
        }
      }
    ],
    "error": null,
    "reported_at": "2026-09-25T11:02:00Z"
  }
}
```

## MCP tools

The workflow part registers two tools with the
[project MCP server](../glossary.json#concept.project-mcp-server) through its
[part registration](../glossary.json#concept.part-registration); where the workflow part is not
installed, neither exists. The server runs each call as it runs every registered tool, with a
process of its own of the current Concorde, and returns its answer or refusal unchanged.

| Tool | Arguments | Result |
| --- | --- | --- |
| `workflow_step` | `request`, a [step request](#contract.workflows.step-request) as an object; optional `wait`, whole seconds from 0 to 100 (default 100) | the [step outcome](#contract.workflows.step), as [Starting a workflow step](#starting-a-workflow-step) says |
| `workflow_report` | optional `folder`, the absolute workspace folder a [workspace binding](../glossary.json#concept.workspace-binding) names as its `traces` (default: the folder the binding of the session's worktree names); optional `number` ≥ 1 | `{"folder", "number", "path", "report": <workflow result>}`, the saved [workflow result](#contract.workflows.result) of that number, the latest when no number is given |

`workflow_report` reads a saved report and builds none; it knows no task, so whoever knows a task's
workspace folder, such as the task level, which [Tasks](../coordination/tasks/module.md) shows it,
passes that folder, wherever the folder lies now.

### Starting a workflow step

`workflow_step` works on the session's worktree. When that worktree has no workspace binding, or
one that cannot be read, it is refused with `unbound_worktree` and runs nothing. Otherwise it runs
that worktree's own `concorde`, its `.concorde/bin/concorde` or, in Concorde's source checkout,
its `scripts/concorde.py` with the server's Python, as
`concorde workflow step --json <request> --wait <wait>` from the worktree's root, as a child of the
call's process with the server's environment and no standard input, and waits for it at most
`wait` plus 60 seconds. The command is a process of the server's, so the
[detached run](../glossary.json#concept.detached-run) it starts for a new step is a process of
its own and lives until its run ends, whatever becomes of the calls that asked for it or of the
session and its server. The server answers these calls each on a thread of its own, so a waiting
step never holds up the session's other calls, and allows a call's process `wait` plus 120 seconds
before it stops it.

The answer is the JSON object the command printed, unchanged, whatever its exit status: a
[step outcome](#contract.workflows.step), finished, running, lost or refused. An object without a
step outcome's `key` whose `error` is a link is the step command's refusal and is returned as the
tool's refusal, that link unchanged; output that is no JSON object is refused with `step_failed`.

### Refusals of the tools

| Code | Reason | When |
| --- | --- | --- |
| `unbound_worktree` | `environment` | `workflow_step`, or `workflow_report` without `folder`, in a session whose worktree has no usable [workspace binding](../glossary.json#concept.workspace-binding), such as the primary worktree; the detail names the worktree and, for a binding that cannot be read, its code |
| `step_failed` | `environment` | `concorde workflow step` printed no JSON object, or gave no answer within its wait and 60 seconds more; the detail carries the command, its exit status and the end of its output |
| `no_report` | `input` | `workflow_report` finds no saved workflow result in the folder, or not the one named |
| any Workflows code | as here | `concorde workflow step` refused the request or the workspace with `{"error": <link>}` and no step outcome, such as `invalid_request`; that link unchanged |

## Workflow trace

The workflow of a workspace is a [trace node](../glossary.json#concept.trace-node) of kind `workflow`, `workflow/` of the
workspace folder, and each step one of kind `step` below it, as
[Tracing](../kernel/tracing/contracts.md#contract.tracing.node) defines them; their contents are these values.

```concorde-contract
{
  "id": "contract.workflows.workflow-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "workflow",
      "steps",
      "reports"
    ],
    "properties": {
      "workflow": {
        "type": "string",
        "minLength": 1
      },
      "steps": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "key",
            "name",
            "run_id",
            "mode",
            "answers",
            "error",
            "superseded",
            "node",
            "at"
          ],
          "properties": {
            "key": {
              "type": "string",
              "minLength": 1
            },
            "name": {
              "type": "string",
              "minLength": 1
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
                  "minLength": 1,
                  "format": "project-path"
                }
              ]
            },
            "error": {
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "object"
                }
              ]
            },
            "superseded": {
              "type": "boolean"
            },
            "node": {
              "type": "string",
              "minLength": 1,
              "format": "project-path"
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
          "type": "object",
          "additionalProperties": false,
          "required": [
            "status",
            "path",
            "rendered",
            "at"
          ],
          "properties": {
            "status": {
              "type": "string",
              "minLength": 1
            },
            "path": {
              "type": "string",
              "minLength": 1,
              "format": "project-path"
            },
            "rendered": {
              "type": "string",
              "minLength": 1,
              "format": "project-path"
            },
            "at": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      }
    }
  },
  "semantics": "The data of the typed value concorde-workflow-trace, the content of a workflow's trace node, which is the workspace's workflow record. workflow names the workspace's one workflow. steps lists every step ever recorded, in order: its key, the Operation or execution command it ran, its run identity or null when it was refused, the mode it ran in, the answers file it passed (relative to the workflow's node), the refusal's error link or null, whether a later rerun superseded it, its node folder relative to the workflow's node (steps/<n>-<key>) and when it was recorded. reports lists every report with its status, the paths of its JSON and Markdown files relative to the workflow's node and when it was saved. The node's identity is the workflow name, its metadata the workspace, the workflow and the mode of the latest step, its start the first step, its status running until a report ends it ok, blocked or failed (awaiting_decision counting as blocked, with that outcome), and it is written again with every step and report. A behaviour or field change increments the version.",
  "example": {
    "workflow": "brownfield",
    "steps": [
      {
        "key": "survey",
        "name": "survey",
        "run_id": "r-20260925T100000-survey-1a2b3c4d",
        "mode": "no-ask",
        "answers": null,
        "error": null,
        "superseded": false,
        "node": "steps/1-survey",
        "at": "2026-09-25T10:00:00Z"
      }
    ],
    "reports": [
      {
        "status": "ok",
        "path": "reports/1.json",
        "rendered": "reports/1.md",
        "at": "2026-09-25T11:30:00Z"
      }
    ]
  }
}
```

```concorde-contract
{
  "id": "contract.workflows.step-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "key",
      "name",
      "run_id",
      "mode",
      "superseded",
      "state"
    ],
    "properties": {
      "key": {
        "type": "string",
        "minLength": 1
      },
      "name": {
        "type": "string",
        "minLength": 1
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
      "superseded": {
        "type": "boolean"
      },
      "state": {
        "enum": [
          "running",
          "finished",
          "lost",
          "refused"
        ]
      }
    }
  },
  "semantics": "The data of the typed value concorde-step-trace, the content of one workflow step's trace node. key is the step key, name the Operation or execution command, run_id the run it started, whose node is run/ inside this one, or null when it was refused, mode the workflow's mode, superseded whether a later rerun superseded it, and state what the step command or report last saw of its run. The node starts when the step is recorded and ends once a step or report command sees its run finished, lost or refused, with the run's status (ok, blocked or failed, failed for lost and refused) and the state as outcome; its error is the run's error, or the step's own link for a lost or refused step. A behaviour or field change increments the version.",
  "example": {
    "key": "describe:module.checkout",
    "name": "code_to_spec",
    "run_id": "r-20260925T104000-code_to_spec-5e6f7a8b",
    "mode": "no-ask",
    "superseded": false,
    "state": "finished"
  }
}
```

## Errors

The codes of links whose level is `workflow`, with the actor `workflow <name> (workspace
<workspace>)`. The refusals of the workflow record and of the runner keep their own codes as
causes.

| Code | Where | Reason | Raised when |
| --- | --- | --- | --- |
| `awaiting_decision` | result | `decision` | an interactive run ended at [decision points](../glossary.json#concept.decision-point); the evidence names each pending point |
| `step_blocked` | result | `decision` | the procedure stopped at a step that ended `blocked`, its error the cause, or at a step whose output declared it [blocking](#contract.workflows.step-output), with that declaration's code and detail as evidence |
| `step_failed` | result | `decision` | the procedure stopped at a step that ended `failed`; the step's error is the cause |
| `step_lost` | step outcome, result | `environment` | a step's run has no result and no living runner, its link carrying the end of the runner's output `host.out` as evidence and as its one cause, a `component` link of the actor `Execution runner of <run-id>` with the code `host_ended` and reason `environment`, whose detail says the runner ended without a result and gives the end of that output, `(nothing)` when it wrote none; or the script reported the key with nothing recorded |
| `step_refused` | step outcome, result | `input` | the runner rejected the step's command line (its message is the cause) or the detached runner did not start (the `detach_failed` link is the cause) |
| `step_running` | result | `exhausted` | a report was taken while a current step still runs |
| `step_rejected` | step outcome | `input` | the workflow record refused the step (`workflow_conflict`, `step_conflict`, `record_unreadable`), its `Workflows (workflow record)` link the cause; nothing was started or recorded, and the outcome has state `refused` |
| `step_unrecorded` | step outcome | `environment` | a run started but the workflow record refused to record it, its link the cause; the link names the live run |
| `workspace_retired` | step outcome | `environment` | the workflow lock's file was removed or replaced while the step command waited for it, or, once it held the lock, the worktree's binding was gone, untrusted or no longer the one the command read: whoever retired the workspace moved its folder away; a `Workflows (workflow lock)` link of code `lock_removed`, `binding_gone`, `binding_untrusted` or `binding_changed` is the cause. Nothing was started or recorded, and the outcome has state `refused`; when the step had started a run that ended before the retirement, the link names that run and so does the outcome |
| `incomplete` | result | `capability` | the recorded steps end before the procedure's last step without any of the stops above, such as a script that ended early |
| `report_failed` | report command | `capability` | the report could not be built for a reason of its own, such as a recorded result the report's contract refuses; the detail names the reason, instead of the command ending in a traceback |

The step and report commands also answer with a `component` link of the actor
`Workflows (concorde [workflow step](../glossary.json#concept.workflow-step))` or
`Workflows (concorde workflow report)`, printed as `{"error": <link>}` with exit status 1, when they
cannot work at all: `binding_required` when the worktree they start in has no
[workspace binding](../glossary.json#concept.workspace-binding), `binding_unreadable`,
`binding_invalid` or `binding_misplaced` when its binding is refused, `invalid_step_output` with
reason `input` when a finished run's output carries a `workflow` object that breaks the
[step output convention](#contract.workflows.step-output), which a report answers as
`report_failed`, and, for the report,
`no_workflow` when the workspace ran no [workflow step](../glossary.json#concept.workflow-step)
and `record_unreadable` when its workflow record cannot be read, and, for the report, `workspace_retired` with reason `environment` when the workspace was retired while it waited for the workflow lock, as for a step. A command line that breaks the
[step request](#contract.workflows.step-request) contract, or a malformed report command line, is
answered with a `component` link of
the actor `Workflows (concorde workflow)`, code `invalid_request`, reason `input`, and exit status
2.
