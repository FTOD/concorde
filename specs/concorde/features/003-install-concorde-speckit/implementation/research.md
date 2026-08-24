# Phase 0 Research: Concorde Spec Kit Distribution

**Feature**: `feature.concorde.install-with-spec-kit`  
**Date**: 2026-08-22  
**Scope**: Make release-installed command surfaces match the Concorde workflow in a clean project

## Decision 1: Split workflow authority from distribution authority

**Decision**: Feature 001 owns workspace layout, phase-path meaning, command intent, architecture
services, and failures. Feature 003 owns preset/extension manifests, command composition strategy,
registration, release/catalog lifecycle, agent presentation, and clean installed evidence. Every
release receipt records the Feature 001 handoff version and digest it implements.

**Rationale**: The workflow must have one semantic authority while distribution remains independently
testable and replaceable. A digest prevents a clean install from being reported verified after the
workspace contract changes.

**Alternatives considered**:

- Duplicating phase rules in both features was rejected because they would drift.
- Moving package lifecycle into Feature 001 was rejected because Distribution and Integration
  already own those boundaries.

## Decision 2: Keep the bundle a passive pinned recipe

**Decision**: `concorde-starter` continues to pin one `concorde-core` preset and one `concorde`
extension. Spec Kit resolves and installs each component through its native manager and records
ownership/provenance.

**Rationale**: This preserves preview, update, shared-component, and safe removal behavior without a
second Concorde installer.

**Alternatives considered**:

- Embedding component files in the bundle was rejected because it bypasses native component
  lifecycle and provenance.
- A Spec Kit workflow component or reusable steps remain unnecessary for the initial release.

## Decision 3: Use `replace` for all nine affected core commands

**Decision**: Keep the three inherited template entries `append`, add the Concorde-only permanent
design template as `replace`, and make all nine existing-command entries authoritative `replace`
layers. Each command replacement preserves its Spec Kit phase responsibility and
invokes the installed Feature 001 workspace adapter before any path-sensitive setup, prerequisite,
or artifact read/write.

**Rationale**: The clean-project audit showed that an appended Concorde addendum appears after the
stock command has already invoked helpers that choose root-level plan/task paths. `prepend` or `wrap`
cannot reliably suppress that incompatible step. Spec Kit 0.16.4 explicitly supports preset command
replacement and registers the winning content through `CommandRegistrar`.

**Alternatives considered**:

- `append` was rejected because corrective instructions arrive too late.
- `prepend` was rejected because the unchanged lower command can still re-resolve legacy paths.
- `wrap` was rejected because `{CORE_TEMPLATE}` preserves the incompatible core step.
- Direct replacement of `.specify/scripts/` was rejected: preset script delivery is marked reserved
  for future use and installer patching would be an unsupported fork.
- New Concorde-prefixed duplicates of normal phases were rejected because Spec Kit must retain its
  canonical lifecycle surface.

## Decision 4: Lock replacement semantics to Spec Kit 0.16.4

**Decision**: Maintain a compatibility map from each replacement to the canonical 0.16.4 command's
purpose, inputs, outputs, hooks, and failure gates. Supporting another Spec Kit version requires an
explicit review and acceptance run for all nine replacements before widening manifests/catalogs.

**Rationale**: Full replacement necessarily owns the complete prompt surface. A narrow supported
range makes divergence visible rather than silently claiming compatibility.

**Alternatives considered**:

- Byte-copying upstream commands and applying unreviewed search/replace was rejected as brittle.
- Advertising a broad range based on manifest parsing alone was rejected because command semantics
  can change without package schema changes.

## Decision 5: Package six Concorde-specific commands in the extension

**Decision**: The extension contains init, feature create, feature select, feature harden, context, and validate
commands plus every launcher, workspace adapter, and runtime file they reference. All paths resolve
from the installed extension root.

**Rationale**: These are new capabilities with deterministic runtime behavior, which is the extension
boundary. The preset should modify normal workflow instructions but own no runtime.

**Alternatives considered**:

- Putting the six commands in the preset was rejected because they introduce active capabilities.
- Depending on repository-local Python imports was rejected because a user project does not contain
  the source checkout.

## Decision 6: Treat the active integration as a materializer, not an authority

**Decision**: Spec Kit resolves the winning command layer, then renders it into the active
integration's Markdown, skill, TOML, or companion format. Acceptance records both the canonical
source package and materialized artifact hash, while comparing behavior to Feature 001 contracts.

**Rationale**: Agent-specific syntax can vary without changing command meaning. Tracking the winner
prevents a matching but inactive file from being mistaken for the executed command.

**Alternatives considered**:

- Validating only preset source files was rejected because registration or precedence can select
  another layer.
- Treating agent filenames as canonical IDs was rejected because integrations encode names
  differently.

## Decision 7: Define an executable installed-command-surface receipt

**Decision**: For each of the 14 installed surfaces, acceptance resolves the actual winning artifact,
binds it to package and handoff digests, executes its installed workspace/bootstrap entry point, and
records the resulting phase root, output paths, exit status, and source-access audit. Full skills and
slash-command scenario runs complement this deterministic bootstrap receipt.

