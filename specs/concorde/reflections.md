# Reflections: Concorde

The project's one reflection log: every difficulty or problem a coding agent met while planning or
implementing any feature, attributed to the feature being worked on and naming the source the
problem concerns. Grammar:
[reflection-log contract](features/005-record-workflow-reflections/contracts/reflection-log.md).
Kept by hand under constitution B.II until the rule Feature 005 specifies is installed.

### R-001 · Self-hosting cannot refresh the Claude integration used by this checkout

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: tooling
- **Concerns**: feature.concorde.self-host-framework
- **Expected**: `scripts/development/self-host-concorde.py status` reports the freshness of this
  checkout's installed Concorde surfaces so a framework change can be refreshed and counted as used.
- **Observed**: Status returns `unknown` with `CONCORDE-SELF-HOST-005: Integration 'claude' has no
  self-hosting surface evidence in protocol v1`; `.specify/integration.json` selects `claude`.
- **Effect**: worked-around
- **Action**: Planned the refresh through Spec Kit's public development-mode install plus the
  installed-surface byte-equality test (Feature 005 research D7) instead of the self-hosting tool.
- **Improvement**: Extend Feature 004's surface evidence and drift check to the Claude integration.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-28 feature.concorde.record-workflow-reflections — refreshed the mirrors with
    `specify preset remove concorde-core` + `specify preset add --dev … --priority 10` and
    `specify extension add … --dev --force` (plain `preset add` refuses an installed preset); byte
    equality proven by `diff -r` and `test_installed_command_surfaces`; a new agent session is
    still required before the refreshed skills are active.

### R-002 · Plan and tasks guidance disagree on whether an attempt may edit `module.md`

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: guidance
- **Concerns**: presets/concorde-core/templates/tasks-template.md
- **Expected**: One rule for module-summary edits during an attempt.
- **Observed**: The tasks append layer says to include tasks that update "module registrations" and
  the "current-level Archify JSON", and also says not to generate a task that edits "any module
  `module.md`"; the plan append layer forbids editing `abstract.md`, `design.md`, the feature
  `design.md`, and a module `design.md` but not `module.md`.
- **Effect**: assumed
- **Action**: Planned the `architecture.json` change as an implementation task and the `module.md`
  prose reconciliation as a maintainer-approved edit presented before it is applied (research D8).
- **Improvement**: State in both append layers that a level view and a module summary may change
  inside an attempt only as a reviewed architecture change presented for approval.
- **Status**: open

### R-003 · The specification contradicted the root view once the maintainer's request landed

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: specification
- **Concerns**: specs/concorde/features/005-record-workflow-reflections/design.md#concorde-architecture-alignment
- **Expected**: The alignment section describes the root view's relationship to the feature
  durably.
- **Observed**: It stated the root view "is not amended by this specification; drawing this feature
  in the root view is planned work", which becomes false when research D8 adds the node, and an
  attempt may not edit `design.md`.
- **Effect**: deferred
- **Action**: Left `design.md` unchanged during planning; the 2026-08-28 specification revision
  (R-004) reworded the bullet to "the root view shows this feature as a root feature node".
- **Improvement**: Keep alignment prose descriptive of the intended end state, not of pending work.
- **Status**: resolved
- **Note**: Resolved on 2026-08-28 by the specification revision that accompanied R-004; the
  `module.md` "not yet drawn" sentence is still reconciled by task T036.

### R-004 · A per-attempt log could not hold problems about other features' implementations

- **Phase**: plan
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: specification
- **Concerns**: specs/concorde/features/005-record-workflow-reflections/design.md#functional-requirements
- **Expected**: FR-003 placed the reflection log inside each attempt's `attempt/`
  directory, removed at hardening with a per-entry disposition.
- **Observed**: The maintainer pointed out that problems met while implementing a feature usually
  concern existing implementations, often of other features; a per-attempt file scatters the same
  problem across roots and deletes it with the attempt.
- **Effect**: worked-around
- **Action**: Revised the specification, abstract, plan, research, data model, contract, quickstart,
  and tasks on 2026-08-28: one project-wide log at the specification root, entries attributed to
  the selected feature with a free `Concerns` target, no removal at hardening, and a citation rule
  instead of dispositions; moved this attempt's entries here.
