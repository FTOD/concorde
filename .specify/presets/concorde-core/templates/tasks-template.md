
## Concorde Task Coverage

When applicable, include dependency-ordered tasks to update module-owned feature specifications,
module registrations, boundary contract definitions and custom schemas/examples under the module's
`architecture/contracts/`, the level's diagrams under `architecture/diagrams/`, deterministic Concorde validation, implementation/test traceability, and generated
output freshness. Mark evidence only after the producing command passes; retain `unknown` when no
implementation evidence exists.

First verify that the feature has at most one `role: core` diagram and that it uses Archify
`architecture` to show stable components and interactions; dynamic diagram kinds must be
`role: supplemental`. For each required feature-owned diagram, include tasks for the explanatory prose, descriptive Archify
JSON source under `diagrams/`, declaration in `design.md`, contract/scenario traceability, showcase
validation, explicit `meta.legend.mode: hidden`, generated HTML delivery, automatic feature-page
embedding, visual evidence when available, and freshness checks. Do not treat generated HTML or
screenshots as maintained intent.

Execution records the problems it meets in the project reflection log (`workspace.reflections`), not
in task text; a problem concerning another feature is recorded there and never fixed in that
feature's sources; and no task edits a maintainer-set status or note in the log.

Write the task list to `attempt/tasks.md` inside the selected feature workspace. Treat it as
work for the active delivery attempt, not as durable feature intent, and do not create a root-level
copy or symlink. Generate tasks against both feature `design.md` and accepted `implementation.md`
(a placeholder means no accepted baseline), but do
not generate a task that edits `abstract.md`, feature `design.md`, feature `implementation.md`, any
module `module.md` or `design.md`, or removes `attempt/`; after every task is complete,
the user may invoke the separate Concorde acceptance command.

For a selected sub-feature, every task path must remain beneath that child root except explicit
read-only references to the parent durable design/implementation. Do not generate tasks that mutate or
accept a parent/sibling root, read a parent/sibling attempt implicitly, or create another
`subfeatures/` directory beneath the child.
