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

A definition is a `Provider` value of `concorde.execution.context`. Execution owns that class and
gives its constructor in [The provider interface](../runner.md#the-provider-interface). The value is
frozen. The constructor requires `name`, `task_type`, `writes` and `steps`. Every other field has a
default. The catalog reads these fields of it:

| Field | Meaning | Default |
| --- | --- | --- |
| `name` | the name a command line gives the run; for an execution command, also the name of its `concorde` command | required |
| `kind` | `operation` or `command` | `operation` |
| `module` | the identity of the providing [Module](../../glossary.json#concept.module), such as `module.understanding` | none, which the catalog refuses |
| `workers` | the [worker ids](../../glossary.json#concept.worker-id) of the workers the Operation may launch; the first is the default; an execution command has none | `("worker",)` |
| `task_type` | the [task type](../../glossary.json#concept.task-type) of the workers, or none when each run names it | required |
| `binding` | `required`, or `optional`, with which the definition may also run [unbound](../../glossary.json#concept.unbound-run) | `required` |
| `writes` | whether a run may change the workspace; for an execution command, what the command catalog reports as what the command writes | required |
| `output_schema` | the contract of the output | none: any output passes |

The runner reads the other fields, as
[What a definition gives the runner](../runner.md#what-a-definition-gives-the-runner) says:

| Field | Meaning | Default |
| --- | --- | --- |
| `steps` | the ordered step functions | required |
| `add_arguments` | the function that adds the definition's own arguments | none: no argument of its own |
| `admit` | the definition's admission of the Modules | none: the Modules as named |
| `runtime_paths` | the runtime-path resolver of a definition that may run unbound | none: nothing is linked |

The function `command(name, steps, **fields)` of `concorde.execution.context` builds the definition
of an execution command. It sets the kind `command`, no task type and no worker id. It passes the
other fields on unchanged, so a command's `writes` and `module` are given among them.

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
