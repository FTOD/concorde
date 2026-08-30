# Validation Evidence: Relax Fast-Loop Eligibility

## Baseline

- **Worktree at implementation start**: selected Feature 010 specification/contract, reflection log,
  and this attempt were already changed by specification/planning. Unrelated Claude reflection-triage
  setup appeared concurrently in `.gitignore`, `.claude/agents/`, `.claude/reflections.config.json`,
  `.claude/settings.json`, and `.claude/skills/reflections-triage/`; these paths are excluded and must
  remain byte-identical.
- **Canonical command digest before implementation**:
  `sha256:7d74a4a22553bcf4f56b158e1e1fb251aab9384939dfc4239d9c4e297549aae4`.
- **Child accepted realization before implementation**:
  `sha256:ff6e038505ec61c75d63b221dd7e635e6cc3df07e2d713215a86a036bad99f9f`.
- **Parent accepted realization before implementation**:
  `sha256:46171981ba9674a65438ca53b7a497a0796fd726367277bfc2f5c694ecc75429`.
- **Root module summary before implementation**:
  `sha256:803b0ceb4bdae9575097938318eebc4c3216f1203b3553d4604365873a176473`.
- **Self-host baseline**: active integration `claude`, status `current`, all source/installed/registry/
  surface dimensions matching, activation `reload_required`.
- **Obsolete policy locations**: canonical preset command plus installed Codex/Claude and self-hosted
  preset projections; accepted child realization remains intentionally unchanged until acceptance.

## Test-First Evidence

- Added policy assertions to command/contract, installed Codex, installed Gemini, self-hosted
  Codex/Claude, and repeated explicit-root workspace tests.
- Ran `.venv/bin/python -m unittest tests.concorde.contract.test_agent_commands
  tests.concorde.unit.test_feature_workspace`: 16 tests, 15 passed and the new canonical policy test
  failed at missing `anchor feature`, proving the old command did not satisfy the relaxed contract.

## Architecture Review

- **State**: `review_pending`
- **Sources**:
  - `contracts/fast-loop-command.md`;
  - `../contracts/architecture-sources.md` and `../contracts/agent-commands.md`;
  - `specs/concorde/architecture/contracts/concorde-workflow/contract.md`;
  - `../diagrams/concorde-workflow-components.json`;
  - `specs/concorde/architecture/diagrams/skill-workspace-file-flow.json`;
  - parent/child behavioral designs and abstracts that describe the architecture-review boundary.
- **Requirement**: Present the exact validated architecture diff with the acceptance proposal; do not
  treat it as final project intent before maintainer confirmation.
- **Archify**:
  - Parent architecture view: specification
    `sha256:57c825622c9b7a318fd47c0d3e46c43846ee8cf212b6e5cc867bdd0055cfa5d0`,
    delivered artifact
    `sha256:c3ead4cc71266889db2873aca79fab1bbc5b35ce8a78f772db2345650df6059f`;
    9/9 showcase checks, 16 repository references verified, zero errors/warnings.
  - Project data-flow view: specification
    `sha256:0d361db3d4449b09526f4889ac86f2e5e0d5fd5d4003a8bfd7857b12838d84f1`,
    delivered artifact
    `sha256:9ac99458955a43c260f016ecbfd97e55146d1238fd8ed5f8292e7bce1ddb87f2`;
    9/9 showcase checks, zero errors/warnings.
  - Visual check: `skipped`; Chrome/Chromium unavailable, visual review remains pending (R-026).

## Proposed Accepted-Realization Delta

Neither accepted `implementation.md` is edited during task execution.

### Feature 010 candidate

- Keep fast-loop additive, agent-followed, root-scoped, attempt-free, and acceptance-free.
- Replace one-feature ownership with one selected anchor plus a complete affected feature set. Invoke
  the existing adapter independently for every affected root; Protocol v8 and Python runtime remain
  unchanged.
- Require non-placeholder accepted realizations and absent attempts for every affected feature.
- Permit bounded cross-feature behavior plus related contract/data-format, maintained-diagram,
  module-reference, and user-guide reconciliation.
- Reject feature/module creation or restructuring, module responsibility/dependency changes,
  project-level compatibility/migration policy changes for users of the whole project, unsafe
  worktree overlap, and material ambiguity.
- Add per-feature hashes/document impact and architecture review states `not_required`,
  `review_pending`, and `reviewed`; no success while exact architecture review is pending.
