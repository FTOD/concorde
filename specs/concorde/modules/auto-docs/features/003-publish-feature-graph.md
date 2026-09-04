---
id: feature.auto-docs.publish-feature-graph
kind: feature
module: module.concorde.auto-docs
related_features:
  - id: feature.auto-docs.publish-project-docsite
    relation: depends_on
  - id: feature.concorde.define-project-ontology
    relation: depends_on
  - id: feature.understanding.validate-architecture
    relation: relates_to
interfaces:
  provided:
    - interface.auto-docs.feature-graph
  required:
    - contract.auto-docs.build-manifest
evidence_status: unknown
---

# Feature Design: Publish the Feature Graph

**Created**: 2026-09-04

**Input**: Give a programmer a knowledge-graph-like view of how features relate, generated from the
specification hierarchy: first one JSON relationship description derived from feature front matter,
then a diagram in the docsite built from that description. Archify is unsuitable for the derived
graph because it has no graph layout and its showcase checks target curated views of at most
about twelve nodes; the graph must scale past that by layering, not by cramming.

## Outcome and Scope

**Outcome**: A reader of the published docsite opens one `/graph` page and sees every published
feature as a node grouped by its module, connected by typed edges that say how features relate:
`composes`, `refines`, `depends_on`, `relates_to`, and interface-derived `requires` edges labeled
with the interface each dependency crosses. The same facts are available as one versioned JSON
document, `feature-graph.json`, and every feature page shows its depth-one neighborhood beside the
related-feature list.

**In scope**:

- Feature Graph 1: a deterministic JSON projection of feature nodes, module groups, and typed edges
  derived only from validated feature front matter (`module`, typed `related_features`, and
  `interfaces.provided`/`interfaces.required` ownership), with generator and source provenance.
- Publication-time validation that every edge endpoint resolves, every relation uses the shared
  vocabulary, each required interface has exactly one provider, and each directional family
  (`composes`, `refines`, `depends_on`, `requires`) is acyclic.
- The `/graph` page: an interactive client-side view with module compound nodes, edge-kind and
  module filters, search, neighbor highlighting with links to feature pages, a legend, and a
  textual edge table that carries the same facts without JavaScript.
- A depth-one neighborhood view on each feature page and a relation label on each related-feature
  entry.
- Registration of the graph document in the Build Manifest so publication provenance covers it.

**Out of scope**:

- Editing relations from the site; feature files remain the only authority.
- Rendering the derived graph with Archify or maintaining it as an architecture-owned diagram.
- Entity-level or code-level knowledge graphs; those remain the alignment explorer's domain.
- Inferring relation types from prose; a relation is typed only when its front matter says so.

## Usage

A maintainer types each `related_features` entry as `{id, relation}` while specifying a feature.
Publication derives the graph, fails on an unknown relation, an unresolved endpoint, a duplicate
interface provider, or a cycle in a directional family, and otherwise writes `feature-graph.json`
beside `build-manifest.json`. A programmer opens `/graph`, filters to `requires` and `composes`,
searches for a feature, and follows the highlighted neighbors to their pages; on any feature page the
neighborhood view shows the same edges for that feature only.

### Edge Cases

- A project with a root architecture and no features publishes an empty graph and an empty-state
  `/graph` page; publication still succeeds.
- A reciprocal declaration (`A composes B` and `B composed_by A`) is one edge whose `declared_by`
  lists both features; a plain string entry is read as `relates_to`.
- Two features that declare contradictory directional relations (`A composes B` and `B composes A`)
  form a cycle and fail publication with the offending edge list.
- A feature that requires an interface no published feature provides, and that declares no external
  provider block, fails publication; an external provider yields no edge.
- JavaScript disabled or a server-side render leaves the textual edge table and the empty canvas
  placeholder; nothing else on the page depends on the client-only view.

## User Scenarios & Testing

### User Story 1 — See how features relate (Priority: P1)

A programmer new to the project opens `/graph`, sees module groups with their features, and reads
which features compose, refine, depend on, or require which others.

**Why this priority**: This is the orientation the graph exists to provide.

**Independent Test**: Build the docsite for this repository, open `/graph`, and verify the node
count equals the number of published features, every module is a group, and the legend, filters,
search, and edge table are present.

**Acceptance Scenarios**:

1. **Given** a validated docsite build, **When** `/graph` opens, **Then** every published feature is a
   node inside its module group and every derived edge is drawn with its kind.
2. **Given** the reader clicks one node, **When** the selection changes, **Then** its neighbors and
   their edges are highlighted, the detail panel names the feature and its outcome, and a link opens
   the feature page.
3. **Given** the reader unchecks `relates_to`, **When** the filter applies, **Then** only typed
   directional edges remain and isolated nodes stay visible.

### User Story 2 — Orient from one feature page (Priority: P2)

