```concorde-document
{"id":"[stable-document-id]","targets":["[module-id]"],"main_visible":true}
```

# [Module title]

Save the reading entry as module.md and explicitly register this Module's complete collection.

## Features

[Define the provided set of features, their stable IDs, observable promises, effects and failures.]

## Interfaces

[Explain how each feature is used: API, function, CLI, file, protocol, event or other exchange.
Specify input/output shapes, preconditions, errors, compatibility and applicable retry semantics.]

## Architecture

[Describe the internal domain: concepts, private submodules, responsibilities, relationships,
collaborations, rules, state and completion/failure conditions. Each submodule has one parent.
A shared capability is an independent sibling. Implementation file layout is a separate relation.]

## Relied-upon promises

[Describe each direct dependency and submodule locally. Use concorde-dependencies entries with
target_id, responsibility, selection_condition and nonempty relied_upon_promises. Do not require
reading the provider's Spec or implementation to understand this Module or plan its tasks.]

## Missing information

[Identify unknown facts and the steps they block. Implementation Specs cannot fill semantic gaps.]
