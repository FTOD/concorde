# Request admission contracts

The exact envelopes, declarations, records and error codes of [Request admission](module.md). The
[requirements](requirements.md) state what the Host promises about them.

The schemas below use an offline JSON Schema subset: `type`, `properties`, `required`,
`additionalProperties`, `items`, `enum`, `const`, `anyOf` and `minLength` have their ordinary
meanings, and no schema loads another document.

## Typed values of admission

Admission owns these registered typed values; every other capability's request, response and
stage values are specified by the Module that owns them.

| Identity | What it carries |
| --- | --- |
| `concorde-operation-invocation@3` | one capability request on the launcher's standard input |
| `concorde-operation-result@3` | the one result envelope on standard output |
| `concorde-operation-configuration@2` | the stored Agent models, thinking levels and time limits |
| `concorde-configure-request@4` | a `concorde-configure` proposal or apply request |
| `concorde-configure-response@3` | the outcome of a `concorde-configure` request |
| `concorde-configuration-proposal@1` | a configuration proposal bound to its source digest |

## Launcher input

The launcher `scripts/run-operation.py <capability>` belongs to Distribution; what it passes to
admission is fixed here. It accepts exactly one argument, the name of one public capability in the
catalog. Standard input holds one capability request of at most 1 MiB. Any other argument, a larger
input, or a request whose `operation_id` differs from the argument is refused with an envelope
whose `mode` is null. The launcher hands admission the project root (its working directory), the
package root, the catalog of capability declarations, the dispatcher, the installation service and
the session provenance it verified, if any.

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
  "semantics": "Run one public capability. operation_id names the capability and must equal the launcher argument. mode execute runs it; describe-policy describes what would run without launching an Agent or changing project files. configuration is null for the stored project configuration or a concorde-operation-configuration typed value equal to it; a capability that takes its configuration from its request requires null. input is the capability's own request typed value {type_id, schema_version, data}, validated against the request type its declaration names; unknown fields and versions are refused. Any other schema_version is refused with unsupported_version.",
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
  "version": 4,
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
  "semantics": "The one result of a capability request. operation_id and mode are null only when the request was refused before a capability and mode were admitted. invocation_id identifies the run that produced the envelope; its run record is .concorde/runs/<invocation_id>/run.json in the primary worktree when the request executed. status succeeded or described exits 0; blocked or failed exits 3. output is the capability's response typed value or null; its outcome completed, ready or delivered gives succeeded, failed gives failed, any other outcome gives blocked; describe-policy gives described. workspace is null or {path, branch, change_id, ...} of the worktree the request ran in. Each error has a stable code, a JSON-pointer field (possibly empty), a sanitized message and optional causal feedback. A relayed request returns the candidate launcher's envelope unchanged, including the candidate's invocation_id and workspace; the relaying request's own run record links to that invocation.",
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

**Participation.** Request admission provides both envelopes to the Pi session's `concorde` tool,
which builds requests and reads results; any other caller of the launcher uses the same contracts.

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

**Participation.** Request admission provides the feedback record in every error entry it creates;
the Pi session displays it. The same record is produced on the Pi side through
`pi/execution-error.mjs`, so a failure keeps one format across the Host and the Pi process.

Sanitization removes argument values that follow `Received arguments:`, model output that follows
`Output:`, bearer tokens, and values labelled as API keys, access or refresh tokens, passwords,
secrets or authorization. A record whose serialized form exceeds the Pi display limit (12,000
bytes) is written to a new mode-0600 file under the system temporary directory, and the display
shows its path, digest and size instead. A failed export is reported as incomplete, never clipped
silently.

## Capability declaration

