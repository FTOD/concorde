---
name: concorde-resolve-context
description: "Run resolve-context through Concorde's enforced Spec context and JSON boundary."
exposure: public
operation: operation.py
capabilities: []
---

# concorde-resolve-context

Invoke this deterministic Operation to resolve one context manifest. The host constructs the
complete cognitive snapshot internally but returns only target, phase, membership, Protocol binding
and content digests. Raw Spec or Protocol bodies never cross this public boundary. Supply the user's
task as typed input; do not inspect project files directly.

Send one concorde-operation-invocation@2 JSON object on stdin to `{OPERATION}`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-resolve-context", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-resolve-context-request@1).
Task requests select target_id and task, with optional focus_id, constraints, and change_id.
Initialization/migration use their typed propose/apply requests; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Use the supplied target identity. The returned manifest proves what the host would admit but is not
itself worker context. Report blocked execution as returned; do not reconstruct or fetch document
bodies from its paths or digests.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-resolve-context-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-resolve-context-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-resolve-context-request": {
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
        "phase": {
          "enum": [
            "ask",
            "specify",
            "plan",
            "tasks",
            "implementation",
            "spec-review",
            "code-review",
            "validate",
            "deliver",
            "context-solve"
          ]
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
