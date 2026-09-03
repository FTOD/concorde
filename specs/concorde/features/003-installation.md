---
id: feature.concorde.install
kind: feature
module: module.concorde
related_features:
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
standalone Concorde package from a source checkout into a clean or existing project without first
initializing or installing another framework. An applied installation provisions a Concorde-owned
virtual environment at `.concorde/.venv`, installs the locked Operation runtime there, and reports
success only after all installed Operations start through their projected entry point. Dependency
download is allowed while applying an installation; after success, every Operation starts without
network access. Concorde preserves the target project's own `.venv`, project-authored
control/specification/code, and unrelated agent assets.

## Usage

From a Concorde checkout, run `python3 scripts/install-concorde.py --target <project> --integration
codex` to inspect exact file actions. Add `--apply` only after accepting that plan. From another
working directory, pass the package root that contains `concorde.json` with `--checkout`.
Repeating the same apply returns `unchanged`; a new package version updates only receipt-owned
unchanged outputs and rebuilds `.concorde/.venv` only when its locked runtime changes or validation
shows that the managed environment is unusable. The source checkout's root `.venv` remains its
development environment and is never copied into an installed project.

## User Scenarios & Testing

### User Story 1 — Preview and Apply from a Checkout (Priority: P1)

**Independent Test**: Run the installer once in preview mode and once with `--apply` against an empty
target; prove preview writes nothing, apply installs the framework, all 17 leaf Skills, three
Operation pairs/projections, internal agents, default paths, and one isolated Operation runtime, then
prove every installed Operation starts through the exact projected launcher with network disabled.

1. **Given** a clean target, **When** installation runs without `--apply`, **Then** status is `preview`
   and the target remains empty.
2. **Given** an existing divergent target path, **When** preview runs, **Then** status is `conflict`
   and no path changes.
3. **Given** a checkout and clean target, **When** the installer runs once with `--apply`, **Then**
   installation completes without a prior `.specify` or other framework bootstrap and leaves a
   verified `.concorde/.venv` whose dependencies are sufficient for offline Operation startup.

### User Story 2 — Apply and Update Owned Files (Priority: P2)

**Independent Test**: Apply twice, then apply a changed package and verify installed/unchanged/update
outcomes plus preservation of unrelated files.

1. **Given** an accepted conflict-free plan, **When** `--apply` runs, **Then** one framework projection,
   selected integration surface, reflection assets/defaults, managed Operation runtime, and
   ownership receipt are written.
2. **Given** an existing target-root `.venv`, **When** installation or update runs, **Then** its files,
   interpreter, and installed packages remain byte-for-byte untouched.
3. **Given** an obsolete or invalid Concorde-owned `.concorde/.venv`, **When** apply rebuilds the
   runtime, **Then** the old managed environment is removed before the replacement is finally tested,
   and no obsolete Concorde environment remains after success.

### User Story 3 — Install from an Explicit Package Root (Priority: P2)

**Independent Test**: Run the installer from outside the checkout with `--checkout` pointing at the
package root, and prove its desired output inventory matches an in-checkout installation of the same
version.

1. **Given** an explicit `--checkout` package root, **When** the installer runs from another working
   directory, **Then** the resulting installation is equivalent to an in-checkout installation.
2. **Given** automation requests JSON output, **When** preview, conflict, failure, or apply completes,
   **Then** the result uses stable status and action fields.

## Interfaces

### `contract.concorde.installation` — Standalone Concorde installation

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Package request to preview plan or applied installation result.
- **Entry points**: `scripts/install-concorde.py` with `--target`, optional `--checkout`,
  `--integration`, optional `--apply`, and output format.
- **Inputs**: Real target directory, package root containing `concorde.json`, Codex/Claude choice,
  preview/apply mode, human or JSON output selection, Python 3.11+, and network/package-index access
  during apply when the locked runtime is not already locally available.
- **Outputs**: Stable status, version, integration, receipt path, and sorted
  create/adopt/update/remove/conflict actions with role/digest in human or JSON form; a legacy
  `.claude/reflections.config.json` without its canonical `.concorde/reflections/config.json`
  counterpart yields one `conflict` action naming the legacy path and directing the maintainer to
  agent-asset sync rather than silently seeding a default configuration; a runtime receipt identifies
  the managed interpreter, Python version, dependency-lock digest, and verified Operations.
- **Obligations**: Require Python 3.11+; preview by default and without network access; validate
  manifest/inventory and the locked Operation dependency set; require no prior framework
  initialization; own only `.concorde/.venv` as runtime state; never create, remove, inspect packages
  in, or execute through the target-root `.venv`; render Operation Skills through a standard-library
  bootstrap that selects the managed interpreter without relying on shell activation; allow network
  only while provisioning; verify the exact installed launcher for all Operations without network;
  reject symlink/ownership collisions; update only prior matching digests; write the receipt last;
  restore prior owned bytes and remove a partial new runtime on apply failure; never seed a default
  reflection-triage configuration over an unmigrated legacy config.
