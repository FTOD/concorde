---
name: concorde-deliver
description: "Validate and remove one completed temporal feature attempt"
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-deliver/SKILL.md"
  kind: "skill"
  exposure: "public"
user-invocable: true
disable-model-invocation: false
---
## User Input

```text
$ARGUMENTS
```

# Deliver a Concorde Attempt

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

Delivery is cleanup-only. By this point explicit implementation tasks have already reconciled the
feature file, providing module architecture, code, tests, interface fixtures, and projections.
Delivery writes no durable specification or implementation narrative; it proves eligibility and
atomically removes exactly the selected `.concorde/attempts/<stable-feature-id>/`.

## Concorde Protocol evolution guard

Before proposing delivery, if this is the Concorde repository and the selected work changes normative
Concorde Protocol semantics, stop without reading, rewriting, or removing the attempt. Such an
attempt is ineligible by Constitution 8.1.0; report `feature.concorde.evolve-protocol` and preserve
all state for explicit maintainer disposition.

## Propose

1. From the target project root invoke `python3 scripts/concorde.py deliver $ARGUMENTS --propose`.

2. Require a Protocol 13 workspace and Delivery Proposal 9 result. Stop on any status other than
   `eligible`; report every finding and leave the attempt byte-identical. Never check off, rewrite,
   delete, or reinterpret task/checklist/evidence state to make it eligible.
3. Verify the proposal binds the stable feature target, current source/attempt digest, exact safe
   attempt removal path, task/checklist/evidence summaries, project validation result, and retained
   authority digests. `remove` must contain exactly the returned `workspace.attempt_dir`.
4. Read only enough returned material to confirm that all tasks/checklists have passed evidence,
   every architecture/feature/code/test/projection reconciliation is already present, paths are real
   project-relative non-symlinks, and each reflection remains in its canonical per-file collection. Do not draft content.

## Attempt Evidence grammar

The canonical compact block in `validation.md` is:

```markdown
- **T### · <trace>**
  - **Outcome**: passed|failed|skipped
  - **Check**: <actual command or check>
  - **Evidence**: <project-relative path or concise output>
  - **Scope**: <behavior or boundary proved>
  - **Limitation**: <material limit or none>
```

The `- **T### · <trace>**` boundary must be one complete top-level line with no trailing prose; the
legacy `### T### ...` boundary remains readable. Only an exact in-block `- **Outcome**: passed`
counts. A wrapped/nested boundary, “passed” in the title or prose, or `failed`/`skipped` outcome is
missing passing evidence and blocks delivery. Delivery reports this state but never rewrites it.

## Apply

The user's delivery invocation authorizes proposal and apply in one Tool run; do not ask for a
second approval. Immediately invoke the same launcher with
`python3 scripts/concorde.py deliver --apply --proposal <returned-project-relative-proposal-path>`.

Apply must revalidate the digest, completeness, project validation, safe target, and exact removal
manifest. It atomically removes only the selected attempt. Any stale digest, incomplete evidence,
unsafe/symlinked path, validation failure, or removal failure preserves the complete attempt and all
durable/executable sources.

## Invariants and report

Delivery never changes module architecture, the direct feature file, code, tests, generated projections,
control selection, related features, ancestor modules, or the project reflection collection. It never
archives temporal work elsewhere in project control state, the module, or beside the feature source.

Report the feature ID, Proposal 9 path/digest, task/checklist/evidence summaries, validation result,
removed artifact manifest/count, retained architecture/feature/code/test/reflection digests, findings,
and whether the feature now has no active attempt.
