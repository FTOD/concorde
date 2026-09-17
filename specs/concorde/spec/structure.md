# Spec structure and validation

This document defines the registry shape this Module admits and the deterministic validation it performs against that shape. Selection and returned value records are defined in [registry](registry.md) and [values](values.md); the admission scenarios for a consistent or inconsistent inventory are defined in [module](module.md).

### Registry shape

Registry schema 5 contains `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. A Module descriptor has `id`, `kind="module"`, `title`, `documents`, `references`, `parent`, `uses`, `files` and `checks`. Every array is explicit. `files` holds listing entries: an exact project file, or a directory prefix written with a trailing `/` that binds every regular file below it. It MUST equal the sorted union of the Module's own entity listing declarations, entry for entry, so a directory prefix appears as that prefix and never as its expanded file names; membership, composition and dependency are checked independently of that entry set. The entry names one Module, and its complete collection starts routing.

Each registered reading document has a `.md.json` companion with `schema_version: 2`, `document`
identity/owner/role and explicit `entities`, `dependencies` and `bindings` arrays. Entity records contain
id/title/kind and a local readable meaning anchor, with optional files/pending/target_id. Dependency
records contain target_id and a local meaning anchor. Participant bindings contain id/version/role/
peer and a local meaning anchor. Responsibilities, conditions, guarantees and obligations remain
readable prose, never copied semantic strings in metadata. File/directory binding specificity and
pending rules still apply, and neither source member may be bound as implementation or external
material. Every child and used Module has exactly one local entity and one dependency explanation.

The principal Relationships diagram uses a nonempty subset of local entity titles and labels each
edge. Scoped omission of an inventory node is permitted; inventing a node is not. Check records
retain id/target_id/argv/timeout_seconds and optional inputs. Shared implementation changes concern
every listing Module, whose contract is evaluated separately.

Topology preparation stores the exact validated registry/document replacements below the ignored `.concorde/topology-proposals/` host area. Its public ArtifactRef binds path and digest. Applying the artifact rechecks its embedded design identity, discovery context, Protocol, registry base and every file before-digest before one atomic transaction.

### Reference and interface validation

Schema 5 requires a references array on every Module. Each `{kind, id}` must resolve to the
declared Module/document kind; duplicates, self references, document aliases and multiple owners
are errors. Overlap is deduplicated with all provenance, and cycles do not recurse. Each binding's
canonical definition/version must occur in its participant's resolved context; internal peers
require complementary bindings. Definitions have one owner and cannot be duplicated in consumers.
Required links to excluded definitions identify gaps rather than authorizing another read.
Structural checks report missing references/definitions separately from semantic incompleteness.

## Precise specifications

The Spec Module owns the exact obligations and interface details in [contracts](contracts.md), [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
