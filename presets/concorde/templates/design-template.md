## Terminology

<!--
  Define only concepts and expressions introduced by this level. Terms from ancestor modules, the
  providing module chain, and (for a sub-feature) the immediate parent feature are inherited and
  MUST NOT be copied here. Use the exact columns below. A term cell contains one backticked preferred
  expression and may add `<br>Aliases:` followed by backticked aliases. Relationships are `None` or
  semicolon-separated `` `predicate` → `Target term` `` expressions whose targets resolve locally or
  through the permitted ancestor chain.

  If this level introduces no terminology, replace the table with exactly:
  No local terminology. This level uses inherited terminology unchanged.
-->

| Term | Meaning | Relationships |
|---|---|---|
| `[Preferred term]` | [Non-circular meaning sufficient for a reader who knows ancestor levels.] | `[predicate]` → `[Target term]` |

## Concorde Architecture Alignment

Record this feature in its single canonical `design.md` inside the providing module's
`features/<number-name>/` workspace.

Keep the adjacent durable `abstract.md` (the self-contained overview this phase authors together with
the design: Purpose, Functionality, Structure, Logic, Read Next; under 15 minutes) and
`implementation.md` (the accepted realization). Design work may read `implementation.md` to avoid
confusing accepted realization with required behavior, but must never update it. New features start
with the resolved implementation template's explicit placeholder: no implementation realization has
been accepted yet.

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
- **Legend policy**: every maintained Concorde Archify source explicitly sets
  `meta.legend.mode: hidden`; domain labels and the textual counterpart carry the meaning
- **Contracts**: at least one provided contract and every required boundary contract
- **Level views**: the providing module's architecture diagrams under `architecture/diagrams/`,
  linked from its `module.md`; a feature never redefines them
- **Evidence status**: `unknown`, `partial`, `verified`, or `disagrees`

Place feature-owned diagrams under the selected feature/sub-feature's `diagrams/` directory and name them for the question
or scenario they explain; do not call them `architecture.json`. Declare each diagram's `core` or
`supplemental` role in `design.md` so
the project docsite embeds it automatically. They supplement `design.md` and the providing module's
bounded level views, and must not silently define behavior or contracts. Do not create a parallel
Concorde feature specification or an `architecture/` tree outside the module hierarchy; a module's
own `architecture/` directory (its diagrams, boundary contracts, and submodules) belongs to its
package, and a change there is an architecture change, never a feature-owned artifact.
