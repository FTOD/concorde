# Operations scenarios

These concrete situations show the [requirements](requirements.md) of [Operations](module.md) at
work in its catalog. [Method's scenarios](../../method/scenarios.md) show how Method's Operations
run their workers. Whatever a run's definition, the [Execution scenarios](../scenarios.md) show
what the run does.

## The catalog

### scenario.operations.registered — The catalog lists what the installed parts register

- GIVEN a part that, when its code loads, registers the
  [Operation](../../glossary.json#concept.operation) `probe`
- WHEN `concorde run probe` starts in a bound workspace
- THEN the runner finds `probe`'s definition in the catalog
- AND the runner runs `probe`'s steps
- AND registering the same definition again changes nothing
- BUT `concorde run` naming an Operation no installed part registers is a command-line error
- AND the command-line error names the Operation
- AND that command starts no run

### scenario.operations.unique-names — Two parts cannot register one name

- GIVEN a part that registered the Operation `probe`
- WHEN another part registers a different definition named `probe`
- THEN the catalog refuses it with `duplicate_definition`
- AND the refusal names both parts
- AND the first definition stays registered
- AND the command catalog refuses a second
  [execution command](../../glossary.json#concept.execution-command) of one name the same way

### scenario.operations.definition-complete — A definition names its providing Module and its workers

- GIVEN a part that registers definitions with the catalogs
- WHEN it registers an Operation or an execution command whose definition names no providing
  [Module](../../glossary.json#concept.module), or an Operation that declares no
  [worker id](../../glossary.json#concept.worker-id)
- THEN the catalog refuses the definition with `invalid_definition`
- AND the catalog does not list the definition
- AND a complete definition is listed with its providing Module, such as `module.understanding` for
  Method's `understand`
- AND the listing includes the part that registered the complete definition
