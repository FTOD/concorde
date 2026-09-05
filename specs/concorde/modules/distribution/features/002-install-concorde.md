---
id: feature.distribution.install-concorde
kind: feature
module: module.concorde.distribution
related_features:
  - id: feature.distribution.package-concorde
    relation: depends_on
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
  - id: feature.lifecycle.standard-development-loop
    relation: depended_on_by
  - id: feature.capabilities.permission-bounded-execution
    relation: depended_on_by
  - id: feature.auto-docs.create-project-docsite
    relation: depended_on_by
  - id: feature.understanding.explore-alignment
    relation: relates_to
interfaces:
  provided:
    - contract.concorde.installation
    - interface.concorde.one-command-install
    - interface.concorde.official-understand-anything-viewer
  required:
    - contract.concorde.agent-platform
    - contract.understand-anything.knowledge-graph
    - contract.understand-anything.viewer-package
---

# Feature Design: Install Concorde Natively

## Outcome and Scope

A maintainer can use one Python entry command, in preview or explicit-apply mode, to install a
standalone Concorde package from a source checkout into a clean or existing project without first
initializing or installing another framework. An applied installation provisions a Concorde-owned
virtual environment at `.concorde/.venv`, installs the locked Operation runtime there, and reports
success only after all installed Operations start through their projected entry point. When Node.js
18+ and npm are available, the same transaction also runs lifecycle-script-disabled `npm ci` from a
Package Manifest 2-pinned lock, integrity-verifies and installs the official Understand Anything
Viewer, and smoke-tests its entry point inside the managed runtime. Dependency download is allowed
only while applying an installation; after success, every
Operation and the Viewer start without dependency resolution or network access. Concorde preserves
the target project's own `.venv`, `node_modules`, package manifests, project-authored
control/specification/code, and unrelated agent assets. The Viewer reads an original UA
`.ua/knowledge-graph.json` (or legacy `.understand-anything/knowledge-graph.json`); it never treats a
Concorde `explore` result envelope as a UA graph.

## Usage

From a Concorde checkout, run `python3 scripts/install-concorde.py --target <project> --integration
codex` to inspect exact file actions. Add `--apply` only after accepting that plan. From another
working directory, pass the package root that contains `concorde.json` with `--checkout`.
Repeating the same apply returns `unchanged`; a new package version updates only receipt-owned
unchanged outputs and rebuilds `.concorde/.venv` only when its locked runtime changes or validation
shows that the managed environment is unusable. The source checkout's root `.venv` remains its
development environment and is never copied into an installed project.

After apply, start the pinned official Viewer from an installed target with
`python3 .concorde/framework/scripts/run-viewer.py --project-root .`. The launcher accepts optional
`--port <0-65535>` and `--no-open`, prints the official tokenized localhost URL, and stays attached
until interrupted. It resolves only the conventional raw-UA graph locations. Run `concorde explore`
separately when an agent or CI consumer needs the evidence-qualified specification-to-code JSON
envelope; that envelope is not Viewer input.

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

### User Story 4 — Launch the Pinned Official UA Viewer Offline (Priority: P1)

**Independent Test**: Apply to a clean target with a controlled official Viewer asset and Node.js
18+, disable network access, then invoke the installed launcher against raw modern and legacy UA
graphs; prove the official entry point starts, prints a tokenized loopback URL, and rejects a
Concorde `explore` envelope before spawning Node.

1. **Given** a successful installation and `.ua/knowledge-graph.json`, **When** the maintainer invokes
   the installed Viewer launcher, **Then** the pinned official Viewer starts without `npx`, npm,
   package resolution, download, or project `node_modules` mutation.
2. **Given** only `.understand-anything/knowledge-graph.json`, **When** the launcher starts, **Then** it
   deliberately follows the official legacy-first data-directory rule.
3. **Given** a missing graph, malformed raw graph, or Concorde `explore` envelope stored at a candidate
   graph path, **When** the launcher runs, **Then** it exits non-zero with an actionable diagnostic
   before the official Viewer starts.

## Interfaces

### `contract.concorde.installation` — Standalone Concorde installation

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Package request to preview plan or applied installation result.
- **Entry points**: `scripts/install-concorde.py` with `--target`, optional `--checkout`,
  `--integration`, optional `--apply`, and output format.
- **Inputs**: Real target directory, package root containing `concorde.json`, Codex/Claude choice,
  preview/apply mode, human or JSON output selection, Python 3.11+, Node.js 18+, npm, and network
  access to the configured Python package index and pinned official GitHub release asset during
  apply when the locked runtime is not already locally available.
