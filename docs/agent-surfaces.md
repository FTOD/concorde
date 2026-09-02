# Maintaining Agent Surfaces

Concorde's framework checkout keeps canonical package sources at the repository root and generated
Codex/Claude surfaces in their normal project locations.

## Authorities

Canonical:

- `concorde.json`
- `skills/`
- `operations/`
- `templates/`
- `src/concorde/`
- `scripts/`
- `agent-assets/`

Generated checkout projections:

- `.agents/skills/concorde-*/SKILL.md`
- `.agents/skills/concorde-standard-dev-loop/SKILL.md`
- `.agents/skills/concorde-reflections-triage/SKILL.md`
- `.codex/agents/reflection_*.toml`
- `.claude/skills/concorde-*/SKILL.md`
- `.claude/skills/concorde-standard-dev-loop/SKILL.md`
- `.claude/skills/concorde-reflections-triage/SKILL.md`
- `.claude/agents/reflection-*.md`

The framework repository does not copy its package under `.concorde/framework`; root sources are
already available. Consumer projects receive that installed framework projection through the native
installer.

## Check and apply

```bash
python3 scripts/development/sync-agent-surfaces.py status --format json
python3 scripts/development/sync-agent-surfaces.py apply --format json
```

Status renders every leaf/Operation Skill and internal reflection-agent output for both integrations and classifies each desired path
as `current`, `create`, `update`, `replace-symlink`, or `conflict`. It does not write. Apply refreshes
only those exact generated paths, then reports their current state.

Capability rendering validates names/front matter, exact Operation pairs, safe package-relative
entry points, supported integration metadata, output uniqueness, and resolution of
`{SCRIPT}`/`{FRAMEWORK}`/`{OPERATION}` tokens. Source
checkout surfaces use root `scripts/` and `templates/`; installed surfaces use
`.concorde/framework/scripts/` and `.concorde/framework/templates/`.

## Preservation and failure behavior

Checkout sync treats its declared output paths as generated and may replace stale files or legacy
symlinks there. It never edits canonical inputs or unrelated agent assets. A desired path that is a
non-file conflict stops apply. Run deterministic validation/tests after refresh and commit canonical
sources and generated changes together.

For consumer installations, ownership is stricter: `.concorde/install.json` records every output
digest/role, and updates/removals require observed bytes to match that receipt. See
[Quick start](quick-start.md).
