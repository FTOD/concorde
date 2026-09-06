---
name: concorde-constitution
description: "Run constitution through Concorde's enforced Spec context and JSON boundary."
exposure: public
operation: operation.py
capabilities: ["concorde-coordinator", "concorde-spec-author"]
---

# concorde-constitution

Invoke this Operation to constitution. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@2 JSON object on stdin to `{OPERATION}`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-constitution", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-constitution-request@1).
New task requests require task and may supply target_id/focus_id as routing hints; main discovery
selects the owning target before the bounded author starts. Existing changes retain their bound target.
Initialization/migration use their typed propose/apply requests; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Main may inspect Domain/Service Specs on demand but cannot read Module Specs or code. It returns one
typed route for this Operation; the host then starts a different target worker. The host captures a committed-base worktree for mutations when necessary.
Its result names that workspace. Report Spec gaps or blocked execution as returned; do not work
around the boundary. Non-implementation agents never receive implementation code or raw test logs.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-constitution-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-constitution-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-constitution-request": {
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
        "task"
      ],
      "additionalProperties": false
    }
  }
}
```
