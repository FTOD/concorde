# Feature Design: Concorde Workflow

**Feature**: `feature.concorde.workflow`

**Design status**: Accepted realization of the architecture-aware Spec Kit workflow, including nested feature workspaces, durable feature design, temporal checklist and implementation artifacts, bounded architecture services, deterministic validation, and review-first feature hardening.

## Realization Overview

The Concorde workflow combines normal Spec Kit phases with deterministic architecture and workspace controls. Spec Kit remains responsible for specification, clarification, planning, tasks, implementation, analysis, convergence, and task-to-issue conversion. Concorde adds reviewed module ownership, nested feature placement and selection, phase-specific workspace routing, bounded architectural context, deterministic validation, feature-owned diagrams, and explicit promotion of a completed implementation milestone into durable design.

A feature root separates permanent sources from one active delivery attempt. `spec.md`, `design.md`, feature contracts, and maintained Archify JSON under `diagrams/` are durable. Requirements-quality review state, planning artifacts, tasks, research, technical models, acceptance guidance, and validation evidence live only under `implementation/`. The selected feature root is stored in Spec Kit's project-local `.specify/feature.json`; Concorde derives all other paths rather than maintaining a parallel workspace registry.

The root module architecture in `specs/concorde/architecture.json` remains authoritative for ownership, boundaries, and one-level organization. This design records how those architectural capabilities collaborate to realize Feature 001 without redefining them.

## Module and Feature Collaboration

- `module.concorde.spec-kit-integration` provides `contract.integration.feature-workspace`, normal-command composition, installed agent command surfaces, nested feature creation and selection, and phase-specific path routing. Its child `feature.integration.manage-feature-workspace` refines this feature's workspace behavior.
- `module.concorde.architecture-core` provides initialization, placement support, bounded context, readiness checks, and deterministic validation through `contract.core.architecture-services`. It remains independent of agent-specific presentation and documentation tooling.
- `module.concorde.distribution` packages the `concorde-core` preset and `concorde` extension consumed by Feature 003. Feature 001 owns the behavioral handoff; Distribution owns archive, catalog, installation, update, and removal mechanics.
- `module.concorde.documentation` consumes validated durable sources and generated diagram projections through Feature 002. It publishes a read model and never mutates maintained intent.

The `concorde-core` preset replaces nine path-sensitive Spec Kit command surfaces so workspace resolution occurs before normal phase work. The `concorde` extension supplies six Concorde-specific command definitions plus portable Bash, PowerShell, and Python launchers, the selected-workspace adapter, and the deterministic Python runtime. Coding-agent skills and slash commands are presentations of package-neutral Markdown; they instruct an agent but do not independently implement runtime behavior.

The custom Feature Workspace Protocol v2 carries safe project-relative durable and temporal paths, selection state, proposed changes, findings, and source digests. Architecture operations use Architecture Service Protocol v1. Module contracts retain architectural ownership; feature-local schemas and examples define the detailed representations used by this feature.

## Scenario Realization

### Establish and navigate the architecture hierarchy

A maintainer invokes `speckit.concorde.init`, `context`, or `validate` through an installed agent surface. The portable launcher loads the extension-relative Python runtime, which reads `.concorde/config.json` and the recursive `specs/` package. Context projection returns the requested module, its features and contracts, immediate children and their I/O summaries, permitted externals, current-level scenarios, and stable navigation references while excluding child feature bodies and grandchildren. Validation runs focused hierarchy, layout, contract, scenario, evidence, and freshness rules and returns deterministic findings without changing maintained sources.

### Place, select, and specify a feature

Feature creation uses bounded context to propose a providing module, stable ID, nested feature root, module registration, and source digest before durable mutation. After placement approval, the normal specification phase creates the canonical root `spec.md` and the initial root `design.md`, and selection stores only that feature root in `.specify/feature.json`. Selecting an existing feature validates its ownership and safe path and requires an explicit resume decision for a non-empty active attempt.

For every normal phase, the installed command first invokes `workspace.py --phase <phase>`. Specification and clarification use durable feature-root intent while placing requirements-quality review state at `implementation/checklists/`. Planning reads both root `spec.md` and accepted root `design.md`; planning, task, implementation, analysis, convergence, task-to-issue, and delivery evidence use the same temporal `implementation/` workspace. No root-level checklist, plan, task, compatibility copy, or symlink is created.

### Review, implement, and reconcile

Planning treats `design.md` as the accepted baseline and records only the proposed realization delta in `implementation/`. Architecture review checks the providing module, adjacent refinements, immediate participants, dependency direction, governing contracts, affected one-level views, feature-diagram needs, and expected evidence. During implementation, the agent requests bounded context only for the relevant level. Deterministic validation reports disagreement or unknown evidence rather than inferring correctness from structurally valid architecture.

