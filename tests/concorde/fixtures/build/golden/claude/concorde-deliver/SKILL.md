---
name: concorde-deliver
description: "Lifecycle: stage a verified change, remove its worktree, and explicitly merge from the primary session."
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
worktree or the primary Git worktree. A third-worktree or nested invocation cannot deliver this
change. Keep the session and its loaded Skills bound to their original participant.

Send one concorde-capability-invocation@3 JSON object on stdin to `python3 scripts/run-capability.py concorde-deliver`. Its exact fields
are type_id, schema_version:3, capability_id:"concorde-deliver", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-capability-configuration@1),
and input (concorde-deliver-request@1). Supply the selected change_id from the primary worktree's
`.concorde/worktrees.json` inventory or its saved delivery receipt. Optional target/task metadata
cannot replace change ownership. No domain flags or positional arguments are accepted.

Default delivery verifies the candidate and its integration with the current primary commit,
confirms every entity entry marked `pending`, an exact file or a directory prefix, that now exists on
disk and clears its marker as part of the delivered commit (an entry still missing stays pending and
is reported), creates
`concorde/delivered/<change_id>` without checking it out, and removes the source worktree
and its local state. Each change has an independent delivery branch. The primary worktree's
checked-out branch, index and project files are unchanged. `keep_worktree:true` explicitly retains
the source; ownership of the requesting session does not retain it automatically. After removal,
end the source session without further project work. Further work requires a fresh P10 session.
Managed AGENTS.md/CLAUDE.md blocks and local control state never enter the delivered tree.

Only when the user explicitly requests the final primary-branch merge, invoke a separate request
with `merge_primary:true` and the delivered change_id from the primary worktree's owning session.
A generic delivery request does not authorize this flag. At most one agent may own writes in the
primary worktree; other agents work in their own linked worktrees. The host holds the shared
repository lock for delivery state changes and the entire primary merge, rechecks the current
integration and rejects conflicts or failed checks before changing the primary branch. Preserve
local edits; a dirty primary blocks final merging but does not block default branch delivery.
Do not start another primary writer or perform manual Git delivery around the host.

Receipts retain delivery and primary merge evidence separately, including which files were
confirmed and which remain pending. Retry failed cleanup without
another branch merge. Retry an already completed primary merge without merging twice. After source
removal, retry from the primary session using the receipt's change_id. Conflicts or failed checks
preserve the candidate or delivered branch for repair in a new change worktree. Report the returned
branch, outcome, cleanup status and whether final primary merging remains pending faithfully.

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
        },
        "merge_primary": {
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
