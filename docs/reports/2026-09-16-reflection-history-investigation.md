# Legacy Reflection reinvestigation — 2026-09-16

## Scope and authority

The developer requested a fresh, one-by-one investigation of preserved Reflection history and
registration of still-applicable problems using the new Issue system. This is direct maintenance
in `/home/zhenyu/concorde`, branch `main`, investigated at
`4b4fb0fce4435f163fa640b262e14c153952b33a`. No retired Reflection flow, Issue solve flow,
model worker, delegated reviewer or production repair was launched.

The archive contains **four remaining Reflection records, R-071 through R-074**, plus evidence
from earlier completed work. Its `high_water: R-074` is an allocator marker, not 74 retained open
records. This investigation covers each retained record and its separate follow-ups. It also
checks the applicability of the substantive R-060 and R-066–R-070 problems described in the
retained resolution evidence. It does **not** claim to reconstruct every deleted R-001–R-070
record from Git history or rerun their original model-based evaluations.

All historical archive bytes are unchanged. An archived `status: open` is a historical fact,
not the status of the new queue. No old record was silently closed, reclassified or approved.
The current Issue collection was empty before this investigation.

## Disposition summary

| Historical item | Current finding | New registration |
| --- | --- | --- |
| R-071 original unbound-resume KeyError | Repaired; persisted owner state, not request change_id alone, selects routing | None |
| R-071/F1 topology recovery | Still a capability limitation for non-entry development owners; safe refusal, not owner overwrite | [I-81d4173fa1595f1a871e7605c389a77c](../../.concorde/issues/I-81d4173fa1595f1a871e7605c389a77c.md), limitation, `module.dev-loop` |
| R-071/F2 hidden path semantics | Explicit-root precedence is still not stated clearly enough; current behavior reproduced | [I-d2d72e8022785dc7b150ebf0a1602263](../../.concorde/issues/I-d2d72e8022785dc7b150ebf0a1602263.md), gap/missing-contract, `module.spec` |
| R-071/F3 routing and classification diagnostics | Host now retains single-target intent and diagnoses changed route fields; remaining broad diagnostic suggestions lack a separate established defect | None |
| R-072 finding/gap string equality | Retired by immutable Issue receipts and host-derived blockers; accepted reports also survive final-result failure | None |
| R-073 foreign and stranded task-text gaps | Replaced by Module/work-scope/phase/Issue relations; isolation and cross-coordinator reassessment reproduced | None |
| R-074 impossible provider acceptance | Partially improved guidance; semantic dispatch limitation remains, with narrower current claim | [I-61c12e3efc4655a29315033898bbc807](../../.concorde/issues/I-61c12e3efc4655a29315033898bbc807.md), limitation, `module.planning` |

These are **three distinct open Issues**, not four copied Reflections and not approved repair
plans. Current Module ownership replaces the old catch-all `module.development` attribution where
appropriate. Shared implementation realization still requires separate affected-Module checks if
and when a repair is authorized.

## R-071 — investigate each part separately

Historical source: [R-071](../../.concorde/archive/reflections/pending/R-071.md).

### Original resume failure: no new Issue

`capability_host._dispatch_nodes.initialize_target` now calls `resume_owner`, restores a bound
owner only when present and otherwise enters discovery. `bind_target` binds the discovered owner.
`change_worktree.bind_owner` validates missing fields with a structured error rather than a direct
missing-key access. This matches the current Development Flow failure/recovery contract.

The current `WorktreeLifecycleTests.test_public_handoff_resumes_unbound_candidate_with_fresh_host`
checks all four specify/review combinations through the public host, from unbound handoff to ready.
The neighboring bound-resume, hints/intent and malformed-state tests also passed in the full suite.
Those tests use fixture process doubles; they do not establish real-model routing quality.

### F1: register an owner-preserving topology recovery limitation

Ordinary authoring preserves registration, so a required listing/reference/ownership change still
needs Topology. Development Flow explicitly has no topology-repair transition. The new Issue solver
adds ordinary owner-only Spec repair, not a topology reconciliation path.

`_topology_apply_nodes.apply_atomically` chooses `design.registry.entry_target` as the application
owner and refuses an existing different owner. The current probe binds a `module.ledger` candidate,
uses identical task intent to design and prepare a simple title-only topology application, then
applies it. It receives `incompatible_handoff: topology application differs from this worktree's
owning task`; the original owner and registry bytes remain intact. No missing-contract theory or
invented target is needed to observe the limitation.

Thus the old unsafe-drop-in concern has a **safe guard**, but not an owner-preserving recovery path.
Register this as a limitation, not a regression, data-loss bug or permission to weaken the guard.
Any future design must retain explicit acceptance, original intent and affected-evidence invalidation.

