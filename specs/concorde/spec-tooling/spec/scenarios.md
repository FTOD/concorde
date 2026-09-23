# Spec scenarios

The concrete situations the [Spec core](module.md) Module promises to handle, one outcome each.
The headings group them by subject; each scenario belongs to the Module as a whole. The obligations
they illustrate are in the [requirements](requirements.md).

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
- WHEN a repository is constructed for a consumer
- THEN construction fails with an error naming the file and the problem
- AND no repository is returned

### scenario.spec.validate-unreadable-registry — Validating a project whose registry cannot be read

- GIVEN a project whose registry is not valid JSON
- WHEN the validator runs
- THEN it returns status `invalid` with one `CONCORDE-SOURCE-008` error naming the problem
- BUT it raises no exception and writes no file

### scenario.spec.reject-unsupported-profile — Refusing an unaccepted Protocol

- GIVEN a project whose configuration binds a Protocol version or manifest digest that differs from the copy under `.concorde/protocol/`, whose installed copy has a changed asset, or whose copy differs from the running package's Protocol
- WHEN a repository is constructed
- THEN construction fails with `protocol_mismatch`
- AND no repository is returned

A newer installed Protocol is adopted only when the developer explicitly rebinds the configuration
to it.

### scenario.spec.reject-configuration-profile — Refusing another configuration profile

- GIVEN a project whose configuration has a `profile_version` other than the one this Concorde supports
- WHEN a repository is constructed
- THEN construction fails with `unsupported_profile`
- AND the configuration is not reinterpreted

### scenario.spec.document-roles — Explanation and precise definitions in different roles

- GIVEN a Module whose entry and topics have role `module` and whose requirements, scenarios and contracts are in documents with role `implementation`
- WHEN the project is validated
- THEN no role finding is reported
- AND both roles contribute both members to the Module's Spec context

### scenario.spec.document-role-misplaced — Definitions in the wrong role

- GIVEN a requirement, scenario or contract fence in a `module` document, a concept defined in an `implementation` document, or a document with a missing or unknown role
- WHEN the validator runs
- THEN it reports `CHK.defines.role` for each misplaced definition and `CHK.document.role` for the missing or unknown role

## Checks

### scenario.spec.validate-success — A conforming project validates

- GIVEN a project whose declarations satisfy every Protocol check and every Concorde convention
- WHEN the validator runs
- THEN it returns status `success` with no error findings
- AND the result carries a digest of the assessed inputs
- AND the result states that semantic completeness is not proven

### scenario.spec.validate-structural-errors — Every violation is reported with its check

- GIVEN a project with several independent violations, such as a duplicate node identity, a Module that uses itself, a file no Module binds and a link to a requirement identity that the linked document does not define
- WHEN the validator runs
- THEN it returns status `invalid`
- AND reports one finding per violation, each naming its rule identity, severity, file and a remediation, with `CONCORDE-LINK-001` for the broken link
- BUT it does not stop at the first violation and does not judge whether the described behaviour is correct

### scenario.spec.node-checks — Malformed nodes

- GIVEN an implementation document with a requirement whose first sentence has no `SHALL`, a scenario whose steps return from `THEN` to `GIVEN`, and a `concorde-contract` fence whose example does not satisfy its schema
- AND a module document whose concept record has a `meaning` anchor that does not resolve, or no defining Terminology row
- WHEN the validator runs
- THEN it reports `CHK.requirement.statement`, `CHK.scenario.steps`, `CHK.contract.fence`, `CHK.node.meaning` and `CHK.concept.definition` as errors

### scenario.spec.node-unexplained — An anchor with no explanation

- GIVEN a module document whose anchor group is followed only by links and headings
- WHEN the validator runs
- THEN it reports a `CHK.node.explained` warning for that anchor group
- AND the status is not made `invalid` by it

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
- BUT headings inside fences do not count as sections

### scenario.spec.terminology-imports — Importing a provider's term

- GIVEN a Module document whose Terminology table has a defining row for each concept it defines and a link-only row for a concept of a provider it uses
- WHEN the validator runs
- THEN the import is accepted without a finding
- AND the provider's defining document is required in the Module's context

