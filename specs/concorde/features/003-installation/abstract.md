# Feature Abstract: Install and Set Up Concorde with Spec Kit

`feature.concorde.install-with-spec-kit` · specified at `module.concorde` · about five minutes.
This page is enough to understand how Concorde gets into a project, what is installed, and what
must hold; the links at the end only redirect you when you want more.

## Purpose

Get Concorde into a Spec Kit project through Spec Kit's component lifecycle plus one bounded,
previewed agent-projection stage, so that a clean project receives exactly the workflow and native
reflection-triage subagents Concorde uses on itself rather than a copy of this repository's local
files. The bundle remains the component authority; the Concorde installer adds only the custom-agent
projection primitive Spec Kit 0.16.4 lacks. It serves the maintainer who wants to know every file and
owner before setup, and the release builder who has to publish something a stranger's project can
install, update, and remove safely.

## Functionality

**What is delivered.** Concorde ships as three independently versioned release units plus discovery
metadata, each with one job:

| Part | Job | Explicitly not |
|---|---|---|
| Catalog | Advertises identity, version, compatibility, location, integrity, and trust of each unit. | An installed component. |
| Bundle `concorde-bundle` | A non-executable recipe that pins exactly one tested `concorde` preset and one `concorde` extension, distinguished by component type. | Behavior, a template layer, or a separate workflow. |
| Preset `concorde` | Composes Concorde guidance into the normal templates (specification, abstract, design reference, plan, tasks) and modifies the installed instructions for the nine path-sensitive Spec Kit commands so the selected workspace is resolved first. | A new command namespace or a second feature specification. |
| Extension `concorde` | Registers five Concorde commands and ships the runtime plus canonical triage bodies, Claude/Codex wrappers, queue helper, and deterministic projector. | The owner of normal phases, user permissions, or mutable triage state. |
| Coding-agent integration | Materializes resolved commands and selects the platform-native triage projection. | A change to command, role, queue, or plan semantics. |
| Agent projection receipt | Records path/digest ownership for generated triage skill/role files after bundle installation. | Ownership of shared config, plans, worktrees, logs, modified files, or unrelated agent assets. |

**What the maintainer can do.**

- **Inspect** before anything changes: preview the bundle and see the expanded plan — component
  IDs, versions, compatibility range, preset priority and strategy, trust source, inherited
  integration, native agent targets, digest ownership actions, conflicts, and the project-facing
  changes.
- **Install** into a new or an existing supported project from a trusted catalog, a directory, a
  manifest, or a built archive; repeating the install is idempotent and never touches
  project-authored `.concorde/`, `specs/`, or `docs/` sources.
- **Verify the workflow, not just files**: in clean Claude and Codex projects that cannot read the
  Concorde checkout, all nine normal commands, fast-loop, five Concorde commands, and the native
  triage skill plus two roles are materialized from installed bytes; durable/temporal paths and
  ownership protections are exercised rather than inferred from text.
- **Update, disable, or remove** with only Concorde-owned components changing; shared components
  and project sources stay, and failures never record success.
- **Publish a release** (sub-feature `publish-release`): a tagged version is built, verified, and
  published to a stable public location with catalogs a clean project can register.
- **Install with one command** (sub-feature `one-command-install`): an accelerator that sequences
  public Spec Kit init/catalog/bundle operations, then invokes the installed extension's projector,
  idempotently and with a local-checkout development mode. The documented manual equivalent is the
  same bundle path followed by that same installed operation.

**Not part of this feature**: the workflow or triage semantics themselves, the documentation site, a
second Spec Kit lifecycle, modifying user permission settings, or arbitrary copying outside the
installed manifest/receipt contract.

## Structure

The core view is <a href="/architecture/concorde-spec-kit-component-model.html">the Spec Kit
component model</a> (maintained source `diagrams/spec-kit-component-model.json`); the
supplemental <a href="/architecture/concorde-bundle-installation-flow.html">bundle installation
flow</a> (`diagrams/bundle-installation-flow.json`) shows the release-to-use order. In one sketch:

```text
Concorde source ──build + verify──▶ release: preset · extension · bundle archives + catalogs
                                          │  register catalogs (public location, or localhost in development)
Spec Kit 0.16.4 ◀── preview · install ────┘
   ├─ concorde preset       ──▶ .specify/templates + 9 resolved Spec Kit phase commands
   ├─ concorde extension    ──▶ 5 commands + runtime + canonical triage assets/projector
   ├─ active coding-agent integration ──▶ command skills/slashes + native triage skill/roles
   └─ projection receipt    ──▶ owns only matching generated agent paths
Project-owned: .concorde/config.json · .concorde/reflections/** · specs/** · .specify/feature.json
```

- **Spec Kit** is the host: it resolves trust and compatibility, expands the plan, installs each
  unit through its native lifecycle, records provenance, and rematerializes commands on update or
  removal.
