---
id: feature.concorde.publish-project-docsite
kind: feature
module: module.concorde
refines: []
scenarios:
  - publish-architecture
contracts:
  provided:
    - contract.documentation.architecture-site
  required: []
architecture_view: specs/concorde/architecture.json
diagrams:
  - source: specs/concorde/features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json
    role: supplemental
    kind: sequence
    scenarios:
      - publish-architecture
    output: generated/architecture/project-docsite-publication-flow.html
evidence_status: verified
canonical_spec: specs/concorde/features/002-create-project-docsite/spec.md
---

# Feature Specification: Create Unified Project Docsite

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-19

**Revised**: 2026-08-25

**Status**: Implemented; automated publication and deterministic diagram evidence verified

**Input**: User description: "Create an independent root `docsite/` containing Docusaurus
configuration and formatting, keep actual Markdown documentation in a separate root `docs/`, and
present those documents, feature specifications under `specs/`, and Concorde architecture sources
and views as one project website. Maintain a useful custom documentation baseline—including a quick
start, project description, conceptual model, project structure, workflow, and command guidance—so
the generated site teaches the Concorde framework rather than presenting specifications alone."

## Scenario and Component Diagram

`diagrams/project-docsite-publication-flow.json` is a maintained, supplemental sequence view for the
`publish-architecture` scenario. Its generated projection is
`generated/architecture/project-docsite-publication-flow.html`. The view shows the build command
invoking the source registry, Archify delivery, disposable content materialization, Docusaurus build,
candidate validation, and atomic publisher before a programmer or agent browses the result.

The diagram explains component involvement and call order; the user stories and requirements below
remain the behavioral authority, and `specs/concorde/architecture.json` remains the bounded root
architecture view.

This feature does not add a separate core component diagram because the bounded root view already
shows Documentation, Architecture Core, Spec Kit Integration, the coding agent, and the maintainer at
the level where this root feature is owned. Repeating those components here would duplicate that
canonical structure. The publication sequence is therefore explicitly `role: supplemental` and
answers only the narrower call-order question.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse the Whole Project in One Site (Priority: P1)

As a maintainer, contributor, or reviewer, I can open one project website and browse the maintained
architecture, project documentation, and every feature's permanent specification and design so that
I can understand both intended behavior and accepted realization without navigating the repository manually.

**Why this priority**: A unified, browsable read model is the primary value of the feature. Without
all three navigation families and all four source collections in one coherent site, the docsite does
not represent the project as requested.

**Independent Test**: Populate `specs/` with a module, boundary contract, delivered view, and two
feature specifications and designs, and `docs/` with a small documentation hierarchy; build and open the site, then
confirm that every eligible source is reachable through distinct Architecture, Documentation, and
Features navigation paths and project-wide discovery.

**Acceptance Scenarios**:

1. **Given** eligible architecture and feature sources in the hierarchical `specs/` tree and Markdown
   documents in `docs/`, **When** a visitor opens the generated site, **Then**
   the visitor can reach all three navigation families from a
   project landing page without knowing their repository paths.
2. **Given** multiple nested documentation pages and multiple features, **When** the visitor browses
   the site navigation, **Then** documentation hierarchy is preserved and feature specifications are
   grouped with their permanent designs under a clearly labeled Features area.
3. **Given** a feature specification and design, **When** their pages are displayed, **Then** the
   specification's identifying facts and both pages' source provenance are visible.
4. **Given** a visitor looking for a known phrase, module, or feature, **When** the visitor uses the
   site's discovery facilities, **Then** matching project documentation and feature specifications can
   both be found.

---

### User Story 2 - Author Documentation Outside the Site Project (Priority: P2)

As a contributor, I can add or edit ordinary Markdown files in the root `docs/` directory without
copying them into the site project or learning its presentation internals so that documentation stays
simple to author and has one canonical location.

**Why this priority**: Separating maintained content from presentation configuration prevents the
site project from becoming a second content authority and keeps documentation approachable.

**Independent Test**: Add a nested Markdown page under `docs/`, link it from another document, rebuild
the site without editing `docsite/`, and verify that the new page and link appear in the expected
documentation hierarchy.

**Acceptance Scenarios**:

