# Development host boundary

### Capability execution boundary

A Capability is a State-based LangGraph node under the Capability and Harness contract. Each
registered entry declares its State, USES and optional model execution profile. Existing host
adapters additionally retain versioned request/response transport contracts; model-only nodes do
not acquire new wire envelopes. Rendered public Skills expose exactly one public Capability.
Non-public Capabilities have no Skill or direct launcher entry. Every external request passes
through this host. The capability registry is a member of this complete Spec; exact wire
schemas are code, exported by the build for runtime/API use, and this document states
their promises.

Executable entry: `python3 scripts/run-capability.py <skill-name>`, no task command-line arguments.
A name that is not a Skill is refused with `unknown_capability`. stdin is exactly one JSON object
`concorde-capability-invocation@3` with fields type_id, schema_version=3, capability_id (the Skill's
name), mode=execute|describe-policy, configuration and input. Maximum input is 1 MiB. Schema 2
invocations are rejected with `unsupported_version`. configuration is a
`concorde-capability-configuration@1` TypedValue or null for the initialized host settings; input is
the capability's named request TypedValue. A TypedValue is {type_id,schema_version:1,data}; unknown
fields and versions fail admission. Configuration is the Pi worker model selection: an optional
default model, thinking level and timeout and optional per-worker and per-child overrides. It is
stored at initialization under `capability_configuration` and required to match host settings for
ordinary invocations. Caller input never substitutes for permission authority.

