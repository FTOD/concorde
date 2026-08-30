# Feature Implementation: Install and Set Up Concorde with Spec Kit

**Realization status**: Candidate second milestone, prepared for explicit acceptance on 2026-08-30.

**Selected level**: Top-level feature of `module.concorde`; it has no parent feature.

## Realization Overview

Concorde is delivered through Spec Kit 0.16.4 as three independently versioned, type-qualified
components: `bundle:concorde-bundle@0.5.0`, `preset:concorde@0.5.0`, and
`extension:concorde@0.5.0`. The bundle remains a passive recipe that pins exactly one preset and one
extension. The preset and extension intentionally share the `concorde` ID because Spec Kit resolves
them through separate component types, catalogs, registries, installed directories, and lifecycle
verbs.

The preset contributes six templates, complete instruction modifications for the nine existing Spec
Kit lifecycle commands, and the additive `speckit.fast-loop` command. The extension contributes five
Concorde command surfaces, their launchers and runtime, and Feature 005's canonical reflection-triage
bodies, platform wrappers, shared queue helper, and deterministic projector. The agent assets are
support files rather than a sixth command surface.

Spec Kit remains authoritative for bundle preview, component installation, provenance, command
composition, and active-integration materialization. Because Spec Kit 0.16.4 cannot project arbitrary
custom-agent files, the Concorde installer adds one bounded stage after component installation: it
invokes only the projector from the installed extension, verifies digest ownership, and reports
terminal success only after the native triage skill and roles are verified.

## Module and Feature Collaboration

`module.concorde.distribution` owns release inventory, deterministic archives, catalogs, the passive
bundle recipe, one-command installation, the post-bundle projection transaction, and safe
install/update/remove behavior. `module.concorde.skills` owns the preset commands/templates and the
extension command and canonical agent sources. `module.concorde.scripts` owns the installed runtime,
projection operation, queue helper, and self-host bootstrap. `module.concorde.workspace-files` owns
the installed registries, selected feature state, durable/temporal workspace paths, and the distinction
between generated projection receipts and maintainer-owned reflection state.

Feature 001 remains authoritative for command intent, selected-workspace routing, durable versus
temporal files, validation, fast-loop, and implementation acceptance. Feature 005 owns triage
actions, role boundaries, queue/plan semantics, worktree isolation, and log-status authority.
Feature 003 packages and invokes those capabilities without redefining them. The `publish-release`
sub-feature owns immutable public publication; `one-command-install` owns the accelerator over the
native bundle-plus-projector path; Feature 004 reuses the same installed projector for self-hosting.

`contract.concorde.spec-kit-installation` and `contract.concorde.spec-kit-platform` govern the host
boundary. Feature-local bundle-distribution, installed-command-surface, and ecosystem-explanation
profiles specialize release inventory, native projections, evidence, and lifecycle behavior. The
component and installation-flow diagrams explain the collaboration without changing module
responsibilities or dependency direction.

## Scenario Realization

### Inspect the release

`scripts/release/build-components.py` reads the bundle version as the release authority, checks both
same-ID component pins by collection, and builds deterministic allowlisted preset, extension, and
bundle archives. The extension allowlist includes every canonical reflection asset plus the declared
queue helper. Separate catalogs advertise the type-appropriate archives, digests, compatibility,
repository, and manifest-derived capabilities. `verify-release.py` checks safe membership, digest and
URL agreement, version compatibility, and byte-equivalent rebuilding.

Installer preview initializes a disposable project, installs the candidate bundle there, and invokes
that disposable project's installed `agent-assets preview` operation against the real target. The
target remains byte-identical while the maintainer sees both the expanded component plan and exact
native projection actions: `create`, `unchanged`, `adopt`, `update`, `remove`, `preserve`, or
`conflict`.

### Install into a project

