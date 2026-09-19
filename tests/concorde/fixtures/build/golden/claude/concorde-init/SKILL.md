---
name: concorde-init
description: "Operation: propose and apply explicit project initialization with a pinned Protocol and an honest registry stub."
argument-hint: "Optional operation guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-init.md"
  kind: "skill"
  operation: "init"
  entrypoint: "scripts/run-operation.py concorde-init"
user-invocable: true
disable-model-invocation: true
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
A mutating request from the primary worktree runs in a candidate worktree the host creates from
the committed base; this session stays where it is and receives that candidate's result, whose
workspace names the candidate's path, branch and change_id. Continue the same change from here
with that change_id. Uncommitted primary edits are not carried into the candidate. Report Spec gaps
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
