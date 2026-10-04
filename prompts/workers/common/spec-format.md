---
audience: worker
---

## How Spec documents are written

You cannot read the Spec Protocol from the project. The host therefore appends its installed
**Spec writing guidelines** and templates at the end of this brief. The guidelines have four
parts. Use each of them:

- **Required format** for machine-checkable structure and syntax
- **Writing guidance** for what the content must explain to its reader
- **Sentence style** for how each sentence is written
- **Evaluating a Spec** for how a Spec is judged good

Semantic requirements and mandatory terms retain their force.
Passing structural validation does not establish semantic sufficiency. After you finish, the host
validates every document. A structural error stops your run. The complete guidelines follow. The
reminders below cover common format mistakes and writing judgments:

- **A document is a pair**: a reading file `X.md` and its metadata `X.md.json`. Every document a
  Module owns is listed in `module.owns` of the Module's entry metadata. Never edit the project
  registry. The host regenerates it.
- **Metadata `defines` holds only `concept` and `realization` records.** The following are never
  metadata records:
  - requirements
  - scenarios
  - contracts

  They are declared in the reading of an `implementation` document. That document's metadata is
  exactly
  `{"schema_version": 3, "document": {"id": "document.<name>", "owner": "<module id>", "role": "implementation"}, "defines": [], "relations": [], "extensions": {}}`.
- **A requirement** is a heading `### req.<local>.<name> — Title` followed by one sentence that
  contains `SHALL` or `SHALL NOT` exactly once. Further paragraphs may explain the requirement.
  Two obligations are two requirements.
- **A scenario** is a heading `### scenario.<local>.<name> — Title` followed by list items. Each
  item starts with one of these keywords and a space, never a comma:
  - `GIVEN`
  - `WHEN`
  - `THEN`
  - `AND`
  - `BUT`

  `AND, once
  …` is not a step: write `AND once …`. A scenario starts with `GIVEN` or `WHEN`. It has at least
  one `WHEN` and one `THEN`. It never returns to an earlier kind.
- **A contract** is one `concorde-contract` JSON fence with exactly these fields:
  - `id`
  - `version` (a positive integer)
  - `schema`
  - `semantics`
  - `example`

  The example satisfies the schema. The schema uses only these keywords:
  - `$schema`
  - `$id`
  - `$defs`
  - `$ref` (only `#/$defs/<name>`)
  - `title`
  - `description`
  - `examples`
  - `default`
  - `type`
  - `properties`
  - `required`
  - `additionalProperties`
  - `items`
  - `minItems`
  - `maxItems`
  - `uniqueItems`
  - `minLength`
  - `maxLength`
  - `pattern`
  - `minimum`
  - `maximum`
  - `enum`
  - `const`
  - `anyOf`
  - `oneOf`
  - `allOf`
  - `format`

  Say anything else, such as a constraint on keys (`propertyNames`), in `semantics`.
- **A concept** is an entry of the project glossary, never a record in document metadata. The
  project glossary is the JSON file the root Module's `glossary` field names. A concept entry has
  this form:
  `{"id": "concept.<name>", "title": "<Title>",
  "owner": "<the owning Module>", "definition": "<one sentence>", "explanation": "<module.md path of
  the owner>#<anchor>"}`.
  Keep entries sorted by `id`. Before the prose in that document that explains the concept, put
  an anchor `<a id="<anchor>"></a>`. Titles are unique in the project. Before adding a concept,
  look for an existing term with that meaning and use it. Add a concept only for a word that meets
  both conditions:
  - The word is not common sense (its meaning here is narrower than or different from ordinary
    usage).
  - A Module other than its owner uses the word.

  The root Module's own terms are exempt from the second condition. Explain any other word in
  its owner's document where it is first used, or use it in its ordinary sense. Names of the
  following are not concepts:
  - an Operation
  - a command
  - a rule
  - a component

  Nor is an output record no other Module reasons about. A concept's entry holds these fields:
  - `narrows`
  - `supersedes`
  - `contrasts`
  - `relates`

  Change only entries your bound Modules own.
- **A term link** is how a document uses a term:
  `[text](<relative path to the glossary>#concept.<name>)`.
  Where a document first uses each term, link the term. There are no Terminology tables.
- **A realization** record has these fields:
  - `id`
  - `type`
  - `title`
  - `meaning`
  - `entries` (exact paths or directories ending in `/`)

  Keep the entries the Module already binds.
- **Identities** are lowercase and project-wide unique. `<local>` is the Module identity without
  `module.`. An anchor is `<a id="identity"></a>` on a line of its own or at the very start of a
  paragraph. It is never inside a sentence or a table. Before the next heading or anchor, every
  anchor needs its own prose. Anchors explained by the same prose go together on one line
  (`<a id="a"></a><a id="b"></a>`). A blank line between two anchors leaves the first one empty.
- **The entry** `module.md` has no required sections. The whole entry is the Module's design.
  Organize it for a developer who wants to understand the Module quickly. Use this order:
  - Start with its purpose, in short plain prose.
  - Present its core concepts: the Module's own terms, explained at their glossary anchors, and
    the terms it builds on, linked.
  - Present overview diagrams of its main structure, functions and flows with short prose.
  - Present the details: its parts, its collaborations with each child and provider at their
    `meaning` anchors, its entry points, errors and design reasons.

  Leave command-level walk-throughs to the Module that owns the commands. Never move the design
  or the Module's concept explanations into a separate topic.
- **Diagrams** use D2 wherever they make any of these clearer:
  - relationships
  - order
  - branching
  - state
  - data

  Place overview diagrams near the top of the entry. Place the others next to the details they
  explain. Draw every process as a workflow diagram. Include branches, retries and an
  interaction among several Modules or agents. Use step nodes, directed edges and a clear main
  path. When helpful, use a lane per participant or stage groups. Only when the interleaving of
  messages is itself the point, use a sequence diagram. For a lifecycle, use a state diagram.
  For the design question at hand, use any of these views:
  - component
  - context
  - deployment
  - data-model

  Each diagram answers one clear question. It uses the Spec's terminology. It complements
  explanatory prose about these aspects:
  - conditions
  - effects
  - failure reactions

  There is no quota. Invent no promises to fill a view. A checked `d2` block uses only the
  semantic subset and declared static relations. It uses these forms:
  - nesting for containment, ownership and bindings
  - unlabelled Module edges for `uses`
  - labelled edges for `relates` with their declared verbs

  All other views use `d2 illustrative`, including these views:
  - workflows
  - sequences
  - state transitions

  Illustrative views carry no authority beyond the prose. They never replace the declaration
  and explanation of a load-bearing collaboration. Disconnected inventories usually add
  nothing to a list. Mermaid is an error. A plain block never uses a D2 keyword, not even as a
  shape key such as `link: Source link`. Its D2 keywords are these:
  - `label`
  - `shape`
  - `style`
  - `class`
  - `classes`
  - `direction`
  - `near`
  - `icon`
  - `tooltip`
  - `link`
  - `width`
  - `height`
  - `top`
  - `left`
  - `constraint`
  - `vars`
  - `layers`
  - `scenarios`
  - `steps`
  - `grid-rows`
  - `grid-columns`
  - `grid-gap`
  - `vertical-gap`
  - `horizontal-gap`
  - `source-arrowhead`
  - `target-arrowhead`
  - `filled`
  - `multiple`
  - `3d`
- **Every `uses`** in the `module` block has a `meaning` anchor in the entry. The anchor resolves
  to prose that explains the collaboration.
