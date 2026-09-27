# Module entry template

A starter for `module.md`. Begin with [Spec writing guidelines](../writing.md) and use both parts:
[Required format](../format.md) for structure and syntax, and [Writing guidance](../module.md) for
what each section must explain. Satisfying this shape establishes nothing about meaning.

Register the entry in the project registry and write its paired `.md.json` with
`schema_version: 3`, `document.role: module`, the `module` block and explicit `defines` and
`relations` arrays. Declare the Module's concepts as entries of the project glossary. The
[required format](../format.md) applies.

````markdown
# [Module title]

## Purpose

[What this Module is for, who relies on it, where its promises stop, and the relevant non-goals.
Short plain prose. Do not restate the directory or package name as a responsibility.]

## Usage

[Audience, use conditions, prerequisites and actual entry points. Follow one representative input
through its result and effects. Then errors, repeat invocation, cancellation and compatibility.
Include a concrete illustration where abstraction would hide a user decision. Name unsupported
behaviour as unsupported. Use a diagram next to the normal path when it makes the process clearer.
The lightweight workflow below shows progression; replace its placeholders with the actual steps
and explain their conditions and effects in prose, or omit it if it adds no clarity. Add lanes or
stage groups only when responsibility or phases matter.]

```d2 illustrative
direction: right
start: "[User's first step]"
act: "[Module's action]"
finish: "[Result and effects]"
start -> act -> finish
```

<a id="concept.example-record"></a>

[Explain the [example record](../glossary.json#concept.example-record) where understanding it
matters. Link every term where the document first uses it, such as the provider's
[thing](../glossary.json#concept.thing).]

## Design

<a id="realization.example.service"></a>

[How the Module is built and why: the decomposition, state, flow and failure containment, and how
each significant choice fulfils a guarantee or prevents a problem. Distinguish significant choices
from incidental implementation and open questions.]

[The inside, if the Module has structure worth drawing: its children and the realizations that
carry its function, with the files they bind and the edges that matter.]

```d2
example: Example {
  service: Example service {
    "src/example/"
  }
  record: Example record
  service -> record: saves
}
```

[The outside: how the Module works with the Modules around it, and which of its parts meets which
of theirs.]

```d2
example: Example {
  service: Example service
}
provider: Provider
example.service -> provider: reserves stock through
example -> provider
```

<a id="uses-example-provider"></a>

[For each child and provider: its responsibility, when the collaboration applies, the canonical
promises relied upon, and this Module's own duties and failure reactions. This is the anchor a
`contains` or `uses` relation points to. Explain the conditions and reactions a picture cannot
carry. Use further diagrams wherever they clarify relationships, order, branching, state or data:
a workflow/activity/flow view for a process and its branches or retries, a sequence for participant
message ordering, a state view for a lifecycle, or a component, context, deployment or data-model
view for the design question at hand. Each answers one question next to explanatory prose, using
the same terminology. There is no required count or set of diagrams; invent no promises to fill
them.]
````

The two term links declare that this document mentions `concept.example-record`, which Example
owns, and `concept.thing`, which the provider owns: a reader of Example receives both definitions.
The anchor `concept.example-record` holds the extended explanation the glossary entry names.

The Usage workflow is `d2 illustrative`: its steps and progression explain behaviour, not declared
static relations. Sequence lifelines are useful when message ordering needs explanation, not a
prerequisite for drawing a process. Keep Usage views by the normal path or other behaviour they
explain, and design views in Design.

Both Design diagrams are checked, and each answers one question: the first how Example is built,
the second how it meets its provider. `Example` and `Provider` resolve to Module titles, `Example
service` and `Example record` to this Module's nodes, and `src/example/` to the entry the service
binds. Nesting asserts that Example owns both nodes and that the service binds its entry; the
labelled edges match the `relates` declarations below and the unlabelled edge between the two
Modules matches the `uses`. Checked diagrams use only the D2 semantic subset and declared static
relations; the look is the publisher's. All other views use `d2 illustrative`, with no authority
beyond the surrounding prose and no substitute for declaring load-bearing collaborations. There
is no separate Relationships section: the design holds both the inside and the outside.

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
