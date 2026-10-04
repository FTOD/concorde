# Views

A view is any rendering of the model:

- A diagram.
- The glossary page.
- An index.
- A navigation tree.
- A graph export.
- A documentation site.

Views serve understanding: they are how most humans meet the specification. Axiom A6 governs all of
them: **a view is derived or checked**. Axiom A6 also states that **an unchecked picture is marked
as such**. These rules ensure that what a human sees cannot contradict what a harness computes
boundaries from.

## Derived views

A publisher renders views from declared relations. The renderer chooses:

- **scope** — which Modules, nodes and relation types to show.
- **grouping** — nesting, layers and ordering.
- **layout and styling**.

The renderer MUST NOT choose which relations exist. An omitted node or edge is a scope decision.
It is not by itself a missing contract. An added edge is invalid output. Rendered views state their
scope and the relation types they display, so a reader knows what the absence of an edge means.

Derived views are rendered at publication or delivery time. They are never written into reading
files. A publisher renders the glossary as a page. The publisher sends every term link to its entry
there. A publisher MAY enrich reading, for example by showing a term's definition when a reader
points at its link. Another example is listing the terms a Module owns on its page. Every such
enrichment is a view.

## Checked diagrams

A document draws structure in [D2](https://github.com/d2lang/d2). A `d2` block that is not marked
`illustrative` is a **checked diagram**. It states only:

- What is drawn.
- What nests in what.
- What points at what.

A checked diagram may only assert what is declared. The publisher chooses how the diagram looks
from what each shape resolves to. This look, its shapes, colours, line styles, layout and direction, is
never written in reading. A checked diagram appears only in `module` reading.

**The semantic subset.** A checked diagram consists of:

- **shapes**, written `key` or `key: Label`. A key may be quoted. The label is the text that
  resolves.
- **nesting**, written as a shape followed by a `{ ... }` block holding other statements.
- **edges**, written `a -> b` or `a -> b: label`, possibly chained. Their ends are keys or dotted
  key paths relative to the enclosing block.
- Comments starting with `#`, and `;` between statements on one line.

Nothing else is allowed. No D2 keyword (such as `style`, `shape`, `class`, `direction`, `near`,
`label`, `icon`, `vars`) is allowed. Imports, globs, filters, substitutions, block strings and arrays
are not allowed. No edge other than `->` is allowed.

**Shapes.** When a shape has no label, it resolves by its key. Otherwise, it resolves by its label.
Every shape resolves to exactly one of:

- A concept or realization of the owning Module, by title.
- A Module, by title.
- A node of another Module, by the qualified form `Module title / node title`.
- Only directly inside a realization shape, a **file** of that realization.

That file is a bound entry path, or a suffix of exactly one bound entry that begins after a
`/`. An unresolved or ambiguous shape is an error. In a Module's own reading, its own title always
names the Module, even when one of its concepts shares that title. Such a concept is drawn with the
qualified form, `Checkout / Checkout`.

**Nesting** asserts what it encloses:

| Outer shape | Inner shape | Asserts |
| --- | --- | --- |
| Module | Module | the outer Module `contains` the inner one |
| Module | concept, realization or qualified node | the outer Module owns the node |
| realization | file | the realization binds the file |

Any other nesting is an error. Containment is drawn only by nesting, never by an edge.

**Edges** assert a declared relation in the drawn direction:

- An unlabelled edge between two Modules asserts a `uses`: the plain arrow is the dependency.
- A labelled edge asserts a `relates` between its ends. Its label SHOULD be the relation's
  `verb`. An edge that touches a concept, realization or qualified node always carries a label.
- A file shape has no edges. It asserts only its binding.

A checked diagram need not show every declared relation. Like a derived view, its omissions are
scope decisions. An entry draws its structure in as many diagrams as it needs. Each diagram answers
one question. Typically, it shows the inside or the outside. A typical inside diagram is one where
a Module whose function is carried by several realizations draws them with the files they bind
and the edges between them. A typical outside diagram shows the Module among the Modules it uses
and those that use it.

Whichever Module declares the relation, an edge may join any two shapes whose relation is declared.
Thus, the outside view may draw a consumer's `uses` of this Module or a `relates` from one of its
realizations to another Module. Realizations that only keep the repository running are left to
prose. Examples include project configuration, development tooling or test suites. A diagram shows
architecture, not an inventory of files. See [Writing
guidance](module.md#diagrams).

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

Here the names resolve as follows:

- `Checkout` and `Inventory` resolve to Modules.
- `Checkout service` resolves to a realization.
- `Order record` resolves to a concept of Checkout.
- `service.py` resolves to a file that Checkout service binds.

The picture asserts the following:

- Checkout owns both nodes.
- The realization binds the file.
- A `relates` with verb `saves` connects the nodes.
- Checkout `uses` Inventory.

Naming a shape in a view grants no context. It transfers no ownership. The owner is visible in a
qualified label or in the enclosing Module. Thus, a node of another Module cannot be mistaken for a
local one.

## Illustrative blocks

Explanation sometimes needs a picture that is not a relationship inventory:

- A workflow.
- A state sketch.
- A before/after comparison.

Such a block is marked `illustrative` in its info string. It may use the whole D2 language:

````markdown
```d2 illustrative
direction: right
customer: Customer {
  submit: Submit basket
  receive: Receive order number
}
checkout: Checkout {
  hold: Hold stock
  order: Create order
  hold -> order
}
customer.submit -> checkout.hold
checkout.order -> customer.receive
```
````

An `illustrative` block has these properties:

- It is excluded from the model.
- It is labelled non-normative by the publisher.
- It is not checked against declarations.

It carries no authority beyond the surrounding prose. An `illustrative` block MUST NOT be the only
place a collaboration is described. A load-bearing relationship is declared. Diagrams in any other
language are not part of reading. A Mermaid block is an error.

## Publication obligations

A publisher MUST do all of the following:

- Expose every stable identity as an addressable anchor.
- Keep links as links rather than transclusion.
- Show one canonical definition per node with its owner rather than copies.

A rendered view grants no reader context. A rendered view MUST NOT be offered as a substitute for a
complete document. The Protocol specifies readable meaning and identity preservation. It does not
prescribe pages, sidebars, themes, folding or interaction behaviour.
