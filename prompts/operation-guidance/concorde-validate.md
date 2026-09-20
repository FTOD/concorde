---
name: concorde-validate
description: "Operation: run deterministic Spec and configured code checks and record readiness for the current candidate."
operation: validate
---

# concorde-validate

@prompts/workflow-host/invoke-operation-opener.md ACTION=validate
@prompts/workflow-host/lifecycle-no-cognition.md

@prompts/workflow-host/task-request-fields.md
@prompts/workflow-host/init-request-and-no-flags.md

@prompts/workflow-host/target-identity-opener.md
@prompts/workflow-host/candidate-worktree.md

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
