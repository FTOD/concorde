# Request admission scenarios

Concrete situations of [Request admission](module.md). Module-wide obligations are stated once in
[requirements](requirements.md).

## Admitting a request

### scenario.admission.execute-request — Run an admitted capability

- GIVEN a public capability in the catalog and a well-formed capability request in `execute` mode, started at a worktree root
- WHEN the Host admits the request
- THEN it checks the request, the workspace and the configuration as the capability's declaration says, opens a run record, and hands the request to the dispatcher
- AND the request ends with one result envelope carrying the provider's typed output, with status `succeeded` when its outcome is `completed`, `ready` or `delivered`

See [single boundary](requirements.md#req.admission.single-boundary),
[declarations only](requirements.md#req.admission.declarations-only),
[one envelope](requirements.md#req.admission.one-envelope) and
[distinct outcomes](requirements.md#req.admission.distinct-outcomes).

### scenario.admission.typed-reject — Refuse a malformed request before anything runs

- GIVEN a capability request whose envelope or typed request has an unknown type or version, a missing or unknown field, a wrong value type, duplicate JSON keys, a non-finite number or an unsafe path
- WHEN the Host reads or admits it
- THEN it refuses the request with status `blocked`, a stable code such as `invalid_json`, `unknown_type`, `unsupported_version`, `invalid_field` or `unsafe_path`, and a JSON-pointer `field`
- AND the envelope keeps the admitted mode when the envelope itself was valid
- BUT no provider runs, no run record is opened and no default value replaces the rejected one

### scenario.admission.unknown-capability — Refuse a capability the catalog does not offer

- GIVEN a capability name that the catalog does not list, or lists as not public
- WHEN the Host admits a request for it
- THEN it refuses the request with `unknown_operation`
- AND no provider runs

### scenario.admission.invalid-declaration — Refuse a capability whose declaration is invalid

- GIVEN a catalog entry that violates the capability declaration contract, or names a hook or entry point that cannot be resolved
- WHEN the Host admits a request for that capability
- THEN it refuses the request with `invalid_input` before any effect

### scenario.admission.unknown-target — A target that does not resolve is refused

- GIVEN a request for a Module-bound capability whose `target_id` names no registered Module
- WHEN admission checks the target
- THEN the request is refused with `unknown_target`
- BUT no candidate is bound, no other Module is chosen and no provider runs

### scenario.admission.invalid-focus — A focus outside the target is refused

- GIVEN a request whose `focus_id` is not a scenario owned by its target Module
- WHEN admission checks the target
- THEN the request is refused with `invalid_focus`
- BUT no candidate is bound and no provider runs

### scenario.admission.stale-build — A stale build blocks a model-backed request

- GIVEN a model-backed capability and a Concorde build whose sources changed since it was made
- WHEN the Host admits a top-level request for it
- THEN the request is refused with `stale_build` before any provider runs
- AND the change status is unchanged and no candidate is created

See [fresh build](requirements.md#req.admission.fresh-build).

### scenario.admission.deterministic-no-model — Deterministic capabilities run without a build check or a model

- GIVEN a request for a deterministic capability, such as initialization, configuration, validation, delivery or Issue bookkeeping, and a stale build
- WHEN the Host runs it
- THEN the same request, workspace, target, configuration and finalization checks apply
- AND the provider runs without the build check, without starting a model and without importing LangGraph

### scenario.admission.describe-policy — Preview a capability without running it

- GIVEN a capability request with `mode: describe-policy`
- WHEN the Host processes it
- THEN it returns status `described` with the provider's description of what would run
- AND no Agent is launched, no project file changes, no candidate is created and no run record is opened

### scenario.admission.provider-hook — A provider selects its own target before the workspace is chosen

- GIVEN a capability whose declaration names a target selection hook, such as `concorde-issues` selecting the Issue to solve
- WHEN the Host admits a request for it
- THEN it calls the hook with the request data before binding the workspace
- AND every later step uses the data the hook returned and the hook's decision whether this request mutates
- BUT admission itself interprets none of the hook's fields

### scenario.admission.configuration-mismatch — A request with another configuration is refused

- GIVEN a capability that declares stored configuration, and a request whose configuration differs from the stored one, or a project with none stored
- WHEN the Host admits the request
- THEN it is refused with `configuration_mismatch`
- AND no provider runs

See [configuration match](requirements.md#req.admission.configuration-match).

### scenario.admission.request-configuration — Initialization needs no stored configuration

- GIVEN a directory with no stored operation configuration
- WHEN the user session requests `concorde-init` with a configuration in its request data and a null envelope configuration
- THEN the Host admits the request without reading a stored configuration
- AND the provider receives the configuration from the request

## Where a request runs

### scenario.admission.worktree-binding — A request binds to the worktree it was started in

- GIVEN the Pi tool starts the launcher from the root of a Git worktree or from a directory outside any Git repository
- WHEN the Host admits the request
- THEN the project root is exactly that directory, without searching parent directories
- AND the registry, Specs and implementation files come from that worktree alone, while change status and run records come from the primary worktree
- AND the workspace kind is `primary`, `change` or `unversioned` accordingly

See [the project is the entry directory](requirements.md#req.admission.project-root).

### scenario.admission.subdirectory-refused — A directory inside a worktree is not a project root

- GIVEN the launcher is started from a directory inside a Git worktree that is not its root
- WHEN the Host admits the request
- THEN the request is refused with `workspace_mismatch`
- AND no Spec is read and no provider runs

### scenario.admission.relay — A mutating request from the primary runs in a new candidate

- GIVEN an admitted mutating request without a `change_id`, started in the primary worktree of a consumer project on an attached branch
- WHEN the Host binds its workspace
- THEN it creates a candidate from the committed `HEAD`, records the change in primary status, has the installation service install the running package into the candidate, and runs the same request through the candidate's launcher with the candidate's change identity
- AND it returns that launcher's complete envelope, including the candidate's invocation identity and a workspace naming the candidate, and forwards its standard error
- BUT uncommitted primary edits are not copied, and the user session never moves

See [relay result](requirements.md#req.admission.relay-result).

### scenario.admission.relay-resume — A change identity continues in its candidate

- GIVEN a live candidate recorded for a change
- WHEN a mutating request from the primary names that `change_id`
- THEN the Host relays it into that candidate without creating another or reinstalling
- AND the recorded task and target of the change are kept

### scenario.admission.relay-missing-change — A change without a live candidate is refused

- GIVEN a `change_id` that no live candidate records
- WHEN a mutating request from the primary names it
- THEN the request is refused with `missing_change`
- AND no candidate is created

### scenario.admission.relay-failed — A candidate launcher without an envelope fails the relay

- GIVEN a relayed request whose candidate launcher exits without printing a result envelope
- WHEN the Host reads the launcher's output
- THEN the request ends with status `failed` and error `relay_failed`, a transport failure rather than a refusal, whose causal feedback keeps the launcher's exit code and sanitized output
- AND the candidate and its change status are kept

See [relay result](requirements.md#req.admission.relay-result).

### scenario.admission.source-primary-refused — Concorde's source primary does not run mutations

- GIVEN Concorde's own source checkout, whose project is the running package
- WHEN a mutating request is started in its primary worktree, with or without a `change_id` or `run_in_primary`
- THEN the request is refused with `fresh_session_required`
- AND no candidate is created

### scenario.admission.unversioned-mutation-refused — A mutation needs a Git worktree

- GIVEN a project directory outside any Git repository
- WHEN a mutating request is started there through the launcher
- THEN the request is refused with `workspace_mismatch`
- AND nothing is written and no change is registered

See [committed worktree](requirements.md#req.admission.committed-worktree).

### scenario.admission.primary-opt-in — Configure or initialize the primary on explicit request

- GIVEN the primary worktree of a consumer project on an attached branch
- WHEN the user session calls `concorde-configure` or `concorde-init` with action `apply` and `run_in_primary: true`
- THEN the Host applies the request in the primary worktree and returns an envelope whose workspace is null
- AND no candidate is created and no change status is registered

See [primary opt-in](requirements.md#req.admission.primary-opt-in).

### scenario.admission.primary-opt-in-outside-primary — The opt-in is refused in a candidate

- GIVEN a candidate worktree
- WHEN a request with `run_in_primary: true` is started there
- THEN it is refused with `workspace_mismatch` naming the field
- AND nothing is applied

### scenario.admission.delivery-session — Delivery runs where it was started

- GIVEN a request of a capability that declares the delivery session as its workspace, started in a change's candidate or in the primary
- WHEN the Host binds its workspace
- THEN the request runs in that worktree without a relay, a new candidate or a change registration
- AND the provider decides whether this worktree takes part in the change

### scenario.admission.delivery-in-progress — A change being delivered accepts no other mutation

- GIVEN a change whose status says it is being delivered or its cleanup is pending after delivery
- WHEN a mutating request other than delivery is started in its worktree
- THEN it is refused with `delivery_in_progress`
- AND the change status is unchanged

### scenario.admission.candidate-installation — A new candidate runs its own installation

- GIVEN a consumer primary whose installed Concorde package and runtime are ignored by Git
- WHEN the Host creates a candidate for a relayed request
- THEN the installation service gives the candidate its own installation before its launcher runs
- AND a later relay into the same candidate verifies and reuses that installation without reinstalling
- AND change status and run records stay in the primary

See [own installation](requirements.md#req.admission.relay-own-installation).

### scenario.admission.candidate-installation-failure — A failed installation keeps the candidate recoverable

- GIVEN a candidate whose installation is missing, stale, conflicting or failed
- WHEN the relay asks the installation service for its launcher
- THEN the request stops with `local_installation_required` before the candidate's launcher runs, without falling back to the primary's or a global installation
- AND the candidate is kept, with status `blocked` and its original owner and task recorded in primary status
- AND after the developer installs into that candidate, retrying the request continues the same change

## Records and failures

### scenario.admission.run-record — An executed request is recorded in the primary

- GIVEN an admitted request in `execute` mode
- WHEN it finishes, successfully or not
- THEN one run record in the primary worktree holds its source worktree, commit, input tree, runtime, build and final envelope
- AND a relaying request's run record names the candidate's run identity from the returned envelope

See [run record](requirements.md#req.admission.run-record).

### scenario.admission.state-persistence-failed — A lost record write is reported beside the output

- GIVEN a request whose provider produced its output
- WHEN writing its final change status or finishing its run record fails
- THEN the envelope keeps the output and adds an error `state_persistence_failed`
- AND a `succeeded` status becomes `blocked` when the run record could not be finished

### scenario.admission.cancelled — An interrupted request ends as cancelled

- GIVEN a running request
- WHEN the Host receives Ctrl-C or SIGTERM
- THEN the request ends with status `failed` and error `execution_cancelled`, and the change's lifecycle status becomes `cancelled`
- AND a relayed launcher receives SIGTERM and is killed only after thirty seconds
- BUT the candidate and its edits are kept

### scenario.admission.execution-failure — An execution failure is not a business outcome

- GIVEN a provider whose Agent call failed or ran past its time limit
- WHEN the request finalizes
- THEN the envelope has status `failed` with `execution_failed` or `execution_limit`, and the change's lifecycle status becomes `failed` or `limit_exhausted`
- BUT the output, if any, is never reported as `completed`

### scenario.admission.feedback-causes — Failures keep their causes through every caller

- GIVEN a native proposal, a Workflow child, a Host step or a relay fails with a known lower-level cause
- WHEN each caller above it reports the failure
- THEN the reported error keeps that cause's code, sanitized message and known attempt identity, and adds its own layer as context
- AND no-submission, schema rejection, Host refusal, capture, exit, cancellation, timeout, transport and observation failures remain distinguishable, and an unknown cause stays unknown
- BUT feedback never turns a failure into completion, never retries, and never includes credential values, request bodies or transcripts

See [feedback keeps causes](requirements.md#req.admission.feedback-keeps-causes).

### scenario.admission.feedback-export — A large failure record is exported, not clipped

- GIVEN a causal feedback record larger than Pi's display limit
- WHEN it is displayed
- THEN the whole sanitized record is written to a new private temporary file and the display shows its path, digest and size
- AND a failed export is reported as incomplete rather than silently clipped

## Configuration

### scenario.admission.configure-propose — Propose a configuration change

- GIVEN an initialized project and a valid operation configuration that differs from the stored one
- WHEN `concorde-configure` is called with action `propose`
- THEN it returns status `proposed`, a proposal holding the new value and the digest of the current configuration file, and the proposal's digest
- AND no file changes

### scenario.admission.configure-apply — Apply the reviewed proposal

- GIVEN a proposal and its digest, and a configuration file unchanged since the proposal
- WHEN `concorde-configure` is called with action `apply`, that proposal and that digest
- THEN the new value is written under `operation_configuration`, every other key of the file is kept, and the result is `status: applied`

See [digest-bound](requirements.md#req.admission.configure-digest-bound).

### scenario.admission.configure-stale — A changed configuration file refuses the proposal

- GIVEN a proposal whose source digest no longer matches the configuration file
- WHEN it is applied
- THEN the request fails with `stale_proposal`
- AND the file is unchanged

### scenario.admission.configure-altered-proposal — An altered proposal is refused

- GIVEN a proposal whose content no longer matches the proposal digest the apply request names
- WHEN it is applied
- THEN the request fails with `invalid_proposal`
- AND the file is unchanged

### scenario.admission.configure-invalid — An invalid configuration leaves the file unchanged

- GIVEN a proposal whose value is invalid, or whose write would leave a project that no longer loads, or a write that fails
- WHEN it is applied
- THEN the request fails with the error that stopped it
- AND `.concorde/config.json` has its previous bytes

See [all or nothing](requirements.md#req.admission.configure-atomic).

### scenario.admission.accept-protocol — Accept the installed Protocol explicitly

- GIVEN an initialized project whose Protocol binding does not match the Protocol copy under `.concorde/protocol/`
- WHEN a proposal made with `accept_protocol: true` is applied
- THEN the configuration is bound to the copy's manifest and the write is kept because the project then loads

### scenario.admission.protocol-not-accepted — A Protocol mismatch is not accepted silently

- GIVEN an initialized project whose Protocol binding does not match its installed Protocol copy
- WHEN `concorde-configure` proposes a change without `accept_protocol`
- THEN it fails with `protocol_mismatch`
- AND the binding stays unchanged

### scenario.admission.configure-preview-refused — Configuration has no policy preview

- GIVEN a `concorde-configure` request with `mode: describe-policy`
- WHEN the Host processes it
- THEN it is refused with `use_proposal`, because the proposal step is the preview
