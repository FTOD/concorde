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
diagrams:
  - source: specs/concorde/features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json
    role: supplemental
    kind: sequence
    scenarios:
      - publish-architecture
    output: generated/architecture/project-docsite-publication-flow.html
evidence_status: verified
canonical_design: specs/concorde/features/002-create-project-docsite/design.md
---

# Feature Design: Create Unified Project Docsite

**Feature Branch**: Not created; no `before_specify` branch hook is configured

**Created**: 2026-08-19

**Revised**: 2026-08-29

**Status**: Implemented; build-owned Archify delivery and clean-checkout publication verified

**Input**: User description: "Create an independent root `docsite/` containing Docusaurus
configuration and formatting, keep actual Markdown documentation in a separate root `docs/`, and
present those documents, feature specifications under `specs/`, and Concorde architecture sources
and views as one project website. Maintain a useful custom documentation baseline—including a quick
start, project description, conceptual model, project structure, workflow, and command guidance—so
the generated site teaches the Concorde framework rather than presenting specifications alone."

**Revision Input**: "Make Archify validation and HTML delivery part of building the Docusaurus site
so a clean checkout does not depend on committed or manually pre-generated diagram output. Install
Archify through its official project-local skill mechanism so preview, build, and deployment require
no machine-specific renderer environment variable."

**Revision Input**: "Although architecture and feature sources share the same `specs/` packages,
publish them as independent read models: Architecture follows the module hierarchy, while Features
follows the feature hierarchy without exposing architecture storage directories as feature
navigation."

**Revision Input**: "Improve the project README so key features and Concorde commands appear at the
beginning, and publish that same maintained README as the generated Docusaurus site's home page
instead of maintaining a separate site-only landing page."

## Scenario and Component Diagram

`diagrams/project-docsite-publication-flow.json` is a maintained, supplemental sequence view for the
`publish-architecture` scenario. Its generated projection is
`generated/architecture/project-docsite-publication-flow.html`. The view shows the build command
invoking the source registry, Archify delivery, disposable content materialization, Docusaurus build,
candidate validation, and atomic publisher before a programmer or agent browses the result.

The diagram explains component involvement and call order; the user stories and requirements below
remain the behavioral authority, and `specs/concorde/architecture/diagrams/level-view.json` remains the bounded root
architecture view.

This feature does not add a separate core component diagram because the bounded root view already
shows Documentation, Scripts, Skills, the coding agent, and the maintainer at
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
2. **Given** features specified at the root and inside nested module packages, **When** the visitor
   browses Features, **Then** feature navigation follows feature identity and explicit feature
   containment without presenting architecture directories or modules as feature categories.
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

**Independent Test**: Change the title, status, and one requirement in an existing `design.md`; add a
feature beneath a nested module and a sub-feature beneath a parent feature; rebuild the site and
confirm that all pages reflect their canonical files, the sub-feature is nested under its parent,
and no Architecture or module-storage category appears in Features.

**Acceptance Scenarios**:

1. **Given** a feature directory containing a canonical `design.md`, **When** the site is rebuilt,
   **Then** the feature appears in the Features area with its current title, status, identifier, and
   full specification content.
2. **Given** a canonical feature specification changes, **When** the next build succeeds, **Then** its
   published page reflects that change without requiring a synchronized copy.
3. **Given** a feature workspace also contains an `attempt/` directory, root checklists, or
   other supporting artifacts,
   **When** the first version of the site is built, **Then** those files are not presented as canonical
   feature specifications.
4. **Given** a feature is physically stored beneath a module's architecture package, **When** its
   feature page and navigation entry are generated, **Then** its providing module and refinement
   relationships are available as metadata or links but do not become parent categories in the
   feature hierarchy.

---

### User Story 4 - Verify a Reproducible Site Build (Priority: P4)

As a maintainer, I can preview and build the complete site from the independent `docsite/` project and
receive actionable failures for invalid content so that only a complete, traceable read model is
treated as publishable.

**Why this priority**: A repeatable build and explicit failure behavior make the website trustworthy
and suitable for later continuous integration and publication work.

**Independent Test**: Remove all disposable diagram deliveries, build the same unchanged content
twice, and compare the diagram and page inventories; then add an invalid diagram, a broken link, and
a duplicate page identity and confirm that each failure names the affected source and prevents the
incomplete result from being reported as successful.

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
6. **Given** a clean checkout containing maintained diagram JSON but no delivered diagram HTML,
   **When** preview or production publication starts, **Then** every declared diagram is validated and
   delivered before the site consumes it, without a separate manual rendering step.
