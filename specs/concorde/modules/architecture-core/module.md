---
id: module.concorde.architecture-core
kind: module
parent: module.concorde
children: []
features:
  - feature.architecture-core.manage-bounded-sources
contracts:
  provided:
    - contract.core.architecture-services
  required: []
---

# Architecture Core

## Responsibility

Define the Concorde source model and provide deterministic initialization, bounded context retrieval,
and validation over module, feature, scenario, contract, and architecture-view relationships.

## Boundary

Architecture Core owns source semantics, stable identity, relationship resolution, one-level
visibility, and validation findings. It does not own agent invocation syntax, distribution, Archify
rendering, Docusaurus publication, or implementation correctness.

## Structure

This leaf module has no submodules, so no separate level view is maintained; its structure is the one
feature and the one provided contract inventoried below, realized by the standard-library Python
runtime under `extensions/concorde/runtime/concorde/`. The Feature 001 core view
<a href="/architecture/concorde-workflow-components.html">workflow components</a> (maintained source
`specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json`) shows how
the installed command surfaces reach this runtime and which architecture sources it reads.

## Features

| Feature ID | Outcome | Refines | Specification |
|---|---|---|---|
| `feature.architecture-core.manage-bounded-sources` | A maintainer or coding agent can safely propose a root specification hierarchy, retrieve exactly one architectural level for feature placement or implementation, and deterministically validate maintained module, feature, contract, scenario, evidence, and view relationships. | `feature.concorde.workflow` | [spec.md](features/001-manage-bounded-sources/spec.md) |

## Contracts

| Contract ID | Role | Flow | Counterparty | Definition |
|---|---|---|---|---|
| `contract.core.architecture-services` | provided | bidirectional | Spec Kit Integration and Documentation | [contract.md](contracts/architecture-services/contract.md) |

The required set is an explicit empty set for the current slice; filesystem access is an
implementation detail constrained to the project root.

## Submodules

None.

## Representative Scenario

`scenario.architecture-core.manage-bounded-sources` shows an installed Concorde command, materialized
by Spec Kit Integration, sending one Concorde Architecture Service Protocol v1 request across
`contract.core.architecture-services` that names one operation and one target path or stable ID.
Initialization returns a proposal that is applied only after explicit approval; context returns
exactly the requested level (the module, its immediate submodules, current-level features and
contracts, scenarios, and stable deeper references) and nothing deeper; validation reads every source
and returns deterministic findings without writing. Each response is either a complete result or
explicit findings, never a partial silent mutation. Documentation later consumes the validated sources
through its own contracts.

## Design Rationale

Architecture Core is the single place where source semantics, stable identity, and relationship
resolution are decided, so it stays independent of agent command syntax and publication tooling and
exposes one deterministic service protocol. Determinism (byte-equivalent repeated runs and explicit
findings instead of guesses) is what lets validation act as a review gate and lets the other modules
trust bounded context. Protocol details and recorded decisions are in the
[design reference](design.md).
