---
id: feature.concorde.install-with-spec-kit.one-command-install
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
evidence_status: unknown
canonical_design: specs/concorde/features/003-installation/subfeatures/002-one-command-install/design.md
---

# Feature Design: One-Command Installation

**Created**: 2026-08-27
**Status**: Specified; no installer realization has been accepted yet
**Input**: Provide a single-command installer that sequences the native Spec Kit lifecycle (project
initialization, catalog registration, bundle installation) idempotently against a published release,
with a development mode that installs from a local Concorde checkout.

**Revision input**: After bundle install/update, project Feature 005's installed canonical assets as
native Claude or Codex triage skill/roles with previewed digest ownership, while preserving user and
inactive-integration state.

## Outcome

A maintainer turns a new or existing directory into a Concorde-enabled Spec Kit project with one
command, and the result matches the parent's documented bundle-plus-projector path: the same
components, registries, commands, native reflection-triage agents, shared default config, and
projection receipt.

## Parent Context and Boundary

The parent owns what gets installed, Spec Kit's authority over the component lifecycle, the
inspect-before-install rule, and the clean-project verification matrix. This child owns only the
convenience surface that sequences public Spec Kit operations and then invokes only the deterministic
agent-projector installed by that bundle. The installer is the complete one-command surface because
Spec Kit 0.16.4 cannot project arbitrary custom agents; the documented manual equivalent remains
bundle install followed by the installed projector. It must never bypass the bundle recipe or render
from checkout-local agents, because component and projection ownership depend on their receipts.

The parent installation-flow diagram already shows the ordered stages the installer sequences; no
child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Install into a fresh directory with one command (Priority: P1)

A maintainer with no Concorde checkout, no Spec Kit CLI, and no Python environment runs one command
in an empty directory, names their coding-agent integration, and obtains a Concorde-enabled project.

**Why this priority**: This is the whole point of the feature; the current path needs a checkout, a
build, a local server, and eight commands.

**Independent Test**: On a machine without the Concorde checkout, run the single command in an empty
directory for Claude and Codex and verify that components, commands, native triage skill/roles,
shared config, and receipt equal the parent's manual bundle-plus-projector path.

**Acceptance Scenarios**:

1. **Given** an empty directory and a supported integration name, **When** the command runs,
   **Then** the directory becomes a supported Spec Kit project with the current published Concorde
   release installed through the bundle, its commands materialized, and its native triage skill and
   two roles projected and verified for that integration.
2. **Given** the supported Spec Kit CLI is not present on the machine, **When** the command runs,
   **Then** it obtains the pinned supported CLI version without requiring the Concorde checkout and
   without altering any other project's environment.
3. **Given** the command completes, **When** the maintainer reads its final output, **Then** it
   lists component versions, projection actions/digests, whether an agent reload is needed, and the
   Concorde workflow as the next step.

---

### User Story 2 - Re-run safely on an existing project (Priority: P1)

A maintainer runs the same command in a directory that is already a Spec Kit project, possibly with
Concorde already installed, and nothing is duplicated or overwritten.

**Why this priority**: Idempotence is what makes a one-command path trustworthy on real projects.

**Independent Test**: Run the command three times, switch the active integration once, and update
from an older projection while preserving customized config, an existing plan, a modified role, and
an unrelated skill; compare full byte maps after each run.

**Acceptance Scenarios**:

1. **Given** an existing Spec Kit project without Concorde, **When** the command runs, **Then**
   the project's existing integration, presets, extensions, and authored sources are preserved and
   only the Concorde components are added.
2. **Given** Concorde is already installed at the same version, **When** the command runs again,
   **Then** it reports components and projections as current and changes no bytes.
3. **Given** Concorde is installed at an older version, **When** the command runs, **Then** it
   previews the version change and applies it only through the native update path.
4. **Given** the project already has a different integration than the one named, **When** the
   command runs, **Then** it stops and names the conflict instead of switching integrations silently.
5. **Given** a modified or unowned target at a desired projection path, **When** installation runs,
   **Then** it preserves the file, reports an ownership conflict, and emits no terminal success.
6. **Given** Claude and Codex managed surfaces coexist, **When** either integration is refreshed,
   **Then** the inactive integration remains byte-identical.

---

### User Story 3 - Preview before mutating (Priority: P2)

A maintainer can see every component and agent-projection operation, with exact release versions,
target paths, digests, actions, and conflicts, before anything is written.

**Independent Test**: Run in preview mode on an empty directory and on an existing project; verify no
file changes and that the printed plan matches the operations later performed.

**Acceptance Scenarios**:

1. **Given** preview mode, **When** the command runs, **Then** it prints the ordered public Spec
   Kit operations, release/component versions, and every `create`/`unchanged`/`adopt`/`update`/
   `remove`/`preserve`/`conflict` projection action, and writes nothing.
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
   install, installs through the same bundle path, projects only from the installed extension copy,
   and stops the serving process before exiting.
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
- Bundle installation succeeds but agent projection fails or conflicts before success output.
- A stale receipt names a missing or modified output.
- Existing manual `.claude` agent/config/plan state requires explicit migration rather than silent
  adoption.

## Requirements

- **FR-001**: The installer MUST be runnable as one command from a public location with, at most,
  the target directory and the coding-agent integration as required inputs.
- **FR-002**: The installer MUST perform project/component lifecycle changes only through public
  Spec Kit operations, then MAY invoke only the installed extension's deterministic agent projector.
  It MUST NOT render from checkout-local assets or copy/edit component files, and the parent's manual
  bundle-plus-projector path MUST remain documented and sufficient.
- **FR-003**: The installer MUST obtain the pinned supported Spec Kit CLI version when it is absent,
  without requiring the Concorde checkout, a project-specific virtual environment, or changes to
  other projects.
