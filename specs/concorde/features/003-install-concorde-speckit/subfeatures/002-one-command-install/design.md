---
id: feature.concorde.install-with-spec-kit.one-command-install
kind: feature
module: module.concorde
parent_feature: feature.concorde.install-with-spec-kit
refines: []
subfeatures: []
scenarios:
  - inspect-install-and-verify-concorde
  - manage-concorde-installation
contracts:
  provided:
    - contract.concorde.spec-kit-installation
  required:
    - contract.concorde.spec-kit-platform
evidence_status: unknown
canonical_design: specs/concorde/features/003-install-concorde-speckit/subfeatures/002-one-command-install/design.md
---

# Feature Design: One-Command Installation

**Created**: 2026-08-27
**Status**: Specified; no installer realization has been accepted yet
**Input**: Provide a single-command installer that sequences the native Spec Kit lifecycle (project
initialization, catalog registration, bundle installation) idempotently against a published release,
with a development mode that installs from a local Concorde checkout.

## Outcome

A maintainer turns a new or existing directory into a Concorde-enabled Spec Kit project with one
command, and the result is byte-for-byte the same installed component set that the parent's native
step-by-step Spec Kit path produces.

## Parent Context and Boundary

The parent owns what gets installed, Spec Kit's authority over the component lifecycle, the
inspect-before-install rule, and the clean-project verification matrix. This child owns only the
convenience surface that sequences those public Spec Kit operations for a person who has nothing but a
shell and network access. The installer is an optional accelerator: every step it performs remains
available and documented as a public Spec Kit command, so the parent's "no separate installer is
required" rule still holds. It must never bypass the bundle recipe, because the parent's update and
removal behavior depends on the bundle ownership record.

The parent installation-flow diagram already shows the ordered stages the installer sequences; no
child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Install into a fresh directory with one command (Priority: P1)

A maintainer with no Concorde checkout, no Spec Kit CLI, and no Python environment runs one command
in an empty directory, names their coding-agent integration, and obtains a Concorde-enabled project.

**Why this priority**: This is the whole point of the feature; the current path needs a checkout, a
build, a local server, and eight commands.

**Independent Test**: On a machine without the Concorde checkout, run the single command in an empty
directory with one supported integration and verify that the installed bundle, preset, extension,
and materialized command surfaces equal those produced by the parent's manual native path.

**Acceptance Scenarios**:

1. **Given** an empty directory and a supported integration name, **When** the command runs,
   **Then** the directory becomes a supported Spec Kit project with the current published Concorde
   release installed through the bundle and its commands materialized for that integration.
2. **Given** the supported Spec Kit CLI is not present on the machine, **When** the command runs,
   **Then** it obtains the pinned supported CLI version without requiring the Concorde checkout and
   without altering any other project's environment.
3. **Given** the command completes, **When** the maintainer reads its final output, **Then** it
   lists the installed component identities and versions, whether an agent reload is needed, and
   points to the Concorde workflow as the next step.

---

### User Story 2 - Re-run safely on an existing project (Priority: P1)

A maintainer runs the same command in a directory that is already a Spec Kit project, possibly with
Concorde already installed, and nothing is duplicated or overwritten.

**Why this priority**: Idempotence is what makes a one-command path trustworthy on real projects.

**Independent Test**: Run the command three times on the same project, and once on a project that
already used the manual native path; compare registry state and project-authored source hashes after
each run.

**Acceptance Scenarios**:

1. **Given** an existing Spec Kit project without Concorde, **When** the command runs, **Then**
   the project's existing integration, presets, extensions, and authored sources are preserved and
   only the Concorde components are added.
2. **Given** Concorde is already installed at the same version, **When** the command runs again,
   **Then** it reports the installation as already current and changes no bytes.
3. **Given** Concorde is installed at an older version, **When** the command runs, **Then** it
   previews the version change and applies it only through the native update path.
4. **Given** the project already has a different integration than the one named, **When** the
   command runs, **Then** it stops and names the conflict instead of switching integrations silently.

---

### User Story 3 - Preview before mutating (Priority: P2)

A maintainer can see every operation the command would perform, with the exact release and
component versions, before anything is written.

**Independent Test**: Run in preview mode on an empty directory and on an existing project; verify no
file changes and that the printed plan matches the operations later performed.

**Acceptance Scenarios**:

1. **Given** preview mode, **When** the command runs, **Then** it prints the ordered public Spec
   Kit operations, the release version, and the pinned component versions, and writes nothing.
2. **Given** the printed plan, **When** the command is run without preview, **Then** the performed
   operations are exactly those listed.

---

### User Story 4 - Install from a local checkout (Priority: P2)

A Concorde developer or acceptance test runs the same command in development mode against a local
Concorde checkout so that the current unreleased sources are installed through the identical
sequence.

