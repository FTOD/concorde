# Operation host service

## feature.workflow.execute

An Operation is a public Skill paired with an executable Python entry point. Canonical internal
Skills name one agent role; they are not public agent shortcuts. Every request passes through this
host. The local Operation registry and wire-contract document are members of this complete Spec.

Executable entry: `python operations/<operation-id>/operation.py`, no task command-line arguments.
stdin is exactly one JSON object with type_id=concorde-operation-invocation, schema_version=2,
operation_id, mode=execute|describe-policy, configuration and input. Maximum input is 1 MiB.
configuration is a concorde-operation-configuration@1 TypedValue or null for initialized host settings;
input is the Operation's named request TypedValue. A TypedValue is {type_id,schema_version:1,data};
unknown fields and versions fail admission. Configuration is integration codex|claude and enforcement
native|outer, stored at initialization and required to match host settings for ordinary operations.
Caller input never substitutes for permission authority.

stdout is concorde-operation-result@2 with operation_id, invocation_id, mode, status
succeeded|blocked|failed|described, workspace (null or {path,branch,base_commit}), output (typed response
or null) and errors [{code,field,message}]. Exit 0 means succeeded/described; 3 means blocked/failed.
Describe-policy does not launch agents or mutate project state; policy descriptions go to stderr.
A mutating request in the primary worktree creates an isolated branch from committed HEAD and
reports that workspace. It does not copy uncommitted primary changes. Host administrators may
explicitly allow a primary worktree; runtime task input cannot set that permission.

The host resolves the complete selected collection and Protocol/kind definition for every stage.
Non-implementation agents start in a private capsule containing only the frozen context. Implementation
agents get the same context plus explicitly owned code paths. Sessions are fresh, network and credential
access disabled, writes restricted by phase. A native integration unable to enforce the grant blocks;
outer enforcement requires a host-issued sandbox. Executor completions must match invocation, policy,
launch and context identities. No ambient conversation or predecessor transcript is admitted.

Authoring returns local document replacements; the host alone applies them. Planning runs a separate
context assessment first and creates an attempt only for a sufficient context and nonempty plan.
Task authoring receives a concorde-plan-artifact. Implementation receives concorde-implementation-task
and returns identical tasks marked complete only when acceptance is met. Registry, context and
configuration are rechecked after each stage. Only implementation code may change in that phase.

Standard loop executes specify, plan, tasks, implement, validate and deliver using the same public
contracts as standalone Operations. Fast loop starts at plan. Both stop on the first non-successful
outcome. Domain implementation coordinates independently selected participating component contexts;
all affected local consumer/provider contracts are reconciled before component code changes.

Validation is deterministic: global registry/local contract checks plus configured check argv with
timeouts. Its raw logs stay host-private. Delivery requires current Spec/implementation identities,
completed tasks and all configured checks passing, then removes only that attempt. It never merges a
branch. Failed or stale evidence preserves the attempt for an explicit retry. Checklist authoring
creates acceptance criteria; taskstoissues produces local issue drafts without sending messages.

```concorde-contract
{
  "id": "contract.context.selection",
  "version": 1,
  "role": "required",
  "peer": "service.spec-context",
  "schema": {
    "type": "object",
    "properties": {
      "target_id": {
        "type": "string",
        "minLength": 1
      },
      "task": {
        "type": "string",
        "minLength": 1
      }
    },
    "required": [
      "target_id",
      "task"
    ],
    "additionalProperties": false
  },
  "semantics": "Select the entire explicitly registered collection for target_id and assess exactly task. No relationship or link adds context.",
  "example": {
    "target_id": "service.transfer",
    "task": "Explain transfer admission"
  }
}
```

Each reported Spec gap carries host-bound target_id and context_id provenance. A Domain coordinator
retains that provenance when a component stage is blocked, so callers can author the correct local
Spec before retrying. Agent-supplied mismatched gap provenance is rejected.
