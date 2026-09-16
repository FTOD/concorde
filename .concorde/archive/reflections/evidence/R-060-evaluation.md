# R-060 implementation and evaluation

Date: 2026-09-07. Candidate: `change.599d4ebe-7c52-4a3e-b130-4deb96fd0964`, branch
`design/domain-scopes-and-spec-contexts`, in `/tmp/concorde-domain-scopes-edit`.
The work remains an uncommitted maintenance candidate until primary-session delivery.

## Implemented behavior

- Public `concorde-review` has independent Spec and code modes, separate fresh sessions, complete
  admitted Spec collections, scoped changes, typed findings/gaps and version-bound run artifacts.
  Spec review cannot read implementation; code review receives only enumerated registered files.
  Both reviewers have no host-project write authority and no network authority.
- Standard loops review the Spec before planning, and code after checks but before ready. Fast loops
  explicitly record skips, preserve stronger prior requirements and propagate upgrades to completed
  Domain components. Unrelated review queries cannot substitute for accepted authoring or overwrite
  required lifecycle evidence.
- Necessary task gaps pause dependent work, persist and deduplicate in existing change history,
  retain target/context provenance and resolve after successful host acceptance of repaired work.
  Rejected outputs, failed plan persistence and failed delivery preserve recoverable blockers.
  Reflection status exposes stable gap IDs; explicit `record-gaps` links selected gaps to the existing
  queue without treating a pure question as a mutation.
- Confirmed executor, registry, publication and workflow-host contracts are supplied locally or in
  explicitly registered Shared Specs. Native Codex startup and exact-file read grants work under
  default denial. Publication checks the materialization identity before plugin loading and after
  building, rejecting source changes that would otherwise certify old pages with a new digest.

## Real reviewer observations

These are native Codex runs, separate from the process doubles used by deterministic tests.
Each retained report includes exact input digests, target/context identities, coverage, findings,
native receipts and completion gates. Earlier iterations are historical evidence, not current gates.

| Case | Observed result | Interpretation |
| --- | --- | --- |
| Four original R-060 target collections | All four reported the recorded necessary contract omissions | 4/4 known target-level gap groups detected; no observed miss among these four groups |
| Final repaired target collections | All four same representative task requests accepted on the final runtime and Spec inputs | Coverage-specific acceptance; exact reports and native receipts are retained |
| Deliberately defective transfer implementation | Both missing subtraction and missing invalid-transfer rejection reported | Two seeded behavior defects detected |
| Correct transfer implementation | No findings or gaps | No false positive observed in this one normal code case |
| Actual workflow-host change, first code review | Three lifecycle defects reported | Each reproduced by a failing regression and repaired |
| Actual workflow-host change, second code review | Two additional failure-recovery defects reported | Each reproduced by a failing regression and repaired |
| Actual workflow-host change, third code review | Failed-preview persistence and a standalone dependent-step bypass reported | Both reproduced and repaired; the dependent-step regression covers tasks, implementation, checklist and issue drafts |
| Actual workflow-host change, fourth code review | Rejected checklist artifacts could resolve a prior gap | Reproduced and repaired; a local audit also reproduced and repaired the equivalent reflection-investigation path |
| Actual workflow-host change, fifth code review | Standalone dependents could reuse old tasks across an unresolved upstream planning gap | Reproduced for assessment and planning gaps; admission now checks prerequisites while allowing independent queries |
| Actual workflow-host change, sixth code review | Failed reviews discarded available native attestation | Reproduced and repaired; failure records privately retain exception receipts or returned execution results |
| Final actual workflow-host code review | No findings or gaps for the covered paths | Uses current source, tests and Spec inputs; static review did not execute checks |

Follow-up Spec review also found incomplete schema error semantics, publication preconditions,
undiscoverable gap identifiers and the preparation/plugin identity gap. The corresponding contracts
and implementation were repaired rather than dismissing concrete findings to obtain a clean result.
The host reviews used different implementation revisions. Delivery clearing visible gaps,
failed-preview persistence, the standalone task-review bypass, rejected-checklist gap resolution and
upstream-gap bypass and lost failure attestation were present but unreported in the first review:
these are six observed misses among subsequently
confirmed defects. The reflection-investigation source is outside this host review's grant, so its
locally discovered counterpart is not counted as a reviewer miss.
The stranded-plan-gap trigger was evaluated after gap acceptance changed, so it is a follow-up
finding rather than a measured baseline miss. No general false-negative rate is estimated.

- [Original known-gap Spec runs](R-060-baseline-reviews.json)
- [Additional contract review observations](R-060-contract-followups.json)
- [Known-defect and normal code runs](R-060-code-cases.json)
- [First actual-host code review](R-060-host-code-initial.json)
- [Second actual-host code review](R-060-host-code-followup.json)
- [Third actual-host code review](R-060-host-code-boundaries.json)
- [Fourth actual-host code review](R-060-host-code-checklist.json)
- [Fifth actual-host code review](R-060-host-code-prerequisites.json)
- [Sixth actual-host code review](R-060-host-code-receipts.json)
- [Final repaired Spec reviews](R-060-spec-accepted.json)
- [Final actual-host code review](R-060-host-code-accepted.json)

## Verification and limits

Mechanism tests cover scope isolation, positive/negative native reads, host-file write protection,
network denial, fresh sessions, malformed/replayed output, input drift, explicit skips, required
review failure, gap ownership/persistence/deduplication, repair/resumption and Domain aggregation.
Failure-injection regressions verify host acceptance and recovery, including rejected authoring,
plans/tasks/completion, failed plan-file writes and refused delivery in disposable Git fixtures.

The native Linux sandbox may create disposable files in its private directory scaffolding; tests
also verify that those files never appear in the actual host project. The real host files remain
unchanged. The native runtime evaluated here is `codex-cli 0.153.4`. Claude configuration rendering
has deterministic test coverage, but no real Claude reviewer was evaluated. The evaluation did not
independently pin an exact model, and these few cases do not establish a statistical reliability rate.
Model success and deterministic validation both retain `semantic_completeness=not_proven`.

R-060 retains its original feature `feature.concorde.evolve-protocol`, which belongs to
`domain.concorde`; its concerns path is evidence, not ownership. Triage is complete and the original
record remains open in `planned/` until delivery. Its original context, observations and occurrence
history are preserved. Delivery belongs to a new agent opened in `/home/zhenyu/concorde`, as required
by this secondary worktree's AGENTS policy.

## Final verification

- All **474 Python tests passed**, with no skips. This includes the installed Linux native sandbox
  boundary test and the recovery regressions. [Full suite output](R-060-python-tests.log).
- All **119 docsite tests passed** across 26 files, including actual production build and promoted
  manifest/graph checks. TypeScript checking and docsite registry validation also passed.
  [Docsite suite output](R-060-docsite-tests.log).
- All three configured candidate checks passed: context runtime, workflow runtime and publication
  types. Structural self-validation found no findings; generated agent surfaces are current
  (50 outputs), and `git diff --check` passed.
- The final four Spec reports and actual-host code report all have no findings/gaps. The host
  separately verified their current input identities and artifact integrity before finalization.

[Verification identities and checks](R-060-verification.json) and the
[implemented resolution plan](R-060-resolution-plan.md) are retained with this report. This is the
existing direct-maintenance candidate path; loop gates were also exercised through the deterministic
workflow tests. No commit, merge, deployment or real-project delivery was performed here. The
worktree lifecycle records readiness only after verifying the final candidate containing this evidence.
