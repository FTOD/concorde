# Operations contracts

The canonical envelope every Operation of [Operations](module.md) returns. How the host fills it is
in [How the host runs an Operation](host.md).

## Operation result

```concorde-contract
{
  "id": "contract.operations.result",
  "version": 7,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "operation",
      "task",
      "modules",
      "run_id",
      "status",
      "summary",
      "output",
      "worker",
      "worker_runs",
      "host_evidence",
      "error",
      "started_at",
      "finished_at"
    ],
    "properties": {
      "operation": {
        "type": "string",
        "pattern": "^[a-z][a-z_]*$"
      },
      "task": {
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
      "modules": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
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
          "failed"
        ]
      },
      "summary": {
        "type": "string",
        "minLength": 1
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
      "worker": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object"
          }
        ]
      },
      "worker_runs": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "host_evidence": {
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
      },
      "started_at": {
        "type": "string",
        "minLength": 1
      },
      "finished_at": {
        "type": "string",
        "minLength": 1
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
  "semantics": "The envelope of one Operation run, printed by concorde run and saved as .concorde/runs/<run_id>/result.json in the primary worktree. operation is a catalog name; task, modules and run_id identify the run: task is null for a run without a task, which worked on the primary worktree, and modules may be empty when the run was refused before its Modules were resolved or when a run without a task named none. status ok means the Operation did what it promises; blocked means it cannot continue without a decision of the main agent; failed means an error of the host, the worker, the audit or the checks, or a refusal before the run began. summary is written by the host. output is the Operation-specific value defined by the provider's output contract, or null when the run produced none. worker is the last worker result exactly as the worker returned it, or null for a run without a worker; its content is the worker's claim and never host evidence. worker_runs lists the run records written for the run's worker launches, in launch order. host_evidence holds only facts the host produced itself; kind is one of grant, context-identity, worker-model, audit, check, rounds, transcript, stderr, refused, cancelled, host-error, invalid-output, record, git, readiness or commit, or a kind the provider's own Spec defines, such as structural or finding-scope, ref names the path, command or identity concerned and detail explains it. error is null exactly when status is ok; otherwise it is the Operation's own link of the error chain, a contract.concorde.error link of level operation whose causes are the errors it received, unchanged; $defs error, evidence and unhandled are that contract's definitions. Timestamps are RFC 3339 in UTC. A behaviour or field change increments the version.",
  "example": {
    "operation": "implement",
    "task": "severity",
    "modules": [
      "module.issues"
    ],
    "run_id": "r-20260924T093000-implement-5c1e0a77",
    "status": "failed",
    "summary": "The worker run w-20260924T093001-implement-0f3b2a91 ended failed (checks_failed).",
    "output": null,
    "worker": {
      "status": "ok",
      "summary": "Added the severity field to reports and updated the store.",
      "error": null,
      "proposed_deletions": [],
      "output": {
        "addresses": [
          "scenario.issues.report-severity"
        ]
      }
    },
    "worker_runs": [
      "w-20260924T093001-implement-0f3b2a91"
    ],
    "host_evidence": [
      {
        "kind": "grant",
        "ref": "sha256:7d1f",
        "detail": "implement grant"
      },
      {
        "kind": "audit",
        "ref": "4",
        "detail": "2 changed, violations: none"
      },
      {
        "kind": "check",
        "ref": "check.issues.tests",
        "detail": "failed, exit 1; log .concorde/runs/w-20260924T093001-implement-0f3b2a91/checks/4/check.issues.tests.log"
      },
      {
        "kind": "rounds",
        "ref": "",
        "detail": "4 round(s)"
      }
    ],
    "error": {
      "level": "operation",
      "actor": "Operation implement r-20260924T093000-implement-5c1e0a77 (task severity)",
      "code": "checks_failed",
      "detail": "the implement worker run w-20260924T093001-implement-0f3b2a91 ended failed: checks_failed: 1 configured check(s) still fail after 4 round(s) (3 resume round(s) allowed): check.issues.tests",
      "evidence": [],
      "attempts": [],
      "unhandled": {
        "reason": "decision",
        "explanation": "the Operation used every resume round it is configured with; whether to narrow the goal, change the Spec or allow more rounds is the main agent's decision"
      },
      "options": [
        "run the Operation again with a narrower goal or more --rounds",
        "run understand to check whether the Spec supports the change"
      ],
      "recommendation": "run the Operation again with a narrower goal or more --rounds",
      "causes": [
        {
          "level": "workers",
          "actor": "Workers run w-20260924T093001-implement-0f3b2a91 (implement worker)",
          "code": "checks_failed",
          "detail": "1 configured check(s) still fail after 4 round(s) (3 resume round(s) allowed): check.issues.tests",
          "evidence": [
            {
              "kind": "run-record",
              "ref": ".concorde/runs/w-20260924T093001-implement-0f3b2a91/record.json",
              "detail": ""
            }
          ],
          "attempts": [
            "round 1: the worker ended ok; failing: check.issues.tests (failed, exit 1)",
            "round 4: the worker ended ok; failing: check.issues.tests (failed, exit 1)"
          ],
          "unhandled": {
            "reason": "exhausted",
            "explanation": "Workers resumes the worker at most 3 time(s) with the failures and does not extend that"
          },
          "options": [],
          "recommendation": "",
          "causes": [
            {
              "level": "check",
              "actor": "check.issues.tests",
              "code": "check_failed",
              "detail": "the configured check check.issues.tests of module.issues failed with exit code 1; its log ends with: FAILED tests/concorde/issues/test_store.py::test_severity_round_trip - KeyError: 'severity'",
              "evidence": [
                {
                  "kind": "log",
                  "ref": ".concorde/runs/w-20260924T093001-implement-0f3b2a91/checks/4/check.issues.tests.log",
                  "detail": ""
                }
              ],
              "attempts": [],
              "unhandled": {
                "reason": "capability",
                "explanation": "a configured check only measures the code it runs against"
              },
              "options": [],
              "recommendation": "",
              "causes": []
            }
          ]
        }
      ]
    },
    "started_at": "2026-09-24T09:30:00Z",
    "finished_at": "2026-09-24T09:52:00Z"
  }
}
```