### scenario.spec.terminology-import-invalid — Malformed Terminology rows

- GIVEN an import row with a definition, a defining row with no matching concept, or an import of a concept the document's own Module owns
- WHEN the validator runs
- THEN it reports `CHK.terminology.import-row`, `CHK.terminology.rows` or `CHK.imports.foreign` as an error for each row

### scenario.spec.import-owner-warning — Importing from an unrelated Module

- GIVEN a Module that imports a concept owned by a Module it neither uses, contains nor descends from
- AND the defining document is in its context through an inclusion
- WHEN the validator runs
- THEN it reports a `CHK.imports.owner` warning naming the concept and its owner

### scenario.spec.composition-checks — Composition and dependency errors

- GIVEN a registry with a composition cycle, a Module with two parents, a Module that uses itself, or two `uses` of one provider
- WHEN the validator runs
- THEN it reports `CHK.contains.acyclic`, `CHK.contains.single-parent`, `CHK.uses.no-self` or `CHK.uses.unique` as errors

### scenario.spec.multiple-roots — More than one root

- GIVEN a project in which two Modules have no parent
- WHEN the validator runs
- THEN it reports a `CHK.contains.root` warning

### scenario.spec.mutual-uses — Two Modules that use each other

- GIVEN two Modules that each declare a `uses` of the other
- WHEN the validator runs
- THEN no composition or dependency finding is reported for them
- AND each Module's Spec context contains the other's selected documents, one level deep

### scenario.spec.relies-on — Narrowed dependencies

- GIVEN a Module that uses a provider with `relies_on` listing one requirement and one concept the provider owns
- WHEN the Module's Spec context is resolved
- THEN it contains the provider's entry and the documents defining those two nodes
- BUT no other document of the provider

### scenario.spec.relies-on-invalid — A `relies_on` that does not match its explanation

- GIVEN a `uses` whose `relies_on` names a node the provider does not own, and whose meaning section links to a provider node the list omits
- WHEN the validator runs
- THEN it reports `CHK.relies-on.owned` for the foreign node and `CHK.relies-on.linked` for the unlisted link

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
- BUT no document is silently added to or removed from any context

### scenario.spec.includes-redundant — A redundant inclusion

- GIVEN a Module that includes a document it already selects through a `uses` without `relies_on`
- WHEN the validator runs
- THEN it reports a `CHK.includes.redundant` warning for the inclusion
- AND the document still appears once in the context, listing both relations

### scenario.spec.context-reconciled — A declaration requires its definition in context

- GIVEN a Module that relates one of its realizations to another Module's concept, without any `uses`, `contains` or `includes` that selects the concept's defining document
- WHEN the validator runs
- THEN it reports `CHK.context.reconciled` naming the Module and the missing document

### scenario.spec.meaning-relations — Invalid relations between meanings

- GIVEN concepts where one narrows itself through a chain of `narrows`, a `supersedes` from a concept that is not retired, two `contrasts` for one pair, or a `relates` with an empty verb or a source the declaring document does not define
- WHEN the validator runs
- THEN it reports `CHK.narrows.acyclic`, `CHK.concept.retired`, `CHK.contrasts.once`, `CHK.relates.verb` or `CHK.relates.source`

### scenario.spec.relates-module-source — A Module as the source of `relates`

- GIVEN a document whose metadata declares a `relates` whose source is the document's owning Module and whose target's defining document is in that Module's context
- WHEN the validator runs
- THEN the relation is accepted without a finding

### scenario.spec.name-collision — Same-named nodes of different owners

- GIVEN two concepts of different Modules whose titles differ only in case, hyphens or spacing, or a concept whose title equals another Module's title, with no `contrasts` between them
- WHEN the validator runs
- THEN it reports `CHK.contrasts.required` for the pair
- BUT a concept is never compared with its own Module

### scenario.spec.name-collision-contrasted — A declared contrast settles a collision

