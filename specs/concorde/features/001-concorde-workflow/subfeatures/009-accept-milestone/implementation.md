# Feature Implementation: Deliver Milestone

**Realization status**: Accepted realization of the one-invocation Deliver Milestone workflow, Feature Workspace Protocol v9, delivery proposal v7, and the complete Concorde 0.6.0 surface migration.

**Selected level**: Immediate sub-feature of `feature.concorde.workflow`; parent durable sources remain aggregate read-only context. The stable feature ID and `subfeatures/009-accept-milestone/` path are retained for traceability.

## Realization Overview

Deliver Milestone is the workflow operation that promotes one completed temporal attempt into the selected feature or immediate sub-feature's durable `implementation.md`. Its canonical public surface is `speckit.concorde.deliver`, its runtime verb and structured operation are `deliver`, successful apply returns `delivered`, and diagnostics use `CONCORDE-DELIVER-001` through `CONCORDE-DELIVER-012`.

The user's delivery invocation is the authorization. The agent still invokes a read-only proposal phase, synthesizes a complete digest-bound candidate, and invokes apply immediately, but it does not display a second approval question or wait for another response. This removes one interaction without collapsing the technical safety boundary.

Eligibility still requires at least one recognizable task, every task complete, and every existing checklist item complete and well formed. Apply still enforces canonical paths, a current source digest, the six required implementation sections, centralized reflection ownership, an optional full providing-module design amendment, exactly one whole-attempt removal target, atomic staging, recoverable cleanup, and complete rollback on failure.

The migration is a clean break. The former command, nested CLI verb, operation discriminator, status, diagnostic prefix, proposal filename, command file, runtime module, test modules, and installed skill are absent. No compatibility alias or parser fallback remains. The architecture feature ID and directory retain their stable historical identity; they are not executable aliases.

## Module and Feature Collaboration

The parent `feature.concorde.workflow` owns lifecycle order, the durable-versus-temporal authority model, the six-section feature implementation shape, and the aggregate command inventory. This child owns delivery eligibility, candidate-synthesis guidance, invocation-bound authorization, proposal identity, atomic apply and rollback, cleanup, transient reflection presentation, and normative result reporting.

- `module.concorde.skills` publishes the installed `speckit.concorde.deliver` procedure, the nine normal Spec Kit phase overrides, fast-loop, and the feature templates. The delivery procedure performs propose and apply in one user interaction.
- `module.concorde.scripts` supplies `delivery.py`, CLI dispatch, Feature Workspace Protocol v9 serialization, delivery diagnostics, source-digest computation, reflection parsing, target validation, atomic promotion, and rollback.
- `module.concorde.workspace-files` owns the selected feature's durable trio, the active `attempt/`, proposal path `attempt/deliver-proposal.json`, and delivery proposal v7 shape.
- `module.concorde.distribution` packages preset, extension, and bundle 0.6.0, publishes matching catalogs and reproducible archives, and materializes the delivery skill for Claude and Codex.
- `module.concorde.auto-docs` verifies the renamed maintained sources and fresh diagrams through the project documentation gate; generated pages and HTML remain projections.

The operation crosses `contract.concorde.workflow` and `contract.concorde.spec-kit-platform`. Command intent is governed by `contracts/agent-commands.md`; request, workspace, proposal, status, digest, reflection-summary, and result shapes are governed by `contracts/feature-workspace.schema.json`. Module responsibilities, boundaries, contracts, containment, and dependency direction remain unchanged.

## Scenario Realization

### Deliver an eligible attempt

1. The installed command invokes `deliver --propose` for the explicit target or selected feature.
2. Runtime resolution returns the Protocol v9 workspace, task and checklist summaries, transient reflection counts, exact proposal path, exact cleanup target, and source digest.
3. The agent reads only the bounded selected root, permitted parent context and sibling summaries, providing-module summary and design, relevant contracts and architecture, the complete selected attempt, and cited code and tests.
4. The agent writes delivery proposal v7 with the full feature implementation candidate, an optional full providing-module design replacement when warranted, and exactly the selected `attempt/` removal target.
5. The original command invocation authorizes immediate `deliver --apply --proposal ...`; no second question is emitted.
6. Apply re-resolves every path and completion gate, recomputes the digest while ignoring only the proposal itself, validates durable candidate content, stages every update, moves the attempt recoverably, promotes atomically, and removes recovery artifacts.
7. The result reports prior and resulting implementation digests, optional module-design digests, removed artifacts, retained authorities, reflection summary, findings, selected target, and absent attempt state.

