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
  - plan 2026-08-29 feature.concorde.workflow.accept-milestone — status again returned
    `CONCORDE-SELF-HOST-005` for the active `claude` integration, so the terminology migration must
    refresh canonical sources and installed mirrors through the supported public Spec Kit path.

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
- **Occurrences**:
  - implement 2026-08-29 feature.concorde.install-with-spec-kit.one-command-install — README and the
    quick start initially linked the child `contracts/installer-cli.md`; changed the public links to
    the published child `design.md` and retained the contract as a backtick path.

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
- **Occurrences**:
  - plan 2026-08-29 feature.concorde.publish-project-docsite — the root feature now publishes
    `README.md` at `/`, while FR-DOC-004 and the Documentation module's project-content contract still
    describe exactly two accepted source roots; both require their own owning lifecycle update.

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

### R-015 · The self-host bootstrap requires an explicit Python interpreter

- **Phase**: plan
- **Date**: 2026-08-29
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: tooling
- **Concerns**: scripts/development/self-host-concorde.py
- **Expected**: The repository bootstrap status command can be invoked from the documented project
  root to inspect installed-surface freshness before planning the terminology migration.
- **Observed**: Direct execution returned permission denied because the tracked script is not
  executable; invoking it through `.venv/bin/python` produced the structured status result.
- **Effect**: worked-around
- **Action**: Used the explicit project interpreter for status and planned the same invocation style
  for later self-host checks.
- **Improvement**: Keep contributor commands explicit about the Python interpreter, or make the
  bootstrap executable consistently across supported checkouts.
- **Status**: open

### R-016 · The project environment does not install pytest

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: environment
- **Concerns**: feature.concorde.workflow.accept-milestone
- **Expected**: The focused migration test command runs with the repository virtual environment.
- **Observed**: `.venv/bin/python -m pytest` failed because pytest is not installed; the suite is
  written for Python's standard-library unittest runner.
- **Effect**: worked-around
- **Action**: Replaced focused and full quickstart commands with `python -m unittest` module and
  discovery invocations.
- **Improvement**: Derive validation commands from the repository's existing test entry points rather
  than assuming a third-party runner.
- **Status**: open

### R-017 · The shared-component fixture pinned the previous preset version

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: implementation
- **Concerns**: tests/concorde/fixtures/releases/shared-component/bundle.yml
- **Expected**: Bundle lifecycle fixtures that deliberately share the real `concorde-core` source
  resolve the current 0.4.0 preset during the terminology migration.
- **Observed**: The shared-component fixture still pinned 0.3.0, so Spec Kit rejected installation
  when the source manifest resolved 0.4.0.
- **Effect**: worked-around
- **Action**: Updated only the fixture's shared preset pin to 0.4.0; its independent bundle fixture
  version remains unchanged.
- **Improvement**: Make fixtures that consume live component sources derive or centrally declare the
  expected source version.
- **Status**: open

### R-018 · Feature 002's accepted route placeholder was invalid MDX

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: implementation
- **Concerns**: specs/concorde/features/002-create-project-docsite/implementation.md
- **Expected**: The full docsite gate publishes all accepted feature implementations while validating
  the Accept Milestone terminology migration.
- **Observed**: Feature 002 contained bare `/features/<feature-id>` text; MDX parsed `<feature-id>` as
  an unclosed JSX tag and stopped the production build.
- **Effect**: worked-around
- **Action**: Applied a syntax-only correction by formatting the route and adjacent path tokens as
  code spans; no Feature 002 behavior or architecture changed.
- **Improvement**: Require accepted implementation candidates containing angle-bracket placeholders
  to pass the docsite MDX build before milestone acceptance.
- **Status**: open

### R-019 · Sandbox policy rejected temporary-directory cleanup

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.workflow.accept-milestone
- **Kind**: environment
- **Concerns**: scripts/release/build-components.py
- **Expected**: Ephemeral Codex-skill backup and release-build directories can be removed after their
  contents are restored or published into maintained catalogs.
- **Observed**: The execution policy rejected the explicit recursive removal command even though both
  targets were task-specific `mktemp` directories outside the repository.
- **Effect**: deferred
- **Action**: Left the two temporary directories for normal operating-system cleanup; no project
  source, mirror, receipt, or generated publication depends on them.
- **Improvement**: Provide a sanctioned temporary-directory cleanup operation for task-scoped paths.
- **Status**: open

### R-020 · Validation quickstart placed the global project option after the verb

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.publish-project-docsite
- **Kind**: tooling
- **Concerns**: specs/concorde/features/002-create-project-docsite/implementation.md
- **Expected**: The accepted implementation guidance invokes deterministic Concorde validation with the project
  root explicitly selected.
