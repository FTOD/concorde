---
name: concorde-validate
description: "Lifecycle: run deterministic Spec and configured code checks and record readiness for the current candidate."
capability: validate
---

# concorde-validate

@include prompts/workflow-host/invoke-capability-opener.md ACTION=validate
@include prompts/workflow-host/lifecycle-no-cognition.md

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-validate
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-validate
@include prompts/workflow-host/task-request-fields.md
@include prompts/workflow-host/init-request-and-no-flags.md

@include prompts/workflow-host/target-identity-opener.md
@include prompts/workflow-host/worktree-handoff.md

Validation checks every Module's `module.md` for its four mandatory sections in order -- Purpose,
Scenarios, Entities, Architecture -- the syntax of its scenario, requirement and `concorde-entities`
declarations, unique stable IDs, and that the registry's `files` for a Module equal the sorted
union of its entities' `files`. It also checks that the Architecture flowchart's node labels are
exactly the declared entity titles and that every edge carries a label. A file an entity lists that
does not exist and is not marked `pending` is an error; a file still marked `pending` after it
exists on disk is a warning. Warnings are reported alongside errors but never by themselves turn a
successful validation into a failure; only errors do.