1. **Given** a valid new Markdown file under `docs/`, **When** the site is rebuilt, **Then** the page is
   included without a copied canonical file or a required manual registration in `docsite/`.
2. **Given** a documentation page is renamed, moved, or removed, **When** the site is rebuilt, **Then**
   the site reflects the new maintained state and does not retain an unexplained stale page.
3. **Given** a document uses supported Markdown links and formatting, **When** it is presented in the
   site, **Then** its meaning and link destinations are preserved under the site's shared visual
   formatting.

---

### User Story 3 - Publish Feature Specifications From Their Canonical Location (Priority: P3)

As a product owner or reviewer, I can read every feature's canonical specification from the same site
while Spec Kit continues to own the files under `specs/`, so that publication does not fork or rewrite
the feature-development lifecycle.

**Why this priority**: Feature specifications are the second required content source, and preserving
their authority is essential to the Concorde and Spec Kit ownership boundary.

**Independent Test**: Change the title, status, and one requirement in an existing `spec.md`, add a
second feature directory, rebuild the site, and confirm that both feature pages reflect their current
canonical files with no generated changes under `specs/`.

**Acceptance Scenarios**:

1. **Given** a feature directory containing a canonical `spec.md`, **When** the site is rebuilt,
   **Then** the feature appears in the Features area with its current title, status, identifier, and
   full specification content.
2. **Given** a canonical feature specification changes, **When** the next build succeeds, **Then** its
   published page reflects that change without requiring a synchronized copy.
3. **Given** a feature workspace also contains an `implementation/` directory, root checklists, or
   other supporting artifacts,
   **When** the first version of the site is built, **Then** those files are not presented as canonical
   feature specifications.

---

### User Story 4 - Verify a Reproducible Site Build (Priority: P4)

As a maintainer, I can preview and build the complete site from the independent `docsite/` project and
receive actionable failures for invalid content so that only a complete, traceable read model is
treated as publishable.

**Why this priority**: A repeatable build and explicit failure behavior make the website trustworthy
and suitable for later continuous integration and publication work.

**Independent Test**: Build the same unchanged content twice and compare the page inventory, then add
a broken link and a duplicate page identity and confirm that each failure names the affected source
and prevents the incomplete result from being reported as successful.

**Acceptance Scenarios**:

1. **Given** a clean checkout with valid content, **When** a maintainer follows the documented preview
   or build entry point from `docsite/`, **Then** the complete site is produced without first moving or
   editing canonical content.
2. **Given** unchanged maintained inputs and site configuration, **When** two builds run independently,
   **Then** they produce the same page inventory, navigation relationships, and source-to-page mapping.
3. **Given** an unreadable source, broken internal link, invalid required metadata, or route collision,
   **When** the site build runs, **Then** it fails with an actionable diagnostic that identifies the
   affected source and reason.
4. **Given** a failed build, **When** the maintainer reviews its result, **Then** the incomplete output
   is not represented as the current successful project site.
5. **Given** the textual publication scenario and its feature-owned diagram, **When** a maintainer
   reviews the build path, **Then** they can identify which component validates sources, renders
   diagrams, materializes content, builds the site, validates the candidate, and promotes output.

---

### User Story 5 - Learn and Adopt Concorde from Maintained Guides (Priority: P2)

As a prospective user, maintainer, or contributor, I can follow a coherent set of project-authored
guides that explains Concorde, gets me started, and tells me where workflow artifacts belong so that
I do not have to reconstruct the framework from feature specifications or repository source alone.

**Why this priority**: Specifications are the primary content of a spec-driven project, but they are
organized as normative feature authorities rather than a progressive learning path. A useful
Documentation collection must orient readers and connect concepts, tasks, and canonical sources.

**Independent Test**: Give a reader only the generated site's landing page and ask them to explain
Concorde's purpose, distinguish architecture/specification/design/implementation artifacts, locate a
quick-start path, identify the two command families, and name the canonical file to edit for five
representative changes.

**Acceptance Scenarios**:

1. **Given** a first-time visitor on the Documentation landing page, **When** they follow the
   recommended path, **Then** they can reach a quick start, framework overview, specification model,
   project structure guide, core workflow, and command reference without browsing repository files.
