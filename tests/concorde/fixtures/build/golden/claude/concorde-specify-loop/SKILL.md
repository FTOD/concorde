---
name: concorde-specify-loop
description: "Spec loop: route one change, author or revise its Spec, then independently review it; stop before planning and implementation."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-specify-loop/SKILL.md"
  kind: "skill"
  capability: "specify_loop"
  entrypoint: "scripts/run-capability.py concorde-specify-loop"
user-invocable: true
disable-model-invocation: false
---
# concorde-specify-loop

Invoke this capability to run the Spec loop. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-capability-invocation@3 JSON object on stdin to `python3 scripts/run-capability.py concorde-specify-loop`. Its exact fields
are type_id, schema_version:3, capability_id:"concorde-specify-loop", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-capability-configuration@1), and input (concorde-specify-loop-request@1).
New task requests require task and may supply target_id/focus_id (a scenario ID) as routing hints;
main discovery selects the owning target before the bounded loop starts. Existing changes retain
their bound target.
Optional `specify` (default true) and `run_reviews` (default true) select authoring and Spec review.
`specify:false` reviews the existing Spec without authoring. `run_reviews:false` records an explicit
Spec review skip unless that review was already required for this change. A later request cannot
cancel a recorded requirement. This loop does not require or skip code review.
Initialization uses its typed propose/apply request; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Main may explicitly admit complete Module Specs for routing, but cannot read implementation files.
It returns one typed route for this capability; the host then starts a different target worker.
When a mutation starts in the primary worktree, the host prepares a committed-base linked
worktree and returns its identity and a handoff draft; it does not launch the next outer session.
Follow P10 to start that session automatically with the returned worktree as its initial directory,
fresh context and its own Skills. Only if automatic startup is unavailable or cannot establish these
conditions, ask the user to open it manually with the complete copyable prompt. Stop development in
this conversation; never carry it or its worktree-owned Skill bodies across that boundary. Report Spec gaps
or blocked execution as returned; do not work around the boundary. Non-implementation agents never
receive implementation code or raw test logs.

This loop authors or revises the selected Module's owned Spec documents, then independently reviews
the complete contract and every affected consumer in separate fresh contexts. It returns `completed`
with artifact references after the selected Spec stages succeed. Explicit review skips remain
visible; completion never claims semantic completeness or implementation readiness.

Blocking findings, incomplete coverage and necessary contract gaps stop advancement. Preserve the
candidate, repair the missing contract and resume with fresh context. Accepted authoring and current
review evidence are retained for the same task. This loop does not plan, author implementation tasks,
write code, run code checks, mark ready or deliver. To continue implementation, invoke
`concorde-dev-loop` in the same change with the same task and constraints; it composes this loop and
then proceeds through planning, tasks, implementation, checks and code review.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-specify-loop-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-specify-loop-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-specify-loop-request": {
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
        "specify": {
          "type": "boolean"
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
