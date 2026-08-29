---
description: "Retrieve exactly one bounded architectural level"
---

# Retrieve Concorde Context

Require one stable module or feature ID in `$ARGUMENTS`, then run:

- POSIX: `.specify/extensions/concorde/scripts/bash/concorde.sh context $ARGUMENTS --format json`
- PowerShell: `.specify/extensions/concorde/scripts/powershell/concorde.ps1 context $ARGUMENTS --format json`

Present the returned current module, its current-level features and I/O, all immediate children and
their concise I/O, externals, scenarios, adjacent refinements, feature-containment summaries, and
deeper navigation references. The module context result also returns the module's `summary`
(`module.md` path), `design_reference` (`design.md` path), and `diagrams` (the paths of the module's
diagrams under `architecture/diagrams/`) as navigation references,
and each feature summary names its `abstract.md` and `design.md` paths the same way. Present them as
paths to open deliberately; never expand the body of an `abstract.md`, feature `design.md`, or feature `implementation.md`.
When the project reflection log exists, the result carries `reflections` (its path and the open
entry count per feature) and each feature summary and workspace carries `reflections_open`; present
the path and the counts, and open the log only when the maintainer asks about recorded problems.
A parent feature lists immediate sub-feature summaries in authored
order; a sub-feature lists its parent and concise siblings. Never expand another feature body,
parent/sibling attempt, third feature level, lower-module feature body, or grandchild module. This
operation is read-only; show all findings and preserve the runtime status and exit behavior.
