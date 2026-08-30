# Research: Relax Fast-Loop Eligibility

## Decision: Use one selected anchor and a discovered affected feature set

**Rationale**: Spec Kit's standard selection is intentionally one canonical pointer, and Protocol v8
already resolves any explicit feature directory safely. Fast-loop needs a starting context, not a new
multi-selection registry. The agent can discover related behavioral authorities from relevant code,
tests, contracts, module summaries, and docs, then call the adapter explicitly for each affected root.
This retains path safety while removing the one-feature eligibility restriction.

**Alternatives considered**:

- Add a multi-feature array to `.specify/feature.json`: rejected because it would change selection for
  every normal phase and duplicate Spec Kit's ownership.
- Add all project features to every workspace response: rejected because it weakens bounded context
  and still cannot determine semantic impact automatically.
- Treat paths inferred by the agent as authoritative: rejected because every affected root can use
  the existing adapter and its canonical path checks.

## Decision: Define significant architecture by module responsibility and dependency direction

**Rationale**: Module boundaries are the stable ownership/dependency model. Contract payloads,
schemas, examples, maintained views, and module references are architecture detail that may need to
change for a small coordinated correction. Keeping them categorically out of fast-loop causes common
bounded changes to require ceremony without changing architectural decomposition.

**Alternatives considered**:

- Keep every contract or diagram edit ineligible: rejected by the requested policy and because it
  conflates boundary detail with changed module ownership.
- Allow module responsibility/dependency changes when the diff is small: rejected because line count
  cannot make a boundary redesign low-risk.

## Decision: Keep whole-project compatibility and migration policy at project level

**Rationale**: The fast-loop compatibility gate protects promises to users who adopt the entire
project. Internal contract formats and coordinated feature behavior may change when all affected
authorities and evidence are reconciled. Feature and module sources may describe current format facts
but cannot invent independent compatibility or migration policy.

**Alternatives considered**:

- Reject every internal format/version transition: rejected because it reproduces the old blanket
  contract restriction.
- Remove compatibility gating entirely: rejected because changes to supported project versions,
  public persisted formats, or user upgrade commitments are durable product policy.

## Decision: Preserve constitutional human review for architecture-source edits

**Rationale**: Constitution A.V requires exact human review for AI-authored architecture changes.
Fast-loop may author contract or maintained-diagram changes and validate them directly, but the
result remains `review_pending` until the maintainer confirms the displayed diff. This is a narrow
architecture review, not an implementation-acceptance proposal, and creates no attempt artifact.

**Alternatives considered**:

- Treat command invocation as review of a future unknown diff: rejected because authorization to edit
  is not review of the resulting architecture intent.
- Send all contract changes back to normal acceptance: rejected because it preserves the blanket
  ineligibility the new policy removes.

## Decision: Keep Python workspace and packaging behavior stable

**Rationale**: The eligibility decision lives in the canonical agent-followed command. Existing
workspace, release, and self-host scripts do not encode the former one-feature/contract policy. They
already resolve arbitrary explicit feature roots and materialize canonical command Markdown. The
implementation therefore changes instruction surfaces and their contract tests, then exercises the
unchanged scripts through workspace, package, and self-host validation.

**Alternatives considered**:

- Introduce a deterministic impact-discovery runtime: rejected because semantic feature impact cannot
  be derived reliably from paths alone and would duplicate the coding agent.
- Change Protocol v8 only to satisfy wording: rejected because an unused protocol field would add
  compatibility cost without enabling behavior.

## Decision: Reconcile architecture contracts and diagrams without changing topology

**Rationale**: Parent and project workflow contracts currently describe durable writes and normal
phase ownership without the relaxed fast-loop exception. Their diagrams also describe one selected
root as a universal isolation boundary. Updating wording and authority cards makes the new direct
path visible while preserving every component and dependency. The exact architecture-source changes
receive maintainer review and deterministic Archify validation.

**Alternatives considered**:

- Update only the command and public docs: rejected because durable architecture sources would retain
  contradictory authority rules.
- Add new multi-feature runtime components or diagram nodes: rejected because repeated use of the
  existing adapter realizes the policy without a new component.
