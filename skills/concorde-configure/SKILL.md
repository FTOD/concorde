---
name: concorde-configure
description: "Operation: apply the Pi worker model selection (model, thinking level, timeout and per-worker overrides); with accept_protocol, rebind the project to the installed Protocol copy."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-configure.md"
  kind: "skill"
  operation: "configure"
  entrypoint: ".concorde/framework/scripts/run-operation.py concorde-configure"
---
# concorde-configure

Invoke this operation to configure. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.
This is a deterministic lifecycle operation: it runs no agent cognition and selects no context.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 .concorde/framework/scripts/run-operation.py concorde-configure`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-configure", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@2), and input (the independently versioned concorde-configure-request; use the exact schema below).
Task requests select target_id and task, with optional focus_id (a scenario ID), constraints, and
change_id.
Initialization uses its typed propose/apply request; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Use the supplied target identity; if it is ambiguous, ask the user to identify it instead of
searching other Specs.
The user-facing session coordinates needs and may delegate a complete task to one fresh task
child, or handle a simple consumer-project task directly. Task children never delegate tasks or
move worktrees. They may run several public Operations on the same change through delivery;
Operation workers are terminal nodes scheduled by the Graph/host and retain their file/tool grants.

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

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-configure-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 2
    },
    "data": {
      "$ref": "#/$defs/concorde-configure-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-configure-request": {
      "type": "object",
      "properties": {
        "configuration": {
          "type": "object",
          "properties": {
            "type_id": {
              "const": "concorde-operation-configuration"
            },
            "schema_version": {
              "type": "integer",
              "const": 2
            },
            "data": {
              "$ref": "#/$defs/concorde-operation-configuration"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        },
        "accept_protocol": {
          "type": "boolean"
        }
      },
      "required": [
        "configuration"
      ],
      "additionalProperties": false
    },
    "concorde-operation-configuration": {
      "type": "object",
      "properties": {
        "model": {
          "type": "string",
          "minLength": 1
        },
        "thinking": {
          "enum": [
            "off",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max"
          ]
        },
        "timeout_seconds": {
          "type": "integer"
        },
        "workers": {
          "type": "object",
          "properties": {},
          "additionalProperties": {
            "type": "object",
            "properties": {
              "model": {
                "type": "string",
                "minLength": 1
              },
              "thinking": {
                "enum": [
                  "off",
                  "minimal",
                  "low",
                  "medium",
                  "high",
                  "xhigh",
                  "max"
                ]
              },
              "timeout_seconds": {
                "type": "integer"
              }
            },
            "required": [],
            "additionalProperties": false
          }
        }
      },
      "required": [],
      "additionalProperties": false
    }
  }
}
```
