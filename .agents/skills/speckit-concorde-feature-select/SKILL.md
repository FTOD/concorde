---
name: speckit-concorde-feature-select
description: Select an existing nested Concorde feature for normal Spec Kit phases.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: concorde:commands/speckit.concorde.feature.select.md
---

## User Input

```text
$ARGUMENTS
```

## Workflow

Invoke `.specify/extensions/concorde/scripts/bash/concorde.sh feature select` with the stable feature
ID or canonical feature-root path. Pass `--resume` only after the user explicitly chooses to resume a
non-empty implementation attempt. Present all normative JSON findings and derived paths.

Selection writes only `.specify/feature.json`; it verifies the canonical `spec.md`/`design.md` pair
and never copies `spec.md`, `design.md`, `plan.md`, or `tasks.md`.