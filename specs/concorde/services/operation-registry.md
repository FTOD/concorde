```concorde-document
{
  "id": "document.operation.registry",
  "targets": ["domain.workflow", "service.workflow-host"],
  "main_visible": true
}
```

# Project Operation registry

Every Operation below has a paired executable. Configuration and runtime input are separate JSON
TypedValues. Global and lifecycle Operations are projected as public Skills; internal stage
Operations are not projected and are reachable only through a composing public Operation — see
Operation classes below. Internal roles under `skills/` have no direct public invocation.

| Operation | Request type @1 | Response type @1 | Role or child Operations | Behavior |
| --- | --- | --- | --- | --- |
| concorde-configure | concorde-configure-request | concorde-configure-response | Deterministic host | Apply initialized operation configuration |
| concorde-context-solve | concorde-context-solve-request | concorde-context-solve-response | concorde-context-assessor | Validate Domain participant routing, then assess information sufficiency without expanding worker context |
| concorde-deliver | concorde-deliver-request | concorde-deliver-response | Deterministic host | From a primary agent session, verify, merge and clean up the selected change worktree |
| concorde-fast-loop | concorde-fast-loop-request | concorde-fast-loop-response | concorde-coordinator, concorde-review, concorde-plan, concorde-tasks, concorde-implement, concorde-validate | Route, optionally review Spec, plan, tasks, implement, validate, optionally review code, then ready; skips are explicit |
| concorde-implement | concorde-implement-request | concorde-implement-response | concorde-implementation-worker | Implement component tasks or coordinate participating components |
| concorde-init | concorde-init-request | concorde-init-response | Deterministic host | Propose/apply explicit project initialization |
| concorde-main | concorde-main-request | concorde-main-response | concorde-coordinator, concorde-reader, concorde-spec-author | Answer through fresh readers or design, prepare and atomically apply an explicitly accepted topology |
| concorde-plan | concorde-plan-request | concorde-plan-response | concorde-context-assessor, concorde-planner | Assess sufficiency, then create revision-bound plan |
| concorde-reflections-triage | concorde-reflections-triage-request | concorde-reflections-triage-response | concorde-implementation-worker, concorde-standard-dev-loop | Select/status, explicitly record existing gaps, investigate/implement/dispose owned reflections |
| concorde-review | concorde-review-request | concorde-review-response | concorde-spec-reviewer, concorde-code-reviewer | Independently review a complete Spec or its registered code read-only; retain version-bound findings and gaps |
| concorde-specify | concorde-specify-request | concorde-specify-response | concorde-spec-author | Author the bound target's Spec replacements |
| concorde-standard-dev-loop | concorde-standard-dev-loop-request | concorde-standard-dev-loop-response | concorde-coordinator, concorde-specify, concorde-review, concorde-plan, concorde-tasks, concorde-implement, concorde-validate | Route, specify, review Spec, plan, tasks, implement, validate, review code, then ready |
| concorde-tasks | concorde-tasks-request | concorde-tasks-response | concorde-task-author | Author acceptance tasks from the accepted plan |
| concorde-validate | concorde-validate-request | concorde-validate-response | Deterministic host | Run deterministic Spec and configured code checks |

## Operation classes

Every Operation belongs to exactly one class, distinguished by who selects its context:

- **Global** — receives only the caller's intent, at most with target/focus routing hints; the
  host's coordinator discovers main-visible Domain/Service Specs and selects the owning target, and
  the Operation may span several targets and stages. Members: `concorde-main`,
  `concorde-standard-dev-loop`, `concorde-fast-loop`, `concorde-reflections-triage`.
- **Lifecycle** — deterministic host behavior with no agent cognition and no context selection.
  Members: `concorde-init`, `concorde-configure`, `concorde-validate`, `concorde-deliver`.
- **Internal stage** — receives an already bound `target_id` and one frozen context snapshot from
  its composing Operation, runs exactly one role, and never reselects or expands its context.
  Members: `concorde-specify`, `concorde-review`, `concorde-context-solve`, `concorde-plan`,
  `concorde-tasks`, `concorde-implement`.

Global and lifecycle Operations are public: each is projected as a user-invocable Skill. Internal
stage Operations are never projected as Skills; the executable boundary rejects a direct invocation
of an internal stage's `operation.py` with error code `internal_operation`. They are reachable only
in-process, composed by a global Operation (or by another internal stage that already holds a bound
target, such as code review composing per-component reviewers, or reflection investigation composing
implementation). Main routing — discovering targets and binding one `target_id` to the invocation —
happens only inside global Operations; every internal stage always starts with `target_id` already
bound by its caller.

Target workers use concorde-agent-stage-context/result @1 with explicit document order, Target Spec and Shared Specs. Coordinator routing, topology design and synthesis use concorde-main-stage-context/result with an append-only main-visible discovery context and typed concorde-main-worker-result handoffs. Accepted topology design uses topology-proposal, topology-author-context/result and a host-private topology-application artifact; shared replacements require every reference and identical bytes. Plan artifacts, implementation tasks and selected reflections have separate registered type identities. Fresh snapshots accompany every handoff. Deterministic outputs carry identities and digests, never non-visible Module collections/code/logs into main or unrelated cognition.

Reviewers use `concorde-review-stage-context@1` containing a full `concorde-context-snapshot@1`
and host-produced `concorde-review-input@1`; they return `concorde-review-stage-result@1`. The host
publishes `concorde-review-result@1` with target/focus/revision identity and `semantic_completeness=not_proven`.
Spec and code modes use different fresh roles, with no writes in either mode. Complete collections
remain distinct from the scoped change patches. Domain candidate review aggregates separately scoped
results for its recorded participating components; it never hands a project diff to one reviewer.
