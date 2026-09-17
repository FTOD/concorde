# Validation requirements

These precise specifications belong directly to the [Validation Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

No specialized terminology.

## Validation

### req.development.check-isolation — Configured checks use enforced read-only execution

Validation SHALL execute configured checks through [Harness Module](../harness/module.md)'s OS-enforced project-read-only executor.
