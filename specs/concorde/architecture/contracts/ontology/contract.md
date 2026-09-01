---
id: contract.concorde.ontology
kind: contract
module: module.concorde
role: provided
flow: bidirectional
representation:
  kind: custom
  format: Concorde Terminology Declaration
  version: "1"
  definition: specs/concorde/features/007-project-ontology/contracts/terminology-declaration.schema.json
examples:
  - specs/concorde/features/007-project-ontology/contracts/terminology-declaration.example.json
counterparties:
  - external.maintainer
  - external.coding-agent
consumers:
  - external.maintainer
  - external.coding-agent
features:
  - feature.concorde.define-project-ontology
evidence_status: partial
---

# Concorde Ontology Contract

## Purpose

Give maintainers and coding agents one readable, deterministic way to define the important concepts introduced by every module, feature, and sub-feature level while reusing ancestor vocabulary consistently.

## Information

The contract carries a level-local terminology declaration with three fields: a preferred term and optional aliases, a non-circular meaning, and zero or more typed relationships to local or inherited concepts. The normative authoring grammar, normalization, identity, and ancestry rules are defined by Concorde Terminology Table Profile 1; the linked JSON Schema and example define the normalized declaration model used for deterministic contract conformance.

## Obligations

- Every maintained module, feature, and sub-feature `design.md` MUST contain exactly one conforming `## Terminology` declaration.
- A level MUST define every important concept it introduces and MUST NOT copy unchanged ancestor rows.
- Preferred terms, aliases, and relationship targets MUST resolve deterministically in the current bounded inheritance scope.
- A descendant MUST NOT incompatibly redefine an inherited expression; a narrower concept uses a distinct preferred term and explicit relationship.
- Maintained text remains authoritative. Archify views visualize relationships and generated documentation projects the table without creating another ontology authority.
- Validation MUST be read-only, deterministic, and actionable.

## Failure Semantics

A missing or malformed declaration, duplicate local expression, inherited redefinition, ambiguous alias, unresolved relationship target, or empty semantic field produces a `CONCORDE-ONTOLOGY-*` error that names the current source and relevant defining level. Validation does not repair or select a meaning automatically.

## Compatibility

Profile 1 permits additional prose outside the terminology section but treats its table headers, expression normalization, ancestry, qualified identity, and relationship grammar as stable. Changing any of those semantics requires a new profile version and an explicit migration of affected designs.

## Evidence

Parser, ancestry, conflict, workflow/template, initialization, non-mutation, self-application, diagram, and documentation projection tests provide the implementation evidence. Evidence remains `partial` until every current Concorde design is migrated and the full validation/docsite suites pass.
