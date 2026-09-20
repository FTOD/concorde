---
name: concorde-code-review
description: "Operation: independently review or diagnose a Module's granted implementation against its Spec and return scoped read-only findings."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-code-review.md"
  kind: "skill"
  operation: "code_review"
  entrypoint: ".concorde/framework/scripts/run-operation.py concorde-code-review"
---
# concorde-code-review

Invoke this operation to review or diagnose the selected implementation against its Spec. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 .concorde/framework/scripts/run-operation.py concorde-code-review`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-code-review", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (the independently versioned concorde-code-review-request; use the exact schema below).

The request requires target_id and task. The calling agent selects the Module explicitly;
optional focus_id must name its scenario. Constraints and a current-worktree change_id may be
supplied. There is no implicit routing or review_mode selector. The host deterministically checks
the target and freezes its complete context before starting a fresh read-only reviewer.

Review runs in the current worktree without creating a development change or requiring a preexisting
Issue. It reads the complete selected Module contract and only its admitted implementation files,
external references and scoped changes. Reviewers have no write, network or credential grants.
The host persists review reports separately from reviewer authority.

A managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.
Do not claim this compares against another branch or a merge base. Report the returned review
coverage, Issue judgments and limitations, preserving incomplete or failed outcomes. Findings do
not authorize repairs. describe-policy previews grants without launching agents or persisting
review results. A separate review intent cannot replace another task's required lifecycle review.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-code-review-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 2
    },
    "data": {
      "$ref": "#/$defs/concorde-code-review-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-code-review-request": {
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
        }
      },
      "required": [
        "target_id",
        "task"
      ],
      "additionalProperties": false
    }
  }
}
```
