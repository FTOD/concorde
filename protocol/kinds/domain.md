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

Every component whose registry record directly names this Domain in `participates_in` has exactly one
entry in a fenced `concorde-participants` JSON array somewhere in this Domain's registered collection:

```concorde-participants
[
  {
    "target_id": "service.transfer",
    "kind": "service",
    "responsibility": "Decide transfer admission and execute accepted transfers in this Domain.",
    "selection_condition": "Select for a task about transfer rules, execution, completion, or failure.",
    "relied_upon_promises": [
      "Accepted transfers debit the sender and credit the receiver exactly once."
    ]
  }
]
```

The array may contain several participants and a collection may contain several blocks, but target
IDs are unique across the complete collection. Each entry describes this Domain's perspective, not
the participant's private interface. A broader Domain may repeat a component participating in a
nested Domain when the broader scope genuinely routes work to it. Missing or inconsistent entries
are rejected by deterministic validation. Context solving reports a missing direct entry as a Spec
gap and an inconsistent entry as conflicting.
