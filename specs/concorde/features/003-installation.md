---
id: feature.concorde.install
kind: feature
module: module.concorde
related_features:
  - feature.concorde.release.publish
  - feature.distribution.package-concorde
  - feature.skills.project-workflow
  - feature.operations.standard-development-loop
  - feature.operations.permission-bounded-planning
interfaces:
  provided:
    - contract.concorde.installation
    - interface.concorde.one-command-install
  required:
    - contract.concorde.agent-platform
evidence_status: verified
---

# Feature Design: Install Concorde Natively

## Outcome and Scope

A maintainer can use one Python entry command, in preview or explicit-apply mode, to install a
standalone Concorde package from a source checkout or extracted release archive into a clean or
existing project without first initializing or installing another framework. Concorde owns only its
framework projection and generated integration files; it preserves project-authored
control/specification/code and unrelated agent assets.

## Usage

From a Concorde checkout, run `python3 scripts/install-concorde.py --target <project> --integration
codex` to inspect exact file actions. Add `--apply` only after accepting that plan. From an extracted
release archive, invoke its included installer and pass the extracted package root with `--checkout`.
Repeating the same apply returns `unchanged`; a new package version updates only receipt-owned
unchanged outputs.

## User Scenarios & Testing

### User Story 1 — Preview and Apply from a Checkout (Priority: P1)

**Independent Test**: Run the installer once in preview mode and once with `--apply` against an empty
target; prove preview writes nothing, apply installs the framework, all 17 leaf Skills, three
Operation pairs/projections, internal agents, and default paths, and the installed validator launcher
runs.

1. **Given** a clean target, **When** installation runs without `--apply`, **Then** status is `preview`
   and the target remains empty.
2. **Given** an existing divergent target path, **When** preview runs, **Then** status is `conflict`
   and no path changes.
3. **Given** a checkout and clean target, **When** the installer runs once with `--apply`, **Then**
   installation completes without a prior `.specify` or other framework bootstrap.

### User Story 2 — Apply and Update Owned Files (Priority: P2)

**Independent Test**: Apply twice, then apply a changed package and verify installed/unchanged/update
outcomes plus preservation of unrelated files.

1. **Given** an accepted conflict-free plan, **When** `--apply` runs, **Then** one framework projection,
   selected integration surface, reflection assets/defaults, and ownership receipt are written.

### User Story 3 — Install the Same Package from an Extracted Release (Priority: P2)

**Independent Test**: Extract a verified release archive, run its included installer, and prove its
desired output inventory matches installation from a checkout of the same version.

1. **Given** a verified extracted release, **When** its included installer runs with that package
   root, **Then** the resulting installation is equivalent to a checkout installation.
2. **Given** automation requests JSON output, **When** preview, conflict, failure, or apply completes,
   **Then** the result uses stable status and action fields.

## Interfaces

### `contract.concorde.installation` — Standalone Concorde installation

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Package request to preview plan or applied installation result.
- **Entry points**: `scripts/install-concorde.py` from a checkout or
  `concorde/scripts/install-concorde.py` from an extracted archive, with `--target`, `--checkout`,
  `--integration`, optional `--apply`, and output format.
- **Inputs**: Real target directory, checkout or extracted package root containing `concorde.json`,
  Codex/Claude choice, preview/apply mode, and human or JSON output selection.
- **Outputs**: Stable status, version, integration, receipt path, and sorted
  create/adopt/update/remove/conflict actions with role/digest in human or JSON form.
- **Obligations**: Require only Python 3.11+; preview by default; validate manifest/inventory; make
  checkout and extracted-archive sources equivalent; require no prior framework initialization or
  network access; reject symlink/ownership collisions; update only prior matching digests; write
  receipt last; restore prior bytes on apply failure.
- **Failures**: Invalid package, unsupported integration/profile, unsafe path, modified owned output, unrelated collision, or filesystem failure returns diagnostics without claiming success.
- **Compatibility**: Concorde 2.1.0 Package Manifest 2, Profile 7, and Protocol 13 must match Runtime;
  17 packaged leaves and three pairs use one global namespace while only 15 leaves project publicly.
- **Example**: `python3 scripts/install-concorde.py --target ../app --integration codex --apply`.
- **Implementing entities**: `module.concorde.distribution`, `entity.concorde.installer`,
  `entity.concorde.package-manifest`, `entity.concorde.skills`, `entity.concorde.operations`, and
  `entity.concorde.agent-assets`; `entity.concorde.runtime` supplies the installed Tool package.

### `interface.concorde.one-command-install` — Invoke native installation

- **Consumer**: Project maintainer and installation automation.
- **Direction**: One installer invocation to a preview or applied native installation result.
- **Entry points**: `python3 scripts/install-concorde.py` in a checkout or
  `python3 concorde/scripts/install-concorde.py` after archive extraction.
- **Inputs**: `--target`, optional `--checkout`, `--integration`, preview/default or explicit
  `--apply`, and output format.
- **Outputs**: Human-readable or stable JSON installation plan/result and
  `.concorde/install.json` after apply.
