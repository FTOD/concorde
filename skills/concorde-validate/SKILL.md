---
name: concorde-validate
description: "Operation: run deterministic Spec and configured code checks and record readiness for the current candidate."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "prompts/skills/concorde-validate.md"
  kind: "skill"
  operation: "validate"
  entrypoint: ".concorde/framework/scripts/run-operation.py concorde-validate"
---
# concorde-validate

Invoke this operation to validate. The host owns context
resolution, agent execution, permissions, and lifecycle state. Supply the user's task as typed
input; do not perform it directly in this ambient conversation or inspect additional project files.
This is a deterministic lifecycle operation: it runs no agent cognition and selects no context.

Send one concorde-operation-invocation@3 JSON object on stdin to `python3 .concorde/framework/scripts/run-operation.py concorde-validate`. Its exact fields
are type_id, schema_version:3, operation_id:"concorde-validate", mode:"execute" or "describe-policy",
configuration (null to load initialized host settings, or a matching concorde-operation-configuration@1), and input (concorde-validate-request@1).
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

Validation checks document-unit identity and ownership, the paired reading/metadata sources,
Purpose/Usage/Design/Relationships reading structure, requirement and scenario syntax, local readable
meaning references, unique stable IDs and canonical identity links. Registry files equal the exact
union of entity metadata entries; file/directory kinds, pending markers, implementation exclusions,
provider sets and complementary interface bindings remain checked. A scoped Relationships diagram
uses declared local entities and labeled edges, without needing to reproduce the whole inventory.
Metadata-only edits affect complete-context identity and evidence just as reading edits do.

Tests declare verified scenario IDs in their own source. Unknown IDs and unreadable tests are errors;
uncovered scenarios and tests outside their scenario owner's listing are warnings. Missing unmarked
implementation entries are errors; stale pending markers and unlisted files are warnings. Warnings
do not by themselves fail validation. No structural result proves reading completeness, semantic
completeness or implementation conformance.

## Input TypedValue schema

This complete schema is the invocation's input field. It does not grant project reads.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "type_id": {
      "const": "concorde-validate-request"
    },
    "schema_version": {
      "type": "integer",
      "const": 1
    },
    "data": {
      "$ref": "#/$defs/concorde-validate-request"
    }
  },
  "required": [
    "type_id",
    "schema_version",
    "data"
  ],
  "additionalProperties": false,
  "$defs": {
    "concorde-validate-request": {
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
        "run_checks": {
          "type": "boolean"
        }
      },
      "required": [
        "target_id",
        "task"
      ],
      "additionalProperties": false
    }
  }
}
```
