---
name: concorde-validate
description: "Lifecycle: run deterministic Spec and configured code checks and record readiness for the current candidate."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-validate/SKILL.md"
  kind: "skill"
  capability: "validate"
  entrypoint: "scripts/run-capability.py concorde-validate"
---
# concorde-validate

Invoke this capability to validate. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.
This is a deterministic lifecycle capability: it runs no agent cognition and selects no context.

Send one concorde-capability-invocation@3 JSON object on stdin to `python3 scripts/run-capability.py concorde-validate`. Its exact fields
are type_id, schema_version:3, capability_id:"concorde-validate", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-capability-configuration@1), and input (concorde-validate-request@1).
Task requests select target_id and task, with optional focus_id (a scenario ID), constraints, and
change_id.
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

Validation checks every Module's `module.md` for its four mandatory sections in order -- Purpose,
Scenarios, Entities, Architecture -- the syntax of its scenario, requirement and `concorde-entities`
declarations, unique stable IDs, and that the registry's `files` for a Module equal the sorted
union of its entities' `files`, entry for entry. A listing entry is an exact file or a directory
prefix ending in `/` that binds every regular file below it, so the registry repeats the prefix
rather than its expanded names. It also checks that the Architecture flowchart's node labels are
exactly the declared entity titles and that every edge carries a label. An entry an entity lists
whose file or directory does not exist and is not marked `pending` is an error; an entry still marked
`pending` after it exists on disk is a warning, and so is a regular file that no Module's entries
cover. Warnings are reported alongside errors but never by themselves turn a
successful validation into a failure; only errors do.

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
