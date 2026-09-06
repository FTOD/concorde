```concorde-document
{
  "id": "[stable-document-id]",
  "targets": [
    "[target-id]"
  ],
  "main_visible": false
}
```

# [Target title]

Stable target ID: [id]. Register this and every other member explicitly; filenames have no meaning.

# Module

A Module is a cohesive implementation responsibility specified through its provided and required APIs.
Function calls are valid boundaries. Its complete resolved Target Spec plus Shared Specs defines callable signatures,
input and output types, preconditions, state/effects, obligations, errors, compatibility, and representative
usage. Describe APIs directly instead of manufacturing Feature wrappers. Interface signatures and usage
examples are Spec content; private algorithms and helpers belong to implementation source.

A Module may compose components and participate in Domain scopes independently. Its own Spec states
all business facts and collaborator promises required to understand and use its APIs. Shared
membership admits only that physical document; it does not inherit a Service's, Domain's, parent's,
provider's, or co-referencing entity's remaining Spec. Selecting one API retains the complete
resolved context. Only an implementation invocation may expose authorized source code.

The main coordinator may design or route this Module from identity, responsibility and selection
facts contained in admitted main-visible Domain/Service documents plus exact registry metadata. It
never expands this Module target. A main-visible shared document may be seen through an admitted
Domain or Service without admitting the Module's other documents. During an accepted topology
change, separately bound referencing Spec authors receive the current Module documents and proposed
descriptor.

## Local promises and interactions

[Define all target-relevant entities, ownership, inputs, outputs, conditions, failure, completion and retry semantics here. Include every required collaborator contract locally. Do not rely on parent, provider or sibling documents outside the registered collection.]

## Missing information

[State unresolved obligations honestly. A task blocked by missing facts returns Spec incomplete.]
