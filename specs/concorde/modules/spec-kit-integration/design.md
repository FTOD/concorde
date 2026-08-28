# Design Reference: Spec Kit Integration

This reference explains and justifies the Spec Kit Integration module. Responsibility, boundary, and
the five boundary contracts remain owned by `module.md` and the contract documents under
`contracts/`.

## Implementation Notes

### Preset and extension model

The preset and extension are complementary but not interchangeable:

- `concorde-core` is a composition layer without its own runtime. Its template layers add Concorde
  prompts and gates to Spec Kit's existing spec, plan, and task templates. Its command layers override
  the nine affected normal lifecycle surfaces so selected-workspace routing occurs before any
  inherited root-path assumption. Phase meanings remain unchanged: durable `spec.md` and contracts
  stay at the feature root, while requirements-quality checklists and all planning/delivery artifacts
  stay under `implementation/`.
- `concorde` is an active capability package. At installation time, Spec Kit registers its five
  command definitions through the target project's active coding-agent integration. At use time, four
  operational surfaces invoke the same deterministic Architecture Core runtime regardless of their
  displayed skill or slash-command syntax. The fifth, `ask`, is followed directly by the coding
  agent to produce a cited, bounded, read-only explanation; it has no runtime verb.

Neither component replaces the core Spec Kit workflow. The bundle merely installs the tested pair.
The nine preset command overrides call the selected-workspace adapter (`workspace.py --phase`) as the
sole path authority before artifact access; every phase writes only beneath the selected root. For a
sub-feature, commands may read the parent's durable paths as aggregate context but never implicitly
read or write parent or sibling attempts.

### Contract summaries (bounded context)

Maintained definitions live under `contracts/*/contract.md`.

`contract.integration.workflow-composition`

- **Role / flow**: provided, output.
- **Consumers**: Spec Kit feature lifecycle commands.
- **Representation**: commonly adopted Spec Kit preset manifest and template composition, version
  `0.16.4`.
- **Information**: architecture ownership, contract, scenario, traceability, and quality-gate guidance.
- **Guarantees**: composition preserves core lifecycle responsibilities, materializes the winning
  command layer in the active integration, creates no duplicate canonical feature specification, and
  creates no root-level compatibility copy of plan or tasks.
- **Failure**: unresolved templates or incompatible composition stop the affected workflow phase.
- **Evidence**: template composition is verified. Installed durable/temporal routing remains partial
  until every affected winning command surface executes in clean Codex skills and Gemini slash-command
  projects through public preset composition with the source checkout unavailable.

`contract.integration.agent-skills`

- **Role / flow**: provided, bidirectional.
- **Consumers**: supported coding-agent integrations.
- **Representation**: commonly adopted Spec Kit extension command Markdown, version `0.16.4`.
- **Information**: user arguments, bounded project context, requested action, result, and diagnostics.
- **Guarantees**: canonical commands `speckit.concorde.init`, `speckit.concorde.context`,
  `speckit.concorde.validate`, and `speckit.concorde.feature.harden`, plus the agent-only
  `speckit.concorde.ask`, register in the active integration without hard-coded invocation syntax.
  Framework rules, project observations, inference, and uncertainty remain visibly distinguished in
  question answers, which inspect only the smallest relevant installed and maintained sources.
- **Failure**: unsupported integrations or missing dependencies produce an actionable diagnostic.
- **Evidence**: all five command artifacts register in Codex skills mode; the four runtime-backed
  operations remain distinct from `ask`; initialization, context, and validation execute in Codex
  skills and Gemini slash-command modes. Evidence remains partial until feature hardening,
  question-surface semantic review, and the complete normal-command matrix execute from release
  archives in both modes; the platform-compatible registered spelling is `feature-harden`.

`contract.integration.feature-workspace`

- **Role / flow**: provided, bidirectional.
- **Consumers**: maintainers and normal Spec Kit lifecycle commands.
- **Representation**: custom Concorde Feature Workspace Protocol v4 plus Spec Kit's standard
  project-local `feature_directory` selection field.
- **Information**: the resolved standard Spec Kit selection, exact durable/temporal paths,
  relationship context, implementation state, hardening changes, conflicts, findings, and inspected
  source digest.