stdout is `concorde-capability-result@3` with capability_id, invocation_id, mode, status
succeeded|blocked|failed|described, workspace (null or host-supplied worktree metadata), output
(typed response or null) and errors [{code,field,message}]. Exit 0 means succeeded/described; 3 means
blocked/failed. Describe-policy does not launch agents or mutate project state; policy descriptions
go to stderr. Before executing or describing a top-level model-backed capability, the host
verifies the build manifest and refuses a stale build with `stale_build`. The deterministic
capabilities `concorde-init`, `concorde-configure`, `concorde-validate` and
`concorde-deliver` are exempt from this entry check because they launch no workers and consume no
generated worker instructions. Loading an Agent independently verifies build freshness before
trusting its generated binding. The deterministic-entry exception does not waive Protocol, input,
permission, validation or delivery-evidence checks; see the canonical
[build admission scenario](../distribution/scenarios.md#scenario.distribution.build-stale-blocks-execution).

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
use a distinct read-only implementation role with only the current listed implementation files. Every
worker is a fresh Pi process whose tool calls are gated to its grant; no worker receives network or
credential effects, and writes are restricted by phase. Executor outcomes must match invocation,
binding and context identities. No ambient conversation or predecessor transcript is admitted.

Query and route semantics belong to [Query and Routing](../query-routing/query-and-routing.md).
Topology actions of the same public main entry belong to [Topology](../topology/topology.md).
These are semantic siblings using the existing shared main adapter; they add no launcher.

No Skill returns context manifests; context resolution is host-internal and
`describe-policy` mode already previews the exact grants a capability would receive without
launching a worker or mutating project state. Each previewed stage's description also names the
bound worker (`agent`, `agent_binding_digest`, `profile_digest`, `instructions_digest`, `workspace`,
`tools`, `children`) and its resolved `model`, `thinking` and `timeout_seconds`, so a caller can
audit which worker definition and model a launch would use without reading its rendered
instructions. Complete cognitive snapshots never cross
the Skill result boundary.

Provider contracts are [Spec Authoring](../spec-authoring/authoring.md),
[Planning](../planning/plan.md), [Tasks](../planning/tasks.md),
[Implementation](../implementation/implementation.md), [Review](../review/review.md),
[Validation](../validation/validation.md) and [Delivery](../delivery/delivery.md).
The [Specification Flow](../specify-loop/specify-loop.md) and
[Development Flow](../dev-loop/development.md) own ordering and lifecycle policy.
The host rechecks registry, context and initialized configuration after every stage.

The canonical [context selection agreement](../harness/contracts.md#contract.context.selection)
is included through Development's Module reference to Harness.

<a id="participation.document.development.interfaces.1"></a>

**Interface participation.** This Module has the required role for `contract.context.selection` version 3 with `module.harness`.

**When this applies.** Before assessment, planning, authoring or review for a selected Module.

**Relied-upon guarantee.** [Selection](../harness/contracts.md#contract.context.selection) determines the complete admitted contract and its original owners.

**Local obligation.** Supply the explicit Module and task; stop dependent transitions on gaps or stale context, and never treat included provider definitions as writable local Specs.

Each reported Spec gap carries host-bound target_id and context_id provenance. A Module coordinator
retains that provenance when a component stage is blocked, so callers can author the correct local
Spec before retrying. Agent-supplied mismatched gap provenance is rejected.

### Wire contracts

Every TypedValue is `{type_id, schema_version, data}`; `schema_version` is pinned per type below and
`data` must satisfy that type's JSON Schema. The invocation envelope wraps every request and
response; the fourteen capability request/response pairs carry each capability's own task and
result; the remaining types are internal handoffs, review records, topology artifacts, the project
proposal and the stage-input artifacts that pass between stages inside one capability.

#### Invocation envelope

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-capability-invocation@3` | Every request, on stdin | `{type_id, schema_version: 3, capability_id, mode: execute\|describe-policy, configuration, input}`. `capability_id` must name a Skill; a non-public or unknown name is refused with `unknown_capability`. `configuration` is a `concorde-capability-configuration@1` TypedValue or null (falls back to the initialized project settings); `input` is the named capability's own request TypedValue. Any other `schema_version` is refused with `unsupported_version`. |
| `concorde-capability-result@3` | Every response, on stdout | `{type_id, schema_version: 3, capability_id, invocation_id, mode, status: succeeded\|blocked\|failed\|described, workspace, output, errors: [{code,field,message}]}`. `output` is the named capability's own response TypedValue or null; `workspace` is null or host-supplied worktree metadata. Exit code 0 means `succeeded`/`described`; 3 means `blocked`/`failed`. |
| `concorde-capability-configuration@1` | The invocation's `configuration` field, and `concorde-configure-request@1`/`-response@1` | `{model?, thinking?: off\|minimal\|low\|medium\|high\|xhigh\|max, timeout_seconds?, workers?: {<worker> or <worker>/<child>: {model?, thinking?, timeout_seconds?}}}`; `model` is Pi's `provider/id`. The top-level values are the project default; a worker entry overrides them for one worker and a child entry for one worker child, which inherits its worker's entry (see [the worker selection scenario](../harness/scenarios.md#scenario.harness.worker-selection)). An absent model or thinking level keeps Pi's default and an absent timeout the worker profile's. A key naming no worker or worker child, a timeout on a child, a nonpositive timeout or a model without a provider is rejected. Stored at initialization under `.concorde/config.json`'s `capability_configuration` key; an invocation or child stage whose configuration differs from that stored snapshot stops with `configuration_mismatch`. |

#### Capability requests and responses

Common request task fields (named once, not repeated per row): `target_id` (required for every
bound Module request; an optional routing hint for `main`, `dev-loop`, `specify-loop` and `review`), `task`,
`focus_id` (a candidate scenario ID), `constraints`, `change_id`. Common response fields (present in every capability response
except `configure`, which replaces them): `target_id`, `focus_id`, `change_id`, `context_id`,
`outcome`, `answer`, `artifacts`, `blockers`, `checks`, `completed_capabilities`. A blocker contains
an immutable Issue receipt plus its task-local blocked_step, never a second copy of the problem.

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-main-request@1` / `concorde-main-response@2` | main | Every request field is optional at the wire level. Request adds `action` (ask\|design-topology\|accept-topology\|apply-topology, default ask), `topology_proposal` (a `concorde-topology-proposal@1` TypedValue, required for accept-topology) and `application` (an ArtifactRef, required for apply-topology). Response adds `entry_target`, `discovered_targets`, `routes`, nullable `topology_proposal`/`application`, `files` and `workspace`. |
| `concorde-specify-loop-request@1` / `concorde-specify-loop-response@2` | specify-loop | Only `task` is required. Optional target/focus hints, constraints, change_id, `specify` and `run_reviews` (both default true). The common response reports Spec completion or blockers with artifact references; it never reports implementation readiness. |
| `concorde-dev-loop-request@1` / `concorde-dev-loop-response@2` | dev-loop | Only `task` is required. Request adds optional `repair_task_scope:{tasks_digest: sha256}` for exact incomplete-list phase recovery, `specify` (default true; false skips Spec authoring) and `run_reviews` (default true; false records an explicit per-mode skip). Response is the common shape only. |
| `concorde-issues-request@1` / `concorde-issues-response@1` | issues | Select list, show, report, reopen or solve. Show/reopen/solve require one issue_id; report requires a target and classified report. Optional expected_revision rejects stale selection. Response adds complete Issue records and nullable decision. [Canonical operation semantics](../issues/interfaces.md). |
| `concorde-init-request@1` / `concorde-init-response@1` | init | Requires only `action` (propose\|apply); adds optional `name`, `target_id`, `configuration` and `proposal` (a `concorde-project-proposal@1` TypedValue). Response replaces the common shape with `status` (proposed\|applied), a nullable `proposal` and `files`. |
| `concorde-configure-request@1` / `concorde-configure-response@1` | configure | Requires `configuration`. Response requires `configuration` and `status: "applied"`; the only capability whose response does not use the common stage shape. |
| `concorde-validate-request@1` / `concorde-validate-response@2` | validate | Requires `target_id` and `task`; adds optional `run_checks`. Response is the common shape only. |
| `concorde-deliver-request@1` / `concorde-deliver-response@2` | deliver | Requires only `change_id`; adds optional `target_id`, `task`, `focus_id`, `constraints`, `keep_worktree` and `merge_primary`. Response is the common shape only. |
| `concorde-specify-request@1` / `concorde-specify-response@2` | specify (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-review-request@1` / `concorde-review-response@2` | review | Requires `task` and `review_mode` (spec\|code); optional target/focus are routing hints for a new standalone task. A composing capability or current-change resumption supplies the bound target. Response adds `reviews` (`concorde-review-result@2` TypedValues). |
| `concorde-context-solve-request@1` / `concorde-context-solve-response@2` | context-solve (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-plan-request@1` / `concorde-plan-response@2` | plan (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-tasks-request@1` / `concorde-tasks-response@2` | tasks (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-implement-request@1` / `concorde-implement-response@2` | implement (stage) | Requires `target_id` and `task`. Response is the common shape only. |

#### Stage handoffs

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-context-snapshot@6` | Every bound worker invocation's frozen input | [Canonical snapshot](../harness/contracts.md#context-context-snapshot-resolution); preserve its resolution provenance and reject stale inputs. |
| `concorde-agent-stage-context@4` | Host to worker, wrapping the launch | `{snapshot: concorde-context-snapshot@6, change_id, expected_artifacts}`. |
| `concorde-agent-stage-result@2` | Worker to host, the completion | `{context_id, outcome, answer, blockers, documents, plan, tasks, issue_decision?}`; `documents`/`plan`/`tasks`/`issue_decision` are populated only by the phase that produces them. A mismatched `context_id` is rejected as `incompatible_handoff`. |

#### Review types

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-review-input@1` | Host-produced, inside the review stage context | `{review_mode, input_digest, revision, changes: [{path,patch}]}`; binds the exact Spec/code revision under review. |
| `concorde-review-stage-context@4` | Host to reviewer, the launch | `{snapshot: concorde-context-snapshot@6, review: concorde-review-input@1}`. |
| `concorde-review-stage-result@2` | Reviewer to host, the completion | `{context_id, input_digest, review_mode, status: no_findings\|findings\|incomplete, representative_tasks, issues, answer}`. |
| `concorde-review-result@2` | Published in `concorde-review-response@2.reviews` | The stage result plus `target_id`, `focus_id`, `revision`, a nullable `context_id`, `status` extended with skipped\|not_run, and `semantic_completeness: "not_proven"`. |

#### Topology types

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-discovery-context@5` | Host to discovery worker | [Canonical discovery context](../harness/contracts.md#context-global-spec-context-assembly); only explicit selections may expand discovery. |
| `concorde-main-stage-context@4` | Wraps the discovery context for launch | `{snapshot: concorde-discovery-context@5}`. |
| `concorde-main-stage-result@2` | Discovery worker to host, the completion | `{context_id, outcome, answer, expand_targets, routes, blockers, topology_design (nullable)}`. |
| `concorde-topology-design@1` | design-topology's output, embedded in the main stage result | `{summary, registry, spec_tasks (nonempty), migration_constraints, acceptance (nonempty)}`. |
| `concorde-topology-proposal@1` | design-topology's response, and accept-topology's request | `{proposal_id, base_registry_digest, protocol_binding, context_id, discovered_targets (nonempty), task, constraints, target_hint, focus_hint, design: concorde-topology-design@1, workspace}`; a stale `base_registry_digest` or `protocol_binding` is rejected as `stale_proposal`. |
| `concorde-topology-author-context@4` | Host to target-local Spec author, during accept-topology | `{context_id, base_registry_digest, target, task, protocol_binding, protocol, candidate_references, spec_resolution, instructions, workspace}`. |
| `concorde-topology-author-result@2` | Author to host, the completion | `{context_id, target_id, outcome, answer, blockers, documents}`. |
| `concorde-topology-application@1` | Host-private, produced by accept-topology and consumed by apply-topology | `{application_id, topology_proposal: concorde-topology-proposal@1, base_registry_digest, protocol_binding, files (nonempty)}`; the public response exposes only its ArtifactRef, never these bytes. |

The canonical [discovery record](../harness/contracts.md#context-global-spec-context-assembly) defines
deduplicated source pools and per-Module provenance. Development retains it unchanged in each
handoff and checks currentness before using its result; it does not define a second record shape.
The topology-author context's `candidate_references` is the candidate Module's explicit references;
`spec_resolution` is its candidate one-level resolution. Providers are read-only unless the author
is their candidate owner. Ownership transfers, additions and removals bind both prior and candidate
descriptors and all affected consumers in the prepared application.

For ask, the answerer may expand explicitly selected contexts or complete directly from their
original contents with no routes. Other routed capabilities preserve one target task and its
constraints. Spec gaps identify an admitted Module and the current combined context identity.
Old reading-worker results and the synthesis phase are not accepted; clients must use the current
build-bound schemas and instructions. Existing Protocol bindings remain pinned until explicitly
updated; a mismatched package/context is rejected instead of reinterpreted.

#### Project proposal

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-project-proposal@1` | `concorde-init-request@1.proposal` and `-response@1.proposal` | `{action: "initialize", base_digest (nullable), files: [{path, before_digest (nullable), content}]}`. |

#### Issue reporting values

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-issue-report@1` | Worker reporting tool to the host | [Classified observation](../issues/issues.md#store-boundary), without caller-supplied provenance or a flow-control effect. |
| `concorde-issue-receipt@1` | Host to the reporting worker | Immutable `{issue_id, report_id, path}` identity for the exact accepted observation; the tool additionally returns the current record revision for a subsequent append. |

#### Stage-input artifacts

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-plan-artifact@1` | A `stage_inputs` entry: produced by plan, consumed by tasks | `{plan}`. |
| `concorde-task-identity-constraints@1` | Host to every fresh task author, including after replanning | `{reserved_task_ids: list[nonblank str]}`; required, sorted and unique, possibly empty. Includes every retained historical ID and the current list for scope or code-review repair. New tasks must not reuse these identities; collisions report the conflicting IDs without rewriting output or history. No software obligations or code contents. |
| `concorde-implementation-task@1` | A `stage_inputs` entry: produced by tasks, consumed by implement | `{plan, tasks: [{id,target_id,description,acceptance,complete}]}`; implement must return every task with the same identity, marked complete only when its acceptance is met. |
| `concorde-task-scope-feedback@1` | Host to fresh task author only | `{tasks_digest: sha256, reason: "implementation_boundary"}`; fixed semantic feedback preserves software acceptance while separating implementation from later Host validation, review and authorized outer-session commit. No code or raw logs. |
| `concorde-issue-selection@1` | Host to Issue solver only | Selected issue_id/revision, problem/type, bounded host feedback/verification and explicitly admitted duplicate candidates. No code, logs or predecessor conversation. |
| `concorde-issue-intent@1` | Host to ordinary development stages | `{intent}` carries only the selected intended behavior; it never widens a file grant. |
| `concorde-issue-context@1` | Host to admitted tasks/implementation repair | Selected immutable receipts and their contract-level description, impact and basis. It supplies meaning for the exact review references without exposing the whole Issue history. |
| `concorde-review-result@2` | A `stage_inputs` entry: produced by code review, consumed by the repair `tasks`/`implement` iteration | The same value published in `concorde-review-response@2.reviews` (see Review types below), re-verified from its stored artifact before reuse; only accompanies a dev-loop's bounded `review_code -> tasks` repair round. |

Unknown fields, an incompatible `type_id`, an unsupported `schema_version`, and an unsafe or
non-project-relative path are all rejected before any agent launches, with the `TypedDataError`
codes named below. Exported schemas implement the versions specified here, including the version-3
context forms; package/schema alignment checks verify those identities.

| Error code | Meaning |
| --- | --- |
| `already_initialized` | The project is already configured; use `configure` to change settings instead of initializing again. |
| `closed_issue` | Another observation requires reopening the closed Issue first. |
| `invalid_issue` | An Issue report, record, receipt or disposition violates its closed shape or history invariants. |
| `issue_key_conflict` | An invocation reused a report key with different content; the original observation is preserved. |
| `stale_issue` | Selected Issue bytes or an immutable observation no longer match the requested operation. |
| `unknown_issue` | The selected Issue does not exist in this worktree. |
| `ambiguous_route` | Main routing found more than one owning target for a capability that requires exactly one; route cross-target work through a Module instead. |
| `cancelled` | `CapabilityExecutionError.outcome` when the host interrupted a running worker; the host maps this to the `execution_cancelled` result error code. |
| `child_blocked` | A composed child capability returned a blocked or otherwise non-successful outcome and stopped the composing capability. |
| `check_sandbox_unavailable` | Harness could not enforce the configured check's read-only filesystem boundary or launch it inside that boundary; diagnostics remain in the host log and readiness is blocked. |
| `configuration_mismatch` | The invocation's or a child stage's configuration differs from the initialized project settings or the host's own snapshot. |
| `context_limit` | Main discovery exceeded its bounded expansion-step limit. |
| `delivery_in_progress` | The candidate is already being delivered; resume delivery from either participating worktree instead of starting a new mutation. |
| `delivery_session_required` | The current session is not recognized as the change's selected source or destination worktree. |
| `invalid_assessment` | A returned context assessment is internally inconsistent: only a Spec-incomplete outcome may carry structured gaps. |
| `invalid_context` | A resolved context is structurally invalid, for example discovery without nonempty, unique, ordered targets. |
| `invalid_phase` | The requested context or discovery phase is not one this host supports. |
| `missing_source` | A required regular file named by the registry or by a resolved context is missing from the project. |
| `not_installed` | Initialization or Protocol acceptance found no Protocol copy under `.concorde/protocol/`; Concorde has not been installed into the project, so run the installer first. |
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
| `invalid_agent_binding` | A named worker's profile, contract or child definitions are inconsistent with each other or with the current build manifest. |
| `invalid_completion` | A worker returned no single valid result, or its result is internally inconsistent with its own declared context or outcome. |
| `invalid_delivery` | A delivery receipt has an invalid or mismatched identity. |
| `invalid_entry_target` | The registry's `entry_target` is not a Module, so main discovery cannot start there. |
| `invalid_field` | A TypedValue field fails its JSON Schema: wrong type or format, a missing or unknown field, non-unique items, or a mode/action-specific requirement. |
| `invalid_owner` | A document has duplicate or inconsistent ownership or identity. |
| `invalid_reference` | An explicit reference is duplicate, self-directed, unknown or has the wrong kind. |
| `invalid_target` | A context query does not name a registered Module or scenario. |
| `invalid_focus` | A focus hint was given without its required target hint. |
| `invalid_input` | A request's fields are structurally invalid for the requested action (for example, a missing name or configuration on initialization). |
| `invalid_json` | stdin is not parseable JSON. |
| `invalid_merge` | The verified merge of the candidate failed Spec validation. |
| `invalid_proposal` | A topology design or proposal would change the project's own identity, or is otherwise not acceptable. |
| `invalid_spec` | An authored document unit's metadata, ownership or reading structure is invalid. |
| `invalid_worktree_state` | `.concorde/worktree.json` has an invalid identity or schema. |
| `legacy_attempt` | The worktree still carries an unsupported legacy `.concorde/attempts/` state that must be removed before it can be adopted. |
| `limit_exhausted` | `CapabilityExecutionError.outcome` when a worker ran past its timeout; the host maps this to the `execution_limit` result error code. |
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
| `unknown_agent` | The named worker has no matching `capabilities/<name>/` definition. |
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

### Main routing view

Select `module.harness` for context resolution, permission compilation, typed-value admission,
worker binding and Pi worker execution. Select `module.spec` for registry selection, structural
validation and initialization. Select `module.distribution` for build, installation and runtime
provisioning. Select `module.issues` for recorded feedback and gaps. The main router may use
these stable IDs to route a worker but may not expand their Module targets.

### Worktree awareness

One `.concorde/worktree.json` owns a managed change, root intent, target records, phase/status,
gaps and validation identity. Plans and auxiliary artifacts live under
`.concorde/work/<target-id>/`; there is no `.concorde/attempts/<change-id>/` lifecycle.
Components retain progress in the enclosing change. The selected flow determines transitions;
the common host owns persistence and rejects stale or incompatible state before reuse.
The primary worktree maintains `.concorde/worktrees.json` from Git's live worktree inventory, including
unmanaged worktrees, and from each linked worktree's own `.concorde/worktree.json`, the only file of
another worktree the host reads. Each entry has its path, branch, head, managed/locked status and, when available,
change_id, owning target, task summary, phase and status. A secondary worktree registers its own
`.concorde/worktree.json` and receives managed AGENTS.md/CLAUDE.md instructions to treat partial work as
a candidate and request delivery from either participating worktree. Host updates to these control files do not
change Spec authority or grant agent writes outside the selected target.

Every discovery and worker snapshot admits `workspace` lifecycle metadata. Main can answer a pure
workspace-status question directly from this metadata; target-behavior answers still use a separate
answerer invocation. The current workspace identity and status are rechecked after a stage. Other live worktree
summaries are frozen observations and their progress does not invalidate unrelated main cognition.

### Configured check execution

The canonical configured-check and evidence contract is owned by [Validation](../validation/validation.md).

### Independent review contract

The canonical contract is owned by [Review](../review/review.md).

### Review gates, gap history and recovery

[Development Flow](../dev-loop/development.md) owns its review gates; [Specification Flow](../specify-loop/specify-loop.md) owns Spec-only completion. Common attributed gap retention is defined in [Gap handling](review-and-gaps.md).

### Canonical review-result value

The [review-result interface](../review/review-result.md) is the single definition of the public review
record. Harness explicitly references that document for repair stage admission. The Development Flow, through the common host,
checks task intent, evidence currentness and permitted repair transitions before supplying it.

## Design

### Required orchestration model

The registered companion documents of the Harness Module define the Agent model (A1–A5) and the
Agent Flow and Loop model (G1–G4) this host composes. The Harness resolves worker definitions, their
`spec.md` sources, profiles and child definitions into a reproducible `AgentBinding` that every
worker invocation carries, and its executor verifies that binding before any process starts. This
Module MUST coordinate declared Flow transitions and bounded loops with attributed AI feedback and
explicit human decisions, and every capability Flow is a LangGraph graph whose nodes are
deterministic steps or worker invocations. The policy `role` and `agent` fields are the bound
worker's external name.

### Required collaborator interfaces

Canonical interfaces are supplied by the Module references in Development's registration. These
links state local uses and obligations; providers own the definitions, schemas and error semantics.

| Provider definition | Development use and obligation |
| --- | --- |
| [Registry and resolution](../spec/registry.md), [values](../spec/values.md) | Select the unique task owner, freeze its complete resolved context, reconstruct after changes and stop on failed admission. |
| [Context](../harness/contracts.md#contract.context.selection) | Bind every stage to the current task and exact snapshot; handle gaps and stale-context failures before progressing. |
| [Runtime values](../harness/runtime-values.md) and [permissions](../harness/permissions.md) | Compile bounded role permissions and preserve empty reviewer writes; never widen a policy after rejection. |
| [Execution](../harness/execution.md) | Require the bound fresh worker process and its single matching result; stop on failure and retain private evidence. |
| [Typed values](../harness/typed-values.md) | Validate every handoff before state mutation; never use raw logs or code as later Spec-only input. |
| [Build](../distribution/build.md) and [installation](../distribution/installation.md) | Require fresh projections and the pinned Protocol assets before launch; a mismatch blocks the invocation. |
| [Validation](../spec/structure.md) | Require structural evidence and separately configured checks; never interpret it as semantic proof. |
| [Issue interface](../issues/interfaces.md) | Preserve immutable report references and task-local blocker judgments; only explicit solving starts repair. |

Configuration loading remains Development-owned: `load_configuration(project_root: str|Path)`
returns the initialized configuration TypedValue. Ordinary invocations and child stages must equal
that snapshot; mismatch stops the transition without fallback or expanded authority.

#### File transactions

- File transactions (this Module's own `entity.development.file-transactions`, also listed by Spec, Issues and Views): `file_change(root: Path, path: str, content: str) ->
  {path,before_digest,content}` captures current bytes (null digest for new files).
  `apply_files(root: Path, changes: list[dict], allowed: set[str], *, verify=None) -> list[str]` requires
  nonempty unique allowed paths, UTF-8 replacement text and exact before digests. It rechecks before
  writes, optionally calls the zero-argument verifier, and restores written bytes on failure.
  Stale or foreign proposals raise SpecError; no partial transaction is reported successful.

#### Gap capture

The [Issue interface](../issues/interfaces.md) owns report, inspection, reopening and solving semantics.
Development passes host-bound gap provenance, retains history and treats capture as a link to
feedback, never as resolution or approval to implement.

### Diagrams as part of registered documents

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

### Reusable implementation context and evidence

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

### Reference changes and implementation status

Before review/readiness, compute affected Spec consumers from the union of old and candidate
one-level contexts. A provider document edit, ownership transfer, changed reference or changed
provider document inventory invalidates each affected context and dependent plan/review. Changed
code additionally uses the independent listing reverse index. A reference is never a code grant.
Review attribution follows the [canonical review-result interface](../review/review-result.md). Development
routes a provider repair to its sole owner and retains the consumer's blocked-step evidence;
included-file read scope never grants authority to write the provider definition.

The host uses version-3 context wrappers and owner-only author proposals. Candidate overlays receive
separate consumer compatibility reviews; plans, review records and readiness checks bind the complete
owner/reference resolution. Old and candidate consumers are retained for evidence rechecks.
No lifecycle readiness or delivery is established by this documentation maintenance.