2. **Given** a reader learning Concorde's concepts, **When** they use the maintained guides, **Then**
   they can distinguish Spec Kit's normal lifecycle from Concorde's architectural controls and
   explain the roles of durable specifications, durable designs, temporary implementation attempts,
   contracts, diagrams, and generated projections.
3. **Given** a reader preparing a first project or contribution, **When** they follow the quick start
   and workflow guidance, **Then** they can identify prerequisites, the next command or validation
   step, the expected review gate, and the canonical source to change.
4. **Given** a guide that summarizes normative project behavior, **When** a reader needs complete or
   authoritative detail, **Then** the guide links to the relevant architecture or feature source and
   does not claim authority over it.

### Edge Cases

- `docs/` exists but contains no eligible Markdown pages, or `specs/` contains no canonical feature
  specifications.
- A documentation file or feature specification has no display title, duplicate navigation identity,
  invalid metadata, or a path that would map to an existing site route.
- A feature workspace contains root `spec.md` and checklists alongside nested implementation plans,
  tasks, evidence, generated files, or unrelated Markdown.
- Documents in different source collections have the same filename or title.
- A relative link crosses from `docs/` to `specs/`, from a feature specification to `docs/`, or points
  to a source that is not included in the site.
- A source is renamed or removed after a prior build, leaving a formerly valid route or link.
- A draft feature specification is present; it remains visible with its draft status rather than being
  silently omitted or presented as approved.
- Site output or staging content from an earlier build is stale, incomplete, or accidentally placed
  beside canonical Markdown sources.
- Repository paths contain spaces or non-ASCII characters that are valid for maintained sources.
- The Documentation collection technically publishes but contains only a landing page, forcing new
  readers to infer the framework from normative specifications.
- A guide repeats a setup detail that changes while its linked canonical specification remains
  current, creating an obvious documentation-freshness disagreement.
- A reader mistakes installed skills, workflow-control state, temporary implementation files, or
  generated output for durable project intent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST provide an independent root `docsite/` directory for the Docusaurus
  site's configuration, formatting, presentation components, static presentation assets, and
  documented preview and build entry points.
- **FR-002**: The project MUST provide a separate root `docs/` directory as the canonical location for
  project documentation authored as Markdown files.
- **FR-003**: Canonical feature specifications MUST remain in their Spec Kit-owned locations under the
  root `specs/` directory, nested beneath the module that owns each feature.
- **FR-032**: Maintained architecture specifications MUST live in the same root `specs/` hierarchy as
  feature specifications; a separate top-level architecture source tree MUST NOT be required.
- **FR-004**: The `docsite/` directory MUST NOT contain canonical copies of content owned by `docs/` or
  `specs/`.
- **FR-005**: The site MUST include every eligible Markdown document found recursively under `docs/`.
- **FR-006**: The site MUST include the canonical `spec.md` for every feature directory under `specs/`.
- **FR-007**: The first version MUST NOT present plans, tasks, checklists, or other supporting files as
  feature specifications merely because they are stored under `specs/`.
- **FR-008**: Content collection and presentation MUST NOT modify files under `docs/` or `specs/`.
- **FR-009**: The site MUST provide a project landing page with distinct, clearly labeled entry points
  for Architecture, project Documentation, and Features.
- **FR-010**: Documentation navigation MUST preserve the meaningful hierarchy expressed by paths and
  navigation metadata under `docs/`.
- **FR-011**: Feature navigation MUST identify each specification by its feature title and MUST expose
  its stable ID and lifecycle status when those values are present.
- **FR-012**: A newly added eligible document or canonical feature specification MUST be discovered on
  the next build without requiring a canonical copy or per-page registration in `docsite/`.
- **FR-013**: Each generated content page MUST identify its maintained source path and content kind so
  readers can distinguish project documentation from feature specifications and trace the page back
  to its authority.
- **FR-014**: The site MUST apply a consistent project-wide reading and navigation experience to both
  content collections without changing their canonical Markdown meaning.
- **FR-015**: The site MUST support project-wide discovery across architecture, documentation, and
  feature specification content.
- **FR-016**: Supported relative links within and between the three content collections MUST resolve to
  the corresponding site pages while retaining an explicit path back to the source.