```concorde-contract
{
  "id": "contract.admission.capability-declaration",
  "version": 1,
  "schema": {
    "type": "object",
    "properties": {
      "capability": {"type": "string", "minLength": 1},
      "public": {"type": "boolean"},
      "model_backed": {"type": "boolean"},
      "request_type": {"type": "string", "minLength": 1},
      "response_type": {"type": "string", "minLength": 1},
      "mutation": {
        "type": "object",
        "properties": {
          "policy": {"enum": ["never", "always", "by-action"]},
          "actions": {"type": "array", "items": {"type": "string", "minLength": 1}}
        },
        "required": ["policy", "actions"],
        "additionalProperties": false
      },
      "workspace": {"enum": ["candidate", "primary-opt-in", "delivery-session", "none"]},
      "target": {
        "type": "object",
        "properties": {
          "selection": {"enum": ["bound-module", "none", "provider-hook"]},
          "hook": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]}
        },
        "required": ["selection", "hook"],
        "additionalProperties": false
      },
      "default_task": {"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
      "configuration": {"enum": ["stored", "request"]},
      "entry_point": {"type": "string", "minLength": 1}
    },
    "required": ["capability", "public", "model_backed", "request_type", "response_type", "mutation", "workspace", "target", "default_task", "configuration", "entry_point"],
    "additionalProperties": false
  },
  "semantics": "The facts admission needs about one capability. capability is its external name (concorde-<name>). public says whether the launcher may run it; admission refuses a non-public or unlisted name with unknown_operation. model_backed says whether it runs an Agent; a top-level model-backed request needs a fresh build. request_type and response_type are the registered typed-value types of its request data and response. mutation.policy never means the request never changes the project and runs where it was started; always means every request mutates; by-action means a request mutates exactly when its data's action field is one of mutation.actions, which must be empty for the other policies. workspace says where a mutating request runs: candidate (in its change's candidate, relayed from the primary), primary-opt-in (as candidate, and the request type carries run_in_primary, which applies it in the primary when true there), delivery-session (where it was started, never relayed or registered; the provider verifies participation), or none (only with mutation never). target.selection bound-module requires target_id and admits it and any focus_id against the registry, restoring the recorded owner of a mutating request's change; none performs no target check; provider-hook calls target.hook, a module:function entry point that receives the request data and returns the bound data and whether this request mutates. hook is null unless selection is provider-hook. default_task is the task text supplied when the request omits one, or null. configuration stored requires a stored operation configuration equal to the request's; request consults no stored configuration and requires the envelope's configuration to be null. entry_point is the module:function the Operations dispatch runs for the admitted request. A catalog entry violating this contract, or a hook or entry point that cannot be resolved, refuses the request with invalid_input before any effect.",
  "example": {
    "capability": "concorde-configure",
    "public": true,
    "model_backed": false,
    "request_type": "concorde-configure-request",
    "response_type": "concorde-configure-response",
    "mutation": {"policy": "by-action", "actions": ["apply"]},
    "workspace": "primary-opt-in",
    "target": {"selection": "none", "hook": null},
    "default_task": null,
    "configuration": "stored",
    "entry_point": "operations.configure:run"
  }
}
```

<a id="participation-declarations"></a>

**Participation.** Request admission requires one declaration per capability in the catalog the
launcher passes; Operations provides them. A request whose data does not set `task` receives the
declared default task when there is one. A
provider hook runs before the workspace is bound and may read the current worktree, but it must not
write anything; its returned data replaces the request data for every later step.

## Operation configuration

The stored value is the typed value `concorde-operation-configuration`, schema version 2, kept
under `operation_configuration` in `.concorde/config.json`:

```text
{model?: "provider/id", thinking?: off|minimal|low|medium|high|xhigh|max, timeout_seconds?: int,
 workers?: {<agent>: {model?, thinking?, timeout_seconds?}}}
```

A key in `workers` must name an Agent, time limits must be positive integers and a model must name
a provider. A missing stored value, or a project root that is a symbolic link, is
`configuration_mismatch`.

## concorde-configure

The request type is `concorde-configure-request`, schema version 4, one of:

| Action | Fields | Effect |
| --- | --- | --- |
| `propose` | `configuration` (a `concorde-operation-configuration` typed value), optional `accept_protocol` (default false) | none; returns a proposal, or status `unchanged` when the stored value already equals it and no Protocol is to be accepted |
| `apply` | `proposal` (a `concorde-configuration-proposal` typed value), `proposal_digest`, optional `run_in_primary` | writes the proposal |

A proposal is the typed value `concorde-configuration-proposal`, schema version 1, with data
`{path: ".concorde/config.json", source_digest, configuration, protocol}`: `source_digest` is the
`sha256:` digest of the configuration file's bytes when the proposal was made, and `protocol` is
null or the Protocol binding `{version, digest}` of the installed Protocol copy to adopt.
`proposal_digest` is the `sha256:` digest of the canonical JSON of the proposal typed value.

Apply refuses, writing nothing: a `proposal_digest` that is not the digest of the given proposal
(`invalid_proposal`); a configuration file whose digest is not `source_digest`, or an installed
Protocol copy whose binding is not `protocol` (`stale_proposal`); an invalid configuration value
(`invalid_field`). Otherwise it replaces `operation_configuration`, and `protocol` when present,
keeps every other key, and keeps the write through a file transaction only if the project then
loads; if it does not, the file is restored and the error of the failed load is returned. Without
`accept_protocol`, a proposal for a project whose Protocol binding does not match its installed copy
is refused with `protocol_mismatch`.

