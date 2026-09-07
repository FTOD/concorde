---
name: concorde-fast-loop
description: "Global development loop without Spec authoring: route one change, then plan, task, implement and validate to a ready candidate; reviews are optional and every skip is recorded."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-fast-loop/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-fast-loop/operation.py"
---
# concorde-fast-loop

Invoke this Operation to fast loop. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@2 JSON object on stdin to `python3 scripts/run-operation.py operations/concorde-fast-loop/operation.py`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-fast-loop", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-fast-loop-request@1).
New task requests require task and may supply target_id/focus_id as routing hints; main discovery
selects the owning target before the bounded loop starts. Existing changes retain their bound target.
Initialization uses its typed propose/apply request; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Main may inspect Domain/Service Specs on demand but cannot read Module Specs or code. It returns one
typed route for this Operation; the host then starts a different target worker. When a mutation starts in the primary worktree, the host prepares a committed-base linked
worktree and returns a handoff. Open a new agent in the returned worktree before continuing;
never carry this conversation or its worktree-owned Skills across that boundary. Report Spec gaps or blocked execution as returned; do not work
around the boundary. Non-implementation agents never receive implementation code or raw test logs.


This loop ends at a verified `ready` candidate in the current change worktree. It never
invokes deliver. Partial progress and gaps remain in `.concorde/worktree.json` and resume under
the same worktree change. Delivery is a separate request from a new agent opened in the primary
worktree; report its path and the change_id when the candidate is ready.

The standard loop requires independent Spec review after authoring and before planning, then
read-only code review after implementation/checks and before ready. Fast-loop run_reviews defaults
to false; both mode skips are recorded explicitly. A previously required review cannot be disabled
on retry. Required review failure, incomplete coverage and blocking findings stop advancement;
advisory findings remain in the review artifacts. Each mode and target uses a separate fresh
session. Changed inputs invalidate older conclusions. Necessary contract gaps persist in the existing
change state; repair the Spec and resume with a fresh context. No-finding review is not proof of
semantic completeness.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-fast-loop-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-fast-loop-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-fast-loop-request": {
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
        "run_reviews": {
          "type": "boolean"
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
