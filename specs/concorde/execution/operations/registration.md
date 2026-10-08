# Registering a definition

This document specifies how a part registers its definitions with the two catalogs of Execution.
These catalogs are the [Operation catalog](../../glossary.json#concept.operation-catalog) and the
command catalog of [Commands](../commands/module.md). The class `Catalog` of
`concorde.execution.operations.catalog` realizes both catalogs. The Operation catalog is `OPERATIONS`
of that module. The command catalog is `COMMANDS` of `concorde.execution.commands.catalog`. What
the runner does with a definition it looks up is
[What a definition gives the runner](../runner.md#what-a-definition-gives-the-runner).

The [requirements](requirements.md) state the rules every registration follows. The
[scenarios](scenarios.md) show them for Operations. The
[scenarios of Commands](../commands/scenarios.md) show them for
[execution commands](../../glossary.json#concept.execution-command).

## When a part registers

A part registers its definitions when its code loads. The
[part registration](../../glossary.json#concept.part-registration) of the part names that code
among its `loads`. Distribution imports those modules before it routes a command or answers a tool.
So both catalogs are complete before a run looks a name up. In Concorde, Method's module
`concorde.method.registration` registers every
[Operation](../../glossary.json#concept.operation) and execution command of Method.

## The definition

A definition is a `Provider` value of `concorde.execution.context`. Execution owns that class. The
value is frozen. The catalog reads these fields of it:

- `name`: the name a command line gives the run. For an execution command, it is also the name of
  its `concorde` command.
- `kind`: `operation` or `command`.
- `module`: the identity of the providing [Module](../../glossary.json#concept.module), such as
  `module.understanding`.
- `workers`: the [worker ids](../../glossary.json#concept.worker-id) of the workers the Operation
  may launch. The first worker id is the default. An execution command has no worker id.
- `task_type`: the [task type](../../glossary.json#concept.task-type) of the workers, or none when
  each run names it.
- `binding`: `required` or `optional`. With `optional`, the definition may run
  [unbound](../../glossary.json#concept.unbound-run).
- `writes`: whether a run may change the workspace. For an execution command, this field is what the
  command catalog reports as what the command writes.
- `output_schema`: the contract of the output, or none.

The runner reads the other fields:

- `steps`
- `add_arguments`
- `admit`
- `runtime_paths`

The function `command(name, steps, **fields)` of `concorde.execution.context` builds the definition
of an execution command. It sets the kind `command`, no task type and no worker id. It passes the
other fields on unchanged.

## Registering

A part calls `register(part, definition)` of the catalog. The argument `part` is the name of the
part, as its part registration gives it, such as `method`. The call returns nothing. After the call,
the catalog holds the definition under its name, with the part that registered it.

The catalog refuses a registration by raising `CatalogError`. The error has a `code` and a message.
The message names the part and the definition. The catalog refuses these registrations with
`invalid_definition`:

- A value that is no `Provider`, or a definition whose `kind` is not the kind of the catalog.
- A definition whose `module` is no Module identity. A Module identity is `module.` followed by a
  lowercase letter or a digit, and then by lowercase letters, digits, dots and hyphens.
- An Operation without a worker id, or with a worker id that is no nonempty string.
- An execution command whose `binding` is not `required`. Every execution command needs a bound
  workspace.

The catalog refuses a definition under a name it already holds with `duplicate_definition`, except
for a repeated registration (see below). The message names the part that registered the name and
the part that registers it again.

A refused registration changes nothing. The catalog keeps what it held, and it does not list the
refused definition. The error leaves the code of the part as that code loads. A part whose
registration the catalog refuses is therefore an installation error. The `concorde` command cannot
load that part.

## A repeated registration

A part may register the same definition again. When the same part registers a definition equal to
the definition it registered under that name, the registration changes nothing. Two definitions are
equal when every field is equal. Functions, such as the steps, are equal only when they are the same
object. So the code of a part may load twice in one process.

Every other registration under a name the catalog holds is refused with `duplicate_definition`.
This includes these registrations:

- A definition that is not equal to the registered one, from any part.
- An equal definition from another part.

After the refusal, the first definition stays registered with its part.

## Looking a definition up

The catalog answers these questions:

- `get(name)`: the definition registered under the name, or none.
- `part(name)`: the part that registered the name, or none.
- `module(name)`: the identity of the Module that provides the name, or none.
- `name in catalog`: whether the catalog holds the name.
- Iteration: the names the catalog holds, in sorted order.

The runner looks a name up when it parses the command line. A name that no installed part
registers is a command-line error that names it. No run begins.

## Compatibility

The catalogs exist only in the process of the installed Concorde. A definition is a Python value of
the same installation. It has no wire format and no version. Concorde promises no compatibility of
this interface across its versions. A part outside Concorde that registers definitions follows the
interface of the installed Concorde.
