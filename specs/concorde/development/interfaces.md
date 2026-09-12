```concorde-document
{
  "id": "document.development.interfaces",
  "owner": "module.development",
  "main_visible": true
}
```
# Development host boundary

## Required orchestration model
The registered companion documents of the Harness Module define the Agent model (A1–A5) and the
Agent Graph and Loop model (G1–G4) this host composes. The Harness resolves Agent definitions,
their `spec.md` sources, Harness configurations and effective constraints into a reproducible
`AgentBinding` that every structured launch carries, and its executor verifies that binding before
any process starts. This Module MUST coordinate declared Graph transitions and bounded loops with
attributed AI feedback and explicit human decisions, and every capability graph is a LangGraph
graph whose nodes are deterministic steps or Agent invocations. The wire `role` and `agent` fields
remain compatibility identifiers derived from the bound Agent's name.

## Capability execution boundary
A Capability provides usable or composable functionality under the Agent and Harness contract.
The existing host adapter implements each registered entry as a Python module declaring launched
Agents, effects, composed entries and typed request/response contracts. In this adapter, rendered
public Skills expose exactly one global or lifecycle capability. Stage capabilities have no Skill and no direct invocation. Every request
passes through this host. The capability registry is a member of this complete Spec; exact wire
schemas are code, exported by the build and published by the docsite, and this document states
their promises.

Executable entry: `python3 scripts/run-capability.py <skill-name>`, no task command-line arguments.
A name that is not a Skill is refused with `unknown_capability`. stdin is exactly one JSON object
`concorde-capability-invocation@3` with fields type_id, schema_version=3, capability_id (the Skill's
name), mode=execute|describe-policy, configuration and input. Maximum input is 1 MiB. Schema 2
invocations are rejected with `unsupported_version`. configuration is a
`concorde-capability-configuration@1` TypedValue or null for the initialized host settings; input is
the capability's named request TypedValue. A TypedValue is {type_id,schema_version:1,data}; unknown
fields and versions fail admission. Configuration is integration codex|claude and enforcement
native, the only admitted value while no distributed launcher attests an outer sandbox. It is stored
at initialization under `capability_configuration` and required to match host settings for ordinary
invocations. Caller input never substitutes for permission authority.

stdout is `concorde-capability-result@3` with capability_id, invocation_id, mode, status
succeeded|blocked|failed|described, workspace (null or host-supplied worktree metadata), output
(typed response or null) and errors [{code,field,message}]. Exit 0 means succeeded/described; 3 means
blocked/failed. Describe-policy does not launch agents or mutate project state; policy descriptions
go to stderr. Before any launch or policy description the host verifies the build manifest and
refuses a stale build with `stale_build`.

The invocation's project root is the working directory of that entry process, exactly as resolved
and without searching parent directories. The registry, Spec collections, lifecycle state and listed
implementation files it reads are those of the worktree at that directory; the stale-build check
inspects the framework checkout that contains the launched script. A working directory at a Git
worktree root is admitted as a `primary` or `change` workspace and a directory outside any Git
repository as `unversioned`; a directory inside a Git worktree that is not its root is refused with
`workspace_mismatch`. The Skill's entry command is project-relative, so a rendered Skill carries no
worktree identity: the worktree in which the developer's agent session started, the worktree whose
Skill projection supplied the instructions and every other linked worktree contribute no registry,
document or file to the invocation, and changing the working directory selects a different project
rather than a wider one.

A mutating request in the primary worktree creates an isolated branch from committed HEAD and
returns worktree_handoff_required with its path, branch, base commit and change_id. It does not copy
uncommitted primary changes or continue the originating agent session in the new worktree. A new
agent opened in the returned worktree continues the task. The existing error message includes a
Framework execution profile P10 draft with real worktree identity, submitted task/constraints, preparation/check status
and the absolute local state artifact path. Host-created worktrees live in temporary storage and the
draft labels that lifetime explicitly. Unavailable conversation facts are marked unknown for the
outer session to complete/localize; these drafts are never admitted as worker context or authority.
Host administrators may explicitly permit
standalone development for controlled embedding. Delivery separately requires a session in its
selected source or primary worktree; third-worktree and nested sessions are rejected. Default
delivery publishes a per-change branch and removes the source worktree unless explicitly retained.
Final primary merging is a separate merge_primary:true request requiring explicit user authorization
and the primary owning session. Only one agent owns primary writes; the host serializes shared
lifecycle writes and final merges with the repository lock.

The host resolves the complete selected owned and directly referenced Specs and Protocol/kind definition for every stage.
Spec-only agents, including Spec reviewers, start in a private capsule containing only frozen input.
Implementation workers receive the complete Module context plus the contents of its own listed implementation files. Planners and task authors already see those file names through the Module's entity declarations, but receive no file contents. Code reviewers
use a distinct read-only implementation role with only the current listed implementation files. Sessions are fresh, network and credential
access disabled, writes restricted by phase. A native integration unable to enforce the grant blocks;
the attested outer-sandbox rendering path stays in Permissions for a trusted embedding host, but no
admitted configuration selects it. Executor completions must match invocation, policy,
launch and context identities. No ambient conversation or predecessor transcript is admitted.

Every new agent-backed task in a global capability first launches `concorde-coordinator` with the
entry Module.
Main discovery can
admit registered complete Module collections on demand; each admission starts a fresh process with a new context identity. Main never reads implementation file contents or code. For capabilities other than
the `ask` action of `concorde-main`, main must return one owning target; cross-target mutation is
routed through a Module. The host
then starts the capability's different bounded worker or composite flow. For questions,
`concorde-main` answers directly from complete contexts resolved by Python and injected into the
coordinator. Source pools deduplicate full document bodies, while target
records retain sole ownership and every inclusion reason. Additional selections restart the coordinator with the
expanded complete context; no reading worker or synthesis stage intervenes. An optional caller
target/focus is a routing hint, not a context grant.

