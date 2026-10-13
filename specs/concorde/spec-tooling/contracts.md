# Spec tooling contracts

The exact command-line contracts of the [Spec tooling](module.md) part entries that no child owns.

## The init command {#init-command}

`init` is the adapter over Spec core's `initialize`
([Initialization](spec/contracts.md#initialization)):

```text
concorde init --propose --name <name> [--target <id>] [--python <interpreter>]
concorde init --apply --proposal <file>
```

`--propose` calls `initialize` with action `propose`. `--target` defaults to `module.project`.
`--python` is passed only when given.

`--apply` reads the JSON `<file>`. A relative `<file>` is resolved against the project root. The project
root is the `concorde` command's global `--project-root`, by default the working directory. An absolute `<file>` is used as given. The file may lie outside
the project, since the command only reads it. The file must be an object holding at least
`proposal` and `proposal_digest`. The whole `result` that `--propose` printed is one such object.
Any other field of the file is ignored. The command calls `initialize` with action `apply` and those
two fields. `initialize` checks the proposal itself.

Either way, the command prints Spec core's
[shared envelope](spec/contracts.md#validation-result) with `tool` `init` and `target` `.`:

| Outcome | `status` | `result` | `error` | Exit code |
| --- | --- | --- | --- | --- |
| `initialize` answered | `success` | `initialize`'s answer, whose own `status` is `proposed` or `applied` | `null` | 0 |
| a refusal | `failed` | `{}` | the refusal's [error record](spec/errors.md) | 3 |

Besides the refusals of `initialize`, the adapter refuses these cases with `invalid_input`:

- A malformed command line, such as both `--propose` and `--apply` or neither.
- A propose without `--name`.
- An apply without `--proposal`.
- A proposal file that cannot be read as JSON. The error's cause is the reading or parsing failure.

The adapter refuses a file that is not an object holding both fields with `invalid_proposal`.
No refusal writes a file.
