---
title: Project Ontology and Terminology
sidebar_position: 3.5
---

# Project Ontology and Terminology

**Status**: Draft shared project ontology  
**Ontology version**: `1.1.0-draft`  
**Concorde scope**: the complete maintained project hierarchy  
**Understand Anything baseline**: commit
[`ba450c43425f3de6d43daf76526950ad8ca93536`](https://github.com/Egonex-AI/Understand-Anything/tree/ba450c43425f3de6d43daf76526950ad8ca93536)

This document defines the terminology needed to describe Concorde, the pinned Understand Anything
(UA) graph model, and the semantic relationships between them. It is shared across the project; it
is not owned by Alignment Explorer or by any single feature.

The two ontologies remain distinct. UA does not become Concorde's ontology, and Concorde entities do
not become UA entities merely because a renderer uses UA node and edge types. The adapter
representation profile near the end is one application of the relationship model, not the ontology's
primary purpose.

## 1. Scope and authority

This ontology is complete enough when a maintainer, coding agent, validator, or projection can:

- name every durable Concorde architectural and feature concept used by the workflow;
- distinguish source authority, lifecycle, current evidence, and generated read models;
- interpret every formal UA graph container, node type, edge type, graph-kind alias, and metadata
  family used by the pinned compatibility baseline;
- state whether two items are identical, represented, correlated, realized, evidenced, contradictory,
  or merely suggested as similar; and
- explain how a Concorde entity may be rendered through UA without claiming semantic equivalence.

It intentionally does not inventory every source-code class, function, or call. UA may discover those
implementation entities, while Concorde architecture records the responsibilities and promises that
remain meaningful above individual code elements.

### Authority boundaries

| Question | Authority |
|---|---|
| What Concorde's workflow principles require | `.specify/memory/constitution.md` |
| What one module owns and where its boundary lies | That module's `module.md`, boundary contracts, and maintained level views |
| What one feature must do | That feature's `design.md` |
| How an accepted implementation realizes a feature | That feature's `implementation.md` |
| What shared Concorde terminology and relationship names mean | This project ontology |
| What the UA baseline accepts and normalizes | Pinned upstream [`types.ts`](https://github.com/Egonex-AI/Understand-Anything/blob/ba450c43425f3de6d43daf76526950ad8ca93536/understand-anything-plugin/packages/core/src/types.ts) and [`schema.ts`](https://github.com/Egonex-AI/Understand-Anything/blob/ba450c43425f3de6d43daf76526950ad8ca93536/understand-anything-plugin/packages/core/src/schema.ts) |
| What bytes cross the Alignment Explorer boundary | Its normative contract schemas and examples |
| What the code currently does | Source code and executable evidence |

This document may define a shared class such as **Feature** or **Evidence**, but it cannot silently add
behavior to an individual feature. A contract schema may define serialized fields, but it cannot
change the meaning of a term defined here without an ontology revision. When maintained authorities
disagree, validation exposes the conflict; it does not choose a convenient winner.

## 2. Namespaces and modeling rules

The prefixes below are conceptual namespaces. They make statements readable; they do not require an
RDF implementation.

| Prefix | Meaning | Examples |
|---|---|---|
| `concorde:` | Concorde classes, relationships, and stable project identities | `concorde:Feature`, `feature.concorde.workflow` |
| `ua:` | Formal UA graph classes and enum values at the pinned revision | `ua:GraphNode`, `ua:concept`, `ua:depends_on` |
| `alignment:` | Cross-ontology relationships and evidence-qualified alignment records | `alignment:representedAs`, `alignment:evidencedBy` |
| `artifact:` | A path-identified maintained, executable, temporal, or generated artifact | `artifact:docs/ontology.md` |

Five rules govern every cross-ontology statement:

1. **Class is not instance**: `concorde:Feature` is a class; `feature.concorde.explore-alignment` is
   one instance.
2. **Identity is explicit**: equal labels, similar summaries, or the same word such as "module" do
   not establish identity.
3. **Representation is not equivalence**: `alignment:representedAs` means an adapter used a UA graph
   value to carry or render a Concorde entity. It does not mean both ontologies define the same class.
4. **Correlation is evidence-qualified**: a code node may correlate with zero, one, or many Concorde
   entities, and a Concorde entity may correlate with zero, one, or many implementation nodes.
5. **Projection has no source authority**: a generated graph, status badge, route, or report never
   becomes intent merely because it is easier to browse.

## 3. Concorde ontology

### 3.1 Core classes

| Class | Definition | Identity and owning authority |
|---|---|---|
| **Project** | One repository or workspace governed by one Concorde source profile and rooted specification hierarchy | Project path plus `.concorde/config.json`; the configured root module is its architecture entry point |
| **Module** | One architectural level with one responsibility, one boundary, immediate submodules, features specified at that level, provided/required contracts, and maintained level views | Stable `module.*` ID; its `module.md`, contracts, and level views own current-level architecture |
| **Root module** | The module selected by the source profile as the project-level entry point | `root_module_id`; "root" is a lookup role, not a special runtime component |
| **Feature** | One observable outcome specified exactly once at the level where all modules needed to explain it are visible | Stable `feature.*` ID; its `design.md` owns required behavior |
| **Sub-feature** | One immediate focused decomposition of a parent feature, sharing its specifying module and unable to contain another sub-feature | Stable `feature.*` ID plus `parent_feature`; its own `design.md` owns focused behavior |
| **Requirement** | One testable normative statement within a feature design | Feature-qualified `FR-NNN`; the feature ID is required because `FR-NNN` alone is not globally unique |
| **Scenario** | A representative, testable example of behavior and visible participation | Stable `scenario.*` ID or an explicitly prose-only feature scenario; never the complete definition of behavior |
| **Contract** | A human-readable boundary promise naming provider/consumer, flow, information, obligations, failure, compatibility, and evidence | Stable `contract.*` ID; contract document plus normative schema/example when custom |
| **External actor** | A human, system, service, or platform outside the current module boundary that participates through a contract | Stable external identity where maintained; role and counterparty are defined by the owning contract/view |
| **Command intent** | One stable agent operation whose platform-specific skill or slash-command presentation must preserve the same behavior | Canonical dotted ID such as `speckit.concorde.explore`; presentation spelling is not a second intent |
| **Source artifact** | A maintained file that owns or supports one kind of project fact | Canonical project-relative path plus its authority class |
| **Accepted realization** | The durable explanation of how the currently accepted implementation realizes one feature | The feature's `implementation.md`; its placeholder explicitly means no realization is accepted |
| **Attempt** | One temporary delivery proposal containing review state, research, plan, tasks, technical models, guides, and current evidence | The selected feature's `attempt/`; existence never implies acceptance |
| **Implementation entity** | A concrete source file, symbol, configuration, service, data object, document, design element, or test at one revision | Explicit implementation identity, normally path plus symbol/range or an upstream graph ID, anchored to a revision |
| **Evidence** | Executable or deterministic support for a bounded claim about structure, behavior, freshness, or conformance | Check/test identity, outcome, scope, inputs, revision, and provenance |
| **Finding** | A deterministic diagnostic about invalid, stale, missing, unknown, partial, verified, or disagreeing state | Rule ID, severity, subject, source, message, and remediation |
| **Reflection** | A durable record of a workflow problem encountered during an attempt, attributed to a feature and the source it concerns | `R-NNN` in the root `reflections.md`; it is process memory, not behavioral intent |
| **Projection** | A reproducible read model such as a rendered diagram, site, search index, knowledge graph, or alignment report | Generator plus input provenance; always generated/disposable |

### 3.2 Document and artifact roles

The filename alone does not determine meaning; its containing package and declared role do.

| Artifact role | Meaning | Authority |
|---|---|---|
| **Module summary** (`module.md`) | Fast orientation for one level: responsibility, boundary, structure, inventories, representative scenario, rationale link | Owns module responsibility, boundary, immediate hierarchy, and inventories together with contracts/views |
| **Module design reference** (`design.md` beside `module.md`) | Detailed module implementation rationale, alternatives, and decisions | Explains but never redefines module architecture |
| **Level view** (`architecture/diagrams/*.json`) | Maintained machine-readable organization and interaction at one module level | Owns visible current-level composition together with module prose/contracts |
| **Module contract** (`architecture/contracts/**/contract.md`) | Boundary identity and obligations owned by one module | Normative boundary authority |
| **Feature abstract** (`abstract.md`) | Self-contained orientation to one feature in under fifteen minutes | Summary only; cannot define beyond feature design |
| **Feature design** (`design.md` under a feature root) | Complete required behavior, scenarios, constraints, failures, and success criteria | Normative behavioral authority |
| **Feature implementation** (`implementation.md`) | Current accepted realization and implementation detail | Normative accepted-realization authority, not behavioral authority |
| **Feature contract/schema** | Detailed representation or interface specific to one feature | Normative for the serialized/interaction boundary it declares |
| **Feature diagram** (`diagrams/*.json`) | Core or supplemental explanation of feature participation and interaction | Maintained explanation; textual requirements/contracts still govern behavior |
| **Project ontology** (`docs/ontology.md`) | Shared vocabulary for Concorde, the pinned UA compatibility model, and their semantic relationship | Normative terminology and relationship authority across the project |
| **Attempt artifact** (`attempt/**`) | Proposed delivery work and current review/evidence state | Temporal only |
| **Executable source/test** | Current implementation and executable proof | Executable reality/evidence, not required intent |
| **Generated artifact** | Disposable transformation of maintained or executable inputs | No source authority |

### 3.3 Authority classes and lifecycles

| Authority class | Typical artifacts | Lifecycle |
|---|---|---|
| `workflow-control` | `.concorde/config.json`, `.specify/feature.json` | `control` |
| `installed-tooling` | installed extension, presets, agent skills | `installed` |
| `maintained-architecture` | module summaries, contracts, level views | `durable` |
| `module-design-reference` | module `design.md` | `durable` |
| `project-ontology` | `docs/ontology.md` | `durable` |
| `feature-orientation` | feature `abstract.md` | `durable-summary` |
| `durable-feature-intent` | feature `design.md`, feature contracts and declared diagrams | `durable` |
| `feature-implementation` | feature `implementation.md` | `durable-accepted` |
| `temporary-attempt` | `attempt/**` | `temporal` |
| `project-reflection-log` | root `reflections.md` | `durable-process-memory` |
| `executable-reality` | source and tests | `executable` |
| `generated-read-model` | delivered diagrams, docsite output, UA/alignment graph | `generated` |

### 3.4 Concorde relationships

| Relationship | Domain → range | Meaning and invariant |
|---|---|---|
| `concorde:containsModule` | Module → Module | Immediate module containment; acyclic; exactly one parent except the root |
| `concorde:registersFeature` | Module → Feature | The level at which a top-level feature is specified; exactly one registration |
| `concorde:containsSubfeature` | Feature → Sub-feature | One immediate decomposition level; bidirectional with `parent_feature`; acyclic |
| `concorde:refines` | Feature → Feature | Lower-level outcome refines a feature at the adjacent parent module; acyclic and distinct from containment |
| `concorde:provides` | Module/Feature → Contract | The subject exposes behavior through the contract |
| `concorde:requires` | Module/Feature → Contract | The subject depends on the contract |
| `concorde:governs` | Contract → boundary interaction | The contract owns information and obligations crossing that boundary |
| `concorde:participatesIn` | Module/External actor → Scenario | The participant is visible in the representative behavior |
| `concorde:specifiedBy` | Feature/Requirement → Source artifact | The artifact owns required prose |
| `concorde:realizedBy` | Feature/Requirement → Accepted realization or Implementation entity | An explicit realization/correlation, never inferred from equal names alone |
| `concorde:evidencedBy` | any bounded subject → Evidence | Evidence supports or refutes a claim for a stated scope and revision |
| `concorde:documents` | Source artifact → subject | The artifact explains the subject without necessarily owning its meaning |
| `concorde:projects` | Source/Executable inputs → Projection | Deterministic or declared generation lineage; projection remains non-authoritative |
| `concorde:concerns` | Reflection/Finding → stable subject or path | The diagnostic/process record identifies what it is about |
| `concorde:selectedAs` | workflow control → Feature | The current lifecycle routing selection; no behavioral meaning |

### 3.5 Concorde invariants

- Stable IDs are unique and references resolve.
- Module containment, feature containment, and adjacent-level refinement remain distinguishable and
  acyclic.
- A feature is specified once; a sub-feature has exactly one parent and cannot have children.
- Provided and required contract sets are explicit; every boundary interaction has a governing
  contract.
- Durable intent, accepted realization, temporary attempt, executable reality, evidence, and
  generated read models never collapse into one authority class.
- `unknown`, `partial`, `verified`, and `disagrees` describe evidence state, not workflow completion.
- A structural validation pass proves structural conformance only; it does not prove implementation
  correctness.

## 4. Understand Anything ontology at the pinned baseline

This section records the UA vocabulary consumed by Concorde. The pinned upstream source remains
authoritative for UA. This project ontology supplies stable definitions and compatibility expectations
so downstream code does not rely on enum names without semantics.

### 4.1 Graph classes

| UA class | Required meaning and fields |
|---|---|
| **KnowledgeGraph** | Root envelope: `version`, optional `kind`, `project`, `nodes`, `edges`, `layers`, `tour` |
| **ProjectMeta** | Project name, languages, frameworks, description, analysis time, and analyzed Git commit |
| **GraphNode** | Identified typed item with `id`, `type`, `name`, `summary`, tags, complexity, optional source location/notes, and optional metadata family |
| **GraphEdge** | Relationship with `source`, `target`, `type`, direction, optional description, and weight in `[0,1]` |
| **Layer** | Logical grouping with ID, name, description, and member node IDs; membership is not ontology identity |
| **TourStep** | Ordered explanatory step with title, description, node IDs, and optional language lesson |
| **DomainMeta** | Optional business-domain details: entities, business rules, cross-domain interactions, entry point/type |
| **KnowledgeMeta** | Optional knowledge-base details: wikilinks, backlinks, category, and content |
| **FigmaMeta** | Optional design details: file/node identity, raw Figma type, preview/dimensions, token data, prototype targets, component key |

`GraphNode` and its three metadata objects preserve additional fields at the pinned revision. The root
graph and edge parser do not provide that same arbitrary-field preservation guarantee. Concorde
therefore keeps canonical cross-ontology relation records in the alignment companion rather than
relying on custom fields on UA edges.

### 4.2 Graph kinds

| `kind` | Meaning |
|---|---|
| `codebase` | Structural/semantic graph of code and non-code project artifacts; also the default when `kind` is absent |
| `knowledge` | Markdown/knowledge-base graph using articles, entities, topics, claims, and sources |
| `design` | Figma/design graph using pages, screens, components, instances, and tokens |

The formal root enum has no `domain` value at the pinned revision. Domain graphs use `domain`, `flow`,
and `step` nodes and a dedicated view/file convention, but they do not introduce a fourth formal root
kind. Consumers must not invent `kind: "domain"` without an upstream compatibility change.

### 4.3 Node types: code and abstraction

| UA type | Definition | Typical identity |
|---|---|---|
| `file` | Source, script, markup, style, test, or other code-like file analyzed as one implementation unit | `file:<relative-path>` |
| `function` | Significant callable function or method within a file | `function:<relative-path>:<name>` |
| `class` | Class-like definition, including aliases normalized from interface or struct | `class:<relative-path>:<name>` |
| `module` | Higher-level logical module or package synthesized above individual files | `module:<name>` |
| `concept` | Higher-level abstract concept, architectural idea, pattern, or lesson | `concept:<name>` |

`module` and `concept` are deliberately broad UA abstractions. Neither is equivalent to a Concorde
Module or Feature without a separate `alignment:representedAs` assertion and Concorde metadata.

### 4.4 Node types: non-code project structure

| UA type | Definition | Typical source |
|---|---|---|
| `config` | Configuration artifact controlling compilation, runtime, tooling, or environment | JSON/YAML/TOML config, `.env`, package/tool config |
| `document` | Documentation artifact whose primary role is explanatory prose | README, guide, API documentation |
| `service` | Deployable/runnable service or infrastructure description of one | Dockerfile, Compose service, Kubernetes workload/service |
| `table` | Persistent relational table/view or migration-centered database object | SQL schema/migration |
| `endpoint` | Addressable API operation or route | OpenAPI operation, HTTP route, GraphQL query/mutation |
| `pipeline` | Automated build, test, deployment, or data-processing workflow | CI/CD workflow, Jenkinsfile, job pipeline |
| `schema` | Formal data/interface definition | GraphQL, Protobuf, Prisma, typed schema |
| `resource` | Provisioned infrastructure resource or declaration | Terraform, CloudFormation, Kubernetes resource |

These are semantic classifications of artifacts, not Concorde authority classes. A UA `document`
does not say whether a file is a module summary, feature design, temporary plan, or generated page.

### 4.5 Node types: business domain

| UA type | Definition | Structural expectation |
|---|---|---|
| `domain` | Named business capability or bounded area extracted from implementation terminology | May carry entities, business rules, and cross-domain interactions in `domainMeta` |
| `flow` | Business process or outcome within a domain, optionally with a trigger/entry type | Every flow belongs to a domain through `contains_flow` |
| `step` | Ordered unit of a business flow, preferably linked to concrete source when known | Every step belongs to a flow through `flow_step`; weight encodes order in the domain view |

These are implementation-derived business semantics. A UA `flow` is not automatically a Concorde
Scenario, and a UA `domain` is not automatically a Concorde Module.

### 4.6 Node types: knowledge base

| UA type | Definition | Typical role |
|---|---|---|
| `article` | One source knowledge document or note | Primary reading unit; may carry wikilinks/backlinks/content |
| `entity` | Named real or conceptual entity discussed by knowledge articles | Person, organization, system, place, product, or domain object |
| `topic` | Category, tag, theme, or subject used to organize knowledge | Classification target |
| `claim` | Specific assertion, thesis, decision, or proposition that may be supported or contradicted | Semantic statement, not proof by itself |
| `source` | Cited reference or provenance-bearing knowledge source | Paper, external reference, raw source |

Model-generated knowledge nodes may help navigation but do not become Concorde evidence merely by
being present. Evidence requires explicit provenance and deterministic or executable support.

### 4.7 Node types: design/Figma

| UA type | Definition | Typical identity |
|---|---|---|
| `page` | Figma page/canvas grouping top-level design content | `page:<figma-node-id>` |
| `screen` | Top-level frame or artboard representing a UI screen | `screen:<figma-node-id>` |
| `component` | Reusable main component | `component:<figma-node-id>` |
| `componentSet` | Collection of component variants | `componentSet:<figma-node-id>` |
| `instance` | Placed use of a reusable component | `instance:<figma-node-id>` |
| `token` | Published style or variable for color, type, spacing, effect, or grid | `token:<token-kind>:<name>` |

UA intentionally uses a shallow design graph: nested groups, text, vectors, and shapes may be read
for relationships or metadata without becoming graph nodes.

### 4.8 Edge types and direction

Direction below is the canonical semantic direction expected by the pinned producers. `weight`
expresses confidence/strength except where a producer explicitly uses it for ordering, such as
`flow_step`.

| Category | UA edge | Direction and meaning |
|---|---|---|
| Structural | `imports` | importing node → imported dependency |
| Structural | `exports` | exporting file/module → exported symbol or abstraction |
| Structural | `contains` | container → contained member |
| Structural | `inherits` | subclass/derived definition → superclass/base definition |
| Structural | `implements` | concrete realization → abstraction or implemented business step |
| Behavioral | `calls` | caller → callee |
| Behavioral | `subscribes` | subscriber → event/channel/publisher it observes |
| Behavioral | `publishes` | publisher → event/channel/consumer-facing signal |
| Behavioral | `middleware` | middleware participant → request path/target it mediates, as described by the edge |
| Data flow | `reads_from` | consumer → data source |
| Data flow | `writes_to` | producer/writer → data sink |
| Data flow | `transforms` | transformer → transformed input/output subject named by the edge |
| Data flow | `validates` | validator → validated subject |
| Dependency | `depends_on` | dependent → dependency |
| Dependency | `tested_by` | production subject → test evidence |
| Dependency | `configures` | configuration artifact → affected target |
| Semantic | `related` | general directed relation; no stronger semantics implied |
| Semantic | `similar_to` | similarity relation, normally interpreted symmetrically when direction is bidirectional |
| Infrastructure | `deploys` | deployment/infrastructure artifact → deployed code/service |
| Infrastructure | `serves` | service/proxy/workload → exposed endpoint or served target |
| Infrastructure | `provisions` | infrastructure declaration → provisioned resource |
| Infrastructure | `triggers` | trigger/configuration → invoked workflow/action |
| Schema/data | `migrates` | migration → table/schema changed |
| Schema/data | `documents` | document → described subject |
| Schema/data | `routes` | routing configuration → destination service/endpoint |
| Schema/data | `defines_schema` | schema artifact → code/API/data subject governed by that schema |
| Domain | `contains_flow` | domain → flow |
| Domain | `flow_step` | flow → step; domain producer may encode step order in weight |
| Domain | `cross_domain` | source domain → interacting target domain |
| Knowledge | `cites` | article/claim → cited source/article |
| Knowledge | `contradicts` | claim/article → contradicted claim/article |
| Knowledge | `builds_on` | later knowledge item → prior item it extends |
| Knowledge | `exemplifies` | example/entity/article → generalized concept/claim |
| Knowledge | `categorized_under` | article/entity/claim → topic/category |
| Knowledge | `authored_by` | article/source → author entity |
| Design | `instance_of` | instance → component |
| Design | `variant_of` | component variant → component set |
| Design | `uses_token` | screen/component/instance → token |

### 4.9 Normalization aliases

Aliases make ingestion tolerant; they are not additional ontology classes. After normalization the
canonical value is the right-hand side.

| Alias group | Normalization |
|---|---|
| Code nodes | `func`, `fn`, `method` → `function`; `interface`, `struct` → `class`; `mod`, `pkg`, `package` → `module` |
| Non-code nodes | `container`, `deployment`, `pod` → `service`; `doc`, `readme`, `docs` → `document`; `job`, `ci` → `pipeline`; `route`, `api`, `query`, `mutation` → `endpoint` |
| Config/data/infra nodes | `setting`, `env`, `configuration` → `config`; `infra`, `infrastructure`, `terraform` → `resource`; `migration`, `database`, `db`, `view` → `table`; `proto`, `protobuf`, `definition`, `typedef` → `schema` |
| Domain nodes | `business_domain` → `domain`; `business_flow`, `business_process` → `flow`; `task`, `business_step` → `step` |
| Knowledge nodes | `note`, `wiki_page` → `article`; `person`, `actor`, `organization` → `entity`; `tag`, `category`, `theme` → `topic`; `assertion`, `decision`, `thesis` → `claim`; `reference`, `raw`, `paper` → `source` |
| Design-only nodes | `frame`, `artboard` → `screen`; `canvas` → `page`; `main_component` → `component`; `component_set`, `variant_set`, `componentset` → `componentSet`; `design_token`, `style` → `token` |
| Non-design node collision | `page` → `article`; only `kind: design` keeps canonical `page` |
| Structural/behavioral edges | `extends` → `inherits`; `invokes`, `invoke` → `calls`; `uses`, `requires` → `depends_on`; `import` → `imports`; `export` → `exports`; `contain` → `contains`; `publish` → `publishes`; `subscribe` → `subscribes` |
| Semantic edges | `relates_to`, `related_to` → `related`; `similar` → `similar_to` |
| Non-code edges | `describes`, `documented_by` → `documents`; `creates` → `provisions`; `exposes`, `listens` → `serves`; `deploys_to` → `deploys`; `migrates_to` → `migrates`; `routes_to` → `routes`; `triggers_on`, `fires` → `triggers`; `defines` → `defines_schema` |
| Domain edges | `has_flow` → `contains_flow`; `next_step` → `flow_step`; `interacts_with` → `cross_domain` |
| Knowledge edges | `references`, `cites_source` → `cites`; `conflicts_with`, `disagrees_with` → `contradicts`; `refines`, `elaborates` → `builds_on`; `illustrates`, `example_of` → `exemplifies`; `belongs_to`, `tagged_with` → `categorized_under`; `written_by`, `created_by` → `authored_by` |
| Design-only edges | `instantiates` → `instance_of`; `variant` → `variant_of`; `styled_by`, `applies_token` → `uses_token` |
| Non-design edge collision | `instance_of` → `exemplifies`; only `kind: design` keeps canonical `instance_of` |

UA deliberately does not alias `implemented_by` to `implements` because it reverses direction.
Likewise, ambiguous `process` is not automatically normalized to business `flow`. Node types are
lowercased during sanitization, so `componentSet` requires the design-only `componentset` repair.

## 5. Relationship between the ontologies

The relationship is a typed association model, not a type-to-type merge.

### 5.1 Cross-ontology relationships

| Relationship | Domain → range | Meaning |
|---|---|---|
| `alignment:representedAs` | Concorde entity/artifact → UA GraphNode | The adapter uses this UA node and node type to serialize or render the Concorde subject; no equivalence implied |
| `alignment:correlatesWith` | Concorde entity → Implementation entity | Explicitly supported association at a named revision and basis |
| `alignment:realizedBy` | Feature/Requirement → Accepted realization or Implementation entity | The target realizes some stated scope of required behavior |
| `alignment:evidencedBy` | bounded alignment claim → Evidence | Evidence supports or refutes the claim for stated inputs/revision |
| `alignment:disagreesWith` | Finding → two or more authoritative/executable subjects | Deterministic evidence establishes an actual conflict |
| `alignment:derivedFrom` | Projection/record → source/evidence/revision | Provenance lineage used for freshness and reproduction |
| `alignment:suggestedMatch` | Concorde entity ↔ Implementation entity | Name/summary/similarity candidate only; cannot establish `verified` or `disagrees` |
| `alignment:renderedEdgeAs` | Concorde/cross-ontology relationship → UA GraphEdge | Adapter representation of a relationship for UA visualization; canonical relation remains in the companion record |

There is no default `sameAs` relationship. A future equivalence assertion would require an explicit,
reviewed rule proving that both identifiers denote the same subject, not merely compatible labels.

### 5.2 Cardinality and identity

- A Concorde entity may have zero or many UA adapter representation nodes.
- One UA implementation node may correlate with zero or many Concorde features/requirements.
- A represented Concorde entity keeps its stable ID in `concordeMeta.stableId`; the UA node ID remains
  a graph identity, not a replacement project identity.
- Display name, summary, tags, node type, and semantic similarity never establish identity alone.
- Path matches require a revision and path-normalization context. Stable Concorde IDs survive path
  renames; path-identified implementation nodes do not automatically do so.

### 5.3 Required Concorde metadata on represented nodes

| Field | Meaning |
|---|---|
| `concordeMeta.kind` | Canonical Concorde class represented by the node |
| `concordeMeta.stableId` | Stable project identity when one exists |
| `concordeMeta.sourcePath` | Canonical project-relative source path |
| `concordeMeta.authorityClass` | Authority class from section 3.3 |
| `concordeMeta.lifecycle` | Lifecycle from section 3.3 |
| `concordeMeta.moduleId` | Architectural level when applicable |
| `concordeMeta.featureId` | Feature context when applicable |
| `concordeMeta.ontologySource` | Always `docs/ontology.md` for this ontology |
| `concordeMeta.ontologyVersion` | Ontology version that governed representation |

## 6. Alignment semantics

An alignment record is a claim about one Concorde subject at named source and implementation
revisions. It is not a property inherent in a UA node.

### Coverage dimensions

| Dimension | Values | Meaning |
|---|---|---|
| `specification` | `present`, `absent`, `not-applicable` | Whether authoritative required intent exists for the subject |
| `accepted_realization` | `present`, `placeholder`, `absent`, `not-applicable` | Whether durable realization exists |
| `implementation` | `present`, `absent`, `ambiguous`, `not-applicable` | Whether implementation correlation is established |
| `evidence` | `present`, `absent`, `failing`, `stale`, `not-applicable` | Whether current executable/deterministic evidence supports the claim |

### Evidence states

| State | Meaning | Minimum condition |
|---|---|---|
| `unknown` | Available sources cannot establish agreement or disagreement | Default for absent, ambiguous, incompatible, or stale inputs |
| `partial` | Some explicit correlation/evidence exists, but required coverage is incomplete | At least one non-name-only basis and no deterministic conflict |
| `verified` | Required intent, accepted/current realization where applicable, implementation, and positive deterministic evidence agree for the stated scope and revisions | All required coverage present/current and relevant deterministic checks pass |
| `disagrees` | Deterministic evidence establishes conflict among maintained authorities or between intent and executable reality | Current finding identifies both sides and the failed rule/evidence |

Absence of evidence is `unknown` or `partial`, not `disagrees`. Model-generated summaries and
similarity may create `alignment:suggestedMatch`, but never `verified` or `disagrees`. A stale record
cannot remain verified in the current presentation.

## 7. Adapter representation profile for UA rendering

This section is intentionally subordinate to sections 3–6. It answers only: "If an adapter must put a
Concorde subject into a UA graph, which existing UA node/edge type can carry it without losing the
canonical relationship record?"

### Node representation profile

| Concorde subject | Default UA adapter representation type | Alternatives | Required qualification |
|---|---|---|---|
| Project/root module/module | `module` | none | Preserve `module.*`, hierarchy level, and `concordeMeta.kind: module` |
| Feature/sub-feature | `concept` | none in v1 | Preserve `feature.*`, containment/refinement, and exact Concorde kind |
| Contract | `schema` | `concept` when it has no data representation | User-facing label remains Contract; UA `schema` does not own contract semantics |
| Scenario | `flow` | `concept` for non-flow examples | Preserve scenario ID and governing contracts; do not infer a business domain |
| Command intent | `endpoint` | `concept` | Preserve canonical dotted intent; slash/skill names are presentations, not browser routes |
| Requirement | `claim` | `concept` | Qualify `FR-NNN` by feature ID; requirement prose remains in feature design |
| Module/feature/project Markdown | `document` | `article` only in a knowledge graph | Preserve artifact role, authority, and lifecycle |
| Maintained/generated diagram, manifest, receipt, asset | `resource` | `document` when text-first | Preserve maintained versus generated distinction |
| Attempt | `pipeline` | `concept` | Always `temporary-attempt`; never imply acceptance |
| Accepted realization | `concept` | `document` for physical `implementation.md` | Semantic realization and document may be separate nodes |
| Finding | `claim` | none | Only deterministic findings affect evidence state |
| Evidence record | `source` | native `file`/`function`/`class` for executable test | UA `source` means knowledge provenance, not source-code file |
| External actor/system | `service` | `concept`, `resource` | Preserve counterparty and external identity |
| Implementation/design entity | Native UA type | another type only under pinned normalization rules | Concorde adds correlation/provenance; it does not overwrite accurate implementation structure |

### Edge representation profile

| Canonical relationship | Default UA adapter edge type | Qualification |
|---|---|---|
| `concorde:containsModule`, `registersFeature`, `containsSubfeature` | `contains` | Companion record retains the exact Concorde relationship |
| `concorde:refines` | `builds_on` | Not feature containment |
| `concorde:provides` | `exports` | Provider → contract |
| `concorde:requires` | `depends_on` | Consumer → contract |
| command/contract exposes feature outcome | `serves` | Companion canonical relation is `exposes` |
| scenario contains ordered step | `flow_step` | Ordering is recorded explicitly; UA weight may support rendering |
| scenario/requirement relates to participant | `related` | Does not imply realization |
| implementation realizes feature/requirement | `implements` | UA direction is implementer → abstraction; companion relation may be feature → realization |
| subject has executable evidence | `tested_by` | Subject → test/evidence |
| artifact explains subject | `documents` | Explanation is not necessarily authority |
| deterministic finding establishes conflict | `contradicts` | Only after current deterministic evidence |
| candidate match | `similar_to` | Always non-verifying |

Because UA edges do not preserve arbitrary custom metadata, every represented relationship used for
alignment also has a companion relation record containing canonical relationship, semantic source and
target identities, adapter edge type, mapping basis, and provenance.

### Example

```json
{
  "id": "concorde:feature.concorde.explore-alignment",
  "type": "concept",
  "name": "Alignment Explorer",
  "concordeMeta": {
    "kind": "feature",
    "stableId": "feature.concorde.explore-alignment",
    "sourcePath": "specs/concorde/features/006-alignment-explorer/design.md",
    "authorityClass": "durable-feature-intent",
    "lifecycle": "durable",
    "ontologySource": "docs/ontology.md",
    "ontologyVersion": "1.1.0-draft"
  }
}
```

The Concorde assertion is:

```text
feature.concorde.explore-alignment is a concorde:Feature
feature.concorde.explore-alignment alignment:representedAs
  concorde:feature.concorde.explore-alignment
```

It is not:

```text
concorde:Feature sameAs ua:concept
```

## 8. Terms that must not collapse

| Collision | Required distinction |
|---|---|
| Concorde Module vs UA `module` | Architectural responsibility level vs broad code/package abstraction |
| Concorde Feature vs UA `concept` | Observable required outcome vs general abstraction/pattern |
| Concorde Contract vs UA `schema` | Boundary promise with obligations/failure/compatibility vs data/interface definition |
| Concorde Scenario vs UA `flow` | Representative behavior example vs implementation-derived business process |
| Concorde Evidence vs UA `source` | Bounded executable/deterministic support vs knowledge provenance node |
| Source authority vs source-code file | Artifact ownership of a fact vs an implementation file |
| Command intent vs presentation vs browser route | Canonical operation identity vs slash/skill spelling vs eventual URL |
| Module `design.md` vs feature `design.md` | Module rationale/reference vs required feature behavior |
| Feature `implementation.md` vs executable implementation | Accepted realization explanation vs code/config/data |
| Attempt vs accepted realization | Temporary proposal/review state vs durable accepted implementation |
| Maintained diagram vs generated graph/page | Source explanation vs disposable read model |
| UA design `page`/`instance_of` vs non-design aliases | Graph-kind-sensitive canonical design values vs knowledge-mode normalization |
| Representation vs equivalence | Adapter choice vs proof of identical semantic class/instance |

## 9. Versioning and drift

1. The ontology version changes when a shared Concorde class/relation, UA compatibility definition,
   cross-ontology relationship, evidence-state rule, authority/lifecycle class, or adapter profile
   changes.
2. The UA repository revision, 27-node registry, 38-edge registry, graph-kind rules, alias tables, and
   metadata pass-through behavior are pinned together.
3. A new UA revision is not accepted merely because JSON still parses. Additions, removals, category
   changes, alias direction changes, or metadata-stripping changes produce ontology drift.
4. Concorde source discovery, digesting, validation, bounded context, link checking, and publication
   include `docs/ontology.md`; a changed ontology version makes older projections stale.
5. Ontology prose, contract schemas/examples, feature requirements/abstracts, UI labels, deterministic
   fixtures, and generated projections evolve in one reviewed unit whenever their shared semantics
   change.
6. Generated projections record both ontology source/version and upstream source/revision. Missing or
   mismatched provenance prevents a current `verified` presentation.

## 10. Read next

- [Abstract, Design, Implementation, and Architecture](specification-model.md)
- [Project Structure and Source Authority](project-structure.md)
- [Concorde Workflow](concorde-workflow.md)
- [Alignment Explorer feature](../specs/concorde/features/006-alignment-explorer/abstract.md)
- [Alignment Explorer bundle contract](../specs/concorde/architecture/contracts/alignment-explorer/contract.md)
- [Understand Anything compatibility contract](../specs/concorde/architecture/contracts/understand-anything-graph/contract.md)