The response type is `concorde-configure-response`, schema version 3:
`{status: proposed|unchanged|applied, proposal, proposal_digest, configuration}`, where `proposal`
and `proposal_digest` are null unless `status` is `proposed`, and `configuration` is the stored
value after the request. A `describe-policy` request is refused with `use_proposal`.

## Relay

The relay runs `[<candidate python>, <candidate launcher>, <capability>]` with the candidate as
working directory, the environment without `PYTHONPATH` and `PYTHONHOME`, and the relayed request
on standard input. The relayed request is the original with `configuration: null` and, when its
request type has a `change_id` field, the candidate's change identity. On interrupt the relay sends
SIGTERM and waits 30 seconds before killing the launcher. Output that is not a result envelope
fails with `relay_failed`, category `transport`, attempt the relaying invocation, and diagnostics
holding the exit code, standard output and standard error.

Before relaying into an existing candidate the relay checks that the candidate's change status
names the requested change and path (`workspace_mismatch`) and, for a request that mutates, that its
owner fields do not conflict (`incompatible_handoff`). The candidate launcher is selected by the
installation service: `install(candidate, package_root, bootstrap)` returns the candidate's own
interpreter and launcher, installing only when `bootstrap` is true (a new candidate), and raises
`local_installation_required` when the candidate has no verified installation of the package; the
candidate's change is then marked `blocked` with that outcome. A candidate of Concorde's own source
is never installed into: it must have its own fresh build, `.venv` interpreter and launcher, else
`missing_runtime`.

An embedding Host (a Python program that calls admission directly) may be created with
`allow_primary_worktree`; it then applies mutating requests in place, registering a change for the
primary or unversioned project. The launcher never sets it.

## Error codes

Every code any Concorde component raises is listed here, because every code can reach a caller
through the result envelope. The last column names the Modules where it arises; each of them owns
the code's meaning in its own context.

