```concorde-document
{
  "id": "document.spec.structure",
  "owner": "module.spec",
  "main_visible": true
}
```

# Spec structure and validation

This document defines the registry shape this Module admits and the deterministic validation it performs against that shape. Selection and returned value records are defined in [registry](registry.md) and [values](values.md); the admission scenarios for a consistent or inconsistent inventory are defined in [module](module.md).

## Registry shape

Registry schema 4 contains `schema_version`, `project_id`, `entry_target`, `targets` and `checks`. A Module descriptor has `id`, `kind="module"`, `title`, `documents`, `references`, `parent`, `uses`, `files` and `checks`. Every array is explicit. `files` holds listing entries: an exact project file, or a directory prefix written with a trailing `/` that binds every regular file below it. It MUST equal the sorted union of the Module's own entity listing declarations, entry for entry, so a directory prefix appears as that prefix and never as its expanded file names; membership, composition and dependency are checked independently of that entry set. The entry names one Module, and its complete collection starts routing.

Each Markdown document declares `id`, its sole `owner` and `main_visible`. A Module's `concorde-dependencies` entries contain `target_id`, `responsibility`, `selection_condition` and nonempty `relied_upon_promises`, covering exactly its children and `uses` targets. A Module's `concorde-entities` blocks declare `id`, `title`, `kind`, `responsibility` and optionally `files`, `pending` and `target_id`; every child and used Module needs exactly one entity naming it by `target_id`. `files` entries are exact files or directory prefixes, `pending` may mark either kind as declared but not yet created, and within one Module the most specific entry owns a covered file: an exact file before a directory, and a longer directory before a shorter one. A listed directory MUST NOT contain a registered Spec document. Every Concorde Module has a principal entity diagram in its `module.md` Relationships subsection, whose node labels equal its own entity titles, excluding referenced foreign definitions, as required by the Protocol. Check records declare `id`, `target_id`, `argv`, `timeout_seconds` and optional `inputs`. Shared implementation changes affect every Module whose entries cover the changed file, whether exactly or through a directory prefix; validation and downstream tools evaluate each affected Module's own contract separately.

Topology preparation stores the exact validated registry/document replacements below the ignored `.concorde/topology-proposals/` host area. Its public ArtifactRef binds path and digest. Applying the artifact rechecks its embedded design identity, discovery context, Protocol, registry base and every file before-digest before one atomic transaction.

## Scenarios

### scenario.spec.validate-success — A conforming Spec state validates successfully

- GIVEN a registry and documents that satisfy every structural rule
- WHEN the validator runs
- THEN it returns success with no error findings and a source digest for the assessed state
- BUT success is not represented as proof that every promise is semantically complete

### scenario.spec.validate-structural-errors — Reporting structural errors, not semantics

- GIVEN a Module missing one of its four mandatory sections, an unresolved scenario/requirement/entity identity collision, an entity entry union that disagrees with the registry, or a missing local dependency promise
- WHEN the validator runs
- THEN it returns invalid with one rule-identified, remediable finding per problem
- AND it does not attempt to judge whether the underlying behavior is correct

### scenario.spec.validate-pending-warning — A created entry still marked pending

- GIVEN an entity lists an exact file or a directory prefix as both present in files and in pending
- AND that file or directory now exists on disk
- WHEN the validator runs
- THEN it reports a warning, not an error
- BUT a declared entry whose file or directory is missing and not marked pending is still an error

### scenario.spec.validate-architecture-mismatch — Diagram nodes must equal entity titles

- GIVEN a Module's Relationships subsection flowchart nodes differ from its declared entity titles, or an edge has no label
- WHEN the validator runs
- THEN it reports an architecture finding identifying the mismatched or unlabeled elements
- AND it requires the diagram nodes to be exactly the entity titles before the Module can validate successfully

### scenario.spec.link-anchors — ID-shaped link fragments must resolve to their definition

