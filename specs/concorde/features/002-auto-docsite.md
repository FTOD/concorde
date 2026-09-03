---
id: feature.concorde.publish-project-docsite
kind: feature
module: module.concorde
related_features:
  - feature.auto-docs.publish-project-docsite
  - feature.concorde.workflow.initialize-architecture
  - feature.concorde.install
interfaces:
  provided:
    - interface.concorde.scaffold-docsite
    - interface.concorde.publish-docsite
  required:
    - contract.auto-docs.architecture-site
    - contract.distribution.native-installation
evidence_status: verified
---

# Feature Design: Create Unified Project Docsite

## Outcome and Scope

A maintainer of any Concorde project can create the project docsite from the template shipped in the
installed Concorde package through one reviewed proposal/apply cycle, then publish the root README,
project documents, module architectures, feature designs, and architecture-owned diagrams as one
searchable, accessible site with exact source provenance.

**In scope**: the packaged docsite template, its project-owned site identity file, the preview/apply
scaffold Tool offered through `concorde-init`, and publication from the scaffolded adapter.

**Out of scope**: installing Node.js, npm, or Archify; updating an already scaffolded `docsite/` to a
newer template; hosting beyond an optional GitHub Pages workflow file; authoring the content the site
projects.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.auto-docs` | Owns the docsite adapter whose bytes are shipped as the template and implements discovery, validation, rendering, materialization, and atomic publication. |
| `module.concorde.distribution` | Inventories the docsite template in Package Manifest 2 and installs it beneath `.concorde/framework/` with the rest of the package. |
| `entity.concorde.package-manifest` | Declares the docsite template root so checkout, archive, and installed layouts scaffold identical bytes. |
| `entity.concorde.cli` | Routes the docsite scaffold propose/apply Tool actions. |
| `entity.concorde.runtime` | Generates, digest-binds, validates, and atomically applies the Docsite Scaffold Proposal. |
| `entity.concorde.specification` | Supplies the maintained module and feature sources the scaffolded site projects. |
| `entity.concorde.archify` | Produces disposable standalone diagram deliveries during publication. |

## Interfaces

### `interface.concorde.scaffold-docsite` — Create the project docsite from the packaged template

- **Consumer**: Maintainer bootstrapping documentation for a Concorde-initialized project.
- **Direction**: Scaffold request to reviewed proposal, then accepted proposal to applied docsite files.
- **Entry points**: Leaf Skill `concorde-init` as an explicit step after the root architecture exists,
  and the native `scripts/concorde.py docsite` Tool (`--propose`, `--apply --proposal <path>`) in
  source and installed (`.concorde/framework/scripts/concorde.py`) package layouts.
- **Inputs**: Project root; site title (default: the root module name); repository URL (default: the
  project's `origin` remote when present); site URL and base path (default for a
  `github.com/<owner>/<repo>` repository: `https://<owner>.github.io` and `/<repo>/`, otherwise `/`);
  optional `--github-pages` for a deployment workflow; the explicit apply flag with a saved proposal path.
- **Outputs**: Digest-bearing Docsite Scaffold Proposal 1 listing every file with its SHA-256, or an
  applied/unchanged structured result with created paths and findings. Applied files are the
  `docsite/` adapter (package manifest and lockfile, Docusaurus configuration, sidebars, content plugin,
  scripts, theme, portable tests, README), the project-owned site identity file `docsite/site.json`,
  a minimal project `README.md` only when the project has none, and, only when requested,
  `.github/workflows/deploy-docsite.yml`.
- **Obligations**: Preview by default; apply only the current digest-bound proposal and promote its
  files atomically; never overwrite an existing `docsite/`, an unowned collision, or a symlinked
  target; copy template bytes exactly from the package and parameterize only the identity file; report
  missing Node.js 20+, npm, or pinned Archify prerequisites with remediation without installing them or
  using the network.
- **Failures**: Unconfigured project (no Profile 7 root architecture), existing or colliding
  `docsite/`, unsafe target path, stale or edited proposal, or a package whose template inventory is
  missing or disagrees with Package Manifest 2 returns a non-success result and writes nothing.
- **Compatibility**: Docsite Scaffold Proposal 1 and site identity schema 1 accompany Package
  Manifest 2; the scaffolded adapter emits Build Manifest 10 and needs Node.js 20+ with locked
  dependencies. Initialization Proposal 3 is unchanged: the scaffold is a separate propose/apply cycle.
- **Example**: `concorde.py --project-root . docsite --propose --title Atlas --repository
  https://github.com/org/atlas` writes nothing and prints the proposal; after review,
  `concorde.py --project-root . docsite --apply --proposal .concorde/docsite-proposal.json` creates
  `docsite/` with `docsite/site.json`; `npm ci && npm run check` in `docsite` then publishes the site.
- **Implementing entities**: `entity.concorde.cli`, `entity.concorde.runtime`,
  `entity.concorde.package-manifest`, `module.concorde.distribution`, `module.concorde.auto-docs`.

### `interface.concorde.publish-docsite` — Publish the project read model

- **Consumer**: Maintainer, contributor, and CI.
- **Direction**: Maintained content/build request to static site and Manifest 10 result.
- **Entry points**: `npm run start`, `npm run validate`, `npm run build`, and `npm run check` in `docsite`.
- **Inputs**: Site identity from `docsite/site.json`; root README, `docs/**/*.md`, recursive module
  `architecture.md`, direct `features/*.md`, and declared module diagrams; native `.concorde/**`
  control/framework state is excluded.
