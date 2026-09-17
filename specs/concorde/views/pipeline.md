# From source documents to a published site

The publication pipeline protects the last working site while a new one is prepared. It separates
reading source admission, candidate generation, validation and replacement so that partial output
cannot be mistaken for a successful publication.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Publication candidate | A separately generated website that must pass checks before replacing the published site. |
| Promotion | Replacing the published website with a checked, current publication candidate. |
| [Module Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Implementation Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Document role](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Document unit](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Scenario](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |

## Follow one build

The publisher reads the explicitly registered document pairs and their roles. It creates one page
per reading document, organizes both tabs under the same Module hierarchy, and renders authored
diagrams and links. It checks the completed candidate against the current source before replacing
the published directory.

For example, moving a scenario to another owned document requires its retained links to follow the
new location. If a link still points to the old fragment, the candidate is rejected and the previous
site stays available. Changing only a role changes navigation, not the document's canonical route.

## Why a candidate is separate

Rendering can fail halfway through, and sources can change during a build. Generating separately and
checking freshness before promotion prevents either case from damaging the current site. A successful
replacement removes obsolete generated pages; a failed attempt does not silently promote the parts
that happened to render.

## Reading and customization

Module Specs explain responsibilities; Implementation Specs carry their precise obligations. Search,
provenance and identity anchors work across both. Referencing a provider creates a link to its single
owned page, not another copy. Project guides and interactive custom pages can use separate tabs,
but do not become agent Spec context merely by appearing on the site.

Preview and production use separate build caches so a production build does not destroy an active
preview. Exact framework hooks, route rewriting, records, aliases and promotion algorithms belong in
the Module's publication and execution contracts. The [publication topic](publication.md) explains
scaffolding and the user-facing workflow.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#pipeline-publication-pipeline).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
