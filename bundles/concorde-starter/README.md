# Concorde Starter bundle

This integration-agnostic bundle pins `concorde-core@0.1.0` and `concorde@0.1.0` and inherits the
project's active coding-agent integration. It declares no workflow or reusable step.

The preset contributes three append-only architecture templates and nine complete replacements for
the normal Spec Kit 0.16.4 lifecycle commands. The extension contributes seven Concorde-specific
surfaces: six operations backed by the selected-workspace adapter or deterministic runtime, plus one
agent-followed `ask` procedure that reads cited guidance without mutation. Spec Kit resolves and
materializes both sets through the active agent integration; the bundle is only the pinned
installation recipe.

Before installation, register the Concorde preset and extension catalogs as reviewed,
install-allowed sources. Release catalogs use HTTPS artifact URLs; the localhost HTTP catalogs
created by `scripts/release/build-components.py --base-url http://127.0.0.1:8765` are acceptance-only.

```bash
specify bundle validate --path bundles/concorde-starter
specify bundle build --path bundles/concorde-starter --output dist
specify bundle info concorde-starter --json
specify bundle install concorde-starter
```

Disabling or reprioritizing a preset changes future template resolution but, in Spec Kit 0.16.4,
does not unregister already materialized command surfaces. Removing the bundle recomposes registered
commands and restores any surviving lower preset layer. Project-authored `.concorde/`, `specs/`, and
`docs/` content is never bundle-owned.
