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
  "version": 6,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "action",
      "backend",
      "backend_from",
      "worktree",
      "config",
      "changed",
      "candidates",
      "configured",
      "effective"
    ],
    "properties": {
      "action": {
        "enum": [
          "list",
          "set",
          "unset"
        ]
      },
      "backend": {
        "enum": [
          "claude",
          "pi"
        ]
      },
      "backend_from": {
        "type": "string",
        "minLength": 1
      },
      "worktree": {
        "type": "string",
        "minLength": 1
      },
      "config": {
        "type": "string",
        "minLength": 1
      },
      "changed": {
        "type": "boolean"
      },
      "candidates": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object"
          }
        ]
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
  "semantics": "The output of concorde configure-workers. action is list when the run changed nothing, set when it set a backend, model or level, unset when it removed an entry. backend is the program whose candidates were listed or against which a change was checked: the program the named entry (the default, an Operation's default or one worker's) runs on once the change is applied, pi when no entry chooses one, or for a listing the program --candidates names; backend_from says which: --backend, the entry that chose it (such as operations.spec_panel.workers.chair), --candidates, or Concorde's default worker backend. worktree is the worktree whose configuration file config was read or changed, the Git worktree the command ran in: the primary worktree, whose file new task worktrees inherit, or a task worktree, whose own copy only it reads; changed says whether the file changed. candidates is null for unset and otherwise the listing of the installed program: backend, program, version, complete (false for Claude Code, which cannot list an account's models), reasoning_flag, reasoning_levels, models (each with id, source, reasoning, levels and a note, and for pi context, max_output and images) and a note. configured is the file as written after the change. effective maps every catalog Operation that launches workers to its worker ids, each with the backend that worker runs on and the entry it came from (or Concorde's default worker backend), and the model and reasoning level it runs with and the entry each came from, or null with the source \"the backend's own default\". A behaviour or field change increments the version.",
  "example": {
    "action": "set",
    "backend": "pi",
    "backend_from": "Concorde's default worker backend",
    "worktree": "/work/shop",
    "config": "/work/shop/.concorde/worker-models.json",
    "changed": true,
    "candidates": {
      "backend": "pi",
      "program": "/usr/local/bin/pi",
      "version": "0.87.1",
      "complete": true,
      "reasoning_flag": "--thinking",
      "reasoning_levels": [
        "off",
        "minimal",
        "low",
        "medium",
        "high",
        "xhigh",
        "max"
      ],
      "models": [
        {
          "id": "anthropic/claude-sonnet-5",
          "source": "pi --list-models",
          "reasoning": true,
          "levels": [
            "off",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max"
          ],
          "context": "1M",
          "max_output": "128K",
          "images": true,
          "note": ""
        }
      ],
      "note": "pi lists the models it has credentials for in ~/.pi/agent; workers get a copy of its auth.json and models.json."
    },
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
    }
  }
}
```

## Command result of configure-workers

What the command prints on standard output for every well-formed command line, whether it listed,
changed or refused.

```concorde-contract
{
  "id": "contract.workers.configure-workers-result",
  "version": 1,
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
  "semantics": "What concorde configure-workers prints on standard output. command is always configure-workers. status is ok when the listing or change succeeded and failed when the request was refused, in which case the configuration file is unchanged. output is the worker configuration (contract.workers.worker-configuration) when the status is ok and null otherwise. evidence names the configuration file and what was done to it. error is null exactly when the status is ok; otherwise it is the command's own error link, level command, actor concorde configure-workers (<worktree>), code invalid_request or configuration_refused, whose cause for configuration_refused is the component link of Workers' model configuration. The command writes no run record. A malformed command line prints {\"error\": <link>} with exit status 2. A behaviour or field change increments the version.",
  "example": {
    "command": "configure-workers",
    "status": "failed",
    "output": null,
    "evidence": [
      {
        "kind": "worker-models",
        "ref": "/home/dev/shop/.concorde/worker-models.json",
        "detail": "unknown_model: no-such-model is not a model pi lists"
      }
    ],
    "error": {
      "level": "command",
      "actor": "concorde configure-workers (/home/dev/shop)",
      "code": "configuration_refused",
      "detail": "configure-workers could not complete for /home/dev/shop/.concorde/worker-models.json: unknown_model: no-such-model is not a model pi lists",
      "evidence": [
        {
          "kind": "worker-models",
          "ref": "/home/dev/shop/.concorde/worker-models.json",
          "detail": "unknown_model: no-such-model is not a model pi lists"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "input",
        "explanation": "the command neither guesses a program or model nor repairs the configuration or the installed program"
      },
      "options": [
        "choose a model from the candidates concorde configure-workers lists"
      ],
      "recommendation": "choose a model from the candidates concorde configure-workers lists",
      "causes": [
        {
          "level": "component",
          "actor": "Workers (worker model configuration)",
          "code": "unknown_model",
          "detail": "no-such-model is not a model pi lists",
          "evidence": [],
          "attempts": [],
          "unhandled": {
            "reason": "input",
            "explanation": "only the caller can name a model the program offers"
          },
          "options": [
            "choose a model from the candidates concorde configure-workers lists"
          ],
          "recommendation": "",
          "causes": []
        }
      ]
    }
  }
}
```
