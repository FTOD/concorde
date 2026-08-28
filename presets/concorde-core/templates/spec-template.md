
## Concorde Architecture Alignment

Record this feature in its single canonical `spec.md` inside the providing module's
`features/<number-name>/` workspace.

Keep the adjacent durable `tldr.md` (the self-contained TL;DR this phase authors together with the
specification: Purpose, Functionality, Structure, Logic, Read Next; under 15 minutes) and `design.md`
(the feature design reference). Specification work may read `design.md` to avoid confusing accepted
realization with required behavior, but must never update it. New features start with the resolved
design template's explicit placeholder: no implementation realization has been hardened yet. Never
create a feature-root `implementation.md`; that is the legacy name of the design reference.

- **Stable feature ID**: `feature.<namespace>.<outcome>`
- **Providing module**: exactly one current-level module
- **Decomposition decision**: keep the feature atomic unless one level of correlated sub-features
  makes both aggregate and focused specifications materially simpler
- **Feature containment**: a parent declares an ordered `subfeatures` list; each immediate child uses
  the same `kind: feature`, declares `parent_feature`, inherits the parent module, owns one `## Outcome`,
  and lives at `<parent>/subfeatures/<number-name>/`; a child cannot contain another child
- **Authority split**: parent text owns aggregate outcomes, shared vocabulary/invariants, dependencies,
  and decomposition rationale; child text owns only focused behavior and references shared parent facts
- **Observable textual outcome**: primary definition of the feature
- **Parent refinement**: adjacent parent-level feature IDs, or an explicit internal rationale
- **Representative scenarios**: examples of behavior, not an exhaustive definition
- **Core feature diagram**: at most one text-backed Archify `architecture` view for stable component
  participation and interaction; required for a cross-component feature unless a concise
  sufficiency rationale is recorded
- **Supplemental diagrams**: optional workflow, sequence, data-flow, or lifecycle views for narrower
  invocation, state, or movement questions; never substitutes for the core component view
- **Contracts**: at least one provided contract and every required boundary contract
- **Architecture view**: current module's one-level Archify JSON view
- **Evidence status**: `unknown`, `partial`, `verified`, or `disagrees`

Place feature-owned diagrams under the selected feature/sub-feature's `diagrams/` directory and name them for the question
or scenario they explain; do not call them `architecture.json`. Declare each diagram's `core` or
`supplemental` role in `spec.md` so
the project docsite embeds it automatically. They supplement `spec.md` and the providing module's
bounded view, and must not silently define behavior or contracts. Do not create a parallel Concorde
feature specification or a top-level `architecture/` source tree.
