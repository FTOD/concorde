# Specification scenarios

Concrete situations that show the [requirements](requirements.md) at work. The
[Spec change](../../../glossary.json#concept.spec-change)'s shape is in the
[contracts](contracts.md).

## Changing Specs

### scenario.specification.change — A Spec change is made and validated

- GIVEN a workspace whose Specs pass structural validation
- WHEN the caller runs `specify` for a [Module](../../../glossary.json#concept.module) with an intent the worker can carry out
- THEN the worker edits only documents that Module owns
- AND the [Operation](../../../glossary.json#concept.operation) regenerates the registry mirror and validates the workspace
- AND the result has status `ok` with the changed documents, the affected Modules and an empty `validation.new_errors`

### scenario.specification.declare-pending — A new file is declared, not created

- GIVEN an intent that needs a new implementation file in a bound Module
- WHEN the worker adds the file as a pending entry of one of the Module's realizations
- THEN the Spec change lists the declared entry with its Module and realization
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
- AND its [error chain](../../../glossary.json#concept.error-chain) ends in the worker's own link naming the other Module, the reason it could not change it and the options it sees

### scenario.specification.new-document — A needed document is created and filled

- GIVEN an intent whose precise obligations belong in a new [Spec](../../../glossary.json#concept.spec) document of role `implementation` (such as a contracts or scenarios document) of the bound Module, whose entry is `specs/a/module.md`
- AND no file exists at `specs/a/rules.md` or `specs/a/rules.md.json`
- WHEN the worker ends `blocked` proposing `specs/a/rules.md` for that Module
- THEN the Operation creates `specs/a/rules.md` and its metadata, empty and owned by the Module, and adds it to the Module's `owns` and the registry mirror
- AND it launches a second worker whose brief names the created document, and that worker fills it
- AND the result lists the document under `created_documents` and `changed_documents`, with `document-created` evidence, and two worker runs

### scenario.specification.document-refused — A proposal outside the bound Modules creates nothing

- GIVEN a worker that ends `blocked` proposing a document of a Module the run is not bound to, or a path outside the folder of the bound Module's entry
- WHEN the Operation judges the proposals
- THEN it creates no document and launches no second worker
- AND the result has status `blocked` with `document-refused` evidence naming the reason

### scenario.specification.code-write — A write to code fails the run

- GIVEN a specify run whose [write audit](../../../glossary.json#concept.write-audit) finds a changed implementation file
- WHEN the Operation evaluates the audit
- THEN the result has status `failed` with the changed path as host evidence
- BUT the Operation runs no validation after the worker
