# Module template

Copy the Markdown block below into the Module's `module.md` reading entry, replace placeholders
with project facts and explicitly register the complete collection. This is a starter layout for
the [required format](../format.md), not another kind of Spec or a completed contract.

The four headings Purpose, Requirements, Scenarios and Ontology are mandatory in this order, and
Ontology holds the Entities and Relationships subsections. Requirement and scenario definitions
and further entity blocks may also live in other single-owner documents of the collection. The
Mermaid flowchart must name exactly the declared entity titles and label every edge with the
relationship verb.

````markdown
```concorde-document
{
  "id": "[document-id]",
  "targets": ["[module-id]"],
  "main_visible": true
}
```

# [Module title]

## Purpose

[Two or three sentences of plain prose: what this Module is for, who uses it and the boundary of
its promises. No lists, tables or code.]

## Requirements

[Introduce the Module-level requirements. Each is one decidable SHALL statement.]

### req.[module].[name] — [Requirement title]

[One sentence that SHALL or SHALL NOT hold for the Module as a whole.]

[Optional explanatory prose: rationale, scope, or a pointer to the scenarios that exercise it.]

## Scenarios

[Introduce the usage scenarios. Group them under ordinary headings when that helps reading.]

### scenario.[module].[name] — [Scenario title]

- GIVEN [the precondition or state of the world]
- AND [a further precondition]
- WHEN [the trigger: what an actor or collaborator does]
- THEN [the observable outcome this Module promises]
- AND [a further outcome]
- BUT [an outcome that explicitly does not happen]

### scenario.[module].[failure-name] — [Failure or repeated-invocation scenario]

- GIVEN [the state that makes the request invalid or repeated]
- WHEN [the same trigger]
- THEN [the defined failure or idempotent outcome]

## Ontology

[Introduce the Module's world: what exists in its domain and how those things relate.]

### Entities

[Introduce the entities. Every child Module and used Module needs an entity with its target_id.]

```concorde-entities
[
  {
    "id": "entity.[module].[name]",
    "title": "[Entity title]",
    "kind": "[program | file | record | concept | interface | actor | submodule | used module]",
    "responsibility": "[What this entity does or represents.]",
    "files": ["[exact/project-relative/file]", "[project-relative/directory/]"],
    "pending": ["[a declared entry that does not exist yet, or omit this field]"]
  },
  {
    "id": "entity.[module].[collaborator]",
    "title": "[Collaborator title]",
    "kind": "used module",
    "target_id": "[provider-module-id]",
    "responsibility": "[What this Module relies on it for.]"
  }
]
```

### Relationships

[Explain invariants, state transitions and completion or failure conditions the edges cannot show.]

```mermaid
flowchart TB
    accTitle: [Module title] entities and relationships
    accDescr: [One or two sentences describing the diagram for readers who cannot see it.]
    first["[Entity title]"]
    second["[Collaborator title]"]
    first -->|[verb]| second
```

## Dependencies and composition

[Describe how each direct dependency or child contributes to this Module's promises.]
[Remove the block below if there are no direct dependencies or children.]

```concorde-dependencies
[
  {
    "target_id": "[provider-module-id]",
    "responsibility": "[Provider responsibility]",
    "selection_condition": "[When this collaboration applies]",
    "relied_upon_promises": ["[scenario.provider.name: required provider guarantee]"]
  }
]
```

## Unresolved information

[Name unknown facts and the behavior they leave unspecified, or state that none remain.]
````

Every relied-upon collaborator promise must be understandable locally; a link to another Spec
cannot supply missing meaning. Optional section headings may change without changing identity.
The inventory's `files` for this Module must equal the union of the entity `files` above, entry
for entry: an entry ending in `/` stays that directory prefix and is never expanded into names.
Tests are listed on the entity they realize like any other file; each test declares the scenario
it verifies, and no Spec section lists tests.
