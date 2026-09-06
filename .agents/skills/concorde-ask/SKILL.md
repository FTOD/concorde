---
name: concorde-ask
description: "Run ask through Concorde's enforced Spec context and JSON boundary."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-ask/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-ask/operation.py"
---
# concorde-ask

Invoke this Operation to ask through a separate main coordinator and one or more fresh target
readers. The main coordinator starts from the project's entry Domain or Service and may expand only
registered Domain and Service Specs. It cannot read Module Specs or implementation code. After it
returns typed routes, the host resolves each selected target privately and starts a different reader
process. Supply the user's task as typed input; do not perform it directly in this ambient
conversation or inspect project files.

Send one concorde-operation-invocation@2 JSON object on stdin to `python3 scripts/run-operation.py operations/concorde-ask/operation.py`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-ask", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-ask-request@1).
Ask requests require task and accept optional target_id/focus_id routing hints and constraints.
The hint never grants Spec access to the main coordinator. Other task Operations select target_id
and task, with optional focus_id, constraints, and change_id.
Initialization/migration use their typed propose/apply requests; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

The main coordinator expands Domain/Service context only as needed and records the exact ordered
membership and digests in every discovery identity. A Module may be selected from responsibilities
stated in an admitted Domain or Service, but its Spec is visible only to the fresh target reader.
The public result contains routes, typed worker results and the synthesized answer; it never contains
raw Spec bodies. Report Spec gaps or blocked execution as returned and do not work around the
boundary. Non-implementation agents never receive implementation code or raw test logs.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-ask-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-ask-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-ask-request": {
      "type": "object",
      "properties": {
        "task": {
          "type": "string",
          "minLength": 1
        },
        "target_id": {
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
