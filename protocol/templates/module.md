# Module template

Copy the Markdown block below into the Module's `module.md` reading entry, replace placeholders with
project facts and explicitly register the complete collection. This is a starter layout for the
[required format](../format.md), not another kind of Spec or a completed contract.

The two level-2 parts serve different readers without creating different contracts. Usage &
Contract contains Purpose, Usage, Requirements and Scenarios; Architecture & Realization contains
Design, Entities and Relationships. These are level-3 subsections in the order shown. Additional
internal constraints and scenarios belong in the architecture part, not in the consumer guide.
Companion documents use one or both part headings without repeating this whole starter. The Mermaid
relationship model names exactly the declared entity titles and labels every edge.

````markdown
```concorde-document
{
  "id": "[document-id]",
  "owner": "[module-id]",
  "main_visible": true
}
```

# [Module title]

## Usage & Contract

### Purpose

[Two or three sentences of plain prose: what this Module is for, who uses it and the boundary of its
promises. No lists, tables or code.]

### Usage

[Explain when to use this Module, who or what consumes it, the concepts and prerequisites needed,
and a representative path from input to result. Name actual entry points or explain its role in a
composition; do not invent a public API for a logical responsibility. Explain effects, errors,
repeat behavior, cancellation and compatibility where applicable. Include examples or links to
canonical owned interface definitions; do not require readers to reconstruct use from scenarios.]

### Requirements

[Introduce the Module-level requirements. Each is one decidable SHALL statement.]

#### req.[module].[name] — [Requirement title]

[One sentence that SHALL or SHALL NOT hold for the Module as a whole.]

[Optional explanatory prose: rationale, scope, or a pointer to the scenarios that exercise it.]

### Scenarios

[Introduce the usage scenarios. Group them under ordinary headings when that helps reading.]

#### scenario.[module].[name] — [Scenario title]

- GIVEN [the precondition or state of the world]
- AND [a further precondition]
- WHEN [the trigger: what an actor or collaborator does]
- THEN [the observable outcome this Module promises]
- AND [a further outcome]
- BUT [an outcome that explicitly does not happen]

#### scenario.[module].[failure-name] — [Failure or repeated-invocation scenario]

- GIVEN [the state that makes the request invalid or repeated]
- WHEN [the same trigger]
- THEN [the defined failure or idempotent outcome]

## Architecture & Realization

### Design

[Explain how internal responsibilities, state and control/data flow fulfill the external guarantees.
Link to those guarantees instead of defining them again. Explain significant choices and required
invariants, the dependencies relied on, and the intended realization or explicit unknowns.
An inventory of entities alone is not a design explanation; current code is not a missing Spec.]

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
    "id": "entity.[module].[library]",
    "title": "[External capability title]",
    "kind": "external library",
    "responsibility": "[What this Module relies on it for; its vendored material is an external reference of the Module.]"
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
    library["[External capability title]"]
    first -->|[verb]| second
    first -->|[verb]| library
```

### Dependencies and composition

[Describe how each direct dependency or child contributes to this Module's promises.] [Remove the
block below if there are no direct dependencies or children.]

```concorde-dependencies
[
  {
    "target_id": "[provider-module-id]",
    "responsibility": "[Provider responsibility]",
    "selection_condition": "[When this collaboration applies]",
    "relied_upon_promises": ["[Guarantee](provider/interface.md#scenario.provider.name): [why this Module needs it]"]
  }
]
```

### Internal constraints and verification

[Define any required internal design constraints and their verification scenarios here, with the
same req./scenario. identities and syntax as above. Omit this subsection if none are needed.]

### Unresolved information

[Name unknown design facts and the promises they prevent realizing, or state that none remain.
Put unknown consumer behavior in Usage & Contract as well, where users would need that information.]
````

Register `references: []` or explicit `{kind, id}` entries on the Module, never in document
metadata. Include canonical collaborator definitions through these references and link to them in
prose. State local conditions and obligations without duplicating provider schemas. A link by itself
does not include its target, and referenced Modules' references are never followed. Optional section
headings may change without changing identity. The inventory's `files` for this Module must equal
the union of the entity `files` above, entry for entry: an entry ending in `/` stays that directory
prefix and is never expanded into names. Tests are listed on the entity they realize like any other
file; each test declares the scenario it verifies, and no Spec section lists tests.

## Optional shared interface document

An interface may live in another document owned by this Module. Give that file its own
`concorde-document` ID and the same owner, and add it to this Module's `documents`. Consumers add
its document ID or this Module ID to their own `references`; they do not register it as owned.
Put its consumer-facing definition under `## Usage & Contract` in that document and any internal
realization notes under `## Architecture & Realization`. Use this fragment once in the owner
document, after replacing the illustrative fields:

````markdown
```concorde-contract
{
  "id": "contract.example.request",
  "version": 1,
  "schema": {
    "type": "object",
    "properties": {"request_id": {"type": "string", "minLength": 1}},
    "required": ["request_id"],
    "additionalProperties": false
  },
  "semantics": "[Meaning of the request and its result; relate it to the interface entity.]",
  "example": {"request_id": "example-1"}
}
```

[Declare the offline schema vocabulary; state inputs, outputs, errors, effects, compatibility and
links to the defining scenarios. Ensure every necessary definition is in each participant's
explicitly resolved context. Omit neither failure nor repeated-invocation behavior.]
````

Each participant uses this separate fragment, with its actual peer and role. Internal participants
need complementary bindings; an external peer has the form `external:<name>`.

````markdown
```concorde-contract-binding
{
  "id": "contract.example.request",
  "version": 1,
  "role": "required",
  "peer": "module.provider",
  "selection_condition": "[When this participant uses the interface.]",
  "relied_upon_guarantees": ["[Request agreement](../provider/interface.md#contract.example.request): [local reliance]."],
  "obligations": ["[This participant's duties and response to failure.]"]
}
```
````

Do not copy the schema or example into the binding. These are illustrative placeholders, not another
Spec kind or an assertion that the example Modules and paths exist in a project.
