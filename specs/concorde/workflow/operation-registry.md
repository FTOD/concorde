# Project Operation registry

Every public Skill below has a paired executable. Configuration and runtime input are separate JSON TypedValues. Internal roles have no direct public invocation.

| Operation | Request type @1 | Response type @1 | Role or child Operations | Behavior |
| --- | --- | --- | --- | --- |
| concorde-analyze | concorde-analyze-request | concorde-analyze-response | concorde-context-assessor | Assess task and local contract consistency |
| concorde-ask | concorde-ask-request | concorde-ask-response | concorde-reader | Answer from the complete local Spec |
| concorde-checklist | concorde-checklist-request | concorde-checklist-response | concorde-planner | Author local acceptance checklist |
| concorde-clarify | concorde-clarify-request | concorde-clarify-response | concorde-spec-author | Resolve ambiguities by local authoring |
| concorde-configure | concorde-configure-request | concorde-configure-response | Deterministic host | Apply initialized operation configuration |
| concorde-constitution | concorde-constitution-request | concorde-constitution-response | concorde-spec-author | Author selected target principles |
| concorde-context | concorde-context-request | concorde-context-response | Deterministic host | Resolve exact context snapshot |
| concorde-context-solve | concorde-context-solve-request | concorde-context-solve-response | concorde-context-assessor | Assess information sufficiency without expanding context |
| concorde-converge | concorde-converge-request | concorde-converge-response | concorde-implementation-worker | Reconcile implementation with accepted tasks |
| concorde-deliver | concorde-deliver-request | concorde-deliver-response | Deterministic host | Verify current completion evidence and remove the attempt |
| concorde-fast-loop | concorde-fast-loop-request | concorde-fast-loop-response | concorde-plan, concorde-tasks, concorde-implement, concorde-validate, concorde-deliver | Plan, tasks, implement, validate, deliver |
| concorde-implement | concorde-implement-request | concorde-implement-response | concorde-implementation-worker | Implement component tasks or coordinate participating components |
| concorde-init | concorde-init-request | concorde-init-response | Deterministic host | Propose/apply explicit project initialization |
| concorde-migrate | concorde-migrate-request | concorde-migrate-response | Deterministic host | Propose/apply authored Profile 7 to 8 replacements |
| concorde-plan | concorde-plan-request | concorde-plan-response | concorde-context-assessor, concorde-planner | Assess sufficiency, then create revision-bound plan |
| concorde-reflections-triage | concorde-reflections-triage-request | concorde-reflections-triage-response | concorde-implementation-worker, concorde-standard-dev-loop | Select/status/investigate/implement/dispose owned reflections |
| concorde-resolve-context | concorde-resolve-context-request | concorde-resolve-context-response | Deterministic host | Resolve exact context snapshot |
| concorde-specify | concorde-specify-request | concorde-specify-response | concorde-spec-author | Author local Spec replacements |
| concorde-standard-dev-loop | concorde-standard-dev-loop-request | concorde-standard-dev-loop-response | concorde-specify, concorde-plan, concorde-tasks, concorde-implement, concorde-validate, concorde-deliver | Specify, plan, tasks, implement, validate, deliver |
| concorde-tasks | concorde-tasks-request | concorde-tasks-response | concorde-task-author | Author acceptance tasks from the accepted plan |
| concorde-taskstoissues | concorde-taskstoissues-request | concorde-taskstoissues-response | Deterministic host | Prepare local issue drafts from authored tasks |
| concorde-validate | concorde-validate-request | concorde-validate-response | Deterministic host | Run deterministic Spec and configured code checks |

All Stage handoffs use concorde-agent-stage-context/result @1. Plan artifacts, implementation tasks and selected reflections have separate registered type identities. Fresh snapshots accompany every handoff. Deterministic outputs carry check identities and digests, never raw code/logs into Spec-only cognition.