- GIVEN a registered document with a local link whose fragment has the shape of a scenario, requirement, entity or canonical contract identity
- WHEN the validator resolves that fragment
- THEN it reports a link finding when no definition anywhere carries that identity
- AND it reports a link finding when the link's own document differs from the document that defines the identity
- BUT a link that correctly addresses its defining document, or whose fragment is not ID-shaped, passes without a finding

### scenario.spec.verification-declarations — Verification declarations live with the tests

- GIVEN the Python test files listed by every Module's entities
- WHEN the validator scans them for scenario verification declarations
- THEN a declared scenario ID that no registered Module defines is reported as an error
- AND a declaring file that its scenario's owning Module does not list is reported as a warning
- AND a listed Python file the validator cannot read for its declarations is reported as an error
- BUT no Spec document lists tests; the declarations live only with the code

## Requirements

### req.spec.structural-only — Validation checks structure and explicit references

Validation SHALL check structure and explicit references.

### req.spec.no-semantic-completeness-claim — Validation never claims semantic completeness

Validation SHALL NOT claim to prove semantic completeness.

### req.spec.host-checks-separate — Host checks execute separately with registered argv

Configured implementation checks SHALL execute separately on the host using their registered argv
and timeout_seconds.

### req.spec.host-check-not-a-read-substitute — Check results never substitute for reading source

A configured check's result SHALL NOT substitute for an agent reading source.

### req.spec.digest-per-assessment — Every validation result carries a source digest

Every validation result SHALL carry a source digest of the exact state it assessed.

## Validator interface

`validate_repository(root, target_id=None, package_root=None) -> ToolResult` returns
`status=success|invalid`, findings with `rule_id`, `message` and `remediation`, and a result
containing `source_digest` for the assessed Spec state. It checks identities, document
declarations, unique ownership, one-level references, canonical contract definitions, participant bindings, dependency blocks, scenario/requirement/entity syntax, entity listing
entries against the registry, architecture diagrams, structured contracts and Reflection
attribution; a declared entry whose file or directory is missing is an error unless its entity marks
it pending, a still-pending entry that now exists is a warning, and a regular file that no Module's
entries cover is a warning; it explicitly does not prove semantics. Configured implementation checks
execute separately on the host using the registered `argv` and `timeout_seconds`, returning `check_id`,
`target_id`, `status`, `exit_code`, `source_digest` and `log_digest` with raw output retained
privately. No check result is a source-read proxy for an agent. Validation reads project files and
writes nothing.

## Reference and interface validation

Schema 4 requires a references array on every Module. Each `{kind, id}` must resolve to the
declared Module/document kind; duplicates, self references, document aliases and multiple owners
are errors. Overlap is deduplicated with all provenance, and cycles do not recurse. Each binding's
canonical definition/version must occur in its participant's resolved context; internal peers
require complementary bindings. Definitions have one owner and cannot be duplicated in consumers.
Required links to excluded definitions identify gaps rather than authorizing another read.
Structural checks report missing references/definitions separately from semantic incompleteness.

### scenario.spec.reference-resolution — Resolve only the selecting Module's references

- GIVEN A references Module B and one B-owned document while B references C
- WHEN A's context is resolved
- THEN each B-owned document appears once with every direct inclusion reason and original owner
- AND no C-owned document appears unless A also directly references it
- AND a scenario query for a B-owned definition resolves B's complete context, including its C reference

### scenario.spec.reference-invalid — Reject invalid ownership or reference identities

- GIVEN a duplicate owner, wrong-kind or missing reference, unsafe alias, or binding whose definition is absent from the resolved context
- WHEN the registry is validated
- THEN the validator reports the affected document, Module and declaration without silently adding files
- AND no conforming context or interface agreement is claimed

The maintenance-only `scripts/development/check-spec-v5.py` audits the authored registry without
constructing a legacy runtime repository. It checks ownership, references, binding/example shape,
links, the unchanged Markdown/diagram grammar, entity/file/dependency consistency and manifest
digests; `--base REVISION` also checks stable Requirement/Scenario/Entity ownership against Git.
It is independent documentation evidence, not a lifecycle check or a semantic-completeness claim.
