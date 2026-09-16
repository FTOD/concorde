---
id: "R-060"
title: "Profile 8 self Specs do not supply their registered Module interfaces"
route: "specify"
status: implemented
recorded_under: "feature.concorde.evolve-protocol"
implement_in: "specs/concorde/system.md"
implement_in_id: "feature.concorde.evolve-protocol"
touches_docsite: true
effort: "large"
files: ["protocol/principles.md", "protocol/schemas.json", "src/concorde/capabilities/review.py", "src/concorde/capabilities/scoped_operations.py", "src/concorde/capabilities/change_worktree.py", "src/concorde/capabilities/worktree_delivery.py", "src/concorde/capabilities/operation_executor.py", "src/concorde/capabilities/operation_permissions.py", "src/concorde/capabilities/protocol_contracts.py", "src/concorde/specification/context.py", "src/concorde/reflections/scoped_triage.py", "operations/concorde-review/SKILL.md", "operations/concorde-review/operation.py", "skills/concorde-spec-reviewer/SKILL.md", "skills/concorde-code-reviewer/SKILL.md", "specs/concorde/modules/agent-execution.md", "specs/concorde/modules/registry.md", "specs/concorde/modules/spec-publication.md", "specs/concorde/services/operation-boundary.md", "specs/concorde/services/operation-wire.md", "specs/concorde/shared/agent-runtime-contracts.md", "specs/concorde/shared/registry-contracts.md", "docsite/plugins/scoped-content/index.ts", "docsite/plugins/scoped-content/materialize.ts", "docsite/tests/scoped-registry.test.ts", "tests/concorde/specification/test_review.py", "tests/concorde/capabilities/unit/test_operation_permissions.py"]
verified: "2026-09-07"
verified_commit: "d63af7f37d21b9988d72591fbdc381713455786c"
branch: design/domain-scopes-and-spec-contexts
worktree: /tmp/concorde-domain-scopes-edit
---

## Problem

Verified in the maintained candidate on 2026-09-07. The original feature remains
`feature.concorde.evolve-protocol`, now an owned Feature focus of `domain.concorde`; it is not a
standalone target. Public reflections-triage status succeeds with that Domain target and focus.
The concerns path identifies evidence, not ownership, so the feature and original observation are
preserved. This is an explicitly approved Protocol maintenance change, coordinated across the
actual targets `module.agent-execution`, `module.registry`, `module.spec-publication` and
`service.workflow-host`. Ordinary single-component reflection investigation cannot represent this
cross-target Protocol cutover.

Four real, independent Spec-only reviewer sessions reproduced the four reported target-level
omissions before the contract repairs. Their typed reports, exact input digests and native execution
receipts are retained in `.concorde/reflections/evidence/R-060-baseline-reviews.json`.
Executor construction/call/result/error definitions, Registry methods and returned records,
TypeScript publication interfaces, and the host's required collaborator promises were confirmed
against their owning implementation and restored locally or in explicitly registered Shared Specs.
Follow-up review also exposed a schema-subset/error omission, malformed publication preconditions,
undiscoverable durable gap identifiers and a preparation/plugin source-identity gap; these were
repaired with their relevant tests. The source-identity defect could certify a newer digest over
older generated pages when sources changed between preparation and plugin loading.

Deterministic validation remains structural. Model process doubles verify lifecycle mechanics;
real reviewer evidence evaluates representative task effectiveness without proving completeness.

## Verification

The verified_commit field records the unchanged Git HEAD at investigation time.
This is an uncommitted candidate: actual reviewed input bytes are identified by the Spec/code/input
digests in the retained real-review reports, not by HEAD alone. All four original target-level
omissions reproduced in native Spec-only runs; follow-up sessions on the repaired collections
reported no findings for the same representative tasks. See the evidence directory for exact
coverage, findings, receipts and evaluation limits.

## Change

1. Restore native default-deny execution and verify positive/negative read boundaries.
2. Implement and register independent review modes, roles, typed results and input freshness.
3. Integrate required/optional review in existing loops and necessary gaps in task lifecycle/resume.
4. Add explicit gap capture through existing Reflection ownership/allocation/deduplication.
5. Repair the four confirmed self-Spec collections and publication version continuity.
6. Verify failure recovery: accept artifacts before recording completed work, preserve open gaps
   after rejected output/persistence or delivery, and propagate review upgrades to completed components.
7. Synchronize canonical projections, run deterministic checks and real reviewer evaluations,
   retain their evidence and hand off the verified candidate for primary-session delivery.

## Validation

Run the complete Python suite, focused review/lifecycle/permission tests including
the installed Linux native sandbox, docsite typecheck and all tests including production build,
self-Spec deterministic validation, git diff --check and agent-surface apply/check. Evaluate real
Spec reviewers on known omissions and repaired collections; evaluate code reviewers on a known
transfer defect and a correct implementation, and inspect the actual workflow-host change. A model
run failure is incomplete evidence, not a clean result. Record observations and limits rather than
turning model detections into mandatory deterministic CI assertions.

## Risks and out of scope

No review proves semantic completeness or assesses unadmitted targets. Real runtime
boundary/effectiveness evidence is for the installed Linux Codex runtime; Claude rendering has
deterministic coverage but was not empirically evaluated here. Input changes invalidate prior
evidence. This maintenance does not merge, deploy or remove the managed change worktree.
