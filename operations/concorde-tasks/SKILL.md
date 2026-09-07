---
name: concorde-tasks
description: "Internal stage: author acceptance tasks from the accepted plan."
exposure: internal
operation: operation.py
capabilities: ["concorde-task-author"]
---

# concorde-tasks

This is an internal stage Operation. It receives an already routed `target_id` and one frozen
context snapshot from its composing Operation (`concorde-standard-dev-loop` or `concorde-fast-loop`);
it is never selected directly by a user or by main. It is not projected as a user-invocable Skill,
and the executable boundary rejects a direct invocation of `operations/concorde-tasks/operation.py`
with error code `internal_operation`.

A composing Operation invokes it in-process through `run_operation` with a
`concorde-tasks-request@1` TypedValue; the request requires target_id and task and accepts optional
focus_id, constraints and change_id, all supplied by the caller. Configuration is never a context
grant.

Use the supplied target identity; if it is ambiguous, ask the user to identify it instead of
searching other Specs. When a mutation starts in the primary worktree, the host prepares a committed-base linked
worktree and returns a handoff. Open a new agent in the returned worktree before continuing;
never carry this conversation or its worktree-owned Skills across that boundary. Report Spec gaps or blocked execution as returned; do not work
around the boundary. Non-implementation agents never receive implementation code or raw test logs.

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
      "const": 1
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
