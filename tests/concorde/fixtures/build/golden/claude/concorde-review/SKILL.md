---
name: concorde-review
description: "Global review: route a standalone Spec review, code review or source diagnosis to its owning Module and return scoped, read-only findings."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-review/SKILL.md"
  kind: "skill"
  capability: "review"
  entrypoint: "scripts/run-capability.py concorde-review"
user-invocable: true
disable-model-invocation: false
---
# concorde-review

Invoke this capability to review the selected Spec or implementation. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-capability-invocation@3 JSON object on stdin to `python3 scripts/run-capability.py concorde-review`. Its exact fields
are type_id, schema_version:3, capability_id:"concorde-review", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-capability-configuration@1), and input (concorde-review-request@1).

The request requires task and review_mode (spec or code). Use code for code review or source
diagnosis, and spec for contract review. A new task may supply target_id and focus_id (a scenario
ID) as routing hints, plus constraints. The coordinator selects the owning Module. When resuming
a bound review with change_id, supply its target_id and current-worktree change_id.
No positional task arguments or domain flags are accepted.

Main may explicitly admit complete Module Specs for routing, but cannot read implementation files.
It returns one typed route for this capability; the host then starts a fresh read-only reviewer.

Review runs in the current worktree without creating a development change or requiring a
Reflection. Spec review reads the complete selected Module contract; code review also reads only
its admitted implementation files and scoped changes. Reviewers have no write, network or
credential grants. The host persists review reports separately from reviewer authority.

A managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.
Do not claim this compares against another branch or a merge base. Report the returned review
coverage, findings, gaps and limitations, preserving incomplete or failed outcomes. Findings do
not authorize repairs. describe-policy previews grants without launching agents or persisting
review results. A separate review intent cannot replace another task's required lifecycle review.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-review-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-review-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-review-request": {
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
        "review_mode": {
          "enum": [
            "spec",
            "code"
          ]
        }
      },
      "required": [
        "task",
        "review_mode"
      ],
      "additionalProperties": false
    }
  }
}
```