- **FR-004**: The installer MUST initialize the target as a supported Spec Kit project only when it is
  not one already, and MUST preserve an existing project's integration, components, and authored
  sources.
- **FR-005**: The installer MUST register the release's three catalogs and install the bundle through
  the native bundle lifecycle; it MUST NOT install the preset or extension individually.
- **FR-006**: Repeated runs MUST be idempotent: an already current installation changes no bytes,
  and no registry, catalog, projection, or receipt entry is duplicated.
- **FR-007**: The installer MUST default to the current published release and MUST accept an explicit
  release version; both MUST resolve through the publication feature's stable locations.
- **FR-008**: A preview mode MUST print the complete ordered plan, including release and component
  versions plus native agent paths/digests/actions/conflicts, and MUST write nothing.
- **FR-009**: A development mode MUST accept a local Concorde checkout, build and verify it, serve its
  catalogs only for the duration of the run, install through the same bundle path, and clean up.
- **FR-010**: Any failure MUST stop before claiming success, report which stage failed, name the
  remediation, and describe residual component and projection state.
- **FR-011**: The final report MUST name the installed bundle, preset, and extension versions, state
  whether the coding agent must be reloaded, and direct the maintainer to the Concorde workflow.
- **FR-012**: The installer MUST be plain, readable text so that a maintainer can inspect it before
  running it, and the documentation MUST show how to review it first.
- **FR-013**: Integration conflicts, unsupported Spec Kit versions, and unreachable releases MUST stop
  the run with the same named diagnostics that the native path produces.
- **FR-014**: After successful bundle install/update, the installer MUST run agent projection
  preview, stop on conflicts, apply from the installed extension, verify every output/receipt digest,
  and only then report terminal success.
- **FR-015**: Projection MUST create exactly one triage skill and two specialized roles for the
  active Claude or Codex integration and seed shared config only when absent; it MUST NOT modify user
  permission settings or pin mandatory models.
- **FR-016**: Update and removal MUST change/delete only receipt-owned projection paths whose current
  digest matches; modified, unowned, unrelated, inactive-integration, config, plan, worktree, log,
  and authored sources MUST be preserved.
- **FR-017**: Existing manual files MAY be adopted only when byte-identical or after explicit
  reviewed authorization; otherwise the installer MUST preserve them and report a migration conflict.
- **FR-018**: The final report MUST include projection status, source digest, target actions,
  conflicts or verification, receipt path, reload need, and the next workflow step.
- **FR-019**: The documented manual and one-command paths MUST converge on byte-identical component,
  registry, command, projection, receipt, and shared-default state for the same release/integration.

### Key Entities

- **Installation Plan**: The ordered list of public operations, release version, and component
  versions that preview prints and a real run performs.
- **Run Report**: The final statement of installed versions, reload requirement, next step, and any
  residual state.
- **Development Source**: A local checkout used in place of a published release for the duration of
  one run.
- **Projection Plan**: The previewed active integration, canonical source digest, native target
  actions, ownership conflicts, and remediation.
- **Projection Receipt**: Path/digest ownership for generated agent files only.

## Success Criteria

- **SC-001**: A first-time maintainer on a clean machine reaches an installed, command-ready project
  in one command and under 5 minutes, without reading the release-building documentation.
- **SC-002**: In 100% of acceptance runs, the installer's components, registries, commands,
  projections, receipt, and shared default are byte-identical to the parent's manual
  bundle-plus-projector path for the same release/integration.
- **SC-003**: Three consecutive runs produce zero byte changes after the first across components,
  commands, projections, receipt, config, plans, log, and unrelated files.
- **SC-004**: Preview mode produces zero file changes and its plan matches the subsequent real run in
  100% of acceptance cases.
- **SC-005**: Every seeded failure case ends with no false success record and a named stage and
  remediation.
- **SC-006**: The development mode replaces the current multi-step quick-start section, reducing the
  documented install to one command for both release and checkout installs.
- **SC-007**: Fresh Claude and Codex runs each produce exactly three parsed native triage outputs
  whose action/route/state/write-boundary semantics match Feature 005.
- **SC-008**: Every seeded modified/unowned/legacy projection conflict preserves all target bytes,
  emits no false success, and provides one actionable remediation.

## Assumptions

- A published release with a stable current-release pointer exists, as specified by the sibling
  publication feature; until it does, only development mode is usable.
- The first installer targets POSIX shells; a Windows-native equivalent is a later scope decision.
- The pinned Spec Kit CLI is obtainable from its public package index through a standard Python
  tool runner already common on maintainer machines; the installer names that prerequisite when it
  is missing rather than installing it.
- Inspect-before-install is satisfied by preview mode plus Spec Kit's own bundle preview; the
  installer does not add a second approval prompt on non-interactive runs.
- The installed extension is present before projection and is the only canonical source the
  projector reads.
- The installer lives in the Concorde repository and is published from the same location as the
  current-release pointer.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Installation plan` | The previewed ordered public operations, release version, and component versions that a real run will execute. | `installs` → `Bundle recipe`; `produces` → `Run report` |
| `Run report` | The final status naming installed versions, reload requirements, residual state, and the next safe step. | `describes` → `Installation plan`; `records` → `Projection receipt` |
| `Development source` | A local Concorde checkout substituted for a published release during one explicitly local installation run. | `supplies` → `Installation plan` |
| `Projection plan` | The previewed active integration, source digest, native target actions, ownership conflicts, and remediation. | `produces` → `Projection receipt`; `belongs to` → `Installation plan` |
| `Projection receipt` | The one-command install's verified ownership record for generated agent files. | `specializes` → `Agent projection receipt`; `produced by` → `Projection plan` |
