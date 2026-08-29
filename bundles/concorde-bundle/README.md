# Concorde Bundle

This integration-agnostic bundle pins `concorde-core@0.3.0` and `concorde@0.3.0` and inherits the
project's active coding-agent integration. It declares no workflow or reusable step.

The preset contributes five architecture-aware templates and nine complete replacements for the
normal Spec Kit 0.16.4 lifecycle commands. The extension contributes five Concorde-specific
surfaces: four operations backed by the selected-workspace adapter and deterministic runtime
(`init`, `context`, `validate`, `feature.harden`), plus one agent-followed `ask` procedure that
reads cited guidance without mutation. Spec Kit resolves and materializes both sets through the
active agent integration; the bundle is only the pinned installation recipe.

The installed Feature Workspace Protocol v6 supports an atomic feature or one level of immediate
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
```

Disabling or reprioritizing a preset changes future template resolution but, in Spec Kit 0.16.4,
does not unregister already materialized command surfaces. Removing the bundle recomposes registered
commands and restores any surviving lower preset layer. Project-authored `.concorde/`, `specs/`, and
`docs/` content is never bundle-owned.
