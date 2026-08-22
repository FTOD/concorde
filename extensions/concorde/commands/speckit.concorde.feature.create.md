---
description: Review placement and start one canonical nested feature through the normal Spec Kit lifecycle.
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
   canonical `spec.md`.
5. Register the approved architecture changes, validate them, then invoke
   `speckit.concorde.feature.select` for the created feature.

Never silently choose another module or create a flat feature copy.
