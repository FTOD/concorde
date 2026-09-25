---
audience: worker
---

## How Spec documents are written

You cannot read the Spec Protocol from the project, so its rules for writing a Module
specification are given here, and the host appends the project's own copy of the Protocol's guide
to writing one, with its templates, at the end of this brief. The host validates every document after you finish, and a
structural error stops your run. The rules workers most often break:

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
  each start with `GIVEN`, `WHEN`, `THEN`, `AND` or `BUT` and a space. It starts with `GIVEN` or
  `WHEN`, has at least one `WHEN` and one `THEN`, and never returns to an earlier kind.
- **A contract** is one `concorde-contract` JSON fence with exactly `id`, `version` (a positive
  integer), `schema`, `semantics` and `example`, where the example satisfies the schema.
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
  paragraph; it is never inside a sentence or a table.
- **The entry** `module.md` has the level-2 sections Purpose (plain prose, no lists or tables),
  Terminology, Usage, Design and Relationships, each exactly once.
- **Diagrams** are `d2` blocks. A plain `d2` block may only nest and connect Modules, concepts and
  realizations that are declared; when in doubt, mark it `d2 illustrative`. Mermaid is an error.
- **Every `uses`** in the `module` block has a `meaning` anchor in the entry resolving to prose that
  explains the collaboration.
