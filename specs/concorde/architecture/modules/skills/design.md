# Design Reference: Skills

## Implementation Notes

- `presets/concorde/commands/` owns the nine normal-phase instruction layers.
- `presets/concorde/templates/` owns the composed file templates.
- `extensions/concorde/commands/` owns five Concorde-specific skills.
- Active Spec Kit integrations materialize those sources into `.agents/skills/`, `.claude/`, or an
  equivalent agent-native directory.
- `speckit.concorde.ask` remains an agent-followed, read-only procedure; it is intentionally absent
  from the runtime CLI.

Each skill must make four things obvious: the selected workspace, files it may read, files it may
write, and any script operation it must invoke. Structured script findings are presented without
being silently repaired or reinterpreted.

## Design Rationale

The boundary is defined by user interaction rather than by Spec Kit packaging. Presets and extension
commands belong together here because both become skills. Launchers and runtime Python belong to
Scripts even though the extension archive distributes them together.

## Alternatives Considered

- Organize by preset versus extension package: rejected because users experience one skill set.
- Put workspace routing in Skills: rejected for deterministic path resolution; the skill requests it
  from Scripts and consumes the returned paths.

## Decision Log

- Named the module after the installed user-facing artifact.
- Kept agent-followed questions separate from runtime-backed operations.