- **The preset** modifies the installed instructions for `specify`, `clarify`, `checklist`, `plan`,
  `tasks`, `implement`, `analyze`, `converge`, and `taskstoissues` by contributing complete layers;
  the manifest uses `strategy: replace` rather than append because workspace routing must precede
  every inherited path assumption, but the Spec Kit command names and lifecycle roles remain in use.
- **The extension** contributes four workflow runtime operations, `ask`, canonical triage assets,
  the shared queue helper, and the projection operation. Feature 005 owns their meaning; installation
  owns when and where managed projections are reconciled.
- **Scripts** performs initialization, bounded context, and validation once an installed
  command invokes it; its behavior belongs to the workflow feature, not to installation.

## Logic

**From release to use**

1. **Build and verify** a release from explicit allowlists: deterministic archives (stable member
   order, permissions, timestamps) with SHA-256 digests, and catalogs whose capability counts equal
   the manifests; the future public base address is written into metadata, never contacted.
2. **Register catalogs** in the target project — the published ones, or locally served ones during
   development and acceptance.
3. **Preview** `concorde-bundle`: Spec Kit expands the recipe into the exact component plan the
   maintainer accepts.
4. **Install components**: Spec Kit installs the pinned preset and extension, records ownership,
   resolves the command stack, and materializes command winners for the active integration.
5. **Project agents**: the Concorde installer invokes the installed extension's preview/sync/verify
   operation, writes only conflict-free native targets, and records path/digest ownership.
6. **Verify** in clean Claude and Codex projects: execute installed commands, parse native roles,
   compare workspace/projection results with contracts, and reject any fallback to the checkout.
7. **Hand off** to the workflow: setup guidance ends by pointing at `feature.concorde.workflow`.
8. **Maintain**: on Spec Kit 0.16.4, disabling or reprioritizing the preset changes future
   resolution but keeps already materialized commands; update installs the accepted new layer;
   removal deletes only solely owned components and restores the next surviving lower layer.

**Rules the implementation must keep**

- One native bundle remains the component installation unit; it pins exactly one preset and one
  extension and contains no executable behavior. The installer adds only the installed extension's
  bounded agent-projection lifecycle (FR-001, FR-002, FR-009, FR-033).
- What the maintainer previewed is what gets installed, from any approved source form, under the
  active trust policy (FR-003, FR-004, FR-015).
- The preset supplies the feature abstract and design-reference templates with the normal ones and
  routes every path-sensitive command through the selected workspace before any inherited helper
  can touch a legacy root-level artifact (FR-005, FR-006, FR-007).
- The extension registers five commands and carries integrity-covered canonical triage assets;
  commands and roles remain equivalent across Claude/Codex projections (FR-008, FR-013, FR-014,
  FR-038).
- Repeated installation is byte-idempotent across components, commands, agent projections, receipts,
  and shared state and never modifies project-authored sources (FR-016, FR-039 to FR-043).
- Acceptance evidence comes only from executing installed commands in a clean project with the
  checkout unavailable; finding expected text in a file is not evidence (FR-020, FR-029, FR-030).
- Verification proves the durable-root / temporal-`attempt/` path matrix with no
  compatibility copies or symlinks and every checklist under `attempt/checklists/` (FR-018,
  FR-031).
- Update and removal change only approved components and digest-matching owned projections;
  failures preserve modified/user state and report residual state (FR-021 to FR-024, FR-041,
  FR-042).
- A published release lives at the location its catalogs advertise, and any one-command path
  converges on the native path's installed state (FR-032, FR-033).
- The preset and extension both use the `concorde` ID in their separate component namespaces; all
  sources, releases, installations, tests, and guidance use the type-qualified identities and retain
  no compatibility alias or superseded token (FR-034, FR-035, FR-037).
- User-facing guidance says Concorde modifies the existing Spec Kit commands; technical discussion
  may still name the manifest's `replace` strategy without implying that those commands disappeared
  or should no longer be invoked (FR-036).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): the delivery model
  table, the four user stories, FR-001 to FR-043, and the measurable outcomes.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (accepted realization and
  implementation detail, written by acceptance).
- **The contracts** — `contracts/bundle-distribution.md`,
  `contracts/installed-command-surfaces.md`, and
  `contracts/ecosystem-explanation.md`; the boundary promise is
  [contract.concorde.spec-kit-installation](../../architecture/contracts/spec-kit-installation/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the root summary) and the
  modules that realize it: [Distribution](../../architecture/modules/distribution/module.md) and
  [Skills](../../architecture/modules/skills/module.md).
- **The two sub-features** — [publish-release](subfeatures/001-publish-release/design.md) and
  [one-command-install](subfeatures/002-one-command-install/design.md).
- **After installation** — the workflow abstract: [Concorde Workflow](../001-concorde-workflow/abstract.md);
  and for the fastest start, [docs/quick-start.md](../../../../docs/quick-start.md).
