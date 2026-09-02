---
name: concorde-deliver
description: "Validate and remove one completed temporal feature attempt"
scripts:
  py: scripts/concorde.py deliver
---

## User Input

```text
$ARGUMENTS
```

# Deliver a Concorde Attempt

Delivery is cleanup-only. By this point explicit implementation tasks have already reconciled the
feature file, providing module architecture, code, tests, interface fixtures, and projections.
Delivery writes no durable specification or implementation narrative; it proves eligibility and
atomically removes exactly the selected `.concorde/attempts/<stable-feature-id>/`.

## Propose

1. From the target project root invoke `{SCRIPT} $ARGUMENTS --propose`.

2. Require a Protocol 13 workspace and Delivery Proposal 9 result. Stop on any status other than
   `eligible`; report every finding and leave the attempt byte-identical. Never check off, rewrite,
   delete, or reinterpret task/checklist/evidence state to make it eligible.
3. Verify the proposal binds the stable feature target, current source/attempt digest, exact safe
   attempt removal path, task/checklist/evidence summaries, project validation result, and retained
   authority digests. `remove` must contain exactly the returned `workspace.attempt_dir`.
4. Read only enough returned material to confirm that all tasks/checklists have passed evidence,
   every architecture/feature/code/test/projection reconciliation is already present, paths are real
   project-relative non-symlinks, and the reflection log remains centralized. Do not draft content.

## Apply

The user's delivery invocation authorizes proposal and apply in one Tool run; do not ask for a
second approval. Immediately invoke the same launcher with
`{SCRIPT} --apply --proposal <returned-project-relative-proposal-path>`.

Apply must revalidate the digest, completeness, project validation, safe target, and exact removal
manifest. It atomically removes only the selected attempt. Any stale digest, incomplete evidence,
unsafe/symlinked path, validation failure, or removal failure preserves the complete attempt and all
durable/executable sources.

## Invariants and report

Delivery never changes module architecture, the direct feature file, code, tests, generated projections,
control selection, related features, ancestor modules, or the project reflection log. It never
archives temporal work elsewhere in project control state, the module, or beside the feature source.

Report the feature ID, Proposal 9 path/digest, task/checklist/evidence summaries, validation result,
removed artifact manifest/count, retained architecture/feature/code/test/reflection digests, findings,
and whether the feature now has no active attempt.
