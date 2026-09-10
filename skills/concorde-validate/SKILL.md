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
Requirements, Scenarios, Ontology, the last with its Entities and Relationships subsections -- the
syntax of its requirement sections (one SHALL statement each), scenario sections (steps only) and
`concorde-entities` declarations, unique stable IDs, that a local link whose fragment is a
scenario, requirement or entity ID points at the document defining it, and that the registry's
`files` for a Module equal the sorted union of its entities' `files`, entry for entry. A listing
entry is an exact file or a directory prefix ending in `/` that binds every regular file below it,
so the registry repeats the prefix rather than its expanded names. It also checks that the
Relationships flowchart's node labels are exactly the declared entity titles and that every edge
carries a label. It reads the `verifies` declarations of the listed Python tests without running
them: a declaration naming an unknown scenario or an unreadable Python file is an error, while a
scenario that no test declares and a declaration in a file the scenario's Module does not list are
warnings. An entry an entity lists whose file or directory does not exist and is not marked
`pending` is an error; an entry still marked `pending` after it exists on disk is a warning, and so
is a regular file that no Module's entries cover. Warnings are reported alongside errors but never
by themselves turn a successful validation into a failure; only errors do.
