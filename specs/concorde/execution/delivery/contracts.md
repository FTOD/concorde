# Delivery contracts

The exact commit, evidence bundle and output of the recorded command `delivery` of
[Delivery](module.md).

## Delivery commit

```text
concorde: deliver <workspace>

<goal of the workspace>

Concorde-Workspace: <workspace>
Concorde-Evidence: .concorde/evidence/<workspace>/<n>.json
Concorde-Readiness: <run identity of this delivery run, which decided the readiness>
```

The commit uses the repository's configured author identity and runs the repository's commit hooks
normally. Its parent is the head of the workspace's bound branch that the delivery validated, whose
commits since the base commit the readiness examined. It contains every uncommitted change of the
workspace that Git does not ignore, except an untracked path Git cannot version (neither a regular
file, a symbolic link nor a directory), the metadata changed by the applied confirmations and the
evidence bundle; when every step was committed before, only the bundle and any cleared markers.

The delivery commits are the only record of a delivery. A commit is a delivery commit of a
workspace when it lies on the first-parent history of the branch since the base commit, its
subject is exactly `concorde: deliver <workspace>`, its `Concorde-Workspace` trailer names the same
workspace, and its `Concorde-Evidence` and `Concorde-Readiness` trailers are present, the first
naming a bundle whose file name is its sequence number. Delivery reads its earlier deliveries this
way, and so may anyone who needs to know whether and how often a workspace was delivered.

## Evidence bundle

