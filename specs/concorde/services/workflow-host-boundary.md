```concorde-document
{
  "id": "document.workflow-host.boundary",
  "targets": ["service.workflow-host"],
  "main_visible": true
}
```

# Agent orchestration host boundary

## Required orchestration model

The registered Shared Specs **Agents and Harnesses** and **Agent Graphs, Agent Loops and feedback**
define A1–A4 and G1–G4 for this Service. The host MUST resolve Python Agent definitions, Agent
`spec.md` sources, Harness configurations and effective constraints before execution. It MUST
coordinate declared Graph transitions and bounded loops with attributed AI feedback and explicit
human decisions. Agent definitions live under `agents/<name>/`; `resolve_agent` binds each one's
`spec.md`, registered Harness and Constraints into a reproducible `AgentBinding` that every
structured launch carries as `agent_binding_json`, and the executor's preflight independently
reconstructs and verifies that binding — including its declared-effects policy, compiled through a
narrowing `PolicyBinding` — before any process starts. The wire `role` and `agent` fields remain
compatibility identifiers derived from the bound Agent's name.

## feature.workflow.execute

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
native|outer, stored at initialization under `capability_configuration` and required to match host
settings for ordinary invocations. Caller input never substitutes for permission authority.

stdout is `concorde-capability-result@3` with capability_id, invocation_id, mode, status
succeeded|blocked|failed|described, workspace (null or host-supplied worktree metadata), output
(typed response or null) and errors [{code,field,message}]. Exit 0 means succeeded/described; 3 means
blocked/failed. Describe-policy does not launch agents or mutate project state; policy descriptions
go to stderr. Before any launch or policy description the host verifies the build manifest and
refuses a stale build with `stale_build`.

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
selected source or destination worktree; third-worktree and nested sessions are rejected.

The host resolves the complete selected Target Spec plus one-hop Shared Specs and Protocol/kind definition for every stage.
Spec-only agents, including Spec reviewers, start in a private capsule containing only frozen input.
Implementation workers get the same Spec context plus explicitly owned code paths. Code reviewers
use a distinct read-only implementation role with only the current registered file enumeration. Sessions are fresh, network and credential
access disabled, writes restricted by phase. A native integration unable to enforce the grant blocks;
outer enforcement requires a host-issued sandbox. Executor completions must match invocation, policy,
launch and context identities. No ambient conversation or predecessor transcript is admitted.

Every new agent-backed task in a global capability first launches `concorde-coordinator` with the
entry Domain or Service.
Main discovery can
append only registered main-visible Domain/Service Target Spec and Shared Specs on demand; each append starts a fresh process with a
new context identity. The host rejects Module expansion and code access. For capabilities other than
the `ask` action of `concorde-main`, main must return one owning target; cross-target mutation is
routed through a Domain. The host
then starts the capability's different bounded worker or composite flow. `concorde-main` may route one
or more fresh `concorde-reader` workers, after which a final fresh main invocation receives only typed
worker results for synthesis. An optional caller target/focus is a routing hint, not a context grant.

`concorde-main` also owns topology evolution. `design-topology` admits exact registry metadata and
all three global kind definitions while still withholding direct Module expansion and code. It returns a
digest-bound candidate registry, local Spec tasks, migration constraints and acceptance conditions;
no project file changes. `accept-topology` is the first developer gate. It rechecks the complete
discovery context, starts fresh target-local Spec authors and validates their combined output against
an in-memory registry/document overlay. Full worker documents are stored only in an ignored,
before-digest-bound application artifact. The public response exposes its ArtifactRef, not its
contents. `apply-topology` is the second developer gate and atomically applies the exact reviewed
artifact or leaves/restores the project. A stale registry, Protocol, Spec input, application digest
or invalid final target state blocks mutation.
Document membership changes require tasks for all retained current/candidate references. A shared
replacement is admitted only when every candidate referencing target author returns identical bytes.

No Skill returns context manifests; the context Service is host-internal and
`describe-policy` mode already previews the exact grants a capability would receive without
launching an agent or mutating project state. Each previewed stage's description also names the
bound Agent and Harness identity (`agent`, `harness`, `agent_binding_digest`, `instructions_digest`,
`loop_timeout_seconds`), so a caller can audit which Agent definition and effective loop timeout a
launch would use without reading its rendered instructions. Complete cognitive snapshots never cross
the Skill result boundary.

