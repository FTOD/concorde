---
name: concorde-context
description: "Retrieve exactly one bounded module or feature context"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-context/SKILL.md"
  kind: "skill"
---
# Retrieve Concorde Context

Require one stable module or feature ID in `$ARGUMENTS`, then run
`python3 scripts/concorde.py context $ARGUMENTS --format json`.

For a module, present its `architecture.md`, responsibility/boundary, typed current-level entities,
directed relationships, representative interactions, immediate child-module summaries, level-local
feature summaries, external locators, and architecture diagram paths. Never expand a child module's
internal inventory or a feature body merely because it is discoverable.

For a feature, present its canonical `feature_path`, providing module architecture, visible module
ancestry, related-feature summaries, embedded provided/required interface summaries, Architecture
Zoom references, attempt state/paths, executable context hints, and deeper navigation references.
Never expand a related feature body or any other attempt without an explicit follow-up selection.

When present, return the project-control reflection-log path and open counts, but open the log only when the
maintainer asks about recorded problems. Generated projections may be listed with provenance and
freshness but are never stronger than their architecture or feature source.

This Skill is strictly read-only. Preserve canonical status, findings, source digest, and exit
behavior.
