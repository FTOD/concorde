---
name: concorde-dev-loop
description: "Global development loop: route one change, then specify, review the Spec, plan, task, implement, validate and review code to a ready candidate; specify=false skips authoring and run_reviews=false records explicit review skips."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-dev-loop/SKILL.md"
  kind: "skill"
  capability: "dev_loop"
  entrypoint: "scripts/run-capability.py concorde-dev-loop"
---
# concorde-dev-loop

Invoke this capability to run the development loop. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-capability-invocation@3 JSON object on stdin to `python3 scripts/run-capability.py concorde-dev-loop`. Its exact fields
are type_id, schema_version:3, capability_id:"concorde-dev-loop", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-capability-configuration@1), and input (concorde-dev-loop-request@1).
New task requests require task and may supply target_id/focus_id as routing hints; main discovery
selects the owning target before the bounded loop starts. Existing changes retain their bound target.
Optional `specify` (default true) and `run_reviews` (default true) flags select the loop shape.
`specify:false` skips Spec authoring for this pass, exactly like the former fast loop.
`run_reviews:false` records an explicit skip for each review mode instead of running it. A review
requirement already recorded for this change cannot be disabled by a later `run_reviews:false`;
every skip and every required review remains visible in the change record.
Initialization uses its typed propose/apply request; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Main may explicitly admit complete Module Specs for routing, but cannot read Implementation Specs or code. It returns one
typed route for this capability; the host then starts a different target worker.
When a mutation starts in the primary worktree, the host prepares a committed-base linked
worktree and returns its identity and a handoff draft; it does not launch the next outer session.
Follow P10 to start that session automatically with the returned worktree as its initial directory,
fresh context and its own Skills. Only if automatic startup is unavailable or cannot establish these
conditions, ask the user to open it manually with the complete copyable prompt. Stop development in
this conversation; never carry it or its worktree-owned Skill bodies across that boundary. Report Spec gaps
or blocked execution as returned; do not work around the boundary. Non-implementation agents never
receive implementation code or raw test logs.

This loop ends at a verified `ready` candidate in the current change worktree. It never
invokes deliver. Partial progress and gaps remain in `.concorde/worktree.json` and resume under
the same worktree change. Delivery is a separate request from an agent whose initial working directory is either the
source change worktree or the destination primary worktree; report the participating paths and
change_id when the candidate is ready. Delivery creates an independent branch and removes the
candidate worktree by default. Only an explicit user request permits a separate final merge by
the primary worktree's sole writing agent; other agents must use linked worktrees.

When enabled, the loop requires independent Spec review after authoring and before planning, then
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
