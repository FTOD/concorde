# Specification scenarios

Concrete situations that show the [requirements](requirements.md) at work. The
[Spec change](../../glossary.json#concept.spec-change)'s shape is in the
[contracts](contracts.md).

## Changing Specs

### scenario.specification.change — A Spec change is made and validated

- GIVEN a workspace whose Specs pass structural validation
- WHEN the caller runs `specify` for a [Module](../../glossary.json#concept.module) with an intent the worker can carry out
- THEN the worker edits only documents that Module owns
- AND the [Operation](../../glossary.json#concept.operation) regenerates the registry mirror and validates the workspace
- AND the result has status `ok` with the changed documents, the affected Modules and an empty `validation.new_errors`

### scenario.specification.missing-entry — A worker that binds a file that does not exist

- GIVEN an intent that needs a new implementation file in a bound Module, which the task level has not created
- WHEN the worker adds the file's path to the `entries` of one of the Module's realizations
- THEN validation reports `CHK.binds.exists` for the entry as a new error and the result has status `blocked`
- BUT the file does not exist in the workspace after the run

### scenario.specification.repair-broken — A run repairs Specs that were already invalid

- GIVEN a workspace whose Specs already have structural errors
- WHEN the caller runs `specify` with an intent that repairs some of them
- THEN the remaining baseline errors are reported as pre-existing
- AND the result has status `ok` when the change introduced no new error

## Stopping

### scenario.specification.new-error — A change that breaks the Specs stops the run

- GIVEN a worker whose edit introduces a structural error the baseline did not have
- AND the worker does not repair it when resumed with the error
- WHEN the Operation validates the workspace after the last repair round
- THEN the result has status `blocked` with the new findings as evidence
- AND the worker was resumed with the new errors twice before the run stopped
- AND the worker's edits stay in the workspace for the caller to inspect

### scenario.specification.foreign-document — A needed document of another Module stops the run

- GIVEN an intent that can only be carried out by changing a document of a Module that is not bound
- WHEN the worker finds it cannot make the change within its grant
- THEN the result has status `blocked`
- AND its [error chain](../../glossary.json#concept.error-chain) ends in the worker's own link naming the other Module, the reason it could not change it and the options it sees

### scenario.specification.new-document — A needed document is created and filled

- GIVEN an intent whose precise obligations belong in a new [Spec](../../glossary.json#concept.spec) document of role `implementation` (such as a contracts or scenarios document) of the bound Module, whose entry is `specs/a/module.md`
- AND no file exists at `specs/a/rules.md` or `specs/a/rules.md.json`
- WHEN the worker ends `blocked` proposing `specs/a/rules.md` for that Module
- THEN the Operation creates `specs/a/rules.md` and its metadata, empty and owned by the Module, and adds it to the Module's `owns` and the registry mirror
- AND it launches a second worker whose brief names the created document, and that worker fills it
- AND the result lists the document under `created_documents`, and the document, its metadata and the entry's metadata `specs/a/module.md.json` under `changed_documents`, with `document-created` evidence, and two worker runs
- AND a document proposed below the entry's folder, such as `specs/a/details/rules.md`, is created the same way, linking to the entry as `../module.md`

### scenario.specification.document-refused — A proposal outside the bound Modules creates nothing

- GIVEN a worker that ends `blocked` proposing a document of a Module the run is not bound to, a path outside the folder of the bound Module's entry, or the same path twice
- WHEN the Operation judges the proposals
- THEN it creates no document and launches no second worker
- AND the result has status `blocked` with `document-refused` evidence naming the reason

### scenario.specification.document-symlink — A proposal through a symbolic link creates nothing

- GIVEN a bound Module whose entry is `specs/a/module.md`, and a symbolic link `specs/a/details` to a directory outside the Module, or a dangling symbolic link at `specs/a/dangling.md`
- WHEN the worker ends `blocked` proposing `specs/a/rules.md` together with `specs/a/details/rules.md` or `specs/a/dangling.md`
- THEN the Operation creates no document, writes nothing through the link and launches no second worker
- AND the result has status `blocked` with `document-refused` evidence naming the proposal through the link

### scenario.specification.unreadable-entry — A malformed entry refuses creation and the change is still observed

- GIVEN a worker that leaves the metadata of its Module's entry `specs/a/module.md.json` unreadable as JSON
- WHEN it ends `blocked` proposing `specs/a/rules.md`
- THEN the Operation creates no file and launches no second worker, with `document-refused` evidence saying the entry metadata cannot register the document
- AND the `registry` evidence holds the registry command's refusal naming the entry metadata
- AND validation still runs, and `spec-context` evidence names every Module whose context after the change could not be computed
- AND the result has status `blocked` with the worker's own link and the entry metadata among the changed documents

### scenario.specification.document-identities — Documents of the same name get distinct identities

- GIVEN a bound Module whose entry is `specs/a/module.md`
- WHEN the worker ends `blocked` proposing both `specs/a/rules.md` and `specs/a/details/rules.md`
- THEN the Operation creates both, with the document identities `document.a.rules` and `document.a.details-rules`
- AND the second worker runs and the result has no new structural error

### scenario.specification.code-write — A write to code fails the run

- GIVEN a specify run whose [write audit](../../glossary.json#concept.write-audit) finds a changed implementation file
- WHEN the Operation evaluates the audit
- THEN the result has status `failed` with the changed path as host evidence
- BUT the Operation runs no validation after the worker
