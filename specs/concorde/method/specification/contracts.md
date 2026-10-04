# Specification contracts

The exact shape of what [Specification](module.md) returns. The
[Spec change](../../glossary.json#concept.spec-change) is the `output` of the
[run result](../../glossary.json#concept.run-result). The
[Operation](../../glossary.json#concept.operation) computes its observed fields; the worker
supplies only `summary`, `promise_changes` and `proposed_documents` as the Operation-specific part
of its answer.

## Spec change

```concorde-contract
{
  "id": "contract.specification.spec-change",
  "version": 3,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "intent",
      "summary",
      "changed_documents",
      "created_documents",
      "deleted_documents",
      "promise_changes",
      "proposed_documents",
      "affected_modules",
      "validation"
    ],
    "properties": {
      "intent": {
        "type": "string",
        "minLength": 1
      },
      "summary": {
        "type": "string",
        "minLength": 1
      },
      "changed_documents": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "created_documents": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "deleted_documents": {
        "type": "array",
        "items": {
          "type": "string",
          "minLength": 1
        }
      },
      "promise_changes": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "module",
            "kind",
            "id",
            "change",
            "description"
          ],
          "properties": {
            "module": {
              "type": "string",
              "pattern": "^module\\."
            },
            "kind": {
              "enum": [
                "requirement",
                "scenario",
                "contract",
                "concept",
                "realization",
                "relation",
                "explanation"
              ]
            },
            "id": {
              "anyOf": [
                {
                  "type": "string",
                  "minLength": 1
                },
                {
                  "type": "null"
                }
              ]
            },
            "change": {
              "enum": [
                "added",
                "changed",
                "removed"
              ]
            },
            "description": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "proposed_documents": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "module",
            "path",
            "role",
            "reason"
          ],
          "properties": {
            "module": {
              "type": "string",
              "pattern": "^module\\."
            },
            "path": {
              "type": "string",
              "minLength": 1
            },
            "role": {
              "enum": [
                "module",
                "implementation"
              ]
            },
            "reason": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "affected_modules": {
        "type": "array",
        "items": {
          "type": "string",
          "pattern": "^module\\."
        }
      },
      "validation": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "new_errors",
          "pre_existing_errors",
          "warnings"
        ],
        "properties": {
          "new_errors": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/finding"
            }
          },
          "pre_existing_errors": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/finding"
            }
          },
          "warnings": {
            "type": "array",
            "items": {
              "$ref": "#/$defs/finding"
            }
          }
        }
      }
    },
    "$defs": {
      "finding": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "rule_id",
          "path",
          "message"
        ],
        "properties": {
          "rule_id": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "anyOf": [
              {
                "type": "string",
                "minLength": 1
              },
              {
                "type": "null"
              }
            ]
          },
          "message": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "semantics": "The outcome of one specify run. intent repeats the --intent argument. summary, promise_changes and proposed_documents are the worker's claims: its account of the promises it added, changed or removed in each bound Module (id is the stable identity when the promise has one, null for an explanation), and the new documents it would need, with their owning Module and role, which it cannot create itself. When a blocked worker proposes documents of bound Modules in the folders of their entries, the Operation creates them empty and launches a second worker once; the second worker's proposals are only reported. Every other field is computed by the Operation from the workspace after the audit. changed_documents lists every changed or new reading or metadata file, the project glossary when it changed, and every document the Operation created with its metadata and the metadata of the entry whose owns registers it. created_documents lists the documents the Operation created, empty and owned, for a second worker to fill, because the first proposed them; each also appears in changed_documents. deleted_documents lists every owned document file the Operation deleted at the worker's request inside the grant. affected_modules lists every Module whose Spec context, before or after the change, contains a changed or deleted document. validation holds the structural findings after the change, split into errors the baseline did not have, errors it already had, and warnings; a finding matches a baseline one when its rule_id, path and message match. The run's status is ok only when new_errors is empty and the worker ended ok.",
  "example": {
    "intent": "add an optional severity to Issue reports",
    "summary": "Added severity to the report contract and a scenario for reporting with a severity.",
    "changed_documents": [
      "specs/concorde/issues/interface.md",
      "specs/concorde/issues/scenarios.md"
    ],
    "created_documents": [],
    "deleted_documents": [],
    "promise_changes": [
      {
        "module": "module.issues",
        "kind": "contract",
        "id": "contract.issues.report",
        "change": "changed",
        "description": "reports may carry severity low, medium or high"
      },
      {
        "module": "module.issues",
        "kind": "scenario",
        "id": "scenario.issues.report-severity",
        "change": "added",
        "description": "a report with a severity is saved with it"
      }
    ],
    "proposed_documents": [],
    "affected_modules": [
      "module.issues",
      "module.main-session"
    ],
    "validation": {
      "new_errors": [],
      "pre_existing_errors": [],
      "warnings": []
    }
  }
}
```