- **Failures**: Invalid package, unsupported integration/profile, unsafe path, modified owned output,
  unrelated collision, unmigrated legacy reflection-triage config, incompatible Python, dependency
  resolution/download/install failure, runtime path collision, Operation smoke-test failure, or
  filesystem failure returns diagnostics without claiming success.
- **Compatibility**: Concorde 2.1.0 Package Manifest 2, Profile 7, and Protocol 13 must match Runtime;
  17 packaged leaves and three pairs use one global namespace while only 15 leaves project publicly.
- **Example**: `python3 scripts/install-concorde.py --target ../app --integration codex --apply`.
- **Implementing entities**: `module.concorde.distribution`, `entity.concorde.installer`,
  `entity.concorde.package-manifest`, `entity.concorde.skills`, `entity.concorde.operations`, and
  `entity.concorde.agent-assets`; `entity.concorde.runtime` supplies the installed Tool package.

### `interface.concorde.one-command-install` — Invoke native installation

- **Consumer**: Project maintainer and installation automation.
- **Direction**: One installer invocation to a preview or applied native installation result.
- **Entry points**: `python3 scripts/install-concorde.py` in a checkout, or from elsewhere with
  `--checkout` pointing at one.
- **Inputs**: `--target`, optional `--checkout`, `--integration`, preview/default or explicit
  `--apply`, and output format.
- **Outputs**: Human-readable or stable JSON installation plan/result and
  `.concorde/install.json` after apply.
- **Obligations**: Delegate all lifecycle and ownership behavior to
  `contract.concorde.installation`; do not require a bootstrap framework; permit network access only
  during explicit apply and require installed Operations to remain usable without it.
- **Failures**: Invalid source, target, integration, inventory, ownership, symlink, runtime
  provisioning, Operation verification, or write failure produces non-zero status and actionable
  diagnostics.
- **Compatibility**: Concorde 2.1.0; Package Manifest 2; Profile 7; Protocol 13; Delivery Proposal 9;
  Codex/Claude integrations; Python 3.11+; locked LangGraph runtime; POSIX and Windows
  virtual-environment interpreter layouts.
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
  follow target symlinks or overwrite unowned/modified divergent files; route every Operation through
  the installed managed-runtime bootstrap rather than an ambient interpreter.
- **Failures**: Unsupported integration, invalid capability source/pair/template, output collision, or
  unsafe target path blocks projection.
- **Compatibility**: Codex and Claude are the complete supported set for Package Manifest 2.
- **Example**: `concorde-plan` in both agents invokes installed
  `.concorde/framework/operations/concorde-plan/operation.py`; its two internal leaves do not project.
- **Implementing entities**: `entity.concorde.installer`, `entity.concorde.skills`, `entity.concorde.coding-agent`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `module.concorde.distribution` | Owns package/install semantics. | Supplies the validated package contract. |
| `entity.concorde.package-manifest` | Defines identity and exact inventories. | Gates every desired output calculation. |
| `entity.concorde.installer` | Plans and applies ownership and runtime changes. | Compares desired, prior receipt, observed bytes, and managed-runtime health; provisions and verifies `.concorde/.venv` before success. |
| `entity.concorde.skills` | Supplies canonical public/internal leaf intent and effects. | Public leaves render; internal planner leaves remain framework-only. |
| `entity.concorde.operations` | Supplies paired acyclic Skill/Operation LangGraphs. | Retains Python in the framework, projects associated Markdown through the managed-runtime launcher, and supplies the smoke-test inventory. |
| `entity.concorde.agent-assets` | Supplies internal reflection roles and templates. | Is projected beside user capabilities. |
| `entity.concorde.runtime` | Supplies installed deterministic Tools and the Operation bootstrap. | Is copied beside Scripts under the framework projection; the bootstrap selects the isolated interpreter recorded by installation. |

## Related Features

- `feature.distribution.package-concorde` supplies validated package bytes.
- `feature.skills.project-workflow` supplies canonical capability projection semantics refined here
  so installed Operations enter through the managed-runtime bootstrap.
- `feature.operations.standard-development-loop` depends on this feature to make its LangGraph
  runtime available after every successful installation.
- `feature.operations.permission-bounded-planning` depends on the same managed interpreter for its
  public nested Operation and per-leaf policy compilation.

## Requirements

- **FR-001**: Package Manifest 2/version 2.1.0 MUST inventory every leaf Skill, paired Operation,
  template, package root, supported integration, and locked Operation runtime artifact.
