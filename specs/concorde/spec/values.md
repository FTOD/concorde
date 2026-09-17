# Registry values and selection

### Framework configuration and storage versions

`Profile 14` is the Framework's project-configuration compatibility version for the complete content model and its human-readable subset. It is distinct from Spec Protocol 8.0.0 and from registry schema 5, which versions the Framework's JSON encoding. These numbers do not classify project Modules or add concepts to the specification language.

The Framework reads `.concorde/config.json` with exactly `profile_version: 14`, `registry` (the registry's project-relative path), `protocol` (the accepted version and manifest digest, whose bundle the project carries under `.concorde/protocol/`) and `capability_configuration` (the typed Pi worker model selection: an optional default `model`, `thinking` level and `timeout_seconds`, and optional `workers` overrides per worker or per worker child). Other profile values fail with `unsupported_profile`; an incompatible Protocol binding fails with `protocol_mismatch`.

Registry schema 5 stores exactly `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. `targets` holds Module descriptors; both Module Specs and Implementation Specs are owned units in the same documents collection, distinguished by the explicit schema-2 document.role. Implementation Specs are normative documents, not entity file bindings or implementation source. The separate check records configure executable verification; they are Framework execution metadata. Their serialized shape does not replace the Protocol's meaning of identity, membership, composition, dependency, entity or file binding.

## Identities, roles and snapshots

Module identity names a responsibility. Document identity names one paired unit owned by that
Module, independently of its current path or title. Requirement, scenario and interface identities
name canonical definitions within that owned collection; a topic heading does not introduce another
owner. A document role chooses explanation or precise specification, while a source-member role
identifies reading bytes versus metadata bytes. Confusing these two roles would incorrectly omit
half of a unit or treat implementation specifications as executable source.

A descriptor records declared membership and relationships. A resolution records the selected
one-level closure and the byte identities of its complete paired sources. Neither record certifies
implementation correctness. Reconstruct a repository after changes and bind downstream evidence to
that new resolution rather than retaining a path-only claim of freshness.

Host task artifacts are another category: plans, tasks and reserved task IDs carry admitted workflow
state, not additional software promises or permission to read code. A well-shaped artifact still
needs current, phase-specific admission before use.

## Precise specifications

The Spec Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