- GIVEN two same-named concepts of different Modules
- AND a `contrasts` between them with a reason
- WHEN the validator runs
- THEN no `CHK.contrasts.required` finding is reported for the pair

### scenario.spec.participation — Contract participation

- GIVEN a contract of version 2 defined by one Module and a peer Module that declares it participates in version 1
- WHEN the validator runs
- THEN it reports `CHK.participates.version`
- AND an internal peer that does not declare the complementary role for the same version fails `CHK.participates.complementary`
- AND a repeated contract, peer and role fails `CHK.participates.unique`

### scenario.spec.checked-flowchart — A checked flowchart that asserts only declarations

- GIVEN a module document with an unmarked Mermaid flowchart whose node labels name local concepts and realizations, Module titles and qualified `Module title / node title` labels
- AND every edge is labelled and matches a declared `relates`, `uses` or `contains` in its direction
- WHEN the validator runs
- THEN no view finding is reported
- AND a block marked `mermaid illustrative` in the same document is not checked

### scenario.spec.validate-architecture-mismatch — A flowchart that asserts something undeclared

- GIVEN a module document with an unmarked Mermaid flowchart that has an unresolved or ambiguous node label and an edge with no matching declaration, and an unmarked Mermaid block that is not a flowchart
- WHEN the validator runs
- THEN it reports `CHK.view.nodes` for the label, `CHK.view.edges` for the edge and `CHK.view.marked` for the unmarked block

### scenario.spec.check-input-missing — A configured check names a missing input

- GIVEN a configuration whose configured check declares an input path that does not exist, or one reached through a symbolic link
- WHEN the validator runs
- THEN it reports `CONCORDE-CHECK-001` as an error naming the check and the path
- BUT it runs no check and reads no input's content

### scenario.spec.registry-mirror — A stale registry is reported

- GIVEN a Module whose entry gained a `uses`, or changed its title, without its registry record following
- WHEN the validator runs
- THEN it reports `CHK.registry.mirror` for that Module
- AND a Module with no registry record, or a record with no matching entry, is reported the same way

## Registry mirror

### scenario.spec.registry-regenerate — Regenerating the mirrored fields

- GIVEN a registry whose records are stale for some Modules
- WHEN the developer runs the registry command with `--write`
- THEN every record's `title`, `owns`, `contains`, `uses`, `includes` and `participates` equal its entry's `module` block
- AND each record's identity and entry path, the record order and the set of recorded Modules are unchanged

### scenario.spec.registry-check — Checking the mirror without writing

- GIVEN a registry whose records are stale for some Modules
- WHEN the developer runs the registry command with `--check`
- THEN it reports one `CHK.registry.mirror` finding per stale record
- BUT it writes no file

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
- BUT the query reads none of the returned files' contents

### scenario.spec.query-invalid-target — Refusing an identity that has no context

- GIVEN a document, requirement or concept identity, or a path
- WHEN a caller queries its Spec files
- THEN the query fails with `invalid_target`
- AND no context is returned

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
- AND the implemented-by index lists both Modules for that file, and each Module's binding Modules name the other with that file
- BUT neither Module's Spec context nor either write set changes because of the sharing

### scenario.spec.directory-entry — A directory entry binds a whole directory

- GIVEN a realization entry ending with `/`
- WHEN the Module's implementation files are listed
- THEN every regular file below the directory is included except those the exclusion rule skips
- AND a file created below it later needs no new declaration

### scenario.spec.longest-entry — The longest covering entry decides the realization

- GIVEN a Module with one realization binding `src/a/` and another binding `src/a/special.py`
- WHEN the realization of `src/a/special.py` is looked up
- THEN it is the realization with the exact entry
- AND every other file below `src/a/` belongs to the directory realization

### scenario.spec.pending-entries — A pending entry that does not exist yet

- GIVEN a realization whose `pending` lists an entry that does not exist yet
- WHEN the validator runs
- THEN no finding is reported for it
- AND the entry is part of the Module's implementation scope

### scenario.spec.pending-materialized — A pending entry whose file now exists

- GIVEN a realization whose `pending` lists an entry whose file now exists
- WHEN the validator runs
- THEN it reports `CHK.binds.pending-subset` as an error for that entry