- **Improvement**: When a record serves cross-feature review, specify it at the level where all
  the things it can concern are visible (the root), not at the feature.
- **Status**: resolved
- **Note**: Resolved by the 2026-08-28 revision of Feature 005 (design.md "Revised" line).

### R-005 · The root view cannot draw the feature's crossing into Spec Kit Integration

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: architecture
- **Concerns**: specs/concorde/architecture/diagrams/level-view.json
- **Expected**: Research D8 planned three governed crossings for the new root feature node: from
  the coding agent, into Spec Kit Integration (guidance and log path), and into Architecture Core.
- **Observed**: With Architecture Core placed between the feature column and Spec Kit Integration,
  every route from the new node up to Integration crosses the existing workflow → Architecture Core
  edge or the Integration → Core corridor; Archify showcase validation reports proper crossings and
  ambiguous corridors for each variant tried.
- **Effect**: worked-around
- **Action**: Drew two crossings (agent → feature over `contract.concorde.workflow`, feature →
  Architecture Core over `contract.core.architecture-services`) and stated Integration's guidance
  role in the feature's sublabel and the root card; the feature's own core diagram shows all parts.
- **Improvement**: Reconsider the root view's column order (features, then Integration, then Core)
  or allow Archify to route around the right edge so both realizing modules can be drawn.
- **Status**: open

### R-006 · Analysis is specified as strictly read-only but must record problems

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: specification
- **Concerns**: feature.concorde.workflow.execute-and-reconcile
- **Expected**: FR-001 of this feature requires recording through the analysis phase, while FR-004
  of the execute-and-reconcile sub-feature and the `speckit.analyze` instruction make analysis
  strictly read-only.
- **Observed**: Both cannot hold literally; the analysis instruction had to name one exception.
- **Effect**: assumed
- **Action**: Made appending to the project reflection log the single permitted write of the
  analysis phase in `presets/concorde-core/commands/speckit.analyze.md`; nothing else changed.
- **Improvement**: Reconcile FR-004 of `feature.concorde.workflow.execute-and-reconcile` (and its
  SC-002 "zero filesystem changes") with this exception through specification review of that root.
- **Status**: open

### R-007 · The docsite rejects abstract links to the contract, its example, and the project log

- **Phase**: implement
- **Date**: 2026-08-28
- **Feature**: feature.concorde.record-workflow-reflections
- **Kind**: tooling
- **Concerns**: docsite/plugins/concorde-content/validation.ts
- **Expected**: `npm run validate` and `npm run build` accept the feature page; the abstract's Read
  Next links point readers at the log grammar, the example, and the actual project log.
- **Observed**: The docsite reports `link.target.excluded` for the three links in `abstract.md`
  (`contracts/reflection-log.md`, `contracts/examples/reflections.md`, `../../reflections.md`)
  because those files are non-canonical Spec Kit artifacts that the site does not publish, and the
  build stops; sibling abstracts avoid this by naming such files in backticks instead of linking.
- **Effect**: blocked
- **Action**: Halted task T039 (docsite freshness). The fix is a three-line change to `abstract.md`
  (link → backtick path), which implementation may not make; presented to the maintainer for
  approval as a specification-tier edit.
- **Improvement**: Let the specify guidance say that a abstract may link only to published canonical
  sources, or let the docsite publish feature contracts and the project log as repository assets.
- **Status**: open

### R-008 · The Documentation refinement still couples both published hierarchies

- **Phase**: plan
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: specification
- **Concerns**: feature.documentation.publish-project-docsite
- **Expected**: The Documentation refinement agrees with root Feature 002 that Architecture follows
  module containment while Features follows only feature identity and explicit feature containment.
- **Observed**: FR-DOC-003 still requires both views to preserve the same module/feature hierarchy
  expressed by source paths and IDs, which would retain module-storage categories in Features.
- **Effect**: deferred
- **Action**: Implemented the maintainer-approved root Feature 002 delta without editing the adjacent
  feature's durable sources; the refinement requires its own later specification review.
- **Improvement**: Revise FR-DOC-003 through the Documentation feature's specify lifecycle so it
  requires independent semantic projections from the shared `specs/` packages.
- **Status**: open

### R-009 · The published-site contract named an obsolete manifest schema

