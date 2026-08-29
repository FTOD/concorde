# Design Reference: Architecture Core

This reference explains and justifies the Architecture Core module. Responsibility, boundary, and
the service contract remain owned by `module.md` and
`architecture/contracts/architecture-services/contract.md`.

## Implementation Notes

### Concorde Architecture Service Protocol v1 (bounded summary)

The maintained definition is `architecture/contracts/architecture-services/contract.md`; the
normative JSON Schema is
`specs/concorde/features/001-concorde-workflow/contracts/architecture-service.schema.json`.
The outline below is explanatory and does not replace either.

- **Role / flow**: provided, bidirectional.
- **Consumers**: Spec Kit Integration and Documentation.
- **Representation**: custom Concorde Architecture Service Protocol v1.
- **Message meaning**: request one deterministic operation over one project architecture package and
  return either a complete result or explicit findings.
- **Compatibility**: v1 consumers ignore unknown optional fields; removing or changing a required
  field requires a new major protocol version.
- **Validation evidence**: verified by schema/example contract tests, deterministic operation tests,
  and zero-finding self-application to Concorde's maintained hierarchy.
- **Required contracts**: explicit empty set for the current slice; filesystem access is treated as
  an implementation detail constrained to the project root.

Field semantics:

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `schema_version` | integer | yes | Contract version; exactly `1`. |
| `operation` | string | yes | One of `init`, `context`, or `validate`. |
| `target` | string | yes | Project-relative path or stable module/feature ID. |
| `options` | object | request | Operation-specific documented options; empty is valid. |
| `status` | string | response | Completed outcome: success, proposal, unchanged, invalid source, conflict, or execution failure. |
| `artifacts` | list | response | Project-relative sources read, created, or returned. |
| `findings` | list | response | Deterministic diagnostics with rule, location, and remediation. |
| `result` | object | response | Operation-specific proposal, context, or validation result. |

Representative serialized example (the common envelope only; the complete representative context and
validation values linked by the contract contain every required nested field):

```json
{
  "schema_version": 1,
  "operation": "context",
  "target": "module.concorde",
  "status": "success",
  "artifacts": ["specs/concorde/architecture/diagrams/level-view.json", "specs/concorde/module.md"],
  "findings": [],
  "result": {"context": {"requested_id": "module.concorde"}}
}
```

### Runtime realization

The runtime is standard-library Python (3.11 or later) under `extensions/concorde/runtime/concorde/`.
`repository.py` owns canonical two-level feature discovery and safe path classification;
`frontmatter.py` and `model.py` own the supported YAML subset and source model; `initialize.py`,
`context.py`, `readiness.py`, and `validate.py` own the deterministic operations; `projection.py`
owns bounded module and feature projections; the `validation/` package holds the rule families
(hierarchy, layout, summary, diagrams, contracts, scenarios, evidence, freshness); `implementation_acceptance.py` owns
approval-gated, atomic acceptance; and `diagnostics.py` produces versioned canonical envelopes. Module
containment, feature refinement, and feature containment are validated as three separate acyclic
graphs. Generated outputs are checked for freshness through the responsible deterministic adapter;
renderer and publication validators keep ownership of their formats and their findings are
normalized rather than reimplemented.

## Design Rationale

- One-level visibility: context exposes only the current module, immediate submodules, current-level
  features and contracts, permitted externals, scenarios, and stable deeper references, so a reader or
  agent never holds more than one level and sibling or lower bodies are never expanded implicitly.
- Independence: the runtime knows nothing of skill or slash-command syntax, archive formats, Archify,
  or Docusaurus, so any integration or publication change leaves source semantics untouched.
- Determinism over judgment: the validator is read-only, reports every independently detectable
  finding in a stable order with a rule ID and remediation, and never guesses the meaning of an
  unsupported construct; this is what makes validation usable as a review gate.
- Explicit empty required set: keeping filesystem access an internal detail confined to the project
  root avoids a boundary contract for something no counterparty can substitute.

## Alternatives Considered

- A new major protocol version for the document-model additions was rejected; v1 stays with
  additive optional navigation references (summary, design reference, diagram list, implementation
  paths)
  because no existing result meaning changes.
- Heuristic detection of module summary sections was rejected in favour of fixed heading names so
  the shape rules are deterministic.
- No other alternatives have been recorded for this module yet.

## Decision Log

- 2026-08-29 — Adopted Architecture Source Profile 4 (feature.concorde.workflow): a module package
  keeps its diagrams under `architecture/diagrams/` (any number and any supported kind, discovered
  from the folder, each referenced from `module.md`, `design.md`, or the reflection log), its
  boundary contracts under `architecture/contracts/`, and its submodules under
  `architecture/modules/`, beside `features/`; the single front-matter-declared `architecture.json`
  and the feature `architecture_view` field were withdrawn. Rules owned here: the level-view rules
  `CONCORDE-VIEW-001..005` are evaluated over all of a level's `architecture`-kind diagrams,
  `CONCORDE-VIEW-006` reports an unreferenced module diagram, `CONCORDE-LAYOUT-010` reports Profile 3
  remnants, and `CONCORDE-LAYOUT-011` reports a misplaced module. Initialization seeds
  `<root>/architecture/diagrams/level-view.json` as its fourth file, and the v1 context result
  carries `current_module.diagrams` in place of the optional `current_module.view` reference, with
  externals, scenarios, and readiness `affected_views` drawn from all of the level's diagrams;
  the protocol stays at v1.
- 2026-08-27 — Adopted the module summary / design reference split and renamed feature design.md to
  implementation.md (feature.concorde.workflow); this module's `module.md` was rewritten to the
  summary shape and its protocol narrative moved here. Decisions of the same attempt that touch this
  module, pending the feature's acceptance: Architecture Source Profile 2; the summary rule family
  `CONCORDE-SUMMARY-001..005` and reference rule `CONCORDE-MODULE-002`; layout rules
  `CONCORDE-LAYOUT-005/007/008` for feature-root pairing and legacy names; additive navigation
  references in the v1 context result; and atomic multi-file acceptance apply with rollback.
