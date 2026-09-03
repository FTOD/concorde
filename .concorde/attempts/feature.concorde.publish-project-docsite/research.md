# Research: Create Unified Project Docsite

## Unknown 1 — Where the docsite template lives in the package

- **Decision**: The Concorde `docsite/` adapter itself is the template. `concorde.json` gains the
  package root `docsite`; the installer copies it beneath `.concorde/framework/docsite/`, and the
  release archive carries it under `concorde/docsite/`. One runtime module,
  `src/concorde/docsite_template.py`, owns the inventory rule shared by installer, release builder,
  release verifier, and the scaffold Tool.
- **Rationale**: A separate copy under `templates/` would drift from the adapter Concorde runs for
  its own site (constitution B.II: Concorde develops itself with Concorde). Package Manifest 2
  already fixes `package_roots` and both packaging scripts reject any other inventory, so the root
  must be declared, not discovered.
- **Alternatives considered**: `templates/docsite/` copy (drift, double maintenance); downloading
  the adapter at scaffold time (network, violates NFR-002/FR-010).

## Unknown 2 — Which adapter files are template bytes

- **Decision**: Under `docsite/`, include regular files with suffix `.css`, `.json`, `.md`, `.svg`,
  `.ts`, `.tsx`, `.yml`; exclude directories `node_modules`, `build`, `.generated`, `.docusaurus`,
  `coverage`, `tests/repository`; exclude the project-owned `site.json`. `docsite/scaffold/` ships in
  the package (it holds the GitHub Pages workflow template) but is not copied into a target's
  `docsite/`. Symlinks are rejected.
- **Rationale**: The tracked adapter uses exactly those suffixes (verified with `git ls-files`);
  disposable directories are already ignored; repository-specific evidence must stay out of other
  projects (feature Assumptions).
- **Alternatives considered**: `git ls-files` (unavailable in an extracted archive); an explicit
  file manifest (a second inventory to keep in sync).

## Unknown 3 — Project identity without hardcoding

- **Decision**: `docsite/site.json` (site identity schema 1) is the only project-specific file the
  adapter reads: `schema_version`, `title`, `url`, `baseUrl`, `organizationName`, `projectName`,
  optional `repository`, optional `tagline`. `docusaurus.config.ts` loads it through
  `plugins/concorde-content/site-identity.ts` and fails with an actionable error when missing or
  invalid. The navbar repository icon renders only when `repository` is present.
- **Rationale**: FR-008; keeps every other adapter byte identical between Concorde and any
  scaffolded project.

## Unknown 4 — Minimal project (Initialization Proposal 3 outputs only)

- **Decision**: The scaffold proposal adds a minimal `README.md` only when the target has none, and
  the adapter registers the Documentation collection, its navbar item, and its search directory only
  when `docs/` exists. Recorded in the project reflection log.
- **Rationale**: The adapter's `content.home.required` gate needs a homepage, and Docusaurus rejects
  a docs plugin whose path is missing; Initialization Proposal 3 creates neither.

## Unknown 5 — Proposal shape

- **Decision**: Docsite Scaffold Proposal 1 lists every target path with its SHA-256. Template
  copies reference their package `source` path instead of inlining ~1 MB of content; generated
  files (`docsite/site.json`, optional `README.md`, optional workflow) inline `content`. Apply
  re-reads the package bytes and rejects any digest disagreement (stale package or edited proposal).
- **Rationale**: Digest binding is preserved (FR-007) while the reviewed JSON stays readable.

## Unknown 6 — Prerequisite reporting

- **Decision**: Propose reports Node.js 20+, npm, and the pinned Archify skill
  (`.agents/skills/archify/package.json` plus `skills-lock.json` entry) as `result.prerequisites`
  plus warning findings, outside the proposal object so proposal digests stay deterministic.
- **Rationale**: FR-010 and NFR-001.

## Unknown 7 — Deployment workflow

- **Decision**: `docsite/scaffold/deploy-docsite.yml` is a generic GitHub Pages workflow;
  Concorde's own `.github/workflows/deploy-docsite.yml` is byte-identical to it and a repository
  test proves that. The scaffold writes it only with `--github-pages`.
