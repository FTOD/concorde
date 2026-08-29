# Feature Implementation: Run Workflow Operations

**Realization status**: Accepted implementation baseline.

## Realization Overview

Portable launchers and Python adapters dispatch to the runtime modules under
`extensions/concorde/runtime/concorde/`. The selected-workspace adapter serves normal phases; the CLI
serves init, context, validate, and implementation acceptance.

## Module and Feature Collaboration

Skills request operations. Workspace Files define every valid input and output path. Documentation
may consume validation results but cannot request source mutation.

## Scenario Realization

Repository discovery, parsing, relationship projection, rule evaluation, proposal hashing, and
atomic application are separated so a failed stage leaves maintained files unchanged.

## Durable Implementation Decisions

All results share one envelope. Findings are sorted and explicit. File-system access stays beneath
the discovered project root. Approved application rechecks the reviewed digest.

## Traceability and Evidence

Runtime unit, contract, integration, installed launcher, workspace-safety, and self-validation tests
cover the realized operations.

## Known Limitations

The runtime supports the configured Concorde profile and explicitly tested Python versions only.
