```concorde-document
{
  "id": "document.operation.boundary",
  "targets": ["service.workflow-host"],
  "main_visible": true
}
```

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
succeeded|blocked|failed|described, workspace (null or host-supplied worktree metadata), output (typed response
or null) and errors [{code,field,message}]. Exit 0 means succeeded/described; 3 means blocked/failed.
Describe-policy does not launch agents or mutate project state; policy descriptions go to stderr.
A mutating request in the primary worktree creates an isolated branch from committed HEAD and
returns worktree_handoff_required with its path, branch, base commit and change_id. It does not copy
uncommitted primary changes or continue the originating agent session in the new worktree. A new
agent opened in the returned worktree continues the task. Host administrators may explicitly permit
standalone development for controlled embedding, but that override never authorizes secondary delivery.

The host resolves the complete selected Target Spec plus one-hop Shared Specs and Protocol/kind definition for every stage.
Non-implementation agents start in a private capsule containing only the frozen context. Implementation
agents get the same context plus explicitly owned code paths. Sessions are fresh, network and credential
access disabled, writes restricted by phase. A native integration unable to enforce the grant blocks;
outer enforcement requires a host-issued sandbox. Executor completions must match invocation, policy,
launch and context identities. No ambient conversation or predecessor transcript is admitted.

Every new agent-backed task first launches `concorde-coordinator` with the entry Domain or Service.
Main discovery can
append only registered main-visible Domain/Service Target Spec and Shared Specs on demand; each append starts a fresh process with a
new context identity. The host rejects Module expansion and code access. For Operations other than
the `ask` action of `concorde-main`, main must return one owning target; cross-target mutation is
routed through a Domain. The host
then starts the Operation's different bounded worker or composite flow. `concorde-main` may route one
or more fresh `concorde-reader` workers, after which a final fresh main invocation receives only typed
worker results for synthesis. An optional caller target/focus is a routing hint, not a context grant.

`concorde-main` also owns topology evolution. `design-topology` admits exact registry metadata and
all three global kind definitions while still withholding direct Module expansion and code. It returns a
digest-bound candidate registry, local Spec tasks, migration constraints and acceptance conditions;
no project file changes. `accept-topology` is the first maintainer gate. It rechecks the complete
discovery context, starts fresh target-local Spec authors and validates their combined output against
an in-memory registry/document overlay. Full worker documents are stored only in an ignored,
before-digest-bound application artifact. The public response exposes its ArtifactRef, not its
contents. `apply-topology` is the second maintainer gate and atomically applies the exact reviewed
artifact or leaves/restores the project. A stale registry, Protocol, Spec input, application digest
or invalid final target state blocks mutation.
Document membership changes require tasks for all retained current/candidate references. A shared
replacement is admitted only when every candidate referencing target author returns identical bytes.

Public `concorde-context` and `concorde-resolve-context` return only a redacted membership/digest
manifest. Complete cognitive snapshots never cross the public Operation result boundary.

Authoring returns local document replacements; the host alone applies them. A single-target author
cannot change a multiply referenced document. Planning runs a separate
context assessment first and stores a target plan only for a sufficient context and nonempty result.
One `.concorde/worktree.json` owns the change, its root task, target records, phase/status, gaps and
validation identity. Plans and auxiliary files live under `.concorde/work/<target-id>/`. There is no
new `.concorde/attempts/<change-id>/` lifecycle. Each component keeps progress in the enclosing change.
Task authoring receives a concorde-plan-artifact. Implementation receives concorde-implementation-task
and returns identical tasks marked complete only when acceptance is met. Registry, context and
configuration are rechecked after each stage. Only implementation code may change in that phase.

Standard loop executes specify, plan, tasks, implement and validate using the same public contracts
as standalone Operations. Fast loop starts at plan. Both end at ready and never invoke deliver.
Both stop on the first non-successful outcome and preserve the change worktree. A repeat resumes a
current plan/tasks/implementation phase instead of discarding completed component work.
Domain implementation coordinates independently selected participating component contexts. The host
records each author before launch and after success or blocking. Already authored draft Spec bytes
remain in the candidate when a later component blocks. Cross-component validation runs after every
affected local author finishes; it cannot prevent resuming an incomplete reconciliation. No component
code changes before this agreement. Component fast loops report completion to the same owning change.

Validation is deterministic: global registry/local contract checks plus configured check argv with
timeouts. Its raw logs stay host-private. Delivery requires current Spec/implementation identities, completed authored tasks and passing
configured checks. It is a separate deterministic request selecting change_id, issued only by an
agent opened in the primary worktree. The host rejects secondary, redirected and nested invocations;
changing cwd or forwarding a request cannot convert a secondary agent session into a primary one.
The primary worktree's current attached branch is the destination, regardless of its name. Its local
changes are preserved. The host freezes exact deliverable bytes, checks the actual merge result in a
private deterministic verification checkout, and merges only that verified result. Conflicts, failed
checks and stale bytes preserve both the accepted primary revision and the candidate worktree.
After the merge, it removes the secondary worktree, its state and temporary prompt injection. Primary
`.concorde/deliveries/` receipts preserve commit identities and checks; a cleanup failure is resumable
without a second merge. Local control files and managed prompt blocks are excluded from the Git tree. Checklist authoring
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
  "semantics": "Select target_id's exact Target Spec plus Shared Specs and assess exactly task. Shared membership adds only that document; no relationship or link expands another entity context.",
  "example": {
    "target_id": "service.transfer",
    "task": "Explain transfer admission"
  }
}
```

Each reported Spec gap carries host-bound target_id and context_id provenance. A Domain coordinator
retains that provenance when a component stage is blocked, so callers can author the correct local
Spec before retrying. Agent-supplied mismatched gap provenance is rejected.

## Main routing view

Select `module.wire-contracts` for request/result schema construction and validation,
`module.permissions` for path/network/credential policy compilation, and
`module.agent-execution` for native process launch and completion attestation. Select
`service.spec-context` when the behavior being changed is target/document resolution rather than
Operation orchestration. Public capability projection belongs to `module.package-assets`. The main
coordinator may use these stable IDs to route a worker but may not expand their Module targets.


## Worktree awareness

A directly authored Spec or manual candidate can run explicit validation without inventing a plan
or an attempt. With no authored target plans, validation runs every configured project check and
stores root validation evidence against the exact candidate tree. Existing authored plans and tasks
still require completion; this path cannot bypass unfinished work. Deterministic readiness does not
claim universal semantic completeness. The primary delivery request accepts the verified candidate.

The primary worktree maintains `.concorde/worktrees.json` from Git's live worktree inventory, including
unmanaged worktrees. Each entry has its path, branch, head, managed/locked status and, when available,
change_id, owning target, task summary, phase and status. A secondary worktree registers its own
`.concorde/worktree.json` and receives managed AGENTS.md/CLAUDE.md instructions to treat partial work as
a candidate and leave delivery to a new primary session. Host updates to these control files do not
change Spec authority or grant agent writes outside the selected target.

Every discovery and worker snapshot admits `workspace` lifecycle metadata. Main can answer a pure
workspace-status question directly from this metadata; target-behavior answers still use separate
readers. The current workspace identity and status are rechecked after a stage. Other live worktree
summaries are frozen observations and their progress does not invalidate unrelated main cognition.
