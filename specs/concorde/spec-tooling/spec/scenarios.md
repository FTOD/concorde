# Spec scenarios

The concrete situations the [Spec core](module.md) [Module](../../glossary.json#concept.module)
promises to handle, one outcome each. The headings group them by subject. Each scenario belongs to
the Module as a whole. The obligations they illustrate are in the [requirements](requirements.md).

## Loading

### scenario.spec.admit-inventory — Loading a consistent project

- GIVEN a project whose configuration binds the installed
  [Protocol copy](../../glossary.json#concept.protocol-copy)
- AND whose registry records every Module with its entry path and a copy of its `module` block
- AND whose entries and registered documents are schema-3 pairs
- WHEN a repository is constructed
- THEN it returns a repository that lists every recorded Module with its owned documents and
  relations
- AND every relation keeps the source, target and attributes its declaration states
- BUT it reads no Markdown file that no `owns` lists and no implementation file's contents

### scenario.spec.reject-inconsistent-inventory — Refusing a project that cannot be admitted

- GIVEN a project whose registry is not valid JSON, repeats a key, or has a `schema_version` other
  than 3
- WHEN a repository is constructed for a consumer
- THEN construction fails with an error naming the file and the problem
- AND no repository is returned

### scenario.spec.validate-unreadable-registry — Validating a project whose registry cannot be read

- GIVEN a project whose registry is not valid JSON
- WHEN the validator runs
- THEN it returns status `invalid` with one `CONCORDE-SOURCE-008` error naming the problem
- AND `result.load_error` is the error record with the registry's path, the parser's message, the
  reason and the remediation
- BUT it raises no exception
- BUT it writes no file

### scenario.spec.reject-unsupported-profile — Refusing an unaccepted Protocol

- GIVEN a project whose configuration binds a Protocol version or manifest digest that differs from
  the copy under `.concorde/protocol/`, whose installed copy has a changed asset, or whose copy
  differs from the running package's Protocol
- WHEN a repository is constructed
- THEN construction fails with `protocol_mismatch`
- AND no repository is returned

A newer installed Protocol is adopted only when the developer explicitly rebinds the configuration
to it.

### scenario.spec.reject-configuration-profile — Refusing another configuration profile

- GIVEN a project whose configuration has a `profile_version` other than the one this Concorde
  supports
- WHEN a repository is constructed
- THEN construction fails with `unsupported_profile`
- AND the configuration is not reinterpreted

### scenario.spec.config-fields-moved — A field of an earlier profile names where its setting lives

- GIVEN a configuration of profile 18 that still has `registry`, `checks` and `workers`
- WHEN a repository is constructed
- THEN construction fails with `invalid_spec` naming each of the three fields and where its setting
  lives now
- AND the error names `.concorde/specs.json` as where the registry always lives
- AND the error names `.concorde/checks/<module id>.json` as where the checks live
- AND the error names `.concorde/workers.json` as where the worker limits and runtime paths live
- AND the remediation says to move them
- AND the remediation says to remove the fields
- AND the remediation says to set the current `profile_version`

### scenario.spec.document-roles — Explanation and precise definitions in different roles

- GIVEN a Module whose entry and topics have role `module`
- AND whose requirements, scenarios and contracts are in documents with role `implementation`
- WHEN the project is validated
- THEN no role finding is reported
- AND both roles contribute both members to the Module's
  [Spec context](../../glossary.json#concept.spec-context)

### scenario.spec.document-role-misplaced — Definitions in the wrong role

- GIVEN a requirement, scenario or contract fence in a `module` document, a glossary entry whose
  explanation lies in an `implementation` document, or a document with a missing or unknown role
- WHEN the validator runs
- THEN it reports `CHK.defines.role` for each misplaced definition
- AND it reports `CHK.node.meaning` for the misplaced explanation
- AND it reports `CHK.document.role` for the missing or unknown role

## Checks

### scenario.spec.validate-success — A conforming project validates

- GIVEN a project whose declarations satisfy every Protocol check and every Concorde convention
- WHEN the validator runs
- THEN it returns status `success` with no error findings
- AND the result carries a digest of the assessed inputs
- AND the result states that semantic completeness is not proven

### scenario.spec.validate-structural-errors — Every violation is reported with its check

- GIVEN a project with several independent violations
- AND among them are a duplicate node identity, a Module that uses itself and a file no Module binds
- AND among them is a link to a requirement identity that the linked document does not define
- WHEN the validator runs
- THEN it returns status `invalid`
- AND reports one finding per violation, each naming its rule identity, strictness, file and a
  remediation
- AND reports `CONCORDE-LINK-001` for the broken link
- BUT it does not stop at the first violation
- BUT it does not judge whether the described behaviour is correct

### scenario.spec.node-checks — Malformed nodes

- GIVEN an implementation document with a requirement whose first sentence has no `SHALL`
- AND that document has a scenario whose steps return from `THEN` to `GIVEN`
- AND that document has a `concorde-contract` fence whose example does not satisfy its schema
- AND a glossary entry whose explanation names no anchor with prose in a document its owner owns
- AND another glossary entry whose definition is two sentences
- WHEN the validator runs
- THEN it reports `CHK.requirement.statement`, `CHK.scenario.steps`, `CHK.contract.fence`,
  `CHK.node.meaning` and `CHK.concept.definition` as errors

### scenario.spec.node-unexplained — An anchor with no explanation

- GIVEN a module document whose anchor group is followed only by links and headings
- WHEN the validator runs
- THEN it reports a `CHK.node.explained` warning for that anchor group
- AND the status is not made `invalid` by it

### scenario.spec.reader-parts — Entries of any section structure

- GIVEN an entry whose level-2 sections are Purpose, Usage and Design
- AND an entry with none of these sections
- AND an entry with a level-2 Relationships section
- AND an entry whose Purpose holds a list
- AND a topic that links every term it uses to the glossary
- WHEN the validator runs
- THEN no document-structure finding is reported for any of them
- BUT passing says nothing about whether the explanations are sufficient

### scenario.spec.term-links — Linking another Module's term

- GIVEN a Module document that links a term owned by a Module it neither uses nor contains
- WHEN the validator runs
- THEN the link is accepted without a finding
- AND the term's glossary entry is in the Module's context, with the linking document as the reason
- BUT no document of the term's owner is added to the context

### scenario.spec.term-link-invalid — A term link that names no glossary entry

- GIVEN a link whose fragment is a concept identity but which addresses a document other than the
  glossary, a term link to a concept the glossary does not declare, or a glossary definition that
  links an undeclared concept
- WHEN the validator runs
- THEN it reports `CHK.term.link` as an error for each link

### scenario.spec.term-unlinked — A term used without a link

- GIVEN a document whose prose uses the title of a concept outside code, headings and links, and
  never links that concept
- WHEN the validator runs
- THEN it reports a `CHK.term.unlinked` warning naming the term, the line and the link to write
- AND a title whose words wrap onto the next line is a use, reported on the line it starts on
- BUT a Module's title is no use of a term
- BUT a shorter title inside a longer one is no use of a term
- BUT a title's words apart by code or a link are no use of a term
- BUT a one-word title as the first word of a sentence or table cell is no use of a term

### scenario.spec.style-warnings — Sentences that break the decidable style rules

- GIVEN a document whose prose has a sentence of more than 35 words
- AND its prose has a sentence with a semicolon
- AND its prose has a sentence with two requirement keywords
- AND a glossary entry whose definition has more than 50 words
- WHEN the validator runs
- THEN it reports a `CHK.style.sentence-length`, a `CHK.style.semicolon` and a
  `CHK.style.one-obligation` warning
- AND each warning names the document and the line its sentence starts on
- AND it reports a `CHK.style.sentence-length` warning on the glossary that names the concept
- AND the result status stays `success`
- BUT fences, headings, tables and inline code are no prose
- BUT a link counts as its text
- BUT an inline code span counts as one word
- BUT a definition of 50 words or fewer is not too long
- BUT the statement of a requirement is not measured for length, however long it is

### scenario.spec.concept-local — A concept only its owner uses

- GIVEN a glossary entry that the Module declaring the glossary does not own
- AND no other Module links it in reading, names it in `relies_on` or a `relates`, or reaches it
  from a concept it owns
- WHEN the validator runs
- THEN it reports a `CHK.concept.local` warning naming the concept and its owner
- BUT a concept the declaring Module owns is never reported
- BUT one use by any other Module settles the warning

### scenario.spec.glossary-invalid — A malformed glossary

- GIVEN a glossary entry without an owner or with an unknown field, two concepts whose titles
  normalize equal, entries not sorted by identity, a glossary declared by a Module that has a parent
  or by two Modules, or a concept record left in document metadata
- WHEN the validator runs
- THEN it reports `CHK.glossary.schema`, `CHK.node.title`, `CHK.glossary.declared` or
  `CHK.node.type` for each problem

### scenario.spec.term-selection — The definitions a Module's context holds

- GIVEN a Module A that owns concept X and uses Module B without `relies_on`
- AND a document of A links concept Y
- AND a document of B links concept Z
- AND Y's definition links concept W
- WHEN A's Spec context is resolved
- THEN its terms are the glossary entries of X, Y, Z and W, each with the declarations that selected
  it
- AND `owns` of A selects X
- AND `mentions` of the linking document selects Y and Z
- AND `mentions` of Y selects W
- BUT a concept that no selected document, declaration or selected definition names is not among
  them

### scenario.spec.composition-checks — Composition and dependency errors

- GIVEN a registry with a composition cycle, a Module with two parents, a Module that uses itself,
  or two `uses` of one provider
- WHEN the validator runs
- THEN it reports `CHK.contains.acyclic`, `CHK.contains.single-parent`, `CHK.uses.no-self` or
  `CHK.uses.unique` as errors

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

- GIVEN a Module that uses a provider with `relies_on` listing one requirement and one concept the
  provider owns
- WHEN the Module's Spec context is resolved
- THEN it contains the provider's entry, the document defining the requirement and the document the
  concept's glossary entry names as its explanation
- AND the concept's glossary entry is among its terms
- BUT no other document of the provider

### scenario.spec.relies-on-invalid — A `relies_on` that does not match its explanation

- GIVEN a `uses` whose `relies_on` names a node the provider does not own, and whose meaning section
  links to a provider node the list omits
- WHEN the validator runs
- THEN it reports `CHK.relies-on.owned` for the foreign node and `CHK.relies-on.linked` for the
  unlisted link
- BUT a term link to one of the provider's concepts names a word, not a relied-upon promise, and
  needs no listing

### scenario.spec.reference-resolution — Only the selecting Module's own relations count

- GIVEN Module A uses Module B
- AND B uses Module C
- AND A includes one document of Module D with a reason
- WHEN A's Spec context is resolved
- THEN it contains A's documents, B's documents and the included D document, each with the relation
  that selected it
- AND `owns` selects A's own documents
- AND `uses` of B selects B's documents
- AND `includes` of document D selects D's document
- AND a document selected by two relations appears once, listing both
- AND removing either relation changes the
  [context identity](../../glossary.json#concept.context-identity)
- BUT unless A itself selects it, no document of C appears

### scenario.spec.reference-invalid — Unresolved or misplaced relations

- GIVEN an entry whose `uses` targets an unknown Module, an `includes` that names the Module itself
  or one of its own documents, a duplicate `includes`, or an `includes` without a reason
- WHEN the validator runs
- THEN it reports `CHK.relation.endpoints`, `CHK.includes.no-self`, `CHK.includes.unique` or
  `CHK.includes.reason` for the declaration concerned
- BUT no document is silently added to or removed from any context

### scenario.spec.includes-redundant — A redundant inclusion

- GIVEN a Module that includes a document it already selects through a `uses` without `relies_on`
- WHEN the validator runs
- THEN it reports a `CHK.includes.redundant` warning for the inclusion
- AND the document still appears once in the context, listing both relations

### scenario.spec.context-reconciled — A declaration requires its definition in context

- GIVEN a Module that relates one of its realizations to another Module's realization, without any
  `uses`, `contains` or `includes` that selects the document defining it
- WHEN the validator runs
- THEN it reports `CHK.context.reconciled` naming the Module and the missing document
- BUT a `relates` to another Module's concept needs no selection, because it brings the concept's
  glossary entry into the context itself

### scenario.spec.meaning-relations — Invalid relations between meanings

- GIVEN glossary entries where one narrows itself through a chain of `narrows`, a `supersedes` from
  a concept that is not retired, two `contrasts` for one pair or a `relates` with an empty verb, or
  document metadata with a `relates` whose source the declaring document does not define
- WHEN the validator runs
- THEN it reports `CHK.narrows.acyclic`, `CHK.concept.retired`, `CHK.contrasts.once`,
  `CHK.relates.verb` or `CHK.relates.source`

### scenario.spec.relates-module-source — A Module as the source of `relates`

- GIVEN a document whose metadata declares a `relates` whose source is the document's owning Module
  and whose target's defining document is in that Module's context
- WHEN the validator runs
- THEN the relation is accepted without a finding

### scenario.spec.name-collision — Same-named nodes of different owners

- GIVEN a concept whose title differs only in case, hyphens or spacing from the title of a Module
  other than its owner, with no `contrasts` between them
- WHEN the validator runs
- THEN it reports `CHK.contrasts.required` for the pair
- BUT a concept is never compared with its own Module
- BUT two concepts sharing a title fail `CHK.node.title`, which no contrast settles

### scenario.spec.name-collision-contrasted — A declared contrast settles a collision

- GIVEN a concept named like a Module other than its owner
- AND a `contrasts` to that Module with a reason in the concept's glossary entry
- WHEN the validator runs
- THEN no `CHK.contrasts.required` finding is reported for the pair

### scenario.spec.participation — Contract participation

- GIVEN a contract of version 2 defined by one Module and a peer Module that declares it
  participates in version 1
- AND a participation whose internal peer does not declare the complementary role for the same
  version
- AND a participation that repeats a contract, peer and role
- WHEN the validator runs
- THEN it reports `CHK.participates.version` for the version mismatch
- AND `CHK.participates.complementary` for the missing complementary role
- AND `CHK.participates.unique` for the repetition

### scenario.spec.checked-diagram — A checked diagram that asserts only declarations

- GIVEN a module document with a `d2` block whose shapes name local concepts and realizations
- AND its shapes name Module titles
- AND its shapes name qualified `Module title / node title` labels
- AND inside a realization, its shapes name files it binds
- AND every nesting matches a declared `contains`, the ownership of a node or the binding of a file
- AND every unlabelled edge between two Modules matches a declared `uses` in its direction
- AND every labelled edge matches a declared `relates` in its direction
- WHEN the validator runs
- THEN no view finding is reported
- AND a block marked `d2 illustrative` in the same document, even one that sets styles, is not
  checked
- AND in the Module's own document its title names the Module even when one of its concepts shares
  it
- AND in the Module's own document, a concept that shares the Module's title is drawn as
  `Title / Title`

### scenario.spec.validate-architecture-mismatch — A diagram that asserts something undeclared

- GIVEN a module document with a checked `d2` block that has an unresolved or ambiguous shape, a
  file its realization does not bind, a nesting nothing declares, an edge with no matching
  declaration or an unlabelled edge touching a node, and a statement outside the semantic subset
- AND a Mermaid block, and a checked `d2` block in an `implementation` document
- WHEN the validator runs
- THEN it reports `CHK.view.nodes` for the shapes
- AND it reports `CHK.view.nesting` for the nesting
- AND it reports `CHK.view.edges` for the edges
- AND it reports `CHK.view.subset` for the statement
- AND it reports `CHK.view.marked` for each misplaced block

### scenario.spec.registry-mirror — A stale registry is reported

- GIVEN a Module whose entry gained a `uses`, or changed its title, without its registry record
  following
- WHEN the validator runs
- THEN it reports `CHK.registry.mirror` for that Module
- AND a Module with no registry record, or a record with no matching entry, is reported the same way

## Registry mirror

### scenario.spec.registry-regenerate — Regenerating the mirrored fields

- GIVEN a registry whose records are stale for some Modules
- WHEN the developer runs the registry command with `--write`
- THEN every record's `title`, `owns`, `contains`, `uses`, `includes` and `participates` equal
  its entry's `module` block
- AND where the block declares `glossary`, the record's `glossary` also equals its entry's `module`
  block
- AND each record's identity and entry path are unchanged
- AND the record order is unchanged
- AND the set of recorded Modules is unchanged

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
- AND its Spec context contains both members of every document it owns or selects, each with the
  declarations that selected it and its original owner

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
- WHEN a caller queries its [Spec](../../glossary.json#concept.spec) files
- THEN the result is the Spec context of the Module or of the scenario's owner, both members of each
  document
- AND the result has no duplicates
- AND the result is sorted by path
- BUT the query reads none of the returned files' contents

### scenario.spec.query-invalid-target — Refusing an identity that has no context

- GIVEN a document, requirement or concept identity, or a path
- WHEN a caller queries its Spec files
- THEN the query fails with `invalid_target`
- AND no context is returned

### scenario.spec.write-sets — Spec scope and implementation scope

- GIVEN Module A uses Module B and binds `src/a/`
- WHEN A's write sets are computed
- THEN A's Spec scope contains both members of every document A owns and the glossary file
- AND A's Spec scope contains nothing of B
- AND of the glossary's entries, only those A owns, and new ones naming A as owner, are A's to
  change
- AND A's implementation scope covers every file below `src/a/`, including a file not created yet
  such as `src/a/new.py`
- BUT A's [implementation context](../../glossary.json#concept.implementation-context) lists only
  the names of the files A binds, never their contents

### scenario.spec.shared-file — A file bound by several Modules

- GIVEN two Modules that each bind the same file, one exactly and one through a directory entry
- WHEN the repository is loaded
- THEN each Module keeps its own realization entry
- AND the implemented-by index lists both Modules for that file
- AND each Module's binding Modules name the other with that file
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

### scenario.spec.missing-entry — A declared entry that does not exist

- GIVEN a realization with an entry whose file or directory does not exist
- WHEN the validator runs
- THEN it reports `CHK.binds.exists` as an error for that entry
- AND the finding's remediation says to create the file before binding it or to remove the entry

### scenario.spec.pending-rejected — A realization that still declares pending entries

- GIVEN a realization record that carries a `pending` field, as Protocol 15 allowed
- WHEN the validator runs
- THEN it reports `CHK.document.schema` naming `pending` as an unknown field of that realization

### scenario.spec.unbound-file — Every tracked file is bound

- GIVEN a version-controlled source file that no realization covers
- WHEN the validator runs
- THEN it reports `CHK.binds.unbound` for that path

### scenario.spec.unbound-exemptions — Files that need no binding

- GIVEN version-controlled document members, files under `.concorde/`, generated outputs and
  declared external material that no realization covers
- WHEN the validator runs
- THEN no `CHK.binds.unbound` finding is reported for them

### scenario.spec.bound-spec-member — A realization binds a Spec document

- GIVEN a realization entry that names a document member, or a directory entry that contains one
- WHEN the validator runs
- THEN it reports `CHK.binds.no-spec` for that entry

### scenario.spec.installed-exact — An installed file is bound only by its exact path

- GIVEN an installation record `.concorde/install.json` listing the installer's own files outside
  `.concorde/`, and the files it only amends
- AND a realization entry that is a directory holding installed files
- WHEN the validator runs
- THEN it reports `CHK.binds.installed` for that entry, naming each installed file it holds and the
  installation record
- BUT a directory holding only files the installer amends or the Module's own files is accepted

### scenario.spec.external-reference — Pinned external material

- GIVEN a Module with an `includes` of kind `external` naming a directory of vendored material
  tracked by version control
- WHEN its [external context](../../glossary.json#concept.external-context) is resolved
- THEN it contains the readable files below that directory, media and archives excluded
- AND those files are identified by one digest over their paths and bytes
- AND the material enters neither the Spec context nor the implementation context

### scenario.spec.external-reference-invalid — Missing or overlapping external material

- GIVEN an external inclusion whose path is missing or untracked, and another whose path overlaps a
  document member or a realization entry
- WHEN the validator runs
- THEN it reports `CHK.external.exists` for the first and `CHK.external.no-overlap` for the second

### scenario.spec.impact-indexes — Whom a change concerns

- GIVEN Module A uses Module B with `relies_on` listing a requirement defined in B's requirements
  document
- AND Module C includes that same B document
- AND Modules B and D bind the same file
- WHEN a caller asks which Modules a change concerns
- THEN a change to that document concerns B, A and C through the selected-by index
- AND a change to the listed requirement concerns A through the referenced-by index
- AND a change to the shared file concerns B and D through the implemented-by index
- AND a change to a concept's glossary entry concerns every Module whose terms hold the concept
- BUT the indexes add nothing to any Module's
  [boundary sets](../../glossary.json#concept.boundary-set)

### scenario.spec.changed-definitions — Comparing two revisions of the Specs

- GIVEN two repositories of the same project at different revisions
- AND in the later one a requirement's statement changed while its document's other definitions did
  not
- WHEN a caller asks for the changed documents and the changed nodes between them
- THEN the changed documents are the documents whose members differ
- AND the changed nodes are exactly the nodes whose defining section, contract fence, glossary
  entry, realization record or entry `module` block differ

## Grants

### scenario.spec.grant-understand — An understanding grant reads Specs and names code

- GIVEN Module A that binds `src/a/`
- AND Module A uses Module B
- AND Module A includes pinned external material under `references/lib/`
- WHEN a grant for [task type](../../glossary.json#concept.task-type) `understand` and Module A is
  computed
- THEN both members of every document in A's Spec context are listed as `ro`
- AND every existing file below `src/a/` is listed as `names`
- AND `references/lib/` is listed as `ro`
- AND the grant carries the glossary entries of A's terms
- AND the glossary file itself is not listed
- BUT no path is `rw`
- BUT no file of B's realization or of any other Module appears

A `review-spec` grant for the same Module is equal to it apart from its task type.

### scenario.spec.grant-specify — A specification grant writes the Module's own documents

- GIVEN Module A that owns three documents and uses Module B
- WHEN a grant for task type `specify` and Module A is computed
- THEN both members of A's own documents and the glossary file are listed as `rw`
- AND B's selected documents are listed as `ro`
- AND A's implementation files are listed as `names`
- BUT no implementation file is `ro` or `rw`

### scenario.spec.grant-implement — An implementation grant writes the realization

- GIVEN Module A with a realization binding `src/a/` and another binding the exact entry `src/b.py`
- WHEN a grant for task type `implement` and Module A is computed
- THEN `src/a/` and `src/b.py` are listed as `rw`
- AND A's documents are listed as `ro`, never `rw`
- AND no file below `src/a/` is listed separately as `names`

### scenario.spec.grant-read-code — Testing and code review read the realization

- GIVEN Module A with a realization binding `src/a/`
- WHEN grants for task types `test` and `review-code` and Module A are computed
- THEN each lists `src/a/` as `ro` and A's Spec context as `ro`
- BUT neither lists any path as `rw`

### scenario.spec.grant-project-implementation — Code phases read the whole project's code

- GIVEN Module A that binds `src/a/` and Module B that binds `src/bmod/`
- WHEN a grant is computed for A with task type `implement`, `test`, `review-code` or `code-to-spec`
- THEN `src/bmod/b.py` is readable, as part of ProjectImplementation, and not writable
- BUT a grant for A with `understand`, `specify` or `review-spec` gives no access to
  `src/bmod/b.py` and no read access to A's own code

### scenario.spec.grant-installed — An installed file is never writable

- GIVEN a Module binding, by their exact paths, two installed files, a file the installer only
  amends and a file of its own
- WHEN a grant is computed for it with a task type that writes its implementation
- THEN each installed file is readable and not writable
- AND the amended file and the Module's own file are writable

### scenario.spec.grant-code-to-spec — Describing code reads it and writes the Spec

- GIVEN Module A with a realization binding `src/a/`
- WHEN a grant for task type `code-to-spec` and Module A is computed
- THEN it lists `src/a/` as `ro` and A's own documents as `rw`
- AND the documents A selects from other Modules as `ro`
- BUT no implementation path as `rw`

### scenario.spec.grant-review-architecture — An architecture review reads every Module's Specs and no code

- GIVEN Module A that binds `src/a/`
- AND Module A uses Module B
- AND Module A includes pinned external material under `references/lib/`
- AND Module D that binds `src/shared.py` and that nothing A declares selects
- WHEN a grant for task type `review-architecture` and Module A is computed
- THEN both members of every document of A, B and D and the glossary file are listed as `ro`
- AND every file any Module binds, such as `src/a/one.py`, `src/bmod/b.py` and `src/shared.py`, is
  listed as `names`
- AND `references/lib/` is listed as `ro`
- AND when a byte of a document of D changes, its context identity changes
- AND that change does not change an `understand` grant's context identity
- BUT no path is `rw`
- BUT no implementation file is `ro`

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
- BUT a grant for task type `implement` and Modules A and D lists `src/shared.py` as `rw`
- BUT a grant for task type `understand` and Module A alone lists it as `names`

### scenario.spec.grant-invalid — An unanswerable request gets no grant

- GIVEN a request with an unknown task type, an unregistered Module identity or an empty Module list
- WHEN a grant is computed
- THEN it fails with `invalid_task_type`, `unknown_module` or `invalid_input` respectively
- AND the `concorde grant` command prints that error's record, with its message, reason and
  remediation, as the envelope's `error`
- AND no grant is returned
- AND no file is written

### scenario.spec.grant-worktree — A grant comes from the worktree it names

- GIVEN a primary worktree and a task worktree in which the file `lib/extra.py` was created
- AND Module A's metadata in the task worktree additionally binds it
- WHEN a grant for task type `implement` and Module A is computed with the task worktree as root
- THEN `lib/extra.py` is listed as `rw`
- BUT a grant computed with the primary worktree as root does not list it
- AND the two grants carry different context identities

### scenario.spec.context-identity — The context identity changes only with the context

- GIVEN a grant for Module A, which uses Module B
- WHEN one byte of a B document A selects changes, a redundant inclusion of that document is
  removed, the definition of a concept among A's terms changes, or an implementation file of A
  changes
- THEN the recomputed context identity differs after the change to the document
- AND it differs after the removal of the inclusion
- AND it differs after the change to the definition
- BUT it is unchanged after the change to the implementation file
- BUT it is unchanged after a change to a glossary entry outside A's terms

## Coverage

### scenario.spec.verification-declarations — Tests declare the scenarios they verify

- GIVEN Python and TypeScript tests bound by the Module that owns the scenarios they declare
- WHEN the validator reads them
- THEN every declared scenario is covered by the declaring test, with its path, line and name
- AND no coverage finding is reported for those scenarios
- AND a test whose own code draws a warning from the validator's Python, such as an invalid escape
  sequence, is read without that warning being printed

### scenario.spec.verifies-unknown — A declaration names an unknown scenario

- GIVEN a bound test that declares a scenario identity no Spec defines
- WHEN the validator runs
- THEN it reports `CHK.verifies.resolves` as an error at that declaration

### scenario.spec.coverage-uncovered — A scenario no test declares

- GIVEN a scenario of a Module that binds files, which no bound test declares
- WHEN the validator runs
- THEN it reports a `CONCORDE-COVERAGE-001` warning for the scenario
- BUT a scenario of a Module that binds no files is not reported

### scenario.spec.coverage-foreign-test — A test another Module owns verifies a scenario

- GIVEN a test bound only by Module A that declares a scenario of Module B
- WHEN the validator runs
- THEN the scenario counts as declared
- AND nothing is reported about who owns the test

### scenario.spec.coverage-parse-error — An unreadable test does not stop the scan

- GIVEN one bound Python test file that does not parse
- AND another bound test that declares an unknown scenario
- WHEN the validator runs
- THEN it reports `CONCORDE-COVERAGE-003` as an error for the unparsable file
- AND it still reports `CHK.verifies.resolves` for the other test
- AND it computes coverage from every readable test

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

- GIVEN a value naming an unregistered type, a value with another schema version, and a value whose
  data has a field its closed object schema does not name
- WHEN each is checked
- THEN they fail with `unknown_type`, `unsupported_version` and `invalid_field` respectively, each
  naming the JSON pointer of the offending field

### scenario.spec.typed-value-json-schema — Checking data as JSON Schema does

- GIVEN a registered type whose schema has an object with no `additionalProperties`, an object with
  `additionalProperties: false` and a `number` with a `minimum`
- WHEN values of that type are checked
- THEN the first object admits a field its `properties` do not name
- AND the closed object refuses one with `invalid_field`
- AND the number admits an integer and a non-integral number at or above its minimum
- AND the number refuses a boolean, a string and a number below its minimum with `invalid_field`

### scenario.spec.typed-register-conflict — Registering a type twice with another schema

- GIVEN a type already registered with a version and a schema
- WHEN another registration of the same identity names a different version or schema
- THEN the registration fails
- AND the first registration stays in force

## File transactions

### scenario.spec.rollback-on-failure — Restoring original bytes after a failure

- GIVEN a [file transaction](../../glossary.json#concept.file-transaction) that wrote some of its
  files
- WHEN a later write or the final check of the result fails
- THEN every written file is restored to its original bytes
- AND files that did not exist are removed
- AND the failure is reported, never success

### scenario.spec.transaction-write-refused — A refused write is a Spec error

- GIVEN a file transaction of two files whose second write the operating system refuses
- WHEN it is applied
- THEN it fails with a `SpecError` of code `system_error` naming the second file
- AND its cause is a `system_error` record of the operating system's error
- AND the first file holds its original bytes again

### scenario.spec.transaction-restore-refused — A refused restore is named

- GIVEN a file transaction that wrote two files and whose final check fails
- AND the operating system refuses to restore one of them
- WHEN the failure is handled
- THEN the transaction fails with `system_error` naming the file it could not restore
- AND its causes are the final check's failure and the refused restore
- AND the named file holds the new content
- AND the other file holds its original bytes

### scenario.spec.transaction-check-error — The final check's own error propagates

- GIVEN a file transaction whose final check raises its own exception
- WHEN it is applied
- THEN every written file is restored
- AND the exception the caller receives is the one the final check raised

### scenario.spec.transaction-stale — A changed file stops a transaction before it writes

- GIVEN a file transaction whose expected digest for one file no longer matches that file's bytes
- WHEN it is applied
- THEN it fails with `stale_proposal`
- AND no listed file is written

## Initialization

### scenario.spec.project-python — No interpreter found, none recorded

- GIVEN a project where the installer placed the Protocol copy
- AND no configuration exists
- AND neither `.venv/bin/python` nor `venv/bin/python` exists
- WHEN initialization is proposed without an interpreter
- THEN the proposed configuration has no `python`

### scenario.spec.project-python-found — The project's environment is recorded

- GIVEN a project where the installer placed the Protocol copy
- AND no configuration exists
- AND `.venv/bin/python` exists
- WHEN initialization is proposed without an interpreter
- THEN the proposed configuration's `python` is `.venv/bin/python`

### scenario.spec.project-python-named — A named interpreter is recorded as given

- GIVEN a project where the installer placed the Protocol copy and no configuration exists
- WHEN initialization is proposed with the interpreter `/opt/env/bin/python`
- THEN the proposed configuration's `python` is `/opt/env/bin/python`

### scenario.spec.propose-initialization — Proposing a new project

- GIVEN a project where the installer placed the Protocol copy but no configuration exists
- WHEN a caller initializes it with `action: "propose"` and a name
- THEN the result is an initial proposal with the configuration and the registry
- AND the proposal includes a root entry with its metadata
- AND the root entry says the project's purpose is not yet specified
- AND the root entry says the project's behaviour is not yet specified
- AND the root entry says the project's architecture is not yet specified
- AND its sections are `Purpose`, `Not yet specified` and `Parts`, in that order
- AND its metadata binds the project's existing tracked and not-ignored files in one realization,
  Existing project files
- AND every proposed file has a null before-digest
- BUT no project file is written

### scenario.spec.init-installation — Concorde's installed files are bound apart

- GIVEN a project whose installer receipt lists `.claude/skills/concorde/SKILL.md` among its files
  and `CLAUDE.md` as amended
- WHEN initialization is proposed and the proposal applied
- THEN the root's metadata binds the skill in the realization Concorde installation
- AND the realization Existing project files binds `CLAUDE.md` and the project's other files but not
  the skill
- AND the applied project validates

### scenario.spec.installation-follows-record — Installed files stay bound after initialization

- GIVEN an initialized project whose Concorde installation realization binds the skill and a
  workflow
- AND an installation record that now also lists files a newer Concorde installs
- AND those files exist
- AND the installation record no longer lists the workflow
- AND the workflow is gone
- WHEN the installation is bound
- THEN the newer files are exact entries of the realization
- AND the workflow's entry is removed
- AND only the root's metadata member changes
- AND the project validates
- BUT binding it again changes nothing
- BUT a project without a configuration is left unchanged

### scenario.spec.installation-created — A missing installation realization is created

- GIVEN an initialized project with an installation record whose root Module has no Concorde
  installation realization
- WHEN the installation is bound
- THEN the root's metadata gains the realization Concorde installation with the installed files as
  exact entries
- AND the root entry gains its explaining paragraph
- AND the project validates

### scenario.spec.apply-initialization — Applying an accepted proposal

- GIVEN a proposal returned by propose whose destinations are all still absent and whose project is
  unchanged
- WHEN a caller initializes it with `action: "apply"`, that exact proposal and the
  `proposal_digest` propose returned
- THEN every proposed file is written in one file transaction
- AND the resulting project validates
- AND the result has status `applied`
- AND the result lists the written paths
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

- GIVEN a proposal that is not the one its named `proposal_digest` identifies, whose envelope is
  incomplete, that lacks the configuration or the registry, whose
  [Protocol binding](../../glossary.json#concept.protocol-binding) no longer matches the installed
  copy, or that has a non-null before-digest
- WHEN apply is requested
- THEN it fails with `invalid_proposal`
- AND no file is written

### scenario.spec.reject-stale-proposal — A proposal for an earlier project state

- GIVEN a proposal returned by propose, one of whose destinations was created afterwards, or whose
  changed project makes propose return other realization entries, such as a new file directly under
  the project root
- WHEN apply is requested
- THEN it fails with `stale_proposal`
- AND no file is written

### scenario.spec.reject-proposal-outside-files — A proposal that writes elsewhere

- GIVEN a proposal that also lists a file that is neither the configuration, the registry nor a
  member of a document its registry registers
- WHEN apply is requested
- THEN it fails with `permission_denied`
- AND no file is written