A programmer reading one feature sees its immediate neighborhood without leaving the page.

**Independent Test**: Open any feature page and verify the neighborhood view lists the same edges as
the global graph filtered to that feature, and that each related-feature entry shows its relation.

**Acceptance Scenario**:

1. **Given** a feature with typed relations, **When** its page renders, **Then** the neighborhood view
   shows the feature, each neighbor, and each edge kind, and the related-feature list labels each
   entry with its relation.

### User Story 3 — Trust the graph as a projection (Priority: P1)

A maintainer relies on the graph being derived, deterministic, validated, and traceable to sources.

**Independent Test**: Build twice without source changes and compare `feature-graph.json` byte for
byte; introduce a `composes` cycle in a fixture and verify publication fails naming the cycle.

**Acceptance Scenarios**:

1. **Given** unchanged sources, **When** the site builds twice, **Then** the two graph documents are
   identical and carry the same source digest.
2. **Given** a directional cycle or an unknown relation in a fixture, **When** publication validates,
   **Then** it fails with one finding per offending feature and promotes nothing.

## Interfaces

### `interface.auto-docs.feature-graph` — Feature Graph 1 document and page

- **Consumer**: Docsite readers, the `/graph` page, feature-page neighborhood views, and any tool that
  reads the published `feature-graph.json`.
- **Direction**: Validated content registry (feature front matter, module identity, interface
  ownership) to one JSON document plus one rendered page and per-feature views.
- **Entry points**: `entity.auto-docs.graph` derivation during publication; build output
  `feature-graph.json`; route `/graph`; `entity.auto-docs.neighborhood-view` on feature routes.
- **Inputs**: Every published feature's stable ID, title, module, outcome, evidence status (published
  under the graph `status` key), route, source path and digest; its typed `related_features`
  entries; its `interfaces.provided` and `interfaces.required`; every published module's ID, title,
  parent, and route.
- **Outputs**: `{schema_version: 1, generator: {name, version}, source_digest, modules: [{id, title,
  parent, route}], features: [{id, title, module, outcome, status, route, source_path,
  source_sha256}], edges: [{id, kind, source, target, interface?, declared_by: [...]}], counts:
  {features, modules, edges_by_kind}}`. Edge `kind` is one of `composes`, `refines`, `depends_on`,
  `relates_to`, or `requires`; inverse declarations (`composed_by`, `refined_by`,
  `depended_on_by`) normalize to the forward kind with source and target swapped; `relates_to`
  edges order source and target lexically; arrays are sorted by ID.
- **Obligations**: Derive only from validated front matter; never read prose; keep output
  deterministic and sorted; resolve every endpoint to a published feature; require the shared
  relation vocabulary; derive one `requires` edge per (feature, required interface) whose provider
  is one other published feature; reject cycles in each directional family; merge reciprocal
  declarations into one edge; write the document beside `build-manifest.json` and register its path
  in the manifest; render the same edges in the page's textual table; show an empty state for zero
  features.
- **Failures**: Unknown relation, unresolved endpoint, self-reference, required interface with zero
  or several published providers and no external provider block, or a directional cycle fails
  publication with sourced findings and leaves the last successful site in place.
- **Compatibility**: Feature Graph 1 is additive to Build Manifest 12, which registers
  `featureGraph: "feature-graph.json"`. Plain string `related_features` entries remain valid as
  `relates_to`. Cytoscape version and layout are renderer details that may change without changing
  the document.
- **Example**: `{"kind": "requires", "source": "feature.lifecycle.plan-attempt", "target":
  "feature.understanding.bound-planning-context", "interface":
  "contract.understanding.planning-context", "declared_by": ["feature.lifecycle.plan-attempt"]}` and
  `{"kind": "composes", "source": "feature.concorde.workflow", "target":
  "feature.lifecycle.specify-behavior", "declared_by": ["feature.concorde.workflow",
  "feature.lifecycle.specify-behavior"]}`.
