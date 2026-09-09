# Module template

Copy the Markdown block below into the Module's `module.md` reading entry, replace placeholders
with project facts and explicitly register the complete collection. This is a starter layout for
the [required format](../format.md), not another kind of Spec or a completed contract.

The Features and Interfaces sections may be combined or split across registered documents.
Retain the required Architecture section marker somewhere in the collection. Include an authored
diagram when it helps explain nontrivial structure, and explicitly identify its source, kind and
title. The standard does not require a particular drawing tool.

````markdown
```concorde-document
{
  "id": "[document-id]",
  "targets": ["[module-id]"],
  "main_visible": true
}
```

# [Module title]

[State the cohesive responsibility, who uses it and the boundary of its promises.]

## Spec context

[Identify the complete registered document collection and declared authored diagram sources.]
[Keep this reading guide consistent with the inventory; it is not a second membership authority.]
[Every Feature or Interface query selects this complete Module context.]
[Implementation context follows from the implementation references below; do not list files here.]

## Features

### [feature-id] — [Feature title]

[Explain applicability, observable outcome, guarantees, constraints and failure behavior.]

## Interfaces

### [interface-id] — [Interface title]

[Identify the supported features and exchange: API, function, command, file, protocol or event.]
[Define inputs, preconditions, outputs, effects, errors, compatibility and applicable retry behavior.]
[Include examples that clarify significant behavior.]

## Architecture

[Describe internal concepts, submodules, responsibilities, relationships and collaboration.]
[Explain invariants, state transitions and completion or failure conditions.]
[Keep structural parentage, capability use and implementation reuse distinct.]
[Include a useful diagram, or explain why the structure is simple enough for prose.]

## Dependencies and composition

[Describe how each direct dependency or child contributes to this Module's promises.]
[Remove the block below if there are no direct dependencies or children.]

```concorde-dependencies
[
  {
    "target_id": "[provider-module-id]",
    "responsibility": "[Provider responsibility]",
    "selection_condition": "[When this collaboration applies]",
    "relied_upon_promises": ["[Required provider guarantee]"]
  }
]
```

## Implementation references

[Identify the referenced Implementation Specs and the realizations they supply.]
[Keep exact file ownership in those Implementation Specs.]

## Unresolved information

[Name unknown facts and the behavior they leave unspecified, or state that none remain.]
````

The feature and interface IDs and defining document paths must agree with the explicit inventory.
Every relied-upon collaborator promise must be understandable locally; a link to another Spec
cannot supply missing meaning. Optional section headings may change without changing identity.
