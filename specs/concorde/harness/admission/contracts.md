# Request admission contracts

The exact envelopes, records and error codes of [Request admission](module.md). The
[requirements](requirements.md) state what the host promises about them.

The schemas below use an offline JSON Schema subset: `type`, `properties`, `required`,
`additionalProperties`, `items`, `enum`, `const`, `anyOf` and `minLength` have their ordinary
meanings, and no schema loads another document.

## Launcher

`scripts/run-operation.py <capability>` accepts exactly one argument, the name of one of the eleven
public capabilities: `concorde-context-solve`, `concorde-plan`, `concorde-tasks`,
`concorde-implement`, `concorde-issues`, `concorde-spec-review`, `concorde-code-review`,
`concorde-init`, `concorde-configure`, `concorde-validate` and `concorde-deliver`. Standard input
holds one capability request of at most 1 MiB. Any other argument, a larger input or a request whose
`operation_id` differs from the launcher argument is refused. In an installed project the launcher
first re-executes itself in the worktree's managed runtime. The environment variable
`CONCORDE_WORKER_POLICY` marks a worker process, and its presence refuses the request with
`permission_denied`. `CONCORDE_SESSION_SELECTION` pins the Concorde code to an explicitly selected
private session build; a selection in `maintenance` mode is refused with `fresh_session_required`.

## Capability request

```concorde-contract
{
  "id": "contract.admission.invocation",
  "version": 3,
  "schema": {
    "type": "object",
    "properties": {
      "type_id": {"const": "concorde-operation-invocation"},
      "schema_version": {"const": 3},
      "operation_id": {"type": "string", "minLength": 1},
      "mode": {"enum": ["execute", "describe-policy"]},
      "configuration": {"anyOf": [{"type": "object"}, {"type": "null"}]},
      "input": {"type": "object"}
    },
    "required": ["type_id", "schema_version", "operation_id", "mode", "configuration", "input"],
    "additionalProperties": false
  },
  "semantics": "Run one public capability. operation_id names the capability and must equal the launcher argument. mode execute runs it; describe-policy describes what would run without launching a worker or changing project files. configuration is null for the stored project configuration or a concorde-operation-configuration typed value equal to it. input is the capability's own request typed value {type_id, schema_version, data}, validated against that capability's request type; unknown fields and versions are refused. Any other schema_version is refused with unsupported_version.",
  "example": {
    "type_id": "concorde-operation-invocation",
    "schema_version": 3,
    "operation_id": "concorde-plan",
    "mode": "execute",
    "configuration": null,
    "input": {
      "type_id": "concorde-plan-request",
      "schema_version": 1,
      "data": {"target_id": "module.checkout", "task": "Add retry limits"}
    }
  }
}
```

## Result envelope

```concorde-contract
{
  "id": "contract.admission.result",
  "version": 3,
  "schema": {
    "type": "object",
    "properties": {
      "type_id": {"const": "concorde-operation-result"},
      "schema_version": {"const": 3},
      "operation_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
      "invocation_id": {"type": "string", "minLength": 1},
      "mode": {"anyOf": [{"enum": ["execute", "describe-policy"]}, {"type": "null"}]},
      "status": {"enum": ["succeeded", "blocked", "failed", "described"]},
      "workspace": {"anyOf": [{"type": "object"}, {"type": "null"}]},
      "output": {"anyOf": [{"type": "object"}, {"type": "null"}]},
      "errors": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "code": {"type": "string", "minLength": 1},
            "field": {"type": "string"},
            "message": {"type": "string"},
            "feedback": {"type": "object"}
          },
          "required": ["code", "field", "message"],
          "additionalProperties": false
        }
      }
    },
    "required": ["type_id", "schema_version", "operation_id", "invocation_id", "mode", "status", "workspace", "output", "errors"],
    "additionalProperties": false
  },
  "semantics": "The one result of a capability request. operation_id and mode are null only when the request was refused before a capability and mode were admitted. status succeeded or described exits 0; blocked or failed exits 3. output is the capability's response typed value or null; its outcome completed, ready or delivered gives succeeded, failed gives failed, any other outcome gives blocked. workspace is null or the worktree the request ran in; after a relay it names the candidate. Each error has a stable code, a JSON-pointer field (possibly empty), a sanitized message and optional causal feedback. A relayed request returns the candidate launcher's envelope unchanged apart from being this request's result.",
  "example": {
    "type_id": "concorde-operation-result",
    "schema_version": 3,
    "operation_id": "concorde-plan",
    "invocation_id": "5b0c7f3e-2f5c-4d0e-9a53-8f1b6a1c2d34",
    "mode": "execute",
    "status": "blocked",
    "workspace": null,
    "output": null,
    "errors": [
      {
        "code": "configuration_mismatch",
        "field": "",
        "message": "invocation configuration differs from initialized project settings"
      }
    ]
  }
}
```

