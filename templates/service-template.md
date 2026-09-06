```concorde-document
{
  "id": "[stable-document-id]",
  "targets": [
    "[target-id]"
  ],
  "main_visible": true
}
```

# [Target title]

Stable target ID: [id]. Register this and every other member explicitly; filenames have no meaning.

# Service

A Service is a self-contained capability with an explicit boundary contract. Its complete resolved
context—Target Spec plus explicitly referenced Shared Specs—explains its consumer-facing features, representative uses, prerequisites, obligations,
configuration, runtime inputs, outputs, state/effects, failures, compatibility, and applicable retries
and idempotency. A boundary may be an executable, file exchange, HTTP, or a specified standard format;
standalone deployment is not required. Configuration, runtime data, and host-derived authority are
separate. Every custom wire field has local semantics, a type/version, and a conforming example.

The Service can participate in several Domain scopes and compose Services or Modules. Its own Spec
contains necessary business rules and required collaborator contracts; scope and component parents
and provider or co-referencing entity Specs are not implicit context. Features may have stable IDs
anywhere in the resolved document collection. Selecting a Feature does not reduce that context.

A main coordinator may admit only this Service's `main_visible` Target Spec and Shared Specs to refine routing. Every downstream Domain,
Service, or Module that may receive work is named here by stable target ID, local responsibility and
selection condition. The coordinator may route to a Module from this information but cannot expand
that Module's remaining Spec; a different target worker receives its complete resolved context.

## Local promises and interactions

[Define all target-relevant entities, ownership, inputs, outputs, conditions, failure, completion and retry semantics here. Name routable downstream targets by stable ID, responsibility and selection condition. Include every required collaborator contract locally. Do not rely on parent, provider or sibling documents outside the registered collection.]

## Missing information

[State unresolved obligations honestly. A task blocked by missing facts returns Spec incomplete.]
