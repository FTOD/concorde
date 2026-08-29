# Feature Abstract: Install and Set Up Concorde with Spec Kit

`feature.concorde.install-with-spec-kit` · specified at `module.concorde` · about five minutes.
This page is enough to understand how Concorde gets into a project, what is installed, and what
must hold; the links at the end only redirect you when you want more.

## Purpose

Get Concorde into a Spec Kit project through Spec Kit's own component lifecycle — preview, install,
verify, update, remove — with no separate installer, so that a clean project receives exactly the
workflow Concorde uses on itself rather than a copy of this repository's local files. It serves the
maintainer who sets up a project and wants to know what will be added and who owns each behavior,
and the release builder who has to publish something a stranger's project can install.

## Functionality

**What is delivered.** Concorde ships as three independently versioned release units plus discovery
metadata, each with one job:

| Part | Job | Explicitly not |
|---|---|---|
| Catalog | Advertises identity, version, compatibility, location, integrity, and trust of each unit. | An installed component. |
| Bundle `concorde-bundle` | A non-executable recipe that pins exactly one tested `concorde-core` preset and one `concorde` extension. | Behavior, a template layer, or a replacement workflow. |
| Preset `concorde-core` | Composes Concorde guidance into the normal templates (specification, abstract, design reference, plan, tasks) and replaces the nine path-sensitive Spec Kit commands so the selected workspace is resolved first. | A new command namespace or a second feature specification. |
| Extension `concorde` | Registers the five Concorde surfaces (`init`, `context`, `validate`, `feature.harden`, and the agent-only `ask`) with the selected-workspace adapter, launchers, and the deterministic runtime. | The owner of the normal phases or of agent presentation syntax. |
| Coding-agent integration | Materializes the resolved commands as the active agent's skills or slash commands. | A change to command intent or paths. |

**What the maintainer can do.**

- **Inspect** before anything changes: preview the bundle and see the expanded plan — component
  IDs, versions, compatibility range, preset priority and strategy, trust source, inherited
  integration, and the project-facing changes.
- **Install** into a new or an existing supported project from a trusted catalog, a directory, a
  manifest, or a built archive; repeating the install is idempotent and never touches
  project-authored `.concorde/`, `specs/`, or `docs/` sources.
- **Verify the workflow, not just files**: in a clean project that cannot read the Concorde
  checkout, all nine normal commands and all five Concorde surfaces are materialized and actually
  execute — durable files at the feature root, temporal files under `attempt/`, and hardening
  that refuses incomplete or stale attempts.
- **Update, disable, or remove** with only Concorde-owned components changing; shared components
  and project sources stay, and failures never record success.
- **Publish a release** (sub-feature `publish-release`): a tagged version is built, verified, and
  published to a stable public location with catalogs a clean project can register.
- **Install with one command** (sub-feature `one-command-install`): an accelerator that only
  sequences public Spec Kit operations — init, catalog registration, bundle install — idempotently,
  with a development mode for a local checkout; it converges on the same installed state as the
  native path.

**Not part of this feature**: the workflow itself (`feature.concorde.workflow`), the documentation
site (`feature.concorde.publish-project-docsite`), a replacement Spec Kit lifecycle, and any
installer that copies files or bypasses the bundle recipe.

## Structure

The core view is <a href="/architecture/concorde-spec-kit-component-model.html">the Spec Kit
component model</a> (maintained source `diagrams/spec-kit-component-model.json`); the
supplemental <a href="/architecture/concorde-bundle-installation-flow.html">bundle installation
flow</a> (`diagrams/bundle-installation-flow.json`) shows the release-to-use order. In one sketch:

