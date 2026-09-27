# Execution contracts

The canonical values of [Execution](module.md): the workspace binding a run reads and the run
result every run returns. How the runner reads and fills them is in
[How a run is executed](runner.md).

## Workspace binding

```concorde-contract
{
  "id": "contract.execution.workspace-binding",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "workspace",
      "root",
      "branch",
      "base_commit",
      "goal",
      "modules",
      "records"
    ],
    "properties": {
      "schema_version": {
        "const": 1
      },
      "workspace": {
        "type": "string",
        "pattern": "^[a-z0-9][a-z0-9-]{0,47}$"
      },
      "root": {
        "type": "string",
        "minLength": 1
      },
      "branch": {
        "type": "string",
        "minLength": 1
      },
      "base_commit": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "goal": {
        "type": "string",
        "minLength": 1
      },
      "modules": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "string",
          "pattern": "^module\\.[a-z][a-z0-9-]*(?:\\.[a-z0-9-]+)*$"
        }
      },
      "records": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "semantics": "The workspace binding .concorde/workspace.json at the root of a workspace. workspace names it, as runs, locks, workflow records and delivery commits name it. root is the absolute real path of the worktree the file lies in; a binding whose root is another worktree is refused. branch is the branch the workspace works on, which task-validation and delivery require the worktree's head to be on; base_commit is the commit its changes are measured from; goal is the text workers are briefed with and a delivery commit carries; modules are the Modules a run works on when it names none; records is the absolute directory whose runs/ holds the workspace's runs, its runs/locks/ the workspace lock and runs/workflows/ its workflow record. Whoever prepares the workspace writes the file; Execution only reads it. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 1,
    "workspace": "retry",
    "root": "/home/dev/shop/.claude/worktrees/retry",
    "branch": "concorde/retry",
    "base_commit": "4be1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9",
    "goal": "Limit HTTP retries to three attempts.",
    "modules": [
      "module.http"
    ],
    "records": "/home/dev/shop/.concorde"
  }
}
```

## Run result

```concorde-contract
{
  "id": "contract.execution.run-result",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "kind",
      "name",
      "workspace",
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
  "semantics": "The result of one run, printed on standard output and saved as <records>/runs/<run_id>/result.json. kind is operation for an Operation and command for a recorded command; name is the Operation's or command's name. workspace is the bound workspace's name, or null for an unbound run. modules are the Modules the run worked on. status is ok when the run did what it promises, blocked when it needs a decision above it and failed otherwise. output is the definition's output, checked against its own contract when the status is ok. worker is the last worker result unchanged, a claim, and worker_runs the identities of the worker runs the run started; both are empty for a recorded command. host_evidence holds only what the runner and its steps observed themselves; kind is one of grant, context-identity, worker-model, audit, check, rounds, transcript, stderr, refused, cancelled, host-error, invalid-output, git, readiness, commit or removed-module (a Module the binding names that the workspace no longer registers, which the run left out), or a kind the definition's own Spec defines; ref names the path, command or identity concerned and detail explains it. Timestamps are RFC 3339 in UTC. error is null exactly when the status is ok; otherwise it is the run's own error link, level operation or command, whose causes are the errors it received, unchanged. A behaviour or field change increments the version.",
  "example": {
    "kind": "command",
    "name": "task-validation",
    "workspace": "retry",
    "modules": [
      "module.http"
    ],
    "run_id": "r-20260927T101500-task_validation-3f2a9c1b",
    "status": "blocked",
    "summary": "Not deliverable: 1 blocking finding(s). check check.http.tests: module.http check failed (exit 1); log .concorde/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests.log",
    "output": null,
    "worker": null,
    "worker_runs": [],
    "host_evidence": [
      {
        "kind": "check",
        "ref": "check.http.tests",
        "detail": "failed, exit 1; log .concorde/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests.log"
      }
    ],
    "error": {
      "level": "command",
      "actor": "Command task-validation r-20260927T101500-task_validation-3f2a9c1b (workspace retry)",
      "code": "not_deliverable",
      "detail": "workspace retry is not deliverable: 1 blocking finding(s), each a cause below; delivery, which decides the same readiness again, refuses the workspace until they are repaired (readiness in .concorde/runs/r-20260927T101500-task_validation-3f2a9c1b/readiness.json)",
      "evidence": [
        {
          "kind": "blocking",
          "ref": "check.http.tests",
          "detail": "module.http check failed (exit 1)"
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
      "recommendation": "repair the first blocking finding: check check.http.tests: module.http check failed (exit 1)",
      "causes": [
        {
          "level": "check",
          "actor": "check.http.tests",
          "code": "check_failed",
          "detail": "the configured check check.http.tests of module.http failed with exit code 1; its log ends with: FAILED tests/test_retry.py::test_three_attempts",
          "evidence": [
            {
              "kind": "log",
              "ref": ".concorde/runs/r-20260927T101500-task_validation-3f2a9c1b/checks/check.http.tests.log",
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
