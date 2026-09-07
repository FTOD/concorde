---
name: concorde-review
description: "Internal stage: independent read-only Spec or code review of the bound target."
exposure: internal
operation: operation.py
capabilities: ["concorde-spec-reviewer", "concorde-code-reviewer"]
---

# concorde-review

This is an internal stage Operation. It receives an already routed `target_id` and one frozen
context snapshot from a composing Operation (`concorde-standard-dev-loop`, `concorde-fast-loop`, or
another internal stage acting on a Domain's recorded component work); it is never selected directly
by a user or by main. It is not projected as a user-invocable Skill, and the executable boundary
rejects a direct invocation of `operations/concorde-review/operation.py` with error code
`internal_operation`.

Invoke this Operation with review_mode=spec or code. The host routes the task, resolves the complete Target Spec and Shared Specs, and starts a fresh reviewer with no project write authority. Spec review cannot read implementation. Code review reads only the target's registered implementation files. Neither mode can modify source, Spec or tests. The host captures structured results and receipts separately.

A composing Operation invokes it in-process through `run_operation` with a
`concorde-review-request@1` TypedValue; the request requires target_id and task (review also
requires review_mode) and accepts optional focus_id, constraints and change_id, all supplied by the
caller. A change_id selects the current worktree's bound change, never another worktree's contents.
Configuration is never a context grant.

Use the executable boundary; do not perform the review in this ambient conversation or inspect project files to fill gaps. The full granted collection is reviewed against representative tasks. The host scopes changes to the selected target and binds results to the candidate's current bytes and its recorded committed base (HEAD for an unmanaged checkout). Cross-target work requires separately bound reviewers and only typed result aggregation.

Report no_findings, findings, incomplete, and host-only not_run/skipped distinctly. A blocking contract gap pauses dependent work and carries question, blocked_step and needed_contract. Nonblocking suggestions remain findings. Input changes invalidate the conclusion; no review proves universal semantic completeness. Public output contains findings, gaps, version identities and result ArtifactRefs, never raw code or logs. This Operation does not repair files or deliver changes.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-review-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-review-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-review-request": {
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
        "review_mode": {
          "enum": [
            "spec",
            "code"
          ]
        }
      },
      "required": [
        "task",
        "review_mode"
      ],
      "additionalProperties": false
    }
  }
}
```
