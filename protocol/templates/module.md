# Module template

Copy the Markdown block below into the Module's `module.md` reading entry, replace placeholders
with project facts and explicitly register the complete collection. This is a starter layout for
the [required format](../format.md), not another kind of Spec or a completed contract.

The four headings Purpose, Scenarios, Entities and Architecture are mandatory in this order.
Scenario definitions and further entity blocks may also live in other single-owner documents of
the collection. The Mermaid flowchart must name exactly the declared entity titles and label every
edge with the relationship verb.

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

## Scenarios

[Introduce the usage scenarios. Group them under ordinary headings when that helps reading.]

### scenario.[module].[name] — [Scenario title]

- GIVEN [the precondition or state of the world]
- AND [a further precondition]
- WHEN [the trigger: what an actor or collaborator does]
- THEN [the observable outcome this Module promises]
- AND [a further outcome]

- req.[module].[name]: [One sentence that SHALL or SHALL NOT hold for this scenario.]

### scenario.[module].[failure-name] — [Failure or repeated-invocation scenario]

- GIVEN [the state that makes the request invalid or repeated]
- WHEN [the same trigger]
- THEN [the defined failure or idempotent outcome]

## Requirements

- req.[module].[invariant]: [One Module-wide sentence that SHALL hold regardless of scenario.]

## Entities

[Introduce the entities. Every child Module and used Module needs an entity with its target_id.]

```concorde-entities
[
  {
    "id": "entity.[module].[name]",
    "title": "[Entity title]",
    "kind": "[program | file | record | concept | interface | actor | submodule | used module]",
    "responsibility": "[What this entity does or represents.]",
    "files": ["[exact/project-relative/file]"],
    "pending": ["[a declared file that does not exist yet, or omit this field]"]
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

## Architecture

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
The inventory's `files` for this Module must equal the union of the entity `files` above.
