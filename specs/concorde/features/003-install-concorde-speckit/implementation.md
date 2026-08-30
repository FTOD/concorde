# Feature Implementation: Install and Set Up Concorde with Spec Kit

**Realization status**: Current verified realization proposed for durable acceptance.

## Realization Overview

Concorde is delivered through Spec Kit 0.16.4 as three independently versioned, type-qualified
components: `bundle:concorde-bundle@0.4.0`, `preset:concorde@0.4.0`, and
`extension:concorde@0.4.0`. The bundle is a passive recipe that pins exactly one preset and one
extension. The preset and extension intentionally share the `concorde` ID because Spec Kit resolves
them through separate component types, catalogs, registries, installed directories, and lifecycle
verbs.

The preset contributes six templates, complete instruction modifications for the nine existing Spec
Kit lifecycle commands, and the additive `speckit.fast-loop` command. User-facing guidance describes
the normal commands as modified by Concorde: their names, lifecycle roles, and expected use remain
Spec Kit's. The manifest entries use `strategy: replace` only so the selected-workspace gate runs
before any inherited flat-path assumption. The extension contributes five Concorde-specific
surfaces—four deterministic runtime-backed operations plus the agent-followed, read-only `ask`
procedure—and includes their launchers, selected-workspace adapter, schemas, and Python runtime.

Release construction emits three distinct transport assets:
`concorde-preset-<version>.zip`, `concorde-extension-<version>.zip`, and
`concorde-bundle-<version>.zip`. Each archive retains its manifest identity independently of its
filename. Separate preset, extension, and bundle catalogs advertise the type-appropriate archive,
digest, compatibility range, repository, and capabilities. No compatibility alias or duplicate
preset identity is installed.

## Module and Feature Collaboration

`module.concorde.distribution` owns the bundle recipe, type-specific catalogs, deterministic archives,
release verification and publication helpers, one-command installer, provenance, and safe
install/update/remove behavior. `module.concorde.skills` owns the preset command/template sources and
the extension command definitions materialized by the active coding-agent integration.
`module.concorde.scripts` owns the self-host bootstrap and the installed selected-workspace/runtime
operations. `module.concorde.workspace-files` supplies the separate preset and extension registries,
installed component directories, selected feature state, and durable/temporal paths.
`module.concorde.auto-docs` publishes the maintained package explanation and declared diagrams as a
generated read model.

Feature 001 remains authoritative for command intent, selected-workspace routing, durable versus
temporal files, validation, and implementation acceptance. Feature 003 packages that handoff and
proves it from installed artifacts; it does not define a second workflow. The `publish-release`
sub-feature owns immutable public release publication, and `one-command-install` owns the optional
accelerator that sequences public Spec Kit initialization, catalog registration, and bundle
installation. Feature 004 reuses the same component lifecycle to materialize and verify the current
checkout.

The stable package interaction is explained by `diagrams/spec-kit-component-model.json`; the
release-to-use order is explained by `diagrams/bundle-installation-flow.json`. The root and module
level views remain the authority for module responsibility and dependency direction.

## Scenario Realization

### Inspect the release

`scripts/release/build-components.py` reads the bundle version as the release authority, checks both
same-ID component pins by collection, verifies manifest versions, compatibility, and repository
metadata, and builds deterministic allowlisted ZIP archives. It writes three catalogs whose keys and
IDs are `concorde` in their separate preset/extension collections and `concorde-bundle` in the bundle
collection. `scripts/release/verify-release.py` checks archive safety, digest and URL agreement,
capability metadata, version/repository compatibility, and byte-equivalent rebuilds.

`scripts/release/publish-release.py` publishes the three archives, three catalogs, and deterministic
`release.json` pointer through a reviewable draft-first decision table. A missing release can be
created; a leftover draft can be repaired; an identical published release is a no-op; a divergent
published release is refused rather than overwritten.

### Install into a project

Spec Kit previews `concorde-bundle`, showing `preset:concorde` and `extension:concorde` independently
with their versions, trust, priority/strategy, compatibility, provenance, and intended effects. It
then installs each component through its native type-specific lifecycle and materializes the winning
normal and Concorde-specific command surfaces through the target project's active integration.

`scripts/install-concorde.py` supports a published release or local checkout while still using public
Spec Kit operations. Its development catalogs are temporary, installation is idempotent, a
conflicting requested integration stops before mutation, and terminal success is printed only after
mandatory cleanup succeeds. Repeated installation preserves project-authored `.concorde/`, `specs/`,
and `docs/` sources.

### Verify the installed workflow

Clean-project acceptance builds and serves release artifacts, installs them outside the Concorde
checkout, inventories both type-qualified component records, and executes the selected-workspace
surface matrix. The installed preset routes durable specification work to the feature root and
review/planning/delivery state under `attempt/`; no root-level compatibility copy or symlink is
created. The installed extension resolves launchers and runtime only from its installed directory.
Codex and Claude materializations carry `source: preset:concorde` for the preset commands and retain
equivalent command intent.

Development self-hosting models component identity as `(kind, id)`, validates the preset and
extension pins separately inside the bundle, binds proposals to a deterministic source inventory,
uses public Spec Kit add/remove operations, verifies installed bytes and registries, and restores
scoped state on failure. The final Codex cycle reached `current`; the active Claude integration was
then rematerialized through the public lifecycle.

### Update, disable, and remove

