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

## Isolated worktree gate

After applying any Protocol-evolution guard, read-only inspection may remain in the primary
worktree. Before planning, selection persistence, attempt/checklist/reflection creation, an external
mutation, or any other write, unless the maintainer explicitly authorizes primary-worktree mutation
for this request, resolve only the primary worktree's committed `HEAD`, create a unique branch and
linked worktree at that exact commit, and continue the complete request there. If already in an
isolated worktree, stay there and do not create a nested worktree. Treat every staged, unstaged,
untracked, or ignored primary-worktree path as another programmer's state: never use it as input,
stash it, copy it, commit it, reset it, clean it, or otherwise import or alter it. If required input
is absent from committed `HEAD`, stop and report the missing input. `--allow-primary-worktree` is
valid only after an explicit instruction to modify the primary worktree; a generic task request is
not that authorization. A non-Git checkout likewise requires explicit current-directory mutation
authorization.

Treat `$ARGUMENTS` as the complete requested change. Fast-loop is a direct, no-attempt path for one
small, fully understood change. It preserves the same
module/feature ontology and evidence standard as the full workflow.

## Concorde Protocol evolution guard

Before workspace resolution or preflight, if this is the Concorde repository and the request changes
normative Concorde Protocol semantics, stop without selection or mutation. Apparent size and backward
compatibility do not make the change fast-loop eligible. Report the separate direct isolated-
worktree route `feature.concorde.evolve-protocol`. A fix that restores already specified Protocol
behavior may continue through normal fast-loop eligibility.

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
Immediately after creating the document or appending an occurrence, run
`scripts/reflections_queue.py --validate-entry <id>`; correct only that new entry until it reports
`valid`. Findings on other entries are reported separately as unrelated and are not this phase's to
fix; a reserved ID stays retired even if the entry is abandoned.

Report eligibility, changed paths, checks/results, limitations, architecture/interface impact, and
that no attempt was created.