### scenario.spec.pending-confirm — Confirming pending entries

- GIVEN realizations whose `pending` lists some entries whose files now exist and some that are still missing
- WHEN a caller confirms pending entries
- THEN the existing entries leave `pending` in one file transaction that rewrites only the affected metadata members
- AND the result lists each confirmed entry with its Module and realization, and each still-missing entry
- BUT no reading member and no registry byte changes

### scenario.spec.missing-entry — A declared entry that does not exist

- GIVEN a realization with a non-pending entry that does not exist, or a `pending` item that is not in `entries`
- WHEN the validator runs
- THEN it reports `CHK.binds.exists` for the missing entry and `CHK.binds.pending-subset` for the stray pending item

### scenario.spec.unbound-file — Every tracked file is bound

- GIVEN a version-controlled source file that no realization covers
- WHEN the validator runs
- THEN it reports `CHK.binds.unbound` for that path

### scenario.spec.unbound-exemptions — Files that need no binding

- GIVEN version-controlled document members, files under `.concorde/`, generated outputs and declared external material that no realization covers
- WHEN the validator runs
- THEN no `CHK.binds.unbound` finding is reported for them

### scenario.spec.bound-spec-member — A realization binds a Spec document

- GIVEN a realization entry that names a document member, or a directory entry that contains one
- WHEN the validator runs
- THEN it reports `CHK.binds.no-spec` for that entry

### scenario.spec.external-reference — Pinned external material

- GIVEN a Module with an `includes` of kind `external` naming a directory of vendored material tracked by version control
- WHEN its external context is resolved
- THEN it contains the readable files below that directory, media and archives excluded, identified by one digest over their paths and bytes
- AND the material enters neither the Spec context nor the implementation context

### scenario.spec.external-reference-invalid — Missing or overlapping external material

- GIVEN an external inclusion whose path is missing or untracked, and another whose path overlaps a document member or a realization entry
- WHEN the validator runs
- THEN it reports `CHK.external.exists` for the first and `CHK.external.no-overlap` for the second

### scenario.spec.impact-indexes — Whom a change concerns

- GIVEN Module A uses Module B with `relies_on` listing a requirement defined in B's requirements document
- AND Module C includes that same B document
- AND Modules B and D bind the same file
- WHEN a caller asks which Modules a change concerns
- THEN a change to that document concerns B, A and C through the selected-by index
- AND a change to the listed requirement concerns A through the referenced-by index
- AND a change to the shared file concerns B and D through the implemented-by index
- BUT the indexes add nothing to any Module's boundary sets

### scenario.spec.changed-definitions — Comparing two revisions of the Specs

- GIVEN two repositories of the same project at different revisions
- AND in the later one a requirement's statement changed while its document's other definitions did not
- WHEN a caller asks for the changed documents and the changed nodes between them
- THEN the changed documents are the documents whose members differ
- AND the changed nodes are exactly the nodes whose defining section, contract fence, concept record and definition row, realization record or entry `module` block differ

## Grants

### scenario.spec.grant-understand — An understanding grant reads Specs and names code

- GIVEN Module A that binds `src/a/`, uses Module B and includes pinned external material under `reference/lib/`
- WHEN a grant for task type `understand` and Module A is computed
- THEN both members of every document in A's Spec context are listed as `ro`
- AND every existing file below `src/a/` is listed as `names`
- AND `reference/lib/` is listed as `ro`
- BUT no path is `rw`, and no file of B's realization or of any other Module appears

A `review-spec` grant for the same Module is equal to it apart from its task type.

### scenario.spec.grant-specify — A specification grant writes the Module's own documents

- GIVEN Module A that owns three documents and uses Module B
- WHEN a grant for task type `specify` and Module A is computed
- THEN both members of A's own documents are listed as `rw`
- AND B's selected documents are listed as `ro`
- AND A's implementation files are listed as `names`
- BUT no implementation file is `ro` or `rw`

### scenario.spec.grant-implement — An implementation grant writes the realization

