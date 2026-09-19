---
name: concorde-specify-loop
description: "Spec loop: route one change, author or revise its Spec, then independently review it; stop before planning and implementation."
argument-hint: "Optional operation guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-specify-loop.md"
  kind: "skill"
  operation: "specify_loop"
  entrypoint: "scripts/run-operation.py concorde-specify-loop"
user-invocable: true
disable-model-invocation: true
---
# concorde-specify-loop

Invoke this operation to run the Spec loop. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 scripts/run-operation.py concorde-specify-loop`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-specify-loop", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-specify-loop-request@1).
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
It returns one typed route for this operation; the host then starts a different target worker.
The user-facing session coordinates needs and may delegate a complete task to one fresh task
child, or handle a simple consumer-project task directly. Task children never delegate tasks or
move worktrees. They may run several public Operations on the same change through delivery;
bounded Operation workers still obey the actual harness's depth and permission limits.

A mutating Operation requested from a consumer primary normally runs in a host-created candidate;
an Operation already in an assigned candidate reuses it. The requesting session stays where it
started and receives path, branch and stable change_id. Uncommitted primary edits are not copied.
Durable status and runs belong only to the primary coordinator, not duplicate candidate archives.
Task-authorized `.concorde` edits in the owned workspace are not forbidden by directory name;
preserve task scope, truthful evidence and concurrency safety, and obey actual worker grants.

For Concorde source maintenance, the main creates a candidate and a fresh Skill-free maintenance
child with inherited/discovered catalogs disabled. After the writer checks, commits and stops,
a separate fresh sibling test child receives only exact candidate-built Skills and runtime
provenance. Neither forks old Skill bodies or delegates tasks. The tester never rewrites governing
Skills; failures return to maintenance and then a new tester. Maintenance may finish through
ordinary Git with explicit merge authorization, without Concorde delivery. Skill metadata alone
is not evidence of loading or execution. Never fall back to global or primary Skills.

Report Spec gaps or blocked execution as returned. Non-implementation workers never receive
implementation code or raw test logs.

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