- **Outputs**: Stable status, version, integration, receipt path, and sorted
  create/adopt/update/remove/conflict actions with role/digest in human or JSON form; a legacy
  `.claude/reflections.config.json` without its canonical `.concorde/reflections/config.json`
  counterpart yields one `conflict` action naming the legacy path and directing the maintainer to
  agent-asset sync rather than silently seeding a default configuration; a runtime receipt identifies
  the managed interpreter, Python version, Operation dependency-lock digest, pinned Viewer identity,
  Viewer asset digest, detected Node version, installed Viewer entry point, and verified Operations.
- **Obligations**: Require Python 3.11+; preview by default and without network access; validate
  manifest/inventory and the locked Operation dependency set; require no prior framework
  initialization; own only `.concorde/.venv` as runtime state, including the official Viewer payload
  below its Concorde share directory; never create, remove, inspect packages in, or execute through
  the target-root `.venv`, `node_modules`, or package-manager files; render Operation Skills through
  a standard-library bootstrap that selects the managed interpreter without relying on shell
  activation; run `npm ci --ignore-scripts` only against the shipped manifest-pinned Viewer lock,
  require its integrity to match the declared official asset, reject unexpected package identity or
  missing entry/dashboard bytes, and invoke it only through Node.js 18+; allow network only while
  provisioning; verify the exact installed launcher for all Operations and the official Viewer
  entry point without network; reject symlink/ownership collisions; update only prior matching
  digests; write the receipt last; restore prior owned bytes and remove a partial new runtime on
  apply failure; never seed a default reflection-triage configuration over an unmigrated legacy
  config.
- **Failures**: Invalid package, unsupported integration/profile, unsafe path, modified owned output,
  unrelated collision, unmigrated legacy reflection-triage config, incompatible Python, Node.js, or
  npm, dependency or Viewer download/integrity/install failure, runtime path collision, Operation or
  Viewer smoke-test failure, or filesystem failure returns diagnostics without claiming success.
- **Compatibility**: Concorde 3.0.0 Package Manifest 2, Profile 7, and Protocol 13 must match Runtime;
  17 packaged leaves and three pairs use one global namespace while only 15 leaves project publicly;
  official Viewer `Egonex-AI/Understand-Anything` v2.9.0, its manifest-pinned release asset SHA-256,
  and Node.js 18+ form the Viewer compatibility boundary.
- **Example**: `python3 scripts/install-concorde.py --target ../app --integration codex --apply`.
- **Implementing entities**: `entity.distribution.installer`, `entity.concorde.package-manifest`,
  `entity.distribution.runtime-provisioner`, `entity.distribution.framework-projection`, and
  `module.concorde.capabilities`.

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
  during explicit apply and require installed Operations plus the official Viewer to remain usable
  without it; never install into or mutate project npm state.
- **Failures**: Invalid source, target, integration, inventory, ownership, symlink, runtime
  provisioning, Operation verification, or write failure produces non-zero status and actionable
  diagnostics.
- **Compatibility**: Concorde 3.0.0; Package Manifest 2; Profile 7; Protocol 13; Delivery Proposal 9;
  Codex/Claude integrations; Python 3.11+; Node.js 18+; locked LangGraph runtime; pinned official UA
  Viewer v2.9.0; POSIX and Windows virtual-environment interpreter layouts.
- **Example**: `python3 scripts/install-concorde.py --target ../my-project --integration codex --apply`.
- **Implementing entities**: `entity.distribution.installer`, `entity.concorde.package-manifest`, and
  `module.concorde.capabilities`.

### `interface.concorde.official-understand-anything-viewer` — Launch the installed official Viewer

- **Consumer**: Project maintainer exploring an original Understand Anything implementation graph.
- **Direction**: One installed project root plus launch options to the official local read-only
  dashboard process and its tokenized loopback URL.
- **Entry points**: `python3 .concorde/framework/scripts/run-viewer.py --project-root <project>` with
  optional `--port <0-65535>` and `--no-open`.
- **Inputs**: A real non-symlink project directory containing either
  `.understand-anything/knowledge-graph.json` (preferred when that legacy directory exists) or
  `.ua/knowledge-graph.json`; the graph root must be the raw UA knowledge-graph shape with project,
  node, and edge collections rather than a Concorde Tool envelope.
- **Outputs**: The unmodified official Viewer process, its `127.0.0.1` server, token-gated dashboard
  URL on stdout, inherited diagnostics, and the official process exit status; no generated graph,
  index, npm state, or Concorde `explore` output file.
- **Obligations**: Resolve the installer-owned manifest-pinned entry point below
  `.concorde/.venv`; verify Node.js 18+, runtime identity, graph containment/regular-file status, raw
  root shape, and explicit absence of the Concorde `explore` envelope before spawning; pass the
  project root and supported options without shell interpolation; perform no download, `npx`, npm,
  graph rewrite, or source mutation at launch time; keep official token and loopback behavior intact.