- **Phase**: plan
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: specification
- **Concerns**: specs/concorde/features/002-create-project-docsite/contracts/published-site.md
- **Expected**: The published-site compatibility section points to the current manifest schema owned
  by `contract.documentation.build-manifest`.
- **Observed**: It named schema version 5 while the build-manifest contract, schema, and implementation
  use schema version 8.
- **Effect**: worked-around
- **Action**: Corrected the selected feature contract to schema version 8 during Phase 1 contract
  design and included contract validation in the attempt evidence.
- **Improvement**: Assert cross-contract version references in the docsite contract suite.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-29 feature.concorde.publish-project-docsite — added the cross-contract
    assertion; its first wording expected a capitalized phrase rather than the contract's exact
    compatibility sentence, then passed against the actual schema-v8 reference.

### R-010 · Duplicate feature IDs now collide at every companion route

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: implementation
- **Concerns**: docsite/tests/unit/feature-designs.test.ts
- **Expected**: The duplicate-ID fixture emits the two existing `feature.id.duplicate` findings.
- **Observed**: Stable-ID-derived routing also emits six deterministic `content.route.duplicate`
  findings for the two features' abstract, design, and implementation pages.
- **Effect**: worked-around
- **Action**: Kept both actionable validation classes and updated the test to assert two identity and
  six paired-page route findings explicitly.
- **Improvement**: If diagnostic noise becomes a usability problem, group companion route collisions
  beneath the primary duplicate feature-ID finding without weakening route validation.
- **Status**: open

### R-011 · Docusaurus reused compiled links from the old feature routes

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: tooling
- **Concerns**: docsite/scripts/prepare-publication.ts
- **Expected**: Preview and production render the freshly materialized semantic feature routes and
  rewritten cross-collection links.
- **Observed**: The first full production test reused `.docusaurus` cache entries compiled against
  the former source-path routes and failed with broken links to `/features/concorde/features/...`.
- **Effect**: worked-around
- **Action**: Made shared publication preparation remove the ignored `.docusaurus` cache after
  materialization, before either preview or production invokes Docusaurus.
- **Improvement**: Keep renderer caches inside the publication freshness boundary whenever route or
  content identity is derived from a generated registry.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-29 feature.concorde.publish-project-docsite — clearing `.docusaurus` alone did
    not remove compiled Markdown links; the repeated full build identified `node_modules/.cache` as
    the persistent bundler cache, so shared preparation now clears both disposable locations.

### R-012 · The first final digest command used a root-relative path from docsite

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: tooling
- **Concerns**: specs/concorde/features/002-create-project-docsite/implementation.md
- **Expected**: The final digest check proves the accepted implementation remained byte-identical.
- **Observed**: The first `sha256sum` ran from `docsite/` with a repository-root-relative feature path
  and reported that path missing after successfully hashing the generated diagram.
- **Effect**: worked-around
- **Action**: Reran the digest check from the repository root and confirmed the original
  `418a774d…c7b` implementation digest.
- **Improvement**: Run cross-package validation commands from the repository root when their evidence
  spans `docsite/`, `generated/`, and `specs/`.
- **Status**: open

### R-013 · Refinement links observed routes before route assignment completed

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: implementation
- **Concerns**: docsite/plugins/concorde-content/registry.ts
- **Expected**: A module-level feature's `refines` link targets the finalized stable-ID route of the
  root feature it refines.
- **Observed**: The first relationship pass assigned and consumed routes in source order, so the
  Documentation feature captured Feature 002's old parsed source-path route.
- **Effect**: worked-around
- **Action**: Split projection into two deterministic passes: assign every feature route first, then
  derive refinement relationship summaries from the finalized registry.
- **Improvement**: Resolve graph node identities before projecting any edge that embeds node routes.
- **Status**: open

### R-014 · Refinement summaries were absent from the strict manifest schema

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: implementation
- **Concerns**: specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json
- **Expected**: The generated manifest validates after feature pages retain refinement cross-links.
- **Observed**: Schema v8 uses `additionalProperties: false` and did not declare the compatible
  optional `refinements` relationship array, so fixture and production manifests were rejected.
- **Effect**: worked-around
- **Action**: Added optional `refinements` using the existing `featureRelation` shape, updated the
  contract semantics and example, and retained schema version 8 under its additive-field rule.
- **Improvement**: Update strict schemas in the same task that adds shared page-projection fields.
- **Status**: open
