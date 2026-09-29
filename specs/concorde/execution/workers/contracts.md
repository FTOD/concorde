# Workers contracts

The exact answer every worker ends with, and the worker configuration file.

## Worker result

The [entry](../../glossary.json#concept.worker-result) explains the worker result's role; [the run
mechanics](launch.md#rounds) say how the host reacts to it. Its `error` is the worker's link of the
Framework's [error chain](../../tracing/contracts.md#contract.tracing.error).

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
  "semantics": "The structured result a worker returns at the end of every round, through --json-schema on Claude Code and as the argument of the concorde_result tool on pi; the host validates it against this schema on both. status ok means the worker finished its task; blocked means it cannot continue without a decision above it, such as a Spec gap or a missing grant, and failed means it tried and could not finish. summary says what was done. error is null exactly when status is ok; for blocked and failed it is the worker's own link of the error chain, the contract.tracing.error link without level, actor and causes: code names the error, detail describes it completely with the exact messages, evidence items point at a file, command, output or Spec (kind) by a path or identity (ref) with a short explanation (detail), attempts lists what was tried, unhandled gives the reason and the specific explanation why the worker could not handle it, and options and recommendation are what it offers. The error is the worker's claim, never host evidence; Workers adds the level worker, the actor and no causes when it puts it in the chain. proposed_deletions lists absolute paths in the worktree the worker wants deleted; the host deletes only those in the grant's rw list after a clean audit. output is the Operation-specific part of the answer, such as an assessment, a code change summary or review findings; the Operation supplies its schema, which the host embeds at this key in the schema it validates against and passes to --json-schema on Claude Code, and it is an empty object for Operations without one. A result whose error does not match its status is invalid. The host keeps the result verbatim in the run record.",
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

The file the [worker configuration](../../glossary.json#concept.worker-configuration) is, which
[Choosing worker models](module.md#choosing-worker-models) explains.

```concorde-contract
{
  "id": "contract.workers.worker-configuration",
  "version": 8,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version"
    ],
    "properties": {
      "schema_version": {
        "const": 1
      },
      "default": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "backend": {
            "enum": [
              "claude",
              "pi"
            ]
          },
          "model": {
            "type": "string",
            "minLength": 1,
            "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
          },
          "reasoning": {
            "type": "string",
            "minLength": 1,
            "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
          }
        },
        "anyOf": [
          {
            "required": [
              "backend"
            ]
          },
          {
            "required": [
              "model"
            ]
          },
          {
            "required": [
              "reasoning"
            ]
          }
        ]
      },
      "operations": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "default": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "backend": {
                  "enum": [
                    "claude",
                    "pi"
                  ]
                },
                "model": {
                  "type": "string",
                  "minLength": 1,
                  "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
                },
                "reasoning": {
                  "type": "string",
                  "minLength": 1,
                  "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
                }
              },
              "anyOf": [
                {
                  "required": [
                    "backend"
                  ]
                },
                {
                  "required": [
                    "model"
                  ]
                },
                {
                  "required": [
                    "reasoning"
                  ]
                }
              ]
            },
            "workers": {
              "type": "object",
              "additionalProperties": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "backend": {
                    "enum": [
                      "claude",
                      "pi"
                    ]
                  },
                  "model": {
                    "type": "string",
                    "minLength": 1,
                    "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
                  },
                  "reasoning": {
                    "type": "string",
                    "minLength": 1,
                    "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
                  }
                },
                "anyOf": [
                  {
                    "required": [
                      "backend"
                    ]
                  },
                  {
                    "required": [
                      "model"
                    ]
                  },
                  {
                    "required": [
                      "reasoning"
                    ]
                  }
                ]
              }
            }
          }
        }
      },
      "limits": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "timeout_seconds": {
            "type": "number",
            "minimum": 1
          },
          "max_turns": {
            "type": "integer",
            "minimum": 1
          },
          "max_budget_usd": {
            "type": "number",
            "minimum": 0.01
          },
          "rounds": {
            "type": "integer",
            "minimum": 0
          }
        }
      },
      "runtime": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1,
          "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
        },
        "uniqueItems": true
      }
    }
  },
  "semantics": "The worker configuration .concorde/workers.json of a worktree, tracked by Git and edited directly. schema_version is 1. default, operations.<operation>.default and operations.<operation>.workers.<worker id> each may set backend (pi or claude), model and reasoning; operation and worker names are those of the Operation catalog, and reasoning must be a level of the effective backend. For each field the most specific entry that sets it wins, except that an entry setting backend starts that program afresh, so model and reasoning come only from that entry or a more specific one. A backend no entry sets is pi, and a model or level no entry sets is the program's own default. limits sets timeout_seconds per round (default 1800), max_turns (default 200), max_budget_usd (default none) and rounds of resume (default 3) for every worker launch; runtime lists the paths Bash may read besides the grant, relative to the workspace or absolute (default .venv and node_modules, each only when it exists). A missing file means every default. Duplicate keys, unknown fields, unknown Operations or workers and levels the backend does not know are refused with config_invalid when a worker launches; so is a worktree without this file that still has the retired untracked .concorde/worker-models.json.",
  "example": {
    "schema_version": 1,
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
    },
    "limits": {
      "timeout_seconds": 1800,
      "max_turns": 200,
      "rounds": 3
    },
    "runtime": [
      ".venv",
      "node_modules",
      "docsite/node_modules"
    ]
  }
}
```
