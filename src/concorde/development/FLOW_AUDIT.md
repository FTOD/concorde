# Development Flow audit

## Scoped-review scheduler freshness repair

Invocation: 354d5a66-bea7-4277-a4e6-be6542dcd78a.
Context: sha256:a6ca6d1adbbaee882c8ae3d79014b175351baba19eb52d70aec53e9a08d3fce0.
Review input identity now additionally binds coordination_flow.py, loop_flow.py and
specify_flow.py as Framework runtime sources. These executing factories schedule
component finalization, development review and specification review respectively.
The existing runtime inputs remain bound; lifecycle-only observations are unchanged.

test_scope_scheduler_change_invalidates_accepted_review independently varies each
of these three sources and review.py through the runtime byte reader for both Spec
and code review of a consumer that does not bind those files. It asserts changed
input identity with unchanged consumer revision and patches, rejection of accepted
evidence (including the required-review gate), and reuse of the preserved artifact
when unchanged runtime bytes are restored. This is a controlled byte-observation
regression, not an execution of modified scheduler code or a package-build check.
It supersedes the narrower scheduler-freshness coverage noted in the prior audit.

Attempted once:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.concorde.development.test_review.ReviewTests.test_scope_scheduler_change_invalidates_accepted_review
```

Import failed because concorde.spec.typed_data is unavailable under the programmer
grant, reached through change_worktree.py. No behavioral test ran; execution is
deferred to Host, not passed. A separate `PYTHONDONTWRITEBYTECODE=1 python3 -`
command using ast.parse and compile passed for review.py and test_review.py without
project imports or bytecode writes. No scheduler topology, interruption handling,
generated output or lifecycle state was changed. Host checks and independent review
remain pending; the earlier audit below retains its own provenance and limits.

## Fresh implementation recheck

Invocation: 2e9d8ea9-4519-48c4-93a9-39c95294eff7.
Context: sha256:10d256868f30a3a43214e3823b03997b92a26c9aabba364a05b6946a5f933ec8.
The current admitted implementation already contains the interruption propagation,
nine-case composition regression and local-review eligibility regression described below.
Source inspection confirmed their assertions and the executable discovery, scoped-review,
coordination and stabilization call sites. No additional omission or necessary runtime
repair was demonstrated. Existing implementation and test bytes were preserved.

The exact unittest command recorded below was attempted once in this invocation.
All three selected modules failed import because `concorde.spec.typed_data` is unavailable
under the grant; no behavioral tests ran. Host execution remains deferred, not passed.
Using `PYTHONDONTWRITEBYTECODE=1 python3 -`, `ast.parse` followed by `compile` passed
for the eleven exact Python files listed below plus `test_specify_loop.py` (twelve total),
without project imports or bytecode writes. This establishes syntax only.
The remaining sections retain the earlier audit's provenance and bounded conclusions;
their historical execution claims are not substituted for current Host evidence.

Invocation: 2d7e1816-4b95-4542-bcff-93103d944c3f. Module: module.development.
Context: sha256:f6349db78e778c521ff6450aadc57b8a6a4620d7ed09451b1c22ef3507e51e5a.
This replaces historical audit claims with the current bounded source assessment.
It is implementation evidence, not Host validation or independent review.

## Executing topology

| Supported path | Executing and inspectable surface | Selection, continuation and stop |
| --- | --- | --- |
| Capability admission | capability_flow.build_capability_flow and dispatch_flow.build_dispatch_flow | Capability-specific variants select actual child instances. Failed admission goes to finalize; expose_stateless_subflow exposes the same executing instance for xray inspection. |
| Discovery | target_flow.build_target_flow(discover=True/False), discovery_flow.build_discovery_flow; MainInvocation.discovery_nodes/discover_routes | initialize_target selects saved binding or discovery. decide selects expand_context, bind_routes, finish or END. Expansion returns to decide only without a stopping result. The caller budgets 2 * (target count + 1) + 3 scheduler steps; the decision node enforces the domain bound. Main question/design uses the separate query Flow. |
| Scoped local/component review | review.review_scope calls run_batch_flow named scope_review_flow, item review_module | The first item selects local review: always for Spec or a code-owning target; component records do not replace local code review. Later items select admitted recorded components/Spec consumers/shared implementation users. Non-code peers skip code review. First unsuccessful output stops the batch. This is a separately bound executable batch instance, not evidence of missing topology merely because public review is a callback. |
| Component writers | coordination_flow.build_coordination_flow, Invocation coordination nodes | reconcile_specs -> validate_specs -> implement_components -> implement_local -> finalize_components -> record_completion. Each intermediate node can stop. Host defer_component_checks and finalize_components select the applicable work; caller task JSON does not supply them. Component iterations use executable batch instances. |
| Final shared-consumer checks | coordination_flow.build_stabilization_flow and component_finalization_flow batch | snapshot -> verify_components -> check_stability; failure stops before stability, changed implementation returns to snapshot, stable revisions end. Runtime limit is 1 + 2 * participant count, scheduling allowance 3 * limit + 3; exhaustion rejects nonconvergence without restart. |
| Specification/development stops | specify_flow.build_specify_flow and loop_flow.build_loop_flow(dynamic=True) | Current authoring/review admission selects work. Development exposes resume destinations and review_code -> tasks repair. Failed Review domain output stops; trusted cancellation/exhaustion remains in shared host lifecycle and final events. |

No omitted topology was demonstrated within these inspected Development surfaces.
Separate executable factories/instances satisfy the audit boundary; no duplicate graph or
scheduler is added. Internal factories compile with checkpointer=False. Runtime callbacks
and host objects remain ephemeral. The public JSON checkpoint boundary and actual viewer
projection belong to separate Harness/Views implementations, which were not inspected here.
Atomic delivery remains outside this repair and may remain one deterministic node.

## Interruption and preservation evidence

Retained review.py consumes CapabilityExecutionError.outcome, saves cancelled,
limit_exhausted or failed, and returns incomplete Review evidence with failed domain outcome.
It retains private failure diagnostics and reports state_persistence_failed on a failed
progress write. specify_flow and capability_host loop stopping preserve interruption status;
capability finalization uses existing execution_cancelled/execution_limit errors and event
status without changing public schemas. Root entry starts fresh lifecycle observations.
Only conflicting code findings select repair; failed Review output cannot select that edge.
No additional runtime change was needed.

The nine-case test_reviewer_interruptions_survive_enclosing_flows_and_final_events now
separately captures actual Review domain outputs, checks candidate implementation and Spec
bytes at interruption, and asserts the final started Flow stage. It retains assertions for
incomplete stored reports, enclosing status/events, accepted target progress, requirements,
gap history, unrelated edits and no automatic repair. The matrix covers three review entry
paths times cancelled/limit_exhausted/failed. It declares only flow-execution: it injects
trusted executor errors and does not exercise Harness's conversion of native process failures,
so claiming scenario.harness.execute-failure would overstate this test. Successful-ready and
recursive-delegation declarations are absent from the interruption-only matrix.

A new Flow-surface regression exercises local code review both with and without recorded
component work. Existing preservation tests retain sticky requirements, exact intent and
revision currentness, accepted authoring/current review reuse, blocking-then-clean repair,
unchanged-feedback waiting, repair-limit exhaustion and direct edit repair-count reset.
Relevant sources are test_review.py and test_specify_loop.py; these are test assertions,
not passing execution evidence in this invocation.

Existing test_flow_surfaces.py relates inspected edges to visited execution paths, checks
inspection precedes node execution, repeats get_graph, and asserts stateless compilation.
It exercises 36 discovery decisions, domain-limit rejection before a decision, coordination
stops at each intermediate node, two independent 30-round stabilization instances and scoped
review failures over 40 peers. These collaborator tests do not prove native isolation.
The retained scheduler freshness regression checks review identity invalidation on changed
review.py bytes. No unrelated scenario declarations were changed.

## Current verification and limits

Attempted command:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.concorde.development.test_review tests.concorde.development.test_flow_surfaces tests.concorde.development.test_specify_loop
```

All three modules failed to import: concorde.spec.typed_data is unavailable under this grant.
No behavioral test executed. Full suite execution, including the newly added local-review
case, is deferred to Host. No dependency replacement, broader read or unchanged-input retry
was attempted. Other test fixtures and runtime dependencies remain Host inputs.

A syntax-only check uses Python ast.parse and compile on the exact eleven files named below,
without project imports or bytecode writes: development review.py, capability_host.py,
capability_flow.py, dispatch_flow.py, discovery_flow.py, target_flow.py, coordination_flow.py,
loop_flow.py, specify_flow.py; tests test_review.py and test_flow_surfaces.py.
All eleven files passed that syntax check; it establishes syntax only.
Host configured checks and separate current reviews for affected listing Modules remain
mandatory. No build, protected authoring, generated output, lifecycle-state mutation,
commit, delivery, cleanup or primary merge was performed by this invocation.