<a id="participation-envelopes"></a>

**Participation.** Request admission provides both envelopes to any caller of the launcher; the Pi
`concorde` tool and the native preparation steps are the callers today. The host validates every
incoming request against the request contract before admission and emits exactly one result per
request.

Standard error carries, when present, a canonical JSON line `{"policies": [...]}` with the policy
descriptions of a `describe-policy` request, and a line `{"usage": {...}}` summarizing the usage
records of the request's run.

## Causal feedback

```concorde-contract
{
  "id": "contract.admission.feedback",
  "version": 1,
  "schema": {
    "type": "object",
    "properties": {
      "schema_version": {"const": 1},
      "code": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
      "message": {"type": "string"},
      "layer": {"type": "string", "minLength": 1},
      "category": {
        "enum": ["no-submission", "schema-rejection", "host-refusal", "capture-failure", "native-exit", "cancelled", "timeout", "transport", "observation", "invalid-completion", "unknown"]
      },
      "attempt": {"anyOf": [{"type": "string"}, {"type": "null"}]},
      "causes": {"type": "array", "items": {"type": "object"}},
      "diagnostics": {
        "type": "object",
        "properties": {
          "complete": {"type": "boolean"},
          "redacted": {"type": "boolean"},
          "text": {"anyOf": [{"type": "string"}, {"type": "null"}]},
          "references": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["complete", "redacted", "text", "references"],
        "additionalProperties": false
      }
    },
    "required": ["schema_version", "code", "message", "layer", "category", "attempt", "causes", "diagnostics"],
    "additionalProperties": false
  },
  "semantics": "A diagnostic record of one failure. code and message are the failure's own code and sanitized message; layer names where it was observed; category classifies it; attempt is the known ticket, run, tool-call or invocation identity, or null when unknown. causes are the lower-level feedback records in order, each of this same shape. diagnostics.complete is true only when this record and every cause are complete; redacted is always true; text holds selected sanitized facts; references name files from which a fuller record can be retrieved. A record grants nothing: it never changes a status, accepts a result or authorizes a retry.",
  "example": {
    "schema_version": 1,
    "code": "relay_failed",
    "message": "the candidate worktree's launcher returned no result envelope",
    "layer": "relay",
    "category": "transport",
    "attempt": "5b0c7f3e-2f5c-4d0e-9a53-8f1b6a1c2d34",
    "causes": [],
    "diagnostics": {
      "complete": true,
      "redacted": true,
      "text": "{\"exit_code\":1,\"stderr\":\"\",\"stdout\":\"\"}",
      "references": []
    }
  }
}
```

<a id="participation-feedback"></a>

**Participation.** Request admission provides the feedback record in every error entry it creates.
The same record is produced by the native Pi side through `pi/execution-error.mjs`, so a failure
keeps one format across the Python Host and the Pi process.

Sanitization removes argument values that follow `Received arguments:`, model output that follows
`Output:`, bearer tokens, and values labelled as API keys, access or refresh tokens, passwords,
secrets or authorization. A record whose serialized form exceeds the Pi display limit (12,000
bytes) is written to a new mode-0600 file under the system temporary directory, and the display
shows its path, digest and size instead.

