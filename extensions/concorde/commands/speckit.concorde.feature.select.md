---
description: Select an existing top-level Concorde feature or immediate sub-feature for normal Spec Kit phases.
---

## User Input

```text
$ARGUMENTS
```

## Workflow

Invoke `.specify/extensions/concorde/scripts/bash/concorde.sh feature select` with the stable feature
or sub-feature ID or canonical lifecycle-root path. Pass `--resume` only after the user explicitly chooses to resume a
non-empty implementation attempt. Present all normative JSON findings and derived paths.

Selection writes only `.specify/feature.json`; it verifies the canonical `spec.md`/`design.md` pair,
module/parent registration, and Protocol v3 relationship fields. For a selected sub-feature, parent
durable paths are read-only aggregate context and siblings are concise summaries only. Selection
never copies lifecycle artifacts or reads/writes parent/sibling attempts implicitly.
