---
audience: worker
---

## How Spec documents are written

You cannot read the Spec Protocol from the project, so the host appends its installed
**Spec writing guidelines** and templates at the end of this brief. Use both parts: **Required
format** for machine-checkable structure and syntax, and **Writing guidance** for what the content
must explain to its reader. Semantic requirements and mandatory terms retain their force;
passing structural validation does not establish semantic sufficiency. The host validates every
document after you finish, and a structural error stops your run. The reminders below cover
common format mistakes and writing judgments; the complete guidelines follow.

- **A document is a pair**: a reading file `X.md` and its metadata `X.md.json`. Every document a
  Module owns is listed in `module.owns` of the Module's entry metadata. Never edit the project
  registry; the host regenerates it.
- **Metadata `defines` holds only `concept` and `realization` records.** Requirements, scenarios
  and contracts are never metadata records: they are declared in the reading of an
  `implementation` document, and that document's metadata is exactly
  `{"schema_version": 3, "document": {"id": "document.<name>", "owner": "<module id>", "role": "implementation"}, "defines": [], "relations": [], "extensions": {}}`.
- **A requirement** is a heading `### req.<local>.<name> — Title` followed by one sentence that
  contains `SHALL` or `SHALL NOT` exactly once; further paragraphs may explain it. Two
  obligations are two requirements.
- **A scenario** is a heading `### scenario.<local>.<name> — Title` followed by list items that
  each start with `GIVEN`, `WHEN`, `THEN`, `AND` or `BUT` and a space, never a comma (`AND, once
  …` is not a step: write `AND once …`). It starts with `GIVEN` or
  `WHEN`, has at least one `WHEN` and one `THEN`, and never returns to an earlier kind.
- **A contract** is one `concorde-contract` JSON fence with exactly `id`, `version` (a positive
  integer), `schema`, `semantics` and `example`, where the example satisfies the schema. The
  schema uses only these keywords: `$schema`, `$id`, `$defs`, `$ref` (only `#/$defs/<name>`), `title`, `description`, `examples`, `default`, `type`, `properties`, `required`, `additionalProperties`, `items`, `minItems`, `maxItems`, `uniqueItems`, `minLength`, `maxLength`, `pattern`, `minimum`, `maximum`, `enum`, `const`, `anyOf`, `oneOf`, `allOf` and `format`. Say anything else, such as a
  constraint on keys (`propertyNames`), in `semantics`.
- **A concept** is defined only in a `module` document: a metadata record
  `{"id": "concept.<local>.<name>", "type": "concept", "title": "<Title>", "meaning": "#concept.<local>.<name>"}`,
  exactly one row `| <Title, exactly the record's title> | <one sentence> |` in that document's
  Terminology table, and an anchor `<a id="concept.<local>.<name>"></a>` before the prose that
  explains it. A row of the table either defines a concept of the document or links to another
  Module's concept with an empty definition cell; there are no other rows.
- **A realization** record has `id`, `type`, `title`, `meaning` and `entries` (exact paths or
  directories ending in `/`); keep the entries the Module already binds.
- **Identities** are lowercase and project-wide unique; `<local>` is the Module identity without
  `module.`. An anchor is `<a id="identity"></a>` on a line of its own or at the very start of a
  paragraph; it is never inside a sentence or a table. Every anchor needs its own prose before the
  next heading or anchor: anchors explained by the same prose go together on one line
  (`<a id="a"></a><a id="b"></a>`), because a blank line between two anchors leaves the first one
  empty.
- **The entry** `module.md` has the level-2 sections Purpose (plain prose, no lists or tables),
  Terminology, Usage and Design, each exactly once, and no `Relationships` section: Design holds
  how the Module is built inside and how it works with the Modules around it, and explains each
  child and provider at its `meaning` anchor.
- **Diagrams** use D2 wherever they make relationships, order, branching, state or data clearer.
  Place Usage diagrams next to the normal path or other behaviour they explain, and design diagrams
  in Design. Choose a lightweight workflow/activity/flow diagram for a process, including branches
  and retries: action or step nodes, directed edges and a clear main path, with responsibility lanes
  or stage groups when helpful. Use a sequence diagram when participant message ordering needs
  explanation; ordinary processes do not need lifelines. Use a state diagram for a lifecycle, or
  component, context, deployment and data-model views for the design question at hand. Each diagram
  answers one clear question, uses the Spec's terminology and complements explanatory prose about
  conditions, effects and failure reactions. There is no quota; invent no promises to fill a view.
  A checked `d2` block uses only the semantic subset and declared static relations: nesting for
  containment, ownership and bindings, unlabelled Module edges for `uses`, labelled edges for
  `relates` with their declared verbs. All other views use `d2 illustrative`, including workflows,
  sequences and state transitions. Illustrative views carry no authority beyond the prose and never
  replace the declaration and explanation of a load-bearing collaboration. Disconnected inventories
  usually add nothing to a list. Mermaid is an error.
  A plain block never uses a D2 keyword, not even as a shape key such as `link: Source link`: its
  D2 keywords are `label`, `shape`, `style`, `class`, `classes`, `direction`, `near`, `icon`,
  `tooltip`, `link`, `width`, `height`, `top`, `left`, `constraint`, `vars`, `layers`,
  `scenarios`, `steps`, `grid-rows`, `grid-columns`, `grid-gap`, `vertical-gap`,
  `horizontal-gap`, `source-arrowhead`, `target-arrowhead`, `filled`, `multiple` and `3d`.
- **Every `uses`** in the `module` block has a `meaning` anchor in the entry resolving to prose that
  explains the collaboration.
