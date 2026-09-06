---
id: module.concorde.distribution
kind: module
parent: module.concorde
modules: []
features:
  - feature.distribution.package-concorde
  - feature.distribution.install-concorde
  - feature.distribution.self-distribute-concorde
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-distribution-system-overview.html
---

# Architecture: Distribution

## Responsibility

Package, validate, install, and update Concorde 3.0.0 while preserving identity, capability pairing,
integrity, path safety, explicit ownership, and user-authored files. Self-distribute canonical
Concorde capability and reflection-agent sources into each source worktree's own Codex/Claude
surfaces without carrying an agent session across worktrees.

## Boundary

Distribution owns the preview/apply installer, installation receipt, isolated installed Operation
environment, and the manifest-pinned official Understand Anything Viewer payload and launcher stored
inside that managed environment; it reads the root Package Manifest 2 as package identity and
inventory authority rather than owning that entity itself. It also owns source-checkout projection
status/check/apply, worktree-affinity verification, repository-only agent policy, generated checkout
surfaces, and their pull-request freshness gate. Agent capability projection semantics and the
Operation launcher are owned by `module.concorde.capabilities`; distribution calls that module to
render public leaf/Operation projections into an installed target or the current source worktree and
to verify every installed Operation before it writes the receipt. Reflection owns the specialist
agent sources that self-distribution projects. The official Viewer remains upstream-owned, and its
raw UA graph semantics remain outside Distribution. Distribution does not own project
specifications/code, the project's root `.venv`, `node_modules` or package-manager state,
coding-agent behavior after projection, Skill prompt semantics, Operation graph semantics, or Viewer
UI behavior.

## Operation Contract Boundary

Distribution installs Operation definitions and projects each associated Skill into an agent CLI;
it does not create invocation state or own domain input types. Package Manifest 2 currently owns
three exact pairs, their launcher, and managed-runtime verification. The root concept's one-or-more
Python realization rule is presently satisfied by one primary `operation.py` per pair.

