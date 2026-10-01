# Code review contracts

The exact shape of what [Code review](module.md) returns. The report is the `output` of the
[run result](../../../glossary.json#concept.run-result). Each reviewer supplies its summary,
`findings` and `resolved` as the Operation-specific part of its answer; the
[Operation](../../../glossary.json#concept.operation) adds the inputs it examined, the
[Issues](../../../glossary.json#concept.issue) it reported to, the outcomes and the verdict.

## Reviewer result

A reviewer ends with the ordinary [worker result](../../../glossary.json#concept.worker-result)
whose `output` is `{"findings": [...], "resolved": [...]}`. A finding is `{module, kind, tier,
title, problem, impact, basis, locations, evidence, suggestion}`, plus `earlier` when it is an
earlier Issue's problem, naming that Issue; it is a report finding without `issue`. `resolved`, which
may be left out, holds `{issue, reason}` for each earlier Issue the code no longer has. A `blocked`
or `failed` reviewer still returns an empty `findings` array.

## Code review report

```concorde-contract
{
  "id": "contract.code-review.review",
  "version": 3,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["scope", "base", "focus", "reviewed_paths", "named_only_paths", "checks",
                 "verdict", "modules"],
    "properties": {
      "scope": {"enum": ["change", "module"]},
      "base": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
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
            "outcome": {"enum": ["passed", "failed", "timed_out"]},
            "exit_code": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "log": {"type": "string", "minLength": 1}
          }
        }
      },
      "verdict": {"enum": ["accepted", "changes_required", "incomplete"]},
      "modules": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["module", "outcome", "context_identity", "summary", "findings",
                       "earlier_issues"],
          "properties": {
            "module": {"type": "string", "pattern": "^module\\."},
            "outcome": {"enum": ["accepted", "changes_required", "incomplete"]},
            "context_identity": {
              "anyOf": [{"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}, {"type": "null"}]
            },
            "summary": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
            "findings": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": ["module", "kind", "tier", "title", "problem", "impact", "basis",
                             "locations", "evidence", "suggestion", "issue"],
                "properties": {
                  "module": {"type": "string", "pattern": "^module\\."},
                  "kind": {"enum": ["violation", "defect", "missing-test", "out-of-scope",
                                    "spec-gap", "spec-challenge"]},
                  "tier": {"enum": ["suggestion", "obvious-fix", "preferred-fix",
                                    "decision-needed"]},
                  "title": {"type": "string", "minLength": 1},
                  "problem": {"type": "string", "minLength": 1},
                  "impact": {"type": "string", "minLength": 1},
                  "basis": {"type": "string", "minLength": 1},
                  "locations": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1}
                  },
                  "evidence": {"type": "string", "minLength": 1},
                  "suggestion": {"type": "string", "minLength": 1},
                  "earlier": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
                  "issue": {
                    "anyOf": [{"type": "string", "pattern": "^I-[0-9a-f]{32}$"}, {"type": "null"}]
                  }
                }
              }
            },
            "earlier_issues": {
              "anyOf": [
                {"type": "null"},
                {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["carried", "resolved", "ignored"],
                  "properties": {
                    "carried": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["issue", "tier", "title"],
                        "properties": {
                          "issue": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
                          "tier": {
                            "anyOf": [
                              {"enum": ["suggestion", "obvious-fix", "preferred-fix",
                                        "decision-needed"]},
                              {"type": "null"}
                            ]
                          },
                          "title": {"type": "string", "minLength": 1}
                        }
                      }
                    },
                    "resolved": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["issue", "reason"],
                        "properties": {
                          "issue": {"type": "string", "pattern": "^I-[0-9a-f]{32}$"},
                          "reason": {"type": "string", "minLength": 1}
                        }
                      }
                    },
                    "ignored": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["issue", "reason"],
                        "properties": {
                          "issue": {"type": "string", "minLength": 1},
                          "reason": {"type": "string", "minLength": 1}
                        }
                      }
                    }
                  }
                }
              ]
            }
          }
        }
      }
    }
  },
  "semantics": "One code review, of a workspace's changes (scope change) or of each named Module's whole code (scope module), against the reviewed Modules' Specs. base is the resolved commit the diff starts from, null in scope module; focus repeats --focus or is null. reviewed_paths lists the changed paths whose contents the reviewer received and named_only_paths those it received by name only, both empty in scope module, where each reviewer reads its Module's code through its grant. checks has one item per configured check result of the Operation, projected from Check execution's result without its digests: check is the check's identity, module its Module, outcome its status with timeout written timed_out, exit_code its exit status or null when it timed out, and log the path of its saved log; these fields are computed by the Operation. modules has one item per reviewed Module in the order named: context_identity is that of the grant its reviewer worked under, null when no grant was computed; summary is its reviewer's summary, null when no reviewer returned one; findings are its reviewer's claims about it, each with the Module it concerns, a kind (violation of a stated promise, defect the Spec's promises imply, missing test for a scenario the reviewed code touches, change outside the reviewed Modules' code, Spec gap, or Spec challenge of a promise the reviewer judges unreasonable or unrealizable), a tier, a title, the problem, its impact, its basis (a stable identity or a document path with an optional anchor from the reviewed Modules' Spec context), the locations that show it (a project path, optionally followed by :line or :first-last), the quoted evidence and a suggested repair. The Operation checks that every finding's Module was reviewed, that every basis resolves in the Spec context and that every location's file exists, in the worktree or among the changed paths, with its lines; issue is the Issue the Operation reported the finding to, null when it was not reported; earlier, present only when the Operation appended the finding to an earlier Issue it offered, names that Issue. earlier_issues is null when the Module's earlier Issues were never read; otherwise carried lists the earlier Issues no finding named and no resolution resolved, which still stand, resolved those the reviewer found the code no longer has, with its reason, for the task to close, and ignored the names a finding or resolution gave that were not offered or already settled. outcome is incomplete when the Module could not be reviewed or its Issues could not be read or all written, changes_required when an Issue of a blocking tier (obvious-fix, preferred-fix, decision-needed) stands for it, reported now or carried, and accepted otherwise; verdict is incomplete if any Module is, else changes_required if any is, else accepted. An accepted verdict is evidence about these inputs only.",
  "example": {
    "scope": "module",
    "base": null,
    "focus": null,
    "reviewed_paths": [],
    "named_only_paths": [],
    "checks": [
      {"check": "check.issues.store", "module": "module.issues", "outcome": "passed", "exit_code": 0, "log": "/home/dev/shop/.concorde/tasks/severity/workspace/runs/r-0003/checks/check.issues.store/output.log"}
    ],
    "verdict": "changes_required",
    "modules": [
      {
        "module": "module.issues",
        "outcome": "changes_required",
        "context_identity": "sha256:0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0",
        "summary": "The store keeps reports immutable except when a severity is saved.",
        "findings": [
          {
            "module": "module.issues",
            "kind": "violation",
            "tier": "obvious-fix",
            "title": "Saving a severity rewrites earlier reports",
            "problem": "Saving a report with a severity rewrites the severity of earlier reports of the same Issue.",
            "impact": "An Issue's history no longer shows what earlier reporters observed.",
            "basis": "req.issues.retention",
            "locations": ["src/concorde/issues/store.py:240-252"],
            "evidence": "store.py:244 assigns report['severity'] for every report of the record.",
            "suggestion": "Store the severity with the new report only.",
            "issue": "I-0123456789abcdef0123456789abcdef"
          }
        ],
        "earlier_issues": {"carried": [], "resolved": [], "ignored": []}
      }
    ]
  }
}
```
