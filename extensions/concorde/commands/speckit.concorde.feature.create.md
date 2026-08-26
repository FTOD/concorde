---
description: Review placement and start one canonical top-level feature or immediate sub-feature through the normal Spec Kit lifecycle.
---

## User Input

```text
$ARGUMENTS
```

## Workflow

1. Invoke `.specify/extensions/concorde/scripts/bash/concorde.sh feature create` with exactly one
   placement mode: the reviewed module ID for a top-level feature, or `--parent-feature` for one
   immediate sub-feature; also pass the stable feature ID, short name, and permitted options.
2. Present the exact proposal, Protocol v3 workspace kind, source digest, module/parent registration,
   read-only parent context, view effects, and conflicts.
3. Do not write maintained intent until the user explicitly approves that exact proposal.
4. After approval, invoke the normal Spec Kit specify operation with
   `SPECIFY_FEATURE_DIRECTORY` set to `workspace.feature_directory`; Spec Kit authors that lifecycle
   root's only canonical `spec.md` and adjacent durable `design.md`. A sub-feature must declare
   `parent_feature`, inherit its module, own one focused `## Outcome`, and declare no children.
   Before any milestone has been hardened,
   the design must explicitly say that no implementation realization is hardened yet and must not
   invent implementation details.
5. Verify that both `workspace.feature_spec` and `workspace.feature_design` exist as real files.
   Register the approved architecture changes, validate them, then invoke
   `speckit.concorde.feature.select` for the created feature.

Never silently choose another module/parent, create a flat feature copy, allow a sub-feature to parent
another child, duplicate parent-owned facts, or create temporal plan/task files at a durable root.
