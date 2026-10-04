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

### scenario.scaffold.stale — A proposal overtaken by the worktree

- GIVEN a survey proposing `module.checkout` bound to `src/checkout/`
- AND `src/checkout/` was removed from the workspace after the survey
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `blocked` with `stale_proposal` naming the missing entry
- AND each mismatch is a cause of its own in the [error chain](../../glossary.json#concept.error-chain)
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

### scenario.scaffold.write-failed — A refused write names every file not restored

- GIVEN a survey whose proposal fits the workspace
- WHEN the operating system refuses one of the scaffold's writes
- THEN the result is `failed` with `write_failed`, reason `environment`, Spec core's error as its cause, and every file of the workspace is as before
- AND when the scaffold's files would add a structural error and the operating system refuses to remove the created `specs/shop/checkout/module.md` while the transaction restores the workspace, the result is `failed` with `write_failed` instead of `scaffold_invalid`
- AND that result names that file as still holding the scaffold's content and tells to remove it
- AND every other file is then as before

### scenario.scaffold.refused-input — The scaffold needs one survey of its workspace

- GIVEN a workspace `adopt`
- WHEN the main agent runs the scaffold with no `--input`, with two, or with a run of the workspace that is not a survey
- THEN each of these runs is `failed` with `invalid_request` naming what was given and what is needed
- AND no file was written
- BUT an unbound survey, or one of another workspace, is refused before the first step: the result is `failed` and its `command` link `refused` has the cause `input_not_admissible`

### scenario.scaffold.unbound — The scaffold needs a bound workspace

- GIVEN an unbound survey run in the primary worktree
- WHEN the main agent runs `concorde scaffold --input <that run>` in the primary worktree
- THEN the result is `failed`, of kind `command` with `workspace` null, and its `command` link `refused` has the cause `binding_required`
- AND no file was written
- BUT the same command in a bound task worktree, with an `ok` survey of that workspace whose proposal fits it, ends `ok`, of kind `command` with no worker

### scenario.scaffold.vendored-external — Vendored code becomes external material

- GIVEN a survey whose worker proposes `src/db.py` as vendored third-party code used by the proposed child `module.checkout`
- WHEN the survey ends and the scaffold applies its proposal
- THEN `src/db.py` is among no [Module](../../glossary.json#concept.module)'s entries and `module.checkout` includes it as external material with the worker's reason
- AND the project validates with no new error
- AND when the vendored path lies inside a child's directory entry instead, such as `src/checkout/payment.py` inside `src/checkout/`, which holds `src/checkout/api.py` too, that child binds `src/checkout/api.py` and includes `src/checkout/payment.py` as external material
- BUT a vendored path equal to a child's entry, or a vendored directory containing one, such as `src/checkout/` itself, fails the survey with `inconsistent_proposal`
