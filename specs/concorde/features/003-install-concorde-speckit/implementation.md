# Feature Implementation: Install Concorde with Spec Kit

**Realization status**: Reviewed realization proposed for permanent acceptance.

## Realization Overview

Concorde is delivered through Spec Kit's native component lifecycle as three independently identifiable release units. The passive `concorde-bundle@0.1.0` bundle pins the tested `concorde-core@0.1.0` preset and `concorde@0.1.0` extension; it contains no executable workflow or reusable steps. Spec Kit remains the host that resolves trust and compatibility, previews the expanded plan, installs the components, records provenance, and materializes commands through the target project's active coding-agent integration.

The preset changes the existing Spec Kit feature lifecycle. It contributes three append-composed guidance templates, one replacement template for permanent `design.md`, and complete replacement layers for the nine path-sensitive normal commands. The extension contributes five Concorde-specific commands (four runtime-backed operations plus the agent-followed `ask` procedure) together with platform launchers, the selected-workspace adapter, and the deterministic Concorde runtime. Catalogs advertise these packages and their integrity metadata but are not installed runtime components.

Release archives are built from explicit allowlists with stable member ordering, permissions, timestamps, versions, URLs, and SHA-256 digests. The supplied base URL is serialized into catalog metadata and is not contacted during a build. A release is accepted only from built artifacts installed into checkout-isolated projects, so repository-local `.agents/` and `.specify/` content cannot masquerade as distributed functionality.

## Module and Feature Collaboration

This root feature is realized by existing module-level refinements rather than redefining their architecture. `feature.distribution.package-concorde-bundle` supplies the reproducible archives, catalogs, exact component plan, provenance, and install/update/remove lifecycle governed by the Distribution module's bundle and component-package contracts. `feature.integration.compose-concorde-workflow` supplies the preset and extension composition governed by the Spec Kit Integration module's workflow-composition, agent-skills, and Spec Kit platform contracts.

Feature 001's `feature.integration.manage-feature-workspace` remains authoritative for nested feature selection, durable and temporal paths, command intent, result envelopes, and hardening semantics. Feature 003 packages that handoff and proves it from installed artifacts; it does not redefine the workflow. Architecture Core performs initialization, bounded context, and validation after an installed command invokes it. Feature 002 publishes the declared Feature 003 diagrams and prose without becoming behavioral authority.

The stable package interaction is explained by `diagrams/spec-kit-component-model.json`, while `diagrams/bundle-installation-flow.json` supplements it with release-to-use order. The canonical one-level project architecture remains `specs/concorde/architecture.json`, and module responsibilities and contracts remain in their respective module specifications.

## Scenario Realization

### Inspect the installation

The release builder produces separate preset, extension, and bundle archives plus matching catalogs. Spec Kit resolves an approved catalog, directory, manifest, or archive source into one expanded plan. The preview exposes the bundle recipe, exact preset and extension versions, compatibility range, source trust, preset priority and strategies, inherited integration, and planned mutations before the maintainer accepts installation.

### Install into a project

Spec Kit validates the accepted plan, installs the pinned components, and materializes their winning command layers through the active integration. The preset provides four templates and replaces `specify`, `clarify`, `checklist`, `plan`, `tasks`, `implement`, `analyze`, `converge`, and `taskstoissues`. The extension registers `init`, `feature-harden`, `context`, `validate`, and the agent-only `ask`. Repeated installation converges on one bundle, preset, and extension record without changing project-authored `.concorde/`, `specs/`, or `docs/` sources.

### Execute the installed workflow

Every normal command invokes the extension-installed workspace adapter before path-sensitive work. `specify` and `clarify` use root `spec.md` and durable contracts while placing generated review state in `implementation/checklists/`; `checklist` uses that same temporal checklist directory. Planning, task generation, implementation, analysis, convergence, and issue conversion use the selected feature's single `implementation/` workspace and read root `design.md` as immutable accepted context. No root plan, task, checklist compatibility copy, alias, or symlink is created.

The four runtime-backed extension commands resolve their launchers and runtime relative to the installed extension. Their canonical intent and results are presentation-neutral: Spec Kit may render Codex skills or Gemini slash commands, but the workspace paths, operations, failures, and Architecture Core handoff remain equivalent. Completed attempts may be hardened only by a digest-bound proposal after all tasks and checklist items are complete and the exact design replacement and implementation-directory deletion receive explicit approval.

