# Concorde Core preset

This preset keeps the normal Spec Kit specification, planning, and task workflow while adding
Concorde's hierarchical architecture controls. It does not create another feature document.

At priority 10, its three spec/plan/tasks template contributions use `append`: they add architecture
guidance without replacing Spec Kit's templates. Its nine normal lifecycle command contributions use
`replace`: each complete command preserves the corresponding Spec Kit 0.16.4 phase while resolving
Concorde's selected feature and durable/temporal paths before any path-sensitive work. The installed
extension supplies that workspace adapter and the five Concorde-specific commands.

A feature remains one canonical module-owned `features/<number-name>/spec.md`; its text and
requirements define behavior, while scenarios are representative examples. The preset encourages
descriptively named, text-backed feature-owned Archify diagrams when component invocation, boundary
crossings, state, or data flow benefit from visual explanation. Cross-component scenarios require
such a view or a concise rationale that prose and the bounded module view are sufficient. Maintained
JSON lives under the feature's `diagrams/` directory, is declared by `spec.md`, and is embedded
automatically by the project docsite; generated HTML never becomes specification authority.
