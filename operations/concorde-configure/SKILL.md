---
name: concorde-configure
description: "Run configure through Concorde's enforced Spec context and JSON boundary."
exposure: public
operation: operation.py
capabilities: []
---

# concorde-configure

Invoke this Operation to configure. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@2 JSON object on stdin to `{OPERATION}`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-configure", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-configure-request@1).
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
      "const": "concorde-configure-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-configure-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-configure-request": {
      "type": "object",
      "properties": {
        "configuration": {
          "type": "object",
          "properties": {
            "type_id": {
              "const": "concorde-operation-configuration"
            },
            "schema_version": {
              "type": "integer",
              "const": 1
            },
            "data": {
              "$ref": "#/$defs/concorde-operation-configuration"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "configuration"
      ],
      "additionalProperties": false
    },
    "concorde-operation-configuration": {
      "type": "object",
      "properties": {
        "integration": {
          "enum": [
            "codex",
            "claude"
          ]
        },
        "enforcement": {
          "enum": [
            "native",
            "outer"
          ]
        }
      },
      "required": [
        "integration",
        "enforcement"
      ],
      "additionalProperties": false
    }
  }
}
```