### Update, disable, or remove Concorde

Spec Kit owns lifecycle state. On Spec Kit 0.16.4, disabling or reprioritizing the preset changes future resolution while preserving already registered command artifacts. Compatible update materializes the accepted new layer. Removing the bundle removes solely owned components, retains shared components and project sources, and restores the next surviving lower command layer for all nine normal surfaces. Failures do not create false success records; rollback retains the prior successful state when possible and reports residual state otherwise.

## Durable Implementation Decisions

- Concorde uses one native Spec Kit bundle as an inspectable recipe; it has no separate installer, dedicated workflow component, or reusable steps.
- Bundle, preset, and extension versions are independent and pinned exactly in the tested bundle recipe. Initial compatibility is `>=0.16.4,<0.16.5`.
- The preset contains three append template layers, one replacement `design-template`, and nine complete command replacements. Replacement is required because selected-workspace routing must precede every legacy path assumption.
- The extension contains five Concorde commands (four runtime-backed plus `ask`), four platform/runtime entry scripts, and all declared runtime dependencies. Installed commands may not fall back to the Concorde source checkout.
- Feature 001 owns command and workspace semantics. Feature 003 owns package composition, materialization, provenance, and lifecycle proof and binds installed surfaces to the packaged handoff digest.
- Durable specification, accepted design, contracts, and diagrams remain at the feature root. Checklists and all other current-attempt artifacts remain under the single temporal `implementation/` directory until approved hardening removes it.
- Catalog entries and release archives are reproducible projections of maintained manifests and sources. Catalog capability counts must equal the actual component manifests, and catalog archive digests must match deterministic builds.
- The target project's active coding-agent integration owns presentation syntax only. Canonical command identity, arguments, paths, results, and failures remain integration-independent.
- Preview/install parity, trust and compatibility checks, idempotency, source preservation, rollback, shared-component retention, and lower-layer restoration are required lifecycle properties.
- The feature's core diagram explains stable package and runtime interaction; its supplemental workflow explains release, installation, use, and recomposition. Neither replaces module architecture or textual contracts.

## Traceability and Evidence

The durable behavioral authority is `spec.md` together with `contracts/bundle-distribution.md`, `contracts/installed-command-surfaces.md`, and `contracts/ecosystem-explanation.md`. Package identity and content are maintained in `bundles/concorde-bundle/bundle.yml`, `presets/concorde-core/preset.yml`, and `extensions/concorde/extension.yml`; deterministic release and catalog generation are implemented by `scripts/release/build-components.py` and checked by `scripts/release/verify-release.py`.

Manifest and archive contracts verify the exact two-component recipe, four preset templates, nine normal replacements, five extension commands, archive allowlists, catalog capability counts, reproducibility, and handoff content. Clean-install contract, integration, and acceptance tests install built archives through served catalogs into isolated Codex-skills and Gemini-slash projects, inventory all thirteen runtime-backed materialized surfaces, execute the selected-workspace bootstrap, compare repeated phase receipts, and reject checkout fallback. Lifecycle tests cover supported source forms, preview/install parity, idempotency, compatible update, failed update, shared ownership, project-source preservation, Spec Kit's persistent registration semantics, and restoration of all nine lower command layers.

The two maintained Archify sources pass all nine Archify 2.16 showcase checks with zero errors or warnings and their generated projections provide deterministic component and workflow evidence, while the documentation publication tests verify declaration-driven embedding. Generated catalogs, archives, diagrams, and receipts remain evidence and projections rather than maintained behavioral authority.

## Known Limitations

- The initial compatibility window is intentionally limited to Spec Kit 0.16.4. Every additional host version requires reviewing all nine replacement commands against the corresponding upstream command responsibilities and rerunning clean-install and recomposition acceptance.
- Presentation equivalence is currently verified for Codex skills and Gemini slash commands. Other Spec Kit integrations require the same installed-surface and result-equivalence evidence before being claimed as supported.
- The release builder produces archives and catalog metadata but does not operate a public catalog host or upload release assets; publication transport is a separate release operation.
- Disable and priority changes retain already registered commands because that is Spec Kit 0.16.4 behavior; maintainers must use update or removal when they need command artifacts to be rematerialized immediately.
