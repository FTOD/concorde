---
name: concorde-dev-loop
description: "Development loop: route one change, call specify-loop, then plan, task, implement, validate and review code to a ready candidate; specify=false skips authoring and run_reviews=false records explicit review skips."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-dev-loop.md"
  kind: "skill"
  operation: "dev_loop"
  entrypoint: "scripts/run-operation.py concorde-dev-loop"
---
# concorde-dev-loop

Invoke this operation to run the development loop. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 scripts/run-operation.py concorde-dev-loop`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-dev-loop", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-dev-loop-request@1).
New task requests require task and may supply target_id/focus_id (a scenario ID) as routing hints;
main discovery selects the owning target before the bounded loop starts. Existing changes retain
their bound target.
Optional `specify` (default true) and `run_reviews` (default true) flags select the loop shape.
`specify:false` skips Spec authoring for this pass, exactly like the former fast loop.
`run_reviews:false` records an explicit skip for each review mode instead of running it. A review
requirement already recorded for this change cannot be disabled by a later `run_reviews:false`;
every skip and every required review remains visible in the change record.

To repair an existing incomplete task list that incorrectly requires later Host validation,
review or commit before implementation can finish, pass `repair_task_scope:{tasks_digest:...}`.
The digest is `sha256:` plus SHA-256 of the UTF-8 canonical JSON task list (sorted keys, compact
separators, ASCII escaping as in Python `json.dumps`). The Host binds that exact list, supplies only semantic phase
feedback and the admitted plan/tasks to a fresh task author, preserves history and then runs
implementation, validation and required reviews normally. It preserves software acceptance and
does not edit the plan, complete tasks, grant permissions or skip checks. Replaying a consumed
digest resumes the replacement list; stale digests and unresolved gaps are rejected.
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

This loop ends at a verified `ready` candidate in the current change worktree. It never
invokes deliver. Partial progress and gaps remain in the primary-owned `.concorde/status/<change_id>.json` and resume under
the same worktree change. Delivery is a separate request from an agent whose initial working directory is either the
source change worktree or the destination primary worktree; report the participating paths and
change_id when the candidate is ready. Delivery creates an independent branch and removes the
candidate worktree by default. Only an explicit user request permits a separate final merge by
the primary worktree's sole writing agent; other agents must use linked worktrees.

The loop calls `concorde-specify-loop` for Spec authoring and review before planning. When enabled,
it requires independent Spec review after authoring and before planning, then
read-only code review after implementation/checks and before ready. A skipped review is recorded
explicitly rather than run. A review already required for this change cannot be disabled by a
later request. Required review failure, incomplete coverage and blocking findings stop advancement;
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
      "const": "concorde-dev-loop-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-dev-loop-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-dev-loop-request": {
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
        "task"
      ],
      "additionalProperties": false
    }
  }
}
```
