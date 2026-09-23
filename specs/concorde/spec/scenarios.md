# Spec scenarios

The concrete situations the [Spec tooling](module.md) Module promises to handle. The headings group them by
subject; each scenario belongs to the Module as a whole. The obligations they illustrate are in the
[requirements](requirements.md).

## Loading

### scenario.spec.admit-inventory — Loading a consistent project

- GIVEN a project whose configuration binds the installed Protocol copy
- AND whose registry records every Module with its entry path and a copy of its `module` block
- AND whose entries and registered documents are schema-3 pairs
- WHEN a repository is constructed
- THEN it returns a repository that lists every recorded Module with its owned documents and relations
- AND every relation keeps the source, target and attributes its declaration states
- BUT it reads no Markdown file that no `owns` lists and no implementation file's contents

### scenario.spec.reject-inconsistent-inventory — Refusing a project that cannot be admitted

- GIVEN a project whose registry is not valid JSON, repeats a key, or has a `schema_version` other than 3
- WHEN a repository is constructed
- THEN construction fails with an error naming the file and the problem
- AND no repository is returned
- BUT validating the same project reports the problem as an error finding instead of stopping without a result

### scenario.spec.reject-unsupported-profile — Refusing an unaccepted Protocol

- GIVEN a project whose configuration binds a Protocol version or manifest digest that differs from the copy under `.concorde/protocol/`, whose installed copy has a changed asset, or whose copy differs from the installed Concorde package's Protocol
- WHEN a repository is constructed
- THEN construction fails with `protocol_mismatch`
- BUT a project whose binding names exactly the installed, unchanged copy loads normally

A newer installed Protocol is adopted only when the developer accepts it with `concorde-configure`.

### scenario.spec.document-roles — Explanation and precise definitions in different roles

- GIVEN a Module whose entry and topics have role `module` and whose requirements, scenarios and contracts are in documents with role `implementation`
- WHEN the project is validated
- THEN no role finding is reported
- AND both roles contribute both members to the Module's Spec context
- BUT a requirement, scenario or contract fence in a `module` document fails `CHK.defines.role`, a concept defined in an `implementation` document fails `CHK.defines.role`, and a missing or unknown role fails `CHK.document.role`

## Checks

### scenario.spec.validate-success — A conforming project validates

- GIVEN a project whose declarations satisfy every Protocol check
- WHEN the validator runs
- THEN it returns status `success` with no error findings
- AND the result carries a digest of the assessed inputs
- BUT the result states that semantic completeness is not proven

### scenario.spec.validate-structural-errors — Every violation is reported with its check

- GIVEN a project with several independent violations, such as a duplicate node identity, a Module that uses itself, a file no Module binds and a link to a requirement identity that the linked document does not define
- WHEN the validator runs
- THEN it returns status `invalid`
- AND reports one finding per violation, each naming its check identity, severity, file and a remediation, with `CONCORDE-LINK-001` for the broken link
- BUT it does not stop at the first violation and does not judge whether the described behaviour is correct

### scenario.spec.node-checks — Malformed nodes

- GIVEN an implementation document with a requirement whose first sentence has no `SHALL`, a scenario whose steps return from `THEN` to `GIVEN`, and a `concorde-contract` fence whose example does not satisfy its schema
- AND a module document whose concept record has a `meaning` anchor that does not resolve, or no defining Terminology row
- WHEN the validator runs
- THEN it reports `CHK.requirement.statement`, `CHK.scenario.steps`, `CHK.contract.fence`, `CHK.node.meaning` and `CHK.concept.definition` as errors
- AND an anchor group whose prose is only links or headings is reported as a `CHK.node.explained` warning

### scenario.spec.reader-parts — A well-formed entry and topic

- GIVEN an entry whose first level-2 headings are Purpose, Terminology, Usage, Design and Relationships, in that order
- AND a topic that defines a concept and starts with a Terminology section
- WHEN the validator runs
- THEN no document-structure finding is reported
- BUT passing says nothing about whether the explanations are sufficient

### scenario.spec.reader-parts-invalid — A malformed entry

- GIVEN an entry with a missing, repeated or misordered required section, a Purpose containing a list, or a Usage section holding only links
- WHEN the validator runs
- THEN it reports `CHK.document.sections` or `CHK.document.prose` for each problem
- AND headings inside fences do not count as sections

### scenario.spec.terminology-imports — Terminology rows and imports

