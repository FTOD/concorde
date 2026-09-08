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

Stable target ID: [id]. Save this main Spec as `ontology.md`, register it explicitly, reference
only this Domain, and keep it main-visible. Other topic documents remain explicit members of this
Domain's complete Spec collection. File layout is not component composition.

## Scope

[Introduce this Domain's purpose, who or what participates, and the outcomes it explains. Prefer
an overview that establishes overall understanding. Put detailed explanations in the relevant child
Domain, Service, Module or topic Spec where useful, with links for readers. Expand internal structure
when it helps explain actual collaborations; no fixed abstraction level or black-box view is required.
These are writing suggestions, not additional conformance gates.]

## Ontology

[Group entities into meaningful categories. Define each entity type, its meaning and responsibility,
and name directed relationships within this Domain and with relevant external entities. Briefly
explain unfamiliar terms where helpful. Using a protocol or modeling system does not automatically
make all of its internal concepts part of this page's subject. Distinguish modeling concepts from
physical files when they are relevant to the Domain. Do not replace relationships with a flat glossary.]

## Architecture overview

[Register one Archify JSON source with kind `architecture` and recipe `system-overview`. Explain the
Domain boundary, the primary collaboration path and relevant external relationships. The docsite
embeds the accepted diagram on this ontology.md main page. Use Archify System overview, request
showcase validation, and target generated/diagrams/. Do not invent architecture for unknown facts.]

## Local promises and interactions

[Explain the collaborations, triggers, relied-upon promises, completion, failure and retry behavior
needed to understand this Domain. Detail can live in other explicitly registered documents rather
than being repeated on the main page. Name routable targets by stable ID, responsibility and selection
condition in the main-visible collection. Links guide human readers but do not implicitly admit a
parent, participant or sibling's remaining Specs into an agent's context.]

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
