---
name: concorde-validate
description: "Lifecycle: run deterministic Spec and configured code checks and record readiness for the current candidate."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-validate/SKILL.md"
  kind: "skill"
  capability: "validate"
  entrypoint: "scripts/run-capability.py concorde-validate"
---
# concorde-validate

Invoke this Operation to validate. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.
This is a deterministic lifecycle Operation: it runs no agent cognition and selects no context.

Send one concorde-operation-invocation@2 JSON object on stdin to `python3 scripts/run-capability.py concorde-validate`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-validate", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-validate-request@1).
Task requests select target_id and task, with optional focus_id, constraints, and change_id.
Initialization uses its typed propose/apply request; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Use the supplied target identity; if it is ambiguous, ask the user to identify it instead of
searching other Specs.
When a mutation starts in the primary worktree, the host prepares a committed-base linked
worktree and returns a handoff. Open a new agent in the returned worktree before continuing;
never carry this conversation or its worktree-owned Skills across that boundary. Report Spec gaps
or blocked execution as returned; do not work around the boundary. Non-implementation agents never
receive implementation code or raw test logs.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-validate-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-validate-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-validate-request": {
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
        "run_checks": {
          "type": "boolean"
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