- GIVEN a Module document whose Terminology table has a defining row for each concept it defines and a link-only row for a concept of a provider it uses
- WHEN the validator runs
- THEN the import is accepted and the provider's defining document is required in the Module's context
- BUT an import row with a definition fails `CHK.terminology.import-row`, a row with no matching concept fails `CHK.terminology.rows`, an import of the document owner's own concept fails `CHK.imports.foreign`, and an import from a Module that is neither used nor an ancestor is a `CHK.imports.owner` warning

### scenario.spec.composition-checks — Composition and dependency rules

- GIVEN a registry with a composition cycle, a Module with two parents, a Module that uses itself, or two `uses` of one provider
- WHEN the validator runs
- THEN it reports `CHK.contains.acyclic`, `CHK.contains.single-parent`, `CHK.uses.no-self` or `CHK.uses.unique` as errors
- AND more than one Module without a parent is a `CHK.contains.root` warning
- BUT mutual `uses` between two Modules is accepted

### scenario.spec.relies-on — Narrowed dependencies

- GIVEN a Module that uses a provider with `relies_on` listing one requirement and one concept the provider owns
- WHEN the Module's Spec context is resolved
- THEN it contains the provider's entry and the documents defining those two nodes, and no other provider document
- BUT a listed identity the provider does not own fails `CHK.relies-on.owned`, and a link from the relation's meaning section to an unlisted provider node fails `CHK.relies-on.linked`

### scenario.spec.reference-resolution — Only the selecting Module's own relations count

- GIVEN Module A uses Module B, and B uses Module C
- AND A includes one document of Module D with a reason
- WHEN A's Spec context is resolved
- THEN it contains A's documents, B's documents and the included D document, each with the relation that selected it: `owns` for A's own, `uses` of B for B's, `includes` of document D for D's
- AND a document selected by two relations appears once, listing both, and removing either changes the context identity
- BUT no document of C appears unless A itself selects it

### scenario.spec.reference-invalid — Unresolved or misplaced relations

- GIVEN an entry whose `uses` targets an unknown Module, an `includes` that names the Module itself or one of its own documents, a duplicate `includes`, or an `includes` without a reason
- WHEN the validator runs
- THEN it reports `CHK.relation.endpoints`, `CHK.includes.no-self`, `CHK.includes.unique` or `CHK.includes.reason` for the declaration concerned
- AND a spec inclusion whose documents are already selected is a `CHK.includes.redundant` warning
- BUT no document is silently added to or removed from any context

### scenario.spec.context-reconciled — A declaration requires its definition in context

- GIVEN a Module that relates one of its realizations to another Module's concept, without any `uses`, `contains` or `includes` that selects the concept's defining document
- WHEN the validator runs
- THEN it reports `CHK.context.reconciled` naming the Module and the missing document
- BUT adding a `uses` whose selection contains that document removes the finding

### scenario.spec.meaning-relations — Relations between meanings

- GIVEN concepts where one narrows itself through a chain of `narrows`, a `supersedes` from a concept that is not retired, two `contrasts` for one pair, or a `relates` with an empty verb or a source the declaring document does not define
- WHEN the validator runs
- THEN it reports `CHK.narrows.acyclic`, `CHK.concept.retired`, `CHK.contrasts.once`, `CHK.relates.verb` or `CHK.relates.source`
- AND a `relates` whose source is the declaring document's owning Module is accepted

### scenario.spec.name-collision — Same-named nodes of different owners

- GIVEN two concepts of different Modules whose titles differ only in case, hyphens or spacing, or a concept whose title equals another Module's title
- WHEN the validator runs
- THEN it reports `CHK.contrasts.required` for the pair
- BUT a `contrasts` between them with a reason removes the finding, and a concept is never compared with its own Module

### scenario.spec.participation — Contract participation

- GIVEN a contract of version 2 defined by one Module and a peer Module that declares it participates in version 1
- WHEN the validator runs
- THEN it reports `CHK.participates.version`
- AND an internal peer that does not declare the complementary role for the same version fails `CHK.participates.complementary`
- AND a repeated contract, peer and role fails `CHK.participates.unique`

### scenario.spec.validate-architecture-mismatch — Checked flowcharts assert only declarations

