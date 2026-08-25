# Feature Design: Concorde Workflow

**Feature**: `feature.concorde.workflow`

**Design status**: Accepted realization of the architecture-aware Spec Kit workflow, including nested feature workspaces, durable feature design, temporal implementation attempts, bounded architecture services, deterministic validation, review-first hardening, and a distributed read-only question surface.

## Realization Overview

The Concorde workflow combines normal Spec Kit phases with deterministic architecture and workspace controls. Spec Kit remains responsible for specification, clarification, planning, tasks, implementation, analysis, convergence, and task-to-issue conversion. Concorde adds reviewed module ownership, nested feature placement and selection, phase-specific workspace routing, bounded architectural context, deterministic validation, feature-owned diagrams, explicit promotion of a completed milestone into durable design, and source-grounded help about the workflow itself.

A feature root separates permanent sources from one active delivery attempt. `spec.md`, `design.md`, feature contracts, and maintained Archify JSON under `diagrams/` are durable. Requirements-quality review state, planning artifacts, tasks, research, technical models, acceptance guidance, and validation evidence live only under `implementation/`. The selected feature root is stored in Spec Kit's project-local `.specify/feature.json`; Concorde derives all other paths rather than maintaining a parallel workspace registry.

The root module architecture in `specs/concorde/architecture.json` remains authoritative for ownership, boundaries, and one-level organization. This design records how those architectural capabilities collaborate to realize Feature 001 without redefining module architecture.

## Module and Feature Collaboration

- `module.concorde.spec-kit-integration` provides `contract.integration.feature-workspace`, normal-command composition, installed agent command surfaces, nested feature creation and selection, phase-specific path routing, and the question procedure. Its child `feature.integration.manage-feature-workspace` refines this feature's workspace behavior.
- `module.concorde.architecture-core` provides initialization, placement support, bounded context, readiness checks, and deterministic validation through `contract.core.architecture-services`. The question surface may read its maintained outputs as evidence but does not invoke an Architecture Service operation.
- `module.concorde.distribution` packages the `concorde-core` preset and `concorde` extension consumed by Feature 003. Feature 001 owns workflow behavior; Distribution owns archive, catalog, installation, update, and removal mechanics.
- `module.concorde.documentation` consumes validated durable sources and generated diagram projections through Feature 002. It publishes a read model and never mutates maintained intent.

The `concorde-core` preset replaces nine path-sensitive Spec Kit command surfaces so workspace resolution occurs before normal phase work. The `concorde` extension supplies seven Concorde-specific command definitions. Six—`init`, `feature-create`, `feature-select`, `context`, `validate`, and `feature-harden`—reach the deterministic Python runtime through portable Bash or PowerShell launchers. `ask` is deliberately agent-only: its package-neutral Markdown tells the coding agent how to inspect installed Concorde guidance and, when needed, the smallest relevant maintained project sources. Coding-agent skills and slash commands are presentations of package-neutral Markdown, not independent runtime implementations.

The custom Feature Workspace Protocol v2 carries safe project-relative durable and temporal paths, selection state, proposed changes, findings, and source digests. Architecture operations use Architecture Service Protocol v1. Module contracts retain architectural ownership; feature-local schemas and examples define detailed representations used by this feature. The question surface returns standard Markdown rather than inventing a deterministic service protocol.

## Scenario Realization

### Establish and navigate the architecture hierarchy

A maintainer invokes `speckit.concorde.init`, `context`, or `validate` through an installed agent surface. The portable launcher loads the extension-relative Python runtime, which reads `.concorde/config.json` and the recursive `specs/` package. Context projection returns the requested module, its features and contracts, immediate children and their I/O summaries, permitted externals, current-level scenarios, and stable navigation references while excluding child feature bodies and grandchildren. Validation runs focused hierarchy, layout, contract, scenario, evidence, and freshness rules and returns deterministic findings without changing maintained sources.

### Place, select, and specify a feature

Feature creation uses bounded context to propose a providing module, stable ID, nested feature root, module registration, and source digest before durable mutation. After placement approval, the normal specification phase creates canonical root `spec.md` and initial root `design.md`, and selection stores only that feature root in `.specify/feature.json`. Selecting an existing feature validates its ownership and safe path and requires an explicit resume decision for a non-empty active attempt.

