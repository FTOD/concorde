```concorde-document
{
  "id": "document.operation.boundary",
  "targets": ["service.workflow-host"],
  "main_visible": true
}
```

# Operation host service

## feature.workflow.execute

A global or lifecycle Operation is a public Skill paired with an executable Python entry point. An
internal stage Operation shares the same paired executable shape but is not projected as a Skill; it
is reachable only in-process, composed by a global Operation or by another already-bound internal
stage, and the executable boundary rejects its direct invocation with error code `internal_operation`.
Canonical internal Skills name one agent role; they are not public agent shortcuts. Every request
passes through this host. The local Operation registry and wire-contract document are members of
this complete Spec.

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
agent opened in the returned worktree continues the task. The existing error message includes a
Protocol P10 draft with real worktree identity, submitted task/constraints, preparation/check status
and the absolute local state artifact path. Host-created worktrees live in temporary storage and the
draft labels that lifetime explicitly. Unavailable conversation facts are marked unknown for the
outer session to complete/localize; these drafts are never admitted as worker context or authority.
Host administrators may explicitly permit
standalone development for controlled embedding. Delivery separately requires a session in its
selected source or destination worktree; third-worktree and nested sessions are rejected.

The host resolves the complete selected Target Spec plus one-hop Shared Specs and Protocol/kind definition for every stage.
Spec-only agents, including Spec reviewers, start in a private capsule containing only frozen input.
Implementation workers get the same Spec context plus explicitly owned code paths. Code reviewers
use a distinct read-only implementation role with only the current registered file enumeration. Sessions are fresh, network and credential
access disabled, writes restricted by phase. A native integration unable to enforce the grant blocks;
outer enforcement requires a host-issued sandbox. Executor completions must match invocation, policy,
launch and context identities. No ambient conversation or predecessor transcript is admitted.

Every new agent-backed task in a global Operation first launches `concorde-coordinator` with the
entry Domain or Service.
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

No public Operation returns context manifests; the context Service is host-internal and
`describe-policy` mode already previews the exact grants an Operation would receive without
launching an agent or mutating project state. Complete cognitive snapshots never cross the public
Operation result boundary.

Authoring returns local document replacements; the host alone applies them. A single-target author
cannot change a multiply referenced document. Planning runs a separate
context assessment first and stores a target plan only for a sufficient context and nonempty result.
One `.concorde/worktree.json` owns the change, its root task, target records, phase/status, gaps and
validation identity. Plans and auxiliary files live under `.concorde/work/<target-id>/`. There is no
new `.concorde/attempts/<change-id>/` lifecycle. Each component keeps progress in the enclosing change.
Task authoring receives a concorde-plan-artifact. Implementation receives concorde-implementation-task
and returns identical tasks marked complete only when acceptance is met. Registry, context and
configuration are rechecked after each stage. Only implementation code may change in that phase.

Standard loop executes specify, Spec review, plan, tasks, implement, deterministic validation and
code review, then verifies readiness. It uses the same public contracts as standalone Operations.
Fast loop starts with optional Spec review before plan and optional code review after checks.
Both end at ready and never invoke deliver.
Both stop on the first non-successful outcome and preserve the change worktree. A repeat resumes a
current plan/tasks/implementation phase instead of discarding completed component work.
Domain implementation coordinates independently selected participating component contexts. The host
records each author before launch and after success or blocking. Already authored draft Spec bytes
remain in the candidate when a later component blocks. Cross-component validation runs after every
affected local author finishes; it cannot prevent resuming an incomplete reconciliation. No component
code changes before this agreement. Component fast loops report completion to the same owning change.

Validation is deterministic: global registry/local contract checks plus configured check argv with
timeouts. Its raw logs stay host-private. Delivery requires current Spec/implementation identities, completed authored tasks and passing
configured checks plus current required reviews and resolved task gaps. It is a separate deterministic request selecting change_id, issued only by an
agent whose initial working directory is either the selected source or destination primary worktree.
The host rejects unrelated third-worktree and nested invocations; changing cwd or forwarding a
request does not confer participating-session identity.
The primary worktree's current attached branch is the destination, regardless of its name. Its local
changes are preserved. The host freezes exact deliverable bytes, checks the actual merge result in a
private deterministic verification checkout, and merges only that verified result. Conflicts, failed
checks and stale bytes preserve both the accepted primary revision and the candidate worktree.
After the merge, it retains the source when it owns the session or `keep_worktree:true` is requested;
otherwise it removes that worktree, its state and temporary prompt injection. Primary
`.concorde/deliveries/` receipts preserve commit identities and checks; a cleanup failure is resumable
without a second merge. Local control files and managed lifecycle prompt blocks are excluded from the Git tree.
Installed root Protocol entries are project content and remain in the delivered tree.

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
a candidate and request delivery from either participating worktree. Host updates to these control files do not
change Spec authority or grant agent writes outside the selected target.