Authoring returns local document replacements; the host alone applies them. A single-target author
cannot change a multiply referenced document. Planning runs a separate
context assessment first and stores a target plan only for a sufficient context and nonempty result.
One `.concorde/worktree.json` owns the change, its root task, target records, phase/status, gaps and
validation identity. Plans and auxiliary files live under `.concorde/work/<target-id>/`. There is no
new `.concorde/attempts/<change-id>/` lifecycle. Each component keeps progress in the enclosing change.
Task authoring receives a concorde-plan-artifact. Implementation receives concorde-implementation-task
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
feedback across a repair attempt, or exhausting the declared limit, stops the Graph instead of
retrying forever: the change `status` becomes `waiting` (a human decision or a Spec/code change is
needed) or `limit_exhausted` respectively, and the wire `outcome` remains `conflicting`. Elsewhere, a
Spec gap (`spec_incomplete`) stops the Graph with status `waiting`, a failed deterministic check
stops it with status `failed`, and another blocking/unsupported outcome stops it with status
`blocked`. A human directly changing the Spec or the implementation between invocations resets the
recorded repair count instead of silently continuing a stale repair attempt. Preserving the change
worktree on a stop and resuming a current plan/tasks/implementation phase on a repeat instead of
discarding completed component work otherwise remain unchanged.
Domain implementation coordinates independently selected participating component contexts. The host
records each author before launch and after success or blocking. Already authored draft Spec bytes
remain in the candidate when a later component blocks. Cross-component validation runs after every
affected local author finishes; it cannot prevent resuming an incomplete reconciliation. No component
code changes before this agreement. Component development loops report completion to the same owning change.

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
| `concorde-capability-configuration@1` | The invocation's `configuration` field, and `concorde-configure-request@1`/`-response@1` | `{integration: codex\|claude, enforcement: native\|outer}`. Stored at initialization under `.concorde/config.json`'s `capability_configuration` key; an invocation or child stage whose configuration differs from that stored snapshot stops with `configuration_mismatch`. |

### Capability requests and responses

