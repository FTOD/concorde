# Workflows contracts

The exact shapes of [Workflows](module.md): what one step prints, the request a pi step agent
passes on standard input, the workflow result, and the error codes of the workflow's own links.
Error links follow the Framework's [error contract](../contracts.md#contract.concorde.error),
copied here as `$defs`.

## Step outcome

Printed by `concorde workflow step`, from the task record and the saved Operation result.

```concorde-contract
{
  "id": "contract.workflows.step",
  "version": 2,
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
    },
    "type": "object",
    "additionalProperties": false,
    "required": [
      "workflow",
      "task",
      "key",
      "operation",
      "run_id",
      "state",
      "status",
      "summary",
      "result_path",
      "decision_points",
      "created_modules",
      "ready",
      "error"
    ],
    "properties": {
      "workflow": {
        "type": "string",
        "minLength": 1
      },
      "task": {
        "type": "string",
        "minLength": 1
      },
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
      "created_modules": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "id",
            "uses"
          ],
          "properties": {
            "id": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "uses": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
              }
            }
          }
        }
      },
      "ready": {
        "anyOf": [
          {
            "type": "boolean"
          },
          {
            "type": "null"
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
      }
    }
  },
  "semantics": "The outcome of one workflow step. key is the step key, including the answers digest when answers were passed. run_id names the Operation run recorded for the key, null for a refused step, and result_path where its Operation result is or will be saved. state is running while the run has no result and its host lives, finished once it has a result, lost when it has neither a result nor a living host, and refused when the run could not start; status and summary are the result's once finished and null otherwise. decision_points counts the result's open questions, and for a survey also its decisions decided by the worker. created_modules lists the Modules a scaffold created, each with the other created Modules it uses, empty for any other Operation. decision_points leaves out the points the step's own answers settle. ready is a validate result's readiness and null otherwise. error is null for running and finished, and the workflow's link for lost and refused. A behaviour or field change increments the version.",
  "example": {
    "workflow": "brownfield",
    "task": "adopt",
    "key": "survey",
    "operation": "survey",
    "run_id": "r-20260925T101500-survey-1a2b3c4d",
    "state": "finished",
    "status": "ok",
    "summary": "survey finished for module.shop.",
    "result_path": ".concorde/runs/r-20260925T101500-survey-1a2b3c4d/result.json",
    "decision_points": 1,
    "created_modules": [],
    "ready": null,
    "error": null
  }
}
```

## Step request

What `concorde workflow step --stdin` reads, and what the pi step agent receives as its task.

```concorde-contract
{
  "id": "contract.workflows.step-request",
  "version": 3,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "task",
      "workflow",
      "mode",
      "key",
      "argv"
    ],
    "properties": {
      "task": {
        "type": "string",
        "minLength": 1
      },
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
                "answer"
              ],
              "properties": {
                "id": {
                  "type": "string",
                  "pattern": "^[dq]\\.[a-z0-9-]+$"
                },
                "question": {
                  "type": "string",
                  "minLength": 1
                },
                "answer": {
                  "type": "string",
                  "minLength": 1
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
  "semantics": "One step request, with the meaning of the command line's options: the task, workflow, mode and base step key, argv as the Operation name followed by its arguments without --task, answers as the list of every answer given for this step so far or null, retry to start a new run for a key whose current step did not end ok, and restart, a short generation label or null, to start the step again whatever its outcome: the label is part of the step key, so the restarted step supersedes the earlier one and every later step once, and a relaunch with the same label finds it again. answers, retry and restart are optional and mean null, false and null when left out; the workflow scripts leave them out whenever they hold that value, so that a step agent that retypes the request has less to copy. A behaviour or field change increments the version.",
  "example": {
    "task": "adopt",
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
        "answer": "a Module of its own"
      }
    ],
    "retry": false,
    "restart": null
  }
}
```

## Workflow result

Printed by `concorde workflow report` and saved at `.concorde/tasks/<task-id>.workflow.json`.