- **Failures**: Missing/unhealthy installed Viewer, missing/incompatible Node.js, unsafe project or
  graph path, missing/malformed graph, Concorde envelope input, invalid port, or official process
  failure exits non-zero with an actionable stderr diagnostic.
- **Compatibility**: Concorde 3.0.0 installed layout; official Viewer v2.9.0; Node.js 18+; modern
  `.ua` and official legacy `.understand-anything` directory rules. Later official Viewer versions
  require an explicit manifest pin, digest, test, and compatibility update.
- **Example**: `python3 .concorde/framework/scripts/run-viewer.py --project-root . --port 0 --no-open`.
- **Implementing entities**: `entity.distribution.framework-projection`,
  `entity.distribution.managed-runtime`, `entity.distribution.receipt`, and
  `entity.distribution.runtime-provisioner`.

### `contract.understand-anything.knowledge-graph` — Raw official Viewer input

- **Provider**: `external:Egonex-AI/Understand-Anything@ba450c43425f3de6d43daf76526950ad8ca93536`.
- **Consumer**: Installed official Viewer launcher and Viewer process.
- **Direction**: One original UA graph at its conventional project-relative data-directory path to
  read-only visualization.
- **Entry points**: `.ua/knowledge-graph.json` or legacy
  `.understand-anything/knowledge-graph.json`; no arbitrary `--graph` file input.
- **Inputs**: UA graph version/kind/project metadata plus node, directed-edge, layer, and tour
  collections.
- **Outputs**: Validated input for the official Viewer; Concorde does not rewrite or persist it.
- **Obligations**: Preserve raw UA identity and provenance; distinguish this graph from the schema-2
  Concorde `explore` envelope even though that envelope may contain a bounded implementation
  projection.
- **Failures**: Missing, unsafe, malformed, or envelope-shaped input blocks launch.
- **Compatibility**: The Concorde adapter vocabulary remains pinned to the named upstream revision;
  the installed Viewer version is pinned separately by Package Manifest 2.
- **Example**: Run `/understand` in the project before invoking the installed Viewer launcher.
- **Implementing entities**: `entity.distribution.framework-projection` and
  `entity.distribution.managed-runtime`.

### `contract.understand-anything.viewer-package` — Pinned official Viewer release asset

- **Provider**: `external:Egonex-AI/Understand-Anything@v2.9.0`.
- **Consumer**: Concorde native installer and managed-runtime provisioner.
- **Direction**: One immutable official release tarball to a verified installer-owned runtime
  payload.
- **Entry points**: The exact HTTPS release-asset URL and SHA-256 declared by Package Manifest 2.
- **Inputs**: Self-contained npm-compatible tarball with package name
  `understand-anything-viewer`, version `2.9.0`, Node engine `>=18`, `bin/viewer.mjs`, and embedded
  dashboard `dist/`.
- **Outputs**: A lock-verified official Viewer below `.concorde/.venv` with no unresolved npm
  dependency.
- **Obligations**: Fetch only during explicit apply through lifecycle-script-disabled `npm ci` using
  the shipped lock and its asset integrity; reject unexpected package identity/version/entry point
  or missing dashboard bytes; preserve upstream package metadata and README.
- **Failures**: Network, HTTP, size, integrity, npm-install, identity, engine, or smoke-test failure
  aborts installation and participates in the existing runtime rollback.
- **Compatibility**: Official v2.9.0 release asset
  `sha256:a8626ff3ad90041e807bfdb8994eefdd986e891593c4759d08222667e5405330`;
  794982 bytes; MIT package metadata; Node.js 18+.