| Code | Meaning | Where it arises |
| --- | --- | --- |
| `already_initialized` | the project is initialized; use `concorde-configure` to change settings | Spec tooling |
| `check_sandbox_unavailable` | the read-only sandbox for configured checks cannot be enforced, so checks do not run | Check execution |
| `closed_issue` | a new observation needs the closed Issue to be reopened first | Issues |
| `configuration_mismatch` | the request's or a Host step's configuration differs from the stored one, or none is stored | Request admission, Agent execution |
| `delivery_in_progress` | a mutation was requested while the change is being delivered | Request admission |
| `delivery_required` | a primary merge needs a completed staged delivery | Delivery |
| `delivery_session_required` | the session is not in the change's candidate or primary worktree | Delivery |
| `detached_primary` | the primary worktree has no attached branch to deliver onto | Delivery |
| `detached_worktree` | a candidate has no attached branch | Candidate worktrees |
| `dirty_primary` | a primary merge is blocked by local changes in the primary | Delivery |
| `duplicate_type` | a type identity is registered again with another version or schema | Spec tooling |
| `execution_cancelled` | the Host was interrupted or an Agent call was cancelled; the candidate is kept | Request admission, Agent execution |
| `execution_failed` | any other failure outside the named codes | Request admission, Agent execution |
| `execution_limit` | an Agent call ran past its time limit | Request admission, Agent execution |
| `failed_merge_checks` | the merged candidate failed its configured checks | Delivery |
| `fresh_session_required` | a mutation from the primary of Concorde's own source checkout | Request admission, Pi session |
| `incompatible_contracts` | shared contracts of participating Modules disagree | Implementation |
| `incompatible_handoff` | a returned or supplied identity does not match what the Host issued, a stage input is not admitted, or a request conflicts with the recorded change owner | Request admission, Task context, Agent execution, Candidate worktrees |
| `incomplete_change` | validation or delivery was requested before every task was complete | Validation, Delivery |
| `incomplete_tasks` | implementation did not report every task as complete | Implementation |
| `invalid_agent_binding` | an Agent definition is inconsistent or not recorded in the build | Task context |
| `invalid_assessment` | a context assessment contradicts its own blockers | Planning |
| `invalid_completion` | an Agent call returned no single valid result, or one its definition forbids | Task context, Agent execution |
| `invalid_context` | a resolved context is structurally invalid | Spec tooling, Agent execution |
| `invalid_delivery` | a delivery record has an invalid or mismatched identity | Delivery |
| `invalid_field` | a typed value violates its schema | Spec tooling, Request admission |
| `invalid_focus` | the scenario focus does not belong to the selected Module | Spec tooling |
| `invalid_input` | a request's fields are invalid for the requested action, or a catalog declaration is invalid | Request admission, Spec tooling, Candidate worktrees |
| `invalid_issue` | an Issue record, report or disposition violates its shape or history | Issues |
| `invalid_json` | the input is not JSON, or has duplicate keys or non-finite numbers | Spec tooling |
| `invalid_merge` | the merged candidate failed Spec validation | Delivery |
| `invalid_phase` | the step phase is not the bound Agent definition's phase | Task context |
| `invalid_proposal` | a proposal, its digest or a source override is not acceptable | Spec tooling, Request admission |
| `invalid_reference` | an external inclusion is not checked out | Task context |
| `invalid_spec` | a document's metadata, ownership or reading structure is invalid | Spec tooling |
| `invalid_target` | a context query names no registered Module or scenario | Spec tooling |
| `invalid_worktree_state` | a change status, owner, incarnation token, guidance marker or provider section is malformed | Candidate worktrees, Request admission |
| `issue_key_conflict` | a report key was reused with different content | Issues |
| `local_installation_required` | the worktree's own installation is missing, stale, foreign or not the running one | Distribution, Request admission |
| `merge_conflict` | the candidate conflicts with the primary branch | Delivery |
| `missing_change` | no managed change or live candidate exists for the request | Candidate worktrees, Request admission, Planning, Implementation, Validation |
| `missing_plan` | task authoring was requested without a plan | Planning |
| `missing_runtime` | no usable interpreter, environment or native runtime was found | Request admission, Agent execution, Distribution |
| `missing_source` | a file named by the registry or a context is missing | Spec tooling |
| `missing_tasks` | implementation was requested without tasks | Implementation |
| `native_required` | a model-backed step needs its prepared native Agent call; there is no other backend | Agent execution |
| `not_installed` | no Protocol copy is installed in the project | Spec tooling |
| `permission_denied` | a result fills a field its Agent definition does not permit, or an action exceeds its granted authority | Task context, Agent execution |
| `primary_session_required` | the command must run in the primary worktree | Candidate worktrees, Delivery |
| `primary_unavailable` | the primary worktree cannot be found; restore it and retry | Candidate worktrees |
| `protocol_mismatch` | the project's Protocol binding does not match the installed Protocol | Spec tooling, Request admission |
| `relay_failed` | the candidate's launcher returned no result envelope | Request admission |
| `review_required` | a required review is missing, incomplete, blocking or stale | Review, Issue solving |
| `spec_incomplete` | the Spec lacks something the step needs; a gap was recorded | Planning, Implementation, Review, Validation |
| `stale_build` | the build is missing or older than its sources | Request admission, Task context, Distribution |
| `stale_context` | a frozen context no longer matches the repository | Task context, Agent execution |
| `stale_delivery` | a recorded delivery is no longer on its target branch | Delivery |
| `stale_evidence` | recorded evidence no longer matches the current bytes | Validation, Review, Delivery, Agent execution |
| `stale_issue` | the selected Issue changed since it was read | Issues, Issue solving |
| `stale_proposal` | a proposal's base changed since it was produced | Spec tooling, Request admission |
| `stale_reference` | an artifact reference's digest does not match the file | Spec tooling |
| `stale_status` | a change status changed since it was read | Candidate worktrees |
| `state_persistence_failed` | status or run evidence could not be written after a final outcome | Request admission, Delivery |
| `undeclared_operation` | an Operation composed another it does not declare | Agent execution |
| `unknown_agent` | no Agent has this name | Task context |
| `unknown_change` | a change identity has no status or delivery record | Candidate worktrees, Delivery |
| `unknown_issue` | the Issue does not exist | Issues |
| `unknown_operation` | the capability is not in the catalog or not public | Request admission |
| `unknown_target` | the target Module is not registered | Spec tooling |
| `unknown_type` | a typed value names no registered type | Spec tooling |
| `unsafe_path` | a path escapes the project, aliases a control path or crosses a symbolic link | Spec tooling, Candidate worktrees |
| `unsupported_profile` | the registry declares an unsupported profile | Spec tooling |
| `unsupported_target` | the Module has no implementation for the requested behaviour | Implementation, Review |
| `unsupported_version` | a request or typed value has an unsupported version | Request admission, Spec tooling |
| `use_proposal` | `describe-policy` cannot preview initialization or configuration; use their proposals | Request admission, Spec tooling |
| `workspace_mismatch` | the entry directory, worktree or incarnation is not the one the request requires, a mutation was started outside a Git worktree, or `run_in_primary` was set outside the primary worktree | Request admission, Candidate worktrees |
