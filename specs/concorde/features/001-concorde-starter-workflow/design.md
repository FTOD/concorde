# Feature Design: Concorde Core Workflow

**Feature**: `feature.concorde.core-workflow`

**Design status**: Accepted baseline through nested workspace routing, bounded context, and
deterministic validation. The durable-design hardening behavior added to `spec.md` on 2026-08-23 is
the next implementation delta and is not claimed as accepted by this baseline.

## Realization Overview

The Concorde core workflow is realized by composing normal Spec Kit lifecycle phases with a small
set of Concorde architecture operations. The normal phases remain agent-directed procedures. Before
they access paths, an installed selected-workspace adapter resolves the active nested feature and
separates durable feature-root artifacts from the temporal `implementation/` directory. Concorde
operations use portable launchers to reach a deterministic Python runtime for initialization,
feature placement/selection, bounded context, and validation.

The root module architecture in `specs/concorde/architecture.json` remains authoritative for module
ownership and boundary organization. This design explains how those owned capabilities collaborate
to realize Feature 001; it does not redefine their boundaries.

## Module and Feature Collaboration

- `module.concorde.spec-kit-integration` provides selected-feature workspace routing and the
  agent-facing command surfaces used by normal Spec Kit phases.
- `module.concorde.architecture-core` provides initialization, bounded context, architecture
  readiness, and deterministic validation through `contract.core.architecture-services`.
- `module.concorde.distribution` packages the preset and extension described by Feature 003; Feature
  001 defines their behavioral handoff but does not own installation.
- `module.concorde.documentation` consumes validated durable sources and generated diagrams through
  Feature 002; it never mutates the workflow authorities.

The root `feature.concorde.core-workflow` coordinates these capabilities through
`contract.concorde.core-workflow`. Lower-level integration and architecture-core features refine the
workspace and architecture-service responsibilities at the adjacent module level.

## Scenario Realization

### Establish and navigate architecture

An installed Concorde command reaches the Python runtime through the project-relative launcher. The
runtime reads `.concorde/config.json`, loads the recursive specification package, and returns only the
current module plus its immediate children, contracts, features, externals, and deliberate navigation
references.

### Place and select a feature

Feature placement uses bounded architecture context to propose the providing module and nested
feature root. After explicit approval, the normal specify phase authors the canonical `spec.md`, the
providing module registers the stable feature ID, and `.specify/feature.json` records only the nested
feature root. Subsequent phase routing derives all durable and temporal paths from that selection.

### Plan and implement

The `concorde-core` preset replaces the nine path-sensitive normal command procedures. Each procedure
invokes `workspace.py --phase <phase>` before reading or writing lifecycle artifacts. Specification,
clarification, and requirements checklists use the feature root. Planning, tasks, implementation,
analysis, convergence, task-to-issue conversion, and delivery validation use `implementation/`.

### Reconcile and validate

Architecture Core discovers maintained module, feature, contract, scenario, and diagram sources plus
bounded implementation evidence. Focused validators check hierarchy, layout, contracts, scenarios,
evidence, and generated freshness in stable order. Findings are canonical structured output and do
not authorize source mutation.

## Durable Implementation Decisions

- The Spec Kit selected-feature record is reused; Concorde maintains no parallel workspace registry.
- Installed command Markdown is package-neutral intent. Coding-agent skills or slash commands are
  presentations of that intent, while deterministic operations live in the installed runtime.
- All runtime and adapter entry paths are project-relative so installed projects do not depend on the
  Concorde source checkout.
- Module architecture, feature behavior, temporal work, code/tests, and generated read models retain
  separate authority even though they coexist in one project.
- Feature diagrams are maintained Archify JSON declared by `spec.md`; generated HTML is a reproducible
  read model rather than a maintained source.

## Traceability and Evidence

- The installed component and workspace relationships are maintained in
  `diagrams/core-workflow-components.json` and delivered to
  `generated/architecture/concorde-core-workflow-components.html`.
- The normative command handoff is `contracts/agent-commands.md`.
- Workspace path/result shapes are defined by `contracts/feature-workspace.schema.json` and its
  examples.
- Maintained source semantics are defined by `contracts/architecture-sources.md`.
- Automated baseline evidence is recorded under the current temporal
  `implementation/validation.md`; it remains temporal until the new hardening lifecycle is
  implemented and explicitly invoked.

## Known Limitations and Next Delta

The accepted baseline does not yet create `design.md` for every newly specified feature, expose the
sixth `speckit.concorde.feature.harden` surface, enforce task-complete eligibility, or atomically
remove a hardened implementation workspace. Those behaviors are requirements of the revised
Feature 001 specification and must be implemented and validated in the current attempt before they
can replace this limitation section through an explicit hardening operation.
