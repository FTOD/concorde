# Workers contracts

The exact answer every worker ends with, the grant a caller hands over, the worker configuration
file, and what a worker run and each of its rounds retain in their trace nodes.

## Worker result

The [entry](../../glossary.json#concept.worker-result) explains the worker result's role; [the run
mechanics](launch.md#rounds) say how the host reacts to it. Its `error` is the worker's link of the
Framework's [error chain](../../kernel/tracing/contracts.md#contract.tracing.error).

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
  "semantics": "The structured result a worker returns at the end of every round, through --json-schema on Claude Code and as the argument of the concorde_result tool on pi; the host validates it against this schema on both. status ok means the worker finished its task; blocked means it cannot continue without a decision above it, such as a Spec gap or a missing grant, and failed means it tried and could not finish. summary says what was done. error is null exactly when status is ok; for blocked and failed it is the worker's own link of the error chain, the contract.tracing.error link without level, actor and causes: code names the error, detail describes it completely with the exact messages, evidence items point at a file, command, output or Spec (kind) by a path or identity (ref) with a short explanation (detail), attempts lists what was tried, unhandled gives the reason and the specific explanation why the worker could not handle it, and options and recommendation are what it offers. The error is the worker's claim, never host evidence; Workers adds the level worker, the actor and no causes when it puts it in the chain. proposed_deletions lists the paths in the worktree the worker wants deleted, each relative to the worktree as the brief asks of every path in the result; the host also accepts an absolute path, which it normalizes and reads as the same path in the worktree, refusing one outside it, and it deletes only those in the grant's rw list after a clean audit (launch.md#proposed-deletions). output is the job-specific part of the answer, such as an assessment, a code change summary or review findings; the caller supplies its schema, which the host embeds at this key in the schema it validates against and passes to --json-schema on Claude Code, and it is an empty object for a caller without one. A result whose error does not match its status is invalid. The host keeps the result verbatim in the run record.",
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

## Grant input {#grant-input}

The [grant](../../glossary.json#concept.grant) a caller hands the worker harness for one run, as
data. The worker harness owns this format and computes nothing in it: it never derives a grant from
Specs, widens one or reads where it came from. In Concorde, a step of Method fills it from the grant
Spec core computes, projecting its `task_type`, `entries` and `context_identity`, which have exactly
this shape; Spec core's grant also carries the Modules and glossary terms, which Method keeps for
itself and never passes. A contract test on each side keeps the three shared fields equal, so
neither part imports the other.

```concorde-contract
{
  "id": "contract.workers.grant-input",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "task_type",
      "entries",
      "context_identity"
    ],
    "properties": {
      "task_type": {
        "enum": [
          "understand",
          "specify",
          "implement",
          "test",
          "review-spec",
          "review-code",
          "code-to-spec",
          "review-architecture"
        ]
      },
      "entries": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "path",
            "level"
          ],
          "properties": {
            "path": {
              "type": "string",
              "minLength": 1
            },
            "level": {
              "enum": [
                "rw",
                "ro",
                "names"
              ]
            }
          }
        }
      },
      "context_identity": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "semantics": "The grant of one worker run, handed over by its caller as data and frozen for the whole run. task_type is the Protocol task type of the worker's job, which selects its tool set. entries lists every path the worker may reach with its level: rw writable, ro readable, names known by name only; a path is relative to the worktree the worker works in, never absolute and never leaving it through .., a directory ending in /, and a path no entry names is hidden. context_identity identifies what selected the entries, as the caller computed it; the worker harness records it and the digest of the grant, and never interprets either. A grant whose entries break this shape is refused before anything is generated, with grant_malformed naming the first such entry; one without a task type, entries or context identity with grant_unavailable. A behaviour or field change increments the version.",
  "example": {
    "task_type": "implement",
    "entries": [
      {
        "path": "src/checkout/cart.py",
        "level": "rw"
      },
      {
        "path": "specs/shop/checkout/module.md",
        "level": "ro"
      },
      {
        "path": "src/billing/invoice.py",
        "level": "ro"
      }
    ],
    "context_identity": "sha256:9f2c1e4b7a6d5c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b"
  }
}
```

## Worker configuration

The file the [worker configuration](../../glossary.json#concept.worker-configuration) is, which
[Choosing worker models](module.md#choosing-worker-models) explains.

```concorde-contract
{
  "id": "contract.workers.worker-configuration",
  "version": 9,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "enabled_models"
    ],
    "properties": {
      "schema_version": {
        "const": 2
      },
      "enabled_models": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "reasoning": {
              "type": "string",
              "minLength": 1,
              "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
            }
          }
        }
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
  "semantics": "The worker configuration .concorde/workers.json of a worktree, tracked by Git and edited directly. schema_version is 2. enabled_models is required and not empty: it names every model an entry may choose by its project model name, letters, digits, '.', '_' and '-' starting with a letter or digit, which depends on no installation, each with an optional reasoning level of its own. default, operations.<operation>.default and operations.<operation>.workers.<worker id> each may set backend (pi or claude), model (a name of enabled_models) and reasoning; operation and worker names are labels: the caller that asks for a worker declares the Operations and worker ids it may launch, against which the whole file's names are checked, and reasoning must be a level of the effective backend. For each field the most specific entry that sets it wins, a backend no more than a model or a level. A backend no entry sets is pi. The level is that of the entry that chose the model or of a more specific one, otherwise the model's own, otherwise one a less specific entry sets, otherwise none, which leaves the program's own default level. A worker whose entries set no model is refused with model_unresolved, and an entry naming a model outside enabled_models with model_not_enabled; the model map of the machine gives the model's local id on the worker's backend (contract.workers.model-map). limits sets timeout_seconds per round (default 1800), max_turns (default 200), max_budget_usd (default none) and rounds of resume (default 3) for every worker launch; runtime lists the paths Bash may read besides the grant, relative to the workspace or absolute (default .venv and node_modules, each only when it exists). A worktree without the file runs no worker (config_missing). Duplicate keys, unknown fields, Operations or workers the caller does not declare, a model name that is not a project model name, levels the backend does not know and any other schema_version are refused with config_invalid when a worker launches, schema_version 1, whose models were one program's local ids, with how to rewrite it; so is a worktree without this file that still has the retired untracked .concorde/worker-models.json.",
  "example": {
    "schema_version": 2,
    "enabled_models": {
      "claude-sonnet-5": {
        "reasoning": "medium"
      },
      "gpt-6-astra": {},
      "claude-opus-5-5": {}
    },
    "default": {
      "model": "claude-sonnet-5"
    },
    "operations": {
      "spec_panel": {
        "workers": {
          "reviewer2": {
            "model": "gpt-6-astra",
            "reasoning": "high"
          },
          "chair": {
            "backend": "claude",
            "model": "claude-opus-5-5"
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

## Model map

The file the [model map](../../glossary.json#concept.model-map) is, which
[Choosing worker models](module.md#choosing-worker-models) explains.

```concorde-contract
{
  "id": "contract.workers.model-map",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "models"
    ],
    "properties": {
      "schema_version": {
        "const": 1
      },
      "models": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "claude": {
              "type": "string",
              "minLength": 1,
              "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
            },
            "pi": {
              "type": "string",
              "minLength": 1,
              "pattern": "^[^\\s\\x00-\\x1f\\x7f](?:[^\\x00-\\x1f\\x7f]*[^\\s\\x00-\\x1f\\x7f])?\\Z"
            }
          }
        }
      }
    }
  },
  "semantics": "The model map of one machine: a JSON file of the user, outside every repository and never committed, that the file CONCORDE_MODEL_MAP names by its absolute path, else concorde/models.json of the user's XDG configuration directory ($XDG_CONFIG_HOME when it is absolute, otherwise ~/.config). schema_version is 1. models maps each project model name to its local model id on pi, on Claude Code or on both, the id that program takes with --model, such as local-openai/gpt-6-astra on pi or claude-opus-5-5 on Claude Code. It may name models no project enables. Workers reads it only when a worker launches, never writes it, and reads nothing else of the user's environment to choose a model. A missing file is refused with model_map_missing, showing what the file holds; a CONCORDE_MODEL_MAP that is not an absolute path, and a file that is unreadable, has duplicate keys, unknown fields, a model without an id or a name that is not a project model name, with model_map_invalid, saying what is wrong; and a worker whose model has no id for its backend with model_unmapped, naming the exact entry to add. Every refusal names the file, and the project model name is never used as a local id.",
  "example": {
    "schema_version": 1,
    "models": {
      "gpt-6-astra": {
        "pi": "local-openai/gpt-6-astra"
      },
      "gpt-6.1-sol": {
        "pi": "local-openai/gpt-6.1-sol"
      },
      "claude-opus-5-5": {
        "pi": "anthropic/claude-opus-5-5",
        "claude": "claude-opus-5-5"
      }
    }
  }
}
```

## Worker run trace

Every worker run is a [trace node](../../glossary.json#concept.trace-node) of kind `worker-run`, and each of
its rounds one of kind `worker-round` below it, as [Tracing](../../kernel/tracing/contracts.md#contract.tracing.node)
defines them; their contents are these values.

```concorde-contract
{
  "id": "contract.workers.worker-run-trace",
  "version": 4,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "task_type",
      "backend_source",
      "local_model",
      "model_map",
      "tools",
      "transcript",
      "worker_result",
      "deleted",
      "deletions_refused",
      "deletions_absent",
      "deletions_failed",
      "rounds"
    ],
    "properties": {
      "task_type": {
        "type": "string",
        "minLength": 1
      },
      "backend_source": {
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
      "local_model": {
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
      "model_map": {
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
      "tools": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          }
        ]
      },
      "transcript": {
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
      "worker_result": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object"
          }
        ]
      },
      "deleted": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "deletions_refused": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "deletions_absent": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "deletions_failed": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "rounds": {
        "type": "integer",
        "minimum": 0
      }
    }
  },
  "semantics": "The data of the typed value concorde-worker-run-trace, the content of a worker run's trace node, which is its run record. task_type is the worker's task type; backend_source says what chose the backend: the worker configuration entry that set it, such as operations.implement.default or the configuration's own default entry, the text Concorde's default worker backend when no entry sets one and pi applies, or null when the request was made without resolving the worker's backend; local_model is the id the model map gave the worker's project model name on its backend, passed with --model, and model_map the path of that map, both null when the request named no local id; tools is the tool set the worker was given, or null when the run was refused before a backend was prepared. transcript is the path, relative to the node's folder, of the transcript the host moved there from the runtime directory once the worker ended (transcript.jsonl), null when no session existed. worker_result is the last worker result verbatim, a claim, or null. deleted lists the proposed deletions the host performed, deletions_refused those it refused as the worker gave them, deletions_absent those in the rw list it found already absent and deletions_failed those whose deletion failed, each but the refused relative to the worktree (launch.md#proposed-deletions). rounds is how many rounds began; each is a worker-round node below this one. The worker run's identity, times, status, outcome, error (Workers' link), its metadata (the Modules, the Operation and worker id it was launched for, task type, backend, project model name and reasoning level as configured, context identity and the grant, brief and settings digests) and its files (status.json, grant.json, brief.md, transcript.jsonl) are the uniform fields of its trace node. A behaviour or field change increments the version.",
  "example": {
    "task_type": "implement",
    "backend_source": "operations.implement.default",
    "local_model": "local-openai/gpt-6-astra",
    "model_map": "/home/dev/.config/concorde/models.json",
    "tools": [
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "Bash"
    ],
    "transcript": "transcript.jsonl",
    "worker_result": {
      "status": "ok",
      "summary": "Retry limited to three attempts.",
      "error": null,
      "proposed_deletions": [],
      "output": {}
    },
    "deleted": [],
    "deletions_refused": [],
    "deletions_absent": [],
    "deletions_failed": [],
    "rounds": 2
  }
}
```

```concorde-contract
{
  "id": "contract.workers.worker-round-trace",
  "version": 4,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "round",
      "prompt",
      "session",
      "exit",
      "audit",
      "evidence",
      "validation",
      "agent"
    ],
    "properties": {
      "round": {
        "type": "integer",
        "minimum": 1
      },
      "prompt": {
        "enum": [
          "initial",
          "repair"
        ]
      },
      "session": {
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
      "exit": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "integer"
          }
        ]
      },
      "audit": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "verdict",
              "changed",
              "violations"
            ],
            "properties": {
              "verdict": {
                "enum": [
                  "clean",
                  "violation"
                ]
              },
              "changed": {
                "type": "array",
                "items": {
                  "type": "string",
                  "minLength": 1
                }
              },
              "violations": {
                "type": "array",
                "items": {
                  "type": "string",
                  "minLength": 1
                }
              }
            }
          }
        ]
      },
      "evidence": {
        "type": "array",
        "items": {
          "type": "object"
        }
      },
      "validation": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string"
          }
        ]
      },
      "agent": {
        "type": "object"
      }
    }
  },
  "semantics": "The data of the typed value concorde-worker-round-trace, the content of one worker round's trace node. round is its number from 1; prompt says what the worker was given: the brief (initial) or what the caller's round validation reported to repair (repair). session is the agent session the round ran in, exit the agent process's exit status (null when it could not be started), audit the host's audit after the round, or null when the round ended before it: verdict is clean or violation, changed lists every worktree-relative path created, changed or deleted since the snapshot, and violations each violation as a string, HEAD or index for a changed Git state, the path of a file created or changed outside rw and the path followed by a space and (deleted) for a deleted file (launch.md#audit); evidence the values the caller's round validation returned to keep with the round, in the caller's own shape, such as Concorde's check results with their logs as paths relative to this node's folder, empty when none ran, and validation the outcome of the round validation (clean, the text to repair, or why it could not validate), null when none ran. agent is what the agent program reported about the round, as its backend reads it: under claude, the result envelope's subtype, is_error, num_turns, total_cost_usd, permission_denials (the tool calls Claude Code refused, each with its tool name, tool use id and input), modelUsage (each model's tokens and cost) and duration_api_ms, each as the envelope gave it and null when it gave none; or under pi, its last stop reason, turn count and cost. The round's tokens, cost, turns and duration are its usage; its standard error is the artifact stderr.log, and the nodes the round validation placed in its folder, such as check nodes, lie below it. A behaviour or field change increments the version.",
  "example": {
    "round": 1,
    "prompt": "initial",
    "session": "5d7c9a8e-1f2b-4c3d-9e0f-a1b2c3d4e5f6",
    "exit": 0,
    "audit": {
      "verdict": "clean",
      "changed": [
        "src/http/retry.py"
      ],
      "violations": []
    },
    "evidence": [
      {
        "check_id": "check.http.tests",
        "module": "module.http",
        "status": "failed",
        "exit_code": 1,
        "source_digest": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
        "log": "checks/check.http.tests/output.log",
        "log_digest": "sha256:7777777777777777777777777777777777777777777777777777777777777777"
      }
    ],
    "validation": null,
    "agent": {
      "claude": {
        "subtype": "success",
        "is_error": false,
        "num_turns": 14,
        "total_cost_usd": 0.41,
        "permission_denials": [
          {
            "tool_name": "Write",
            "tool_use_id": "toolu_01",
            "tool_input": {
              "file_path": "/work/specs/http/module.md"
            }
          }
        ],
        "modelUsage": {
          "claude-sonnet-5-5": {
            "inputTokens": 42,
            "outputTokens": 5120,
            "cacheReadInputTokens": 310422,
            "cacheCreationInputTokens": 20510,
            "costUSD": 0.41
          }
        },
        "duration_api_ms": 61240
      }
    }
  }
}
```

## Returned run record

What the host returns to the caller that asked for the worker, in Concorde an
[Operation](../../glossary.json#concept.operation)'s step: the
[run record](../../glossary.json#concept.run-record) as the caller reads it, which carries every
round's content so that the caller reads the audits and the round validation's evidence without
reading a file. It is
not stored; the run's trace node and its rounds' nodes are the record that is kept.

```concorde-contract
{
  "id": "contract.workers.worker-run-record",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "run_id",
      "status",
      "error",
      "started_at",
      "ended_at",
      "task_type",
      "operation",
      "worker",
      "backend",
      "backend_source",
      "model",
      "local_model",
      "model_map",
      "reasoning",
      "worktree",
      "context_identity",
      "grant_digest",
      "settings_digest",
      "brief_digest",
      "tools",
      "transcript",
      "stderr_tail",
      "worker_result",
      "deleted",
      "deletions_refused",
      "deletions_absent",
      "deletions_failed",
      "run_directory",
      "runtime_directory",
      "rounds"
    ],
    "properties": {
      "run_id": {
        "type": "string",
        "minLength": 1
      },
      "status": {
        "enum": [
          "ok",
          "blocked",
          "failed"
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
      "task_type": {
        "type": "string",
        "minLength": 1
      },
      "operation": {
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
      "worker": {
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
      "backend": {
        "type": "string",
        "minLength": 1
      },
      "backend_source": {
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
      "local_model": {
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
      "model_map": {
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
      "worktree": {
        "type": "string",
        "minLength": 1
      },
      "context_identity": {
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
      "grant_digest": {
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
      "settings_digest": {
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
      "brief_digest": {
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
      "tools": {
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
      "transcript": {
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
      "stderr_tail": {
        "type": "string"
      },
      "worker_result": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object"
          }
        ]
      },
      "deleted": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "deletions_refused": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "deletions_absent": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "deletions_failed": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "run_directory": {
        "type": "string",
        "minLength": 1
      },
      "runtime_directory": {
        "type": "string",
        "minLength": 1
      },
      "rounds": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "round",
            "prompt",
            "usage"
          ],
          "properties": {
            "round": {
              "type": "integer",
              "minimum": 1
            },
            "prompt": {
              "enum": [
                "initial",
                "repair"
              ]
            },
            "session": {
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
            "exit": {
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "duration": {
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "number",
                  "minimum": 0
                }
              ]
            },
            "usage": {
              "type": "object"
            },
            "claude": {
              "type": "object"
            },
            "pi": {
              "type": "object"
            },
            "audit": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "verdict",
                "changed",
                "violations"
              ],
              "properties": {
                "verdict": {
                  "enum": [
                    "clean",
                    "violation"
                  ]
                },
                "changed": {
                  "type": "array",
                  "items": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "violations": {
                  "type": "array",
                  "items": {
                    "type": "string",
                    "minLength": 1
                  }
                }
              }
            },
            "evidence": {
              "type": "array",
              "items": {
                "type": "object"
              }
            },
            "validation": {
              "type": "string"
            }
          }
        }
      }
    }
  },
  "semantics": "The value the host returns to its caller, in Concorde an Operation's step, when a worker run ends, however it ends, so that the caller reads the audits and the round validation's evidence without reading a file; it is never written itself, and the record kept is the run's trace node and its rounds' nodes (contract.workers.worker-run-trace, contract.workers.worker-round-trace), from which runs.read_record rebuilds it but for worktree, stderr_tail and runtime_directory. It holds the run node's content and, as that node keeps them, its identity run_id, status (ok, blocked or failed), error (Workers' link, null for ok), started_at and ended_at, and its metadata operation, worker, backend, model, reasoning and context_identity with the grant, settings and brief digests, each null until made; it differs from the node's content in that tools is the tool set as the backend's comma-separated list, as passed to --tools, transcript the absolute path of the transcript in the run directory, and rounds not their number but the ordered list of every round that began. Each round carries what its node's content and usage hold: round, prompt, session, exit, duration (seconds) and usage (the tokens, cost and turns the agent program reported and duration_seconds); what the agent program reported under the key of its backend, claude or pi, as the round content's agent holds it; audit, the audit object of contract.workers.worker-round-trace, once the round was audited; evidence, the round validation's evidence as the caller returned it, with each artifact path absolute, only when the round validation ran; and validation, its outcome, only when it ran. A key absent from a round means that step did not happen in it. worktree is the worker's worktree, run_directory the worker run's node folder, runtime_directory its runtime directory, removed by the time the record is returned, and stderr_tail the end of the last round's standard error. A behaviour or field change increments the version.",
  "example": {
    "run_id": "w-20261002T101500-a1b2c3",
    "status": "failed",
    "error": {
      "level": "workers",
      "actor": "Workers run w-20261002T101500-a1b2c3 (implement worker)",
      "code": "audit_violation",
      "detail": "round 1: the worker changed 2 path(s) outside the grant's writable paths: src/shop/legacy.py (deleted), src/shop/pricing.py; the worker itself reported status ok",
      "evidence": [
        {
          "kind": "audit",
          "ref": "1",
          "detail": "violation: src/shop/legacy.py (deleted)"
        },
        {
          "kind": "audit",
          "ref": "1",
          "detail": "violation: src/shop/pricing.py"
        },
        {
          "kind": "trace",
          "ref": "w-20261002T101500-a1b2c3",
          "detail": "/repo/.concorde/tasks/discounts/workspace/runs/r-1/workers/w-20261002T101500-a1b2c3"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "permission",
        "explanation": "Workers never accepts a write outside the grant and never widens it"
      },
      "options": [],
      "recommendation": "",
      "causes": []
    },
    "started_at": "2026-10-02T10:15:00Z",
    "ended_at": "2026-10-02T10:21:40Z",
    "task_type": "implement",
    "operation": "implement",
    "worker": "worker",
    "backend": "pi",
    "backend_source": "default",
    "model": "gpt-6-astra",
    "local_model": "local-openai/gpt-6-astra",
    "model_map": "/home/dev/.config/concorde/models.json",
    "reasoning": null,
    "worktree": "/repo/.claude/worktrees/discounts",
    "context_identity": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
    "grant_digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    "settings_digest": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
    "brief_digest": "sha256:5555555555555555555555555555555555555555555555555555555555555555",
    "tools": "read,grep,find,ls,edit,write,bash,concorde_result",
    "transcript": "/repo/.concorde/tasks/discounts/workspace/runs/r-1/workers/w-20261002T101500-a1b2c3/transcript.jsonl",
    "stderr_tail": "",
    "worker_result": {
      "status": "ok",
      "summary": "Added discount rules.",
      "error": null,
      "proposed_deletions": [],
      "output": {}
    },
    "deleted": [],
    "deletions_refused": [],
    "deletions_absent": [],
    "deletions_failed": [],
    "run_directory": "/repo/.concorde/tasks/discounts/workspace/runs/r-1/workers/w-20261002T101500-a1b2c3",
    "runtime_directory": "/tmp/concorde-a1b2c3-x7k2",
    "rounds": [
      {
        "round": 1,
        "prompt": "initial",
        "session": "w-20261002T101500-a1b2c3",
        "exit": 0,
        "duration": 401.2,
        "usage": {
          "tokens_in": 120,
          "tokens_out": 3400,
          "tokens_cache_read": 210400,
          "tokens_cache_write": 18200,
          "cost_usd": 0.12,
          "turns": 9,
          "duration_seconds": 401.2
        },
        "pi": {
          "stop_reason": "toolUse",
          "turns": 9,
          "cost": 0.12
        },
        "audit": {
          "verdict": "violation",
          "changed": [
            "src/shop/cart.py",
            "src/shop/legacy.py",
            "src/shop/pricing.py"
          ],
          "violations": [
            "src/shop/legacy.py (deleted)",
            "src/shop/pricing.py"
          ]
        }
      }
    ]
  }
}
```