`scripts/install-concorde.py` supports a published release or local checkout while sequencing public
Spec Kit operations. Apply installs or updates the accepted bundle first, then runs the target's
installed projector through preview, sync, and verify. Fresh Claude and Codex targets receive one
native `reflections-triage` skill, one investigator role, one implementer role, shared default config
when absent, and `.specify/concorde-agent-assets.json` path/digest ownership evidence.

Repeated installation is byte-idempotent. Byte-identical manual files may be adopted; modified or
unowned files are preserved as conflicts. Project-authored `.concorde/`, `specs/`, and `docs/`
sources, reflection logs, plans, worktrees, unrelated agent assets, and permission settings are never
projection-owned. Development catalogs are removed before terminal success is printed.

### Verify the installed workflow

Clean-project acceptance builds and serves release artifacts, installs them outside the Concorde
checkout, inventories both type-qualified component records, and executes the selected-workspace
surface matrix. The installed preset routes durable intent to the feature root and temporal review
and delivery artifacts under `attempt/`. The installed extension resolves runtime, queue, canonical
agent bodies, and wrappers only from its installed directory.

Claude Markdown frontmatter and Codex TOML are parsed structurally. Both projections must agree on
the four triage actions and routes, plan states, shared paths, investigator read-only boundary,
implementer worktree boundary, and maintainer-owned merge/log status. They contain no checkout path
or mandatory model pin. Deterministic structural and lifecycle evidence is required; live model
execution remains an experiential smoke test.

Development self-hosting inventories component and projection sources, binds proposals to their
digests, applies through public Spec Kit operations, invokes the same projector, verifies receipts,
and preserves inactive integration surfaces and customized shared state while switching between
Claude and Codex.

### Update, disable, and remove

Spec Kit 0.16.4 keeps already materialized commands when the preset is disabled or reprioritized but
changes future resolution. Compatible update installs the accepted component layer, then reconciles
only receipt-owned matching projections. Removal deletes only solely owned components and
digest-matching projected paths, retains shared components and modified/unowned/inactive files, and
restores the next surviving lower layer for the nine modified normal commands. A projection conflict
or failure produces residual-state evidence and never records false terminal success.

## Durable Implementation Decisions

- **Installed extension as the sole projection source**: installer-local rendering was rejected
  because it would duplicate Feature 005 and could silently diverge from released bytes.
- **Projection as terminal installation work**: component success is necessary but insufficient;
  installation succeeds only after native outputs and their receipt verify.
- **Disposable installed preview**: preview exercises the actual candidate archive and stays
  read-only against the target rather than consulting checkout-local assets.
- **One aligned 0.5.0 release**: bundle, preset, and extension versions advance together so an
  already-current 0.4.0 installation cannot skip new archive members or projections.
- **Explicit release allowlists**: canonical agent assets extend the integrity-covered extension
  inventory without inventing an unsupported Spec Kit manifest field.
- **Digest-scoped ownership**: receipts authorize changes only to matching generated paths; names
  alone never authorize overwriting or deletion.
- **Shared cross-platform state**: Claude and Codex projections use one maintainer-owned
  `.concorde/reflections/` state model and preserve inactive integration records.
- **Structural agent evidence**: parsable metadata, shared semantics, ownership transitions, and
  checkout isolation are deterministic release gates; model output is not.
- **Type-qualified identity retained**: `preset:concorde` and `extension:concorde` remain distinct
  despite their shared ID, and transport filenames include component type.

## Traceability and Evidence

Primary implementation sources:

- `extensions/concorde/agent-assets/reflections/**`
- `extensions/concorde/runtime/concorde/agent_assets.py`
- `extensions/concorde/scripts/python/reflections_queue.py`
- `scripts/install-concorde.py`
- `scripts/development/self-host-concorde.py`
- `scripts/release/build-components.py`
- `bundles/concorde-bundle/bundle.yml`, `presets/concorde/preset.yml`, and
  `extensions/concorde/extension.yml`

