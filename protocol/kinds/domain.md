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

A main coordinator may admit this complete Domain Spec while routing a task. Therefore every child
Domain, participating Service, or downstream Module that may receive work is named here by stable
target ID together with its Domain-local responsibility and the condition for selecting it. This is
a routing view, not inherited access to the downstream Spec.