- **Guarantees**: one nested canonical specification, no root-level plan/task aliases, read-only
  resolution of the standard Spec Kit selection, and no silent replacement of an implementation
  attempt.
- **Failure**: unsafe, stale, unregistered, unknown, or ambiguous targets leave sources and selection
  unchanged and return actionable findings.
- **Evidence**: safe resolution, active-attempt reporting, phase routing, clean installation, and
  no-root-alias behavior are covered by contract, unit, integration, and acceptance tests.

`contract.integration.spec-kit-platform`

- **Role / flow**: required, bidirectional.
- **Provider**: external Spec Kit `0.16.4`.
- **Representation**: commonly adopted extension, preset, command-registration, and hook contracts.
- **Guarantees required**: runtime template resolution and install-time command registration behave as
  documented by Spec Kit.
- **Failure**: incompatibility stops installation or the affected phase without silent fallback.
- **Evidence**: verified against Spec Kit 0.16.4 by the native lifecycle suite.

`contract.integration.architecture-services`

- **Role / flow**: required, bidirectional.
- **Provider**: `module.concorde.architecture-core`.
- **Representation**: custom Concorde Architecture Service Protocol v1 defined by Architecture Core.
- **Information**: target path or stable ID, operation, bounded context, validation findings, and
  artifact changes.
- **Guarantees required**: deterministic results and explicit unknown evidence.
- **Failure**: invalid sources fail without partial silent mutation.
- **Evidence**: verified by structured-result, launcher, and installed bundle-journey tests.

## Design Rationale

- Routing before inheritance: overriding the nine path-sensitive commands and resolving the standard
  selection through one adapter is the only way to keep nested workspaces authoritative without
  changing what each Spec Kit phase means.
- One selection, no second store: the standard `.specify/feature.json` pointer written by specify (or
  `SPECIFY_FEATURE_DIRECTORY`) is resolved read-only; relationship context is derived from validated
  sources rather than duplicated into control state.
- Portable surfaces: command definitions carry no hard-coded invocation syntax, so the same five
  surfaces register in skills and slash-command integrations, and the four runtime-backed operations
  reach one runtime through project-relative launchers.
- `ask` stays agent-followed and read-only so a question can never mutate the workspace or invoke an
  operation by accident, and its answers cite installed guidance before project sources.
- Compatibility is deliberately bounded to Spec Kit 0.16.4; another host version requires renewed
  review of every replaced command, template, and registration behavior.

## Alternatives Considered

- Concorde-owned feature creation and selection commands (`feature.create`, `feature.select`) were
  removed on 2026-08-27 in favour of the standard Spec Kit selection; a second lifecycle or store
  contradicted Spec Kit's ownership of feature creation.
- A `subfeature.create` namespace was rejected for the same reason; sub-features are created by the
  normal specify phase and invalid placement is rejected by validation and workspace resolution.
- Keeping Feature Workspace Protocol v4 with a deprecated alias beside the renamed field was rejected
  in the current document-model attempt because Concorde is the only adopter and an alias would
  prolong the old name across nine command surfaces.
- No other alternatives have been recorded for this module yet.

## Decision Log

- 2026-08-27 — Adopted the module summary / design reference split and renamed feature design.md to
  implementation.md (feature.concorde.workflow); this module's `module.md` was rewritten to the
  summary shape and the preset/extension model and contract narratives moved here. The same attempt
  proposes, pending contract updates and hardening: Feature Workspace Protocol v4
  (`feature_implementation`, `module_summary`, `module_design`, `implementation_digest_*`,
  `module_design_digest_*`); hardening proposal v2; the preset `implementation-template` replacing
  `design-template`; `FEATURE_IMPLEMENTATION` in the tracked bash scripts; and a 0.2.0 bump of
  `concorde-core` and `concorde`.
- 2026-08-27 — Removed `feature.create` and `feature.select`; installed the Claude Code agent
  integration.
- 2026-08-26 — Added the self-hosted development workflow and first-class sub-features.
- 2026-08-25 — Added the source-grounded read-only `ask` command.
