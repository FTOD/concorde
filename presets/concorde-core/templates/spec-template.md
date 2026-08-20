
## Concorde Architecture Alignment

Record this feature in its single canonical `spec.md` inside the providing module's
`features/<number-name>/` workspace.

- **Stable feature ID**: `feature.<namespace>.<outcome>`
- **Providing module**: exactly one current-level module
- **Observable textual outcome**: primary definition of the feature
- **Parent refinement**: adjacent parent-level feature IDs, or an explicit internal rationale
- **Representative scenarios**: examples of behavior, not an exhaustive definition
- **Contracts**: at least one provided contract and every required boundary contract
- **Architecture view**: current module's one-level Archify JSON view
- **Evidence status**: `unknown`, `partial`, `verified`, or `disagrees`

Do not create a parallel Concorde feature specification or a top-level `architecture/` source tree.
