# Module entry template

A starter for `module.md`. Begin with [Spec writing guidelines](../writing.md) and use both parts:
[Required format](../format.md) for structure and syntax, and [Writing guidance](../module.md) for
what the entry must explain. Satisfying this shape establishes nothing about meaning.

The Protocol requires no section of an entry. The headings below follow the recommended reading
order, purpose, core concepts, overview, then details; rename, merge or split them as the Module's
reader needs, and give the details whatever headings suit the Module.

Register the entry in the project registry and write its paired `.md.json` with
`schema_version: 3`, `document.role: module`, the `module` block and explicit `defines` and
`relations` arrays. Declare the Module's concepts as entries of the project glossary. The
[required format](../format.md) applies.

````markdown
# [Module title]

## Purpose

[What this Module is for, who relies on it, where its promises stop, and the relevant non-goals.
Short plain prose. Do not restate the directory or package name as a responsibility.]

## Core concepts

<a id="concept.example-record"></a>

[Explain the [example record](../glossary.json#concept.example-record): what it is, why the Module
needs it and how it relates to the other ideas here. Link every term of another Module where the
document first uses it, such as the provider's [thing](../glossary.json#concept.thing).]

## Overview

[How the Module is built and how it meets the Modules around it, in one picture if one suffices,
with short prose saying what it shows.]

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

[How a typical piece of work progresses, as a workflow with a lane per participant when who does
each step matters. Replace the placeholders with the actual steps and explain their conditions and
effects in prose, or omit the diagram if it adds no clarity.]

```d2 illustrative
direction: right
user: User {
  request: "[User's request]"
  result: "[Result and effects]"
}
example: Example {
  act: "[Module's action]"
}
user.request -> example.act -> user.result
```

## [A detail, under a heading that names it]

<a id="realization.example.service"></a>

[The details, in the order that suits the Module: its parts and how each carries the function; its
actual entry points, following a representative input through its result and effects, then errors,
repeat invocation, cancellation and compatibility, naming unsupported behaviour as unsupported; the
reasons for significant choices, distinguished from incidental implementation and open questions.]

<a id="uses-example-provider"></a>

[For each child and provider: its responsibility, when the collaboration applies, the canonical
promises relied upon, and this Module's own duties and failure reactions. This is the anchor a
`contains` or `uses` relation points to. Add further diagrams beside the details they clarify: a
state view for a lifecycle, a workflow for a process with its branches and retries, or a component,
context, deployment or data-model view for the design question at hand. Draw a sequence diagram
only when the interleaving of messages is itself the point. There is no required count or set of
diagrams; invent no promises to fill them.]
````

The two term links declare that this document mentions `concept.example-record`, which Example
owns, and `concept.thing`, which the provider owns: a reader of Example receives both definitions.
The anchor `concept.example-record` holds the extended explanation the glossary entry names, in the
entry of its owner rather than in a separate topic.

The overview diagram is checked and answers one question: how Example is built and how it meets
its provider. `Example` and `Provider` resolve to Module titles, `Example service` and `Example
record` to this Module's nodes, and `src/example/` to the entry the service binds. Nesting asserts
that Example owns both nodes and that the service binds its entry; the labelled edges match the
`relates` declarations below and the unlabelled edge between the two Modules matches the `uses`. A
Module with more structure may draw its inside and its outside in two diagrams. Checked diagrams
use only the D2 semantic subset and declared static relations; the look is the publisher's.

The workflow is `d2 illustrative`: its steps and progression explain behaviour, not declared
static relations. Its lanes show who does each step, and an edge between lanes is a hand-off, which
is why a process among several participants needs no sequence lifelines. Illustrative views carry
no authority beyond the surrounding prose and never substitute for declaring load-bearing
collaborations. How the Module fits with the rest is part of its explanation, not a separate list
of relationships.

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
       "relies_on": ["concept.thing"]}
    ],
    "includes": [],
    "participates": []
  },
  "defines": [
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
     "target": "concept.example-record"},
    {"type": "relates", "source": "realization.example.service",
     "verb": "reserves stock through", "target": "module.provider"}
  ]
}
````

The `uses` entry selects the provider's entry and the document explaining `concept.thing`, which
satisfies the context requirement of relating to `module.provider`. The `Provider` label in the
diagram resolves because the provider Module's title is `Provider`.

## Glossary entry

Example's concept is an entry of the project glossary, which names Example as its owner and the
anchor above as its explanation:

````json
{
  "id": "concept.example-record",
  "title": "Example record",
  "owner": "module.example",
  "definition": "The durable record of one accepted request.",
  "explanation": "example/module.md#concept.example-record"
}
````

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
     "relies_on": ["concept.thing"]}
  ],
  "includes": [],
  "participates": []
}
````
