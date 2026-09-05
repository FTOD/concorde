# [Target title]

Stable target ID: [id]. Register this and every other member explicitly; filenames have no meaning.

# Domain

A Domain is a business or problem-space scope, independent of the Service/Module component structure.
Its complete Markdown collection explains the system's operation within this scope: meaningful entities,
relationships, responsibilities, interaction triggers, rules, state transitions, completion, and failure.
A Domain can describe observable features. It does not own implementation paths. A narrower Domain may
have a scope parent; participating Services and Modules are a separate relation and can be shared across
scopes. Parent and participant Specs are not implicit context.

To assess completeness, ask what each entity means, who is responsible for each rule, when interactions
occur, what information crosses them, and how success, failure, and retry affect the business outcome.
Missing facts block the affected task as Spec incomplete. A Domain's Spec need not reproduce private
component inventories, but it must contain the promises it uses to explain the system.

## Local promises and interactions

[Define all target-relevant entities, ownership, inputs, outputs, conditions, failure, completion and retry semantics here. Include every required collaborator contract locally. Do not rely on parent, provider or sibling documents outside the registered collection.]

## Missing information

[State unresolved obligations honestly. A task blocked by missing facts returns Spec incomplete.]