7. **Given** a maintained diagram changes or a previous delivery is stale, **When** the next build
   runs, **Then** the build replaces the disposable delivery from the current source and publishes
   only the matching result.
8. **Given** a diagram is invalid or its renderer fails, **When** the build runs, **Then** publication
   stops with an actionable source-specific diagnostic and does not silently reuse an older delivery
   or replace the last successful site.
9. **Given** preview or production publication completes, **When** repository state is inspected,
   **Then** generated diagram HTML and machine-local visual-check evidence remain disposable,
   non-authoritative, and excluded from version control.

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
   project structure guide, Concorde workflow, and command reference without browsing repository files.
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

---

### User Story 6 - Start from One Project Introduction Everywhere (Priority: P1)

As a prospective user or contributor, I see the same project introduction in the repository and at
the generated site's root so that I can learn Concorde's value and available commands immediately
without reconciling two independently maintained home pages.

**Why this priority**: The repository README and public site root are the two most likely first
contacts with the project. They must share one maintained authority and put the information needed
to evaluate and operate Concorde before project history and contributor detail.

**Independent Test**: Change a heading, feature summary, and command entry in the root `README.md`,
build the site, and verify that `/` contains the changed content, reports `README.md` as its source,
and has no separate hand-authored landing-page copy.

**Acceptance Scenarios**:

1. **Given** a visitor opens either the repository README or the generated site root, **When** they
   scan the opening sections, **Then** they encounter the project summary, key features, and the full
   Concorde-specific command set before project status or detailed installation instructions.
2. **Given** the maintained root `README.md` changes, **When** the next site build succeeds, **Then**
   `/` reflects that exact maintained content without a second canonical homepage edit.
3. **Given** links in `README.md` target project documentation, architecture, features, or external
   resources, **When** the page is read in the repository or generated site, **Then** supported links
   resolve appropriately in both contexts and broken internal links fail site validation.
4. **Given** the generated homepage is included in a successful publication, **When** a reader or
   maintainer inspects it, **Then** it identifies `README.md` as the maintained source and the build
   manifest maps that source to exactly one `/` route.

### Edge Cases

- `docs/` exists but contains no eligible Markdown pages, or `specs/` contains no canonical feature
  specifications.
- A documentation file or feature specification has no display title, duplicate navigation identity,
  invalid metadata, or a path that would map to an existing site route.
- A feature workspace contains root `design.md` and checklists alongside nested implementation plans,
  tasks, evidence, generated files, or unrelated Markdown.
- Documents in different source collections have the same filename or title.
- A relative link crosses from `docs/` to `specs/`, from a feature specification to `docs/`, or points
  to a source that is not included in the site.
- A source is renamed or removed after a prior build, leaving a formerly valid route or link.
- A draft feature specification is present; it remains visible with its draft status rather than being
  silently omitted or presented as approved.
- Site output or staging content from an earlier build is stale, incomplete, or accidentally placed
  beside canonical Markdown sources.
- A clean checkout has no `generated/` directory, or a previous checkout has stale or extra diagram
  deliveries that no maintained declaration owns.
- The diagram renderer is missing, incompatible, exits unsuccessfully, emits malformed output, or
  attempts to write outside the disposable delivery root.
- Repository paths contain spaces or non-ASCII characters that are valid for maintained sources.
- The Documentation collection technically publishes but contains only a landing page, forcing new
  readers to infer the framework from normative specifications.
- A guide repeats a setup detail that changes while its linked canonical specification remains
  current, creating an obvious documentation-freshness disagreement.
- A reader mistakes installed skills, workflow-control state, temporary implementation files, or
  generated output for durable project intent.
- Two features at different module levels use the same numeric directory prefix or short name; their
  stable IDs remain distinct and their generated feature routes do not collide.
- A feature refines behavior at an adjacent module level but is not a contained sub-feature; the site
  shows the refinement as a relationship without inventing a parent-child navigation relationship.
- The README contains repository-relative links whose browser targets must be rewritten for the site
  without changing the maintained Markdown.
- A generated-site configuration or source page also claims `/`, colliding with the README homepage.
- The README is renamed, unreadable, or missing; publication must not silently substitute a stale or
  site-only introduction.

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
- **FR-006**: The site MUST include the canonical `design.md` for every feature directory under `specs/`.
- **FR-007**: The first version MUST NOT present plans, tasks, checklists, or other supporting files as
  feature specifications merely because they are stored under `specs/`.
- **FR-008**: Content collection and presentation MUST NOT modify files under `docs/` or `specs/`.
- **FR-009**: The site MUST publish the root `README.md` as the project landing page at `/`, with
  distinct, clearly labeled entry points for Architecture, project Documentation, and Features.