For every normal phase, the installed command first invokes `workspace.py --phase <phase>`. Specification and clarification use durable feature-root intent while placing requirements-quality review state at `implementation/checklists/`. Planning reads both root `spec.md` and accepted root `design.md`; planning, task, implementation, analysis, convergence, task-to-issue, and delivery evidence use the same temporal `implementation/` workspace. No root-level checklist, plan, task, compatibility copy, or symlink is created.

### Review, implement, and reconcile

Planning treats `design.md` as the accepted baseline and records only the proposed realization delta in `implementation/`. Architecture review checks the providing module, adjacent refinements, immediate participants, dependency direction, governing contracts, affected one-level views, feature-diagram needs, and expected evidence. During implementation, the agent requests bounded context only for the relevant level. Deterministic validation reports disagreement or unknown evidence rather than inferring correctness from structurally valid architecture.

The maintained core Archify architecture diagram, `diagrams/concorde-workflow-components.json`, shows the stable collaboration among the maintainer, coding-agent integration, nine phase surfaces, seven Concorde surfaces, adapters, launchers, six-operation runtime, control state, architecture sources, durable feature intent/design, and the temporal attempt. The documentation feature embeds its fresh generated projection automatically on the canonical feature page.

### Ask about Concorde

A maintainer invokes `speckit.concorde.ask <question>` through an installed skill or slash command. The coding agent first grounds the answer in the installed extension command and preset instructions, which remain available even when no project feature is selected. For a project-specific question it reads only the smallest relevant maintained source set, such as selection state, the active feature's durable documents, the providing module, its one-level architecture view, or the applicable contract. It does not call a launcher, dispatch a Python operation, mutate the workspace, select a feature, run another lifecycle phase, or treat generated pages as authority.

The answer leads with a direct explanation, names the relevant lifecycle stage or command when useful, cites project-relative source paths, and distinguishes framework rules, observed project facts, agent inferences, and uncertainty. When authoritative sources are missing, stale, or conflicting, the agent states that limitation and does not invent a deterministic finding. If the question cannot be safely interpreted, it asks one focused clarification. General command-timing and project artifact-placement questions therefore use the same installed procedure while retaining different bounded evidence.

### Harden an accepted milestone

`feature harden --propose` is read-only. The runtime resolves the selected feature, requires at least one recognizable task and no incomplete or malformed task, then scans sorted real Markdown files directly below `implementation/checklists/`. Checked `[X]` or `[x]` items are satisfied; unchecked or checkbox-like malformed items block hardening. A missing optional checklist directory represents zero items, while symlinked checklist or attempt inputs are invalid.

An eligible schema-v2 result returns the exact `proposal_path`, separate task and checklist summaries, workspace paths, source digest, durable design target, and whole-attempt removal target. The agent synthesizes the candidate design and asks the maintainer to approve those exact bytes and paths. Apply re-resolves eligibility, excludes only the canonical proposal file from its whole-attempt digest, rejects stale or escaping inputs, stages the design replacement and complete implementation-directory move, and either commits both outcomes or restores the previous design and attempt.

## Durable Implementation Decisions

- One recursive `specs/` hierarchy contains both behavioral and architectural specifications; no separate architecture source tree is introduced.
- One selected feature root is authoritative. Durable paths derive from that root, `implementation_dir` is `<feature-root>/implementation`, and `checklists_dir` is `<implementation-dir>/checklists`.
- `spec.md` owns required behavior and why it matters; scenarios are representative examples. `design.md` owns the accepted feature realization. Module documents, module contracts, and bounded `architecture.json` views continue to own architectural boundaries and organization.
- The normal checklist phase may read durable feature context, but every generated checklist is temporal. Root checklist aliases and symlinks are rejected rather than supported as migration authorities.
- Installed preset and extension sources are primary for user projects. Checked-in `.agents/skills/` and `.specify/` files are self-hosting materializations kept behaviorally aligned with those distribution sources.
- Seven Concorde command surfaces are installed, but only six are runtime-backed. The `ask` surface is intentionally an agent-executed, read-only Markdown procedure and is excluded from Python CLI dispatch and launcher inventories.
- Question answers use installed guidance first, bounded maintained project sources only when necessary, project-relative citations, and explicit evidence labels. They remain explanatory agent output, never deterministic architecture validation.
- The workspace adapter performs path selection before inherited Spec Kit behavior; deterministic Concorde operations run only through project-relative launchers and extension-relative Python modules.
- Schema-v2 hardening eligibility exposes `proposal_path`, `task_summary`, and `checklist_summary` as operation metadata. The version-1 proposal remains narrowly bound to the target, source digest, complete design content/path, and exactly one implementation-directory removal target.
- Hardening eligibility and maintainer authorization are separate gates. Checked work and passing tests never imply approval, and normal phases never modify durable design or remove the attempt.
- Generated diagrams, documentation pages, catalogs, receipts, and question answers are reproducible evidence or read models, not maintained feature or architecture authority.

