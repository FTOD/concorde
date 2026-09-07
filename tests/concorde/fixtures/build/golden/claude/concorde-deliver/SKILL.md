---
name: concorde-deliver
description: "Lifecycle: from the primary worktree, verify, merge and clean up one ready candidate change."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-deliver/SKILL.md"
  kind: "skill"
  capability: "deliver"
  entrypoint: "scripts/run-capability.py concorde-deliver"
user-invocable: true
disable-model-invocation: false
---
# concorde-deliver

Invoke delivery from an agent whose initial working directory is either the selected source
worktree or the destination (primary) Git worktree. The primary worktree is a location, not a
branch named main; its checked-out branch remains the merge destination. A third worktree or a
nested Operation cannot initiate delivery for this pair. Keep the session and its loaded Skills
bound to their original participant while the deterministic host operates on the integration.
Do not redirect a third-worktree session or forward its invocation to bypass the participant check.

Send one concorde-operation-invocation@2 JSON object on stdin to `python3 scripts/run-capability.py concorde-deliver`. Its exact fields
are type_id, schema_version:2, operation_id:"concorde-deliver", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1),
and input (concorde-deliver-request@1). Supply the selected change_id from the primary worktree's
`.concorde/worktrees.json` inventory. Optional target/task metadata cannot replace change ownership. Set keep_worktree:true to retain
the source; the source is always retained when it owns the requesting session.
No domain flags or positional arguments are accepted.

The deterministic host checks current completion evidence and the exact candidate tree, verifies
its actual integration with the primary branch, merges it, and cleans up the source unless retained by request or because it owns the session. Managed AGENTS.md/CLAUDE.md prompts and local work state do not enter
the delivered Git tree. A primary-local delivery receipt retains the verified commit and checks.
Conflicts, stale evidence or failed checks preserve the candidate. If merging succeeded but cleanup
failed, repeat this request from either participating session to finish cleanup without merging again.
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
        },
        "keep_worktree": {
          "type": "boolean"
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
