# Concorde extension

The extension registers five integration-neutral commands:

- `speckit.concorde.init` proposes a root specification hierarchy and writes only after explicit
  acceptance of an exact proposal.
- `speckit.concorde.feature.create` proposes a nested, module-owned feature workspace and starts its
  one canonical specification only after approval.
- `speckit.concorde.feature.select` atomically selects an existing nested feature for the normal
  Spec Kit phases.
- `speckit.concorde.context` returns one bounded architectural level.
- `speckit.concorde.validate` deterministically validates the configured hierarchy.

The extension also provides the selected-workspace adapter used by the preset's nine normal command
replacements. Every command invokes the installed, standard-library Python runtime through
project-relative paths. Target projects need Python 3.11 or newer; they do not need `uv` or
third-party Python packages.