## Operation configuration

The stored value is the typed value `concorde-operation-configuration`, schema version 2, kept
under `operation_configuration` in `.concorde/config.json`:

```text
{model?: "provider/id", thinking?: off|minimal|low|medium|high|xhigh|max, timeout_seconds?: int,
 workers?: {<worker>: {model?, thinking?, timeout_seconds?}}}
```

A key in `workers` must name a worker, timeouts must be positive and a model must name a provider.
A missing stored value, or a project root that is a symlink, is `configuration_mismatch`.
`propose_configuration` returns a proposal bound to the SHA-256 digest of the current file;
`apply_configuration` writes it only when the file still has that digest, keeping every other key
of the file.

## Wire identities

Every value that crosses a capability or step boundary is a typed value
`{type_id, schema_version, data}` whose version is fixed per type; an unknown field or another
version is refused. The schemas themselves are registered with the Spec Module's wire types. The
owner is the Module whose behaviour gives the value its meaning.

### Envelopes

| Identity | What it carries | Owner |
| --- | --- | --- |
| `concorde-operation-invocation@3` | one capability request on the launcher's standard input | Request admission |
| `concorde-operation-result@3` | the one result envelope on standard output | Request admission |
| `concorde-operation-configuration@2` | the stored worker models, thinking levels and time limits | Request admission |

### Capability requests and responses

Most requests carry `target_id`, `task` and optionally `focus_id`, `constraints` and `change_id`.
Most responses carry `target_id`, `focus_id`, `change_id`, `context_id`, `outcome`, `answer`,
`artifacts`, `blockers`, `checks` and `completed_operations`.

| Identity | What it carries | Owner |
| --- | --- | --- |
| `concorde-context-solve-request@1`, `concorde-context-solve-response@3` | whether the Module's Spec suffices for the task | Planning |
| `concorde-plan-request@1`, `concorde-plan-response@3` | a plan for one Module | Planning |
| `concorde-tasks-request@2`, `concorde-tasks-response@3` | implementation tasks derived from the plan; the request may select a scope repair or a code-review repair | Planning |
| `concorde-implement-request@1`, `concorde-implement-response@3` | implementation of the accepted tasks | Implementation |
| `concorde-spec-review-request@2`, `concorde-spec-review-response@3` | an independent Spec review of an explicit Module; the response adds `reviews` | Review |
| `concorde-code-review-request@2`, `concorde-code-review-response@3` | an independent code review of an explicit Module; the response adds `reviews` | Review |
| `concorde-validate-request@1`, `concorde-validate-response@3` | deterministic validation and optional configured checks | Validation |
| `concorde-deliver-request@1`, `concorde-deliver-response@3` | delivery of a change, optionally keeping the worktree or merging into the primary | Delivery |
| `concorde-issues-request@1`, `concorde-issues-response@2` | list, show, report, reopen or solve an Issue; the response adds Issue records and a decision | Issues |
| `concorde-init-request@3`, `concorde-init-response@1` | propose or apply the first Spec of a project, optionally opting in to apply in the primary worktree; the response has `status`, `proposal` and `files` | Spec |
| `concorde-project-proposal@1` | the files of an initialization proposal with their base digests | Spec |
| `concorde-configure-request@3`, `concorde-configure-response@2` | a new operation configuration, optionally opting in to apply in the primary worktree; the response has `configuration` and `status` | Distribution |

### Step inputs and results

