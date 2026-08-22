
## Concorde Task Coverage

When applicable, include dependency-ordered tasks to update module-owned feature specifications,
module registrations, boundary contract definitions and custom schemas/examples, current-level
Archify JSON, deterministic Concorde validation, implementation/test traceability, and generated
output freshness. Mark evidence only after the producing command passes; retain `unknown` when no
implementation evidence exists.

First verify that the feature has at most one `role: core` diagram and that it uses Archify
`architecture` to show stable components and interactions; dynamic diagram kinds must be
`role: supplemental`. For each required feature-owned diagram, include tasks for the explanatory prose, descriptive Archify
JSON source under `diagrams/`, declaration in `spec.md`, contract/scenario traceability, showcase
validation, generated HTML delivery, automatic feature-page embedding, visual evidence when
available, and freshness checks. Do not treat generated HTML or screenshots as maintained intent.

Write the task list to `implementation/tasks.md` inside the selected feature workspace. Treat it as
work for the active delivery attempt, not as durable feature intent, and do not create a root-level
copy or symlink.
