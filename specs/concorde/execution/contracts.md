# Execution contracts

The canonical values of [Execution](module.md): the
[run result](../glossary.json#concept.run-result) every run returns and the content of the trace node
every run leaves. How the runner reads and fills
them is in [How a run is executed](runner.md).

## Run result

```concorde-contract
{
  "id": "contract.execution.run-result",
  "version": 3,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "kind",
      "name",
      "workspace",
      "commit",
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
      "kind": {
        "enum": [
          "operation",
          "command"
        ]
      },
      "name": {
        "type": "string",
        "pattern": "^[a-z][a-z_-]*$"
      },
      "workspace": {
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
  "semantics": "The result of one run, printed on standard output and saved as result.json in the run's trace node folder. kind is operation for an Operation and command for an execution command; name is the Operation's or command's name. workspace is the bound workspace's name, or null for an unbound run or a run whose binding was refused. commit is the commit an unbound run examined, the HEAD of the worktree it started in, which its throwaway checkout held; it is null for a bound run, which works on its workspace as it stands, uncommitted changes included, and for a run refused before its checkout existed. modules are the Modules the run worked on, empty when the run was refused before they were settled. status is ok when the run did what it promises, blocked when it needs a decision above it and failed otherwise. output is the definition's output, checked against its own contract when the status is ok; for task-validation it is Validation's readiness (contract.validation.readiness), whose check logs are relative to the run's trace node, while host_evidence and error name them by their absolute paths. worker is the last worker result unchanged, a claim, and worker_runs the identities of the worker runs the run's steps started through the worker harness; both are empty for an execution command. host_evidence holds only what the runner and its steps observed themselves; kind is one of trace (the run's own trace node, by its run identity, with its folder in the detail), grant, context-identity, worker-model, audit, check, rounds, transcript, stderr, refused, cancelled, host-error, invalid-output, git, readiness, commit, removed-module (a Module the binding names that the workspace no longer registers, which the run left out), checkout (the throwaway checkout an unbound run worked in), submodule or submodule-absent (a submodule the checkout did or did not check out), environment or environment-not-linked (a runtime path the checkout did or did not link from the worktree the run started in) or checkout-not-removed (a part of the checkout Git would not remove, deleted directly), or a kind the definition's own Spec defines; ref names the path, command or identity concerned and detail explains it. Timestamps are RFC 3339 in UTC. error is null exactly when the status is ok; otherwise it is the run's own error link, level operation or command, whose causes are the errors it received, unchanged. A behaviour or field change increments the version.",
  "example": {
    "kind": "command",
    "name": "task-validation",
    "workspace": "retry",
    "commit": null,
    "modules": [
      "module.http"
    ],
    "run_id": "r-20260927T101500-task_validation-3f2a9c1b",
    "status": "blocked",
    "summary": "Not deliverable: 1 blocking finding(s). check check.http.tests: module.http check failed (exit 1); log /home/dev/shop/.concorde/tasks/retry/workspace/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests/output.log",
    "output": {
      "workspace": "retry",
      "ready": false,
      "inputs": {
        "head": "4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
        "base": "4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
        "changed": [
          {
            "path": "src/http/retry.py",
            "mode": "100644",
            "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
          }
        ],
        "config_digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
        "digest": "sha256:3333333333333333333333333333333333333333333333333333333333333333"
      },
      "modules": [
        "module.http"
      ],
      "blocking": [
        {
          "kind": "check",
          "ref": "check.http.tests",
          "detail": "module.http check failed (exit 1); log /home/dev/shop/.concorde/tasks/retry/workspace/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests/output.log"
        }
      ],
      "warnings": [],
      "checks": [
        {
          "check": "check.http.tests",
          "module": "module.http",
          "status": "failed",
          "exit_code": 1,
          "measured_digest": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
          "log": "checks/check.http.tests/output.log"
        }
      ]
    },
    "worker": null,
    "worker_runs": [],
    "host_evidence": [
      {
        "kind": "trace",
        "ref": "r-20260927T101500-task_validation-3f2a9c1b",
        "detail": "/home/dev/shop/.concorde/tasks/retry/workspace/runs/r-20260927T101500-task_validation-3f2a9c1b"
      },
      {
        "kind": "check",
        "ref": "check.http.tests",
        "detail": "failed, exit 1; log /home/dev/shop/.concorde/tasks/retry/workspace/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests/output.log"
      }
    ],
    "error": {
      "level": "command",
      "actor": "Command task-validation r-20260927T101500-task_validation-3f2a9c1b (workspace retry)",
      "code": "not_deliverable",
      "detail": "workspace retry is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in /home/dev/shop/.concorde/tasks/retry/workspace/runs/r-20260927T101500-task_validation-3f2a9c1b/readiness.json)",
      "evidence": [
        {
          "kind": "blocking",
          "ref": "check.http.tests",
          "detail": "module.http check failed (exit 1); log /home/dev/shop/.concorde/tasks/retry/workspace/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests/output.log"
        }
      ],
      "attempts": [],
      "unhandled": {
        "reason": "decision",
        "explanation": "task-validation only decides readiness and never repairs; each finding needs a Spec change (specify) or a code change (implement), which the task level chooses"
      },
      "options": [
        "repair each blocking finding in the workspace and run task-validation again",
        "run specify for a Spec finding, implement for a code or check finding"
      ],
      "recommendation": "repair the first blocking finding: check check.http.tests: module.http check failed (exit 1); log /home/dev/shop/.concorde/tasks/retry/workspace/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests/output.log",
      "causes": [
        {
          "level": "check",
          "actor": "check.http.tests",
          "code": "check_failed",
          "detail": "the configured check check.http.tests of module.http failed with exit code 1; its log ends with: FAILED tests/test_retry.py::test_three_attempts",
          "evidence": [
            {
              "kind": "log",
              "ref": "/home/dev/shop/.concorde/tasks/retry/workspace/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests/output.log",
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
    },
    "started_at": "2026-09-27T10:15:00Z",
    "finished_at": "2026-09-27T10:15:41Z"
  }
}
```

## Run trace

Every run is a [trace node](../glossary.json#concept.trace-node) of kind `run` as
[Tracing](../kernel/tracing/contracts.md#contract.tracing.node) defines it, whose content is this value.

```concorde-contract
{
  "id": "contract.execution.run-trace",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "kind",
      "name",
      "argv",
      "exit_code",
      "steps",
      "worker_runs",
      "summary"
    ],
    "properties": {
      "kind": {
        "enum": [
          "operation",
          "command"
        ]
      },
      "name": {
        "type": "string",
        "pattern": "^[a-z][a-z_-]*$"
      },
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
      },
      "steps": {
        "type": "array",
        "items": {
          "$ref": "#/$defs/step"
        }
      },
      "worker_runs": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "summary": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "string",
            "minLength": 1
          }
        ]
      }
    },
    "$defs": {
      "step": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "name",
          "started_at",
          "ended_at",
          "outcome"
        ],
        "properties": {
          "name": {
            "type": "string",
            "minLength": 1
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
          "outcome": {
            "enum": [
              "running",
              "continue",
              "stop",
              "raised",
              "cancelled"
            ]
          }
        }
      }
    }
  },
  "semantics": "The data of the typed value concorde-run-trace, the content of a run's trace node. kind and name are the run's definition; argv is its command line after the name, without --detach and --trace-at; exit_code is the exit status the runner returned (0 for ok, 1 otherwise), null while the run runs. steps lists, in order, every step of the definition that began, with when it began and ended and how: continue, stop (it ended the run with a status), raised (it raised and the run failed), cancelled (a signal ended it) or running; the runner's own work before the first step and after the last is not a step. worker_runs are the identities of the worker runs the run's steps started, whose nodes lie in its workers/ folder. summary is the result's summary once the run ended, null before. The run's times, status, outcome (its status, or cancelled), duration, error, metadata, inputs (references input) and the files of its folder (result.json, status.json, host.out, readiness.json, tracebacks) are the uniform fields of its trace node. A behaviour or field change increments the version.",
  "example": {
    "kind": "command",
    "name": "delivery",
    "argv": [],
    "exit_code": 0,
    "steps": [
      {
        "name": "readiness",
        "started_at": "2026-09-27T10:30:00.200000Z",
        "ended_at": "2026-09-27T10:30:41.000000Z",
        "outcome": "continue"
      },
      {
        "name": "commit",
        "started_at": "2026-09-27T10:30:41.000000Z",
        "ended_at": "2026-09-27T10:30:42.500000Z",
        "outcome": "continue"
      }
    ],
    "worker_runs": [],
    "summary": "Delivered workspace retry as 9f8e7d6c5b4a39281706f5e4d3c2b1a098765432."
  }
}
```