## Traceability and Evidence

Behavioral requirements and representative scenarios remain in `spec.md`; module ownership and root interactions remain in `specs/concorde/module.md` and `specs/concorde/architecture.json`. Command intent and failure behavior are defined by `contracts/agent-commands.md`; maintained-source semantics are defined by `contracts/architecture-sources.md`; workspace requests, responses, and proposals are defined by `contracts/feature-workspace.schema.json` and its examples.

Runtime realization is centered in `extensions/concorde/runtime/concorde/feature_workspace.py`, `feature_hardening.py`, `context.py`, `validate.py`, and `diagnostics.py`, reached through portable scripts in `extensions/concorde/scripts/`. The question realization is defined by `extensions/concorde/commands/speckit.concorde.ask.md`, materialized for supported agents, and mirrored for this self-hosting checkout by `.agents/skills/speckit-concorde-ask/SKILL.md`. User-project phase routing is shipped by `presets/concorde-core/`; deterministic release catalogs bind the current preset and extension archives.

The accepted milestone passed all 108 Python unit, contract, integration, acceptance, clean-install, and release tests. Focused question-surface evidence covered seven unique installed artifacts, four scripts, the six-operation runtime boundary, installed-source grounding, Codex/Gemini presentation equivalence, checkout independence, absence of a launcher from `ask`, representative question semantics, and unchanged hardening behavior. Concorde source validation returned 35 sorted artifacts, zero findings, and source digest `sha256:c1ac8cb03aae14ccaca3e9f7767198f992702170d88579fb7a035b5f13db877a`.

The documentation gate passed TypeScript checking, 15 Vitest files with 33 tests, validation of 45 published pages with 17 temporal sources excluded and zero errors, diagram embedding and freshness checks, and a production Docusaurus build. Deterministic release build and verification produced `concorde-0.1.0.zip` (`sha256:8aa61ab7bd6c34449bcf5e0fca52009d9f5e09e4df6b5b4eda893026018ffc19`), `concorde-core-0.1.0.zip` (`sha256:04dca60d7fe2e0ab596a307afc6d6657a8f3c2233352ccf028feab2fe898758c`), and `concorde-starter-0.1.0.zip` (`sha256:1bc7ab13051a3f01c1491ca475e7b29664f0c04754e532ea1949b5104f6b5af2`).

All four affected maintained diagrams passed all nine Archify showcase checks with zero errors or warnings. The Feature 001 core source digest is `5aea587f1299c912f74002a48b7681b7902ef2609607e2c8083b69e85b0d88ef`; its generated artifact digest is `e42580274313ff0b1b9cc4a9b71409fd5302ad811ad2400256a53f7586354fbb`. Representative question review is recorded as agent/human semantic evidence rather than deterministic runtime proof, and it left the measured workspace digest unchanged at `70c654088ebc9847f6383ea09c507021c5fdc5beec28fa44a69e893df6a3174d`.

## Known Limitations

- Human studies for module placement, workflow mental-model comprehension, question usability, architecture approval, and durable-versus-temporal artifact comprehension remain pending; automated evidence does not substitute for those outcomes.
- Browser containment and light/dark perceptual review of the affected diagrams remain pending because Chrome or Chromium was unavailable during validation. Deterministic diagram checks do not establish visual polish.
- The packaged workflow is compatibility-bounded to the explicitly tested Spec Kit `0.16.4` range. Supporting another host version requires renewed review of all replaced commands, templates, registration behavior, and installed-project matrices.
- Architecture validity, passing workflow tests, and source-grounded question answers do not prove application-level implementation correctness. Missing or conflicting code/test evidence remains unknown or disagreement until separately demonstrated.
- Feature 003's current distribution sources package all seven command surfaces, but its accepted `design.md` still records the prior six-command baseline. That durable cross-feature design remains pending a separate completed Feature 003 attempt and explicit hardening approval.