`concorde-main` also owns topology evolution. `design-topology` admits exact registry metadata and
the Module kind definition while withholding implementation file contents and code. It returns a
digest-bound candidate registry, local Spec tasks, migration constraints and acceptance conditions;
no project file changes. `accept-topology` is the first developer gate. It rechecks the complete
discovery context, starts fresh target-local Spec authors and validates their combined output against
an in-memory registry/document overlay. Full worker documents are stored only in an ignored,
before-digest-bound application artifact. The public response exposes its ArtifactRef, not its
contents. `apply-topology` is the second developer gate and atomically applies the exact reviewed
artifact or leaves/restores the project. A stale registry, Protocol, Spec input, application digest
or invalid final target state blocks mutation.
Ownership/reference changes reconcile all old and candidate context consumers. Only the candidate
owner supplies replacement bytes; each consumer reviews compatibility under its own resolved context.

No Skill returns context manifests; context resolution is host-internal and
`describe-policy` mode already previews the exact grants a capability would receive without
launching an agent or mutating project state. Each previewed stage's description also names the
bound Agent and Harness identity (`agent`, `harness`, `agent_binding_digest`, `instructions_digest`,
`loop_timeout_seconds`), so a caller can audit which Agent definition and effective loop timeout a
launch would use without reading its rendered instructions. Complete cognitive snapshots never cross
the Skill result boundary.

Authoring returns local document replacements; the host alone applies them. An owner may propose a change to its document even when others reference it; acceptance requires
the affected-consumer checks, while a referencing author cannot replace provider documents. Planning runs a separate
context assessment first and stores a target plan only for a sufficient context and nonempty result.
One `.concorde/worktree.json` owns the change, its root task, target records, phase/status, gaps and
validation identity. Plans and auxiliary files live under `.concorde/work/<target-id>/`. There is no
new `.concorde/attempts/<change-id>/` lifecycle. Each component keeps progress in the enclosing change.
Task authoring receives a concorde-plan-artifact and concorde-task-identity-constraints. Implementation receives concorde-implementation-task
and returns identical tasks marked complete only when acceptance is met. Registry, context and
configuration are rechecked after each stage. Only implementation code may change in that phase.

