---
id: feature.concorde.install-with-spec-kit.publish-release
kind: feature
module: module.concorde
parent_feature: feature.concorde.install-with-spec-kit
refines: []
subfeatures: []
scenarios:
  - installation
contracts:
  provided:
    - contract.concorde.spec-kit-installation
  required:
    - contract.concorde.spec-kit-platform
evidence_status: verified
canonical_design: specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/design.md
---

# Feature Design: Publish a Concorde Release

**Created**: 2026-08-27
**Status**: Specified; no publication realization has been accepted yet
**Input**: Publish a real, publicly reachable Concorde release with catalogs and archives so that
installation no longer requires a Concorde checkout, a local build, or a local catalog server.

## Outcome

A maintainer publishes one versioned Concorde release from the maintained sources, and any supported
project can afterwards discover and install exactly that release from a stable public location,
without cloning Concorde, building archives, or serving catalogs locally.

## Parent Context and Boundary

The parent defines what a release contains (one bundle recipe pinning one preset and one extension),
how Spec Kit installs it, and how installed behavior is verified. This child owns only how a built
and verified release becomes publicly available: when publication happens, where the archives and
catalogs live, how their advertised locations stay truthful, and how a consumer finds the current
release. It does not change package contents, bundle composition, or installed command behavior.

The parent component and installation-flow diagrams already show the release, discovery, and
installation stages; this child adds a publication step between "release built and verified" and
"catalog discovered" and needs no diagram of its own.

## User Scenarios & Testing

### User Story 1 - Publish a tagged release (Priority: P1)

A maintainer marks a release version in the repository and the release archives and catalogs are
built, verified, and published automatically to a public location that Spec Kit can read.

**Why this priority**: Without a published release every consumer must be a release builder, which
is the root cause of the current installation complexity.

**Independent Test**: Mark one release version, wait for publication, then from a machine without
the Concorde checkout register the published catalogs in a fresh supported project and preview the
bundle; the preview must name the published preset and extension versions.

**Acceptance Scenarios**:

1. **Given** a release version is marked on the maintained sources, **When** publication runs,
   **Then** the bundle, preset, and extension archives plus their three catalogs become available at
   the public location that the catalogs themselves advertise.
2. **Given** the published catalogs, **When** a clean supported project registers them and previews
   the bundle, **Then** Spec Kit resolves the pinned component versions and integrity data without any
   local build or local server.
3. **Given** release verification fails, **When** publication is attempted, **Then** nothing is
   published for that version and the failure names the failing check.

---

### User Story 2 - Discover the current release (Priority: P2)

A consumer who does not know the latest version number can still find the current release catalogs
and the version they point to.

**Why this priority**: The one-command installer and the documentation must not hard-code a version
that goes stale.

**Independent Test**: Publish two consecutive versions; resolve the current-release location after
each and verify it identifies the newer version while the older version-specific location remains
unchanged.

**Acceptance Scenarios**:

1. **Given** at least one published release, **When** a consumer reads the current-release
   location, **Then** it identifies exactly one version and the catalog locations for that version.
2. **Given** a newer release is published, **When** the current-release location is read again,
   **Then** it identifies the newer version, and every previously published version-specific
   location still serves its original, unchanged content.

---

### User Story 3 - Trust what was published (Priority: P2)

A maintainer can confirm that the published archives are the ones built from the marked sources and
that their advertised digests match.

**Independent Test**: Rebuild the same version from the marked sources on another machine and compare
digests with the published catalogs.

**Acceptance Scenarios**:

1. **Given** a published version, **When** the archives are rebuilt from the same marked sources,
   **Then** every digest in the published catalogs matches the rebuilt archives.
2. **Given** a published archive whose digest disagrees with its catalog entry, **When** Spec Kit
   installs from that catalog, **Then** installation stops before claiming success.

### Edge Cases

- The advertised download location in the catalogs differs from the location actually used for
  publication (today the catalogs advertise a repository that is not the maintained one).
- A version is marked twice or publication is re-run for an already published version.
- Publication succeeds for some archives and fails for others.
- The publication platform is temporarily unreachable while a consumer installs.
- The marked version does not match the version recorded in the maintained component manifests.

## Requirements

- **FR-001**: Publication MUST be triggered by marking a release version on the maintained sources
  and MUST require no manual upload steps.
- **FR-002**: Every published release MUST contain the bundle, preset, and extension archives and the
  three matching catalogs produced by the parent's release build, unchanged.
- **FR-003**: Catalog metadata MUST advertise the exact public locations at which the archives and
  catalogs are actually published; a mismatch MUST fail publication.
- **FR-004**: Publication MUST run the parent's release verification first and MUST publish nothing
  for a version whose verification fails.
- **FR-005**: The marked release version MUST equal the version recorded in the maintained bundle,
  preset, and extension manifests, and publication MUST stop when they disagree.
- **FR-006**: Every published version-specific location MUST be immutable once published; re-running
  publication for the same version MUST either reproduce byte-identical content or stop with a
  named conflict.
- **FR-007**: A stable current-release location MUST identify the newest published version and its
  catalog locations, and MUST be updated only after that version is fully published.
- **FR-008**: Published catalogs MUST be registrable by Spec Kit's public catalog registration from a
  clean supported project with no Concorde checkout and no local server.
- **FR-009**: A published release MUST include human-readable notes naming the component versions and
  the supported Spec Kit range.
- **FR-010**: The development path that builds and serves catalogs locally MUST remain available and
  unchanged for acceptance testing.

### Key Entities

- **Published Release**: One immutable version with its archives, catalogs, notes, and locations.
- **Current-Release Pointer**: The stable location that names the newest published version.
- **Publication Record**: The evidence that verification passed and which artifacts were published.

## Success Criteria

- **SC-001**: From a marked version to fully published release requires zero manual steps and
  completes in under 15 minutes.
- **SC-002**: 100% of published catalog digests match archives rebuilt from the same marked sources.
- **SC-003**: A clean supported project on a machine without the Concorde checkout can register the
  published catalogs and preview the bundle in under 2 minutes, using only public Spec Kit commands.
- **SC-004**: Every seeded verification failure, version mismatch, and partial-publication case
  results in no published content for that version and a named cause.

## Assumptions

- The repository's existing hosting platform publishes both versioned release assets and a stable,
  publicly reachable site; the current-release pointer is published alongside the documentation site
  that the parent already deploys automatically.
- The advertised repository location in the release metadata is corrected to the maintained
  repository before the first publication.
- Publication uses the parent's existing release build and verification; it does not introduce a
  second build path.
- Release marking is done by a maintainer with permission to publish; no consumer-facing signing or
  key management is in scope for the first published version.
