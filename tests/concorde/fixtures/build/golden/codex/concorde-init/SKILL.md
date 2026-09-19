---
name: concorde-init
description: "Operation: propose and apply explicit project initialization with a pinned Protocol and an honest registry stub."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-init.md"
  kind: "skill"
  operation: "init"
  entrypoint: "scripts/run-operation.py concorde-init"
---
# concorde-init

Invoke this operation to init. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.
This is a deterministic lifecycle operation: it runs no agent cognition and selects no context.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 scripts/run-operation.py concorde-init`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-init", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-init-request@1).
Task requests select target_id and task, with optional focus_id (a scenario ID), constraints, and
change_id.
Initialization uses its typed propose/apply request; use the published request schema.
No domain flags or positional task arguments are accepted. Configuration is never a context grant.

Use the supplied target identity; if it is ambiguous, ask the user to identify it instead of
searching other Specs.
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

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-init-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 2
    },
    "data": {
      "$ref": "#/$defs/concorde-init-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-init-request": {
      "type": "object",
      "properties": {
        "action": {
          "enum": [
            "propose",
            "apply"
          ]
        },
        "name": {
          "type": "string",
          "minLength": 1
        },
        "target_id": {
          "type": "string",
          "minLength": 1
        },
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
        "proposal": {
          "type": "object",
          "properties": {
            "type_id": {
              "const": "concorde-project-proposal"
            },
            "schema_version": {
              "type": "integer",
              "const": 1
            },
            "data": {
              "$ref": "#/$defs/concorde-project-proposal"
            }
          },
          "required": [
            "type_id",
            "schema_version",
            "data"
          ],
          "additionalProperties": false
        }
      },
      "required": [
        "action"
      ],
      "additionalProperties": false
    },
    "concorde-project-proposal": {
      "type": "object",
      "properties": {
        "action": {
          "enum": [
            "initialize"
          ]
        },
        "base_digest": {
          "anyOf": [
            {
              "type": "string",
              "minLength": 1,
              "pattern": "^sha256:[0-9a-f]{64}$"
            },
            {
              "type": "null"
            }
          ]
        },
        "files": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "path": {
                "type": "string",
                "minLength": 1
              },
              "before_digest": {
                "anyOf": [
                  {
                    "type": "string",
                    "minLength": 1,
                    "pattern": "^sha256:[0-9a-f]{64}$"
                  },
                  {
                    "type": "null"
                  }
                ]
              },
              "content": {
                "type": "string"
              }
            },
            "required": [
              "path",
              "before_digest",
              "content"
            ],
            "additionalProperties": false
          }
        }
      },
      "required": [
        "action",
        "base_digest",
        "files"
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
