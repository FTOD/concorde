---
name: concorde-context
description: "Run context through Concorde's enforced Spec context and JSON boundary."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-context/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-context/operation.py"
user-invocable: true
disable-model-invocation: false
---
# concorde-context

Invoke this deterministic Operation to inspect one context manifest. The host resolves the complete
snapshot internally but returns only target, phase, membership, Protocol binding and content
digests. Raw Spec or Protocol bodies never cross this public boundary. Supply the user's task as
typed input; do not inspect project files directly.

Send one concorde-operation-invocation@2 JSON object on stdin to `python3 scripts/run-operation.py operations/concorde-context/operation.py`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-context", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-context-request@1).
Task requests select target_id and task, with optional focus_id, constraints, and change_id.
Initialization/migration use their typed propose/apply requests; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Use the supplied target identity. This diagnostic manifest is not a cognitive context and cannot be
passed to a worker as a replacement for host resolution. Report blocked execution as returned; do
not try to reconstruct document bodies from paths or digests.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-context-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-context-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-context-request": {
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