- GIVEN a module document with an unmarked Mermaid flowchart
- WHEN the validator runs
- THEN every node label must resolve to one local concept or realization, one Module title, or one qualified `Module title / node title`
- AND every edge must carry a label and match a declared `relates`, `uses` or `contains` in its direction
- BUT an unresolved or ambiguous label fails `CHK.view.nodes`, an unmatched or unlabelled edge fails `CHK.view.edges`, and an unmarked Mermaid block that is not a flowchart fails `CHK.view.marked`

A block marked `mermaid illustrative` is not checked, and a Graph Spec flowchart bound with a graph
comment in an implementation document is checked by the Graph Spec check instead.

### scenario.spec.registry-mirror — A stale registry is reported

- GIVEN a Module whose entry gained a `uses` that its registry record does not have
- WHEN the validator runs
- THEN it reports `CHK.registry.mirror` for that Module
- AND a Module with no registry record, or a record with no matching entry, is reported the same way

## Registry mirror

### scenario.spec.registry-regenerate — Regenerating the mirrored fields

- GIVEN a registry whose records are stale for some Modules
- WHEN the developer runs the registry command with `--write`
- THEN every record's `owns`, `contains`, `uses`, `includes` and `participates` equal its entry's `module` block
- AND each record's identity, title and entry path, and the set of recorded Modules, are unchanged
- BUT with `--check` instead, the command writes nothing and reports each stale record

## Boundary sets

### scenario.spec.select-module — Selecting a Module

- GIVEN a registered Module identity
- WHEN a caller selects it
- THEN the repository returns that Module's descriptor with its entry, owned documents and relations
- AND its Spec context contains both members of every document it owns or selects, each with the declarations that selected it and its original owner

### scenario.spec.select-scenario-focus — Selecting a Module with a scenario focus

- GIVEN a scenario identity owned by a Module
- WHEN a caller selects the Module with that scenario as focus
- THEN the repository returns the same descriptor and the same context as without a focus
- BUT the focus never trims the returned documents

### scenario.spec.reject-foreign-focus — Refusing a focus from another Module

- GIVEN a scenario identity owned by a different Module than the one selected
- WHEN a caller selects the Module with that focus
- THEN selection fails with an invalid-focus error
- AND no descriptor is returned

### scenario.spec.query-files — Resolving an identity to its Spec files

- GIVEN a registered Module identity or scenario identity
- WHEN a caller queries its Spec files
- THEN the result is the Spec context of the Module or of the scenario's owner, both members of each document, without duplicates and sorted by path
- BUT the query reads none of the returned files' contents, and document, requirement and path identities are refused as query targets

### scenario.spec.write-sets — Spec scope and implementation scope

- GIVEN Module A uses Module B and binds `src/a/` with a pending entry `src/a/new.py`
- WHEN A's write sets are computed
- THEN A's Spec scope contains both members of every document A owns and nothing of B
- AND A's implementation scope covers every file below `src/a/` including the not-yet-created `src/a/new.py`
- BUT A's implementation context lists only the names of existing bound files and declared entries, never their contents

### scenario.spec.shared-file — A file bound by several Modules

- GIVEN two Modules that each bind the same file, one exactly and one through a directory entry
- WHEN the repository is loaded
- THEN each Module keeps its own realization entry
- AND the implemented-by index lists both Modules for that file, and each Module's shared files name the other Module with that file
- AND a Spec context requested with shares adds the other Module's documents with a `shares` reason naming that file, while the plain Spec context and both write sets stay unchanged
- BUT within one Module the file belongs to the realization with the longest covering entry

### scenario.spec.directory-entry — A directory entry binds a whole directory

- GIVEN a realization entry ending with `/`
- WHEN the Module's implementation files are listed
- THEN every regular file below the directory is included except those the exclusion rule skips
- AND a file created below it later needs no new declaration
- BUT a longer entry of another realization in the same Module still decides which realization owns the file it covers

### scenario.spec.pending-entries — Pending and missing entries

- GIVEN a realization whose `pending` lists an entry that does not exist yet
- WHEN the validator runs
- THEN no finding is reported for it
- AND once the file exists, `CHK.binds.pending-subset` reports it as an error until the entry leaves `pending`
- AND validating a candidate through the Validation Module first removes such entries from `pending`
- BUT a non-pending entry that does not exist fails `CHK.binds.exists`, and a `pending` item missing from `entries` fails `CHK.binds.pending-subset`

### scenario.spec.unbound-file — Every tracked file is bound