## Worker configuration

The output of [`configure_workers`](module.md#concept.operations.configure-workers).

```concorde-contract
{
  "id": "contract.operations.worker-configuration",
  "version": 3,
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
                "anyOf": [
                  {
                    "type": "null"
                  },
                  {
                    "enum": [
                      "claude",
                      "pi"
                    ]
                  }
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
  "semantics": "The output of configure_workers. action is list when the run changed nothing and was asked for nothing, set when it set a model or level, unset when it removed an entry. backend is the program whose entries were read or changed and backend_from how it was found: --backend, otherwise the entry of the file's backend section that chooses the backend of the named role, Operation or default (such as backend.operations.implement.default), otherwise the main session's variable. worktree is the worktree whose configuration file config was read or changed, the task's with --task and otherwise the primary worktree; changed says whether the file changed. candidates is null for unset and otherwise the listing of the installed program: backend, program, version, complete (false for Claude Code, which cannot list an account's models), reasoning_flag, reasoning_levels, models (each with id, source, reasoning, levels and a note, and for pi context, max_output and images) and a note. configured is the file's entry for the backend as written after the change. effective maps every catalog Operation that launches workers to its worker roles, each with the backend a worker of that role would run on and the entry or main session variable it came from (backend null when neither settles it, with the reason as its source), and the model and reasoning level it would run with in that backend's section and the entry each came from, or null with the source \"the backend's own default\". A behaviour or field change increments the version.",
  "example": {
    "action": "set",
    "backend": "pi",
    "backend_from": "CONCORDE_CLIENT=pi",
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
      "default": {
        "model": "anthropic/claude-sonnet-5",
        "reasoning": "medium"
      },
      "operations": {
        "spec_review": {
          "roles": {
            "checker": {
              "reasoning": "low"
            }
          }
        }
      }
    },
    "effective": {
      "spec_review": {
        "reviewer": {
          "backend": "pi",
          "backend_source": "CONCORDE_CLIENT=pi",
          "model": "anthropic/claude-sonnet-5",
          "reasoning": "medium",
          "model_source": "pi.default",
          "reasoning_source": "pi.default"
        },
        "checker": {
          "backend": "pi",
          "backend_source": "CONCORDE_CLIENT=pi",
          "model": "anthropic/claude-sonnet-5",
          "reasoning": "low",
          "model_source": "pi.default",
          "reasoning_source": "pi.operations.spec_review.roles.checker"
        }
      }
    }
  }
}
```
