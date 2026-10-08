# Operations scenarios

These concrete situations show the [requirements](requirements.md) of [Operations](module.md) at
work in its catalog. [Registering a definition](registration.md) specifies the interface they use.
[Method's scenarios](../../method/scenarios.md) show how Method's Operations run their workers.
Whatever a run's definition, the [Execution scenarios](../scenarios.md) show what the run does.
The [scenarios of Commands](../commands/scenarios.md) show the command catalog.

## The catalog

### scenario.operations.registered — The runner runs a registered Operation

- GIVEN a part that, when its code loads, registers the
  [Operation](../../glossary.json#concept.operation) `probe`
- WHEN `concorde run probe` starts in a bound workspace
- THEN the runner finds `probe`'s definition in the catalog
- AND the runner runs `probe`'s steps

### scenario.operations.repeated — The same part may register the same definition again

- GIVEN a part that registered the Operation `probe`
- WHEN the same part registers a definition equal to `probe`'s definition again
- THEN the catalog accepts the registration
- AND the catalog still holds the first definition of `probe`, registered by that part

### scenario.operations.unknown — An unregistered Operation is a command-line error

- GIVEN no installed part registers an Operation named `probe`
- WHEN `concorde run probe` starts in a bound workspace
- THEN the command fails with a command-line error
- AND the command-line error names `probe`
- AND that command starts no run

### scenario.operations.unique-names — Two parts cannot register one name

- GIVEN a part that registered the Operation `probe`
- WHEN another part registers a definition named `probe`, whether equal to the first or different
- THEN the catalog refuses it with `duplicate_definition`
- AND the refusal names both parts
- AND the first definition stays registered with the first part

### scenario.operations.definition-complete — An incomplete Operation definition is refused

- GIVEN a part that registers an Operation definition
- WHEN the definition names no providing [Module](../../glossary.json#concept.module), declares no
  [worker id](../../glossary.json#concept.worker-id) or declares an empty worker id
- THEN the catalog refuses the definition with `invalid_definition`
- AND the catalog does not list the definition

### scenario.operations.listed — The catalog lists a definition with its Module and part

- GIVEN a part that registers a complete Operation definition
- WHEN the catalog is asked for the Operation's providing Module and registering part
- THEN the catalog gives the providing Module the definition names, such as
  `module.understanding` for Method's `understand`
- AND the catalog gives the part that registered the definition, such as `method`