The maintained core Archify architecture diagram, `diagrams/concorde-workflow-components.json`, shows the stable collaboration among the maintainer, coding-agent integration, nine phase surfaces, six Concorde surfaces, adapters, launchers, runtime, control state, architecture sources, durable feature intent/design, and the temporal attempt. The documentation feature embeds its fresh generated projection automatically on the canonical feature page.

### Harden an accepted milestone

`feature harden --propose` is read-only. The runtime resolves the selected feature, requires at least one recognizable task and no incomplete or malformed task, then scans sorted real Markdown files directly below `implementation/checklists/`. Checked `[X]` or `[x]` items are satisfied; unchecked or checkbox-like malformed items block hardening. A missing optional checklist directory represents zero items, while symlinked checklist or attempt inputs are invalid.

An eligible schema-v2 result returns the exact `proposal_path`, separate task and checklist summaries, workspace paths, source digest, durable design target, and whole-attempt removal target. The agent synthesizes the candidate design and asks the maintainer to approve those exact bytes and paths. Apply re-resolves eligibility, excludes only the canonical proposal file from its whole-attempt digest, rejects stale or escaping inputs, stages the design replacement and complete implementation-directory move, and either commits both outcomes or restores the previous design and attempt.

## Durable Implementation Decisions

- One recursive `specs/` hierarchy contains both behavioral and architectural specifications; no separate architecture source tree is introduced.
- One selected feature root is authoritative. Durable paths derive from that root, `implementation_dir` is `<feature-root>/implementation`, and `checklists_dir` is `<implementation_dir>/checklists`.
- `spec.md` owns required behavior and why it matters; scenarios are representative examples. `design.md` owns the accepted feature realization. Module documents, module contracts, and bounded `architecture.json` views continue to own architectural boundaries and organization.
- The normal checklist phase may read durable feature context, but every generated checklist is temporal. Root checklist aliases and symlinks are rejected rather than supported as migration authorities.
- Installed package sources are primary for user projects. Checked-in `.agents/skills/` and `.specify/` files are self-hosting materializations kept behaviorally aligned with the preset and extension.
- The workspace adapter performs path selection before inherited Spec Kit behavior; deterministic Concorde operations run only through project-relative launchers and extension-relative Python modules.
- Schema-v2 hardening eligibility exposes `proposal_path`, `task_summary`, and `checklist_summary` as operation metadata. The version-1 proposal remains narrowly bound to the target, source digest, complete design content/path, and exactly one implementation-directory removal target.
- Hardening eligibility and maintainer authorization are separate gates. Checked work and passing tests never imply approval, and normal phases never modify durable design or remove the attempt.
- Generated diagrams, documentation pages, catalogs, and receipts are reproducible evidence or read models, not maintained feature or architecture authority.

## Traceability and Evidence

- Behavioral requirements and representative scenarios remain in `spec.md`; module ownership and root interactions remain in `specs/concorde/module.md` and `specs/concorde/architecture.json`.
- Command intent and failure behavior are defined by `contracts/agent-commands.md`; maintained-source semantics are defined by `contracts/architecture-sources.md`; workspace requests, responses, and proposals are defined by `contracts/feature-workspace.schema.json` and its examples.
- Runtime realization is centered in `extensions/concorde/runtime/concorde/feature_workspace.py`, `feature_hardening.py`, `context.py`, `validate.py`, and `diagnostics.py`, reached through the portable scripts in `extensions/concorde/scripts/`.
- User-project routing is shipped by `presets/concorde-core/`; Concorde's self-hosting command skills and templates exercise the same durable/temporal split. Deterministic release catalogs bind the current preset and extension archives.
- Unit, contract, integration, acceptance, clean-install, and release tests cover nested workspace derivation, no-root aliases, command materialization, bounded context, deterministic validation, checklist eligibility, proposal metadata, stale input rejection, atomic apply, and rollback. The accepted milestone passed 103 Python tests, strict Feature Workspace examples, Concorde self-validation with no findings, and the Docusaurus type, test, validation, and production-build gates.
- `diagrams/concorde-workflow-components.json` passed all 9 Archify showcase checks with zero errors or warnings and has a fresh provenance-bearing generated delivery embedded by the documentation build.

## Known Limitations

- Human studies for module placement, workflow mental-model comprehension, architecture approval, and durable-versus-temporal artifact comprehension remain pending; automated evidence does not substitute for those outcomes.
- Browser containment and light/dark perceptual review of the Feature 001 core diagram remain pending because Chrome or Chromium was unavailable during validation. Deterministic diagram checks do not establish visual polish.
- The packaged workflow is compatibility-bounded to the explicitly tested Spec Kit `0.16.4` range. Supporting another host version requires renewed review of all replaced commands, templates, registration behavior, and installed-project matrices.
- Architecture validity and passing workflow tests do not prove application-level implementation correctness. Missing or conflicting code/test evidence remains unknown or disagreement until separately demonstrated.
