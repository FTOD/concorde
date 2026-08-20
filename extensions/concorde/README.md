# Concorde extension

The extension registers three integration-neutral commands:

- `speckit.concorde.init` proposes a root specification hierarchy and writes only after explicit
  acceptance of an exact proposal.
- `speckit.concorde.context` returns one bounded architectural level.
- `speckit.concorde.validate` deterministically validates the configured hierarchy.

Every command invokes the installed, standard-library Python runtime through project-relative paths.
Target projects need Python 3.11 or newer; they do not need `uv` or third-party Python packages.