| Identity | What it carries | Owner |
| --- | --- | --- |
| `concorde-context-snapshot@7` | the frozen context of one worker step | Task context |
| `concorde-agent-stage-context@5` | a worker's input: the snapshot, the change ID and expected artifacts | Task context |
| `concorde-agent-stage-result@3` | a worker's proposal: outcome, answer, blockers, plan, tasks or Issue decision | Task context |
| `concorde-review-stage-context@5` | a reviewer's input: the snapshot and the review input | Task context |
| `concorde-review-stage-result@2` | a reviewer's proposal: status, representative tasks, Issues and answer | Task context |
| `concorde-review-input@1` | the exact Spec or code revision and changes under review | Review |
| `concorde-review-result@2` | a published review, also admitted as a repair input to tasks and implementation | Review |
| `concorde-plan-artifact@1` | an accepted plan passed to task authoring | Planning |
| `concorde-implementation-task@1` | the plan and task list passed to implementation | Planning |
| `concorde-task-identity-constraints@1` | task IDs a new task list must not reuse | Planning |
| `concorde-task-scope-feedback@1` | the digest of a task list that exceeded the implementation boundary | Planning |
| `concorde-issue-selection@1` | the selected Issue, its revision and bounded feedback for the Issue solver | Issues |
| `concorde-issue-intent@1` | the intended behaviour of a selected Issue for ordinary steps | Issues |
| `concorde-issue-context@1` | the selected Issue observations behind a review repair | Issues |
| `concorde-issue-report@1` | one classified observation a worker reports | Issues |
| `concorde-issue-receipt@1` | the immutable identity of an accepted observation | Issues |

## Error codes

Every code any Concorde component raises is listed here, because every code can reach a caller
through the result envelope. The last column names the Module where it arises.

