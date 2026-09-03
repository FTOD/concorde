---
name: concorde-fast-loop
description: "Complete one eligible small change directly across feature intent, architecture, code, and tests."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-fast-loop/SKILL.md"
  kind: "skill"
  exposure: "public"
---
## User Input

```text
$ARGUMENTS
```

# Concorde Fast Loop

Treat `$ARGUMENTS` as the complete requested change. Fast-loop is a direct, no-attempt path for one
small, fully understood change. It preserves the same
module/feature ontology and evidence standard as the full workflow.

## Workspace gate

Run `python3 scripts/workspace.py --phase fast-loop` first and require Protocol 13 for one existing selected feature. Use only the returned
`feature_path`, providing architecture, bounded summaries, executable context, and reflection path.
Reject fast-loop when an attempt already exists. Never create
`.concorde/attempts/<stable-feature-id>/` artifacts.

## Eligibility

Proceed only when all conditions hold:

- one selected feature and one providing module bound the change;
- affected architecture entities, interface semantics, source paths, and tests are already known;
- no new module, feature, entity type, cross-module relationship, or external compatibility policy
  is being invented;
- no migration, destructive action, release, multi-feature coordination, or broad setup change is
  required;
- the change can be implemented and proportionately verified in one focused pass; and
- the user request authorizes every affected durable/source path.

If any condition fails, stop before mutation and recommend specification/clarification followed by
plan, tasks, implementation, and delivery.

## Direct workflow

1. Read the selected feature file, relevant providing architecture sections, and current code/tests.
2. State the exact bounded delta and verification command before editing.
3. Make the smallest coherent change. Require the providing module's Archify `architecture` system
   overview before editing. Reconcile code and tests plus the selected feature file or
   module architecture only when observable behavior, embedded interface semantics, Architecture
   Zoom, or the entity graph actually changed. If the entity graph changes, update its principal
   entities and directed relationships in the overview; do not create alternate source documents or
   optional replacement diagrams.
4. Run focused tests and deterministic validation. If an architecture-owned diagram changed, update
   text/source together and require `meta.quality_profile: showcase`, hidden legend, normalized unique
   output, all nine Archify showcase checks with zero composition errors/warnings, generated freshness,
   and publication.
5. Re-read the diff and prove no out-of-scope path changed. On failure, leave a truthful report; do
   not claim completion or create an attempt retroactively.

Planning and task generation are the normal reflection-recording points. If the fast loop itself
encounters a distinct problem that must persist, use Reflection Document v2 with `phase: fast-loop`:
allocate the ID, create exactly the returned file, and fill only the factual problem sections. Leave
triage sections blank, omit `human_intervention`, retain `User Comments`, and do not propose a fix.
An existing problem receives an occurrence without allocating a new ID.

Report eligibility, changed paths, checks/results, limitations, architecture/interface impact, and
that no attempt was created.