- **FR-002**: Preview MUST be non-mutating and MUST report exact action/path/role/digest state.
- **FR-003**: Apply MUST reject all conflicts and unsafe parents before writing owned outputs.
- **FR-004**: Update/removal MUST require the observed bytes to match the prior receipt digest.
- **FR-005**: Failed apply MUST restore updated/removed owned bytes and the prior receipt, remove any
  partially created managed runtime, and MUST NOT claim an installed or unchanged result.
- **FR-006**: Repeating an identical accepted installation MUST return `unchanged`.
- **FR-007**: One installer invocation MUST discover and validate the package and calculate the
  complete preview without prior framework initialization, target mutation, or network access;
  explicit apply MAY access a package index while provisioning the managed runtime.
- **FR-008**: Installation from inside a checkout and through an explicit `--checkout` package root
  MUST produce equivalent desired outputs for the same package version.
- **FR-009**: The command interface MUST require explicit `--apply`, support Python 3.11+, and expose
  target, checkout, integration, and output-format controls.
- **FR-010**: JSON output MUST use stable schema, status, and action fields for automation.
- **FR-011**: When a project's canonical `.concorde/reflections/config.json` is absent and a legacy
  `.claude/reflections.config.json` exists, agent-asset preview/sync MUST offer and, on apply,
  perform one reviewed, digest-bound `adopt-legacy-config` action: convert the supported v4 schema
  (optional `_doc`, `log`, `features_root`, `plans_dir`, `order`, `investigators`, `implementers`,
  `require_approval`, `skip`) to canonical `schema_version: 1`, always taking the canonical
  `plans_dir`/`worktrees_dir` defaults — legacy `plans_dir` names v4 plan scratch and MUST NOT be
  mapped onto the canonical layout — then archive the legacy file byte-identically to
  `.concorde/reflections/legacy-claude-config.json` only after the canonical config is durably
  written, rolling back the written config if archiving fails so the project is unchanged. Dual
  authority (both files present), an unsupported/malformed/symlinked legacy file, or an occupied
  archive path MUST each conflict without writing. Native installation MUST NOT silently seed a
  default configuration over an unmigrated legacy file; it MUST fail closed and point at agent-asset
  sync instead. Legacy plan scratch at `.claude/reflection-plans` remains an unrelated conflict that
  adoption MUST NOT adopt, delete, or map.
- **FR-012**: Apply MUST create and use an isolated `.concorde/.venv` for installed Operations and
  MUST leave any target-root `.venv` or other project environment unchanged.
- **FR-013**: Every projected Operation Skill MUST invoke one installed standard-library bootstrap
  which deterministically selects `.concorde/.venv` and MUST NOT depend on shell activation, `PATH`
  interpreter ordering, or the installer's process interpreter.
- **FR-014**: Apply MUST install the package's locked Operation dependencies into the managed runtime
  and record the Python version plus lock digest without treating individual virtual-environment
  files as receipt-owned framework outputs.
- **FR-015**: Installation MUST report success only after the exact projected entry point starts all
  three installed Operations with network unavailable; subsequent startup MUST require no download,
  dependency resolution, or package-index access.
- **FR-016**: When runtime rebuilding is required, apply MUST remove only the obsolete
  Concorde-owned `.concorde/.venv` before final replacement verification, and success MUST leave
  exactly one managed Concorde environment.
- **FR-017**: The source checkout MUST continue to use its root `.venv` for development while an
  installed target uses `.concorde/.venv`; neither environment may be copied or mistaken for the
  other.

### Assumptions

- Explicit apply runs with access to the configured Python package index when the managed runtime
  must be created or rebuilt; preview never requires that access.
- The invoking Python 3.11+ distribution can create a virtual environment with `venv` and bootstrap
  `pip`; absence of either is an installation failure rather than a degraded installation.

## Success Criteria

- **SC-001**: A single explicit-apply invocation against clean Codex and Claude targets packages all
  17 leaves/three pairs, exposes exactly 18 public capabilities, retains each pair, omits both
  internal leaves from agents, contains no alias, and starts every Operation through the isolated
  managed interpreter.
- **SC-002**: Conflict, idempotence, integration-change, runtime rebuild/cleanup, offline startup,
  rollback, and project-`.venv` preservation tests pass.
- **SC-003**: In-checkout and explicit `--checkout` installs of the same version produce equivalent
  desired inventories and stable JSON results.

## Edge Cases

- A desired path is a symlink, directory, or divergent unowned file.
- The prior receipt owns a file that was modified or deleted between preview and apply.
- Integration changes while prior generated outputs remain owned or user-modified.
- The target exists but is not a real directory.
- A target parent is a symlink or non-directory even though Python can run the installer.
- `--checkout` points at an incomplete, modified, or wrong package root.
- The target already contains an unrelated root `.venv` or a conflicting `.concorde/.venv` path.
- Dependency provisioning succeeds only partially, the lock is stale, or an installed import is
  corrupt before the Operation smoke test.
- Installation succeeds online and the package index later becomes unavailable.