- **FR-010**: Documentation navigation MUST preserve the meaningful hierarchy expressed by paths and
  navigation metadata under `docs/`.
- **FR-011**: Feature navigation MUST identify each specification by its feature title, MUST expose
  its stable ID and lifecycle status when those values are present, and MUST derive hierarchy only
  from explicit feature containment rather than module containment or source-directory wrappers.
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
  implementation, validation, acceptance, and publication.
- **FR-039**: The maintained Documentation collection MUST distinguish normal Spec Kit lifecycle
  phases from Concorde-specific operations and distinguish agent-facing command presentation from
  adapters, launchers, and deterministic runtime behavior.
- **FR-040**: The Documentation landing page MUST provide a progressive reading path through the
  framework guides, and each guide that summarizes normative behavior MUST link readers to the
  relevant canonical architecture or feature sources for complete authority.
- **FR-041**: Preview and production build entry points MUST discover every declared module and
  feature-owned Archify JSON source and MUST validate and deliver its standalone HTML before content
  registry validation or site rendering consumes that delivery.
- **FR-042**: A clean checkout containing maintained sources and documented prerequisites MUST build
  the complete site without committed diagram HTML, visual-check receipts, or a separate manual
  Archify command.
- **FR-043**: Diagram delivery MUST use a deterministic, compatibility-checked Archify renderer,
  resolved from the officially installed project-local `.agents/skills/archify` package, preserve the
  declared diagram kind and output mapping, and expose source-specific validation or delivery
  diagnostics on failure.
- **FR-044**: A failed or incomplete diagram delivery MUST stop preview or production publication,
  MUST NOT fall back to stale HTML, and MUST NOT replace the last successful published site.
- **FR-045**: Generated diagram HTML, visual-check receipts, captures, contact sheets, and site build
  products MUST remain reproducible disposable outputs excluded from version control; maintained
  Archify JSON and its textual counterpart remain the reviewable sources.
- **FR-046**: Build manifests and any retained deterministic diagram receipts MUST use normalized
  project-relative provenance and MUST NOT persist machine-specific absolute workspace paths.
- **FR-047**: Local preview, production build, tests, and repository deployment MUST consume the same
  version-controlled project-local Archify skill without requiring a machine-specific renderer
  environment variable, global CLI, additional renderer checkout, or agent-home installation.
- **FR-048**: Architecture and Features MUST be generated as independent semantic projections even
  when their canonical sources occupy the same recursive `specs/` packages: Architecture navigation
  follows the declared module hierarchy, while Features navigation follows feature identity and
  explicit parent/sub-feature containment.
- **FR-049**: Architecture storage segments and module identities, including `architecture/`,
  `modules/`, and module-local `features/` wrappers, MUST NOT appear as hierarchy categories or route
  parents in the Features collection. A feature's providing module and adjacent-level `refines`
  relationships MUST remain available as page metadata and links without being treated as feature
  containment.
- **FR-050**: Feature page routes MUST be deterministic and collision-free from stable feature
  identity and explicit containment, independent of the module storage path; supported links from
  architecture, documentation, and other feature pages MUST resolve to those routes.
- **FR-051**: The root `README.md` MUST be the single maintained source for both the repository
  introduction and the generated site's `/` homepage; `docsite/` MUST NOT maintain a separate
  hand-authored homepage that duplicates its project narrative.
- **FR-052**: The README's opening content MUST present, in this order, a concise project explanation,
  a scannable key-feature summary, and the complete Concorde-specific command set before project
  status, release caveats, detailed installation, development, or docsite-operation sections.
- **FR-053**: The generated homepage MUST preserve the README's supported Markdown meaning and MUST
  rewrite supported repository-relative links to their generated-site routes without modifying the
  maintained README or breaking its repository rendering.
- **FR-054**: The source registry, validation, build manifest, search/discovery behavior, and page
  provenance MUST treat `README.md` as one eligible project document mapped to exactly one `/` route.
- **FR-055**: A missing or unreadable root README, an invalid supported README link, or any competing
  homepage route MUST stop publication with an actionable diagnostic and MUST NOT replace the last
  successful site.

### Key Entities

- **Project Document**: A maintained Markdown file under `docs/`, identified by its source path, title,
  navigation metadata, links, and content.
- **Framework Guide**: A project document that progressively explains adoption, concepts, workflow,
  or contribution without replacing the normative architecture and feature sources it references.
- **Project README**: The root maintained Markdown introduction, optimized for repository readers and
  projected unchanged in meaning as the generated site's `/` homepage, with one manifest entry and
  explicit source provenance.