The JSON contract ships with coordinated launcher/Skill projection and installed invocation tests.
Managed runtime verification imports the shared schema/service and checks every registered Python
`run` entry point. Project settings belong to init/config; installation preserves project-authored
configuration. Existing initialized projects must apply an explicit configure proposal before
executing the new boundary; the installed init Skill documents that migration.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.distribution.installer` | program | Calculates ownership plus runtime actions and applies one package only after isolated Operation verification. | `scripts/install-concorde.py` |
| `entity.distribution.runtime-lock` | configuration | Exact install-time Operation dependency pin whose digest controls managed-environment reuse or rebuild. | `operations/requirements.lock` |
| `entity.distribution.runtime-provisioner` | program | Plans ownership/health, creates `.concorde/.venv`, installs the Operation lock plus manifest-pinned official Viewer payload, removes only obsolete owned runtime state, verifies every Operation and the Viewer entry point offline, and returns receipt metadata. | `src/concorde/distribution/managed_runtime.py` |
| `entity.distribution.managed-runtime` | directory | Installer-owned virtual environment containing all dependencies required for post-install offline Operation startup plus the digest-pinned official Viewer below its Concorde share directory; individual files are not framework receipt outputs. | `concept:.concorde/.venv` |
| `entity.distribution.framework-projection` | directory | Installed package bytes, including Scripts and the Viewer launcher, 17 leaf Skills, three Operation pairs, Runtime, templates, the docsite template, and support assets. | `concept:.concorde/framework` |
| `entity.distribution.receipt` | configuration | Output path/role/digest ownership plus managed-runtime path, Python and Node versions, Operation lock digest, Viewer pin/digest/entry point, launchers, and verified-Operation identity for one integration/version. | `concept:native-install-receipt` |
| `entity.distribution.checkout-sync` | program | Reports, enforces, and applies canonical capability/reflection-agent projections only in the source worktree containing the invoked script, and verifies that an agent's loaded project Skill belongs to that same worktree. | `scripts/development/sync-agent-surfaces.py` |
| `entity.distribution.source-agent-policy` | document | Concorde-repository-only canonical agent policy: binds a session to its Skill-owning worktree, forbids direct generated-surface edits, and routes cross-worktree work to a newly opened agent. | `AGENTS.md` |
| `entity.distribution.claude-agent-policy-shim` | document | Claude source-checkout entry instruction that requires the canonical source-agent policy and supplies the Claude project-Skill path shape. | `CLAUDE.md` |
| `entity.distribution.codex-checkout-surface` | directory | Generated source-worktree projection of 15 public leaf and three Operation Skills for Codex; unrelated `.agents/skills` entries are outside its ownership, and reflection agents project separately under `.codex/agents`. | `concept:concorde-source-checkout-codex-surface` |
| `entity.distribution.claude-checkout-surface` | directory | Generated source-worktree projection of the same public capabilities for Claude; unrelated `.claude/skills` entries are outside its ownership, and reflection agents project separately under `.claude/agents`. | `concept:concorde-source-checkout-claude-surface` |
| `entity.distribution.source-checkout-ci` | pipeline | Pull-request and main-branch gate that rejects projection drift and runs self-distribution/worktree-affinity contracts. | `.github/workflows/validate-source-checkout.yml` |
| `entity.distribution.tests` | test | Unit, contract, integration, and acceptance evidence for packaging, installation, managed runtime, and source-checkout self-distribution. | `tests/concorde/distribution` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.distribution.installer` | `reads_from` | `entity.concorde.package-manifest` | Validates exact package inventory and supported integration. |
| `entity.distribution.installer` | `generates` | `entity.distribution.framework-projection` | Copies canonical package sources, the docsite template, and every Operation pair into the owned framework. |
| `entity.concorde.package-manifest` | `declares` | `entity.distribution.runtime-lock` | Binds the one pinned Operation dependency artifact and managed environment path. |
| `entity.distribution.installer` | `calls` | `entity.distribution.runtime-provisioner` | Applies the previewed create/reuse/rebuild action before writing the receipt. |
| `entity.distribution.runtime-provisioner` | `reads_from` | `entity.distribution.runtime-lock` | Installs the exact pinned Operation dependency and combines its digest with the Package Manifest 2 Viewer pin when comparing prior runtime state. |
| `entity.distribution.runtime-provisioner` | `generates` | `entity.distribution.managed-runtime` | Creates or safely replaces only the isolated Concorde-owned environment, including the lock-verified official Viewer. |
| `entity.distribution.runtime-provisioner` | `calls` | `module.concorde.capabilities` | Verifies every installed Operation through the managed launcher offline. |
| `entity.distribution.installer` | `calls` | `module.concorde.capabilities` | Renders 18 public leaf/Operation projections through the capability projector. |
| `entity.distribution.installer` | `writes_to` | `entity.concorde.control-state` | Persists the native install receipt and `.concorde/install.json` ownership record. |
| `entity.distribution.receipt` | `documents` | `entity.distribution.framework-projection` | Records owned bytes used for safe update/removal decisions. |
| `entity.distribution.receipt` | `documents` | `entity.distribution.managed-runtime` | Records runtime identity and verification without claiming every generated environment file. |
| `entity.distribution.checkout-sync` | `reads_from` | `entity.concorde.package-manifest` | Resolves the exact canonical Skill/Operation inventory in the current source worktree. |
| `entity.distribution.checkout-sync` | `calls` | `module.concorde.capabilities` | Renders public capability projections without changing their prompt bodies. |
| `entity.distribution.checkout-sync` | `calls` | `module.concorde.reflections` | Renders specialist agents from reflection-owned canonical sources. |
| `entity.distribution.checkout-sync` | `generates` | `entity.distribution.codex-checkout-surface` | Applies only the current worktree's exact Codex outputs. |
| `entity.distribution.checkout-sync` | `generates` | `entity.distribution.claude-checkout-surface` | Applies only the current worktree's exact Claude outputs. |
| `entity.distribution.source-agent-policy` | `configures` | `entity.concorde.coding-agent` | Requires worktree-affinity verification and a fresh agent when the loaded Skill owner differs from the target worktree. |
| `entity.distribution.claude-agent-policy-shim` | `reads_from` | `entity.distribution.source-agent-policy` | Gives Claude the same canonical worktree-affinity and generated-only rules without duplicating them. |
| `entity.distribution.source-checkout-ci` | `calls` | `entity.distribution.checkout-sync` | Requires drift-sensitive check and focused contract tests on pull requests and main. |
| `entity.distribution.checkout-sync` | `tested_by` | `entity.distribution.tests` | Proves same-worktree apply, drift-sensitive check, generated-only ownership, and cross-worktree rejection. |
| `entity.distribution.installer` | `tested_by` | `entity.distribution.tests` | Proves package ownership, installation, update, and preservation behavior. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.distribution.install` | Maintainer selects target, Package Manifest 2 checkout, and integration. | Validate exact 17/3/runtime/Viewer identity; calculate file plus `.concorde/.venv` actions; preview without network; on apply install framework/projections, create or rebuild only an owned runtime, install the pinned Operation dependency and digest-verified official Viewer, verify all three Operation entry points plus the Viewer entry point offline, then update the receipt last and roll back owned files/remove partial runtime on failure. | Idempotent owned Concorde 3.0.0 installation with offline-capable Operations and official Viewer, or exact conflict/failure diagnostics. | `contract.distribution.native-installation`, `contract.capabilities.agent-surface` |
| `interaction.distribution.self-distribute` | Maintainer or CI checks/applies one Concorde source worktree, or an agent targets a worktree after loading project Skills. | Require the invoked script and project root to belong to the same worktree; render canonical capabilities and reflection agents without prompt injection; report or fail on drift, or atomically refresh exact generated paths; derive an advertised loaded Skill's owning Git root and reject every different target root; CI runs the failing check and focused contracts. | One worktree has current ordinary Codex/Claude projections, or the agent stops and asks the user to open a new agent in the target worktree without altering the old/primary checkout. | `interface.concorde.source-checkout-distribution`, `contract.capabilities.agent-surface` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.distribution.package-concorde` | Ship one inspectable, directly installable package with Tools, 17 leaves, three pairs, 18 owned public integration projections, and the pinned official Viewer lock/launcher. |
| `feature.distribution.install-concorde` | Preview or explicitly apply a checkout into a Codex or Claude project, provisioning offline Operations and the official Viewer without a host framework or project npm mutation. |
| `feature.distribution.self-distribute-concorde` | Keep each Concorde source worktree's generated agent surfaces current and prevent an agent loaded in one worktree from developing another. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Package Manifest 2 and version 3.0.0 define one no-shim capability layout.
- Package roots are exactly `agent-assets`, `docsite`, `operations`, `scripts`, `skills`, `src`,
  `templates`, and `viewer`; the `viewer` root carries only the official release npm package/lock
  and provenance, while `docsite` ships the adapter template without disposable output, `site.json`,
  or repository-specific evidence.