- GIVEN Module A with a realization binding `src/a/` and another with the pending exact entry `src/b.py`
- WHEN a grant for task type `implement` and Module A is computed
- THEN `src/a/` and `src/b.py` are listed as `rw`, although `src/b.py` does not exist yet
- AND A's documents are listed as `ro`, never `rw`
- AND no file below `src/a/` is listed separately as `names`

### scenario.spec.grant-read-code — Testing and code review read the realization

- GIVEN Module A with a realization binding `src/a/`
- WHEN grants for task types `test` and `review-code` and Module A are computed
- THEN each lists `src/a/` as `ro` and A's Spec context as `ro`
- BUT neither lists any path as `rw`

### scenario.spec.grant-multi-module — Several Modules receive the union at the highest level

- GIVEN Module A that uses Module B without `relies_on`
- WHEN a grant for task type `specify` and Modules A and B is computed
- THEN both members of every document A or B owns are listed as `rw`
- AND each path appears once, at the highest level any bound Module's sets assign
- AND the grant names both Modules

### scenario.spec.grant-shared-file — A shared file needs every binding Module

- GIVEN Modules A and D that both bind `src/shared.py`
- WHEN a grant for task type `implement` and Module A alone is computed
- THEN the computation fails with `shared_file`, naming `src/shared.py` and Module D
- AND no grant is returned
- BUT a grant for task type `implement` and Modules A and D lists `src/shared.py` as `rw`, and a grant for task type `understand` and Module A alone lists it as `names`

### scenario.spec.grant-invalid — An unanswerable request gets no grant

- GIVEN a request with an unknown task type, an unregistered Module identity or an empty Module list
- WHEN a grant is computed
- THEN it fails with `invalid_task_type`, `unknown_module` or `invalid_input` respectively
- AND no grant is returned and no file is written

### scenario.spec.grant-worktree — A grant comes from the worktree it names

- GIVEN a primary worktree and a task worktree in which Module A's metadata additionally declares the pending exact entry `lib/extra.py`
- WHEN a grant for task type `implement` and Module A is computed with the task worktree as root
- THEN `lib/extra.py` is listed as `rw`
- BUT a grant computed with the primary worktree as root does not list it
- AND the two grants carry different context identities

### scenario.spec.context-identity — The context identity changes only with the context

- GIVEN a grant for Module A, which uses Module B
- WHEN one byte of a B document A selects changes, a redundant inclusion of that document is removed, or an implementation file of A changes
- THEN the recomputed context identity differs after the change to the document and after the removal of the inclusion
- BUT it is unchanged after the change to the implementation file

## Coverage

### scenario.spec.verification-declarations — Tests declare the scenarios they verify

- GIVEN Python and TypeScript tests bound by the Module that owns the scenarios they declare
- WHEN the validator reads them
- THEN every declared scenario is covered by the declaring test, with its path, line and name
- AND no coverage finding is reported for those scenarios

### scenario.spec.verifies-unknown — A declaration names an unknown scenario

- GIVEN a bound test that declares a scenario identity no Spec defines
- WHEN the validator runs
- THEN it reports `CHK.verifies.resolves` as an error at that declaration

### scenario.spec.coverage-uncovered — A scenario no test declares

- GIVEN a scenario of a Module that binds files, which no bound test declares
- WHEN the validator runs
- THEN it reports a `CONCORDE-COVERAGE-001` warning for the scenario
- BUT a scenario of a Module that binds no files is not reported

### scenario.spec.coverage-foreign-test — A declaration in a test the owner does not bind

- GIVEN a test bound only by Module A that declares a scenario of Module B
- WHEN the validator runs
- THEN it reports a `CONCORDE-COVERAGE-002` warning naming the test and the scenario
- AND the scenario still counts as declared

### scenario.spec.coverage-parse-error — An unreadable test does not stop the scan

- GIVEN one bound Python test file that does not parse
- AND another bound test that declares an unknown scenario
- WHEN the validator runs
- THEN it reports `CONCORDE-COVERAGE-003` as an error for the unparsable file
- AND it still reports `CHK.verifies.resolves` for the other test and computes coverage from every readable test