```concorde-contract
{
  "id": "contract.delivery.evidence-bundle",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "workspace",
      "goal",
      "modules",
      "sequence",
      "base_commit",
      "parent_commit",
      "readiness",
      "confirmations",
      "runs",
      "created_at"
    ],
    "properties": {
      "workspace": {
        "type": "string",
        "minLength": 1
      },
      "goal": {
        "type": "string",
        "minLength": 1
      },
      "modules": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "sequence": {
        "type": "integer",
        "minimum": 1
      },
      "base_commit": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "parent_commit": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "readiness": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "run_id",
          "input_digest",
          "modules",
          "checks",
          "warnings"
        ],
        "properties": {
          "run_id": {
            "type": "string",
            "minLength": 1
          },
          "input_digest": {
            "type": "string",
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "modules": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "checks": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "check",
                "module",
                "status",
                "measured_digest"
              ],
              "properties": {
                "check": {
                  "type": "string",
                  "minLength": 1
                },
                "module": {
                  "type": "string",
                  "minLength": 1
                },
                "status": {
                  "const": "passed"
                },
                "measured_digest": {
                  "type": "string",
                  "pattern": "^sha256:[0-9a-f]{64}$"
                }
              }
            }
          },
          "warnings": {
            "type": "integer",
            "minimum": 0
          }
        }
      },
      "confirmations": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "module",
            "realization",
            "entry"
          ],
          "properties": {
            "module": {
              "type": "string",
              "minLength": 1
            },
            "realization": {
              "type": "string",
              "minLength": 1
            },
            "entry": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "runs": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "run_id",
            "kind",
            "name",
            "modules",
            "status",
            "summary",
            "worker_runs",
            "result_digest"
          ],
          "properties": {
            "run_id": {
              "type": "string",
              "minLength": 1
            },
            "kind": {
              "enum": [
                "operation",
                "command"
              ]
            },
            "name": {
              "type": "string",
              "minLength": 1
            },
            "modules": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "status": {
              "enum": [
                "ok",
                "blocked",
                "failed",
                "interrupted"
              ]
            },
            "summary": {
              "type": "string"
            },
            "worker_runs": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "result_digest": {
              "anyOf": [
                {
                  "type": "null"
                },
                {
                  "type": "string",
                  "pattern": "^sha256:[0-9a-f]{64}$"
                }
              ]
            }
          }
        }
      },
      "created_at": {
        "type": "string",
        "minLength": 1
      }
    }
  },
  "semantics": "The evidence committed with a delivery at .concorde/evidence/<workspace>/<sequence>.json, where sequence is one more than the number of delivery commits of the workspace on its branch since the base commit. workspace, goal and modules are copied from the workspace binding; base_commit is the binding's base commit and parent_commit the validated head the delivery commit is created on. readiness identifies this delivery run, which decided it with Validation's steps, and repeats its input digest, the Modules it covered, its check results without log paths and the number of its warnings; every check passed, because only a ready readiness is delivered. confirmations lists the pending entries whose markers this delivery cleared. runs lists every run of the workspace in the run store, Operation or recorded command, that started after the delivery run named by the previous delivery commit's Concorde-Readiness trailer, or at all when there is none, and before this delivery run, in start order: its kind and name, its Modules, its status and summary from its saved run result, the run record identities of its workers, and the SHA-256 digest of its saved result.json, or null with status interrupted when no result was saved. Run records, results and transcripts themselves stay uncommitted in the run store of the records directory. created_at is RFC 3339 in UTC. A behaviour or field change increments the version.",
  "example": {
    "workspace": "severity",
    "goal": "let Issue reports carry a severity",
    "modules": [
      "module.issues"
    ],
    "sequence": 1,
    "base_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "parent_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "readiness": {
      "run_id": "r-20260924T103800-delivery-77d0e4f5",
      "input_digest": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
      "modules": [
        "module.issues"
      ],
      "checks": [
        {
          "check": "check.issues.tests",
          "module": "module.issues",
          "status": "passed",
          "measured_digest": "sha256:6666666666666666666666666666666666666666666666666666666666666666"
        }
      ],
      "warnings": 1
    },
    "confirmations": [
      {
        "module": "module.issues",
        "realization": "realization.issues.store",
        "entry": "src/concorde/issues/severity.py"
      }
    ],
    "runs": [
      {
        "run_id": "r-20260924T090100-understand-3f2a9c01",
        "kind": "operation",
        "name": "understand",
        "modules": [
          "module.issues"
        ],
        "status": "ok",
        "summary": "Assessment completed; the Spec is sufficient and a plan was returned.",
        "worker_runs": [
          "w-20260924T090102-understand-11aa22bb"
        ],
        "result_digest": "sha256:7777777777777777777777777777777777777777777777777777777777777777"
      },
      {
        "run_id": "r-20260924T103000-task_validation-9b1c0d2e",
        "kind": "command",
        "name": "task-validation",
        "modules": [
          "module.issues"
        ],
        "status": "ok",
        "summary": "Readiness decided: ready.",
        "worker_runs": [],
        "result_digest": "sha256:8888888888888888888888888888888888888888888888888888888888888888"
      }
    ],
    "created_at": "2026-09-24T10:39:00Z"
  }
}
```

## Output

```concorde-contract
{
  "id": "contract.delivery.output",
  "version": 2,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "commit",
      "branch",
      "bundle",
      "sequence",
      "confirmed",
      "recovered"
    ],
    "properties": {
      "commit": {
        "type": "string",
        "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"
      },
      "branch": {
        "type": "string",
        "minLength": 1
      },
      "bundle": {
        "type": "string",
        "minLength": 1
      },
      "sequence": {
        "type": "integer",
        "minimum": 1
      },
      "confirmed": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "recovered": {
        "type": "boolean"
      }
    }
  },
  "semantics": "The output of a delivery run whose status is ok. commit is the delivery commit, now the head of branch, the workspace's bound branch; bundle is the project-relative path of its evidence bundle and sequence its number; confirmed lists the realization entries whose pending markers the delivery cleared. recovered is true when the run found that the branch head already is a delivery commit of the workspace and nothing waits to be delivered, such as after a delivery whose run ended after its commit, and reports that commit instead of committing; confirmed is then empty. A run whose status is not ok has no output. A behaviour or field change increments the version.",
  "example": {
    "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
    "branch": "concorde/severity",
    "bundle": ".concorde/evidence/severity/1.json",
    "sequence": 1,
    "confirmed": [
      "src/concorde/issues/severity.py"
    ],
    "recovered": false
  }
}
```
