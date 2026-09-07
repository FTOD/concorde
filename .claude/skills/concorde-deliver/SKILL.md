---
name: concorde-deliver
description: "Merge and clean up a verified change from an agent opened in the primary worktree."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-deliver/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-deliver/operation.py"
user-invocable: true
disable-model-invocation: false
---
# concorde-deliver

Invoke delivery only from an agent whose initial working directory is the primary Git worktree.
The primary worktree is a location, not a branch named main. Its currently checked-out branch is
where the verified candidate will be merged.

If this agent was opened in a secondary worktree, stop and tell the user to open a new agent in
the primary worktree and request delivery there. Do not invoke this Operation from the secondary
session, change cwd, use git -C, redirect a host or delegate/forward delivery to bypass that rule.
The host independently rejects a secondary or internally forwarded delivery invocation.

Send one concorde-operation-invocation@2 JSON object on stdin to `python3 scripts/run-operation.py operations/concorde-deliver/operation.py`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-deliver", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1),
and input (concorde-deliver-request@1). Supply the selected change_id from the primary worktree's
`.concorde/worktrees.json` inventory. Optional target/task metadata cannot replace change ownership.
No domain flags or positional arguments are accepted.

The deterministic host checks current completion evidence and the exact candidate tree, verifies
its actual integration with the primary branch, merges it, and removes the temporary worktree and
its `.concorde/worktree.json`. Managed AGENTS.md/CLAUDE.md prompts and local work state do not enter
the delivered Git tree. A primary-local delivery receipt retains the verified commit and checks.
Conflicts, stale evidence or failed checks preserve the candidate. If merging succeeded but cleanup
failed, repeat this request in the primary session to finish cleanup without merging again.
Report returned status and gaps faithfully; do not perform Git delivery manually around the host.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-deliver-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-deliver-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-deliver-request": {
      "type": "object",
      "properties": {
        "change_id": {
          "type": "string",
          "minLength": 1
        },
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
        }
      },
      "required": [
        "change_id"
      ],
      "additionalProperties": false
    }
  }
}
```