- **FR-017**: Broken internal links, unreadable sources, invalid required metadata, and route collisions
  MUST stop a successful build and identify the affected source, conflicting target when applicable,
  and reason.
- **FR-018**: Draft or otherwise non-final feature specifications MUST remain discoverable and MUST
  display their recorded status; publication MUST NOT imply approval or implementation agreement.
- **FR-019**: Preview and production build operations MUST use the same content inclusion, routing,
  navigation, and validation rules.
- **FR-020**: Repeated builds from identical maintained sources and configuration MUST produce the same
  page inventory, navigation relationships, and source-to-page mapping without an LLM call.
- **FR-021**: Build output, staged content, navigation indexes, and other generated projections MUST be
  disposable and MUST NOT become maintained documentation or specification sources.
- **FR-022**: Every generated page MUST record enough provenance to distinguish its source collection
  and locate the corresponding maintained file.
- **FR-023**: The project MUST document how a contributor installs the docsite prerequisites, starts a
  local preview, performs a production build, and diagnoses content validation failures.
- **FR-024**: Empty-source states MUST produce a valid explanatory landing experience or an actionable
  diagnostic and MUST NOT fabricate documentation or feature content.
- **FR-025**: A failed build MUST NOT be reported as a complete, publishable project site or silently
  replace the last output known to have completed successfully.
- **FR-026**: The generated site MUST remain a read-only projection; users MUST edit project meaning in
  `docs/`, `specs/`, or the other maintained sources identified by provenance rather than in generated
  pages.
- **FR-027**: The site MUST include every eligible module and boundary-contract Markdown source found
  recursively under `specs/` without copying those authorities into `docs/` or `docsite/`.
- **FR-028**: Architecture navigation MUST mirror the maintained hierarchy and expose stable entity ID,
  kind, owning module or parent when applicable, and project-relative provenance.
- **FR-029**: When an architecture Markdown source declares an Archify JSON view, its page MUST embed
  the corresponding delivered HTML in a sandbox and provide a direct link plus textual source
  provenance outside the embedded view.
- **FR-030**: Missing, invalid, escaping, or unpublishable declared architecture views MUST stop a
  successful build with an actionable deterministic diagnostic.
- **FR-031**: Architecture Markdown, Archify JSON, and delivered Archify HTML MUST remain separate
  authorities and projections: publication MUST NOT rewrite maintained sources or treat generated HTML
  as editable intent.
- **FR-033**: This feature MUST maintain a text-backed Archify sequence view that identifies the
  components invoked by the publication scenario, the information passed at documented boundaries,
  the candidate failure boundary, and the generated output with deterministic provenance and
  freshness validation. The canonical feature page MUST discover the declaration automatically,
  embed the interactive diagram with source provenance, and retain an open-standalone-view link.
- **FR-034**: The maintained Documentation collection MUST include a project overview that explains
  the problem Concorde addresses, its combination of spec-driven development and Architecture as
  Code, its hierarchical abstraction model, and the responsibilities it leaves to Spec Kit and
  adjacent tools.
- **FR-035**: The maintained Documentation collection MUST include a quick-start path that lets a
  reader preview the project read model and follow the supported installation and first-feature path,
  including prerequisites, verification, and approval boundaries.
- **FR-036**: The maintained Documentation collection MUST explain the different authority and
  lifecycle of architecture sources, feature specifications, permanent feature designs, contracts,
  diagrams, current implementation attempts, workflow control, code/tests, and generated
  projections.
- **FR-037**: The maintained Documentation collection MUST provide a project structure guide that
  maps the major workspace locations to their purpose, ownership, maintenance status, and correct
  edit path.
- **FR-038**: The maintained Documentation collection MUST explain the end-to-end Concorde workflow
  from root architecture and feature placement through specification, architecture review,
  implementation, validation, hardening, and publication.
- **FR-039**: The maintained Documentation collection MUST distinguish normal Spec Kit lifecycle
  phases from Concorde-specific operations and distinguish agent-facing command presentation from
  adapters, launchers, and deterministic runtime behavior.
- **FR-040**: The Documentation landing page MUST provide a progressive reading path through the
  framework guides, and each guide that summarizes normative behavior MUST link readers to the
  relevant canonical architecture or feature sources for complete authority.

