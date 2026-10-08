# Commands scenarios

These concrete situations show the command catalog of [Commands](module.md) at work.
[Registering a definition](../operations/registration.md) specifies the interface they use, which
the command catalog shares with the
[Operation catalog](../../glossary.json#concept.operation-catalog). Whatever a run's definition,
the [Execution scenarios](../scenarios.md) show what the run does, such as the refusal of an
[unbound run](../../glossary.json#concept.unbound-run) with `binding_required`.

## The command catalog

### scenario.commands.registered — The runner runs a registered execution command

- GIVEN a part that, when its code loads, registers the
  [execution command](../../glossary.json#concept.execution-command) `check-it`
- WHEN `concorde check-it` starts in a bound workspace
- THEN the runner finds `check-it`'s definition in the command catalog
- AND the runner runs `check-it`'s steps
- AND the [run result](../../glossary.json#concept.run-result) has the `kind` `command` and no
  `worker`

### scenario.commands.listed — The catalog lists a command with its Module, part and writes

- GIVEN a part that registers a complete definition of the execution command `check-it`
- WHEN the command catalog is asked for `check-it`
- THEN the catalog gives the providing [Module](../../glossary.json#concept.module) the definition
  names
- AND the catalog gives the part that registered the definition
- AND the catalog gives whether `check-it` may change the workspace, as the definition's `writes`
  says

### scenario.commands.unique-names — Two parts cannot register one command name

- GIVEN a part that registered the execution command `check-it`
- WHEN another part registers a definition named `check-it`, whether equal to the first or
  different
- THEN the command catalog refuses it with `duplicate_definition`
- AND the refusal names both parts
- AND the first definition stays registered with the first part

### scenario.commands.definition-complete — An incomplete command definition is refused

- GIVEN a part that registers an execution command definition
- WHEN the definition names no providing Module or does not require a
  [workspace binding](../../glossary.json#concept.workspace-binding)
- THEN the command catalog refuses the definition with `invalid_definition`
- AND the command catalog does not list the definition

### scenario.commands.not-an-operation — An execution command is not run as an Operation

- GIVEN a part that registered the execution command `check-it`
- WHEN `concorde run check-it` starts in a bound workspace
- THEN the command fails with a command-line error
- AND the command-line error names `concorde check-it` as the command to use
- AND that command starts no run
