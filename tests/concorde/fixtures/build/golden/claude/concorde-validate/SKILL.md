---
name: concorde-validate
description: "Lifecycle: run deterministic Spec and configured code checks and record readiness for the current candidate."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-validate/SKILL.md"
  kind: "skill"
  capability: "validate"
  entrypoint: "scripts/run-capability.py concorde-validate"
user-invocable: true
disable-model-invocation: false
---
# concorde-validate

Invoke this capability to validate. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.
This is a deterministic lifecycle capability: it runs no agent cognition and selects no context.

Send one concorde-capability-invocation@3 JSON object on stdin to `python3 scripts/run-capability.py concorde-validate`. Its exact fields
are type_id, schema_version:3, capability_id:"concorde-validate", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-capability-configuration@1), and input (concorde-validate-request@1).
Task requests select target_id and task, with optional focus_id, constraints, and change_id.
Initialization uses its typed propose/apply request; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Use the supplied target identity; if it is ambiguous, ask the user to identify it instead of
searching other Specs.
When a mutation starts in the primary worktree, the host prepares a committed-base linked
worktree and returns its identity and a handoff draft; it does not launch the next outer session.
Follow P10 to start that session automatically with the returned worktree as its initial directory,
fresh context and its own Skills. Only if automatic startup is unavailable or cannot establish these
conditions, ask the user to open it manually with the complete copyable prompt. Stop development in
this conversation; never carry it or its worktree-owned Skill bodies across that boundary. Report Spec gaps
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
