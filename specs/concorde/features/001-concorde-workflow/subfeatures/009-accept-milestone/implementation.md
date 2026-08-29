# Feature Implementation: Accept Milestone

**Realization status**: Accepted realization of the approval-gated Accept Milestone workflow and the complete 0.4.0 terminology migration.

**Selected level**: Immediate sub-feature of feature.concorde.workflow; parent durable sources remain aggregate read-only context.

## Realization Overview

Accept Milestone is the one workflow operation that accepts a completed temporal implementation attempt as the selected feature's durable realization. The public command is speckit.concorde.impl.accept, the CLI is impl accept, the structured operation is impl.accept, and a successful apply reports status accepted. Proposal mode remains read-only; apply remains impossible without explicit maintainer approval of the exact digest-bound candidate.

The operation preserves the existing safety model: at least one recognizable task, every task complete, every existing checklist item complete and well formed, safe canonical paths, a current source digest, an implementation candidate with the six required sections, citation of every open reflection attributed to the selected feature, an optional full providing-module design amendment, and exactly one whole-attempt removal target. Apply stages every update, moves the attempt recoverably, promotes all outputs atomically, and restores the previous implementation, module design, and attempt on failure.

The migration is a clean break. No command alias, parser fallback, status alias, proposal compatibility branch, diagnostic compatibility name, old feature root, or old installed skill remains. Historical wording survives only in the append-only project reflection log and version-control history.

## Module and Feature Collaboration

The parent feature feature.concorde.workflow owns lifecycle order, durable/temporal authority, the six-section implementation model, and the rule that only explicit acceptance establishes a new baseline. This child owns eligibility, candidate synthesis guidance, proposal identity, approval binding, atomic apply/rollback, cleanup, reflection citation, and result reporting.

Skills publishes the selected-workspace adapter, nine normal-phase overrides, templates, and the renamed installed command surface. Scripts supplies the portable Python runtime, Feature Workspace Protocol v8, acceptance proposal v6, path resolution, reflection parsing, diagnostics, and mutation boundary. Distribution packages concorde-core 0.4.0, concorde 0.4.0, and concorde-bundle 0.4.0 with regenerated catalogs and release artifacts. Documentation publishes the renamed specifications, commands, examples, accepted realizations, and parent core view.

The operation crosses contract.concorde.workflow and contract.concorde.spec-kit-platform. Detailed command intent is governed by the parent agent-command contract; workspace, proposal, status, digest, reflection, and result shapes are governed by feature-workspace.schema.json. Module responsibilities, boundaries, contracts, and one-level organization are unchanged.

## Scenario Realization

A coding agent or maintainer selects one valid feature or immediate sub-feature. The installed launcher invokes impl accept --propose. Runtime resolution returns Protocol v8 workspace paths, task and checklist summaries, reflection counts, the proposal path attempt/accept-proposal.json, the exact attempt cleanup target, and a digest covering the reviewed durable, architectural, reflection, and temporal inputs.

The agent reads only the bounded selected root, read-only parent context for a child, concise sibling summaries, relevant architecture/contracts, the complete selected attempt, and cited implementation evidence. It drafts a complete implementation.md and, only when warranted, a full providing-module design amendment. The proposal uses proposal_version 6 and operation impl.accept, names exactly the returned implementation and optional module-design paths, and contains exactly the selected attempt directory in remove.

The agent presents the complete candidate, any module amendment diff, cleanup manifest, reflection citations, retained authorities, and digest. Checked boxes and successful validation do not grant approval. Only the maintainer's explicit approval authorizes impl accept --apply --proposal.

Apply re-resolves the target and every path, ignores only the proposal itself when recomputing the digest, rejects changed inputs and unsafe or broader targets, checks the candidate and reflection citations, stages updates, moves the attempt to a recoverable backup, and atomically promotes the reviewed bytes. The result reports prior/resulting implementation digests, optional module-design digests, removed artifacts, retained authorities, reflection summary, changes, findings, selected target, and absent attempt state.

## Durable Implementation Decisions