### F2: register the unresolved explicit-root contract

Current `repository_base.expand_entry` and `bound_by` consistently distinguish explicit roots
from descendants. The probe confirms:

- Exact `.github/workflows/check.yml` is included.
- Explicit `.github/` and `.github/workflows/` roots include the workflow.
- Recursive `source/` excludes `source/.hidden.py`.
- Exact `source/.hidden.py` is included.

P5 in `prompts/protocol/framework-profile.md` broadly names dot-prefixed exclusions. The registry
contract and `scenario.spec.directory-entry` describe recursive expansion but do not explicitly
state precedence for exact hidden files or hidden components of a declared directory root.
The needed clarification is about that boundary, not a blanket claim that all hidden files must
be excluded. Register gap/missing-contract; do not choose a new inclusion policy in this investigation.

### F3: no separate established defect

For non-main single-target routing, `MainInvocation.discovery_nodes.bind_routes` permits omitted
intent fields, derives task/constraints from the host's original request, and reports exact
`routes[index].task` / `.constraints` mismatches if supplied values differ. The process-double
fixture actually omits those fields, and the full-suite route and resume tests pass. Thus the
concrete host-retained-intent suggestion is implemented.

The current Development Flow contract distinguishes unsupported prohibitions, conflicting
contracts, invalid runtime inputs and execution failures; the new Issue classification further
separates bugs, gaps and limitations. The remaining request for richer unbound/excluded-path
recovery guidance is a broad improvement suggestion, not fresh evidence of an additional failure.
F1 and F2 preserve its concrete actionable parts without duplicating them.

## R-072 — text equality replaced, not merely better explained

Historical source: [R-072](../../.concorde/archive/reflections/pending/R-072.md).

`spec.issue_shapes.REVIEW_ISSUE` contains an immutable receipt, severity and affected task.
`issues.references.validate_references` validates admitted identities;
`review_blockers` derives `blocked_step` from the judgment. `development.review._validate` no longer
joins free-text `contract` / `needed_contract` or `affected_task` / gap prose.

The current probe reports an Issue with independent description, basis and impact wording, then
submits a blocking review judgment with a differently worded affected task. The review is admitted
as `findings` and returns `spec_incomplete` with a host-derived blocker and a persisted open Issue.
The new reporting tests also verify that acknowledged observations survive invalid completion,
cancellation and limit exhaustion. The original two-string pairing failure is therefore obsolete;
no replacement Issue is warranted. A failed review still does not count as completed review coverage.

## R-073 — stable relations and bounded snapshots

Historical source: [R-073](../../.concorde/archive/reflections/pending/R-073.md).

The old `gap_history` content model and Reflection capture path have been removed.
`record_task_gaps` retains its legacy Python name but now stores reference-only `issue_blockers`.
The identity hashes change, Module, accepted work scope, phase and Issue—not task prose.
`blocker_scope` maps accepted component intents from different coordinators to the same Module
scope; unrelated independent work remains separate. `workspace_context` filters by Module and scope.

The current probe records one provider Issue under one coordinator, changes the accepted task text,
adds an equivalent nested coordinator intent, and reports the same Issue through that layer. It
observes **one stable relation**, no foreign blocker in the root's snapshot, and successful release
after fresh input and successful reassessment. The Issue itself stays open, as intended. This is
not the old stranded-gap defect: releasing a task dependency and disposing a problem are now
explicitly different operations.

Full-suite coverage also includes Issue blocker-history/scope tests and review tests for unrelated
assessment, stale identity and unsuccessful completion. No new Issue is registered. Historical
`/tmp` paths were not treated as available or current evidence.

## R-074 — acknowledge improvements, retain only the current limitation

Historical source: [R-074](../../.concorde/archive/reflections/pending/R-074.md).

The old task-mode file is gone. `agents/task_author/spec.md` now restricts acceptance to implementation
evidence in the programmer's grant and excludes host checks, independent reviews, readiness and
delivery as preconditions. Explicit task-scope recovery also exists. The original claim that no
phase-boundary guidance exists must not be repeated.

The remaining boundary is **which Module can perform the requested verification**. The coordinator
may name a declared provider, and `implement_scope` checks that relationship, but `_component_intent`
then forwards arbitrary description/acceptance text into that provider's own invocation. The probe
injects a task asking the transfer provider to inspect Banking's `scenario.bank.settlement`
declaration. The provider is dispatched with only its own registered Spec pairs; the consumer Spec
is not granted. The double then correctly reports `spec_incomplete`, before implementation.

