# Scaffold scenarios

Concrete situations that show the [requirements](requirements.md) of [Scaffold](module.md). The
shapes are in the [contracts](contracts.md).

## Applying a proposal

### scenario.scaffold.creates — A scaffold creates the proposed Modules

- GIVEN the root Module `module.shop`, whose entry is `specs/shop/module.md` and whose realization binds `src/`, holding `src/checkout/`, `src/inventory/` and `src/db.py`
- AND the workspace `adopt` with an `ok` survey of `module.shop` proposing `module.checkout` bound to `src/checkout/` and `module.inventory` bound to `src/inventory/`, and a pytest check for checkout
- WHEN the [main agent](../../glossary.json#concept.main-agent) runs `concorde scaffold --input <survey run>` in its worktree
- THEN `specs/shop/checkout/module.md` and `specs/shop/inventory/module.md` exist with their metadata, each stating its purpose and, in a section Not yet specified after it, that its core concepts, behaviour and design are not yet specified
- AND the root's entry contains both with an explaining paragraph each at the end of its `Parts` section, and its realization no longer binds `src/checkout/` or `src/inventory/`
- AND the root still binds every other file it bound under `src/`, here `src/db.py`
- AND a realization the root declares in a document other than its entry is narrowed the same way, in the same [file transaction](../../glossary.json#concept.file-transaction), and the record's `parent_entries_after` is what the root's documents bind after it
- AND the registry has both records
- BUT the project configuration and the checks files are unchanged, and the proposed check stays in the survey's proposal
- AND the worktree validates with no new error
- AND the result is `ok`, of kind `command` with no worker, with a scaffold record listing every file written

### scenario.scaffold.no-parts-section — A parent entry without a Parts section gets one

- GIVEN the root Module `module.shop`, whose entry `specs/shop/module.md` explains its realizations in a section `Code` and has no `Parts` section
- AND an `ok` survey of `module.shop` proposing `module.checkout` and `module.inventory`
- WHEN the main agent runs the scaffold with that survey as input
- THEN the root's entry ends with a new `Parts` section holding one explaining paragraph per child
- AND every section the entry had before is unchanged, in its place
- AND the result is `ok` and the worktree validates with no new error

### scenario.scaffold.distinct-anchors — Distinct identities get distinct anchors

- GIVEN an `ok` survey of `module.shop` proposing `module.stock-hold` and `module.stock.hold`, and `module.checkout` using both
- WHEN the main agent runs the scaffold with that survey as input
- THEN the root's entry has the anchors `contains-stock-hold` and `contains-stock.hold`, each the meaning of its child's `contains`
- AND the entry of `module.checkout` has the anchors `uses-stock-hold` and `uses-stock.hold`, each the meaning of its `uses`
- AND the result is `ok` and the worktree validates with no new error

### scenario.scaffold.concurrent-edit — A file changed after the recheck keeps its change

- GIVEN an `ok` survey whose proposal fits the workspace
- AND the scaffold's recheck has loaded the root's entry `specs/shop/module.md`
- WHEN another process appends a paragraph to that entry before the scaffold writes it
- THEN the result is `blocked` with `stale_proposal`, Spec core's error its cause
- AND the root's entry holds the appended paragraph and none of the scaffold's paragraphs
- AND no folder of a proposed child exists, and every other file is as before the scaffold

### scenario.scaffold.stale — A proposal overtaken by the worktree

- GIVEN a survey proposing `module.checkout` bound to `src/checkout/`
- AND `src/checkout/` was removed from the workspace after the survey
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `blocked` with `stale_proposal` naming the missing entry
- AND each mismatch is a cause of its own in the [error chain](../../glossary.json#concept.error-chain)
- AND no file was written

### scenario.scaffold.surveyed-module-removed — The surveyed Module was renamed after the survey

- GIVEN the workspace `adopt`, whose binding names only `module.shop`, with an `ok` survey of `module.shop`
- AND the workspace renamed `module.shop` to `module.store` after the survey
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `blocked` with `stale_proposal`, whose cause is a `proposal_mismatch` saying that `module.shop` is no longer registered
- AND no file was written

### scenario.scaffold.specs-unloadable — Specs that do not load stop the scaffold

- GIVEN the workspace `adopt` with an `ok` survey of `module.shop`
- AND the registry `.concorde/specs.json` was made unreadable as JSON after the survey
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `failed` with `specs_unloadable`, Spec core's error its cause
- AND no file was written

### scenario.scaffold.target-exists — An existing target is never replaced

- GIVEN a survey proposing `module.checkout`, whose entry would be `specs/shop/checkout/module.md`
- AND that file was created in the workspace after the survey
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `blocked` with `stale_proposal`, naming the folder `specs/shop/checkout/` that holds the file
- AND no file was written and the existing file is unchanged

### scenario.scaffold.target-folder-exists — An existing child folder is refused even when empty

- GIVEN a survey proposing `module.checkout`, whose entry would be `specs/shop/checkout/module.md`
- AND the folder `specs/shop/checkout/` was created empty in the workspace after the survey
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `blocked` with `stale_proposal`, naming the folder `specs/shop/checkout/`
- AND no file was written and the folder is still empty

### scenario.scaffold.invalid-not-kept — A scaffold that would not validate keeps nothing

- GIVEN a survey whose proposed `module.checkout` has a purpose linking to an anchor that no document defines
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `failed` with `scaffold_invalid` and one cause for each structural error the scaffold would add
- AND every file of the workspace is as before the scaffold, and no folder of a proposed child exists

### scenario.scaffold.write-failed — A refused write restores every file

- GIVEN a survey whose proposal fits the workspace
- WHEN the operating system refuses one of the scaffold's writes
- THEN the result is `failed` with `write_failed`, reason `environment`, Spec core's error as its cause
- AND every file of the workspace is as before

### scenario.scaffold.restore-failed — A file not restored is named

- GIVEN a survey whose proposed `module.checkout` has a purpose linking to an anchor that no document defines
- WHEN the main agent runs the scaffold with that survey as input
- AND the operating system refuses to remove the created `specs/shop/checkout/module.md` while the transaction restores the workspace
- THEN the result is `failed` with `write_failed` instead of `scaffold_invalid`
- AND it names that file as still holding the scaffold's content and tells to remove it
- AND every other file is as before

### scenario.scaffold.refused-input — The scaffold needs one survey of its workspace

- GIVEN a workspace `adopt`
- WHEN the main agent runs the scaffold with no `--input`, with two, or with a run of the workspace that is not a survey
- THEN each of these runs is `failed` with `invalid_request` naming what was given and what is needed
- AND no file was written

### scenario.scaffold.foreign-input — A survey of another workspace never reaches the scaffold

- GIVEN a workspace `adopt` and an unbound survey run
- WHEN the main agent runs the scaffold in the worktree of `adopt` with that survey as input
- THEN the runner refuses it before the first step: the result is `failed` and its `command` link `refused` has the cause `input_not_admissible`
- AND no file was written

### scenario.scaffold.unbound — The scaffold needs a bound workspace

- GIVEN an unbound survey run in the primary worktree
- WHEN the main agent runs `concorde scaffold --input <that run>` in the primary worktree
- THEN the result is `failed`, of kind `command` with `workspace` null, and its `command` link `refused` has the cause `binding_required`
- AND no file was written

### scenario.scaffold.bound — The scaffold runs in a bound workspace

- GIVEN the workspace `adopt` with an `ok` survey whose proposal fits it
- WHEN the main agent runs `concorde scaffold --input <that run>` in the worktree of `adopt`
- THEN the result is `ok`, of kind `command` with no worker, and its workspace is `adopt`
- AND its run's [trace node](../../glossary.json#concept.trace-node) lies in the workspace folder of `adopt`, where a later run may admit it

### scenario.scaffold.vendored-external — Vendored code becomes external material

- GIVEN a survey whose worker proposes `src/db.py` as vendored third-party code used by the proposed child `module.checkout`
- WHEN the survey ends and the scaffold applies its proposal
- THEN `src/db.py` is among no [Module](../../glossary.json#concept.module)'s entries and `module.checkout` includes it as external material with the worker's reason
- AND the project validates with no new error

### scenario.scaffold.vendored-inside-child — Vendored code inside a child's directory narrows that child

- GIVEN a survey proposing `module.checkout` bound to `src/checkout/`, which holds `src/checkout/api.py` and `src/checkout/payment.py`
- AND the survey proposes `src/checkout/payment.py` as vendored third-party code used by `module.checkout`
- WHEN the scaffold applies its proposal
- THEN `module.checkout` binds `src/checkout/api.py` and includes `src/checkout/payment.py` as external material
- AND the project validates with no new error

### scenario.scaffold.vendored-child-entry — Vendored code that is a child's entry fails the survey

- GIVEN a survey whose worker proposes `src/checkout/` as vendored third-party code and as the entry of the child `module.checkout`
- WHEN the survey checks its proposal
- THEN the survey fails with `inconsistent_proposal`, as Adoption's [proposal checks](../adoption/requirements.md#req.adoption.proposal-checked) require, and no scaffold can apply it

### scenario.scaffold.vendored-bound-elsewhere — Vendored code another Module binds is refused

- GIVEN an `ok` survey of `module.shop` proposing `src/db.py` as vendored third-party code used by `module.checkout`
- AND the workspace then registered `module.db`, whose realization binds `src/db.py` too
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `blocked` with `stale_proposal`, whose `proposal_mismatch` cause names `module.db` and `src/db.py`
- AND no file was written
