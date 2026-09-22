---
name: concorde-validate
description: "Host service: run deterministic Spec and configured code checks and record readiness for the current candidate."
operation: validate
---

# concorde-validate

@prompts/workflow-host/invoke-operation-opener.md ACTION=validate
@prompts/workflow-host/lifecycle-no-cognition.md

@prompts/workflow-host/task-request-fields.md
@prompts/workflow-host/init-request-and-no-flags.md

@prompts/workflow-host/target-identity-opener.md
@prompts/workflow-host/candidate-worktree.md

Structural findings carry their Protocol check identity (`CHK.*`) and severity. Validation
checks document pairing, identity and ownership, schema-3 metadata, the entry's Purpose,
Terminology, Usage, Design and Relationships structure, Terminology rows (one defining sentence per
concept; link-only import rows), requirement, scenario and contract syntax, local `meaning` anchors,
unique stable IDs and identity links. The registry must mirror every entry's `module` block exactly
(`registry --write` regenerates it). Composition, `uses` with `relies_on`, `includes`,
`participates` versions and peers, realization entries and pending markers, unbound files and the
context reconciliation are checked. An unmarked flowchart in a `module` document may only draw
declared `relates`, `uses` and `contains` relations; other diagrams are marked `mermaid
illustrative`. Metadata-only edits affect complete-context identity and evidence just as reading
edits do.

Tests declare verified scenario IDs in their own source. Unknown IDs and unreadable tests are errors;
uncovered scenarios and tests that the scenario's owner does not bind are warnings. Warnings do not
by themselves fail validation. No structural result proves reading completeness, semantic
completeness or implementation conformance.