**Rationale**: String presence proves neither precedence nor behavior. The machine-executable
workspace bootstrap is the path-critical portion common to every presentation and can be validated
without an LLM; agent scenario evidence then checks orchestration/presentation parity separately.

**Alternatives considered**:

- Grepping for `workspace.implementation_dir` was rejected as insufficient.
- Requiring an LLM for deterministic path validation was rejected by the constitution.
- Invoking only the runtime directly was rejected because it would not prove that the registered
  winning command points to that runtime before other path-sensitive work.

## Decision 8: Isolate clean targets from the source checkout

**Decision**: Build archives first, then create targets outside the repository with sanitized Python
and command search paths. Install only through served catalogs/built artifacts. Audit file reads and
remove individual archive members in negative fixtures.

**Rationale**: The existing repository contains modified `.agents/`, `.specify/`, templates, and
runtime sources that can mask missing release content.

**Alternatives considered**:

- Installing a development directory with `--dev` was retained for component-author debugging only,
  never product acceptance.
- Running tests inside the checkout was rejected for clean-install parity.

## Decision 9: Preserve reproducible independent release units

**Decision**: Build preset, extension, and bundle archives independently from explicit allowlists;
generate catalogs from their manifests and digests; then verify two builds byte-for-byte. `--base-url`
is serialized into catalog download locations and is not contacted while building.

**Rationale**: Independent versions and digests let Spec Kit resolve, trust, update, share, and remove
components correctly.

**Alternatives considered**:

- Committing generated archives as maintained intent was rejected.
- Requiring the future public URL to be live during a local build was rejected because it confuses
  metadata with transport.

## Decision 10: Verify recomposition, not only removal of files

**Decision**: Install a lower-priority fixture layer, then exercise preset enable/disable, priority
change, compatible update, and removal. Spec Kit 0.16.4 explicitly keeps registered commands active
across enable/disable and priority changes, so those transitions must preserve the current nine
materialized winners while changing future resolution. Update and removal must rematerialize the
accepted updated layer or the next surviving lower layer for all nine commands.

**Rationale**: This follows the public host lifecycle instead of inventing eager recomposition that
the host does not provide. Safe update/removal still requires restoration of the correct winner;
deleting Concorde-owned files without rematerializing lower content can leave commands missing or stale.

**Alternatives considered**:

- Checking only preset registry state was rejected because registered agent artifacts can disagree.
- Testing one representative command was rejected because the nine surfaces have different phase
  paths and integration renderings.

## Decision 11: Keep automated and human evidence separate

**Decision**: Automated tests own package parity, command inventory, phase paths, isolation,
recomposition, rollback, determinism, and source preservation. First-time installation time and
ecosystem-role comprehension remain human pilot evidence.

**Rationale**: Tests cannot prove that a new maintainer understands bundle/preset/extension/catalog
roles or completes setup without assistance.

**Alternatives considered**:

- Inferring human outcomes from passing docs/tests was rejected.
- Making human review a prerequisite for deterministic release hashes was rejected.

## Decision 12: Maintain one core and one supplemental Feature 003 diagram

**Decision**: Keep the component model as the feature's single `role: core` Archify architecture view
for ownership and stable composition, and keep the installation flow as a `role: supplemental`
workflow for release-to-clean-use order. Both remain declared under `diagrams/`, text-backed,
showcase validated, delivered with provenance, and automatically embedded by the existing docsite.

**Rationale**: Package roles and temporal installation/use are different questions. Combining them
into root `architecture.json` would overload the bounded module view.

**Alternatives considered**:

- Prose only was rejected because the package and invocation split is materially visual.
- Diagrams only were rejected because behavior and contracts need searchable accessible authority.

## Decision 13: Route checklist state through the temporal implementation workspace

**Decision**: The installed `specify` and `clarify` replacements resolve root `spec.md`, `design.md`,
and durable contracts but write generated requirements-quality state only below
`implementation/checklists/`. The installed `checklist` replacement also targets that temporal
directory. No command creates a root checklist alias, copy, or symlink.

**Rationale**: A checklist records readiness for the current review or delivery attempt; it is not
permanent feature intent. Routing every checklist through the same attempt preserves the authority
split and gives hardening one deterministic location in which to verify that all review items are
resolved before removing the attempt.

**Alternatives considered**:

- Keep root checklists as durable feature content: rejected because checked state belongs to one
  implementation/review cycle and would outlive the conclusions it was evaluating.
- Maintain a root compatibility link: rejected because it creates a second observable path and makes
  clean-project routing evidence ambiguous.

## Unknowns Resolved

- Feature 001 owns semantic handoff; Feature 003 owns installed materialization and lifecycle.
- Three inherited templates remain append-composed, the permanent design template is replaced, and
  all nine affected normal commands use replacement.
- Core scripts are not replaced or patched by the bundle.
- The extension archive contains all six commands—including task-complete, approval-gated
  hardening—plus the workspace adapter, launchers, and runtime.
- Clean-install evidence is built-artifact based, checkout-isolated, and executes the winning surface's
  bootstrap rather than matching snippets.
- Initial compatibility remains exactly Spec Kit 0.16.4.
- The component model is core, the installation flow is supplemental, and both are declaration-published.
- Every installed checklist-producing surface writes only below `implementation/checklists/`.
- All planning questions are resolved.
