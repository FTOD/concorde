# Scaffold scenarios

Concrete situations that show the [requirements](requirements.md) of [Scaffold](module.md). The
shapes are in the [contracts](contracts.md).

## Applying a proposal

### scenario.scaffold.creates — A scaffold creates the proposed Modules

- GIVEN the root Module `module.shop`, whose entry is `specs/shop/module.md` and whose realization binds `src/`, holding `src/checkout/`, `src/inventory/` and `src/db.py`
- AND the workspace `adopt` with an `ok` survey of `module.shop` proposing `module.checkout` bound to `src/checkout/` and `module.inventory` bound to `src/inventory/`, and a pytest check for checkout
- WHEN the [main agent](../../../glossary.json#concept.main-agent) runs `concorde scaffold --input <survey run>` in its worktree
- THEN `specs/shop/checkout/module.md` and `specs/shop/inventory/module.md` exist with their metadata, each stating its purpose and that its behaviour is not yet specified
- AND the root's entry contains both with an explaining paragraph each and its realization no longer binds `src/checkout/` or `src/inventory/`
- AND the root still binds every other file it bound under `src/`, here `src/db.py`
- AND the registry has both records
- BUT the project configuration and the checks files are unchanged, and the proposed check stays in the survey's proposal
- AND the worktree validates with no new error
- AND the result is `ok`, of kind `command` with no worker, with a [scaffold record](../../../glossary.json#concept.scaffold-record) listing every file written

### scenario.scaffold.stale — A proposal overtaken by the worktree

- GIVEN a survey proposing `module.checkout` bound to `src/checkout/`
- AND `src/checkout/` was removed from the workspace after the survey
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `blocked` with `stale_proposal` naming the missing entry
- AND no file was written

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
- THEN `src/db.py` is among no [Module](../../../glossary.json#concept.module)'s entries and `module.checkout` includes it as external material with the worker's reason
- AND the project validates with no new error
- AND when the vendored path lies inside a child's directory entry instead, such as `src/checkout/payment.py` inside `src/checkout/`, which holds `src/checkout/api.py` too, that child binds `src/checkout/api.py` and includes `src/checkout/payment.py` as external material
- BUT a vendored path equal to a child's entry, or a vendored directory containing one, such as `src/checkout/` itself, fails the survey with `inconsistent_proposal`