- **Implementing entities**: `entity.auto-docs.registry`, `entity.auto-docs.graph`,
  `entity.auto-docs.feature-graph`, `entity.auto-docs.validation`, `entity.auto-docs.manifest`,
  `entity.auto-docs.publisher`, `entity.auto-docs.graph-page`, `entity.auto-docs.graph-view`,
  `entity.auto-docs.neighborhood-view`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.auto-docs.registry` | Parses typed `related_features` and interface ownership into the content registry. | Supplies the only inputs the graph derivation reads. |
| `entity.auto-docs.graph` | Derives Feature Graph 1 nodes, module groups, and typed edges. | Normalizes inverse relations, merges reciprocal declarations, derives `requires` edges, and orders everything deterministically. |
| `entity.auto-docs.feature-graph` | Defines the versioned JSON shape. | Validated by schema in tests and by the publisher before promotion. |
| `entity.auto-docs.validation` | Rejects unknown relations, unresolved endpoints, duplicate providers, and directional cycles. | Fails publication before any candidate is built. |
| `entity.auto-docs.manifest` | Registers the graph document in Build Manifest 12. | Keeps provenance for the graph alongside pages and diagrams. |
| `entity.auto-docs.publisher` | Writes `feature-graph.json` into the candidate and promotes it atomically with the site. | Same all-or-nothing promotion as pages and diagrams. |
| `entity.auto-docs.graph-page` | Renders `/graph` with filters, search, legend, detail panel, and the textual edge table. | Reads the graph from plugin global data; the canvas is client-only. |
| `entity.auto-docs.graph-view` | Draws nodes, compound module groups, and typed edges with Cytoscape. | Shared by the global page and the neighborhood view. |
| `entity.auto-docs.neighborhood-view` | Shows one feature's depth-one neighborhood on its page. | Filters the same graph to one node and its edges. |
| `entity.auto-docs.cytoscape` | Client-side graph rendering and layout library. | Loaded only in the browser. |
| `entity.concorde.specification` | Supplies the feature front matter the graph is derived from. | Never edited by publication. |

## Related Features

- `feature.auto-docs.publish-project-docsite` is depended on: the graph is derived inside the same
  registry, validated by the same publication gate, registered in the same manifest, and promoted
  with the same site.
- `feature.concorde.define-project-ontology` is depended on for the typed related-feature vocabulary
  and the rule that directional families stay acyclic.
- `feature.understanding.validate-architecture` relates to this feature: both enforce the same
  vocabulary and acyclicity, one over the maintained sources and one at publication.

## Requirements

### Functional Requirements

- **FR-001**: Publication MUST derive Feature Graph 1 from the validated registry only, using each
  feature's module, typed `related_features`, and `interfaces.provided`/`interfaces.required`.
- **FR-002**: Every `related_features` entry MUST be either a stable feature ID or an object with
  `id` and `relation`; a plain ID reads as `relates_to`; `relation` MUST be one of `composes`,
  `refines`, `depends_on`, `composed_by`, `refined_by`, `depended_on_by`, or `relates_to`.
- **FR-003**: Inverse relations MUST normalize to their forward kind; reciprocal declarations of one
  edge MUST merge into one edge whose `declared_by` lists every declaring feature; `relates_to`
  edges MUST be undirected with lexically ordered endpoints.
- **FR-004**: One `requires` edge MUST exist for each (feature, required interface) whose provider is
  exactly one other published feature; an interface with an external provider block yields no edge;
  zero or several published providers MUST fail publication.
- **FR-005**: The `composes`, `refines`, `depends_on`, and `requires` families MUST each be acyclic;
  a cycle MUST fail publication naming every feature on it.
- **FR-006**: The document MUST be deterministic and sorted, carry generator name/version and the
  source digest of every contributing feature, and be written as `feature-graph.json` beside
  `build-manifest.json`; Build Manifest 12 MUST register its path.
- **FR-007**: The `/graph` page MUST group features by module, draw every edge with a visible kind,
  offer edge-kind and module filters and search, highlight a selected node's neighbors, link every
  node to its feature page, and render a textual edge table with source, target, kind, and interface.
- **FR-008**: Every feature page MUST render the feature's depth-one neighborhood and label each
  related-feature entry with its relation.
- **FR-009**: A project with zero published features MUST publish an empty graph and an empty-state
  page without failing.
- **FR-010**: The client-side view MUST be loaded only in the browser; server-side rendering MUST
  still emit the page, the textual table, and the placeholder.

### Non-Functional Requirements

- **NFR-001**: Deriving and validating the graph for one hundred features MUST complete within the
  existing publication budget with no network access.
- **NFR-002**: The page MUST remain usable with keyboard navigation and the textual table MUST be
  reachable by assistive technology.

### Assumptions

- Cytoscape with the fcose layout is an adequate renderer for up to a few hundred nodes; module
  compound nodes can collapse to keep larger projects readable.
- The docsite is the packaged template for every project, so the graph page ships to every project
  without Concorde-specific assumptions.

## Success Criteria

- **SC-001**: Two builds from unchanged sources produce byte-identical `feature-graph.json`.
- **SC-002**: For this repository the graph publishes every feature as a node, every module as a
  group, every typed relation, and every interface-derived `requires` edge, with zero validation
  findings.
- **SC-003**: A fixture with one directional cycle and a fixture with an unknown relation each fail
  publication with a sourced finding.
- **SC-004**: A project holding only Initialization Proposal 3 output passes `npm run check` with an
  empty graph.
- **SC-005**: Unit, contract, repository, and production-build docsite tests cover derivation,
  schema, counts, page emission, and determinism.
