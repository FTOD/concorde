# Views

## Purpose

Views publishes registered specifications as a readable website and provides tools to export, analyze or open code-structure graphs. Developers use it to understand a project and inspect its declared relationships. A published page or graph does not by itself prove that the code satisfies the specification.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Implementation Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Publication candidate](pipeline.md#terminology) | Defined in From source documents to a published site. |
| [Promotion](pipeline.md#terminology) | Defined in From source documents to a published site. |
| [Document role](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Document unit](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Entity](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Semantic completeness](../spec/structure.md#terminology) | Defined in What structural validation tells you. |

## Usage

Choose among independent uses: publish registered Specs as a docsite, export or overlay a
registry-derived UA graph, run native UA analysis with Spec guidance, or open an existing graph
in the installed viewer. For a new site, propose
a scaffold, inspect it and apply the exact proposal; existing site files are not overwritten.
With site dependencies prepared, build and validate the publication candidate before publication. A broken
link, invalid document or stale input prevents promotion and preserves the previous published site.
[Publication](publication.md) explains scaffolding, custom documentation and reading behavior;
[pipeline](pipeline.md) defines the build API and records.

For reading, start with **Module Specs** to understand a Module's purpose, correct use and design.
When its author explicitly classifies detailed companions, **Implementation Specs** provides a
parallel tab for precise obligations and interfaces, with links back to the owning Module.
Both tabs read from the same registry: references never duplicate a document, and changing its tab
neither changes its canonical route nor removes it from complete agent Spec context.
Classification is explicit, never inferred from a filename or the presence of SHALL statements.
The [publication contract](scenarios.md#scenario.views.reading-collections) specifies the details.

The Spec reader presents Usage before Design, so using a Module
does not require first reading its entity/file inventory. Both explanations remain canonical reading content.
Custom docs are separate human documentation and grant no Spec context. For graphs, use
[UA export](ua-graph.md) to derive or overlay declared structure and `--check` for drift without
writes. Use `ua-analyze` to prepare a Spec-derived seed and complete context indexes, then run
Understand Anything's full native analysis against project code through an installed Claude host.
This optional developer tool requires a separately installed analysis plugin and normal host
permissions; the installed Viewer alone is insufficient. A failed native run can leave partial
UA files, so inspect its receipt before using them. [Native analysis](ua-graph.md#native-analysis)
explains prerequisites, scope and recovery. Use the [viewer launcher](viewer.md) only with an
existing valid graph and verified runtime.
The launcher neither generates a graph nor verifies agreement with code; no rendered view proves
semantic completeness or authorizes a change.

## Design

<a id="entity.views.publication-docsite"></a><a id="entity.views.docsite-build-interface"></a><a id="entity.views.markdown-documents"></a><a id="entity.views.canonical-page"></a><a id="entity.views.navigation"></a><a id="entity.views.candidate-site"></a><a id="entity.views.published-site"></a>

Publication docsite reads Registered Markdown documents and their paired metadata as one source
model, but produces one Canonical page per reading document. Spec navigation follows registered
Module parentage rather than directory structure. The Docsite build interface separates admission,
materialization, candidate build, source/link validation and promotion. Only a current validated
Candidate site replaces the Published site; a failure preserves the last successful build.
Metadata participates in source identity and auxiliary provenance, not an appended file inventory.
The Protocol's explicit document role assigns each source to a reading collection; the publisher
validates that formal definitions occur only in Implementation Specs. Role-based navigation retains
one complete Module specification: both sidebars derive from the same Module parentage, each document appears once, and
shared provider definitions stay at their owner's canonical page. Main entries retain an explanatory
reading path; exact requirements and scenarios can be authored once in owned companions rather
than repeated or extracted into a second generated specification.
The [pipeline design](execution-reference.md#pipeline-design) defines these identities and promotion mechanics.

<a id="entity.views.publication-scaffold"></a><a id="entity.views.docsite-scaffold-command"></a><a id="entity.views.file-transactions"></a>

Docsite scaffold command uses Publication scaffold and File transactions to create only the exact
accepted site files. Scaffolding does not rewrite project Specs or overwrite existing consumer
files. Provider definitions stay at their canonical pages: ordinary links never transclude a
second copy of a shared contract.

<a id="entity.views.ua-graph-exporter"></a><a id="entity.views.ua-graph-command"></a><a id="entity.views.viewer-launcher"></a><a id="entity.views.viewer-launch-command"></a><a id="entity.views.viewer-request"></a><a id="entity.views.code-graph"></a><a id="entity.views.verified-viewer-runtime"></a><a id="entity.views.viewer-process"></a>

UA graph export command uses UA graph exporter to derive or overlay declared structure without
judging implementation conformance. A Raw code graph can also be an observation produced elsewhere.
Viewer launch command passes a Viewer launch request to Viewer launcher, which admits the existing
graph and the Verified installed viewer supplied by [Distribution Module](../distribution/module.md) before starting the Viewer process.
Launch neither regenerates the graph nor checks its freshness against source. Export and launch are
independent of reading publication and grant no additional agent context.

<a id="entity.views.ua-analysis"></a>

UA analysis bridge treats the native Understand Anything flow as one external operation. It
prepares declared structure and byte-bound Protocol/Spec context indexes before launching the
native host, while project code remains an independent input to UA's scanner and analyzers.
This avoids duplicating UA's worker scheduling in Concorde. Execution requires explicit temporary
native-tool consent and first exercises a real bounded permission probe, including an inherited
child invocation, so missing native permissions block before whole-project model analysis. The
host prepares directories and Git identity and retains scratch rather than asking the model to
purge it; managed/project denials and hooks remain active. Afterwards it checks the native
schema, declared identities and relationships, scan coverage and input freshness without
reapplying an overlay that would discard AI enrichment. This is a developer-authorized native
host tool, not a bounded Framework worker or a new Framework Operation. Its prompt is guidance,
not a filesystem sandbox, and native permissions remain in effect. No structural check proves
that workers read every source or that their semantic conclusions are correct.

## Relationships

Publication scaffold and Publication docsite touch disjoint files and never edit each other's
output: the scaffold's own exact-file transaction creates or updates project structure, and
rendering project Specs never authorizes editing them. A publication candidate is promoted only when complete
and current; any invalid link, diagram or stale source during generation leaves the published site
exactly as it was. Registry composition still supplies navigation, and dependency and interface
agreements still undergo validation; none creates a standalone docsite graph projection.

The UA graph exporter derives and writes a skeleton from the registry without judging agreement
with code. UA analysis bridge reuses that derivation as input to whole-project native UA analysis,
without limiting the code scan to registered file bindings. The viewer launcher independently
admits an existing graph and verified runtime and
launches a process; it neither generates nor verifies the freshness of that graph.

### Publication and scaffolding

This view covers reading publication and its creation-only scaffold, not graph generation or viewer
processes. Concorde-only Graph inspection additionally uses [Harness Module](../harness/module.md) under the local agreement below.

```mermaid
flowchart TB
    accTitle: Publication admission and promotion
    accDescr: Spec supplies registered reading and metadata. Publication derives canonical pages and navigation, validates a candidate and promotes it. Scaffolding separately creates accepted site files through file transactions.
    spec["Spec"]
    site["Publication docsite"]
    documents["Registered Markdown documents"]
    page["Canonical page"]
    navigation["Spec navigation"]
    candidate["Candidate site"]
    published["Published site"]
    scaffold["Publication scaffold"]
    transaction["File transactions"]
    spec -->|supplies registered sources to| site
    site -->|reads| documents
    documents -->|render as| page
    site -->|derives| navigation
    page -->|contributes to| candidate
    navigation -->|contributes to| candidate
    candidate -->|validated current output replaces| published
    scaffold -->|creates scaffold for| site
    scaffold -->|applies accepted creation through| transaction
```

### Independent graph export

Export derives or overlays the registry's declared structure; it is not a source-code analysis or a
replacement for a Module's authored relationship view.

```mermaid
flowchart LR
    accTitle: Registry-derived graph export
    accDescr: Spec supplies declared structure to the UA exporter, which writes or overlays a raw graph without judging code conformance.
    spec["Spec"]
    exporter["UA graph exporter"]
    rawGraph["Raw code graph"]
    spec -->|supplies declared structure to| exporter
    exporter -->|writes or overlays| rawGraph
```

### Existing-graph viewing

Launch selects an already-existing graph and a verified viewer. It neither generates that graph
nor verifies its agreement with current implementation.

```mermaid
flowchart LR
    accTitle: Existing graph viewer launch
    accDescr: Distribution provisions the verified viewer. The launcher admits a request, an existing raw graph and the verified runtime before starting the viewer process.
    distribution["Distribution"]
    runtime["Verified installed viewer"]
    request["Viewer launch request"]
    rawGraph["Raw code graph"]
    launcher["Viewer launcher"]
    process["Viewer process"]
    distribution -->|provisions| runtime
    request -->|is admitted by| launcher
    runtime -->|is verified by| launcher
    rawGraph -->|is admitted by| launcher
    launcher -->|starts| process
```

## Precise specifications

The explanation above is the entry to the Views specification. Its
[Module-wide requirements](requirements.md), [scenarios](scenarios.md) and
[interface contracts](contracts.md) provide the precise obligations used for implementation and
verification under **Implementation Specs**. Publication, pipeline, viewer and UA-export pages
remain explanatory topics under **Module Specs**.
They remain normative parts of this same Module, not code documentation or a separate context.

## Dependencies and composition

### Spec

<a id="entity.views.spec"></a><a id="agreement.document.views.module.1"></a>

The [Spec Module](../spec/module.md) supplies the explicit registry, document ownership and references, relationships and file bindings used by publication and UA export, without recursive filename discovery.

Supply the explicit registry, document ownership and references, relationships and entity file bindings consumed by publication and UA export.

This collaboration applies when loading publication inputs, materializing pages or navigation, or exporting the UA graph skeleton.

- [Derive pages and graph structure from explicit unique ownership, references and entity listings](../spec/structure.md#registry-shape)
- [Resolve inclusion provenance without recursive reads](../spec/contracts.md#registry-stable-id-spec-context-queries)

### Distribution

<a id="entity.views.distribution"></a><a id="agreement.document.views.module.2"></a>

Provisions and verifies the official viewer package inside the managed runtime that the viewer launcher checks before starting a launch.

Provision and verify the official viewer package inside the managed runtime.

This collaboration applies when launching the viewer.

- [Launch only the exact verified viewer entrypoint and stop on an absent receipt](../distribution/runtime.md)

### Harness

<a id="entity.views.harness"></a><a id="agreement.document.views.module.3"></a>

Supply inspectable executable Graphs without invoking nodes.

This collaboration applies when compiling Agent execution views without running nodes.

- [Harness contract](../harness/graphs-and-loops.md); preserve its admission conditions, retain distinct blockers and do not infer wider authority from composition.

## Unresolved information

Publication accepts Profile 15 projects only. `requireScoped` refuses any other `profile_version`
with an explicit error, and no compatibility rendering path exists for an older profile: migrating
such a project is a separate, explicit topology change that this Module does not perform.

## Ownership, context and implementation status

The loaders and exporters implement publication schema 21, unique owners, reference provenance, canonical contract anchors and UA reference edges. Reference inclusion creates no transclusion, implementation grant or new page authority.
