
## Concorde Architecture Alignment

Record this feature in its single canonical `spec.md` inside the providing module's
`features/<number-name>/` workspace.

- **Stable feature ID**: `feature.<namespace>.<outcome>`
- **Providing module**: exactly one current-level module
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

Place feature-owned diagrams under the feature's `diagrams/` directory and name them for the question
or scenario they explain; do not call them `architecture.json`. Declare each diagram's `core` or
`supplemental` role in `spec.md` so
the project docsite embeds it automatically. They supplement `spec.md` and the providing module's
bounded view, and must not silently define behavior or contracts. Do not create a parallel Concorde
feature specification or a top-level `architecture/` source tree.
