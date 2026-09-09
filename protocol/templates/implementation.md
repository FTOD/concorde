# Implementation template

Copy the Markdown block below into a registered Implementation document. Replace the placeholders
and register both the document collection and exact file bindings. The starter follows the
[required format](../format.md); its section names and order are suggestions.

````markdown
```concorde-document
{
  "id": "[document-id]",
  "targets": ["[implementation-id]"],
  "main_visible": false
}
```

# [Implementation title]

[Describe the realization and the Module contracts it serves.]

## Bound files

- `[exact/project-relative/file]`
- `[another/exact/file-if-needed]`

[Use an explicit nonempty set. Each file has one authoritative Implementation Spec owner.]
[Mark any declared file that has not yet been created.]

## Responsibilities and interfaces

[Explain the bound files' responsibilities and their implementation interfaces.]
[Keep the public behavioral promises in the using Module contracts.]

## Design, dependencies and constraints

[Describe relevant choices, internal dependencies and invariants.]
[Explain how this realization preserves each using Module's relied-upon contract.]
[If several Modules reuse this implementation, retain one binding and identify the shared reliance.]

## Verification

[Describe meaningful verification and expected outcomes for the realization.]
[Account for every using Module's contract; compatibility with one consumer does not prove all.]

## Unresolved information

[Identify unmade implementation decisions or missing outputs without inventing public promises.]
````

Replace the sample paths with actual declared files; directories and wildcards are not file
bindings. Several Modules may reference the same Implementation Spec without duplicating its
files or document membership. The `main_visible` value is a presentation choice and does not
remove the document from its complete collection.

A query of this Implementation selects its own registered Spec documents and declared authored
diagram sources. To understand how it
realizes a particular Module, explicitly select that using Module as well. Its other consumers
and its bound source files are not automatically added to a Spec query.
