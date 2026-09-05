# Spec publication

## api.publication.build

loadScopedRegistry(root) returns Workspace 14 target/page/edge data from explicit configuration and registry; it rejects malformed axes, focus ownership, document paths, unsupported local links and mismatched shared schemas. materializeScoped writes derived Markdown/sidebar assets preserving target/document identity. The publication plugin binds sourceDigest and emits build-manifest.json plus architecture-graph.json. validateScopedBuild compares fresh source identity and route inventory before the existing atomic output promotion. isScoped(root) dispatches the Profile 8 path; legacy deterministic publication utilities remain separate. The Module exposes no agent tool or read proxy.

## Interface signatures

These signatures identify public call shapes; bodies and private helpers are outside this Spec.

Failures return structured findings or the declared exception; callers must stop the affected transition. Repeating an unchanged read is side-effect free. Mutations require current preconditions and explicit caller-owned paths. Local contract facts above remain authoritative without reading the parent or collaborating Specs.