### scenario.spec.spec-coverage-syntax — A Spec that claims its own coverage

- GIVEN Spec reading that contains test-declaration syntax outside a fence
- WHEN the validator runs
- THEN it reports `CHK.evidence.no-spec-coverage` as an error at that line

## Typed values

### scenario.spec.typed-value-accept — Checking a value of a registered type

- GIVEN an owner that registered a type with a version and a schema
- WHEN a caller builds or checks a value of that type with data the schema allows
- THEN the checked value is returned as a copy equal to the input
- AND checking reads and writes no project file

### scenario.spec.typed-value-reject — Refusing a value that does not fit

- GIVEN a value naming an unregistered type, a value with another schema version, and a value whose data has a field its schema does not declare
- WHEN each is checked
- THEN they fail with `unknown_type`, `unsupported_version` and `invalid_field` respectively, each naming the JSON pointer of the offending field

### scenario.spec.typed-register-conflict — Registering a type twice with another schema

- GIVEN a type already registered with a version and a schema
- WHEN another registration of the same identity names a different version or schema
- THEN the registration fails
- AND the first registration stays in force

## File transactions

### scenario.spec.rollback-on-failure — Restoring original bytes after a failure

- GIVEN a file transaction that has written some of its files
- WHEN a later write or the final check of the result fails
- THEN every written file is restored to its original bytes, and files that did not exist are removed
- AND the failure is reported, never success

### scenario.spec.transaction-stale — A changed file stops a transaction before it writes

- GIVEN a file transaction whose expected digest for one file no longer matches that file's bytes
- WHEN it is applied
- THEN it fails with `stale_proposal`
- AND no listed file is written

## Initialization

### scenario.spec.propose-initialization — Proposing a new project

- GIVEN a project where the installer has placed the Protocol copy but no configuration exists
- WHEN a caller initializes it with `action: "propose"` and a name
- THEN the result is an initial proposal with the configuration, the registry, and a root entry with its metadata
- AND the root entry says the project's purpose, behaviour and architecture are not yet specified
- AND its metadata binds the project's existing tracked and not-ignored files in one realization, Existing project files
- AND every proposed file has a null before-digest
- BUT no project file is written

### scenario.spec.apply-initialization — Applying an accepted proposal

- GIVEN a proposal returned by propose whose destinations are all still absent and whose project is unchanged
- WHEN a caller initializes it with `action: "apply"`, that exact proposal and the `proposal_digest` propose returned
- THEN every proposed file is written in one file transaction and the resulting project validates
- AND the result has status `applied` and lists the written paths
- BUT no Protocol copy or other installer output is created

### scenario.spec.reject-already-initialized — A configured project is not reinitialized

- GIVEN a project that already has `.concorde/config.json`
- WHEN initialization is proposed
- THEN it fails with `already_initialized`
- AND no file changes

### scenario.spec.reject-not-installed — A project without the installer's Protocol copy

- GIVEN a project with no Protocol copy under `.concorde/protocol/`
- WHEN initialization is proposed
- THEN it fails with `not_installed`
- AND no file changes

### scenario.spec.reject-invalid-proposal — A malformed proposal is refused

- GIVEN a proposal that is not the one its named `proposal_digest` identifies, whose envelope is incomplete, that lacks the configuration or the registry, whose Protocol binding no longer matches the installed copy, or that has a non-null before-digest
- WHEN apply is requested
- THEN it fails with `invalid_proposal`
- AND no file is written

### scenario.spec.reject-stale-proposal — A proposal for an earlier project state

- GIVEN a proposal returned by propose, one of whose destinations was created afterwards, or whose project gained or lost a file its realization would bind
- WHEN apply is requested
- THEN it fails with `stale_proposal`
- AND no file is written

### scenario.spec.reject-proposal-outside-files — A proposal that writes elsewhere

- GIVEN a proposal that also lists a file that is neither the configuration, the registry nor a member of a document its registry registers
- WHEN apply is requested
- THEN it fails with `permission_denied`
- AND no file is written