### Key Entities

- **Project Document**: A maintained Markdown file under `docs/`, identified by its source path, title,
  navigation metadata, links, and content.
- **Framework Guide**: A project document that progressively explains adoption, concepts, workflow,
  or contribution without replacing the normative architecture and feature sources it references.
- **Feature Specification**: A feature's canonical `spec.md` under `specs/`, identified by its feature
  directory, stable ID, title, lifecycle status, requirements, scenarios, and source path.
- **Architecture Source**: Maintained module or boundary-contract Markdown under `specs/`, identified
  by stable ID, kind, hierarchy metadata, source path, and an optional adjacent Archify JSON view.
- **Content Page**: A read-only site projection of one maintained source, with a stable route, content
  kind, navigation placement, and provenance.
- **Navigation Entry**: A relationship that places a content page in either the Documentation or
  Features hierarchy while preserving meaningful source organization.
- **Build Manifest**: The deterministic inventory that maps every included maintained source to its
  content page and records exclusions, collisions, and validation outcomes.
- **Supplemental Feature Diagram**: A maintained, text-backed explanation of the publication
  invocation path whose generated HTML is a reproducible, non-authoritative projection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a clean checkout with prerequisites available, a contributor can follow the project
  instructions and open a complete local site in under 5 minutes.
- **SC-002**: 100% of eligible architecture sources, project documents, and canonical feature specifications are reachable
  from the generated navigation and represented exactly once in the build manifest.
- **SC-003**: A contributor can add one valid project document or feature specification and see it in
  the next successful site build without copying its content or registering the page elsewhere.
- **SC-004**: Two independent builds from identical inputs produce identical page inventories,
  navigation relationships, and source-to-page mappings.
- **SC-005**: In validation tests, 100% of broken internal links, unreadable sources, missing required
  identity metadata, and route collisions cause a failed build that names the affected source.
- **SC-007**: Every displayed feature specification visibly identifies its title, source, stable ID,
  and recorded lifecycle status when present, with zero cases in which a draft is presented as final.
- **SC-008**: A repository check after preview and production builds finds zero generated or copied
  content changes under the maintained `docs/` and `specs/` source directories.
- **SC-009**: The publication sequence view passes all deterministic Archify showcase, provenance,
  and freshness checks with zero errors or warnings and appears automatically on the canonical
  Feature 002 page with source provenance and a standalone-view link.
- **SC-010**: From the Documentation landing page, a first-time reader can reach the quick start,
  framework overview, specification model, project structure, workflow, and command guidance in no
  more than two navigation actions per destination.
- **SC-013**: Every maintained framework guide that summarizes a normative workflow or boundary
  provides at least one working link to its canonical architecture or feature authority, with zero
  links to temporary implementation artifacts presented as permanent authority.

## Assumptions

- "The entire project" means three maintained human-facing content views over two source roots:
  architecture and feature specifications under `specs/`, plus recursively discovered project
  Markdown under `docs/`. Archify JSON remains structural authority and its generated HTML is
  embedded from disposable projection output; API references, source-code extraction, and test reports
  remain later features.
- A canonical feature specification is the feature directory's root `spec.md`. Temporal plans,
  tasks, and evidence live below `implementation/`; checklists and other supporting artifacts remain
  outside the first site's Features collection.
- Docusaurus is a required product constraint selected by the maintainer. The implementation plan may
  choose its supported configuration and content-integration mechanisms while preserving the source
  ownership rules in this specification.
- Local preview and reproducible production build are in scope. Public hosting, deployment,
  authentication, analytics, comments, content editing, and versioned release archives are out of
  scope for this feature.
- The site may create disposable staging and build output beneath its own ignored workspace, provided
  those projections are reproducible and never become canonical content.
- The existing root architecture view's `publish-architecture` scenario provides the current-level
  structural trace for this project-wide feature. The feature-owned publication sequence explains
  deeper invocation without expanding child internals in the root view; the Documentation-module
  feature and view remain the adjacent architectural refinement.
- The hand-written Documentation collection is intentionally explanatory and task-oriented. It may
  summarize README material and canonical specifications for a progressive reader journey, but
  architecture and feature sources remain authoritative when wording or detail disagrees.
