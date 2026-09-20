---
name: concorde-tasks
description: "Operation: derive implementation acceptance tasks from the current accepted plan."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-tasks.md"
  kind: "skill"
  operation: "tasks"
  entrypoint: "scripts/run-operation.py concorde-tasks"
---
# concorde-tasks

Invoke this operation to derive implementation acceptance tasks from the current accepted plan. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 scripts/run-operation.py concorde-tasks`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-tasks", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (the independently versioned concorde-tasks-request; use the exact schema below).

Task requests select target_id and task, with optional focus_id (a scenario ID), constraints, and
change_id.

Requires the managed change and current accepted plan for the same intent. Returns new incomplete tasks, preserving prior task identities in history. Optional repair_task_scope binds the exact incomplete task-list digest; optional repair_review names a current blocking code-review ArtifactRef for this same intent. Neither field bypasses currentness or review gates.

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
      "const": "concorde-tasks-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 2
    },
    "data": {
      "$ref": "#/$defs/concorde-tasks-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-tasks-request": {
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
        "repair_review": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "minLength": 1
            },
            "path": {
              "type": "string",
              "minLength": 1
            },
            "digest": {
              "type": "string",
              "minLength": 1,
              "pattern": "^sha256:[0-9a-f]{64}$"
            }
          },
          "required": [
            "id",
            "path",
            "digest"
          ],
          "additionalProperties": false
        },
        "repair_task_scope": {
          "type": "object",
          "properties": {
            "tasks_digest": {
              "type": "string",
              "minLength": 1,
              "pattern": "^sha256:[0-9a-f]{64}$"
            }
          },
          "required": [
            "tasks_digest"
          ],
          "additionalProperties": false
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
