# Views

A view is any rendering of the model: a diagram, a terminology table, an index, a navigation tree,
a graph export, a documentation site. Views serve understanding: they are how most humans meet the
specification. Axiom A6 governs all of them: **a view is derived or checked, and an unchecked
picture is marked as such**, so that what a human sees cannot contradict what a harness computes
boundaries from.

## Derived views

A publisher renders views from declared relations. The renderer chooses:

- **scope** — which Modules, nodes and relation types to show;
- **grouping** — subgraphs, layers and ordering;
- **layout and styling**.

The renderer MUST NOT choose which relations exist. An omitted node or edge is a scope decision and
is not by itself a missing contract; an added edge is invalid output. Rendered views state their
scope and the relation types they display, so a reader knows what the absence of an edge means.

Derived views are rendered at publication or delivery time and are never written into reading
files. A publisher MAY enrich a written table, for example by showing an imported term's
definition next to its link; the enrichment is a view.

## Checked flowcharts

A `module` document may draw the architecture it explains. An unmarked Mermaid `flowchart` or `graph` block in
`module` reading is a **checked flowchart**: it may only assert what is declared.

- **Nodes.** Every node label resolves to exactly one of: a concept or realization of the owning
  Module, by title; a Module, by title; or a node of another Module, by the qualified form
  `Module title / node title`. An unresolved or ambiguous label is an error.
- **Edges.** Every edge carries a nonempty label and corresponds to a declared relation between its
  endpoints in the drawn direction: `relates`, `uses` or `contains`. For a `relates` edge the label
  SHOULD be the relation's `verb`.
- **Nothing else.** Subgraph titles, styling and comments assert nothing.

A checked flowchart need not show every declared relation; like a derived view, its omissions are
scope decisions. The `Relationships` section of an entry SHOULD contain a checked flowchart of the
principal collaboration.

Naming a node in a view grants no context and transfers no ownership. The owner is visible in a
qualified label, so a node of another Module cannot be mistaken for a local one.

## Illustrative blocks

Explanation sometimes needs a picture that is not a relationship inventory: a flow over time, a
state sketch, a before/after comparison. Any other Mermaid block, and any flowchart not meant as a
checked view, MUST be marked `illustrative` in its info string:

````markdown
```mermaid illustrative
sequenceDiagram
    accTitle: How a submission proceeds
    accDescr: Conceptual overview; not a relationship declaration.
    ...
```
````

An `illustrative` block is excluded from the model, labelled non-normative by the publisher and not
checked against declarations. It carries no authority beyond the surrounding prose, and it MUST NOT
be the only place a collaboration is described: a load-bearing relationship is declared.

## Publication obligations

A publisher MUST expose every stable identity as an addressable anchor, keep links as links rather
than transclusion, and show one canonical definition per node with its owner rather than copies.

A rendered view grants no reader context and MUST NOT be offered as a substitute for a complete
document. The Protocol specifies readable meaning and identity preservation; it does not prescribe
pages, sidebars, themes, folding or interaction behaviour.
