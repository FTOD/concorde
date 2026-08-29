# Feature Abstract: Manage Feature Workspaces

`feature.concorde.workflow.manage-feature-workspaces` · sub-feature of `feature.concorde.workflow`,
specified at `module.concorde` · about four minutes. This page is enough to understand this
workflow step; the links at the end only redirect you when you want more.

## Purpose

Make sure every normal Spec Kit phase works on exactly one valid feature-shaped lifecycle root — a
top-level feature or an immediate sub-feature — and receives that root's authoritative durable,
temporal, ownership, parent, and sibling context. The root is chosen through the standard Spec Kit
pointer, not a Concorde command.

## Functionality

This step owns no command of its own. Its surface is the Feature Workspace Protocol: the
selected-workspace adapter's resolution and routing of the standard Spec Kit selection.

| Concern | How it works |
|---|---|
| Selection authority | The `.specify/feature.json` `feature_directory` record, written by `speckit.specify` or set through `SPECIFY_FEATURE_DIRECTORY`; no second selection store |
| Creating a root | `speckit.specify` with `SPECIFY_FEATURE_DIRECTORY` at the canonical path; the specify addendum seeds `abstract.md`, `design.md`, and a placeholder `implementation.md` and records the root in the pointer |
| Canonical placement | A top-level feature lives directly beneath its module's `features/`; a sub-feature inherits its parent's module and lives directly beneath that parent's `subfeatures/`; two containment levels only |
| Workspace result | Selected kind, ID, module, durable paths naming `abstract.md`, `design.md`, and `implementation.md`, temporal paths, `attempt_state`, nullable parent context with the same trio names, and bounded siblings |
| Invalid roots | Unsafe, symlinked, unregistered, misplaced, or third-level paths; missing trio files; legacy `tldr.md`/`spec.md` or `implementation/`; aliases or symlinks |

A non-empty `attempt/` attempt is reported as `attempt_state: active` and is never
replaced, archived, or removed by resolution. Invalid roots produce actionable findings and change
neither maintained sources nor selection state; the same rules are enforced deterministically by
`speckit.concorde.validate`.

**Not part of this step**: the behavior of the phases that consume the resolved paths (the specify,
plan, and execute steps), the full validation rule set (the validate step), and any Concorde
creation or selection command.

## Structure

This step uses the parent's core view, <a href="/architecture/concorde-workflow-components.html">workflow components</a>;
it declares no diagram of its own. The selected-workspace adapter turns the control-state pointer
into the exact paths of one root for every phase surface.

```text
speckit.specify (SPECIFY_FEATURE_DIRECTORY) ──writes──▶ .specify/feature.json ◀──reads── every phase surface
                                                                │
                                                     selected-workspace adapter (Feature Workspace Protocol)
                                                                │
          ┌─────────────────────────────────────────────────────┴───────────────────────────────┐
          selected root: abstract.md · design.md · implementation.md · attempt/ (state: active or absent)
          parent context (sub-feature only): parent's trio, read-only     siblings: bounded summaries
```

The architecture sources supply the registration the root must match: its module's feature list or
its parent's `subfeatures` list, matching the `design.md` front matter.

## Logic

1. A phase starts and reads the selection pointer.
2. The adapter checks that the path is safe, not symlinked, inside the specification package, at a
   legal depth, and registered by its module or parent, with agreeing front matter.
3. It checks that the durable trio is present and no legacy name remains.
4. It returns the workspace result — kind, ID, module, paths, attempt state, parent context,
   siblings — or actionable findings with nothing changed.
5. The phase proceeds confined to those paths; parent and sibling attempts are never implicit
   inputs.

**Rules the implementation must keep**

- The standard `.specify/feature.json` record is the only selection authority; no Concorde creation
  or selection command and no second store exists (FR-001).
- A sub-feature inherits its parent's module and lives directly beneath `subfeatures/`; a top-level
  feature lives directly beneath its module's `features/` (FR-002).
- A valid root holds one canonical `design.md` with adjacent `abstract.md` and `implementation.md` and is
  registered by its module or parent; a new root has that trio seeded (FR-003).
- Resolution accepts exactly one valid root and rejects unsafe, symlinked, unregistered, misplaced,
  or third-level paths without changing selection state (FR-004).
- The protocol returns kind, ID, module, durable trio paths, temporal paths, attempt state,
  nullable parent context, and bounded siblings (FR-005).
- Every phase stays confined to the selected root; parent and sibling attempts are never implicit
  inputs (FR-006).
- A non-empty attempt is reported as active and is never replaced, archived, or removed by
  resolution (FR-007).
- Registration, canonical path, two-level containment, and identity rules are enforced by
  `speckit.concorde.validate`, and invalid roots preserve prior sources and selection (FR-008).
- Legacy `tldr.md`/`spec.md` files or an `implementation/` directory are rejected with migration
  guidance; missing `abstract.md` receives authoring remediation, and aliases or symlinks are invalid
  (FR-009).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): FR-001 to FR-009 and
  SC-001 to SC-004.
- **How the accepted implementation realizes this step** — [implementation.md](implementation.md) (states that no
  realization has been hardened yet).
- **The parent feature** — its [abstract](../../abstract.md) and [design.md](../../design.md).
- **Contracts** — `../../contracts/feature-workspace.schema.json`
  (the protocol result), `../../contracts/agent-commands.md`, and
  `../../contracts/architecture-sources.md`.
- **The level** — [module.md](../../../../module.md).
- **Previous and next steps** — [answer workflow questions](../003-answer-workflow-questions/design.md)
  and [specify behavior](../005-specify-behavior/design.md).