- **Obligations**: Delegate all lifecycle and ownership behavior to
  `contract.concorde.installation`; do not require a bootstrap framework or network access.
- **Failures**: Invalid source, target, integration, inventory, ownership, symlink, or write failure
  produces non-zero status and actionable diagnostics.
- **Compatibility**: Concorde 2.1.0; Package Manifest 2; Profile 7; Protocol 13; Delivery Proposal 9;
  Codex/Claude integrations; Python 3.11+.
- **Example**: `python3 scripts/install-concorde.py --target ../my-project --integration codex --apply`.
- **Implementing entities**: `entity.concorde.installer`, `entity.concorde.package-manifest`,
  `entity.concorde.skills`, `entity.concorde.operations`, and `entity.concorde.runtime`.

### `contract.concorde.agent-platform` — Supported project integration surface

- **Provider**: `external:coding-agent-platform`.
- **Consumer**: Concorde installer, rendered leaf and Operation skills, and project maintainer.
- **Direction**: Canonical agent assets to a supported coding-agent project layout.
- **Entry points**: `.agents/skills/**` plus `.codex/agents/**` for Codex; `.claude/skills/**` plus `.claude/agents/**` for Claude.
- **Inputs**: Canonical public/internal leaf Markdown/effects, paired Operation Python/Markdown, reflection
  templates/roles, package-relative Runtime/template prefix, and integration ID.
- **Outputs**: Regular project files with Concorde metadata and no external composer or registry.
- **Obligations**: Preserve public semantics across integrations; retain all leaves/exact pairs in the
  framework; omit internal leaves; project public leaves and Operations with owned kind roles; never
  follow target symlinks or overwrite unowned/modified divergent files.
- **Failures**: Unsupported integration, invalid capability source/pair/template, output collision, or
  unsafe target path blocks projection.
- **Compatibility**: Codex and Claude are the complete supported set for Package Manifest 2.
- **Example**: `concorde-plan` in both agents invokes installed
  `.concorde/framework/operations/concorde-plan/operation.py`; its two internal leaves do not project.
- **Implementing entities**: `entity.concorde.installer`, `entity.concorde.skills`, `entity.concorde.coding-agent`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `module.concorde.distribution` | Owns package/install/release semantics. | Supplies the verified package contract. |
| `entity.concorde.package-manifest` | Defines identity and exact inventories. | Gates every desired output calculation. |
| `entity.concorde.installer` | Plans and applies ownership changes. | Compares desired, prior receipt, and observed bytes. |
| `entity.concorde.skills` | Supplies canonical public/internal leaf intent and effects. | Public leaves render; internal planner leaves remain framework-only. |
| `entity.concorde.operations` | Supplies paired acyclic Skill/Operation LangGraphs. | Retains Python in the framework and projects associated Markdown as a Skill. |
| `entity.concorde.agent-assets` | Supplies internal reflection roles and templates. | Is projected beside user capabilities. |
| `entity.concorde.runtime` | Supplies installed deterministic Tools. | Is copied beside Scripts under the framework projection. |

## Related Features

- `feature.distribution.package-concorde` supplies verified package bytes.
- `feature.concorde.release.publish` publishes the same installable package immutably.

## Requirements

- **FR-001**: Package Manifest 2/version 2.1.0 MUST inventory every leaf Skill, paired Operation,
  template, package root, and supported integration.
- **FR-002**: Preview MUST be non-mutating and MUST report exact action/path/role/digest state.
- **FR-003**: Apply MUST reject all conflicts and unsafe parents before writing owned outputs.
- **FR-004**: Update/removal MUST require the observed bytes to match the prior receipt digest.
- **FR-005**: Failed apply MUST restore updated/removed bytes and the prior receipt.
- **FR-006**: Repeating an identical accepted installation MUST return `unchanged`.
- **FR-007**: One installer invocation MUST discover and validate the package and calculate the
  complete installation without prior framework initialization or network access.
- **FR-008**: Installation from a checkout and from an extracted release archive MUST produce
  equivalent desired outputs for the same package version.
- **FR-009**: The command interface MUST require explicit `--apply`, support Python 3.11+, and expose
  the same target, checkout, integration, and output-format controls for both package source forms.
- **FR-010**: JSON output MUST use stable schema, status, and action fields for automation.

## Success Criteria

- **SC-001**: A single explicit-apply invocation against clean Codex and Claude targets packages all
  17 leaves/three pairs, exposes exactly 18 public capabilities, retains each pair, omits both
  internal leaves from agents, and contains no alias.
- **SC-002**: Conflict, idempotence, integration-change, rollback, and preservation tests pass.
- **SC-003**: Checkout and extracted-archive installs of the same version produce equivalent desired
  inventories and stable JSON results.

## Edge Cases

- A desired path is a symlink, directory, or divergent unowned file.
- The prior receipt owns a file that was modified or deleted between preview and apply.
- Integration changes while prior generated outputs remain owned or user-modified.
- The target exists but is not a real directory.
- A target parent is a symlink or non-directory even though Python can run the installer.
- An extracted archive is incomplete, modified, or points `--checkout` at the wrong package root.
