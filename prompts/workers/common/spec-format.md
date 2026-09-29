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
- **A concept** is an entry of the project glossary (the JSON file the root Module's `glossary`
  field names), never a record in document metadata: `{"id": "concept.<name>", "title": "<Title>",
  "owner": "<the owning Module>", "definition": "<one sentence>", "explanation": "<module.md path of
  the owner>#<anchor>"}`, kept sorted by `id`, with an anchor `<a id="<anchor>"></a>` before the
  prose in that document that explains it. Titles are unique in the project: before adding a
  concept, look for an existing term with that meaning and use it. Add a concept only for a word
  that is not common sense (its meaning here is narrower than or different from ordinary usage)
  and that a Module other than its owner uses; the root Module's own terms are exempt from the
  second condition. Explain any other word in its owner's document where it is first used, or use
  it in its ordinary sense; a name of an Operation, a command, a rule or a component is not a
  concept, nor is an output record no other Module reasons about. A concept's `narrows`,
  `supersedes`, `contrasts` and `relates` are fields of its entry. Change only entries your bound
  Modules own.
- **A term link** is how a document uses a term: `[text](<relative path to the glossary>#concept.<name>)`.
  Link each term where a document first uses it; there are no Terminology tables.
- **A realization** record has `id`, `type`, `title`, `meaning` and `entries` (exact paths or
  directories ending in `/`); keep the entries the Module already binds.
- **Identities** are lowercase and project-wide unique; `<local>` is the Module identity without
  `module.`. An anchor is `<a id="identity"></a>` on a line of its own or at the very start of a
  paragraph; it is never inside a sentence or a table. Every anchor needs its own prose before the
  next heading or anchor: anchors explained by the same prose go together on one line
  (`<a id="a"></a><a id="b"></a>`), because a blank line between two anchors leaves the first one
  empty.
- **The entry** `module.md` has no required sections; the whole entry is the Module's design.
  Organize it for a developer who wants to understand the Module quickly: its purpose first, in
  short plain prose, then its core concepts (the Module's own terms, explained at their glossary
  anchors, and the terms it builds on, linked), then overview diagrams of its main structure,
  functions and flows with short prose, then the details: its parts, its collaborations with each
  child and provider at their `meaning` anchors, its entry points, errors and design reasons.
  Leave command-level walk-throughs to the Module that owns the commands. Never move the design or
  the Module's concept explanations into a separate topic.
- **Diagrams** use D2 wherever they make relationships, order, branching, state or data clearer.
  Place overview diagrams near the top of the entry and the others next to the details they
  explain. Draw every process as a workflow diagram, including branches, retries and an interaction
  among several Modules or agents: step nodes, directed edges and a clear main path, with a lane per
  participant or stage groups when helpful. Use a sequence diagram only when the interleaving of
  messages is itself the point. Use a state diagram for a lifecycle, or
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
