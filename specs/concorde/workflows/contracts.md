# Workflows contracts

The exact shapes of [Workflows](module.md): what one step prints, the request a pi step agent
passes on standard input, and the workflow result. Error links follow the Framework's
[error contract](../contracts.md#contract.concorde.error), copied here as `$defs`.

## Step outcome

Printed by `concorde workflow step`, from the task record and the saved Operation result.

```concorde-contract
{
  "id": "contract.workflows.step",
  "version": 1,
  "schema": {
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
      "ready"
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
        "pattern": "^[a-z][a-z0-9_:.-]*(?:@[0-9a-f]{8})?$"
      },
      "operation": {
        "type": "string",
        "pattern": "^[a-z][a-z_]*$"
      },
      "run_id": {
        "type": "string",
        "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
      },
      "state": {
        "enum": [
          "running",
          "finished"
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
        "type": "string",
        "minLength": 1
      },
      "decision_points": {
        "type": "integer",
        "minimum": 0
      },
      "created_modules": {
        "type": "array",
        "items": {
          "type": "string",
          "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
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
      }
    }
  },
  "semantics": "The outcome of one workflow step. key is the step key, including the answers digest when answers were passed. run_id names the Operation run recorded for the key and result_path where its Operation result is or will be saved. state is running while the run has no result yet, and status and summary are then null; once finished they are the result's. decision_points counts the result's open questions, and for a survey also its decisions not decided by the developer. created_modules lists the Modules a scaffold created, empty for any other Operation. ready is a validate result's readiness and null otherwise. A behaviour or field change increments the version.",
  "example": {
    "workflow": "brownfield",
    "task": "adopt",
    "key": "survey",
    "operation": "survey",
    "run_id": "r-20260925T101500-survey-1a2b3c4d",
    "state": "finished",
    "status": "ok",
    "summary": "proposed 2 child Module(s) of module.shop with 1 decision and 0 open question(s)",
    "result_path": ".concorde/runs/r-20260925T101500-survey-1a2b3c4d/result.json",
    "decision_points": 1,
    "created_modules": [],
    "ready": null
  }
}
```

## Step request

What `concorde workflow step --stdin` reads, and what the pi step agent receives as its task.

```concorde-contract
{
  "id": "contract.workflows.step-request",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "task",
      "workflow",
      "mode",
      "key",
      "argv",
      "answers",
      "retry"
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
        "pattern": "^[a-z][a-z0-9_:.-]*(?:@[0-9a-f]{8})?$"
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
      }
    }
  },
  "semantics": "One step request: the task, workflow, mode and step key, argv as the Operation name followed by its arguments without --task, answers to pass to the run or null, and retry to start a new run for a key whose recorded run did not end ok. It carries the same meaning as the options of the command line. A behaviour or field change increments the version.",
  "example": {
    "task": "adopt",
    "workflow": "brownfield",
    "mode": "no-ask",
    "key": "describe:module.checkout",
    "argv": [
      "code_to_spec",
      "--modules",
      "module.checkout"
    ],
    "answers": null,
    "retry": false
  }
}
```

## Workflow result

Printed by `concorde workflow report` and saved at `.concorde/tasks/<task-id>.workflow.json`.

```concorde-contract
{
  "id": "contract.workflows.result",
  "version": 1,
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
      "decisions",
      "open_questions",
      "deviations",
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
          "failed"
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
              "pattern": "^[a-z][a-z0-9_:.-]*(?:@[0-9a-f]{8})?$"
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
              "type": "string",
              "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"
            },
            "status": {
              "enum": [
                "ok",
                "blocked",
                "failed",
                "running",
                "lost"
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
            "kind",
            "id",
            "module",
            "question",
            "options",
            "chosen",
            "recommendation"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:@[0-9a-f]{8})?$"
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
            "chosen": {
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
            "recommendation": {
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
      "open_questions": {
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
            "chosen",
            "recommendation"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:@[0-9a-f]{8})?$"
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
            "chosen": {
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
            "recommendation": {
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
              "pattern": "^[a-z][a-z0-9_:.-]*(?:@[0-9a-f]{8})?$"
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
            "chosen",
            "recommendation"
          ],
          "properties": {
            "step": {
              "type": "string",
              "pattern": "^[a-z][a-z0-9_:.-]*(?:@[0-9a-f]{8})?$"
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
            "chosen": {
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
            "recommendation": {
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
              "pattern": "^[a-z][a-z0-9_:.-]*(?:@[0-9a-f]{8})?$"
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
                "lost"
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
  "semantics": "The result of a workflow run in one task. steps lists every recorded step in order with its run and status; a step whose run has no result and no running host is lost. decisions and open_questions gather every decision and open question of every finished step, each with its step and run, and deviations every deviation. pending lists the decision points an interactive run ended at, and is empty otherwise. problems lists every step that did not end ok, each with its Operation's error chain unchanged, or for a lost or running step the workflow's own link describing it. status is ok when the procedure's last step ended ok, awaiting_decision when an interactive run ended at decision points, blocked when it stopped at a blocked step or an unready validation, and failed when it stopped at a failed or lost step. error is null exactly when status is ok; otherwise it is the workflow's link, level workflow, whose causes are the errors of the steps that stopped it, unchanged. A behaviour or field change increments the version.",
  "example": {
    "workflow": "brownfield",
    "task": "adopt",
    "mode": "no-ask",
    "status": "ok",
    "summary": "described module.shop and 2 created Module(s); delivered; 1 Module's description is blocked; 1 decision and 1 open question reported",
    "steps": [
      {
        "key": "survey",
        "operation": "survey",
        "modules": [
          "module.shop"
        ],
        "run_id": "r-20260925T101500-survey-1a2b3c4d",
        "status": "ok",
        "summary": "proposed 2 child Module(s)"
      },
      {
        "key": "describe:module.inventory",
        "operation": "code_to_spec",
        "modules": [
          "module.inventory"
        ],
        "run_id": "r-20260925T104000-code_to_spec-9f8e7d6c",
        "status": "blocked",
        "summary": "1 new structural error"
      },
      {
        "key": "delivery",
        "operation": "delivery",
        "modules": [
          "module.shop"
        ],
        "run_id": "r-20260925T110000-delivery-0a1b2c3d",
        "status": "ok",
        "summary": "committed the task's changes"
      }
    ],
    "decisions": [
      {
        "step": "survey",
        "run_id": "r-20260925T101500-survey-1a2b3c4d",
        "kind": "decision",
        "id": "d.db-helper",
        "module": "module.shop",
        "question": "Does the shared database helper get a Module of its own?",
        "options": [
          "a Module of its own",
          "stay with the root"
        ],
        "chosen": "stay with the root",
        "recommendation": null
      }
    ],
    "open_questions": [
      {
        "step": "describe:module.checkout",
        "run_id": "r-20260925T103000-code_to_spec-5a6b7c8d",
        "kind": "open_question",
        "id": "q.payment-retry",
        "module": "module.checkout",
        "question": "retrying a declined payment",
        "options": [
          "retry declined payments once, never timeouts",
          "retry both",
          "retry neither"
        ],
        "chosen": null,
        "recommendation": "ask whether a timeout should be retried"
      }
    ],
    "deviations": [],
    "pending": [],
    "problems": [
      {
        "step": "describe:module.inventory",
        "run_id": "r-20260925T104000-code_to_spec-9f8e7d6c",
        "status": "blocked",
        "error": {
          "level": "operation",
          "actor": "Operation code_to_spec r-20260925T104000-code_to_spec-9f8e7d6c (task adopt)",
          "code": "new_structural_errors",
          "detail": "the change to module.inventory adds 1 structural error: CHK.scenario.steps in specs/shop/inventory/scenarios.md: scenario.inventory.hold has no THEN step",
          "evidence": [
            {
              "kind": "finding",
              "ref": "specs/shop/inventory/scenarios.md",
              "detail": "CHK.scenario.steps"
            }
          ],
          "attempts": [],
          "unhandled": {
            "reason": "decision",
            "explanation": "a Spec that fails a structural check is repaired by a decision, not by another worker round"
          },
          "options": [
            "repair the scenario",
            "run code_to_spec again for module.inventory"
          ],
          "recommendation": "repair the scenario",
          "causes": []
        }
      }
    ],
    "error": null,
    "reported_at": "2026-09-25T11:02:00Z"
  }
}
```
