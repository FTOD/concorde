# Concorde Core preset

This preset keeps the normal Spec Kit specification, planning, and task workflow while adding
Concorde's hierarchical architecture controls. It does not create another feature document.

At priority 10, its three spec/plan/tasks template contributions use `append`, while its Concorde-only
design template uses `replace`. Its nine normal lifecycle command contributions use
`replace`: each complete command preserves the corresponding Spec Kit 0.16.4 phase while resolving
Concorde's selected feature and durable/temporal paths before any path-sensitive work. The installed
extension supplies that workspace adapter and seven Concorde-specific surfaces: six runtime-backed
operations, including task-complete feature hardening, plus the agent-only, read-only `ask` procedure.

A feature keeps canonical module-owned `spec.md` and `design.md` at `features/<number-name>/`; it may
own one level of immediate sub-features at `subfeatures/<number-name>/`, each with a focused durable
pair and no children. The specification defines behavior, the design records the accepted realization, and scenarios remain
representative examples. The preset encourages
descriptively named, text-backed feature-owned Archify diagrams when component interaction,
invocation, boundary crossings, state, or data flow benefit from visual explanation. A
cross-component feature requires one `role: core` Archify architecture view or a concise rationale
that prose and the bounded module view are sufficient. Dynamic views are `role: supplemental`; a
sequence diagram can never be the core view. Maintained JSON lives under the feature's `diagrams/`
directory, is declared by `spec.md`, and is embedded
automatically by the project docsite; generated HTML never becomes specification authority.

Parent specifications own aggregate outcomes and shared constraints; sub-feature specifications own
focused behavior and inherit the parent module. Protocol v3 routes normal phases to exactly one
selected root and exposes parent durable context read-only without sibling bodies or attempts.