- **Example**: Installation materializes the asset; launch never resolves it again.
- **Implementing entities**: `entity.concorde.package-manifest`, `entity.distribution.installer`, and
  `entity.distribution.runtime-provisioner`.

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
- **Implementing entities**: `entity.distribution.installer`, `module.concorde.capabilities`, and
  `entity.concorde.coding-agent`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.concorde.package-manifest` | Defines identity and exact inventories. | Gates every desired output calculation. |
| `entity.distribution.installer` | Plans and applies ownership and runtime changes. | Compares desired, prior receipt, observed bytes, and managed-runtime health; provisions and verifies `.concorde/.venv` before success. |
| `entity.distribution.runtime-provisioner` | Isolated environment lifecycle. | Creates, health-checks, safely rebuilds, and verifies the managed venv before success. |
| `entity.distribution.managed-runtime` | Installed Operation and Viewer environment. | Supplies the isolated interpreter for every Operation and the digest-pinned official Viewer payload, both usable offline. |
| `entity.distribution.framework-projection` | Installed canonical package copy. | Retains Scripts, all 17 leaves, three pairs, Runtime, Viewer launcher, templates, the docsite template, and support assets. |
| `module.concorde.capabilities` | Agent projection and Operation launch. | Renders public leaf/Operation surfaces into the selected integration and verifies every installed Operation through the managed launcher. |
| `entity.distribution.receipt` | Ownership and verification record. | Is written last, after every Operation entry point starts offline. |
| `entity.concorde.control-state` | Holds native installation ownership state. | Receives `.concorde/install.json` after a successful apply. |
| `entity.concorde.coding-agent` | Consumes the rendered agent surface. | Follows installed leaf/Operation skills once projection succeeds. |

## Related Features

- `feature.distribution.package-concorde` supplies the validated Package Manifest 2 bytes, exact
  17-leaf/three-pair inventory, and pinned Operation runtime declaration that this feature installs.
- `feature.capabilities.provide-capability-surfaces` supplies the capability projector and Operation
  launcher this feature calls to render the selected integration and to smoke-test every Operation.
- `feature.lifecycle.standard-development-loop` depends on this feature to make its paired Operation
  runtime available and callable after every successful installation.
- `feature.capabilities.permission-bounded-execution` depends on the same managed interpreter this
  feature provisions for its public nested Operation and per-leaf policy compilation.
- `feature.auto-docs.create-project-docsite` depends on this feature because its packaged docsite
  template is installed beneath the same framework projection before scaffolding can run.
- `feature.understanding.explore-alignment` relates to this feature because both consume the raw UA
  graph contract, but `explore` emits an agent/CI-oriented evidence envelope while this feature
  launches the official human dashboard against the original graph.

## Requirements

- **FR-001**: Package Manifest 2/version 3.0.0 MUST inventory every leaf Skill, paired Operation,
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
- **FR-018**: Package Manifest 2 MUST pin the official Understand Anything Viewer provider, release
  version, immutable asset URL, SHA-256, byte size, Node engine range, installed relative entry point,
  and supported raw-graph locations.
- **FR-019**: Explicit apply MUST require Node.js 18+ and npm, run lifecycle-script-disabled `npm ci`
  from the shipped lock only when the managed runtime needs creation or rebuild, require its pinned
  official asset integrity, install below `.concorde/.venv`, validate official package identity and
  required bytes, and include Viewer
  identity in managed-runtime health/rebuild decisions and the installation receipt.
- **FR-020**: A successful installation MUST start the installed official Viewer entry point in an
  offline smoke check and later launch MUST perform no npm, `npx`, dependency resolution, download,
  graph rewrite, project package-file write, or project `node_modules` write.
- **FR-021**: The installed Viewer launcher MUST accept one real project root plus optional port and
  no-open controls; resolve only modern or legacy conventional raw-UA graph paths; reject unsafe,
  malformed, or Concorde-envelope input before spawning; invoke Node without a shell; and preserve
  the official process output, tokenized loopback URL, and exit status.
- **FR-022**: Viewer provisioning failure MUST participate in the same fail-closed transaction and
  rollback as Operation-runtime failure, and repeating the same healthy installation MUST reuse the
  exact pinned Viewer without network access.

### Assumptions

- Explicit apply runs with access to the configured Python package index when the managed runtime
  must be created or rebuilt; preview never requires that access.
- The invoking Python 3.11+ distribution can create a virtual environment with `venv` and bootstrap
  `pip`; absence of either is an installation failure rather than a degraded installation.
- Node.js and npm are external prerequisites: Concorde validates Node.js 18+ plus a working npm but
  does not install or update either executable. The official v2.9.0 Viewer asset is otherwise
  self-contained and declares no npm runtime dependencies.
- Explicit apply can reach the manifest-pinned GitHub release URL when the managed runtime requires
  creation or rebuild; an already healthy installation starts the Viewer without network access.

## Success Criteria

- **SC-001**: A single explicit-apply invocation against clean Codex and Claude targets packages all
  17 leaves/three pairs, exposes exactly 18 public capabilities, retains each pair, omits both
  internal leaves from agents, contains no alias, and starts every Operation through the isolated
  managed interpreter.
- **SC-002**: Conflict, idempotence, integration-change, runtime rebuild/cleanup, offline startup,
  rollback, and project-`.venv` preservation tests pass.
- **SC-003**: In-checkout and explicit `--checkout` installs of the same version produce equivalent
  desired inventories and stable JSON results.
- **SC-004**: Clean-install, idempotent reuse, stale-pin rebuild, integrity/npm rejection, rollback,
  Node-version rejection, offline Viewer smoke, modern/legacy raw-graph launch, and Concorde-envelope
  rejection tests pass without touching target-root npm state.

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
- Node is absent or older than 18, npm is absent, the official asset is unavailable or
  integrity-divergent, or its installed package identity/entry point is inconsistent.
- Both modern and legacy data directories exist, a candidate graph path is a symlink, or a user saves
  the `concorde explore` JSON envelope under `knowledge-graph.json`; launch follows the official
  legacy-first rule but never accepts unsafe or envelope-shaped input.
