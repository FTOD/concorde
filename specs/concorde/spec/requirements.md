# Spec requirements

These precise specifications belong directly to the [Spec Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Registry](../module.md#terminology) | Defined in Concorde Framework. |
| [Snapshot](../module.md#terminology) | Defined in Concorde Framework. |
| [Entity](../module.md#terminology) | Defined in Concorde Framework. |
| [Implementation binding](registry.md#terminology) | Defined in Registry. |
| [Structural validation](structure.md#terminology) | Defined in What structural validation tells you. |
| [Semantic completeness](structure.md#terminology) | Defined in What structural validation tells you. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Initialization](initialize.md#terminology) | Defined in Project initialization. |
| [Initial proposal](initialize.md#terminology) | Defined in Project initialization. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |

## Spec

### req.spec.no-body-read — Metadata resolution does not read collaborator bodies

Resolving a Module's identity, ownership or file listing SHALL NOT read a collaborator Module's
Spec body or a listed file's contents.

### req.spec.one-owner-per-module — One owning entity per bound file

Within one Module, a bound implementation file SHALL belong to exactly one entity, the owner of the
most specific entry that covers it.

### req.spec.directory-entry — Directory prefix binds every file below it

A listing entry that ends with `/` SHALL bind every regular file below that directory.

### req.spec.directory-no-spec-document — No Spec document inside a listed directory

A listed directory SHALL NOT contain a registered Spec document.

### req.spec.sibling-sharing — Shared providers may cross hierarchy levels

A shared provider SHALL be admissible independently of its consumers' hierarchy levels, provided
it is not structurally owned by one of those consumers.

Sharing preserves the provider's single identity and at most one structural parent. The ordinary
identity, parentage and composition-cycle checks still apply; cross-level use neither reparents the
provider nor grants its documents or implementation implicitly.

### req.spec.no-structural-proof — Structural checks are not semantic proof

Structural validation SHALL NOT be represented as proof of semantic completeness.

## Registry

### req.spec.no-writes — No writes during construction or queries

SpecRepository construction and every query method SHALL NOT write project files.

### req.spec.snapshot-reconstruct — A repository instance is an immutable snapshot

A repository instance SHALL be treated as a snapshot.

### req.spec.reconstruct-for-changes — Reconstruct the repository to see changes

A caller SHALL reconstruct the repository to observe source changes.

### req.spec.deterministic-order — Deterministic order for repeated queries

Repeated queries against the same admitted repository SHALL return results in the same order.

### req.spec.local-contracts-only — Definition ownership stays local

contracts(target) SHALL return only canonical definitions in documents owned by the target.

### req.spec.contracts-defer-agreement-checks — Cross-Module checks stay with the validator

contracts(target) SHALL leave canonical-definition uniqueness and cross-Module binding checks to the
repository validator.

## Spec structure and validation

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

## Project initialization

### req.spec.init-allowed-files — Initialization touches only its allowed files

Application SHALL touch only .concorde/config.json, .concorde/specs.json,
.concorde/topology-proposals/.gitignore, .concorde/issues/.gitignore and the explicit document paths named in the proposed registry.

### req.spec.init-null-digests — Every proposed file has a null before_digest

Every proposed file SHALL have a null before_digest.

### req.spec.init-destination-absent — Application requires each destination to still be absent

Application SHALL require each proposed destination to still be absent.

### req.spec.init-no-overwrite — New initialization never overwrites an existing file

A new initialization SHALL NOT overwrite an existing file.

### req.spec.init-no-profile-migration — Older profile configurations are not migratable

An existing configuration declaring an older profile SHALL NOT be treated as migratable.

### req.spec.init-explicit-envelope — Apply admits only the exact proposal envelope

Apply SHALL admit the proposal by its exact concorde-project-proposal@1 envelope.

### req.spec.init-no-token-substitute — Apply rejects issuance tokens and store lookups

Apply SHALL NOT accept an issuance token or a store lookup in place of that exact proposal
envelope.

### req.spec.init-configuration-roles — Outer configuration controls host settings only

The invocation's outer configuration SHALL control host settings for the call itself.

### req.spec.init-propose-configuration-role — Propose controls the proposal's settings

The propose request's configuration SHALL control the project settings written into the proposal.

### req.spec.init-apply-uses-proposal-configuration — Apply uses the proposal's configuration bytes

Apply SHALL use the accepted proposal's configuration bytes rather than a replacement from either
invocation field.

### req.spec.init-configuration-required — Null outer configuration loads existing settings

A null outer configuration SHALL load existing project settings.

### req.spec.init-requires-outer-configuration — Uninitialized projects require outer configuration

Before a project is initialized no such settings exist, so the caller SHALL supply a valid outer
configuration or receive configuration_mismatch.

### req.spec.init-worktree-handoff — Initialization from primary applies only in the candidate

An initialization requested from the primary worktree SHALL apply in the host-created candidate
worktree and report that candidate, never as an applied initialization of the primary worktree.

### req.spec.init-no-blind-retry — No blind retries of a rejected proposal

The host SHALL NOT silently retry a rejected proposal against different bytes.
