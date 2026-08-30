# Reflection Triage Contract

## Purpose

Define the portable, installed contract by which a maintainer turns Reflection Log v1 entries into
evidence-backed plans, bounded implementation commits, and safely merged improvements through
specialized coding-agent subagents.

## Entry Point

Every supported subagent integration exposes one `reflections-triage` skill with exactly four
actions:

| Action | Mutation authority | Result |
|---|---|---|
| `status` | none | ordered open-entry queue and plan-state counts |
| `investigate [N | IDs...]` | parent may write validated plan files only | one route/plan or actionable failure per requested entry |
| `implement` | child writes only in assigned worktree; parent updates plan evidence | per-plan commit/ineligible/failed results grouped by owning feature |
| `merge` | parent merges validated branches and cleans their owned worktrees | merged commits, suggested reflection notes, retained failures |

An empty invocation is `status`. Unknown actions or malformed identifiers fail without mutation.

## Shared State

- Configuration: `.concorde/reflections/config.json`, seeded once and then maintainer-owned.
- Plans: `.concorde/reflections/plans/R-NNN.md`, written only by the orchestrator.
- Worktrees: `.concorde/reflections/worktrees/<group>/`, ephemeral and never a source of intent.
- Reflection log: derived from the specification root in `.concorde/config.json`; never duplicated.
- Projection receipt: `.specify/concorde-agent-assets.json`, installer-owned.

Plans and worktrees are ignored by version control by default; configuration is version controlled.
Claude and Codex projections consume the same paths and lifecycle.

## Investigator Obligation

One investigator receives exactly one reflection entry and bounded repository context. It is
read-only, establishes root cause and the authority that owns the improvement, and returns the full
Reflection Plan described by Feature 005 FR-020. It chooses exactly one route:

- `fast-loop`: eligible bounded change under one selected feature;
- `specify`: behavior, architecture, contract, guidance-template, or cross-feature intent must be
  revised through specification;
- `dismiss`: evidence shows no project change is warranted;
- `blocked`: one exact maintainer decision is required.

The investigator never edits the log, plan directory, selected feature, or source files. The parent
validates identity, route, required sections, paths, and uniqueness before persisting the plan.

## Implementer Obligation

One implementer receives an absolute worktree path, one owning feature directory/ID, and the full
ordered text of every ready plan in the group. Before writing it verifies that its Git top-level is
the assigned worktree. For each plan it selects the feature, invokes Speckit Fast Loop, validates the
plan, and creates exactly one commit on success. A bounded failure reverts only that plan's changes
and continues when plan independence permits. Its final result names branch, worktree, head, per-plan
status/commit/files, and any reflection the parent should append.

## Orchestration and Concurrency

- Investigator waves and implementer groups never exceed shared configuration.
- One entry belongs to one investigator; one owning-feature group belongs to one implementer.
- The orchestrator waits for every child in a wave before advancing.
- Missing investigator output is retried once; all other failures are reported without discarding
  successful siblings.
- Ready plans are `fast-loop` plans in `proposed` or `approved`, restricted to `approved` when
  `require_approval` is true.
- Overlapping maintainer changes skip the entire owning-feature group.

## Merge and Maintainer Authority

Merge requires a clean tracked checkout. Branches merge one at a time. A conflict is aborted and
stops the operation. Applicable repository and documentation validation reruns after merge. Only a
successfully merged worktree/branch is removed and only its plan moves to `merged`.

The workflow never edits Reflection Log `Status` or `Note`. It reports the entries that may now be
resolved and suggests notes citing the merged commits. `specify`, `dismiss`, and `blocked` plans are
maintainer decisions and never auto-implemented.

## Projection Contract

Canonical bodies and defaults ship inside `.specify/extensions/concorde/agent-assets/reflections/`.
The deterministic projection operation supports `preview`, `sync`, `verify`, and `remove` for:

| Integration | Skill | Investigator | Implementer |
|---|---|---|---|
| Claude | `.claude/skills/reflections-triage/SKILL.md` | `.claude/agents/reflection-investigator.md` | `.claude/agents/reflection-implementer.md` |
| Codex | `.agents/skills/reflections-triage/SKILL.md` | `.codex/agents/reflection_investigator.toml` | `.codex/agents/reflection_implementer.toml` |

Claude may declare native background/worktree metadata. Codex TOML defines `name`, `description`,
and `developer_instructions`, uses read-only investigator and workspace-write implementer defaults,
and relies on the orchestrator's explicit Git worktree. Neither projection pins a mandatory model or
modifies user permission settings.

## Ownership and Failure Semantics

The projection receipt records every generated output digest. Sync may replace/remove an owned path
only when its current digest matches the prior receipt. A missing, modified, unowned, or legacy file
is previewed as create/adopt/conflict/preserve; conflict stops before that path is changed. Default
config is create-if-absent and never receipt-owned. Plans, worktrees, the log, unrelated agent files,
and user permission configuration are always preserved.

Every operation returns structured status, integration, planned/applied path actions, conflicts,
receipt digest, and remediation. A partial failure never claims success and reports residual bundle
and projection state.

## Compatibility

This is Reflection Triage Contract v1. Adding an integration or optional plan field is additive.
Changing action names, route/status vocabularies, shared state paths, ownership rules, or role write
boundaries requires a contract revision and migration guidance.
