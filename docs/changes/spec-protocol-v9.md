# Protocol 9: explanations for readers without implementation knowledge

## Why the previous migration was insufficient

The Protocol-8 split correctly separated formal definitions and ownership, but did not by itself
make the remaining prose explanatory. The authoring instructions emphasized complete identities,
permission boundaries, failure states and compatibility more concretely than reader prerequisites,
normal-path order or examples. The Framework required exact executable Flow diagrams without fixing
their reading layer. Structural tests could therefore accept a topic that contained a private API or
wire-field catalog written as ordinary prose. This was also an editorial execution problem: removing
formal headings did not establish that the remaining document answered a newcomer's questions.

These are contributing design and instruction pressures, not evidence that a specific model response
was caused by one sentence. The correction addresses Protocol principles, shared author/reviewer
instructions, validators and actual prose together.

## Principles and representation

Protocol 9.0.0 explicitly assumes general software knowledge but no project implementation knowledge.
Entries now follow Purpose, Terminology, Usage, Design and Relationships. Topics have a short
orientation and an early Terminology section. Tables explain relevant concepts, not entity/file
inventories. Definitions are canonical in one table; later uses link directly to that table without
copying the definition. Required sources remain explicit context references, never link traversal.

Private API inventories, wire layouts, byte algorithms, persistence details and exact executable
Flow catalogs are Implementation Specs regardless of heading syntax. Explanations retain the normal
path, outcome, important stops, design reasons, examples and visible safety limitations. Conceptual
diagrams are identified as such and do not compete with machine-checked execution topology. Semantic
review asks whether the intended reader can explain those facts, not whether text is short enough.

Metadata schema 2, Framework Profile 14, registry schema 5 and worker wire layouts are unchanged.
The project explicitly binds the new Protocol bytes. Installation does not migrate consumer Specs
or accept a new Protocol automatically.

## Project editing

All Module entries have plain-language purposes and early terminology. A Framework-owned concepts
unit defines shared vocabulary; local domain concepts are defined in relevant entry/topic tables.
Imported definitions are available through explicit references. The 24 most implementation-heavy
topics were rewritten around user questions and normal examples; their exact clauses, stable anchors,
local declarations and executable diagrams remain in directly Module-owned execution references.
Other explanation pages were revised where needed, including Installation, Registry, Values, Context
and Structural validation. The largest repeated provider agreements and historical ownership ledger
are separated from the default conceptual reading path without losing identity or ownership.

The rewrite preserves the distinction between a worker tool gate and an OS sandbox, the absence of
shell confinement by the gate, Linux-only isolated checks, possible partial code edits on failure,
the managed-runtime replacement gap, source-worktree removal by default delivery, and the separate
explicit primary merge. Easier reading is not a reason to hide those limits.

## Evidence and limits

Python and TypeScript check early section/table shape, definition placement, direct canonical table
links and explicit context inclusion. Fenced examples stay opaque. Exact Flow fences remain in
Implementation Specs and continue to be compared with the compiled runtime. Regression tests check
malformed tables, missing/excluded definitions, forwarding-only tables, metadata invalidation and
fresh consumer initialization. These checks establish structure and traceability, not semantic
completeness or usability with every real reader.

Run the checkout's deterministic build, `build --check`, `validate`, the Python test runner,
docsite checks, and the offline ID/link audit against baseline `6e07e514`. Existing definition IDs,
Module owners, formal requirement statements and scenario steps are preserved except explicit
language-format updates. A relocated ordinary heading needs a corrected link; publication does not
invent redirects from historical fragments.