Every discovery and worker snapshot admits `workspace` lifecycle metadata. Main can answer a pure
workspace-status question directly from this metadata; target-behavior answers still use separate
readers. The current workspace identity and status are rechecked after a stage. Other live worktree
summaries are frozen observations and their progress does not invalidate unrelated main cognition.

## Independent review contract

`concorde-review` requires target_id, task and review_mode=spec|code, with the usual optional focus,
constraints and current-worktree change_id. It is an internal stage Operation invoked with an
already routed target by its composing global Operation or by another already-bound internal stage;
it is never invoked directly with an unrouted task. Spec mode uses the complete admitted Target Spec plus Shared
Specs, Protocol/kind rules, task and only that collection's Spec changes. Code mode uses those
contracts, the target's exact current registered implementation-file enumeration and scoped code
changes. Both roles have empty write grants, no network/credentials, fresh sessions, and empty
predecessor input. Code review does not reuse implement's writable policy.

The host compares the candidate's current bytes, including uncommitted and untracked owned files,
against this managed change's recorded base_commit; an unmanaged Git checkout uses its current HEAD.
An unversioned root has null baseline/head and its current granted files are new input. History is
read only from that repository's Git objects and scoped to the current target grant. No other worktree
supplies content. Deleted files under a current grant appear as scoped changes; removed or unrelated
grants never expose their old contents. Full admitted current documents always accompany Spec review,
even when a focus or patch names only a small portion.

Private `concorde-review-stage-context@1` contains a full context snapshot and a
`concorde-review-input@1` with review_mode, input_digest, revision and changes. Each change is
`{path, patch}`; binary changes carry only digest markers. The revision has spec_digest,
nullable implementation_digest, nullable baseline and nullable head. spec_digest binds the selected
target descriptor, pinned Protocol and ordered complete document byte digests. Code mode additionally
binds every currently enumerated implementation path/byte digest. input_digest covers these values,
scoped changes, absolute current worktree/branch, target/focus, task/constraints/change identity,
initialized configuration, canonical
reviewer instructions/effects and host review/context/permission/executor runtime bytes. Context ID
additionally records the actual frozen lifecycle observation. Lifecycle phase changes alone do not
invalidate an otherwise identical task review; changed relevant input does. Old result artifacts
remain audit history and cannot pass a current gate.

The reviewer returns `concorde-review-stage-result@1` bound to context_id, input_digest and mode, with
representative_tasks, findings, gaps, answer and status=no_findings|findings|incomplete. A finding
has unique id, severity=blocking|advisory, target_id, document (an exact admitted Markdown path),
contract, location={path,line}, problem and affected_task. line is a positive integer or null.
Its contract document must be in the complete collection, and its location must be admitted Spec or
code/change scope. A blocking Spec finding requires a gap with blocked_step=affected_task and
needed_contract=contract. Gap target/context provenance is verified and filled by the host. Missing
contracts during code review also use gaps; a concrete code defect can block without a Spec gap.
Findings and answers contain contract-level descriptions/locations, never raw code, patches or logs.

The host rejects mismatched identities, foreign locations, duplicate IDs/tasks, a clean result with
findings/gaps, a findings result without evidence, and completed review without representative tasks.
It rechecks the context, source/input/configuration identities and frozen capsule after execution.
It publishes `concorde-review-result@1` adding target/focus, revision and
semantic_completeness=not_proven. Public response `reviews` contains these typed results, and artifacts
reference saved review reports. Native receipts and failure diagnostics remain separate host records.

| Review state | Public Operation outcome and progression |
|---|---|
| no_findings with nonempty coverage | completed; bounded review succeeded |
| findings, all advisory and no gaps | completed; findings retained for the consumer |
| concrete necessary gaps | spec_incomplete; dependent steps pause |
| blocking code findings without gaps | conflicting; dependent steps pause |
| incomplete coverage, invalid result or process failure | failed; an incomplete report, never a clean result |
| describe-policy | described with not_run; no execution or persistence |
| fast-loop disabled mode | host records skipped; no reviewer runs |

