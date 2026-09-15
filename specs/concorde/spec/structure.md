# Spec structure and validation

This document defines the registry shape this Module admits and the deterministic validation it performs against that shape. Selection and returned value records are defined in [registry](registry.md) and [values](values.md); the admission scenarios for a consistent or inconsistent inventory are defined in [module](module.md).

### Registry shape

Registry schema 5 contains `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. A Module descriptor has `id`, `kind="module"`, `title`, `documents`, `references`, `parent`, `uses`, `files` and `checks`. Every array is explicit. `files` holds listing entries: an exact project file, or a directory prefix written with a trailing `/` that binds every regular file below it. It MUST equal the sorted union of the Module's own entity listing declarations, entry for entry, so a directory prefix appears as that prefix and never as its expanded file names; membership, composition and dependency are checked independently of that entry set. The entry names one Module, and its complete collection starts routing.

Each registered reading document has a `.md.json` companion with `schema_version: 1`, `document`
identity/owner and explicit `entities`, `dependencies` and `bindings` arrays. Entity records contain
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

### Scenarios

#### scenario.spec.validate-success — A conforming Spec state validates successfully

- GIVEN a registry and documents that satisfy every structural rule
- WHEN the validator runs
- THEN it returns success with no error findings and a source digest for the assessed state
- BUT success is not represented as proof that every promise is semantically complete

#### scenario.spec.validate-structural-errors — Reporting structural errors, not semantics

- GIVEN a Module missing a required reading-entry section or its metadata companion, an unresolved scenario/requirement/entity identity collision, an entity entry union that disagrees with the registry, or a missing local dependency promise
- WHEN the validator runs
- THEN it returns invalid with one rule-identified, remediable finding per problem
- AND it does not attempt to judge whether the underlying behavior is correct

#### scenario.spec.validate-pending-warning — A created entry still marked pending

- GIVEN an entity lists an exact file or a directory prefix as both present in files and in pending
- AND that file or directory now exists on disk
- WHEN the validator runs
- THEN it reports a warning, not an error
- BUT a declared entry whose file or directory is missing and not marked pending is still an error

#### scenario.spec.validate-architecture-mismatch — Scoped diagram nodes must name declared entities

- GIVEN a Module's Relationships subsection flowchart names an undeclared entity, or an edge has no label
- WHEN the validator runs
- THEN it reports an architecture finding identifying the mismatched or unlabeled elements
- AND it requires every depicted node to name a declared local entity, while permitting scoped omission of inventory nodes

#### scenario.spec.link-anchors — ID-shaped link fragments must resolve to their definition

- GIVEN a registered document with a local link whose fragment has the shape of a scenario, requirement, entity or canonical contract identity
- WHEN the validator resolves that fragment
- THEN it reports a link finding when no definition anywhere carries that identity
- AND it reports a link finding when the link's own document differs from the document that defines the identity
- BUT a link that correctly addresses its defining document, or whose fragment is not ID-shaped, passes without a finding

#### scenario.spec.verification-declarations — Verification declarations live with the tests

- GIVEN the Python test files listed by every Module's entities
- WHEN the validator scans them for scenario verification declarations
- THEN a declared scenario ID that no registered Module defines is reported as an error
- AND a declaring file that its scenario's owning Module does not list is reported as a warning
- AND a listed Python file the validator cannot read for its declarations is reported as an error
- BUT no Spec document lists tests; the declarations live only with the code

#### scenario.spec.reader-parts — Read purpose, usage and design before detailed cases

- GIVEN a registered Module entry with Purpose, Usage, Design and Relationships followed by precise details
- AND paired companion documents that cover their own topics without repeating the entry layout
- WHEN structural validation runs
- THEN it accepts the complete source pairs and nonempty required reading explanations
- BUT it does not claim that those explanations are semantically complete or implemented

#### scenario.spec.reader-parts-invalid — Reject malformed reader-oriented structure

- GIVEN an old enclosing-parts entry, missing metadata, missing or duplicate required sections, wrong heading levels or order, empty required explanations or an unresolved meaning anchor
- WHEN structural validation runs
- THEN it reports a remediable Module-structure error for each detected problem
- AND headings inside code fences do not satisfy required structure

#### scenario.spec.internal-contract-context — Internal obligations retain ordinary identity

- GIVEN a Module defines a requirement and verification scenario under Design
- AND a listed test declares that scenario's stable ID
- WHEN definitions, scenario context and verification coverage are resolved
- THEN the internal definitions retain the same Module ownership and identity rules as external definitions
- AND the scenario resolves the complete owned/direct-reference context, including both source members of every selected document unit
- AND the test declaration contributes coverage without creating another Spec kind or granting code access

### Requirements

#### req.spec.structural-only — Validation checks structure and explicit references

Validation SHALL check structure and explicit references.

#### req.spec.no-semantic-completeness-claim — Validation never claims semantic completeness

Validation SHALL NOT claim to prove semantic completeness.

#### req.spec.host-checks-separate — Host checks execute separately with registered argv

Configured implementation checks SHALL execute separately on the host using their registered argv
and timeout_seconds.

#### req.spec.host-check-not-a-read-substitute — Check results never substitute for reading source

A configured check's result SHALL NOT substitute for an agent reading source.

#### req.spec.digest-per-assessment — Every validation result carries a source digest

Every validation result SHALL carry a source digest of the exact state it assessed.

### Validator interface

`validate_repository(root, target_id=None, package_root=None) -> ToolResult` returns
`status=success|invalid`, findings with `rule_id`, `message` and `remediation`, and a result
containing `source_digest` for the assessed Spec state. It checks identities, document
declarations, unique ownership, one-level references, canonical contract definitions, participant bindings, dependency metadata and readable meaning, scenario/requirement/entity syntax, entity listing
entries against the registry, architecture diagrams, structured contracts and Reflection
attribution; a declared entry whose file or directory is missing is an error unless its entity marks
it pending, a still-pending entry that now exists is a warning, and a regular file that no Module's
entries cover is a warning; it explicitly does not prove semantics. Configured implementation checks
execute separately on the host using the registered `argv` and `timeout_seconds`, returning `check_id`,
`target_id`, `status`, `exit_code`, `source_digest` and `log_digest` with raw output retained
privately. No check result is a source-read proxy for an agent. Validation reads project files and
writes nothing.

### Reference and interface validation

Schema 5 requires a references array on every Module. Each `{kind, id}` must resolve to the
declared Module/document kind; duplicates, self references, document aliases and multiple owners
are errors. Overlap is deduplicated with all provenance, and cycles do not recurse. Each binding's
canonical definition/version must occur in its participant's resolved context; internal peers
require complementary bindings. Definitions have one owner and cannot be duplicated in consumers.
Required links to excluded definitions identify gaps rather than authorizing another read.
Structural checks report missing references/definitions separately from semantic incompleteness.

#### scenario.spec.reference-resolution — Resolve only the selecting Module's references

- GIVEN A references Module B and one B-owned document while B references C
- WHEN A's context is resolved
- THEN each B-owned document appears once with every direct inclusion reason and original owner
- AND no C-owned document appears unless A also directly references it
- AND a scenario query for a B-owned definition resolves B's complete context, including its C reference

#### scenario.spec.reference-invalid — Reject invalid ownership or reference identities

- GIVEN a duplicate owner, wrong-kind or missing reference, unsafe alias, or binding whose definition is absent from the resolved context
- WHEN the registry is validated
- THEN the validator reports the affected document, Module and declaration without silently adding files
- AND no conforming context or interface agreement is claimed

The maintenance-only `scripts/development/check-spec-v5.py` audits the authored registry without
constructing the runtime repository. It checks ownership, references, binding/example shape,
links, reading-subset structure, definition/diagram grammar, entity/file/dependency consistency and manifest
digests; `--base REVISION` also checks stable Requirement/Scenario/Entity ownership against Git.
It is independent documentation evidence, not a lifecycle check or a semantic-completeness claim.
