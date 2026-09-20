---
name: concorde-issues
description: "Inspect, report, reopen or assess branch-local Issues; return needed repairs to the caller or verify current work without automatic delivery."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-issues.md"
  kind: "skill"
  operation: "issues"
  entrypoint: "scripts/run-operation.py concorde-issues"
---
# concorde-issues

Invoke this operation to manage or solve explicitly selected Issues. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 scripts/run-operation.py concorde-issues`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-issues", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@2), and input (the independently versioned concorde-issues-request; use the exact schema below).

Choose action list, show, report, reopen or solve. Show, reopen and solve require one issue_id;
expected_revision optionally rejects a changed selection. Report requires target_id and a classified
report; an append also names its issue_id and expected_revision inside the report. Reopen requires
a note. Only solve starts the bounded decision and verification lifecycle; other actions are
current-worktree bookkeeping. An Issue is not an implementation task, and reporting it neither
stops a running agent nor approves a repair.

Solve returns needed implementation or Spec repair to the calling agent with the selected target,
intended behavior and rationale. It does not author Specs, change implementation or start planning
or child development. The caller performs authorized Spec, paired metadata and registry edits or
selects retained Operations explicitly, then requests fresh verification with current inputs.
A return-to-caller result preserves the open Issue and is not completed repair or readiness.
Solve can run Issue-specific read-only verification, resolve, identify a duplicate or reject a
mistaken report from evidence without mandatory human approval. Unresolved product/design choices
are returned as needs-decision. Respect the host's bounded iteration limit and distinct execution
failures. Do not retry by widening permissions.

From the primary worktree the host copies the selected Issue's exact bytes, including an uncommitted
report, into the candidate worktree it creates, without copying unrelated edits, and solves there;
this session receives the candidate's result and continues the change with its change_id.
A successful solve ends at ready with the disposition included in verification. It does not deliver,
merge primary or claim another branch is fixed. Closed Issues remain recorded. Legacy Reflections
are archived history, never automatically converted or used as current approval.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-issues-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-issues-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-issues-request": {
      "type": "object",
      "properties": {
        "target_id": {
          "type": "string",
          "minLength": 1
        },
        "task": {
          "type": "string",
          "minLength": 1
        },
        "focus_id": {
          "type": "string",
          "minLength": 1
        },
        "constraints": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          }
        },
        "change_id": {
          "type": "string",
          "minLength": 1
        },
        "action": {
          "enum": [
            "list",
            "show",
            "report",
            "solve",
            "reopen"
          ]
        },
        "issue_id": {
          "type": "string",
          "minLength": 1,
          "pattern": "I-[0-9a-f]{32}"
        },
        "report": {
          "type": "object",
          "properties": {
            "report_key": {
              "type": "string",
              "minLength": 1
            },
            "type": {
              "enum": [
                "bug",
                "gap",
                "limitation"
              ]
            },
            "subtype": {
              "anyOf": [
                {
                  "enum": [
                    "implementation-spec-mismatch",
                    "spec-conflict",
                    "missing-contract"
                  ]
                },
                {
                  "type": "null"
                }
              ]
            },
            "title": {
              "type": "string",
              "minLength": 1
            },
            "description": {
              "type": "string",
              "minLength": 1
            },
            "impact": {
              "type": "string",
              "minLength": 1
            },
            "basis": {
              "type": "string",
              "minLength": 1
            },
            "owner_target_id": {
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
            "evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "path": {
                    "type": "string",
                    "minLength": 1
                  },
                  "description": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "path",
                  "description"
                ],
                "additionalProperties": false
              }
            },
            "issue_id": {
              "type": "string",
              "minLength": 1,
              "pattern": "I-[0-9a-f]{32}"
            },
            "expected_revision": {
              "type": "string",
              "minLength": 1,
              "pattern": "^sha256:[0-9a-f]{64}$"
            }
          },
          "required": [
            "report_key",
            "type",
            "subtype",
            "title",
            "description",
            "impact",
            "basis",
            "owner_target_id",
            "evidence"
          ],
          "additionalProperties": false
        },
        "expected_revision": {
          "type": "string",
          "minLength": 1,
          "pattern": "^sha256:[0-9a-f]{64}$"
        },
        "note": {
          "type": "string",
          "minLength": 1
        }
      },
      "required": [
        "action"
      ],
      "additionalProperties": false
    }
  }
}
```