Every mode and target uses a separate session. A Domain with recorded component work can request
cross-target review: the host validates each component's participation, starts its own reviewer from
its recorded task and admitted collection, then aggregates only typed results. Spec review also
assesses the Domain itself; code review never gives the Domain code. A Domain without recorded
component work returns unsupported for code review. During a development loop, the Domain's initial
Spec review is local; component reviews occur in the coordinated component loops after reconciliation.

## Review gates, gap history and recovery

Standard-loop resumption skips Spec authoring only after a host-accepted authoring result for the
same target, task, focus and constraints. Standalone review records, including failed or unrelated
reviews, cannot substitute for authoring. A completed Domain still revisits its recorded component
coordination: stronger review requirements propagate before completed component work is reused,
and missing or stale component reviews run before readiness.

Standard development requires both reviews for a code-owning target (only Spec review for a Domain).
Fast-loop `run_reviews` defaults to false and applies to both modes. Requirements and the exact review
intent are saved per target in the existing worktree state; an enabled requirement survives retries
with run_reviews=false. Skips have separate records and never satisfy a required gate. A standalone
review with a different task/focus/constraints remains a run artifact and cannot replace another
intent's lifecycle-required review. Code review runs after checks but before the single ready transition;
a failed/incomplete/blocking review cannot be bypassed by standalone validation or delivery.

A repeated loop preserves current plans/tasks and completed components. It reuses a review only after
checking its artifact digest, exact current inputs, successful coverage and absence of blocking
findings/gaps. Changed Spec invalidates its dependent plan/reviews and rebuilds context; changed code
invalidates code review/check evidence. Explicitly required reviews also apply to directly authored
candidates without inventing plans. Review does not edit files, run repair steps or deliver changes.

Necessary missing/ambiguous contracts discovered during explanation, assessment, planning, task
splitting or implementation use the same question/blocked_step/needed_contract gap contract. Queries
only return them. Development stores gap history with target/task/phase, Spec revision, observed
contexts and status. Identical reports are deduplicated. Unrelated work does not clear open entries;
a still-unchanged blocked step remains paused. A successful fresh assessment after a Spec repair
resolves the affected phase's old gaps while keeping history. For authoring, planning, task creation
and implementation, successful assessment is committed only after the host accepts the returned
documents/artifacts/tasks; rejected replacements or malformed results preserve previous blockers.
Spec authoring may supply the repair
itself. Independent work may continue without claiming dependent tasks complete. The explicit
reflections-triage record-gaps action creates or reuses a durable Reflection link; it neither resolves
the gap nor silently turns a query into authoring, investigation or implementation.

## Required collaborator interfaces

The registered Shared Specs **Agent runtime value and collaborator contracts** and **Registry
selection and value contracts** are members of this same complete collection. They define all policy,
launch, receipt, completion, registry, document and local contract records used below. They do not
admit their other referencing targets' remaining Specs. These local required views are the promises
the host relies on, independently of implementation imports.

- Registry (`module.registry`): `SpecRepository(project_root, package_root=None, *, registry_bytes=None,
  document_overrides=None)` returns the read-only admitted repository described in the Shared Spec.
  `select(target_id, focus_id=None)` returns SpecTarget; documents/contracts/implementation_files use
  that descriptor and the complete locally defined return shapes. Reconstruct after changes; reject
  unknown/foreign selection, unsafe paths, invalid bindings and stale sources before granting access.
- Context (`service.spec-context`): `resolve_context(repository: SpecRepository, target_id: str, *,
  phase: str="ask", task: str="Understand this Spec", focus_id: str|None=None,
  constraints: tuple[str,...]=(), instructions: str="", stage_inputs: tuple[dict,...]=(),
  workspace: dict|None=None) -> ContextSnapshot`. Snapshot exposes canonical serialized JSON,
  `.value: dict` conforming to the local context-snapshot schema and `.id: str`. It returns every
  registered document once, separated by local/shared membership, plus pinned rules and explicit
  inputs. Implementation/code-review phases include only registered code ArtifactRefs.
  `recheck_context(repository, snapshot, *, check_implementation: bool=True) -> None` reconstructs
  current context and rejects changed membership, classification, bytes or worktree identity via
  SpecError(code="stale_context"). These APIs read but never write project sources or execute an
  agent, and this Service is host-internal: no public Operation exposes its return values directly.
- Permissions (`module.permissions`): `compile_policy(effects, binding, role_paths, *, deny_paths=(),
  outer_sandbox_required=False) -> NormalizedPolicy`, the Codex/Claude renderers, and
  `build_launch_specification(...) -> LaunchSpecification` have complete signatures and value types
  in the runtime Shared Spec. They must reject widening, preserve empty reviewer writes and bind
  policy/native/context identities. `PermissionPolicyError(ValueError)` aborts the launch; an opaque
  task string cannot supply outer enforcement.
