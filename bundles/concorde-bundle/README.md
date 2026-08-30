# Concorde Bundle

This integration-agnostic bundle pins `preset:concorde@0.5.0` and
`extension:concorde@0.5.0` and inherits the project's active coding-agent integration. It declares
no workflow or reusable step.

The preset contributes six architecture-aware templates, modifies nine normal Spec Kit 0.16.4
lifecycle commands through complete instruction layers, and adds fast-loop. The extension contributes five Concorde-specific
surfaces: four operations backed by the selected-workspace adapter and deterministic runtime
(`init`, `context`, `validate`, `impl.accept`), plus one agent-followed `ask` procedure that
reads cited guidance without mutation. Spec Kit resolves and materializes both sets through the
active agent integration. The extension also ships Feature 005's canonical reflection-triage
orchestrator, two specialized roles, Claude/Codex wrappers, queue helper, and deterministic
projector. The bundle remains only the pinned installation recipe.

The installed Feature Workspace Protocol v8 supports an atomic feature or one level of immediate
sub-features. Each selected root retains its own `abstract.md`/`design.md`/`implementation.md` trio and at most
one `attempt/` attempt; a selected child receives only read-only parent durable context and
concise sibling navigation, and cannot contain another child. Features are created with the normal
`speckit.specify` phase at their canonical path and selected through standard Spec Kit selection;
the bundle adds no creation or selection command.

Before installation, register the Concorde preset and extension catalogs as reviewed,
install-allowed sources. Release catalogs use HTTPS artifact URLs; the localhost HTTP catalogs
created by `scripts/release/build-components.py --base-url http://127.0.0.1:8765` are acceptance-only.

```bash
specify bundle validate --path bundles/concorde-bundle
specify bundle build --path bundles/concorde-bundle --output dist
specify bundle info concorde-bundle --json
specify bundle install concorde-bundle
python .specify/extensions/concorde/scripts/python/concorde.py --project-root . \
  agent-assets preview --integration codex --concorde-version 0.5.0
python .specify/extensions/concorde/scripts/python/concorde.py --project-root . \
  agent-assets sync --integration codex --concorde-version 0.5.0
python .specify/extensions/concorde/scripts/python/concorde.py --project-root . \
  agent-assets verify --integration codex --concorde-version 0.5.0
```

Disabling or reprioritizing a preset changes future template resolution but, in Spec Kit 0.16.4,
does not unregister already materialized command surfaces. Removing the bundle recomposes registered
commands and restores any surviving lower preset layer. Project-authored `.concorde/`, `specs/`, and
`docs/` content is never bundle-owned. Agent update/removal changes only projection paths whose
current digest still matches `.specify/concorde-agent-assets.json`; shared triage state, modified or
unrelated files, and inactive integration surfaces are preserved.
