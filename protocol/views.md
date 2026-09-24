# Views

A view is any rendering of the model: a diagram, a terminology table, an index, a navigation tree,
a graph export, a documentation site. Views serve understanding: they are how most humans meet the
specification. Axiom A6 governs all of them: **a view is derived or checked, and an unchecked
picture is marked as such**, so that what a human sees cannot contradict what a harness computes
boundaries from.

## Derived views

A publisher renders views from declared relations. The renderer chooses:

- **scope** — which Modules, nodes and relation types to show;
- **grouping** — nesting, layers and ordering;
- **layout and styling**.

The renderer MUST NOT choose which relations exist. An omitted node or edge is a scope decision and
is not by itself a missing contract; an added edge is invalid output. Rendered views state their
scope and the relation types they display, so a reader knows what the absence of an edge means.

Derived views are rendered at publication or delivery time and are never written into reading
files. A publisher MAY enrich a written table, for example by showing an imported term's
definition next to its link; the enrichment is a view.

## Checked diagrams

A document draws structure in [D2](https://github.com/d2lang/d2). A `d2` block that is not marked
`illustrative` is a **checked diagram**: it states only what is drawn, what nests in what and what
points at what, and it may only assert what is declared. How the diagram looks (shapes, colours,
line styles, layout, direction) is chosen by the publisher from what each shape resolves to, never
written in reading. A checked diagram appears only in `module` reading.

**The semantic subset.** A checked diagram consists of:

- **shapes**, written `key` or `key: Label`, where a key may be quoted and the label is the text
  that resolves;
- **nesting**, written as a shape followed by a `{ ... }` block holding other statements;
- **edges**, written `a -> b` or `a -> b: label`, possibly chained, whose ends are keys or dotted
  key paths relative to the enclosing block;
- comments starting with `#`, and `;` between statements on one line.

Nothing else is allowed: no D2 keyword (such as `style`, `shape`, `class`, `direction`, `near`,
`label`, `icon`, `vars`), no imports, globs, filters, substitutions, block strings or arrays, and no
edge other than `->`.

**Shapes.** Every shape resolves by its label, or by its key when it has no label, to exactly one of:
a concept or realization of the owning Module, by title; a Module, by title; a node of another
Module, by the qualified form `Module title / node title`; or, only directly inside a realization
shape, a **file** of that realization: a bound entry path, or a suffix of exactly one bound entry
that begins after a `/`. An unresolved or ambiguous shape is an error. In a Module's own reading,
its own title always names the Module, even when one of its concepts shares that title; such a
concept is drawn with the qualified form, `Checkout / Checkout`.

**Nesting** asserts what it encloses:

| Outer shape | Inner shape | Asserts |
| --- | --- | --- |
| Module | Module | the outer Module `contains` the inner one |
| Module | concept, realization or qualified node | the outer Module owns the node |
| realization | file | the realization binds the file |

Any other nesting is an error. Containment is drawn only by nesting, never by an edge.

**Edges** assert a declared relation in the drawn direction:

- An unlabelled edge between two Modules asserts a `uses`: the plain arrow is the dependency.
- A labelled edge asserts a `relates` between its ends, and its label SHOULD be the relation's
  `verb`. An edge that touches a concept, realization or qualified node always carries a label.
- A file shape has no edges; it asserts only its binding.

A checked diagram need not show every declared relation; like a derived view, its omissions are
scope decisions. The `Relationships` section of an entry SHOULD contain a checked diagram of the
principal collaboration, and a Module that binds files SHOULD draw its realizations with the files
they bind, so a reader sees how the Module is built.

````markdown
```d2
checkout: Checkout {
  service: Checkout service {
    "service.py"
  }
  record: Order record
  service -> record: saves
}
inventory: Inventory
checkout -> inventory
```
````

Here `Checkout` and `Inventory` resolve to Modules, `Checkout service` to a realization and
`Order record` to a concept of Checkout, and `service.py` to a file that Checkout service binds.
The picture asserts that Checkout owns both nodes, that the realization binds the file, that a
`relates` with verb `saves` connects them, and that Checkout `uses` Inventory.

Naming a shape in a view grants no context and transfers no ownership. The owner is visible in a
qualified label or in the enclosing Module, so a node of another Module cannot be mistaken for a
local one.

## Illustrative blocks

Explanation sometimes needs a picture that is not a relationship inventory: a flow over time, a
state sketch, a before/after comparison. Such a block is marked `illustrative` in its info string
and may use the whole D2 language:

````markdown
```d2 illustrative
shape: sequence_diagram
client: Client
checkout: Checkout
client -> checkout: submit
checkout -> client: order number
```
````

An `illustrative` block is excluded from the model, labelled non-normative by the publisher and not
checked against declarations. It carries no authority beyond the surrounding prose, and it MUST NOT
be the only place a collaboration is described: a load-bearing relationship is declared. Diagrams
in any other language are not part of reading; a Mermaid block is an error.

## Publication obligations

A publisher MUST expose every stable identity as an addressable anchor, keep links as links rather
than transclusion, and show one canonical definition per node with its owner rather than copies.

A rendered view grants no reader context and MUST NOT be offered as a substitute for a complete
document. The Protocol specifies readable meaning and identity preservation; it does not prescribe
pages, sidebars, themes, folding or interaction behaviour.
