# Module entry template

A starter for `module.md`. Satisfying this shape establishes nothing about meaning; see
[Module specifications](../module.md) for what each section must explain.

Register the entry in the project registry and write its paired `.md.json` with
`schema_version: 3`, `document.role: module`, the `module` block and explicit `defines` and
`relations` arrays. The [required format](../format.md) applies.

````markdown
# [Module title]

## Purpose

[What this Module is for, who relies on it, where its promises stop, and the relevant non-goals.
Short plain prose. Do not restate the directory or package name as a responsibility.]

## Terminology

| Term | Definition |
| --- | --- |
| Example record | The durable record of one accepted request. |
| [Thing](../provider/module.md#concept.provider.thing) | |

[Optional prose orienting the reader among the terms.]

## Usage

[Audience, use conditions, prerequisites and actual entry points. Follow one representative input
through its result and effects. Then errors, repeat invocation, cancellation and compatibility.
Include a concrete illustration where abstraction would hide a user decision. Name unsupported
behaviour as unsupported.]

<a id="concept.example.record"></a>

[Explain the example record where understanding it matters.]

## Design

<a id="realization.example.service"></a>

[Why the decomposition, state, flow, collaboration and failure containment fulfil the guarantees.
Connect each significant choice to the problem it prevents. Distinguish significant choices from
incidental implementation and open questions.]

## Relationships

```d2
example: Example {
  service: Example service {
    "src/example/"
  }
  record: Example record
  service -> record: saves
}
provider: Provider
example.service -> provider: reserves stock through
example -> provider
```

<a id="uses-example-provider"></a>

[For each child and provider: its responsibility, when the collaboration applies, the canonical
promises relied upon, and this Module's own duties and failure reactions. This is the anchor a
`contains` or `uses` relation points to. Explain the conditions and reactions a picture cannot
carry.]
````

The first Terminology row defines `concept.example.record`; the second is an import row, which
links to the provider's concept by identity and leaves the definition empty.

The diagram is checked. `Example` and `Provider` resolve to Module titles, `Example service` and
`Example record` to this Module's nodes, and `src/example/` to the entry the service binds. Nesting
asserts that Example owns both nodes and that the service binds its entry; the labelled edges match
the `relates` declarations below and the unlabelled edge between the two Modules matches the `uses`.
The look is the publisher's. A picture that should not be checked is marked `d2 illustrative`.

## Paired metadata

````json
{
  "schema_version": 3,
  "document": {
    "id": "document.example.module",
    "owner": "module.example",
    "role": "module"
  },
  "module": {
    "title": "Example",
    "owns": ["example/module.md"],
    "contains": [],
    "uses": [
      {"target": "module.provider", "meaning": "#uses-example-provider",
       "relies_on": ["concept.provider.thing"]}
    ],
    "includes": [],
    "participates": []
  },
  "defines": [
    {
      "id": "concept.example.record",
      "type": "concept",
      "title": "Example record",
      "meaning": "#concept.example.record"
    },
    {
      "id": "realization.example.service",
      "type": "realization",
      "title": "Example service",
      "meaning": "#realization.example.service",
      "entries": ["src/example/"]
    }
  ],
  "relations": [
    {"type": "relates", "source": "realization.example.service", "verb": "saves",
     "target": "concept.example.record"},
    {"type": "relates", "source": "realization.example.service",
     "verb": "reserves stock through", "target": "module.provider"}
  ]
}
````

The `uses` entry selects the provider's entry and the document defining `concept.provider.thing`,
which satisfies the context requirements of importing that concept and of relating to
`module.provider`. The `Provider` label in the diagram resolves because the provider Module's
title is `Provider`.

## Registry record

The project registry mirrors the `module` block and adds the entry path:

````json
{
  "id": "module.example",
  "title": "Example",
  "entry": "example/module.md",
  "owns": ["example/module.md"],
  "contains": [],
  "uses": [
    {"target": "module.provider", "meaning": "#uses-example-provider",
     "relies_on": ["concept.provider.thing"]}
  ],
  "includes": [],
  "participates": []
}
````