- **Outputs**: Searchable site, semantic routes, source provenance, delivered diagrams, and Build Manifest 10.
- **Obligations**: Take title, site URL, base path, organization/project names, and repository link only
  from the site identity file so the adapter stays byte-identical across projects; validate
  identities/links/routes/freshness; never discover `.concorde/**` as pages; diagnose legacy
  specification-local control sources; atomically preserve the last successful site on failure.
- **Failures**: Missing or invalid site identity, invalid sources, missing links, route collision,
  diagram failure, manifest disagreement, or build failure blocks promotion.
- **Compatibility**: Collections are home/architecture/docs/features; the docs and features
  collections appear only when `docs/` exists or at least one feature is published; feature pages have
  no abstract/implementation companions; navigation starts at the root module and labels modules by name.
- **Implementing entities**: `module.concorde.auto-docs`, `entity.concorde.specification`, `entity.concorde.archify`.

## Related Features

- `feature.auto-docs.publish-project-docsite` is the module-level design of the adapter this feature
  packages as the template and runs after scaffolding; this feature depends on it.
- `feature.concorde.workflow.initialize-architecture` composes with this feature: the same
  `concorde-init` Skill offers the docsite scaffold as a distinct step after Initialization Proposal 3
  is applied, and neither proposal changes the other.
- `feature.concorde.install` supplies the installed package whose `.concorde/framework/` copy carries
  the template; this feature depends on it.

## Usage Scenarios

1. After `concorde-init` has applied the root architecture, preview the docsite proposal, apply it,
   run `npm ci && npm run check` in `docsite`, and browse the root architecture page.
2. Preview or validate the current source registry and semantic routes without changing sources.
3. Deliver every declared module diagram, materialize ignored Docusaurus inputs, and build a candidate.
4. Promote only a candidate whose links, provenance, Manifest 10, accessibility, and source digests pass.

## Requirements

### Functional Requirements

- **FR-001**: Each module `architecture.md`, direct feature file, project document, and declared architecture diagram MUST appear exactly once in the normalized registry.
- **FR-002**: Routes MUST derive from stable semantic IDs and remain independent of legacy filenames or storage depth.
- **FR-003**: Build Manifest 10 MUST inventory all included sources, module/feature relations, routes, diagram deliveries, provenance, and generator version deterministically.
- **FR-004**: `.concorde` configuration/selection/constitution/attempt/reflection/framework/receipt state and executable/private source files MUST NOT become
  published pages or broad Manifest exclusions; legacy `specs/**/attempts/**` and specification-root
  reflection logs MUST fail the Profile 7 publication gate.
- **FR-005**: Any discovery, link, render, validation, or build failure MUST preserve maintained sources and the last successful site.
- **FR-006**: The Concorde package MUST ship the docsite adapter as a template inventoried by Package Manifest 2 so checkout, archive, and installed layouts scaffold identical bytes.
- **FR-007**: The scaffold Tool MUST preview by default, bind the proposal to template and input digests, apply exactly that proposal atomically, and never overwrite an existing `docsite/`, unowned collision, or symlink.
- **FR-008**: The adapter MUST NOT hardcode project identity; title, site URL, base path, organization/project names, and repository link MUST come from the project-owned site identity file, and Concorde's own `docsite/` MUST use the same mechanism.
- **FR-009**: A docsite scaffolded into a project that holds only Initialization Proposal 3 outputs MUST pass `npm run check` and publish the root architecture page once Node.js 20+, npm, and the pinned Archify skill are present.
- **FR-010**: The scaffold MUST report missing prerequisites with remediation and MUST complete without network access.

### Non-Functional Requirements

- **NFR-001**: Scaffolding is deterministic: identical package bytes and inputs produce identical proposal digests and files.
- **NFR-002**: The scaffold Tool requires only Python 3.11+, like every other native package Tool.

### Assumptions

- Adding the docsite template root to Package Manifest 2 and to the installed framework projection is
  an architecture change in `module.concorde.distribution` and in the manifest entity's inventory;
  it is surfaced here for architecture work rather than defined by this feature.
- `concorde-init` exposes the scaffold as a distinct second propose/apply step; the initialization
  feature and Initialization Proposal 3 stay unchanged.
- Evidence tests that assert Concorde's own content (page counts, diagram names, Concorde routes)
  remain repository evidence outside the packaged template; the template ships only portable
  fixture-based tests.
- The deployment workflow targets GitHub Pages only and is project-owned after creation.

## Edge Cases

- A feature moves paths while retaining its stable ID and canonical route.
- Two Markdown links differ syntactically but normalize to the same missing or colliding route.
- The project has no `origin` remote: the proposal omits the repository link, uses base path `/`, and
  the maintainer edits `docsite/site.json` afterwards.
- The project has no `README.md`: the proposal adds a minimal homepage README that links the root
  architecture, so the publication gate's homepage rule still holds.
- `docsite/` already exists: the proposal is a conflict listing the existing paths; the scaffold never
  merges or overwrites.
- Archify is absent: scaffolding succeeds with a prerequisite finding, and `npm run build` fails with
  remediation until the pinned skill is installed.
