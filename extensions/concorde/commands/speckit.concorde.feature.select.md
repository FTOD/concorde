---
description: Select an existing nested Concorde feature for normal Spec Kit phases.
---

## User Input

```text
$ARGUMENTS
```

## Workflow

Invoke `.specify/extensions/concorde/scripts/bash/concorde.sh feature select` with the stable feature
ID or canonical feature-root path. Pass `--resume` only after the user explicitly chooses to resume a
non-empty implementation attempt. Present all normative JSON findings and derived paths.

Selection writes only `.specify/feature.json`; it never copies `spec.md`, `plan.md`, or `tasks.md`.