Spec Kit 0.16.4 keeps already materialized commands when the preset is disabled or reprioritized but
changes future resolution. Update installs the accepted new component layer. Bundle removal deletes
only solely owned components, retains a preset shared with another bundle, preserves project sources,
and restores the next surviving lower layer for the nine modified normal commands. The additive
fast-loop surface is removed when solely owned. Failed update and injected self-host failures never
record false success and preserve or report exact residual state.

## Durable Implementation Decisions

- Component identity is the ordered pair `(kind, id)`. `preset:concorde` and
  `extension:concorde` are intentionally distinct even though their IDs match.
- Maintained sources live at `presets/concorde/`, `extensions/concorde/`, and
  `bundles/concorde-bundle/`; installed copies live under the corresponding type-specific
  `.specify/` directories.
- Transport filenames include component type to prevent a same-directory collision, while catalog
  and manifest IDs remain `concorde`.
- The preset modifies existing Spec Kit commands; it does not deprecate them or introduce parallel
  command IDs. Complete `strategy: replace` layers are an installation-order mechanism.
- The rename is a pre-release cutover with no alias, dual registration, or in-place public migration.
  Development installations are rematerialized from the renamed sources.
- The repository-wide invariant covers live paths and content—including installed skills, catalogs,
  fixtures, specifications, reflections, diagrams, and generated release evidence—while Git history
  is intentionally not rewritten.
- Release archives are deterministic projections of maintained sources. Catalog capability counts
  agree with manifests, and catalog digests agree with the built archives.
- Passing text-presence checks are insufficient: clean-project tests execute winning surfaces with
  the source checkout unavailable.
- The explicit maintainer directive authorized the terminology-only reconciliation of historical
  reflection text and referential durable sources while preserving their behavior and meaning
  (R-034, R-035).

## Traceability and Evidence

Behavioral authority is `design.md`, with feature-local profiles in
`contracts/bundle-distribution.md`, `contracts/installed-command-surfaces.md`, and
`contracts/ecosystem-explanation.md`, plus root
`contract.concorde.spec-kit-installation`. Package identity is maintained in
`presets/concorde/preset.yml`, `extensions/concorde/extension.yml`, and
`bundles/concorde-bundle/bundle.yml`. Release behavior is implemented by
`scripts/release/{build-components,verify-release,publish-release}.py`; local installation and
self-hosting are implemented by `scripts/install-concorde.py` and
`scripts/development/self-host-concorde.py`.

The final executable evidence is:

- 261 Python tests passed across unit, contract, integration, and acceptance suites, including the
  zero-token path/content contract and same-ID/type-qualified bundle-pin regression.
- `speckit.concorde.validate` completed with source digest
  `sha256:551326acb6043f4067e4650549013f7ab0c55d23ebeb55e07f3facddd6f791c5`
  and zero findings.
- Release build and byte-equivalent verification produced bundle digest
  `sha256:85e594183e914ac06511e7eac0c5afc0d3be591ffd8946e095d54b43efcb3436`,
  extension digest `sha256:db32fe78ceb6a675c2dc1596db676acdba87256f5ad4053f8ba2864f281682f4`,
  and preset digest `sha256:e80ffe89e8f9aecf42e3f5f3d9a1dd040025eb47a6e72dda770f2ef4164f6af6`.
- Documentation validation covered 108 pages with 32 excluded sources and zero errors; all 19
  Vitest files and 81 tests passed; the optimized production build was promoted successfully.
- Feature 003, parent workflow, and self-hosting component diagrams each passed 9/9 Archify showcase
  validation and delivery with zero errors or warnings. Their generated HTML remains evidence, not
  authority.
- Codex self-host propose/apply/status reached `current` with matching source, installed, registry,
  and surface dimensions before the active integration was restored to Claude and both integrations'
  surfaces were refreshed.

## Known Limitations

- R-034 remains open: the global identity invariant required a maintainer-authorized terminology-only
  rewrite of append-only reflection history. A general reviewed procedure for such migrations is not
  yet defined.
- R-035 remains open: one root-owned package identity migration required referential updates across
  durable sources owned by several features. Concorde has no general coordinated cross-feature
  migration operation.
- R-036 remains open: the failed-update fixture originally duplicated a transport filename instead
  of deriving it from the release inventory; the fixture is corrected, but the improvement remains
  recorded.
- R-037 remains open: the parent workflow diagram needed its repository-evidence revision and source
  references refreshed after the path migration.
- R-038 remains open: the self-hosting diagram exposed the same evidence-pin migration requirement
  during the documentation build.
- Self-host protocol v1 still reports `unknown` for the active Claude integration even after its
  surfaces are rematerialized; the established limitation is recorded by R-001.
- Browser-based containment and light/dark perceptual review remain pending because Chrome/Chromium
  is unavailable; deterministic showcase delivery passed, but it does not establish visual polish
  (R-026).
- Compatibility remains limited to Spec Kit `>=0.16.4,<0.16.5`; every broader range needs the full
  installed-surface and lifecycle matrices.
- Public release hosting and the first-time installation timing proof remain owned by the
  `publish-release` and `one-command-install` sub-features; this realization builds and verifies the
  artifacts but does not claim those pending outcomes complete.

## Implementation Detail

`scripts/release/build-components.py` distinguishes archive allowlists by component kind so the
same component ID cannot select the wrong content. `scripts/development/self-host-concorde.py`
validates each same-ID bundle pin inside its collection and normalizes the two registries separately.
`tests/concorde/contract/test_preset_identity.py` constructs the retired token at runtime so the test
can enforce its absence without retaining it in tracked source. Installed Codex and Claude
projections and `.specify/presets/.registry` identify the preset as `concorde`; the extension registry
independently identifies the extension as `concorde`.
