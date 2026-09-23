# Operations contracts

The canonical envelope every Operation of [Operations](module.md) returns. How the host fills it is
in [How the host runs an Operation](host.md).

## Operation result

```concorde-contract
{
  "id": "contract.operations.result",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["operation", "task", "modules", "run_id", "status", "summary", "output",
                 "worker", "worker_runs", "host_evidence", "escalation", "started_at",
                 "finished_at"],
    "properties": {
      "operation": {"type": "string", "pattern": "^[a-z][a-z_]*$"},
      "task": {"type": "string", "minLength": 1},
      "modules": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "run_id": {"type": "string", "pattern": "^r-[0-9]{8}T[0-9]{6}-[a-z_]+-[0-9a-f]{8}$"},
      "status": {"enum": ["ok", "blocked", "failed"]},
      "summary": {"type": "string", "minLength": 1},
      "output": {"anyOf": [{"type": "null"}, {"type": "object"}]},
      "worker": {"anyOf": [{"type": "null"}, {"type": "object"}]},
      "worker_runs": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "host_evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
      "escalation": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/escalation"}]},
      "started_at": {"type": "string", "minLength": 1},
      "finished_at": {"type": "string", "minLength": 1}
    },
    "$defs": {
      "evidence": {
        "type": "object",
        "additionalProperties": false,
        "required": ["kind", "ref", "detail"],
        "properties": {
          "kind": {"type": "string", "minLength": 1},
          "ref": {"type": "string"},
          "detail": {"type": "string"}
        }
      },
      "escalation": {
        "type": "object",
        "additionalProperties": false,
        "required": ["source", "problem", "attempts", "options", "recommendation", "blocking",
                     "impact"],
        "properties": {
          "source": {"enum": ["worker", "host"]},
          "problem": {"type": "string", "minLength": 1},
          "attempts": {"type": "array", "items": {"type": "string"}},
          "options": {"type": "array", "items": {"type": "string"}},
          "recommendation": {"type": "string"},
          "blocking": {"type": "boolean"},
          "impact": {"type": "string"}
        }
      }
    }
  },
  "semantics": "The envelope of one Operation run, printed by concorde run and saved as .concorde/runs/<run_id>/result.json in the primary worktree. operation is a catalog name; task, modules and run_id identify the run, and modules may be empty only when the run was refused before its Modules were resolved. status ok means the Operation did what it promises; blocked means it cannot continue without a decision of the main agent; failed means an error of the host, the worker, the audit or the checks, or a refusal before the run began. summary is written by the host. output is the Operation-specific value defined by the provider's output contract, or null when the run produced none. worker is the last worker result exactly as the worker returned it, or null for a run without a worker; its content is the worker's claim and never host evidence. worker_runs lists the run records written for the run's worker launches, in launch order. host_evidence holds only facts the host produced itself; kind is one of grant, context-identity, audit, check, rounds, transcript, stderr, refused, cancelled, host-error, invalid-output, record, git, readiness or commit, or a kind the provider's own Spec defines, such as structural or finding-scope, ref names the path, command or identity concerned and detail explains it. escalation is null exactly when status is ok; otherwise source tells whether the worker's result or the host raised it, and its fields have the meaning of the worker result's fields of the same names. Timestamps are RFC 3339 in UTC. A behaviour or field change increments the version.",
  "example": {
    "operation": "implement",
    "task": "severity",
    "modules": ["module.issues"],
    "run_id": "r-20260924T093000-implement-5c1e0a77",
    "status": "failed",
    "summary": "The worker finished, the audit was clean, but check.issues.tests still failed after 3 resume rounds.",
    "output": null,
    "worker": {
      "status": "ok",
      "summary": "Added the severity field to reports and updated the store.",
      "problem": "",
      "attempts": ["edited src/concorde/issues/shapes.py", "edited src/concorde/issues/store.py"],
      "evidence": [],
      "options": [],
      "recommendation": "",
      "blocking": false,
      "impact": ""
    },
    "worker_runs": ["w-20260924T093001-implement-0f3b2a91"],
    "host_evidence": [
      {"kind": "grant", "ref": "sha256:7d1f", "detail": "implement grant for module.issues"},
      {"kind": "audit", "ref": "", "detail": "2 files changed, all inside the grant"},
      {"kind": "check", "ref": "check.issues.tests", "detail": "exit 1; log .concorde/runs/w-20260924T093001-implement-0f3b2a91/checks/3.log"},
      {"kind": "rounds", "ref": "", "detail": "3 of 3 resume rounds used"}
    ],
    "escalation": {
      "source": "host",
      "problem": "check.issues.tests fails in test_store.py::test_severity_round_trip after the last resume round.",
      "attempts": ["3 resume rounds with the failing output"],
      "options": ["run implement again with a narrower goal", "run understand to check whether the Spec defines severity storage"],
      "recommendation": "run understand for module.issues",
      "blocking": true,
      "impact": "The task cannot be validated until the check passes."
    },
    "started_at": "2026-09-24T09:30:00Z",
    "finished_at": "2026-09-24T09:52:00Z"
  }
}
```
