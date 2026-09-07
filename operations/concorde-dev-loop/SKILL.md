---
name: concorde-dev-loop
description: "Global development loop: route one change, then specify, review the Spec, plan, task, implement, validate and review code to a ready candidate; specify=false skips authoring and run_reviews=false records explicit review skips."
exposure: public
operation: operation.py
capabilities: ["concorde-coordinator", "concorde-specify", "concorde-review", "concorde-plan", "concorde-tasks", "concorde-implement", "concorde-validate"]
---

# concorde-dev-loop

This paired Operation exists for the package validator, the `concorde.json` operations inventory
and the managed-runtime launcher, kept working alongside the build for this stage. The authoritative
instructions for this capability are `skills/concorde-dev-loop/SKILL.md`, rendered into
`.claude/skills/concorde-dev-loop/SKILL.md` and `.agents/skills/concorde-dev-loop/SKILL.md` by
`python3 scripts/concorde.py build`.

Send one concorde-operation-invocation@2 JSON object on stdin to `{OPERATION}`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-dev-loop", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-dev-loop-request@1).

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
