---
name: speckit-concorde-feature-create
description: Review placement and start one canonical nested feature through the normal Spec Kit lifecycle.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: concorde:commands/speckit.concorde.feature.create.md
---

## User Input

```text
$ARGUMENTS
```

## Workflow

1. Invoke `.specify/extensions/concorde/scripts/bash/concorde.sh feature create` with the reviewed
   module ID, stable feature ID, short name, and optional participant-module IDs.
2. Present the exact proposal, source digest, module registration, view effects, and conflicts.
3. Do not write maintained intent until the user explicitly approves that exact proposal.
4. After approval, invoke the normal Spec Kit specify operation with
   `SPECIFY_FEATURE_DIRECTORY` set to `workspace.feature_directory`; Spec Kit authors the only
   canonical `spec.md` and the adjacent durable `design.md`. Before any milestone has been hardened,
   the design must explicitly say that no implementation realization is hardened yet and must not
   invent implementation details.
5. Verify that both `workspace.feature_spec` and `workspace.feature_design` exist as real files.
   Register the approved architecture changes, validate them, then invoke
   `speckit.concorde.feature.select` for the created feature.

Never silently choose another module, create a flat feature copy, or create temporal plan/task files
at the durable feature root.