`concorde-dev-loop` executes specify (default `specify=true`; `specify=false` skips Spec authoring
when the target's current Spec already suffices), Spec review, plan, tasks, implement, deterministic
validation and code review, then verifies readiness. It uses the same public contracts as standalone
capabilities. `run_reviews` defaults to `true`; `run_reviews=false` records an explicit skip for each
review mode instead of running it, and cannot cancel a review already required for this change. Every
invocation ends at ready and never invokes deliver.
It stops on the first non-successful outcome and preserves the change worktree, except that a
code-owning target's blocking code review first attempts a declared, bounded repair. The only
automatic revision edge is `review_code -> tasks`: task authoring receives the current completed
tasks and the blocking `concorde-review-result` as `stage_inputs`, and the resulting repair tasks
and their implementation are checked and code-reviewed again like any other change. This repair is
bounded by a declared `max_repair_iterations` policy recorded per target under
`change["graph"][target_id]["policy"]` in `.concorde/worktree.json`; the same record keeps the
current `repair_iteration`, the last blocking-feedback fingerprint and an attributed history of
selected transitions (development.md's "AI and human feedback", G4). Repeated unchanged blocking
feedback is guarded by code: new records carry the formal `source` value `code-driven` or
`model-driven`, while retaining their descriptive legacy `trigger` label. A repair selected from
review findings is model-driven; unchanged-feedback and limit stops are code-driven. Repeated unchanged blocking
feedback across a repair attempt, or exhausting the declared limit, stops the Graph instead of
retrying forever: the change `status` becomes `waiting` (a human decision or a Spec/code change is
needed) or `limit_exhausted` respectively, and the wire `outcome` remains `conflicting`. Elsewhere, a
Spec gap (`spec_incomplete`) stops the Graph with status `waiting`, a failed deterministic check
stops it with status `failed`, and another blocking/unsupported outcome stops it with status
`blocked`. A human directly changing the Spec or the implementation between invocations resets the
recorded repair count instead of silently continuing a stale repair attempt. Preserving the change
worktree on a stop and resuming a current plan/tasks/implementation phase on a repeat instead of
discarding completed component work otherwise remain unchanged.
Module implementation coordinates independently selected participating component contexts. The host
records each author before launch and after success or blocking. Already authored draft Spec bytes
remain in the candidate when a later component blocks. Cross-component validation runs after every
affected local author finishes; it cannot prevent resuming an incomplete reconciliation. No component
code changes before this agreement. Component development loops report completion to the same owning change.

The canonical [context selection agreement](../harness/context.md#contract.context.selection)
is included through Development's Module reference to Harness.

```concorde-contract-binding
{
  "id": "contract.context.selection",
  "version": 2,
  "role": "required",
  "peer": "module.harness",
  "selection_condition": "Before assessment, planning, authoring or review for a selected Module.",
  "relied_upon_guarantees": [
    "[Selection](../harness/context.md#contract.context.selection) determines the complete admitted contract and its original owners."
  ],
  "obligations": [
    "Supply the explicit Module and task; stop dependent transitions on gaps or stale context, and never treat included provider definitions as writable local Specs."
  ]
}
```

Each reported Spec gap carries host-bound target_id and context_id provenance. A Module coordinator
retains that provenance when a component stage is blocked, so callers can author the correct local
Spec before retrying. Agent-supplied mismatched gap provenance is rejected.

## Wire contracts
Every TypedValue is `{type_id, schema_version, data}`; `schema_version` is pinned per type below and
`data` must satisfy that type's JSON Schema. The invocation envelope wraps every request and
response; the thirteen capability request/response pairs carry each capability's own task and
result; the remaining types are internal handoffs, review records, topology artifacts, the project
proposal and the stage-input artifacts that pass between stages inside one capability.

### Invocation envelope

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-capability-invocation@3` | Every request, on stdin | `{type_id, schema_version: 3, capability_id, mode: execute\|describe-policy, configuration, input}`. `capability_id` must name a Skill; a stage or unknown name is refused with `unknown_capability`. `configuration` is a `concorde-capability-configuration@1` TypedValue or null (falls back to the initialized project settings); `input` is the named capability's own request TypedValue. Any other `schema_version` is refused with `unsupported_version`. |
| `concorde-capability-result@3` | Every response, on stdout | `{type_id, schema_version: 3, capability_id, invocation_id, mode, status: succeeded\|blocked\|failed\|described, workspace, output, errors: [{code,field,message}]}`. `output` is the named capability's own response TypedValue or null; `workspace` is null or host-supplied worktree metadata. Exit code 0 means `succeeded`/`described`; 3 means `blocked`/`failed`. |
| `concorde-capability-configuration@1` | The invocation's `configuration` field, and `concorde-configure-request@1`/`-response@1` | `{integration: codex\|claude, enforcement: native}`; `outer` is not admitted while the distributed launchers supply no sandbox attestation. Stored at initialization under `.concorde/config.json`'s `capability_configuration` key; an invocation or child stage whose configuration differs from that stored snapshot stops with `configuration_mismatch`. |

### Capability requests and responses

Common request task fields (named once, not repeated per row): `target_id` (required for every
stage capability; an optional routing hint for `main`, `dev-loop` and `reflections-triage`), `task`,
`focus_id` (a candidate scenario ID), `constraints`, `change_id`. Common response fields (present in every capability response
except `configure`, which replaces them): `target_id`, `focus_id`, `change_id`, `context_id`,
`outcome`, `answer`, `artifacts`, `gaps`, `checks`, `completed_capabilities`.

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-main-request@1` / `concorde-main-response@1` | main | Every request field is optional at the wire level. Request adds `action` (ask\|design-topology\|accept-topology\|apply-topology, default ask), `topology_proposal` (a `concorde-topology-proposal@1` TypedValue, required for accept-topology) and `application` (an ArtifactRef, required for apply-topology). Response adds `entry_target`, `discovered_targets`, `routes`, nullable `topology_proposal`/`application`, `files` and `workspace`. |
| `concorde-dev-loop-request@1` / `concorde-dev-loop-response@1` | dev-loop | Only `task` is required. Request adds optional `repair_task_scope:{tasks_digest: sha256}` for exact incomplete-list phase recovery, `specify` (default true; false skips Spec authoring) and `run_reviews` (default true; false records an explicit per-mode skip). Response is the common shape only. |
| `concorde-reflections-triage-request@1` / `concorde-reflections-triage-response@1` | reflections-triage | Requires `target_id`, `action` (status\|record-gaps\|investigate\|implement\|merge\|close) and `reflection_ids` (a unique array, possibly empty); `task` is optional here, unlike other capabilities, because status and record-gaps need none. Adds optional `gap_ids`. Response adds `reflections` and `gap_records`. |
| `concorde-init-request@1` / `concorde-init-response@1` | init | Requires only `action` (propose\|apply); adds optional `name`, `target_id`, `configuration` and `proposal` (a `concorde-project-proposal@1` TypedValue). Response replaces the common shape with `status` (proposed\|applied), a nullable `proposal` and `files`. |
| `concorde-configure-request@1` / `concorde-configure-response@1` | configure | Requires `configuration`. Response requires `configuration` and `status: "applied"`; the only capability whose response does not use the common stage shape. |
| `concorde-validate-request@1` / `concorde-validate-response@1` | validate | Requires `target_id` and `task`; adds optional `run_checks`. Response is the common shape only. |
| `concorde-deliver-request@1` / `concorde-deliver-response@1` | deliver | Requires only `change_id`; adds optional `target_id`, `task`, `focus_id`, `constraints`, `keep_worktree` and `merge_primary`. Response is the common shape only. |
| `concorde-specify-request@1` / `concorde-specify-response@1` | specify (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-review-request@1` / `concorde-review-response@1` | review (global) | Requires `task` and `review_mode` (spec\|code); optional target/focus are routing hints for a new standalone task. A composing capability or current-change resumption supplies the bound target. Response adds `reviews` (`concorde-review-result@1` TypedValues). |
| `concorde-context-solve-request@1` / `concorde-context-solve-response@1` | context-solve (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-plan-request@1` / `concorde-plan-response@1` | plan (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-tasks-request@1` / `concorde-tasks-response@1` | tasks (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-implement-request@1` / `concorde-implement-response@1` | implement (stage) | Requires `target_id` and `task`. Response is the common shape only. |

### Stage handoffs

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-context-snapshot@2` | Every stage capability's frozen input | [Canonical snapshot](../harness/context.md#context-snapshot-resolution); preserve its resolution provenance and reject stale inputs. |
| `concorde-agent-task@1` | Host or admitted parent to Agent | [Canonical Agent wire values](../harness/typed-values.md#typed-values-and-recursive-dispatch); Development validates before dispatch and never expands the grant. |
| `concorde-agent-answer@1` | Generic Agent to parent | [Canonical Agent wire values](../harness/typed-values.md#typed-values-and-recursive-dispatch); Development validates before dispatch and never expands the grant. |
| `concorde-agent-interruption@1` | Agent to parent | [Canonical Agent wire values](../harness/typed-values.md#typed-values-and-recursive-dispatch); Development validates before dispatch and never expands the grant. |
| `concorde-agent-loop-context@1` | Host to fresh native decision | [Canonical Agent wire values](../harness/typed-values.md#typed-values-and-recursive-dispatch); Development validates before dispatch and never expands the grant. |
| `concorde-agent-loop-step@1` | Native decision to host | [Canonical Agent wire values](../harness/typed-values.md#typed-values-and-recursive-dispatch); Development validates before dispatch and never expands the grant. |
| `concorde-agent-stage-context@2` | Host to worker, wrapping the launch | `{snapshot: concorde-context-snapshot@2, change_id, expected_artifacts}`. |
| `concorde-agent-stage-result@1` | Worker to host, the completion | `{context_id, outcome, answer, gaps, documents, plan, tasks, reflection_findings?}`; `documents`/`plan`/`tasks`/`reflection_findings` are populated only by the phase that produces them. A mismatched `context_id` is rejected as `incompatible_handoff`. |

### Review types

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-review-input@1` | Host-produced, inside the review stage context | `{review_mode, input_digest, revision, changes: [{path,patch}]}`; binds the exact Spec/code revision under review. |
| `concorde-review-stage-context@2` | Host to reviewer, the launch | `{snapshot: concorde-context-snapshot@2, review: concorde-review-input@1}`. |
| `concorde-review-stage-result@1` | Reviewer to host, the completion | `{context_id, input_digest, review_mode, status: no_findings\|findings\|incomplete, representative_tasks, findings, gaps, answer}`. |
| `concorde-review-result@1` | Published in `concorde-review-response@1.reviews` | The stage result plus `target_id`, `focus_id`, `revision`, a nullable `context_id`, `status` extended with skipped\|not_run, and `semantic_completeness: "not_proven"`. |

### Topology types

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-discovery-context@2` | Host to coordinator | [Canonical discovery context](../harness/context.md#global-spec-context-assembly); only explicit selections may expand discovery. |
| `concorde-main-stage-context@2` | Wraps the discovery context for launch | `{snapshot: concorde-discovery-context@2}`. |
| `concorde-main-stage-result@1` | Coordinator to host, the completion | `{context_id, outcome, answer, expand_targets, routes, gaps, topology_design (nullable)}`. |
| `concorde-topology-design@1` | design-topology's output, embedded in the main stage result | `{summary, registry, spec_tasks (nonempty), migration_constraints, acceptance (nonempty)}`. |
| `concorde-topology-proposal@1` | design-topology's response, and accept-topology's request | `{proposal_id, base_registry_digest, protocol_binding, context_id, discovered_targets (nonempty), task, constraints, target_hint, focus_hint, design: concorde-topology-design@1, workspace}`; a stale `base_registry_digest` or `protocol_binding` is rejected as `stale_proposal`. |
| `concorde-topology-author-context@2` | Host to target-local Spec author, during accept-topology | `{context_id, base_registry_digest, target, task, protocol_binding, protocol, candidate_references, spec_resolution, instructions, workspace}`. |
| `concorde-topology-author-result@1` | Author to host, the completion | `{context_id, target_id, outcome, answer, gaps, documents}`. |
| `concorde-topology-application@1` | Host-private, produced by accept-topology and consumed by apply-topology | `{application_id, topology_proposal: concorde-topology-proposal@1, base_registry_digest, protocol_binding, files (nonempty)}`; the public response exposes only its ArtifactRef, never these bytes. |

The canonical [discovery record](../harness/context.md#global-spec-context-assembly) defines
deduplicated source pools and per-Module provenance. Development retains it unchanged in each
handoff and checks currentness before using its result; it does not define a second record shape.
The topology-author context's `candidate_references` is the candidate Module's explicit references;
`spec_resolution` is its candidate one-level resolution. Providers are read-only unless the author
is their candidate owner. Ownership transfers, additions and removals bind both prior and candidate
descriptors and all affected consumers in the prepared application.

For ask, the coordinator may expand explicitly selected contexts or complete directly from their
original contents with no routes. Other routed capabilities preserve one target task and its
constraints. Spec gaps identify an admitted Module and the current combined context identity.
Old reading-worker results and the synthesis phase are not accepted; clients must use the current
build-bound schemas and instructions. Existing Protocol bindings remain pinned until explicitly
updated; a mismatched package/context is rejected instead of reinterpreted.

### Project proposal

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-project-proposal@1` | `concorde-init-request@1.proposal` and `-response@1.proposal` | `{action: "initialize", base_digest (nullable), files: [{path, before_digest (nullable), content}]}`. |

### Stage-input artifacts

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-plan-artifact@1` | A `stage_inputs` entry: produced by plan, consumed by tasks | `{plan}`. |
| `concorde-task-identity-constraints@1` | Host to every fresh task author, including after replanning | `{reserved_task_ids: list[nonblank str]}`; required, sorted and unique, possibly empty. Includes every retained historical ID and the current list for scope or code-review repair. New tasks must not reuse these identities; collisions report the conflicting IDs without rewriting output or history. No software obligations or code contents. |
| `concorde-implementation-task@1` | A `stage_inputs` entry: produced by tasks, consumed by implement | `{plan, tasks: [{id,target_id,description,acceptance,complete}]}`; implement must return every task with the same identity, marked complete only when its acceptance is met. |
| `concorde-task-scope-feedback@1` | Host to fresh task author only | `{tasks_digest: sha256, reason: "implementation_boundary"}`; fixed semantic feedback preserves software acceptance while separating implementation from later Host validation, review and authorized outer-session commit. No code or raw logs. |
| `concorde-reflection-selection@1` | A `stage_inputs` entry: produced by reflections-triage, consumed by dev-loop implementation | `{head, records: [{id,path,digest,content}]}`. |
| `concorde-review-result@1` | A `stage_inputs` entry: produced by code review, consumed by the repair `tasks`/`implement` iteration | The same value published in `concorde-review-response@1.reviews` (see Review types below), re-verified from its stored artifact before reuse; only accompanies a dev-loop's bounded `review_code -> tasks` repair round. |

Unknown fields, an incompatible `type_id`, an unsupported `schema_version`, and an unsafe or
non-project-relative path are all rejected before any agent launches, with the `TypedDataError`
codes named below. The target interface versions are specified here. Legacy exports do not yet include the new
context forms; package/schema alignment checks must be migrated before these handoffs can run.
The existing validation command cannot certify Profile 12 support.

| Error code | Meaning |
| --- | --- |
| `already_initialized` | The project is already configured; use `configure` to change settings instead of initializing again. |
| `ambiguous_route` | Main routing found more than one owning target for a capability that requires exactly one; route cross-target work through a Module instead. |
| `cancelled` | `CapabilityExecutionError.outcome` when the injected runner raised `KeyboardInterrupt`; the host maps this to the `execution_cancelled` result error code. |
| `child_blocked` | A composed child capability returned a blocked or otherwise non-successful outcome and stopped the composing capability. |
| `check_sandbox_unavailable` | Harness could not enforce the configured check's read-only filesystem boundary or launch it inside that boundary; diagnostics remain in the host log and readiness is blocked. |
| `configuration_mismatch` | The invocation's, a child's, or a native launch's configuration differs from the initialized project settings or the host's own snapshot. |
| `context_limit` | Main discovery exceeded its bounded expansion-step limit. |
| `delivery_in_progress` | The candidate is already being delivered; resume delivery from either participating worktree instead of starting a new mutation. |
| `delivery_session_required` | The current session is not recognized as the change's selected source or destination worktree. |
| `invalid_assessment` | A returned context assessment is internally inconsistent: only a Spec-incomplete outcome may carry structured gaps. |
| `invalid_context` | A resolved context is structurally invalid, for example discovery without nonempty, unique, ordered targets. |
| `invalid_phase` | The requested context or discovery phase is not one this host supports. |
| `missing_source` | A required regular file named by the registry or by a resolved context is missing from the project. |
| `primary_session_required` | Final primary merging requires the primary owning outer session. |
| `delivery_required` | Final primary merging requires a completed staged delivery; finish staging or cleanup first. |
| `detached_primary` | The destination (primary) worktree has no attached branch to deliver onto. |
| `detached_worktree` | A change worktree has no attached branch. |
| `dirty_primary` | Final primary merging is blocked by local changes; default branch delivery preserves them and may proceed. |
| `execution_cancelled` | `run_capability` caught a `CapabilityExecutionError` with `outcome == "cancelled"`; the change status becomes `cancelled` and the candidate is preserved. |
| `execution_limit` | `run_capability` caught a `CapabilityExecutionError` with `outcome == "limit_exhausted"`; the change status becomes `limit_exhausted` and the candidate is preserved. |
| `failed_merge_checks` | The verified merge of the candidate into the destination branch failed its configured checks. |
| `incompatible_contracts` | Shared contracts between participating components disagree and must be reconciled before implementation. |
| `incompatible_handoff` | A returned identity (context, target, gap, route, or configuration) does not match what the host issued or expects. |
| `incomplete_change` | Delivery was requested before every authored task for the change was complete. |
| `incomplete_tasks` | Implementation did not report every exact task as complete. |
| `invalid_agent_binding` | A named Agent's definition, Harness reference, or Constraints is inconsistent with its registered Harness or the current build manifest. |
| `invalid_completion` | An agent's or main's returned completion is internally inconsistent with its own declared context or outcome. |
| `invalid_delivery` | A delivery receipt has an invalid or mismatched identity. |
| `invalid_entry_target` | The registry's `entry_target` is not a Module, so main discovery cannot start there. |
| `invalid_field` | A TypedValue field fails its JSON Schema: wrong type or format, a missing or unknown field, non-unique items, or a mode/action-specific requirement. |
| `invalid_focus` | A focus hint was given without its required target hint. |
| `invalid_input` | A request's fields are structurally invalid for the requested action (for example, a missing name or configuration on initialization). |
| `invalid_json` | stdin is not parseable JSON. |
| `invalid_merge` | The verified merge of the candidate failed Spec validation. |
| `invalid_proposal` | A topology design or proposal would change the project's own identity, or is otherwise not acceptable. |
| `invalid_spec` | An authored Spec document's `concorde-document` context declaration is invalid. |
| `invalid_worktree_state` | `.concorde/worktree.json` has an invalid identity or schema. |
| `legacy_attempt` | The worktree still carries an unsupported legacy `.concorde/attempts/` state that must be removed before it can be adopted. |
| `limit_exhausted` | `CapabilityExecutionError.outcome` when the injected runner raised `subprocess.TimeoutExpired`; the host maps this to the `execution_limit` result error code. |
| `merge_conflict` | Integration conflicts with the primary branch. Resolve and revalidate in the candidate worktree, or a new candidate if delivery already removed the source. |
| `missing_change` | A requested existing change or task authoring has no managed change in the current worktree. |
| `missing_plan` | Task authoring was requested without an authored plan. |
| `missing_tasks` | Implementation was requested without authored tasks. |
| `permission_denied` | A request or worker tried to act outside its granted target, Module composition/dependencies, or write scope. |
| `protocol_mismatch` | The project's pinned Protocol binding does not match the installed Protocol assets, or a bound asset has changed. |
| `review_required` | A required Spec or code review is missing, incomplete, blocking, or stale for the current revision. |
| `spec_incomplete` | The current task still has open, unresolved Spec gaps. |
| `stale_build` | The rendered build is missing, or a recorded source has changed since the last `python -m concorde build`. |
| `stale_context` | The frozen context capsule no longer matches the repository: its registry, Protocol, or document bytes changed. |
| `stale_delivery` | A recorded delivery is no longer on its target branch, or has changed since it was recorded. |
| `stale_evidence` | Recorded validation, review, or completion evidence no longer matches the current candidate bytes. |
| `stale_proposal` | A topology proposal's registry or Protocol base has changed since it was produced. |
| `stale_reference` | An artifact reference's declared path or digest does not match the file actually on disk. |
| `state_persistence_failed` | The host could not persist change progress after recording an otherwise-final outcome. |
| `studio_run_failed` | A Studio-driven capability run did not complete successfully. |
| `studio_transport_failed` | The Studio client could not reach or exchange messages with the Studio server. |
| `undeclared_capability` | A capability tried to compose another capability that its own module does not declare in `USES`. |
| `unknown_agent` | The named Agent has no matching `agents/<name>/` definition. |
| `unknown_capability` | The named capability is not registered, or a parent capability referenced a capability that does not exist. |
| `unknown_change` | Delivery named a `change_id` with no registered live worktree or delivery receipt. |
| `unknown_target` | The requested Spec target ID is not registered. |
| `unknown_type` | A TypedValue's `type_id` does not name a schema the wire module recognizes. |
| `unsafe_path` | A path escapes the project root, aliases a control path, or crosses a symlink. |
| `unsupported_profile` | The registry declares a profile older than the Module model this runtime implements; migrate it explicitly. |
| `unsupported_target` | The selected target has no registered implementation for the requested code-owning behavior. |
| `unsupported_version` | The invocation's `schema_version` is not the one this host implements. |
| `use_proposal` | `describe-policy` cannot preview `init`/`configure`; use their deterministic proposal flow instead. |
| `workspace_mismatch` | The current worktree, branch, or worktree topology does not match what the requested capability or transition requires, including an entry process whose working directory lies inside a Git worktree but not at its root. |
| `worktree_handoff_required` | A mutating request in the primary worktree needs a new agent session opened in the linked worktree the host just prepared. |
| `execution_failed` | The host caught an exception outside the named Spec/typed-data/build error vocabulary. |

## Main routing view
Select `module.harness` for context resolution, permission compilation, typed-value admission,
Agent binding and native execution. Select `module.spec` for registry selection, structural
validation and initialization. Select `module.distribution` for build, installation and runtime
provisioning. Select `module.reflections` for recorded feedback and gaps. The main coordinator
may use these stable IDs to route a worker but may not expand their Module targets.

## Worktree awareness
A directly authored Spec or manual candidate can run explicit validation without inventing a plan
or an attempt. With no authored target plans, validation runs every configured project check and
stores root validation evidence against the exact candidate tree. Existing authored plans and tasks
still require completion; this path cannot bypass unfinished work. Deterministic readiness does not
claim universal semantic completeness. The primary delivery request accepts the verified candidate.

Delivery validates its actual integration result in a temporary detached worktree. When that tree
contains `concorde.json`, it is a Concorde package checkout: the host calls `write_build` on that
checkout's own merged sources before Spec/package validation and configured checks. Untracked
build outputs do not alter the deliverable tree. Build or validation failure preserves both
participants and prevents the primary update; no stale-output gate is disabled or bypassed.

The primary worktree maintains `.concorde/worktrees.json` from Git's live worktree inventory, including
unmanaged worktrees, and from each linked worktree's own `.concorde/worktree.json`, the only file of
another worktree the host reads. Each entry has its path, branch, head, managed/locked status and, when available,
change_id, owning target, task summary, phase and status. A secondary worktree registers its own
`.concorde/worktree.json` and receives managed AGENTS.md/CLAUDE.md instructions to treat partial work as
a candidate and request delivery from either participating worktree. Host updates to these control files do not
change Spec authority or grant agent writes outside the selected target.

Every discovery and worker snapshot admits `workspace` lifecycle metadata. Main can answer a pure
workspace-status question directly from this metadata; target-behavior answers still use separate
coordinator. The current workspace identity and status are rechecked after a stage. Other live worktree
summaries are frozen observations and their progress does not invalidate unrelated main cognition.
A change's `status` may also become `cancelled` or `limit_exhausted` after an executor outcome of
the same name (`execution_cancelled`/`execution_limit`), distinguishing a cancelled or time-limited
agent process from an ordinary `blocked`/`failed` outcome; the candidate is preserved for repair or
resumption in every case. A development loop stopping for a necessary Spec gap, or for blocking
code-review feedback that repeats unchanged across a bounded repair attempt, records status
`waiting` instead of the generic `blocked`: both name a concrete point where a human decision or a
Spec/code change is needed before the loop can usefully resume.

## Configured check execution

Only the host admits configured argv, expands an initial `{python}` to its interpreter, and calls
Harness's `execute_check(project_root, argv, timeout=..., environment=...)`. The supplied environment
retains the host environment and sets `PYTHONPATH` to the package's `src`; Harness installs it only
inside the sandbox and directs temporary/cache/report paths to independent external scratch.
Checks may read project files. The operating system denies creation, modification, movement and
deletion by the check and its descendants, including transient writes that are later restored.
The rule covers listed and unlisted files, ignored caches, `.concorde/runs` and lifecycle records.

Harness returns byte `stdout`, byte `stderr`, integer `returncode` and boolean `timed_out` after
terminating the check's descendants. Development alone writes `stdout + b"\n" + stderr` to
`.concorde/runs/<invocation_id>/<check_id>.log`. No project log handle or lifecycle write grant enters
the sandbox. Public evidence contains exactly `check_id`, `target_id`, `status` (`passed`, `failed`
or `timeout`), `exit_code`, `source_digest` and `log_digest`; raw output remains private. Timeout
uses exit code -1. Other exit codes retain Harness's shell encoding; zero is passed and nonzero
is failed. Disposable report files stay outside the project and are removed after execution.

An unavailable backend, unsupported OS, failed sandbox setup or failed isolated launch raises
Harness's `CheckSandboxError`, carrying private diagnostic streams. The host saves that diagnostic
log, then raises `SpecError/check_sandbox_unavailable` naming the check and host log path, without
including raw diagnostics or recording passing evidence. It never runs a less restricted fallback.
Linux currently requires a system bubblewrap and working namespace/pidfd support; no other OS
backend is implemented. There is no task/configuration option to disable enforcement. Project cache
or report writers must migrate to the issued scratch paths, while source-formatting writes belong
to implementation. Finer read, network and credential policy is outside this interface's scope.

Before and after execution, check freshness covers registered commands and explicit inputs plus
the selected Module's implementation. The execution-policy identity `project-read-only-v1` also
participates in the digest, invalidating evidence from the former unrestricted runner. Candidate
tree and affected-Module revision comparisons remain additional defenses against concurrent
external changes; they do not supply the write boundary or claim semantic completeness.

## Independent review contract
`concorde-review` is a public global capability requiring task and review_mode=spec|code, with
optional target/focus routing hints, constraints and current-worktree change_id. A new standalone
request uses Spec-only coordinator discovery to select one owning Module, then starts a fresh
read-only reviewer. A composing capability may supply its trusted bound target without repeating
discovery; a current-change resumption supplies both target_id and change_id. The public launcher
and Studio admit this capability directly. Review runs in the current worktree without creating
a development change or requiring a Reflection record. The host may persist reports and existing
change evidence, but reviewers receive no project write authority.
Spec mode uses the complete admitted owned and directly referenced Specs, Protocol/kind rules, task and scoped changes to any document included in that context. Code mode uses those
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

Private `concorde-review-stage-context@2` contains a full context snapshot and a
`concorde-review-input@1` with review_mode, input_digest, revision and changes. Each change is
`{path, patch}`; binary changes carry only digest markers. The revision has spec_digest,
nullable implementation_digest, nullable baseline and nullable head. spec_digest binds the selected
target descriptor, ownership, explicit references, all inclusion reasons, pinned Protocol and ordered
complete document byte digests, including referenced provider documents. Code mode additionally
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

| Review state | Skill outcome and progression |
|---|---|
| no_findings with nonempty coverage | completed; bounded review succeeded |
| findings, all advisory and no gaps | completed; findings retained for the consumer |
| concrete necessary gaps | spec_incomplete; dependent steps pause |
| blocking code findings without gaps | conflicting; dependent steps pause |
| incomplete coverage, invalid result or process failure | failed; an incomplete report, never a clean result |
| describe-policy | described with not_run; no execution or persistence |
| run_reviews=false | host records skipped; no reviewer runs |

Every mode and target uses a separate session. A Module with recorded component work can request
cross-target review: the host validates each Module's declared relationship, starts its own reviewer from
its recorded task and admitted collection, then aggregates only typed results. Spec review also
assesses the Module itself; code review never gives the Module code. A Module without recorded
component work returns unsupported for code review. During a development loop, the Module's initial
Spec review is local; component reviews occur in the coordinated component loops after reconciliation.

## Review gates, gap history and recovery
`concorde-dev-loop` resumption skips Spec authoring only after a host-accepted authoring result for
the same target, task, focus and constraints. Standalone review records, including failed or
unrelated reviews, cannot substitute for authoring. A completed Module still revisits its recorded
component coordination: stronger review requirements propagate before completed component work is
reused, and missing or stale component reviews run before readiness.

Standard development requires both reviews for a code-owning target (only Spec review for a Module).
`run_reviews` defaults to true and applies to both modes; `run_reviews=false` is the explicit opt-out.
Requirements and the exact review intent are saved per target in the existing worktree state; an
enabled requirement survives retries with run_reviews=false. Skips have separate records and never
satisfy a required gate. A standalone review with a different task/focus/constraints remains a run
artifact and cannot replace another intent's lifecycle-required review. Code review runs after checks
but before the single ready transition; a failed/incomplete/blocking review cannot be bypassed by
standalone validation or delivery.

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

Canonical interfaces are supplied by the Module references in Development's registration. These
links state local uses and obligations; providers own the definitions, schemas and error semantics.

| Provider definition | Development use and obligation |
| --- | --- |
| [Registry and resolution](../spec/registry.md), [values](../spec/values.md) | Select the unique task owner, freeze its complete resolved context, reconstruct after changes and stop on failed admission. |
| [Context](../harness/context.md#contract.context.selection) | Bind every stage to the current task and exact snapshot; handle gaps and stale-context failures before progressing. |
| [Runtime values](../harness/runtime-values.md) and [permissions](../harness/permissions.md) | Compile bounded role permissions and preserve empty reviewer writes; never widen a policy after rejection. |
| [Execution](../harness/execution.md) | Require the bound fresh process and matching completion; stop on failure and retain private evidence. |
| [Typed values](../harness/typed-values.md) | Validate every handoff before state mutation; never use raw logs or code as later Spec-only input. |
| [Build](../distribution/build.md) and [installation](../distribution/installation.md) | Require fresh projections and the pinned Protocol assets before launch; a mismatch blocks the invocation. |
| [Validation](../spec/structure.md) | Require structural evidence and separately configured checks; never interpret it as semantic proof. |
| [Reflection interface](../reflections/interfaces.md) | Preserve returned gap/Reflection identities; only explicitly selected records may start a transition. |

Configuration loading remains Development-owned: `load_configuration(project_root: str|Path)`
returns the initialized configuration TypedValue. Ordinary invocations and child stages must equal
that snapshot; mismatch stops the transition without fallback or expanded authority.

### File transactions

- File transactions (this Module's own `entity.development.file-transactions`, also listed by Spec, Reflections and Views): `file_change(root: Path, path: str, content: str) ->
  {path,before_digest,content}` captures current bytes (null digest for new files).
  `apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]` requires
  nonempty unique allowed paths, UTF-8 replacement text and exact before digests. It rechecks before
  writes, optionally calls the zero-argument verifier, and restores written bytes on failure.
  Stale or foreign proposals raise SpecError; no partial transaction is reported successful.

### Gap capture

The [Reflection interface](../reflections/interfaces.md) owns status/record-gaps semantics.
Development passes host-bound gap provenance, retains history and treats capture as a link to
feedback, never as resolution or approval to implement.

## Diagrams as part of registered documents
Relationships diagrams in this project are inline Mermaid flowchart fences inside a registered
Markdown document, with `accTitle` and `accDescr` accessible text stated beside the fence. A
Module's main diagram, in its `module.md` Relationships subsection, describes its principal entities
and directed relationships; further diagrams may appear in other registered documents. The entire
containing Markdown document is the diagram's only authored source.

The diagram's bytes already occur in `documents` and participate in document,
revision and context digests; no separate diagram-source pool or result field exists. Authors
return a changed fence as part of the changed `documents` entry that contains it. Shared Markdown
changes are authored once by the sole owner and reviewed for all affected direct context consumers; non-author roles
cannot replace these sources; and rendered SVG/HTML is never a cognitive input or another
authority.

Spec review receives scoped Markdown changes, including any diagram fence they touch, and
attributes findings to that registered document and owning Module. A blocked author returns no
replacements. A prepared application binds the complete accepted document set and every
before-digest. Syntax and publication failures remain distinct from an incomplete or contradictory
behavioral contract. Publication renders the same Mermaid source as part of the Markdown page.

## Reusable implementation context and evidence
Each Module's entities carry its file bindings directly in its own Spec, as exact files or as
directory prefixes that bind every regular file below them; the registry's `files` field mirrors
their union entry for entry, and together they determine the Module's implementation context. A
declared entry that does not yet exist, a file or a whole directory, is marked `pending` on its
entity instead of receiving a separate stub document; delivery removes that marker once it exists.
Code writers may create or change the files their Module's own entries bind, including new files
below a listed directory, but cannot change entity identity, membership, the registry, or a Module
Spec document. Non-code authors never read those files' contents, only the declared entries and
bound names through the entity declarations they can already see.

Implementation revisions hash each Module's declared entries together with the current digests of
the files they bind. Validation derives every listing Module from the reverse index, in which a
directory entry covers every path below it, runs their configured checks and records each
Module's contract and implementation revisions. Code review uses a separate Module-only contract
context for each consumer plus its authorized code. Required peer review artifacts are retained
with their own intent; later source, Spec or membership changes invalidate those results. A single
consumer's completion never establishes compatibility for every Module that lists the same shared
file.

## Canonical review-result value

The [review-result interface](review-result.md) is the single definition of the public review
record. Harness explicitly references that document for repair stage admission. Development
checks task intent, evidence currentness and permitted repair transitions before supplying it.

## Reference changes and implementation status

Before review/readiness, compute affected Spec consumers from the union of old and candidate
one-level contexts. A provider document edit, ownership transfer, changed reference or changed
provider document inventory invalidates each affected context and dependent plan/review. Changed
code additionally uses the independent listing reverse index. A reference is never a code grant.
Review attribution follows the [canonical review-result interface](review-result.md). Development
routes a provider repair to its sole owner and retains the consumer's blocked-step evidence;
included-file read scope never grants authority to write the provider definition.

The current host, wire exports, topology authoring agreement, permission projection and evidence
invalidation still implement the old membership model. Version-2 context wrappers, owner-authored
shared-interface changes and consumer-specific checks are required implementation migration work.
No lifecycle readiness or delivery is established by this documentation maintenance.