- Preserve hooks, proportional tests, deterministic validation, reflection behavior, failure
  truthfulness, and no-attempt/no-acceptance reporting.

### Parent workflow candidate

- Keep normal phases and `.specify/feature.json` single-root.
- Document fast-loop as the sole exception that repeatedly performs explicit read-only root
  resolution and directly reconciles every bounded affected authority.
- Reconcile shared FR-023, FR-028, FR-035, SC-014, command/architecture contracts, parent view, and
  public guidance without changing component responsibilities or dependencies.

### Root module design-reference amendment candidate

- Script boundary: `fast-loop` uses the same root-scoped adapter first for its selected anchor and
  then explicitly for every discovered affected feature; no new runtime operation or schema.
- Workspace writes: an eligible invocation may reconcile bounded affected features and related
  contract/architecture detail after proportional evidence; maintained architecture edits remain
  pending exact maintainer review.
- Interaction matrix: reads one selected anchor plus independently resolved affected features and
  related contract/code/test/doc evidence; writes every affected feature authority plus related
  contract/architecture/module-reference/user docs; script use is repeated root-scoped routing.
- Rationale: semantic impact discovery remains with the agent while Scripts provide canonical facts
  one root at a time; risk is stable module responsibility/dependency, project-level user policy,
  affected-authority completeness, and worktree safety rather than line or feature count.

## Implementation and Focused Evidence

- Canonical command and Feature 010 contract tests first failed against the old `anchor feature`
  expectation, then passed after implementation.
- Focused command/workspace/installed/self-host suite: 21 tests passed in 16.677 seconds.
- Self-host: refreshed Claude, regenerated Codex, restored the complete generated Codex skill tree
  after the cross-integration deletion defect (R-042), restored Claude as active, and reached
  `status: current` with matching source/installed/registry/surfaces. Both fast-loop projections carry
  the relaxed policy; unrelated reflection-triage assets remain present.
- Skill-creator generic validation was not applicable because it rejects Spec Kit/Claude-owned
  front-matter keys; repository-native gates are authoritative (R-043).
- Release build and verification passed with identical reported digests:
  - bundle `sha256:85e594183e914ac06511e7eac0c5afc0d3be591ffd8946e095d54b43efcb3436`;
  - extension `sha256:db32fe78ceb6a675c2dc1596db676acdba87256f5ad4053f8ba2864f281682f4`;
  - preset `sha256:9e539dc633f0f4b8c8c906004399c93063fe3daf2170910ea8af6932724e9b11`.
- Deterministic Concorde validation: `success`, zero errors, warnings, infos, or findings; source
  digest `sha256:c6d95a16539949add59bd88bb59483673e0d4b25ad6f20e9b72adffdced88e36`.
- Full Python regression: 281 tests passed in 162.472 seconds.
- Complete docsite gate: TypeScript passed; 19 test files / 81 tests passed; 108 pages validated
  with zero errors; optimized production build promoted. The two known non-fatal AJV strict-type
  warnings recurred and are tracked by R-040.

## Final Review

- `git diff --check`: passed.
- Final deterministic Concorde validation: `success`, zero findings/errors/warnings/infos; source
  digest `sha256:95ce3aa83ffef95805b5d563ff725c71a7a1091357b2cf4a7416a820c6b3687d`.
- Active Claude self-host status: `current`; source, installed, registry, and surfaces all matching;
  activation remains truthfully `reload_required`.
- Canonical preset command and `.specify/presets` projection are byte-identical. Codex and Claude
  installed fast-loop projections contain the anchor/affected-set, module-boundary, project-policy,
  and architecture-review rules.
- Obsolete blanket-rejection search returned no maintained occurrence outside the intentionally
  unchanged accepted implementation baseline and negative test assertions.
- `specs/concorde/module.md`, `specs/concorde/design.md`, parent `implementation.md`, and child
  `implementation.md` remain byte-identical during implementation; the module amendment and both
  realization deltas are proposed above for reviewed acceptance/reconciliation.
- Unrelated Claude reflection-triage changes remain present and excluded: `.gitignore`,
  `.claude/agents/`, `.claude/reflections.config.json`, `.claude/settings.json`, and
  `.claude/skills/reflections-triage/`.
- All 28 tasks and the 22-item requirements checklist are complete.
