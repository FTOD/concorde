---
description: "Deterministically validate Concorde architecture sources"
---

# Validate Concorde

Run the installed project-relative launcher with optional target `$ARGUMENTS`:

- POSIX: `.specify/extensions/concorde/scripts/bash/concorde.sh validate $ARGUMENTS --format json`
- PowerShell: `.specify/extensions/concorde/scripts/powershell/concorde.ps1 validate $ARGUMENTS --format json`

Present the canonical status, complete sorted findings, source digest, and summary. Do not hide errors,
modify maintained sources, or reinterpret `unknown` evidence as agreement. Preserve exit codes:
success 0, invalid 1, conflict 2, and failed 3.

Validate feature containment independently from adjacent-module refinement: canonical two-level
paths, unique IDs, bidirectional parent registration, module inheritance, child absence from the
module top-level registry, no cycles, no third level, safe selection, and isolated durable/temporal
roots must all produce actionable containment or layout findings.
