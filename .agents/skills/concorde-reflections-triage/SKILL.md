---
name: concorde-reflections-triage
description: "Run reflections-triage through Concorde's enforced Spec context and JSON boundary."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-reflections-triage/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-reflections-triage/operation.py"
---
# concorde-reflections-triage

Invoke this Operation to reflections triage. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@2 JSON object on stdin to `python3 scripts/run-operation.py operations/concorde-reflections-triage/operation.py`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-reflections-triage", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-reflections-triage-request@1).
Task requests select target_id and task, with optional focus_id, constraints, and change_id.
Initialization/migration use their typed propose/apply requests; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Use the supplied target identity; if it is ambiguous, ask the user to identify it instead of
searching other Specs. The host captures a committed-base worktree for mutations when necessary.
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
      "const": "concorde-reflections-triage-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-reflections-triage-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-reflections-triage-request": {
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
            "status",
            "investigate",
            "implement",
            "merge",
            "close"
          ]
        },
        "reflection_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          },
          "uniqueItems": true
        }
      },
      "required": [
        "target_id",
        "action",
        "reflection_ids"
      ],
      "additionalProperties": false
    }
  }
}
```
