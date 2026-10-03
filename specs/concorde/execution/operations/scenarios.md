# Operations scenarios

Concrete situations that show the [requirements](requirements.md) of [Operations](module.md) at
work in its catalog. How Method's Operations run their workers is shown by
[Method's scenarios](../../method/scenarios.md), and what every run does, whatever its definition,
by the [Execution scenarios](../scenarios.md).

## The catalog

### scenario.operations.registered — The catalog lists what the installed parts register

- GIVEN a part that registers the [Operation](../../glossary.json#concept.operation) `probe` when its code loads
- WHEN `concorde run probe` is started in a bound workspace
- THEN the runner finds `probe`'s definition in the catalog and runs its steps
- AND registering the same definition again changes nothing
- BUT `concorde run` naming an Operation no installed part registers is a command-line error naming it, which starts no run

### scenario.operations.unique-names — Two parts cannot register one name

- GIVEN a part that registered the Operation `probe`
- WHEN another part registers a different definition named `probe`
- THEN the catalog refuses it with `duplicate_definition`, naming both parts
- AND the first definition stays registered
- AND the command catalog refuses a second [execution command](../../glossary.json#concept.execution-command) of one name the same way

### scenario.operations.definition-complete — A definition names its providing Module and its workers

- GIVEN a part registering definitions with the catalogs
- WHEN it registers an Operation or an execution command whose definition names no providing [Module](../../glossary.json#concept.module), or an Operation that declares no [worker id](../../glossary.json#concept.worker-id)
- THEN the catalog refuses it with `invalid_definition` and does not list it
- AND a complete definition is listed with its providing Module, such as `module.understanding` for Method's `understand`, and the part that registered it
