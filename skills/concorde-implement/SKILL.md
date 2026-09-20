---
name: concorde-implement
description: "Operation: implement current accepted tasks inside the selected Module grant."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-implement.md"
  kind: "skill"
  operation: "implement"
  entrypoint: ".concorde/framework/scripts/run-operation.py concorde-implement"
---
# concorde-implement

Invoke this operation to implement current accepted tasks inside the selected Module grant. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 .concorde/framework/scripts/run-operation.py concorde-implement`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-implement", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@2), and input (the independently versioned concorde-implement-request; use the exact schema below).

Task requests select target_id and task, with optional focus_id (a scenario ID), constraints, and
change_id.

Requires a current accepted plan and tasks. The programmer may change only registered implementation files, never Specs, metadata or registry. Component work and necessary contract changes return to the calling agent for separate selection; no child workflow or Spec authoring runs automatically. Completion is not review, validation, readiness or delivery.

The calling agent chooses whether and when to invoke other Operations. Report invalid or stale
inputs and blockers explicitly; never reinterpret old evidence as fresh. describe-policy previews
the grant without launching a worker. Execution retains bounded context and authority.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-implement-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-implement-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-implement-request": {
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
