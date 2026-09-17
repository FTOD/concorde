---
name: concorde-configure
description: "Operation: apply the Pi worker model selection (model, thinking level, timeout and per-worker overrides); with accept_protocol, rebind the project to the installed Protocol copy."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-configure/SKILL.md"
  kind: "skill"
  operation: "configure"
  entrypoint: "scripts/run-operation.py concorde-configure"
---
# concorde-configure

Invoke this operation to configure. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.
This is a deterministic lifecycle operation: it runs no agent cognition and selects no context.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 scripts/run-operation.py concorde-configure`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-configure", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-configure-request@1).
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
              "const": 1
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
