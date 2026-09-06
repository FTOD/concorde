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

# Domain

A Domain is a business or problem-space scope, independent of the Service/Module component structure.
Its complete resolved context—Target Spec plus explicitly referenced Shared Specs—explains the system's operation within this scope: meaningful entities,
relationships, responsibilities, interaction triggers, rules, state transitions, completion, and failure.
A Domain can describe observable features. It does not own implementation paths. A narrower Domain may
have a scope parent; participating Services and Modules are a separate relation and can be shared across
scopes. Shared membership admits only that physical document; parent, participant and co-referencing
entity collections are not implicit context.

To assess completeness, ask what each entity means, who is responsible for each rule, when interactions
occur, what information crosses them, and how success, failure, and retry affect the business outcome.
Missing facts block the affected task as Spec incomplete. A Domain's Spec need not reproduce private
component inventories, but it must contain the promises it uses to explain the system.

A main coordinator may admit only this Domain's `main_visible` Target Spec and Shared Specs while routing a task. Therefore every child
Domain, participating Service, or downstream Module that may receive work is named here by stable
target ID together with its Domain-local responsibility and the condition for selecting it. This is
a routing view, not inherited access to the downstream Spec.

## Local promises and interactions

[Define all target-relevant entities, ownership, inputs, outputs, conditions, failure, completion and retry semantics here. Name routable downstream targets by stable ID, responsibility and selection condition. Include every required collaborator contract locally. Do not rely on parent, provider or sibling documents outside the registered collection.]

## Participating components

[Include exactly one entry for every Service or Module whose registry `participates_in` list directly
names this Domain. You may also repeat a participant from a nested Domain when this broader Domain
actually needs to route work to it. Omit the block only when the Domain has no relevant participants.]

```concorde-participants
[
  {
    "target_id": "[service-or-module-id]",
    "kind": "[service-or-module]",
    "responsibility": "[Responsibility inside this Domain]",
    "selection_condition": "[When a Domain task selects this target]",
    "relied_upon_promises": [
      "[A complete promise this Domain relies on]"
    ]
  }
]
```

## Missing information

[State unresolved obligations honestly. A task blocked by missing facts returns Spec incomplete.]