- **Feature Specification**: A feature's canonical `design.md` under `specs/`, identified by its feature
  directory, stable ID, title, lifecycle status, requirements, scenarios, and source path.
- **Architecture Source**: Maintained module or boundary-contract Markdown under `specs/`, identified
  by stable ID, kind, hierarchy metadata, source path, and an optional adjacent Archify JSON view.
- **Content Page**: A read-only site projection of one maintained source, with a stable route, content
  kind, navigation placement, and provenance.
- **Navigation Entry**: A relationship that places a content page in its public semantic hierarchy:
  documentation paths for Documentation, module containment for Architecture, and explicit feature
  containment for Features, independent of shared physical source placement.
- **Build Manifest**: The deterministic inventory that maps every included maintained source to its
  content page and records exclusions, collisions, and validation outcomes.
- **Diagram Delivery Set**: The complete, deterministic set of standalone HTML projections produced
  from all currently declared Archify JSON sources for one preview or production build.
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
- **SC-014**: From a clean checkout with zero delivered diagram files, one documented build command
  validates and delivers 100% of declared diagrams and publishes every corresponding standalone and
  embedded route without manual preparation.
- **SC-015**: In tests covering missing tools, invalid sources, escaping outputs, renderer failures,
  stale deliveries, and duplicate outputs, 100% of cases fail before publication with the responsible
  maintained source identified and zero fallback to prior diagram bytes.
- **SC-016**: After preview and production builds, version-control status reports zero tracked or
  newly trackable diagram deliveries, visual-check evidence, or machine-specific absolute paths.
- **SC-017**: Across fixtures containing root features, module-level features, and one level of
  sub-features, 100% of feature navigation entries contain no architecture or module-storage
  categories, and every sub-feature appears under exactly its declared parent feature.
- **SC-018**: Every eligible feature has exactly one deterministic, collision-free route derived
  independently of its module storage path, while 100% of supported inbound links resolve to the
  resulting page.
- **SC-019**: The repository and generated-site root present the same maintained README content, and
  a content change requires exactly one source edit to `README.md` before both surfaces agree.
- **SC-020**: A reader can identify at least five key capabilities and all five Concorde-specific
  command surfaces within the README's first three substantive sections, before encountering project
  status or installation detail.
- **SC-021**: The build manifest contains exactly one `README.md` entry at `/`, the generated homepage
  visibly identifies that source, and no other source or hand-written site page claims `/`.
- **SC-022**: In automated cases for a missing README, a broken supported internal README link, and a
  competing root route, 100% of builds fail with an actionable diagnostic before publication.

## Assumptions

- "The entire project" means three maintained human-facing content views over the root README and
  two recursive source trees: the project introduction in `README.md`, architecture and feature
  specifications under `specs/`, and project guides under `docs/`. Archify JSON remains structural
  authority and its generated HTML is embedded from disposable projection output; API references,
  source-code extraction, and test reports remain later features.
- A canonical feature specification is the feature directory's root `design.md`. Temporal plans,
  tasks, and evidence live below `attempt/`; checklists and other supporting artifacts remain
  outside the first site's Features collection.
- Docusaurus is a required product constraint selected by the maintainer. The implementation plan may
  choose its supported configuration and content-integration mechanisms while preserving the source
  ownership rules in this specification.
- Local preview and reproducible production build are in scope. Public hosting, deployment,
  authentication, analytics, comments, content editing, and versioned release archives are out of
  scope for this feature.
- The Archify renderer is installed through the official project-local skills mechanism and retained
  at `.agents/skills/archify`; the build verifies that package rather than assuming an agent-home or
  global executable.
- The site may create disposable staging and build output beneath its own ignored workspace, provided
  those projections are reproducible and never become canonical content.
- Public navigation is a semantic read model rather than a literal directory browser. Feature
  containment is defined only by the canonical parent/sub-feature relationship; module placement and
  adjacent-level refinement remain cross-links, not parents in the Features hierarchy.
- The existing root architecture view's `publish-architecture` scenario provides the current-level
  structural trace for this project-wide feature. The feature-owned publication sequence explains
  deeper invocation without expanding child internals in the root view; the Documentation-module
  feature and view remain the adjacent architectural refinement.
- The hand-written Documentation collection is intentionally explanatory and task-oriented. It may
  summarize README material and canonical specifications for a progressive reader journey, but
  architecture and feature sources remain authoritative when wording or detail disagrees.
- The README remains conventional GitHub-flavored Markdown without site-only imports or authored
  React components. The generated site may stage a disposable metadata wrapper or rewritten-link
  projection so long as the visible narrative and authority remain the root README.
