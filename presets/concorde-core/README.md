# Concorde Core preset

This preset keeps the normal Spec Kit specification, planning, and task workflow while adding
Concorde's hierarchical architecture controls. It does not create another feature document.

At priority 10, its three spec/plan/tasks template contributions use `append`, while its Concorde-only
`abstract-template` and `implementation-template` feature documents and the project-wide `reflections-template`
(the reflection log seeded at the specification root and appended to by every phase after
specification) use `replace`. Its nine normal lifecycle
command contributions use `replace`: each complete command preserves the corresponding Spec Kit
0.16.4 phase while resolving Concorde's selected feature and durable/temporal paths before any
path-sensitive work. The installed extension supplies that workspace adapter and five
Concorde-specific surfaces: four runtime-backed operations, including task-complete feature
hardening, plus the agent-only, read-only `ask` procedure.

A feature keeps the canonical durable trio `abstract.md`, `design.md`, and `implementation.md` at
`features/<number-name>/`; it may own one level of immediate sub-features at
`subfeatures/<number-name>/`, each with the same focused durable trio and no children. The abstract is
the self-contained page read first (purpose, functionality, structure, logic; under 15 minutes),
feature `design.md` defines behavior, `implementation.md` records the accepted realization (a
placeholder until the first hardening), and scenarios remain representative examples. The
`module.md` of the module at which the feature is specified is the summary read first; its
`design.md` is a design reference opened only for a specific recorded detail and cited. A
temporal work lives only in `attempt/`. The preset encourages
descriptively named, text-backed feature-owned Archify diagrams when component interaction,
invocation, boundary crossings, state, or data flow benefit from visual explanation. A
cross-component feature requires one `role: core` Archify architecture view or a concise rationale
that prose and the module's level views are sufficient. Dynamic views are `role: supplemental`; a
sequence diagram can never be the core view. Maintained JSON lives under the feature's `diagrams/`
directory, is declared by feature `design.md`, and is embedded
automatically by the project docsite; generated HTML never becomes specification authority.

Parent specifications own aggregate outcomes and shared constraints; sub-feature specifications own
focused behavior and inherit the parent module. Protocol v6 routes normal phases to exactly one
selected root and exposes parent durable context read-only without sibling bodies or attempts.