- **Observed**: The first command used `validate --root .`, but the CLI accepts the global
  `--project-root` option only before the `validate` verb.
- **Effect**: worked-around
- **Action**: Corrected the temporal quickstart to use `--project-root . validate` and reran it.
- **Improvement**: Include the global-option ordering in generated quickstart examples for Concorde
  validation.
- **Status**: open

### R-021 · Immediate port rebinding observed TCP cleanup state

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.install-with-spec-kit.one-command-install
- **Kind**: environment
- **Concerns**: tests/concorde/acceptance/test_one_command_install.py
- **Expected**: The development-mode acceptance test can immediately bind the ephemeral catalog port
  after the installer stops and joins its loopback server.
- **Observed**: The first plain bind reported `EADDRINUSE` after shutdown because completed HTTP
  connections left normal TCP cleanup state; no server thread or listener remained.
- **Effect**: worked-around
- **Action**: Set `SO_REUSEADDR` on the probe before binding, matching the loopback HTTP server's own
  reusable-address semantics while still proving that no listener owns the port.
- **Improvement**: Use listener reachability or reusable-address rebinding when testing immediate
  cleanup of short-lived TCP servers.
- **Status**: open

### R-022 · Ephemeral development catalog URLs broke byte-level rerun safety

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.install-with-spec-kit.one-command-install
- **Kind**: implementation
- **Concerns**: scripts/install-concorde.py
- **Expected**: Repeating local-checkout installation at the same version changes no target bytes.
- **Observed**: The first implementation retained installer-owned catalog URLs containing a new
  ephemeral loopback port on every run, so three catalog configuration files changed despite the
  component installation already being current.
- **Effect**: worked-around
- **Action**: Local mode now uses distinct `concorde-dev` registrations and removes them through the
  public Spec Kit catalog commands before stopping the server; permanent `concorde` sources remain
  untouched.
- **Improvement**: Model the lifetime of temporary discovery metadata separately from installed
  component provenance whenever a source is intentionally unreachable after a command exits.
- **Status**: open
- **Occurrences**:
  - plan 2026-08-29 feature.concorde.install-with-spec-kit.one-command-install — reconciled the child
    CLI contract, research decision, data model, and implementation plan with the proven
    `concorde`/`concorde-dev` lifetime split.

### R-023 · README and contract used different fallback labels

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.install-with-spec-kit.one-command-install
- **Kind**: implementation
- **Concerns**: README.md
- **Expected**: Source, contract, README, and quick start consistently identify the retained manual
  native Spec Kit fallback.
- **Observed**: The first consistency test found README's phrase `maintained manual path` did not use
  the contract and quick start's explicit `manual native` label.
- **Effect**: worked-around
- **Action**: Aligned the README phrase and retained the automated cross-source assertion.
- **Improvement**: Add terminology assertions with the first documentation edit when two supported
  paths must remain distinguishable.
- **Status**: open
- **Occurrences**:
  - implement 2026-08-29 feature.concorde.install-with-spec-kit.one-command-install — the first
    assertion was unnecessarily case-sensitive; normalized the guide text while keeping the shared
    `manual native` term mandatory.

### R-024 · Focused test wrapper reused zsh's reserved status variable

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.install-with-spec-kit.one-command-install
- **Kind**: environment
- **Concerns**: feature.concorde.install-with-spec-kit.one-command-install
- **Expected**: A quiet focused-suite wrapper preserves the unittest exit code and prints the tail of
  its log.
- **Observed**: zsh rejected assignment to its reserved read-only `status` parameter after the tests
  ran, causing the wrapper itself to exit 1 before it could report the test result.
- **Effect**: worked-around
- **Action**: Reran the unchanged suite using the task-specific variable `focused_result`.
- **Improvement**: Avoid shell-reserved names in validation wrappers and prefer direct test commands
  when their output volume is acceptable.
- **Status**: open

### R-025 · Development success preceded transient catalog cleanup

- **Phase**: implement
- **Date**: 2026-08-29
- **Feature**: feature.concorde.install-with-spec-kit.one-command-install
- **Kind**: implementation
- **Concerns**: scripts/install-concorde.py
- **Expected**: No development-mode failure can print a success claim before every required cleanup
  operation has completed.
- **Observed**: Final review found `execute_install` printed success before `_operate` removed the
  transient `concorde-dev` catalogs, so a public-command cleanup failure could follow a false success
  line.
- **Effect**: worked-around
- **Action**: Deferred the development success report until after all three transient catalog removals
  succeed; seeded verification failure also asserts that no success text is emitted.
- **Improvement**: Treat cleanup as part of the success transaction and place terminal reporting only
  after every mandatory finalizer.
- **Status**: open