```text
Concorde source ──build + verify──▶ release: preset · extension · bundle archives + catalogs
                                          │  register catalogs (public location, or localhost in development)
Spec Kit 0.16.4 ◀── preview · install ────┘
   ├─ concorde-core preset  ──▶ .specify/templates + 9 resolved Spec Kit phase commands
   ├─ concorde extension    ──▶ 5 Concorde surfaces + selected-workspace adapter + launchers + runtime
   └─ active coding-agent integration ──▶ skills or slash commands the maintainer actually invokes
Project-owned, never component-owned:  .concorde/config.json · specs/** · .specify/feature.json
```

- **Spec Kit** is the host: it resolves trust and compatibility, expands the plan, installs each
  unit through its native lifecycle, records provenance, and rematerializes commands on update or
  removal.
- **The preset** contributes templates and complete replacement layers for `specify`, `clarify`,
  `checklist`, `plan`, `tasks`, `implement`, `analyze`, `converge`, and `taskstoissues`;
  replacement, not append, because workspace routing must precede every inherited path assumption.
- **The extension** contributes the four runtime operations, the `ask` procedure, and everything
  they need to run from the installed location alone.
- **Architecture Core** performs initialization, bounded context, and validation once an installed
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
4. **Install**: Spec Kit installs the pinned preset and extension, records ownership, resolves the
   preset command stack, and materializes the winners for the active integration.
5. **Verify** in a clean project: execute the installed commands, compare the observed workspace
   paths and results with the distribution contract, and reject any fallback to the checkout.
6. **Hand off** to the workflow: setup guidance ends by pointing at `feature.concorde.workflow`.
7. **Maintain**: on Spec Kit 0.16.4, disabling or reprioritizing the preset changes future
   resolution but keeps already materialized commands; update installs the accepted new layer;
   removal deletes only solely owned components and restores the next surviving lower layer.

**Rules the implementation must keep**

- One native, schema-versioned bundle is the installation unit; it pins exactly one preset and one
  extension and contains no executable behavior; there is no separate installer (FR-001, FR-002,
  FR-009).
- What the maintainer previewed is what gets installed, from any approved source form, under the
  active trust policy (FR-003, FR-004, FR-015).
- The preset supplies the feature abstract and design-reference templates with the normal ones and
  routes every path-sensitive command through the selected workspace before any inherited helper
  can touch a legacy root-level artifact (FR-005, FR-006, FR-007).
- The extension registers five surfaces through the project's active integration; intent,
  arguments, paths, results, and failures are equivalent across skills and slash commands (FR-008,
  FR-013, FR-014).
- Repeated installation is idempotent and never modifies project-authored sources (FR-016).
- Acceptance evidence comes only from executing installed commands in a clean project with the
  checkout unavailable; finding expected text in a file is not evidence (FR-020, FR-029, FR-030).
- Verification proves the durable-root / temporal-`attempt/` path matrix with no
  compatibility copies or symlinks and every checklist under `attempt/checklists/` (FR-018,
  FR-031).
- Update and removal change only approved, solely owned components; failures report residual
  state instead of recording success (FR-021 to FR-024).
- A published release lives at the location its catalogs advertise, and any one-command path
  converges on the native path's installed state (FR-032, FR-033).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): the delivery model
  table, the four user stories, FR-001 to FR-033, and the measurable outcomes.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (accepted realization and
  implementation detail, written by hardening).
- **The contracts** — `contracts/bundle-distribution.md`,
  `contracts/installed-command-surfaces.md`, and
  `contracts/ecosystem-explanation.md`; the boundary promise is
  [contract.concorde.spec-kit-installation](../../contracts/spec-kit-installation/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the root summary) and the
  modules that realize it: [Distribution](../../modules/distribution/module.md) and
  [Spec Kit Integration](../../modules/spec-kit-integration/module.md).
- **The two sub-features** — [publish-release](subfeatures/001-publish-release/design.md) and
  [one-command-install](subfeatures/002-one-command-install/design.md).
- **After installation** — the workflow abstract: [Concorde Workflow](../001-concorde-workflow/abstract.md);
  and for the fastest start, [docs/quick-start.md](../../../../docs/quick-start.md).