Common request task fields (named once, not repeated per row): `target_id` (required for every
stage capability; an optional routing hint for `main`, `dev-loop` and `reflections-triage`), `task`,
`focus_id`, `constraints`, `change_id`. Common response fields (present in every capability response
except `configure`, which replaces them): `target_id`, `focus_id`, `change_id`, `context_id`,
`outcome`, `answer`, `artifacts`, `gaps`, `checks`, `completed_capabilities`.

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-main-request@1` / `concorde-main-response@1` | main | Every request field is optional at the wire level. Request adds `action` (ask\|design-topology\|accept-topology\|apply-topology, default ask), `topology_proposal` (a `concorde-topology-proposal@1` TypedValue, required for accept-topology) and `application` (an ArtifactRef, required for apply-topology). Response adds `entry_target`, `discovered_targets`, `routes`, `worker_results` (`concorde-main-worker-result@1` TypedValues), nullable `topology_proposal`/`application`, `files` and `workspace`. |
| `concorde-dev-loop-request@1` / `concorde-dev-loop-response@1` | dev-loop | Only `task` is required. Request adds `specify` (default true; false skips Spec authoring) and `run_reviews` (default true; false records an explicit per-mode skip). Response is the common shape only. |
| `concorde-reflections-triage-request@1` / `concorde-reflections-triage-response@1` | reflections-triage | Requires `target_id`, `action` (status\|record-gaps\|investigate\|implement\|merge\|close) and `reflection_ids` (a unique array, possibly empty); `task` is optional here, unlike other capabilities, because status and record-gaps need none. Adds optional `gap_ids`. Response adds `reflections` and `gap_records`. |
| `concorde-init-request@1` / `concorde-init-response@1` | init | Requires only `action` (propose\|apply); adds optional `name`, `target_id`, `configuration` and `proposal` (a `concorde-project-proposal@1` TypedValue). Response replaces the common shape with `status` (proposed\|applied), a nullable `proposal` and `files`. |
| `concorde-configure-request@1` / `concorde-configure-response@1` | configure | Requires `configuration`. Response requires `configuration` and `status: "applied"`; the only capability whose response does not use the common stage shape. |
| `concorde-validate-request@1` / `concorde-validate-response@1` | validate | Requires `target_id` and `task`; adds optional `run_checks`. Response is the common shape only. |
| `concorde-deliver-request@1` / `concorde-deliver-response@1` | deliver | Requires only `change_id`; adds optional `target_id`, `task`, `focus_id`, `constraints` and `keep_worktree`. Response is the common shape only. |
| `concorde-specify-request@1` / `concorde-specify-response@1` | specify (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-review-request@1` / `concorde-review-response@1` | review (stage) | Requires `task` and `review_mode` (spec\|code); `target_id` is optional at the wire level but always supplied by the composing capability. Response adds `reviews` (`concorde-review-result@1` TypedValues). |
| `concorde-context-solve-request@1` / `concorde-context-solve-response@1` | context-solve (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-plan-request@1` / `concorde-plan-response@1` | plan (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-tasks-request@1` / `concorde-tasks-response@1` | tasks (stage) | Requires `target_id` and `task`. Response is the common shape only. |
| `concorde-implement-request@1` / `concorde-implement-response@1` | implement (stage) | Requires `target_id` and `task`. Response is the common shape only. |

### Stage handoffs

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-context-snapshot@1` | Every stage capability's frozen input | Carries `target_id`, `kind`, `focus_id`, `phase`, `task`, `constraints`, `protocol_binding`, `protocol`, `document_order`, `target_spec`, `shared_specs`, `diagram_sources`, `instructions`, `stage_inputs`, `implementation_artifacts` (populated only for implementation/code-review) and `workspace`. A changed membership or byte digest is rejected as `stale_context`. |
| `concorde-agent-stage-context@1` | Host to worker, wrapping the launch | `{snapshot: concorde-context-snapshot@1, change_id, expected_artifacts}`. |
| `concorde-agent-stage-result@1` | Worker to host, the completion | `{context_id, outcome, answer, gaps, documents, diagrams?, plan, tasks, reflection_findings?}`; `documents`/`diagrams`/`plan`/`tasks`/`reflection_findings` are populated only by the phase that produces them. A mismatched `context_id` is rejected as `incompatible_handoff`. |

### Review types

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-review-input@1` | Host-produced, inside the review stage context | `{review_mode, input_digest, revision, changes: [{path,patch}]}`; binds the exact Spec/code revision under review. |
| `concorde-review-stage-context@1` | Host to reviewer, the launch | `{snapshot: concorde-context-snapshot@1, review: concorde-review-input@1}`. |
| `concorde-review-stage-result@1` | Reviewer to host, the completion | `{context_id, input_digest, review_mode, status: no_findings\|findings\|incomplete, representative_tasks, findings, gaps, answer}`. |
| `concorde-review-result@1` | Published in `concorde-review-response@1.reviews` | The stage result plus `target_id`, `focus_id`, `revision`, a nullable `context_id`, `status` extended with skipped\|not_run, and `semantic_completeness: "not_proven"`. |

### Topology types

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-discovery-context@1` | Host to coordinator/reader, during main routing, synthesis or topology design | `{capability: main\|dev-loop, phase: route\|synthesize, action: route\|ask\|design-topology, task, constraints, target_hint, focus_hint, protocol_binding, protocol, topology (nullable registry, design-topology only), targets, instructions, worker_results, workspace}`. |
| `concorde-main-stage-context@1` | Wraps the discovery context for launch | `{snapshot: concorde-discovery-context@1}`. |
| `concorde-main-stage-result@1` | Coordinator to host, the completion | `{context_id, outcome, answer, expand_targets, routes, gaps, topology_design (nullable)}`. |
| `concorde-main-worker-result@1` | Fresh reader/worker to main, for synthesis | `{target_id, focus_id, context_id, outcome, answer, gaps}`; never carries raw Spec bodies back into main cognition. |
| `concorde-topology-design@1` | design-topology's output, embedded in the main stage result | `{summary, registry, spec_tasks (nonempty), migration_constraints, acceptance (nonempty)}`. |
| `concorde-topology-proposal@1` | design-topology's response, and accept-topology's request | `{proposal_id, base_registry_digest, protocol_binding, context_id, discovered_targets (nonempty), task, constraints, target_hint, focus_hint, design: concorde-topology-design@1, workspace}`; a stale `base_registry_digest` or `protocol_binding` is rejected as `stale_proposal`. |
| `concorde-topology-author-context@1` | Host to target-local Spec author, during accept-topology | `{context_id, base_registry_digest, target, task, protocol_binding, protocol, candidate_document_references, current_document_order, target_spec, shared_specs, diagram_sources, instructions, workspace}`. |
| `concorde-topology-author-result@1` | Author to host, the completion | `{context_id, target_id, outcome, answer, gaps, documents, diagrams?}`. |
| `concorde-topology-application@1` | Host-private, produced by accept-topology and consumed by apply-topology | `{application_id, topology_proposal: concorde-topology-proposal@1, base_registry_digest, protocol_binding, files (nonempty)}`; the public response exposes only its ArtifactRef, never these bytes. |

### Project proposal

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-project-proposal@1` | `concorde-init-request@1.proposal` and `-response@1.proposal` | `{action: "initialize", base_digest (nullable), files: [{path, before_digest (nullable), content}]}`. |

### Stage-input artifacts

| Type | Carried by | Promise |
| --- | --- | --- |
| `concorde-plan-artifact@1` | A `stage_inputs` entry: produced by plan, consumed by tasks | `{plan}`. |
| `concorde-implementation-task@1` | A `stage_inputs` entry: produced by tasks, consumed by implement | `{plan, tasks: [{id,target_id,description,acceptance,complete}]}`; implement must return every task with the same identity, marked complete only when its acceptance is met. |
| `concorde-reflection-selection@1` | A `stage_inputs` entry: produced by reflections-triage, consumed by dev-loop implementation | `{head, records: [{id,path,digest,content}]}`. |
| `concorde-review-result@1` | A `stage_inputs` entry: produced by code review, consumed by the repair `tasks`/`implement` iteration | The same value published in `concorde-review-response@1.reviews` (see Review types below), re-verified from its stored artifact before reuse; only accompanies a dev-loop's bounded `review_code -> tasks` repair round. |

Unknown fields, an incompatible `type_id`, an unsupported `schema_version`, and an unsafe or
non-project-relative path are all rejected before any agent launches, with the `TypedDataError`
codes named below. Every identity named in this section exists in the exported schemas or the
invocation envelope, and every exported identity appears here at least once with its version;
`python -m concorde validate` enforces this alignment deterministically
(`CONCORDE-SPEC-CAPABILITIES-001`, `CONCORDE-SPEC-TYPES-001`).

| Error code | Meaning |
| --- | --- |
| `ambiguous_route` | Main routing found more than one owning target for a capability that requires exactly one; route cross-target work through a Domain instead. |
| `cancelled` | `CapabilityExecutionError.outcome` when the injected runner raised `KeyboardInterrupt`; the host maps this to the `execution_cancelled` result error code. |
| `child_blocked` | A composed child capability returned a blocked or otherwise non-successful outcome and stopped the composing capability. |
| `configuration_mismatch` | The invocation's, a child's, or a native launch's configuration differs from the initialized project settings or the host's own snapshot. |
| `context_limit` | Main discovery exceeded its bounded expansion-step limit. |
| `delivery_in_progress` | The candidate is already being delivered; resume delivery from either participating worktree instead of starting a new mutation. |
| `delivery_session_required` | The current session is not recognized as the change's selected source or destination worktree. |
| `detached_primary` | The destination (primary) worktree has no attached branch to deliver onto. |
| `detached_worktree` | A change worktree has no attached branch. |
| `dirty_primary` | The primary worktree has uncommitted local changes that delivery must preserve rather than discard. |
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
| `invalid_entry_target` | The registry's `entry_target` is not a Domain or Service, so main discovery cannot start there. |
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
| `merge_conflict` | The candidate conflicts with the current destination branch; resolve it in the candidate's own worktree and revalidate. |
| `missing_change` | Task authoring was requested without a managed change. |
| `missing_plan` | Task authoring was requested without an authored plan. |
| `missing_tasks` | Implementation was requested without authored tasks. |
| `permission_denied` | A request or worker tried to act outside its granted target, Domain participation, or write scope. |
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
| `unknown_type` | A TypedValue's `type_id` does not name a schema the wire module recognizes. |
| `unsafe_path` | A path escapes the project root, aliases a control path, or crosses a symlink. |
| `unsupported_target` | The selected target has no registered implementation for the requested code-owning behavior. |
| `unsupported_version` | The invocation's `schema_version` is not the one this host implements. |
| `use_proposal` | `describe-policy` cannot preview `init`/`configure`; use their deterministic proposal flow instead. |
| `workspace_mismatch` | The current worktree, branch, or worktree topology does not match what the requested capability or transition requires. |
| `worktree_handoff_required` | A mutating request in the primary worktree needs a new agent session opened in the linked worktree the host just prepared. |
| `execution_failed` | The host caught an exception outside the named Spec/typed-data/build error vocabulary. |

## Main routing view

Select `module.wire-contracts` for request/result schema construction and validation,
`module.permissions` for path/network/credential policy compilation, and
`module.agent-execution` for native process launch and completion attestation. Select
`service.spec-context` when the behavior being changed is target/document resolution rather than
capability orchestration. Public capability projection belongs to `module.package-assets`. The main
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
A change's `status` may also become `cancelled` or `limit_exhausted` after an executor outcome of
the same name (`execution_cancelled`/`execution_limit`), distinguishing a cancelled or time-limited
agent process from an ordinary `blocked`/`failed` outcome; the candidate is preserved for repair or
resumption in every case. A development loop stopping for a necessary Spec gap, or for blocking
code-review feedback that repeats unchanged across a bounded repair attempt, records status
`waiting` instead of the generic `blocked`: both name a concrete point where a human decision or a
Spec/code change is needed before the loop can usefully resume.

## Independent review contract

`concorde-review` requires target_id, task and review_mode=spec|code, with the usual optional focus,
constraints and current-worktree change_id. It is a stage capability invoked with an already routed
target by its composing global capability or by another already-bound stage; it is never invoked
directly with an unrouted task. Spec mode uses the complete admitted Target Spec plus Shared
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

| Review state | Skill outcome and progression |
|---|---|
| no_findings with nonempty coverage | completed; bounded review succeeded |
| findings, all advisory and no gaps | completed; findings retained for the consumer |
| concrete necessary gaps | spec_incomplete; dependent steps pause |
| blocking code findings without gaps | conflicting; dependent steps pause |
| incomplete coverage, invalid result or process failure | failed; an incomplete report, never a clean result |
| describe-policy | described with not_run; no execution or persistence |
| run_reviews=false | host records skipped; no reviewer runs |

Every mode and target uses a separate session. A Domain with recorded component work can request
cross-target review: the host validates each component's participation, starts its own reviewer from
its recorded task and admitted collection, then aggregates only typed results. Spec review also
assesses the Domain itself; code review never gives the Domain code. A Domain without recorded
component work returns unsupported for code review. During a development loop, the Domain's initial
Spec review is local; component reviews occur in the coordinated component loops after reconciliation.

## Review gates, gap history and recovery

`concorde-dev-loop` resumption skips Spec authoring only after a host-accepted authoring result for
the same target, task, focus and constraints. Standalone review records, including failed or
unrelated reviews, cannot substitute for authoring. A completed Domain still revisits its recorded
component coordination: stronger review requirements propagate before completed component work is
reused, and missing or stale component reviews run before readiness.

Standard development requires both reviews for a code-owning target (only Spec review for a Domain).
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
  agent, and this Service is host-internal: no Skill exposes its return values directly.
- Permissions (`module.permissions`): `compile_policy(effects, binding, role_paths, *, deny_paths=(),
  outer_sandbox_required=False) -> NormalizedPolicy`, the Codex/Claude renderers, and
  `build_launch_specification(...) -> LaunchSpecification` have complete signatures and value types
  in the runtime Shared Spec. They must reject widening, preserve empty reviewer writes and bind
  policy/native/context identities. `PermissionPolicyError(ValueError)` aborts the launch; an opaque
  task string cannot supply outer enforcement.
- Execution (`module.agent-execution`): `AgentProcessExecutor()` constructs the default host executor;
  `executor(launch: LaunchSpecification) -> CapabilityExecutionResult` starts one fresh native process.
  A host may inject a callable with this same interface for a verified backend. The exact result,
  completion and error/receipt records are in the runtime Shared Spec. Successful exit without matching
  completion is failure. `CapabilityExecutionError(RuntimeError)` has a nullable receipt and stops the
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
  rejects aliases and symlink traversal. `TypedDataError(ValueError)` carries code/field; no
  helper expands context or performs remote schema retrieval.
- Configuration (host-owned adapter): `load_configuration(project_root: str|Path) -> dict`
  returns the initialized concorde-capability-configuration TypedValue from `.concorde/config.json`.
  Ordinary invocations and child stages must equal that snapshot; mismatch stops the transition.
  It neither grants permissions nor silently falls back to caller-provided settings.
- Package assets (`module.package-assets`): `build(project_root, integration="all", *,
  framework_prefix="") -> BuildResult` renders every Agent, Skill and Studio-graph projection from
  `agents/`/`prompts/`/`skills/`/`capabilities/`; `write_build(...)` also writes them, including
  `generated/build-manifest.json`. `check_build(project_root, integration="all") -> (bool,
  tuple[str,...])` renders into a temporary directory and reports every stale or drifted output
  without writing. `verify_fresh(project_root) -> None` raises `BuildError` with code `stale_build`
  when a recorded source has changed since the last build; the host calls it before every top-level
  invocation except a lifecycle capability. `load_agent(package_root, name) -> SkillPrompt` returns
  one Agent's rendered body, effect declaration, and complete `AgentBinding` from the current build
  (`load_role_prompt` remains as a compatibility alias). `resolve_agent_spec`/`resolve_role_prompt`/
  `resolve_skill_source(project_root, relative_path) -> ResolvedPrompt` and
  `find_unreachable_prompts(project_root, roots) -> tuple[str,...]` resolve and check `@include`
  prompt sources, raising `PromptResolverError` on a malformed, unresolved or unreachable source.
  `validate_package(root: Path) -> list[Finding]` runs the prompt/capability-module/Agent/contract/
  Spec-alignment/build-output checks behind `python -m concorde validate` and `build --check`.
  `python -m concorde protocol-manifest [--write] [--bind-project]` reports, accepts, or binds the
  tracked Protocol digest to the current build. The host supplies rendered bodies inline and admits
  only role-specific paths; it does not let the worker reopen the source package.
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

## Diagram sources in Spec authoring and review

The host supplies only registered diagram bytes as path/digest/content/declaration records in diagram_sources.
Ordinary Spec authors may return diagram replacements for their target's registered paths, in the
optional diagrams array; other stages cannot author them. Source kind/title and generated output
constraints are validated together with Markdown, and a failure rolls back the complete change.
Shared diagram changes use coordinated topology authoring, with identical returned bytes from all
references. Topology completion returns every accepted Markdown member and diagram source in
descriptor order, including new Domain ontology.md and System overview sources. A blocked author
returns no replacements. The prepared artifact and application checks bind that exact complete set.

Diagram membership and bytes contribute to target revision, context freshness and review identity.
Spec review receives their scoped changes; findings may locate a diagram while attributing the
missing promise to a registered Markdown Spec. A generated HTML file is never an authoring input or
permission grant. Publication separately performs Archify rendering and visual acceptance.

## Optional Studio execution view

The Studio adapter starts or observes the same CapabilityHost used by CLI and Skill invocations.
Its generated graph configuration exposes one graph per Skill; internal stages appear in execution
events without gaining direct public entries. Studio receives an invocation wrapper containing the
existing schema-3 invocation and an optional expected_workspace assertion. Project and package
roots remain host-bound; the assertion does not select another workspace.

The final state exposes the unchanged capability result envelope, admitted policy descriptions and
stage/process events. Pausing or replaying a run does not waive permissions, checks or the worktree
lifecycle, and replay may execute effects again. Ordinary local CLI and Skill calls do not require
a Studio server. The source-checkout setup and debugging guide is scripts/development/STUDIO.md.
This execution view participates in Developer view and feedback through the orchestration host.