**Why this priority**: One sequence for release and development installs keeps the documented path
and the acceptance evidence aligned.

**Independent Test**: Run the command in development mode with a checkout path into a disposable
project and verify the installed components match the checkout's manifests and that no temporary
serving process remains afterwards.

**Acceptance Scenarios**:

1. **Given** a checkout path, **When** the command runs in development mode, **Then** it builds
   and verifies the release from that checkout, serves its catalogs only for the duration of the
   install, installs through the same bundle path, and stops the serving process before exiting.
2. **Given** the checkout fails release verification, **When** development mode runs, **Then**
   nothing is installed and the failing check is named.

### Edge Cases

- Network access to the published release is unavailable mid-run.
- The named integration is not supported by the pinned Spec Kit version.
- The target directory is not empty but is not a Spec Kit project.
- The command is interrupted after project initialization but before bundle installation.
- The maintainer passes both a release version and development mode.
- The tool used to obtain the Spec Kit CLI is not installed on the machine.
- The current-release pointer names a version whose archives are not yet fully published.

## Requirements

- **FR-001**: The installer MUST be runnable as one command from a public location with, at most,
  the target directory and the coding-agent integration as required inputs.
- **FR-002**: The installer MUST perform only public Spec Kit operations and MUST NOT copy, edit, or
  generate component files itself; the parent's native path MUST remain fully documented and
  sufficient without the installer.
- **FR-003**: The installer MUST obtain the pinned supported Spec Kit CLI version when it is absent,
  without requiring the Concorde checkout, a project-specific virtual environment, or changes to
  other projects.
- **FR-004**: The installer MUST initialize the target as a supported Spec Kit project only when it is
  not one already, and MUST preserve an existing project's integration, components, and authored
  sources.
- **FR-005**: The installer MUST register the release's three catalogs and install the bundle through
  the native bundle lifecycle; it MUST NOT install the preset or extension individually.
- **FR-006**: Repeated runs MUST be idempotent: an already current installation changes no bytes,
  and no registry entry or catalog registration is duplicated.
- **FR-007**: The installer MUST default to the current published release and MUST accept an explicit
  release version; both MUST resolve through the publication feature's stable locations.
- **FR-008**: A preview mode MUST print the complete ordered plan, including release and component
  versions, and MUST write nothing.
- **FR-009**: A development mode MUST accept a local Concorde checkout, build and verify it, serve its
  catalogs only for the duration of the run, install through the same bundle path, and clean up.
- **FR-010**: Any failure MUST stop before claiming success, report which stage failed, name the
  remediation, and describe any partial state that was left behind.
- **FR-011**: The final report MUST name the installed bundle, preset, and extension versions, state
  whether the coding agent must be reloaded, and direct the maintainer to the Concorde workflow.
- **FR-012**: The installer MUST be plain, readable text so that a maintainer can inspect it before
  running it, and the documentation MUST show how to review it first.
- **FR-013**: Integration conflicts, unsupported Spec Kit versions, and unreachable releases MUST stop
  the run with the same named diagnostics that the native path produces.

### Key Entities

- **Installation Plan**: The ordered list of public operations, release version, and component
  versions that preview prints and a real run performs.
- **Run Report**: The final statement of installed versions, reload requirement, next step, and any
  residual state.
- **Development Source**: A local checkout used in place of a published release for the duration of
  one run.

## Success Criteria

- **SC-001**: A first-time maintainer on a clean machine reaches an installed, command-ready project
  in one command and under 5 minutes, without reading the release-building documentation.
- **SC-002**: In 100% of acceptance runs, the installer's result is registry- and file-identical to
  the parent's manual native path for the same release and integration.
- **SC-003**: Three consecutive runs on the same project produce zero byte changes after the first.
- **SC-004**: Preview mode produces zero file changes and its plan matches the subsequent real run in
  100% of acceptance cases.
- **SC-005**: Every seeded failure case ends with no false success record and a named stage and
  remediation.
- **SC-006**: The development mode replaces the current multi-step quick-start section, reducing the
  documented install to one command for both release and checkout installs.

## Assumptions

- A published release with a stable current-release pointer exists, as specified by the sibling
  publication feature; until it does, only development mode is usable.
- The first installer targets POSIX shells; a Windows-native equivalent is a later scope decision.
- The pinned Spec Kit CLI is obtainable from its public package index through a standard Python
  tool runner already common on maintainer machines; the installer names that prerequisite when it
  is missing rather than installing it.
- Inspect-before-install is satisfied by preview mode plus Spec Kit's own bundle preview; the
  installer does not add a second approval prompt on non-interactive runs.
- The installer lives in the Concorde repository and is published from the same location as the
  current-release pointer.