- Installation preview is default; mutation requires `--apply`.
- Explicit apply may contact the configured package index and the exact manifest-pinned official
  Viewer release URL; a successful installation subsequently starts all Operations and the Viewer
  from `.concorde/.venv` without dependency resolution or network access.
- The repository root `.venv` is source-development state; installed Concorde owns only
  `.concorde/.venv` and never discovers, mutates, or deletes a target-root `.venv`, `node_modules`, or
  package-manager file. Node.js 18+ and npm are validated as external prerequisites rather than
  installed.
- Every leaf and both files of every Operation pair remain installed in the framework; internal leaves
  stay unprojected while `module.concorde.capabilities` renders each public leaf/Operation Markdown as
  a user Skill through its managed Operation launcher.
- Source-checkout projections remain generated bytes: agents never edit `.agents/skills/concorde-*`,
  `.claude/skills/concorde-*`, or specialist-agent projections directly. They edit canonical sources
  and run the current worktree's sync apply/check; neither primary nor linked worktrees are special.
- A Concorde source agent is bound to the worktree that owns its runtime-advertised project Skill
  path. Creating another worktree does not transfer the session; the user opens a new agent there.
- Exact output digests and roles, not a third-party registry, establish ownership.
- Project-authored `.concorde` control/specification/code and unrelated agent assets are never claimed.
