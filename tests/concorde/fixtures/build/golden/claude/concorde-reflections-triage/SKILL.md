---
name: concorde-reflections-triage
description: "Global reflection queue: report status, capture recorded gaps, and investigate, implement, merge or close owned reflections."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-reflections-triage/SKILL.md"
  kind: "skill"
  capability: "reflections_triage"
  entrypoint: "scripts/run-capability.py concorde-reflections-triage"
user-invocable: true
disable-model-invocation: false
---
# concorde-reflections-triage

Invoke this capability to reflections triage. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.

Send one concorde-capability-invocation@3 JSON object on stdin to `python3 scripts/run-capability.py concorde-reflections-triage`. Its exact fields
are type_id, schema_version:3, capability_id:"concorde-reflections-triage", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-capability-configuration@1), and input (concorde-reflections-triage-request@1).
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

Use action=record-gaps with explicit gap_ids selected from the status response
`gap_records[].id` and an empty
reflection_ids array to preserve durable missing-contract reports in the existing queue. Each gap
keeps its host-bound target owner; a Domain may capture gaps of its participating components.
Repeated capture reuses the linked Reflection ID. Capture does not resolve gaps, investigate, approve
or implement a fix. For existing records, target_id names the owning target and focus_id may name its
Feature/API; a Feature/API ID is not itself a target and concerns is not ownership.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-reflections-triage-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-reflections-triage-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-reflections-triage-request": {
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
        "action": {
          "enum": [
            "status",
            "record-gaps",
            "investigate",
            "implement",
            "merge",
            "close"
          ]
        },
        "reflection_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          },
          "uniqueItems": true
        },
        "gap_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1,
            "pattern": "^sha256:[0-9a-f]{64}$"
          },
          "uniqueItems": true
        }
      },
      "required": [
        "target_id",
        "action",
        "reflection_ids"
      ],
      "additionalProperties": false
    }
  }
}
```
