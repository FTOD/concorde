# Concorde Bundle

This integration-neutral bundle pins `preset:concorde@0.9.0` and
`extension:concorde@0.9.0` and inherits the project's active coding-agent integration. It declares
no workflow or reusable step.

The component set implements Architecture Source Profile 7 and Feature Workspace Protocol 12:

- recursive modules each own one `architecture.md` with typed entities, directed relationships,
  interactions, immediate module/feature inventory, and optional architecture-owned diagrams;
- level-local features are direct `features/<NNN-name>.md` files with usage, requirements, embedded interfaces, and
  an Architecture Zoom over module entities;
- source code and tests are implementation/evidence authority;
- one optional `.concorde/attempts/<stable-feature-id>/` holds temporal planning and validation
  memory, while `.concorde/reflections/log.md` holds tracked process memory; and
- Delivery Proposal 8 validates completion and removes only that attempt.

The preset contributes four templates, replaces nine normal Spec Kit 0.16.4 lifecycle commands, and
adds fast-loop. The extension contributes five commands: runtime-backed `init`, `context`,
`validate`, and `deliver`, plus read-only agent-followed `ask`. It also ships reflection-triage/v3
orchestration assets, atomic reflection ID/removal tooling, and deterministic projection tooling.

Before installation, register the reviewed Concorde catalogs as install-allowed sources. Published
catalogs use HTTPS artifact URLs; loopback HTTP catalogs produced for acceptance testing are not
public release sources.

```bash
specify bundle validate --path bundles/concorde-bundle
specify bundle build --path bundles/concorde-bundle --output dist
specify bundle info concorde-bundle --json
specify bundle install concorde-bundle
python .specify/extensions/concorde/scripts/python/concorde.py --project-root . \
  agent-assets preview --integration codex --concorde-version 0.9.0
python .specify/extensions/concorde/scripts/python/concorde.py --project-root . \
  agent-assets sync --integration codex --concorde-version 0.9.0
python .specify/extensions/concorde/scripts/python/concorde.py --project-root . \
  agent-assets verify --integration codex --concorde-version 0.9.0
```

Disabling or reprioritizing a preset changes future template resolution but may not unregister
already materialized surfaces in Spec Kit 0.16.4. Removing the bundle recomposes registered commands
and restores any surviving lower layer. Project-authored `.concorde/`, `specs/`, source, tests, and
docs are never bundle-owned. Agent projection update/removal touches only receipt-owned unchanged
paths; modified, unrelated, inactive-integration, and shared triage state are preserved.