- GIVEN a version-controlled source file that no realization covers
- WHEN the validator runs
- THEN it reports `CHK.binds.unbound` for that path
- BUT document members, files under `.concorde/`, generated outputs and declared external material are never reported, and a bound document member fails `CHK.binds.no-spec`

### scenario.spec.external-reference — Pinned external material

- GIVEN a Module with an `includes` of kind `external` naming a directory of vendored material tracked by version control
- WHEN its external context is resolved
- THEN it contains the readable files below that directory, media and archives excluded, identified by one digest over their paths and bytes
- AND the material enters neither the Spec context nor the implementation context
- BUT a missing or untracked path fails `CHK.external.exists`, and a path overlapping a document member or realization entry fails `CHK.external.no-overlap`

### scenario.spec.impact-indexes — Whom a change concerns

- GIVEN Module A uses Module B with `relies_on` listing a requirement defined in B's requirements document
- AND Module C includes that same B document
- WHEN a caller asks which Modules a change concerns
- THEN a change to that document concerns B, A and C through the selected-by index
- AND a change to the listed requirement concerns A through the referenced-by index
- AND a change to a file bound by two Modules concerns both through the implemented-by index
- BUT the indexes add nothing to any Module's boundary sets

## Coverage

### scenario.spec.verification-declarations — Tests declare the scenarios they verify

- GIVEN Python and TypeScript tests bound by Modules, some with verification declarations
- WHEN the validator reads them
- THEN a declaration of an unknown scenario fails `CHK.verifies.resolves`
- AND a scenario that no declaration names is a `CONCORDE-COVERAGE-001` warning, unless its Module binds no files
- AND a declaration in a test that the scenario's owner does not bind is a `CONCORDE-COVERAGE-002` warning
- AND a Python test that cannot be parsed, or a malformed declaration, is a `CONCORDE-COVERAGE-003` error
- BUT test-declaration syntax in Spec reading outside a fence fails `CHK.evidence.no-spec-coverage`

## Typed values

### scenario.spec.task-control-values — Checking task metadata values

- GIVEN a `concorde-task-scope-feedback` or `concorde-task-identity-constraints` value as described in the [interface definitions](contracts.md#task-metadata-values)
- WHEN it is checked as a typed value
- THEN a valid version-1 value is returned unchanged
- AND an unknown field, a malformed digest, another reason value, a blank or repeated reserved identity, a wrong type or another version is refused with an error naming its code and field
- BUT checking reads and writes no project file and grants no authority

## Initialization

### scenario.spec.propose-initialization — Proposing a new project

- GIVEN a project where the installer has placed the Protocol copy but no configuration exists
- WHEN the developer calls `concorde-init` with `action: "propose"`, a name and a worker configuration
- THEN the result is an initial proposal with the configuration, the registry, and a root entry with its metadata
- AND the root entry says the project's purpose, behaviour and architecture are not yet specified
- AND its metadata binds the project's existing tracked and not-ignored files in one realization, Existing project files
- AND every proposed file has a null before-digest
- BUT no project file is written

### scenario.spec.apply-initialization — Applying an accepted proposal

- GIVEN a proposal returned by propose whose destinations are all still absent
- WHEN the developer calls `concorde-init` with `action: "apply"` and that exact proposal
- THEN every proposed file is written in one file transaction and the resulting project validates
- AND the result has status `applied` and lists the written paths
- BUT no Protocol copy or other installer output is created

### scenario.spec.reject-already-initialized — A configured project is not reinitialized

- GIVEN a project that already has `.concorde/config.json`
- WHEN initialization is proposed
- THEN it fails with `already_initialized`
- AND no file changes

### scenario.spec.reject-stale-or-invalid-proposal — A changed or malformed proposal is refused

- GIVEN a proposal whose envelope is incomplete, whose Protocol binding no longer matches the installed copy, that writes outside its allowed files, or one of whose destinations now exists
- WHEN apply is requested
- THEN it fails with `invalid_proposal`, `permission_denied` or `stale_proposal`
- AND no file is written

### scenario.spec.rollback-on-failure — Restoring original bytes after a failure

- GIVEN a file transaction that has written some of its files
- WHEN a later write or the final check of the result fails
- THEN every written file is restored to its original bytes, and files that did not exist are removed
- AND the failure is reported, never success
- BUT a failure during the restoration is itself reported as a failure, not as a completed rollback