- Execution (`module.agent-execution`): `AgentProcessExecutor()` constructs the default host executor;
  `executor(launch: LaunchSpecification) -> OperationExecutionResult` starts one fresh native process.
  A host may inject a callable with this same interface for a verified backend. The exact result,
  completion and error/receipt records are in the runtime Shared Spec. Successful exit without matching
  completion is failure. `OperationExecutionError(RuntimeError)` has a nullable receipt and stops the
  affected transition; it never retries permissively. Typed result validation remains mandatory for
  injected executors. Code/log material never becomes a later Spec-only input.
- Wire (`module.wire-contracts`): `typed(type_id: str, data: dict) -> dict` and
  `validate_typed(value: Any, expected: str|None=None, field: str="") -> dict` admit exactly
  `{type_id,schema_version:1,data}` against the complete local wire schemas, rejecting unknown
  types/versions/properties and invalid fields. `decode(text: str) -> Any` rejects duplicate keys and
  non-finite JSON numbers; `canonical(value: Any) -> str` uses sorted compact JSON. Artifact helpers
  `artifact(project: Path, identifier: str, relative: str) -> {id,path,digest}` and
  `verify_artifacts(project: Path, value: Any, field: str="") -> None` bind regular-file bytes and
  reject stale references recursively in objects/lists. `checked_path(project, relative, field="")`
  rejects aliases and symlink traversal. `OperationDataError(ValueError)` carries code/field; no
  helper expands context or performs remote schema retrieval.
- Configuration (host-owned adapter): `load_configuration(project_root: str|Path) -> dict`
  returns the initialized concorde-operation-configuration TypedValue from `.concorde/config.json`.
  Ordinary invocations and child stages must equal that snapshot; mismatch stops the transition.
  It neither grants permissions nor silently falls back to caller-provided settings.
- Package assets (`module.package-assets`): `resolve_skill_prompt(path: Path, kind: "skill"|"operation",
  framework_prefix: str=".concorde/framework") -> SkillPrompt` reads one canonical declared asset.
  SkillPrompt exposes name/description/source_path/body as strings, kind/exposure, optional Operation
  entry, dependency tuple, EffectDeclaration or None, and script path tuple. Missing/unsafe sources,
  wrong name/kind, malformed effects or dependency mismatches raise SkillAssetError(ValueError).
  The host supplies the body inline and admits only role-specific paths; it does not let the worker
  reopen the asset package.
- File transactions (`module.file-transactions`): `file_change(root: Path, path: str, content: str) ->
  {path,before_digest,content}` captures current bytes (null digest for new files).
  `apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]` requires
  nonempty unique allowed paths, UTF-8 replacement text and exact before digests. It rechecks before
  writes, optionally calls the zero-argument verifier, and restores written bytes on failure.
  Stale or foreign proposals raise SpecError; no partial transaction is reported successful.
- Validation (`service.spec-context`): `validate_repository(root: Path|str, target_id: str|None=None,
  package_root: Path|str|None=None) -> ToolResult` returns status=success|invalid, findings and a result
  containing source_digest for the assessed Spec state. Findings have rule_id/message/remediation.
  It checks structure/references/types/permissions and explicitly does not prove semantics.
  Configured implementation checks execute separately on the host using registered argv/timeouts;
  they return check_id/target_id/status/exit_code/source_digest/log_digest as locally defined, with
  raw output retained privately. No check result is an arbitrary source-read proxy for an agent.

A host launching review therefore resolves the current target and full context, derives only scoped
changes, compiles the selected read-only role, builds a fresh launch with review-stage input, validates
its typed completion and stores a version-bound public report. Each prerequisite and failure channel
is supplied within this collection; no provider Spec or source is needed to plan that interaction.

The read-only reflections-triage `status` response exposes `gap_records`, each with id (a digest),
target_id, task, phase, the existing structured gap, status=open|resolved, and nullable reflection_id.
It lists current change history owned by the selected target, including participating component gaps
for a coordinating Domain. Use the returned id values as record-gaps gap_ids; IDs remain stable across
context-only retries and are not calculated by the caller. Status without a managed change returns
an empty list. record-gaps requires a nonempty explicit list and reflection_ids=[]: omitted/empty
lists never mean all; unknown or resolved IDs fail as stale_reference. A repeated capture returns
the existing link. The public metadata is sufficient for selection without reading control files.