### Reject unsafe or incomplete delivery

Incomplete or malformed tasks/checklists, an invalid target, unsafe or broader paths, copied reflection identifiers, placeholder candidate content, a stale digest, a malformed reflection log, a symlink, or an interrupted filesystem mutation returns `invalid`, `conflict`, or `failed`. Before-state tests prove the previous feature implementation, module design, complete attempt, parent, children, and siblings remain recoverable or byte-identical as required.

## Durable Implementation Decisions

- Proposal and apply remain two internal runtime modes because the agent must author Markdown between eligibility and mutation; only the redundant second user authorization was removed.
- The clean-break vocabulary is `speckit.concorde.deliver`, CLI/operation `deliver`, status `delivered`, `CONCORDE-DELIVER-*`, and `deliver-proposal.json`. The former interface is rejected and has no alias.
- Feature Workspace Protocol v9 and delivery proposal v7 make the incompatible closed-enum changes explicit. Preset, extension, and bundle advance together to 0.6.0.
- Constitution 4.0.0 narrowly authorizes one-invocation delivery after the normal completed lifecycle while preserving validation, digest binding, target restriction, atomicity, rollback, and evidence requirements.
- The stable `feature.concorde.workflow.accept-milestone` ID and canonical directory remain unchanged because architecture identities are durable references, not command aliases.
- Delivery retains the optional full providing-module `design.md` amendment so attempt-developed implementation detail and rationale are not discarded. The amendment remains limited to the providing level and applies atomically with feature realization and cleanup.
- `reflections.md` remains the sole persisted reflection-record authority. Delivery presents attributed entries transiently and rejects reflection identifiers in either durable candidate.
- The parent core component view and root command/workspace data-flow views remain the explanatory authorities. Their topology is unchanged; only delivery labels and invocation semantics changed.
- Canonical extension and preset sources remain authoritative. `.specify`, Claude, and Codex materializations are regenerated projections and require a new agent interaction before reload is externally evidenced.

## Traceability and Evidence

Required behavior is defined by this sub-feature's `design.md` and `abstract.md`, with aggregate lifecycle behavior in the parent feature. Related module summaries, design references, boundary contracts, workflow diagrams, installation specifications, user guides, and Constitution 4.0.0 were reconciled with the same delivery ontology.

Runtime realization is centered in `extensions/concorde/runtime/concorde/delivery.py`, `cli.py`, `diagnostics.py`, and `scripts/python/workspace.py`. Canonical command guidance is `extensions/concorde/commands/speckit.concorde.deliver.md`; installed Claude and Codex surfaces contain `speckit-concorde-deliver` and omit the former skill.

Executable evidence on 2026-09-01 includes 84 focused delivery/runtime/contract/installed/bundle tests and the complete 324-test Python suite. Deterministic Concorde validation returns success with zero findings. The documentation gate passes TypeScript, all 19 Vitest files and 85 tests, validation of 118 pages with zero errors, and an optimized production build. Claude self-host source, installed bytes, registry, and surfaces match; Claude and Codex agent-asset verification both succeed.

Three changed workflow sources each pass Archify's 9/9 showcase gate with zero composition errors or warnings and have fresh generated HTML: `concorde-workflow-components.json`, `skill-workspace-file-flow.json`, and `concorde-command-workspace-file-flow.json`. The component build produces reproducible 0.6.0 bundle, extension, and preset archives whose digests are recorded in the completed attempt validation evidence.

## Known Limitations

- Browser containment and light/dark perceptual review of the three changed diagrams remain pending because Chrome/Chromium is unavailable. Showcase validation and production rendering do not establish visual polish.
- The on-disk self-host state is current, but a new agent interaction is required before the refreshed instruction set can be counted as loaded by the running agent.
- The stable feature ID and directory retain the historical `accept-milestone` token. This is deliberate identity continuity; every current executable and user-facing delivery surface uses the new vocabulary.
