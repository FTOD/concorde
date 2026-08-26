---
description: "Retrieve exactly one bounded architectural level"
---

# Retrieve Concorde Context

Require one stable module or feature ID in `$ARGUMENTS`, then run:

- POSIX: `.specify/extensions/concorde/scripts/bash/concorde.sh context $ARGUMENTS --format json`
- PowerShell: `.specify/extensions/concorde/scripts/powershell/concorde.ps1 context $ARGUMENTS --format json`

Present the returned current module, its current-level features and I/O, all immediate children and
their concise I/O, externals, scenarios, adjacent refinements, and deeper navigation references.
Never expand child feature bodies or grandchildren. This operation is read-only; show all findings
and preserve the runtime status and exit behavior.