Evidence covers manifest/archive membership, release determinism, component and projection preview,
fresh Claude/Codex installation, three-run idempotence, manual parity, conflict refusal, update and
removal, installed command and agent surfaces, self-host integration switching, shared-state
preservation, documentation, and maintained diagrams.

Final evidence on 2026-08-30:

- The release inventory checkpoint passed 11 tests; the combined Feature 003/005 lifecycle suite
  passed 82 tests; focused clean-target acceptance passed six cases.
- The full Concorde Python suite passed 294 tests.
- Concorde validation returned zero findings with source digest
  `sha256:8c0842bd38da77720f3e6cb2b0ce130e984f170010f404a6b79260ec2a06ae4f`.
- The 0.5.0 release rebuilt byte-equivalently: bundle
  `sha256:9a81094801d52fd1c2511400b4ec3b2854a9fde69b6a724583476641c5d243c9`,
  extension `sha256:900044f0d275caa38c8a4bae18a1a85666e0e4aee6356b774004f80c8ea4c307`,
  and preset `sha256:997050c07587028f0e5e45fd7eb3fb249bda58f96cb81c5a9f0de54fe5c04fe4`.
- Docsite gates passed 19 test files and 81 tests, validated 108 pages with zero errors, and promoted
  the production build.
- Both Feature 003 diagrams passed 9/9 showcase checks with zero errors or warnings; their source
  digests are `c6ef046652c3084190f968946fc2dabba7f2009022256fb49aa815e0e9d8a809`
  and `58250e1f90f9b22fd2eaac61dc9727b538090fd0968061a498f3f6aa37ec92f2`.

## Known Limitations

- **R-034**: the identity cutover required a maintainer-authorized terminology-only rewrite of
  append-only reflection history; a general reviewed procedure remains undefined.
- **R-035**: one package identity migration required coordinated referential edits across durable
  feature authorities; Concorde still has no general cross-feature migration operation.
- **R-036**: the failed-update fixture once duplicated a transport filename instead of deriving it
  from release inventory; the fixture is corrected but the improvement remains open.
- **R-037**: the workflow diagram exposed stale repository-evidence pins during the identity/path
  migration; its evidence is refreshed, while the recorded tooling improvement remains open.
- **R-038**: the self-hosting diagram exposed the same evidence-pin weakness and remains an open
  tooling lesson despite corrected evidence.
- **R-046**: installer acceptance requires loopback catalog permission unavailable in the default
  sandbox; the unchanged approved rerun passed.
- **R-047**: a docsite fixture duplicated Feature 005's former title; only the stale expectation was
  corrected, while deriving labels from maintained identity remains open.
- Browser-based containment and light/dark perceptual review remains pending because Chrome/Chromium
  was unavailable; deterministic showcase checks are not claimed as visual review (R-026).
- Compatibility remains limited to Spec Kit `>=0.16.4,<0.16.5`.
- Public release hosting and a first-time remote installation timing proof remain owned by the
  `publish-release` and `one-command-install` sub-features; this milestone builds and verifies 0.5.0
  artifacts but does not claim those pending outcomes complete.

## Implementation Detail

### Installer transaction

Preview and apply consume the same resolved release. Projection subprocess results are parsed as
structured envelopes and attached to the install result. Stage-specific failure retains component
and projection facts, reports exit class 4, and suppresses terminal success. Local development uses
temporary `concorde-dev` catalog registrations that are removed through public Spec Kit commands.

### Release and projection inventory

The release builder distinguishes allowlists by component kind and packages the complete canonical
agent-assets manifest, bodies, wrappers, templates, projector runtime, and declared queue helper.
Archive safety and capability counts are verified against manifests. The projector validates safe
paths, rejects symlinks and malformed sources/receipts, and keeps independent integration records.

### Self-hosting

Self-host proposals include source, installed, registry, command-surface, and agent-projection
dimensions. Apply and status use the same installed projector and receipt rules as consumer
installation, so refreshing one active integration preserves the other integration's generated
files and all maintainer-owned reflection state.