| Code | Meaning | Where it arises |
| --- | --- | --- |
| `already_initialized` | the project is initialized; use `concorde-configure` to change settings | Spec |
| `check_sandbox_unavailable` | the read-only sandbox for configured checks cannot be enforced, so checks do not run | Check execution |
| `closed_issue` | a new observation needs the closed Issue to be reopened first | Issues |
| `configuration_mismatch` | the request's or a nested step's configuration differs from the stored one, or none is stored | Request admission, Agent execution |
| `delivery_in_progress` | a mutation was requested while the change is being delivered | Request admission |
| `delivery_required` | a primary merge needs a completed staged delivery | Delivery |
| `delivery_session_required` | the session is not in the change's candidate or primary worktree | Delivery |
| `detached_primary` | the primary worktree has no attached branch to deliver onto | Delivery |
| `detached_worktree` | a candidate has no attached branch | Candidate worktrees |
| `dirty_primary` | a primary merge is blocked by local changes in the primary | Delivery |
| `execution_cancelled` | the host was interrupted or a worker was cancelled; the candidate is kept | Request admission, Agent execution |
| `execution_failed` | any other failure outside the named codes | Request admission, Agent execution |
| `execution_limit` | a worker ran past its time limit | Request admission |
| `failed_merge_checks` | the merged candidate failed its configured checks | Delivery |
| `fresh_session_required` | a mutation from the primary of Concorde's source checkout, or a maintenance session selection | Request admission |
| `incompatible_contracts` | shared contracts of participating Modules disagree | Implementation |
| `incompatible_handoff` | a returned or supplied identity does not match what the host issued, or conflicts with the recorded change owner | Request admission, Task context, Agent execution, Candidate worktrees |
| `incomplete_change` | validation or delivery was requested before every task was complete | Validation, Delivery |
| `incomplete_tasks` | implementation did not report every task as complete | Implementation |
| `invalid_agent_binding` | a worker profile is inconsistent with its contract or the build | Task context |
| `invalid_assessment` | a context assessment contradicts its own blockers | Task context |
| `invalid_completion` | a worker returned no single valid result, or one its contract forbids | Agent execution |
| `invalid_context` | a resolved context or its grant is structurally invalid | Spec, Agent execution |
| `invalid_delivery` | a delivery record has an invalid or mismatched identity | Delivery |
| `invalid_field` | a typed value violates its schema, or a worker selection is malformed | Spec |
| `invalid_focus` | the scenario focus does not belong to the selected Module | Spec |
| `invalid_input` | a request's fields are invalid for the requested action | Request admission, Spec |
| `invalid_issue` | an Issue record, report or disposition violates its shape or history | Issues |
| `invalid_json` | the input is not JSON, or has duplicate keys or non-finite numbers | Spec |
| `invalid_merge` | the merged candidate failed Spec validation | Delivery |
| `invalid_phase` | the step phase is not supported | Task context |
| `invalid_proposal` | a proposal or source override is not acceptable | Spec |
| `invalid_reference` | an external inclusion is not checked out | Task context |
| `invalid_spec` | a document's metadata, ownership or reading structure is invalid | Spec |
| `invalid_target` | a context query names no registered Module or scenario | Spec |
| `invalid_worktree_state` | a change status, owner, incarnation token or guidance marker is malformed | Candidate worktrees |
| `issue_key_conflict` | a report key was reused with different content | Issues |
| `local_installation_required` | the worktree's own installation is missing, stale, foreign or not the running one | Request admission |
| `merge_conflict` | the candidate conflicts with the primary branch | Delivery |
| `missing_change` | no managed change or live candidate exists for the request | Candidate worktrees, Planning, Implementation |
| `missing_plan` | task authoring was requested without a plan | Planning |
| `missing_runtime` | no usable interpreter, environment or native runtime was found | Request admission, Agent execution |
| `missing_source` | a file named by the registry or a context is missing | Spec |
| `missing_tasks` | implementation was requested without tasks | Implementation |
| `native_required` | a model-backed step needs its prepared native worker; there is no other backend | Agent execution, Operations |
| `not_installed` | no Protocol copy is installed in the project | Spec |
| `permission_denied` | a request, worker or result acts outside its granted authority | Request admission, Task context, Agent execution |
| `primary_session_required` | the command must run in the primary worktree | Candidate worktrees, Delivery |
| `primary_unavailable` | the primary worktree cannot be found; restore it and retry | Candidate worktrees |
| `protocol_mismatch` | the project's Protocol binding does not match the installed Protocol | Spec, Distribution |
| `review_required` | a required review is missing, incomplete, blocking or stale | Review, Issues |
| `spec_incomplete` | the Spec lacks something the step needs; a gap was recorded | Planning, Implementation, Review, Validation |
| `stale_build` | the build is missing or older than its sources | Distribution, Task context |
| `stale_context` | a frozen context no longer matches the repository | Task context, Agent execution |
| `stale_delivery` | a recorded delivery is no longer on its target branch | Delivery |
| `stale_evidence` | recorded evidence no longer matches the current bytes | Validation, Review, Delivery, Agent execution |
| `stale_issue` | the selected Issue changed since it was read | Issues |
| `stale_proposal` | a proposal's base changed since it was produced | Spec |
| `stale_reference` | an artifact reference's digest does not match the file | Spec |
| `stale_status` | a change status changed since it was read | Candidate worktrees |
| `state_persistence_failed` | status or run evidence could not be written after a final outcome | Request admission, Delivery |
| `undeclared_operation` | an Operation composed another it does not declare | Agent execution |
| `unknown_agent` | no Agent has this name | Task context |
| `unknown_change` | a change ID has no status or delivery record | Candidate worktrees, Delivery |
| `unknown_issue` | the Issue does not exist | Issues |
| `unknown_operation` | the capability is not registered or not public | Request admission |
| `unknown_target` | the target Module is not registered | Spec |
| `unknown_type` | a typed value names no registered type | Spec |
| `unsafe_path` | a path escapes the project, aliases a control path or crosses a symlink | Spec, Candidate worktrees |
| `unsupported_profile` | the registry declares an unsupported profile | Spec |
| `unsupported_target` | the Module has no implementation for the requested behaviour | Implementation, Review |
| `unsupported_version` | a request or typed value has an unsupported version | Request admission, Spec |
| `use_proposal` | `describe-policy` cannot preview initialization or configuration; use their proposals | Operations |
| `workspace_mismatch` | the entry directory, worktree or incarnation is not the one the request requires, or `run_in_primary` was set outside the primary worktree | Request admission, Candidate worktrees |