This establishes a current semantic-admission limitation while confirming isolation works. It does
**not** establish how often real models generate such tasks, prove the old three incidents recur,
or justify widening the provider grant. Register as limitation, not an unqualified implementation
bug. Potential future work can allocate consumer agreement verification explicitly and detect
unsatisfiable component acceptance before dispatch. Foreign IDs alone are insufficient grounds for
rejection: an explicitly referenced complete consumer unit can legitimately be present.

## Earlier retained resolution evidence

These entries are not open Reflection records in this checkout. Their archived resolutions were
checked against the present mechanisms and deterministic coverage; old passing model reviews were
not promoted to current verification evidence.

| Item | Current applicability check | Registration decision |
| --- | --- | --- |
| R-060 independent review/task gaps | `development.review` still enforces separate Spec/code review contexts and freshness; current review lifecycle, failure retention and prerequisite tests pass. The Reflection capture part is intentionally superseded by immediate Issue reporting. | Do not recreate the completed change or its retired capture API. Historical semantic review effectiveness was not reevaluated. |
| R-066 ignored narrowed role effects | Current worker/permission binding and `test_narrowed_implementation_worker_write_authority_is_never_widened` retain narrowing. | No current reproduction; no new Issue. |
| R-067 missing per-Agent definitions | Twelve current workers have `agents/<name>/spec.md` plus validated Python profiles; `test_resolve_agent_succeeds_for_every_inventory_worker` checks the complete inventory. | Obsolete old nine-role architecture claim. |
| R-068 absent Harness composition | Current Agent binding identifies the worker profile, contract, workspace, tools, timeout and instruction digests; profile validation rejects widening. | Superseded by the current Pi worker model, not a missing old Harness catalog. |
| R-069 no code-review repair loop | `loop_flow.loop_destinations` includes `review_code -> tasks`; `RepairLoopTests` cover successful repair, unchanged feedback and the declared bound. | No new Issue; broader topology recovery is separately retained as F1. |
| R-070 unbounded/unclassified execution | Worker definitions and executor bind configured timeout; cancellation and exhaustion remain distinct in the tested host lifecycle. | No new Issue; retired Codex/Claude native CLI details are not the current contract. |

The unnumbered 2026-09-09 delivery log is an execution record, not another active Reflection. Its
`npm ci` symlink incident no longer describes `check-docsite-types.py`: preparation now uses an
external temporary copy and chooses either reuse by symlink **or** installation, not installation
through that reuse link. Its old diagram-preview observation was not independently reproduced and
is not promoted into an Issue. Bare mentions of R-055/R-061/R-062/R-063 in an old plan do not supply
complete retained records and are not represented as newly investigated open problems.

## Registration and evidence

- [Reproducible probes](2026-09-16-reflection-history-probes.py): disposable fixture projects;
  no model calls, linked worktree creation or production code changes.
- [Probe output](2026-09-16-reflection-history-probes.json): baseline, source digests, selected
  contract-context digests and explicit observations for all five probes.
- [Registration receipts](2026-09-16-reflection-history-registration.json): immutable Issue/report
  references, current revisions, known owners and direct-maintenance provenance.
- [Verification summary](2026-09-16-reflection-history-verification.json).

Registration used the existing `IssueReporter`/store API under the developer's outer maintenance
authority, with only the explicitly investigated owners/evidence paths. Provenance says
`direct-maintenance`, not a fictitious Concorde worker or solve invocation; `change_id` is null.
Each identical report was retried once and returned the same receipt/revision. All three records
remain open with no disposition. This bookkeeping does not create candidate readiness, authorize
implementation, launch repair, merge another branch or claim a problem fixed elsewhere.

## Checks and limitations

- `python3 scripts/concorde.py build --check`: passed before registration and at final verification.
- `python3 scripts/concorde.py validate`: passed before and after registration; final validation
  includes the new Issue bytes, with zero findings.
- Full Python suite: **848 tests, OK, 10 skipped**, 794.452 seconds. No production source was changed.
- The initial broad targeted test command hit its 300-second tool deadline; it is **not** counted as
  a successful test run. The subsequent complete suite is the cited result.
- Two initial probe runs exposed incomplete hand-authored fixture lifecycle state, not product
  regressions. After correcting the fixture owner and coordination status fields, all five final
  probes passed. The committed JSON contains only that complete successful run.
- Active Python LSP diagnostics and final whitespace/integrity checks passed. JSON records are
  validated through the Issue store and repository validator, not an assumed editor diagnostic.
- No live-model reproduction, independent model review, docsite UI test or production repair was
  performed. Deterministic passing checks do not establish semantic completeness.
