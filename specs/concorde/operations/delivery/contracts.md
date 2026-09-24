# Delivery contracts

The exact commit, evidence bundle and output of the `delivery` Operation of [Delivery](module.md).

## Delivery commit

```text
concorde: deliver <task-id>

<goal of the task>

Concorde-Task: <task-id>
Concorde-Evidence: .concorde/evidence/<task-id>/<n>.json
Concorde-Readiness: <run identity of this delivery run, which decided the readiness>
```

The commit uses the repository's configured author identity and runs the repository's commit hooks
normally. Its parent is the head of the task branch that the delivery validated, whose commits
since the base commit the readiness examined. It contains every uncommitted change of the task
worktree that Git does not ignore, except an untracked path Git cannot version (neither a regular
file, a symbolic link nor a directory), the metadata changed by the applied confirmations and the
evidence bundle; when every step was committed before, only the bundle and any cleared markers.

## Evidence bundle

```concorde-contract
{
  "id": "contract.delivery.evidence-bundle",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["task", "goal", "modules", "sequence", "base_commit", "parent_commit",
                 "readiness", "confirmations", "runs", "created_at"],
    "properties": {
      "task": {"type": "string", "minLength": 1},
      "goal": {"type": "string", "minLength": 1},
      "modules": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "sequence": {"type": "integer", "minimum": 1},
      "base_commit": {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"},
      "parent_commit": {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"},
      "readiness": {
        "type": "object",
        "additionalProperties": false,
        "required": ["run_id", "input_digest", "modules", "checks", "warnings"],
        "properties": {
          "run_id": {"type": "string", "minLength": 1},
          "input_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
          "modules": {"type": "array", "items": {"type": "string", "minLength": 1}},
          "checks": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["check", "module", "status", "measured_digest"],
              "properties": {
                "check": {"type": "string", "minLength": 1},
                "module": {"type": "string", "minLength": 1},
                "status": {"const": "passed"},
                "measured_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
              }
            }
          },
          "warnings": {"type": "integer", "minimum": 0}
        }
      },
      "confirmations": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["module", "realization", "entry"],
          "properties": {
            "module": {"type": "string", "minLength": 1},
            "realization": {"type": "string", "minLength": 1},
            "entry": {"type": "string", "minLength": 1}
          }
        }
      },
      "runs": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["run_id", "operation", "modules", "status", "summary", "worker_runs",
                       "result_digest"],
          "properties": {
            "run_id": {"type": "string", "minLength": 1},
            "operation": {"type": "string", "minLength": 1},
            "modules": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "status": {"enum": ["ok", "blocked", "failed", "interrupted"]},
            "summary": {"type": "string"},
            "worker_runs": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "result_digest": {"anyOf": [{"type": "null"},
                                        {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}]}
          }
        }
      },
      "created_at": {"type": "string", "minLength": 1}
    }
  },
  "semantics": "The evidence committed with a delivery at .concorde/evidence/<task>/<sequence>.json, where sequence counts the task's deliveries from 1. goal and modules are copied from the task record; base_commit is the task's base commit and parent_commit the validated head the delivery commit is created on. readiness identifies this delivery run, which decided it with Validation's steps, and repeats its input digest, the Modules it covered, its check results without log paths and the number of its warnings; every check passed, because only a ready readiness is delivered. confirmations lists the pending entries whose markers this delivery cleared. runs lists every Operation run of the task that started after the previous delivery and before this one, in start order, excluding this delivery run: its status and summary from its saved Operation result, the run record identities of its workers, and the SHA-256 digest of its saved result.json, or null with status interrupted when no result was saved. Run records, results and transcripts themselves stay uncommitted in the primary worktree's .concorde/runs/. created_at is RFC 3339 in UTC.",
  "example": {
    "task": "severity",
    "goal": "let Issue reports carry a severity",
    "modules": ["module.issues"],
    "sequence": 1,
    "base_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "parent_commit": "d460b95e0c1a2b3c4d5e6f708192a3b4c5d6e7f8",
    "readiness": {
      "run_id": "r-20260924T103800-delivery-77d0e4f5",
      "input_digest": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
      "modules": ["module.issues"],
      "checks": [
        {"check": "check.issues.tests", "module": "module.issues", "status": "passed",
         "measured_digest": "sha256:6666666666666666666666666666666666666666666666666666666666666666"}
      ],
      "warnings": 1
    },
    "confirmations": [
      {"module": "module.issues", "realization": "realization.issues.store",
       "entry": "src/concorde/issues/severity.py"}
    ],
    "runs": [
      {"run_id": "r-20260924T090100-understand-3f2a9c01", "operation": "understand",
       "modules": ["module.issues"], "status": "ok",
       "summary": "Assessment completed; the Spec is sufficient and a plan was returned.",
       "worker_runs": ["w-20260924T090102-understand-11aa22bb"],
       "result_digest": "sha256:7777777777777777777777777777777777777777777777777777777777777777"},
      {"run_id": "r-20260924T103000-validate-9b1c0d2e", "operation": "validate",
       "modules": ["module.issues"], "status": "ok",
       "summary": "Readiness decided: ready.",
       "worker_runs": [],
       "result_digest": "sha256:8888888888888888888888888888888888888888888888888888888888888888"}
    ],
    "created_at": "2026-09-24T10:39:00Z"
  }
}
```

## Output

```concorde-contract
{
  "id": "contract.delivery.output",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["commit", "branch", "bundle", "sequence", "confirmed", "recovered"],
    "properties": {
      "commit": {"type": "string", "pattern": "^[0-9a-f]{40}([0-9a-f]{24})?$"},
      "branch": {"type": "string", "minLength": 1},
      "bundle": {"type": "string", "minLength": 1},
      "sequence": {"type": "integer", "minimum": 1},
      "confirmed": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "recovered": {"type": "boolean"}
    }
  },
  "semantics": "The output of a delivery run whose status is ok. commit is the delivery commit, now the head of branch; bundle is the project-relative path of its evidence bundle and sequence its number; confirmed lists the realization entries whose pending markers the delivery cleared. recovered is true when the run found an existing delivery commit of the task at the branch head that the task record lacked and recorded it instead of committing; confirmed is then empty. A run whose status is not ok has no output.",
  "example": {
    "commit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
    "branch": "concorde/severity",
    "bundle": ".concorde/evidence/severity/1.json",
    "sequence": 1,
    "confirmed": ["src/concorde/issues/severity.py"],
    "recovered": false
  }
}
```
