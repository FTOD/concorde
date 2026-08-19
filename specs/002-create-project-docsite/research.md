# Research: Create Unified Project Docsite

**Feature**: `002-create-project-docsite`
**Completed**: 2026-08-19

## R1. Runtime and Framework Baseline

**Decision**: Pin Docusaurus packages to 3.10.2 in `docsite/package.json` and `package-lock.json`, use
Node.js 20 or newer, and author site code in TypeScript 5.9.x.

**Rationale**: The npm registry reported 3.10.2 as the current Docusaurus release during planning and
declares Node.js `>=20.0`. Docusaurus provides first-class TypeScript support and requires TypeScript
5.1 or newer. TypeScript 5.9 is a conservative supported line rather than the newly published 7.x
line. Exact Docusaurus versions plus a committed npm lockfile make contributor and CI resolution
repeatable.

**Alternatives considered**:

- JavaScript configuration: simpler initially, but gives weaker contracts for plugin lifecycle data
  and manifest construction.
- Docusaurus `latest` ranges: rejected because they make identical checkouts resolve differently.
- A root workspace package: rejected because the user asked for an independent `docsite/` project and
  no root JavaScript project exists.

**Sources**: [Docusaurus installation](https://docusaurus.io/docs/installation),
[TypeScript support](https://www.docusaurus.io/docs/typescript-support),
[@docusaurus/core package](https://www.npmjs.com/package/@docusaurus/core)

## R2. Reading Canonical Content Without Copies

**Decision**: Configure three instances of `@docusaurus/plugin-content-docs`: an `architecture`
instance for `../architecture/**/*.md`, the default instance for `../docs`, and a `features` instance
for canonical `../specs/**/spec.md`.

**Rationale**: The official docs plugin accepts a content path relative to the site directory and
supports include globs. Docusaurus content plugins explicitly support multiple instances when each has
a unique ID. Direct external paths let the renderer consume the canonical repositories without a
staging copy.

**Alternatives considered**:

- Copy or generate Markdown into `docsite/docs`: rejected because it creates a second content tree and
  weakens provenance.
- Symbolic links: rejected because they add platform and checkout behavior differences.
- One custom renderer for both trees: rejected because it would reimplement the supported Docusaurus
  content boundary.

**Sources**: [Docs plugin configuration](https://docusaurus.io/docs/api/plugins/%40docusaurus/plugin-content-docs),
[multi-instance plugins](https://docusaurus.io/docs/next/using-plugins)

## R3. Canonical Feature Inclusion

**Decision**: Include only `**/spec.md` from `specs/` in the first Features collection. Record other
Markdown artifacts as deliberately excluded in the manifest.

**Rationale**: Spec Kit's canonical behavioral artifact for a feature is `spec.md`; plans, tasks, and
checklists have distinct lifecycle responsibilities. A narrow include glob satisfies the feature
specification and prevents a plan from being mislabeled as a feature specification. Recursive
matching preserves compatibility with an explicitly configured nested feature directory.

**Alternatives considered**:

- Include all Markdown below `specs/`: rejected because it conflates specifications with planning and
  evidence artifacts.
- Require manual feature registration: rejected because new canonical specifications must be
  discovered automatically.

## R4. Validation, Provenance, and Manifest Ownership

**Decision**: Add one local `concorde-content` Docusaurus plugin backed by a pure source-registry
library. It scans all three collections, validates metadata and routes, exposes sorted metadata as global
data for presentation, and verifies actual routes in `postBuild` before writing the manifest.

**Rationale**: Docusaurus lifecycle APIs are designed for reading filesystem content, exposing global
data, adding routes, and post-processing builds. Centralizing discovery prevents the provenance banner,
link transformer, manifest, and tests from inventing different inclusion rules. `postBuild` receives
the rendered route list, allowing the manifest to report verified output rather than an assumption.

**Alternatives considered**:

- Presentation-only theme wrappers: rejected because they cannot establish deterministic inclusion,
  exclusion, and route evidence by themselves.
- A separate preprocessor that emits modified Markdown: rejected because it would create generated
  content copies.
- Read Docusaurus internal cache files: rejected because those are not stable public contracts.

**Sources**: [Docusaurus lifecycle APIs](https://www.docusaurus.io/docs/api/plugin-methods/lifecycle-apis),
[plugin architecture](https://docusaurus.io/docs/advanced/plugins)

## R5. Cross-Collection Links

**Decision**: Resolve Markdown file links through the shared source registry and rewrite included
source targets to their public routes during Markdown processing. Preserve URL fragments and reject
outside-root, missing, excluded, or ambiguous targets.

**Rationale**: Each docs plugin instance owns a separate content root, so a source-relative link from
`docs/` to `specs/` cannot rely on one instance's normal relative-link resolver. A registry-backed
transformer preserves author-friendly repository links while maintaining the separate route spaces.
The same pure mapper is unit-tested and used by validation and rendering.

**Alternatives considered**:

- Require authors to hard-code site URLs: rejected because source Markdown would no longer navigate
  naturally in repository viewers and route knowledge would leak into canonical content.
- Copy both collections under one content root: rejected by source-authority constraints.
- Leave cross-collection links unsupported: rejected by FR-016.

## R6. Broken Links and Route Collisions

**Decision**: Set `onBrokenLinks`, `onBrokenAnchors`, the Markdown broken-link hook, and
`onDuplicateRoutes` to throw, while also reporting source-registry validation findings before render.

**Rationale**: Docusaurus exposes explicit severity controls, but production-build link detection alone
does not provide the content-contract diagnostics needed for every invalid source. Preflight catches
source problems early; Docusaurus remains the final rendered-route authority.

**Alternatives considered**:

- Use warnings: rejected because an incomplete site could be reported as successful.
- Rely only on preflight: rejected because the final renderer can introduce routes and anchors not
  visible to the source registry.

**Source**: [Docusaurus configuration and failure controls](https://docusaurus.io/docs/api/docusaurus-config)

## R7. Local Project-Wide Search

**Decision**: Use `@easyops-cn/docusaurus-search-local` 0.55.3 with `docsRouteBasePath` set to both
`/architecture`, `/docs`, and `/features`, `docsDir` set to all three canonical roots, blog indexing disabled, and hashed
index filenames enabled. Do not enable Ask AI.

**Rationale**: Docusaurus officially documents local search as a community-supported option. This
plugin supports Docusaurus 2/3, multiple docs route bases, and a browser-downloaded local index. It
keeps preview and built-site discovery independent of a hosted crawler and LLM. Its version and
transitive graph are lockfile pinned and covered by production-build tests.

**Alternatives considered**:

- Algolia DocSearch: officially supported, but requires a public/hosted or self-hosted crawler and an
  asynchronous index lifecycle outside this feature.
- Typesense: requires a service and scraper.
- Custom search implementation: gives maximum control but adds avoidable indexing and UI scope for the
  first site.

**Sources**: [Docusaurus search choices](https://docusaurus.io/docs/next/search),
[local search plugin](https://github.com/easyops-cn/docusaurus-search-local)

## R8. Deterministic and Failure-Safe Builds

**Decision**: Build into a fresh ignored candidate directory, verify the manifest and routes, and only
then atomically promote the candidate to `docsite/build/`. Omit timestamps and absolute paths from the
manifest, sort all arrays, disable last-update display, and retain the prior successful output until
promotion completes.

**Rationale**: Docusaurus output is generated and disposable, but FR-025 requires a failed attempt not
to replace the last successful result. Candidate promotion provides that behavior independently of
where Docusaurus fails. Deterministic manifest fields let two builds compare the properties required by
SC-004 without demanding byte-identical bundler output.

**Alternatives considered**:

- Build directly into `docsite/build`: rejected because a failed build can leave partial output.
- Preserve wall-clock build metadata: rejected because it breaks reproducibility without improving
  provenance.
- Require byte-for-byte identical HTML bundles: rejected because the acceptance contract concerns
  pages, navigation, mappings, and maintained meaning.

## R9. Architecture Placement

**Decision**: Keep the project outcome as root feature
`feature.concorde.publish-project-docsite`, and add an adjacent-level refinement
`feature.documentation.publish-project-docsite` owned by `module.concorde.documentation`.

**Rationale**: The public outcome joins Concorde architecture sources, project-authored docs,
Spec Kit-owned feature specifications, and publication, so the project level remains the correct abstraction for the canonical
feature. All implementation behavior belongs to the Documentation module. The refinement records that
placement without duplicating the Spec Kit specification.

**Alternatives considered**:

- Move the canonical spec to Documentation: rejected because it would lose the already modeled
  project-level outcome and root publication scenario.
- Add site-generation behavior to Spec Kit Integration: rejected because that module owns composition
  and agent skills, not presentation.