```concorde-contract
{
  "id": "contract.workflows.result",
  "version": 3,
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
    },
    "type": "object",
    "additionalProperties": false,
    "required": [
      "workflow",
      "task",
      "mode",
      "status",
      "summary",
      "steps",
      "superseded",
      "decisions",
      "open_questions",
      "deviations",
      "reviews",
      "proposed_checks",
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
      "task": {
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
            "operation",
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
            "operation": {
              "type": "string",
              "pattern": "^[a-z][a-z_]*$"
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
            "operation",
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
            "operation": {
              "type": "string",
              "pattern": "^[a-z][a-z_]*$"
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
            "module",
            "question",
            "options",
            "chosen",
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
              "pattern": "^d\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "question": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "minItems": 2,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "chosen": {
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
                "developer"
              ]
            }
          }
        }
      },
      "open_questions": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "id",
            "module",
            "subject",
            "observed",
            "evidence",
            "why_uncertain",
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
              "pattern": "^q\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "subject": {
              "type": "string",
              "minLength": 1
            },
            "observed": {
              "type": "string",
              "minLength": 1
            },
            "evidence": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "why_uncertain": {
              "type": "string",
              "minLength": 1
            },
            "options": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "recommendation": {
              "type": "string",
              "minLength": 1
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
            "module",
            "question",
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
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "question": {
              "type": "string",
              "pattern": "^q\\.[a-z0-9-]+$"
            },
            "intended": {
              "type": "string",
              "minLength": 1
            },
            "observed": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "reviews": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "verdict",
            "modules"
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
            "verdict": {
              "enum": [
                "accepted",
                "changes_required",
                "incomplete"
              ]
            },
            "modules": {
              "type": "array",
              "items": {
                "type": "object"
              }
            }
          }
        }
      },
      "proposed_checks": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "step",
            "run_id",
            "id",
            "module",
            "argv",
            "timeout_seconds",
            "inputs",
            "reason"
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
              "pattern": "^check\\.[a-z0-9-]+(?:\\.[a-z0-9-]+)*$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
            },
            "argv": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "env": {
              "type": "object",
              "additionalProperties": {
                "type": "string",
                "minLength": 1
              }
            },
            "timeout_seconds": {
              "type": "integer",
              "minimum": 1
            },
            "inputs": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "reason": {
              "type": "string",
              "minLength": 1
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
            "kind",
            "id",
            "module",
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
            "kind": {
              "enum": [
                "decision",
                "open_question"
              ]
            },
            "id": {
              "type": "string",
              "pattern": "^[dq]\\.[a-z0-9-]+$"
            },
            "module": {
              "type": "string",
              "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
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
  "semantics": "The result of a workflow in one task, built from the task record and the saved Operation results. steps lists the current steps in the order recorded, each with its run and status: ok, blocked or failed from its result, running while its host lives, lost without result or host, refused without a run. superseded lists the steps a later rerun superseded, which contribute nothing else. decisions and open_questions are every decision and open question of the finished current steps exactly as their Operations reported them, with their step and run; deviations likewise. reviews holds each spec_review step's verdict and per-Module outcomes as it reported them. proposed_checks are the checks the survey proposed, which nothing has configured. pending lists the decision points an interactive run ended at, empty otherwise. problems lists every current step that did not end ok with its Operation's error chain unchanged, or the workflow's own link for a running, lost or refused step. status is running while a current step runs; otherwise failed when the procedure stopped at a failed, lost or refused step, blocked when it stopped at a blocked step or unready validation, awaiting_decision when an interactive run ended at decision points, and ok when its last step ended ok. error is null exactly when status is ok; otherwise it is the workflow's link, level workflow, whose causes are the errors of the steps that stopped it, unchanged. A proposed check keeps the env it was proposed with. A behaviour or field change increments the version.",
  "example": {
    "workflow": "brownfield",
    "task": "adopt",
    "mode": "no-ask",
    "status": "ok",
    "summary": "brownfield described module.shop and 2 created Module(s) and delivered them; 1 problem, 1 decision, 1 open question and 1 proposed check to review",
    "steps": [
      {
        "key": "survey",
        "operation": "survey",
        "modules": [
          "module.shop"
        ],
        "run_id": "r-20260925T101500-survey-1a2b3c4d",
        "status": "ok",
        "summary": "survey finished for module.shop."
      },
      {
        "key": "describe:module.checkout",
        "operation": "code_to_spec",
        "modules": [
          "module.checkout"
        ],
        "run_id": "r-20260925T103000-code_to_spec-5a6b7c8d",
        "status": "ok",
        "summary": "code_to_spec finished for module.checkout."
      },
      {
        "key": "describe:module.inventory",
        "operation": "code_to_spec",
        "modules": [
          "module.inventory"
        ],
        "run_id": "r-20260925T104000-code_to_spec-9f8e7d6c",
        "status": "failed",
        "summary": "The worker run ended failed (worker_timeout)."
      },
      {
        "key": "delivery",
        "operation": "delivery",
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
        "module": "module.shop",
        "question": "Does the shared database helper get a Module of its own?",
        "options": [
          "a Module of its own",
          "stay with the root"
        ],
        "chosen": "stay with the root",
        "reason": "it is 40 lines of connection setup with no behaviour of its own",
        "decided_by": "worker"
      }
    ],
    "open_questions": [
      {
        "step": "describe:module.checkout",
        "run_id": "r-20260925T103000-code_to_spec-5a6b7c8d",
        "id": "q.payment-retry",
        "module": "module.checkout",
        "subject": "retrying a declined payment",
        "observed": "a declined payment is retried once after two seconds, but a timed-out one is not",
        "evidence": [
          "src/checkout/payment.py"
        ],
        "why_uncertain": "no comment, test or configuration says whether the difference is intended",
        "options": [
          "retry declined payments once, never timeouts",
          "retry both",
          "retry neither"
        ],
        "recommendation": "ask whether a timeout should be retried"
      }
    ],
    "deviations": [],
    "reviews": [
      {
        "step": "spec_review",
        "run_id": "r-20260925T105000-spec_review-1b2c3d4e",
        "verdict": "accepted",
        "modules": []
      }
    ],
    "proposed_checks": [
      {
        "step": "survey",
        "run_id": "r-20260925T101500-survey-1a2b3c4d",
        "id": "check.checkout.tests",
        "module": "module.checkout",
        "argv": [
          "python",
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
    ],
    "pending": [],
    "problems": [
      {
        "step": "describe:module.inventory",
        "run_id": "r-20260925T104000-code_to_spec-9f8e7d6c",
        "status": "failed",
        "error": {
          "level": "operation",
          "actor": "Operation code_to_spec r-20260925T104000-code_to_spec-9f8e7d6c (task adopt)",
          "code": "worker_timeout",
          "detail": "the code-to-spec worker run w-20260925T104001-code-to-spec-0f3b2a91 ended failed: worker_timeout: the worker did not finish within 1800 seconds",
          "evidence": [],
          "attempts": [],
          "unhandled": {
            "reason": "exhausted",
            "explanation": "the Operation passes the configured limits to Workers and does not raise them"
          },
          "options": [
            "raise workers.timeout_seconds",
            "run the Operation with a narrower goal"
          ],
          "recommendation": "raise workers.timeout_seconds",
          "causes": [
            {
              "level": "harness",
              "actor": "Workers run w-20260925T104001-code-to-spec-0f3b2a91 (code-to-spec worker)",
              "code": "worker_timeout",
              "detail": "the worker process was stopped after 1800 seconds without a result",
              "evidence": [
                {
                  "kind": "run-record",
                  "ref": ".concorde/runs/w-20260925T104001-code-to-spec-0f3b2a91/record.json",
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

## Errors

The codes of links whose level is `workflow`, with the actor `workflow <name> (task <task-id>)`.
The step command's refusals by Tasks and by `concorde run` keep their own codes as causes.

| Code | Where | Reason | Raised when |
| --- | --- | --- | --- |
| `awaiting_decision` | result | `decision` | an interactive run ended at decision points; the evidence names each pending point |
| `step_blocked` | result | `decision` | the procedure stopped at a step that ended `blocked`, or at a validation that was not ready; the step's error is the cause |
| `step_failed` | result | `decision` | the procedure stopped at a step that ended `failed`; the step's error is the cause |
| `step_lost` | step outcome, result | `environment` | a step's run has no result and no living host, its link carrying the end of the host's output as evidence and cause; or the script reported the key with nothing recorded |
| `step_refused` | step outcome, result | `input` | `concorde run` rejected the step's command line (its message is the cause) or its detached host did not start (the `detach_failed` link is the cause) |
| `step_running` | result | `exhausted` | a report was taken while a current step still runs |
| `step_rejected` | step outcome | `input` | Tasks refused the step (`workflow_conflict`, `step_conflict`, `task_closed`, `unknown_task`), its link the cause; nothing was started or recorded, and the outcome has state `refused` |
| `step_unrecorded` | step outcome | `environment` | a run started but Tasks refused to record it, its link the cause; the link names the live run |
| `incomplete` | result | `capability` | the recorded steps end before the procedure's last step without any of the stops above, such as a script that ended early |
| `invalid_request` | step command | `input` | the step command line or standard-input request breaks the step request contract; exit status 2 |
| `report_failed` | report command | `capability` | the report could not be built for a reason of its own, such as a recorded result the report's contract refuses; the detail names the reason, instead of the command ending in a traceback |
