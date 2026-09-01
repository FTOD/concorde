# Design Reference: Workspace Files

## Implementation Notes

| Scope | Durable | Temporal |
|---|---|---|
| Project | `.concorde/config.json`, specification-root `reflections.md` | None |
| Module | `module.md`, `design.md`, `architecture/contracts/**`, `architecture/diagrams/**` | None |
| Feature | `abstract.md`, `design.md`, accepted `implementation.md`, feature contracts and diagrams | `attempt/**` |
| Selection | `.specify/feature.json` | Pointer to the active feature; not feature content |

`attempt/` may contain plan, tasks, research, data-model, quickstart, checklists, and attempt-local
contracts. Normal phases may update these files. Durable design and accepted implementation remain
outside the directory. The one project reflection log is durable because its entries may outlive the
attempt that discovered them.

## Design Rationale

Path placement communicates authority and lifetime without another database or registry. The
selected-workspace adapter derives paths from one Spec Kit-owned pointer and verifies registration
against the maintained hierarchy.

## Alternatives Considered

- Root-level temporary aliases: rejected because they become ambiguous with nested features.
- One file per reflection: rejected because the workflow needs one reviewable project log.
- Generated summaries as sources: rejected because projections must be disposable.

## Decision Log

- Promoted the file model to an immediate module.
- Defined `attempt/` as the only temporal-memory boundary.
- Kept selection state separate from durable feature content.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Feature workspace` | One canonical feature or sub-feature root containing durable sources and at most one current attempt. | `belongs to` → `Feature`; `contains` → `Durable artifact`; `contains` → `Attempt` |
| `Selection state` | The Spec Kit-owned pointer that chooses exactly one feature workspace for lifecycle routing. | `selects` → `Feature workspace` |
| `Accepted realization` | The durable account of how the currently accepted implementation realizes one feature; a placeholder means none is accepted. | `is a` → `Durable artifact`; `realizes` → `Feature` |
| `Project reflection log` | The specification-root file that records cross-attempt workflow problems without becoming behavioral intent. | `is a` → `Durable artifact`; `concerns` → `Feature` |