- Accept Milestone is the canonical human-facing label; accept is the command/runtime verb; accepted is the success state.
- The owning feature is feature.concorde.workflow.accept-milestone at subfeatures/009-accept-milestone.
- The runtime module is implementation_acceptance.py with propose_acceptance and apply_acceptance.
- Diagnostics retain their established numeric meanings under CONCORDE-ACCEPT-001 through CONCORDE-ACCEPT-012.
- Feature Workspace Protocol v8 changes the operation and success vocabulary while retaining the workspace, digest, change, artifact, finding, reflection, and result fields.
- Acceptance proposal v6 changes the discriminator and proposal identity while retaining implementation, optional module_design, source_digest, target, and exact remove semantics.
- The seeded empty-realization marker is replaced in full by the first accepted milestone; later milestones complete the same durable file.
- The preset, extension, and bundle advance together to 0.4.0 because command identity, runtime dispatch, protocol, proposal, status, diagnostics, templates, packaging allowlists, and installed surfaces form one breaking interface set.
- Architecture Source Profile 4, Architecture Service Protocol v1, Build Manifest v8, and docsite generator 0.3.0 are unchanged because their structures are unaffected.
- Canonical preset/extension sources remain authoritative. .specify, .agents, and .claude are regenerated mirrors verified against those sources and installed-project acceptance tests.
- The parent workflow core diagram remains the single stable component view. Only its milestone view and connection terminology changed; the generated route and component structure are unchanged.
- The append-only reflection log is intentionally exempt from text migration. Current commands, docs, code, contracts, schemas, examples, tests, specifications, accepted realizations, and mirrors use only the new vocabulary.
- The old interface is rejected rather than translated, keeping one safety-sensitive mutation surface.

## Traceability and Evidence

Behavior is defined by this sub-feature's design.md and abstract.md, with parent aggregate behavior in the Concorde Workflow trio. The agent-command contract, architecture-source contract, Feature Workspace Protocol v8 schema, acceptance proposal/eligibility examples, package manifests, and parent core diagram provide durable traceability.

Implementation is centered in extensions/concorde/runtime/concorde/implementation_acceptance.py, cli.py, diagnostics.py, scripts/python/workspace.py, the impl.accept command Markdown, preset phase guidance and templates, bundle/catalog manifests, self-host and release builders, installed Codex/Claude surfaces, and the renamed Python test/support modules.

Focused runtime, contract, installed-surface, and bundle evidence passes 76 tests. The complete Python suite passes 234 tests. Deterministic Concorde validation returns zero findings. The active-source terminology contract passes and verifies the old command and skill paths are absent.

The complete docsite gate passes TypeScript typechecking, 19 Vitest files with 77 tests, validation of 100 pages with 24 deliberate exclusions and zero errors, and verified production rendering. A syntax-only code-span correction to Feature 002's accepted route placeholder was required for MDX compilation and changed no behavior.

All nine maintained diagrams pass the Archify 2.16 gate with 9/9 showcase checks, composition pass, and zero errors or warnings. The updated parent core view is freshly delivered and embedded at /architecture/concorde-workflow-components.html. No browser visual-check was performed, so the evidence makes no new perceptual-review claim.

The supported Codex self-host apply completed for 0.4.0 and reported source, installed bytes, registry, and surfaces matching. Claude was restored and materialized through the public Spec Kit preset/extension flow. Canonical preset and extension trees are byte-equal to their installed mirrors, the new skills exist, and the superseded skill paths are absent.

## Known Limitations

- The self-host status implementation still cannot assess the active Claude integration; Claude surface confidence comes from public Spec Kit materialization and installed acceptance tests rather than self-host status (project reflection R-001).
- The self-host bootstrap requires an explicit Python interpreter in this checkout; direct execution is not permitted by file mode (R-015).
- The project virtual environment does not install pytest; validation uses the standard-library unittest runner (R-016).
- A shared-component bundle fixture that consumes the live preset must keep its pin synchronized with the current package version (R-017).
- Feature 002 required a syntax-only code-span correction because a bare angle-bracket route placeholder was invalid MDX; future accepted candidates should pass the docsite build before acceptance (R-018).
- Task-scoped temporary backup and release directories outside the repository could not be explicitly removed under the execution policy and are left for normal operating-system cleanup; no project artifact depends on them (R-019).
- The current agent process was initialized before the on-disk skill rename. A new session is required before its capability list displays the new skill name, even though both installed trees and tests are current.
- Historical reflection entries retain their original wording by contract. They are records of what agents encountered, not active command guidance.
- Human perceptual review of the terminology-changed diagrams remains pending; automated showcase and production rendering are not visual approval.
