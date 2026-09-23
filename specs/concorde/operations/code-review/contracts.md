# Code review contracts

The exact shape of what [Code review](module.md) returns. The report is the `output` of the
Operation result. The reviewer supplies `summary` and `findings` as the Operation-specific part of
its answer; the host adds the inputs it examined and derives the verdict.

## Code review report

```concorde-contract
{
  "id": "contract.code-review.review",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["base", "focus", "reviewed_paths", "named_only_paths", "checks", "summary",
                 "findings", "verdict"],
    "properties": {
      "base": {"type": "string", "minLength": 1},
      "focus": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
      "reviewed_paths": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "named_only_paths": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "checks": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["check", "module", "outcome", "exit_code", "log"],
          "properties": {
            "check": {"type": "string", "minLength": 1},
            "module": {"type": "string", "pattern": "^module\\."},
            "outcome": {"enum": ["passed", "failed", "timed_out", "not_started"]},
            "exit_code": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "log": {"type": "string", "minLength": 1}
          }
        }
      },
      "summary": {"type": "string", "minLength": 1},
      "findings": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["id", "severity", "kind", "module", "basis", "locations", "description",
                       "suggestion"],
          "properties": {
            "id": {"type": "string", "pattern": "^F[0-9]+$"},
            "severity": {"enum": ["blocking", "advisory"]},
            "kind": {"enum": ["violation", "defect", "missing-test", "out-of-scope", "spec-gap"]},
            "module": {"type": "string", "pattern": "^module\\."},
            "basis": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
            "locations": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "description": {"type": "string", "minLength": 1},
            "suggestion": {"type": "string", "minLength": 1}
          }
        }
      },
      "verdict": {"enum": ["clean", "changes_required"]}
    }
  },
  "semantics": "One review of the task's code changes against the bound Modules' Specs. base is the resolved commit the diff starts from and focus repeats --focus or is null. reviewed_paths lists the changed paths whose contents the reviewer received, named_only_paths the changed paths it received by name only, and checks the host's configured check results with identity, Module, outcome, exit code (null when it did not exit) and log path; these fields are computed by the host. summary and findings are the reviewer's claims. Each finding has a run-local id, a severity, a kind (violation of a stated promise, defect implied by the Spec, missing test for a touched scenario, change outside the bound Modules' code, or Spec gap), the bound Module it concerns, its basis (a stable identity or a document path with an anchor from the bound Modules' Spec context; required for a blocking finding and otherwise possibly null), the file locations that show it, what is wrong and a suggested direction. The host checks that every basis identity resolves and sets verdict to changes_required exactly when a finding is blocking, clean otherwise. A clean verdict is evidence about these inputs only.",
  "example": {
    "base": "0693972f",
    "focus": null,
    "reviewed_paths": ["src/concorde/issues/store.py", "tests/concorde/issues/test_store.py"],
    "named_only_paths": [],
    "checks": [
      {"check": "check.issues.store", "module": "module.issues", "outcome": "passed", "exit_code": 0, "log": ".concorde/runs/r-0003/checks/check.issues.store.log"}
    ],
    "summary": "The store accepts a severity but rewrites earlier reports when saving it.",
    "findings": [
      {
        "id": "F1",
        "severity": "blocking",
        "kind": "violation",
        "module": "module.issues",
        "basis": "req.issues.retention",
        "locations": ["src/concorde/issues/store.py:240"],
        "description": "Saving a report with a severity rewrites the severity of earlier reports of the same Issue.",
        "suggestion": "Store the severity with the new report only."
      }
    ],
    "verdict": "changes_required"
  }
}
```
