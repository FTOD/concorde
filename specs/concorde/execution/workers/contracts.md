# Workers contracts

The exact answer every worker ends with, and what `concorde configure-workers` prints.

## Worker result

The [entry](module.md#concept.workers.worker-result) explains the worker result's role; [the run
mechanics](launch.md#rounds) say how the host reacts to it. Its `error` is the worker's link of the
Framework's [error chain](../../contracts.md#contract.concorde.error).

```concorde-contract
{
  "id": "contract.workers.worker-result",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "status",
      "summary",
      "error",
      "proposed_deletions",
      "output"
    ],
    "properties": {
      "status": {
        "enum": [
          "ok",
          "blocked",
          "failed"
        ]
      },
      "summary": {
        "type": "string",
        "minLength": 1
      },
      "error": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "code",
              "detail",
              "evidence",
              "attempts",
              "unhandled",
              "options",
              "recommendation"
            ],
            "properties": {
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
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "kind",
                    "ref",
                    "detail"
                  ],
                  "properties": {
                    "kind": {
                      "enum": [
                        "file",
                        "command",
                        "output",
                        "spec"
                      ]
                    },
                    "ref": {
                      "type": "string",
                      "minLength": 1
                    },
                    "detail": {
                      "type": "string"
                    }
                  }
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
              "options": {
                "type": "array",
                "items": {
                  "type": "string",
                  "minLength": 1
                }
              },
              "recommendation": {
                "type": "string"
              }
            }
          }
        ]
      },
      "proposed_deletions": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "output": {
        "type": "object"
      }
    }
  },
  "semantics": "The structured result a worker returns through --json-schema at the end of every round. status ok means the worker finished its task; blocked means it cannot continue without a decision above it, such as a Spec gap or a missing grant, and failed means it tried and could not finish. summary says what was done. error is null exactly when status is ok; for blocked and failed it is the worker's own link of the error chain, the contract.concorde.error link without level, actor and causes: code names the error, detail describes it completely with the exact messages, evidence items point at a file, command, output or Spec (kind) by a path or identity (ref) with a short explanation (detail), attempts lists what was tried, unhandled gives the reason and the specific explanation why the worker could not handle it, and options and recommendation are what it offers. The error is the worker's claim, never host evidence; Workers adds the level worker, the actor and no causes when it puts it in the chain. proposed_deletions lists absolute paths in the worktree the worker wants deleted; the host deletes only those in the grant's rw list after a clean audit. output is the Operation-specific part of the answer, such as an assessment, a code change summary or review findings; the Operation supplies its schema, which the host embeds at this key in the schema it passes to --json-schema, and it is an empty object for Operations without one. A result whose error does not match its status is invalid. The host keeps the result verbatim in the run record.",
  "example": {
    "status": "blocked",
    "summary": "Added discount rules to the cart; the rounding rule is not specified.",
    "error": {
      "code": "spec_gap",
      "detail": "req.shop.discount-total in specs/shop/requirements.md states the discounted total but not whether discounts are rounded per line or per order; src/shop/discounts.py needs one of the two to compute invoice lines.",
      "evidence": [
        {
          "kind": "spec",
          "ref": "req.shop.discount-total",
          "detail": "states the total but not the rounding"
        }
      ],
      "attempts": [
        "Searched the Module's requirements and scenarios for rounding",
        "Read the invoice scenario, which shows only whole-order totals"
      ],
      "unhandled": {
        "reason": "decision",
        "explanation": "what the shop Module promises about rounding is the Spec's to state; inferring it from code is forbidden"
      },
      "options": [
        "Round per line",
        "Round per order"
      ],
      "recommendation": "Round per order, as the invoice scenario implies."
    },
    "proposed_deletions": [],
    "output": {}
  }
}
```

## Worker configuration

The output of [`concorde configure-workers`](module.md#concept.workers.configure-workers), inside
its [command result](#contract.workers.configure-workers-result).

```concorde-contract
{
  "id": "contract.workers.worker-configuration",
  "version": 7,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "action",
      "worktree",
      "config",
      "configured",
      "effective"
    ],
    "properties": {
      "action": {
        "enum": [
          "show",
          "check"
        ]
      },
      "worktree": {
        "type": "string",
        "minLength": 1
      },
      "config": {
        "type": "string",
        "minLength": 1
      },
      "configured": {
        "type": "object"
      },
      "effective": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "backend",
              "backend_source",
              "model",
              "reasoning",
              "model_source",
              "reasoning_source"
            ],
            "properties": {
              "backend": {
                "enum": [
                  "claude",
                  "pi"
                ]
              },
              "backend_source": {
                "type": "string",
                "minLength": 1
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
              "reasoning": {
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
              "model_source": {
                "type": "string",
                "minLength": 1
              },
              "reasoning_source": {
                "type": "string",
                "minLength": 1
              }
            }
          }
        }
      }
    }
  },
  "semantics": "Read-only output of configure-workers --show or --check. action names the inspection. worktree and config identify the current Git worktree and its source file. configured is the validated JSON file (schema_version 3 when absent). effective maps every catalog Operation and worker id to its resolved backend, model and reasoning with each source. Resolution is sparse and field by field; an explicit backend resets inherited model and reasoning. No discovery, backend installation or credentials are required. No file, task or run record is written. Model names are accepted without discovery; structural, catalog and backend reasoning vocabulary errors fail validation. A behaviour or field change increments the version.",
  "example": {
    "worktree": "/work/shop",
    "config": "/work/shop/.concorde/worker-models.json",
    "configured": {
      "schema_version": 3,
      "default": {
        "model": "anthropic/claude-sonnet-5",
        "reasoning": "medium"
      },
      "operations": {
        "spec_panel": {
          "workers": {
            "reviewer2": {
              "model": "local-openai/gpt-6",
              "reasoning": "high"
            },
            "chair": {
              "backend": "claude",
              "model": "opus"
            }
          }
        }
      }
    },
    "effective": {
      "implement": {
        "worker": {
          "backend": "pi",
          "backend_source": "Concorde's default worker backend",
          "model": "anthropic/claude-sonnet-5",
          "reasoning": "medium",
          "model_source": "default",
          "reasoning_source": "default"
        }
      },
      "spec_review": {
        "reviewer": {
          "backend": "pi",
          "backend_source": "Concorde's default worker backend",
          "model": "anthropic/claude-sonnet-5",
          "reasoning": "medium",
          "model_source": "default",
          "reasoning_source": "default"
        },
        "checker": {
          "backend": "pi",
          "backend_source": "Concorde's default worker backend",
          "model": "anthropic/claude-sonnet-5",
          "reasoning": "medium",
          "model_source": "default",
          "reasoning_source": "default"
        }
      },
      "spec_panel": {
        "reviewer1": {
          "backend": "pi",
          "backend_source": "Concorde's default worker backend",
          "model": "anthropic/claude-sonnet-5",
          "reasoning": "medium",
          "model_source": "default",
          "reasoning_source": "default"
        },
        "reviewer2": {
          "backend": "pi",
          "backend_source": "Concorde's default worker backend",
          "model": "local-openai/gpt-6",
          "reasoning": "high",
          "model_source": "operations.spec_panel.workers.reviewer2",
          "reasoning_source": "operations.spec_panel.workers.reviewer2"
        },
        "chair": {
          "backend": "claude",
          "backend_source": "operations.spec_panel.workers.chair",
          "model": "opus",
          "reasoning": null,
          "model_source": "operations.spec_panel.workers.chair",
          "reasoning_source": "the backend's own default"
        }
      }
    },
    "action": "show"
  }
}
```

## Command result of configure-workers

What read-only inspection prints with `--json`, including a refused validation.
The interactive editor uses a terminal screen and writes only on Save.

```concorde-contract
{
  "id": "contract.workers.configure-workers-result",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "command",
      "status",
      "output",
      "evidence",
      "error"
    ],
    "properties": {
      "command": {
        "const": "configure-workers"
      },
      "status": {
        "enum": [
          "ok",
          "failed"
        ]
      },
      "output": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object"
          }
        ]
      },
      "evidence": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/evidence"
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
  "semantics": "JSON result printed only for --show --json or --check --json. command is configure-workers. status ok returns contract.workers.worker-configuration in output and exit status 0; failed returns output null and the full command error chain with exit status 1. Error configuration_refused carries the Workers component cause, including config_invalid for bad structure or catalog names. The file remains unchanged. Malformed options, a nonterminal editor invocation or a directory outside Git print {\"error\": <link>} and exit 2. With no flags an interactive terminal opens a draft editor, not JSON output; Save validates and atomically writes; a dirty Cancel, q, Escape or Ctrl-C offers Keep editing by default or explicit Discard changes, while a clean exit needs no prompt. Scope and model search uses / and returning from Edit preserves the selected scope and filter. --show and --check without --json print human-readable inspection. No run is recorded. A behaviour or field change increments the version.",
  "example": {
    "command": "configure-workers",
    "status": "failed",
    "output": null,
    "evidence": [
      {
        "kind": "worker-models",
        "ref": "/home/dev/shop/.concorde/worker-models.json",
        "detail": "config_invalid: unknown worker reviewer6 of spec_panel"
      }
    ],
    "error": {
      "level": "command",
      "actor": "concorde configure-workers (/home/dev/shop)",
      "code": "configuration_refused",
      "detail": "configure-workers could not complete for /home/dev/shop/.concorde/worker-models.json: config_invalid: unknown worker reviewer6 of spec_panel",
      "evidence": [
        {
          "kind": "worker-models",
          "ref": "/home/dev/shop/.concorde/worker-models.json",
          "detail": "config_invalid: unknown worker reviewer6 of spec_panel"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "input",
        "explanation": "the command neither guesses a program or model nor repairs the configuration or the installed program"
      },
      "options": [
        "edit .concorde/worker-models.json and run concorde configure-workers --check"
      ],
      "recommendation": "edit .concorde/worker-models.json and run concorde configure-workers --check",
      "causes": [
        {
          "level": "component",
          "actor": "Workers (worker model configuration)",
          "code": "config_invalid",
          "detail": "unknown worker reviewer6 of spec_panel",
          "evidence": [],
          "attempts": [],
          "unhandled": {
            "reason": "input",
            "explanation": "the file must name a catalog worker"
          },
          "options": [
            "edit .concorde/worker-models.json and run concorde configure-workers --check"
          ],
          "recommendation": "",
          "causes": []
        }
      ]
    }
  }
}
```
