# Request admission scenarios

Concrete situations of [Request admission](module.md). Module-wide obligations are stated once in
[requirements](requirements.md).

## Admitting a request

### scenario.harness.execute-operation — Run an admitted capability

- GIVEN a registered public capability and a well-formed capability request in `execute` mode, started at a worktree root
- WHEN the host admits the request
- THEN it checks the request, the workspace and the configuration, opens a run record, and hands the request to the capability's provider
- AND for a model-backed capability the provider prepares the native call, which is executed and accepted outside this boundary
- AND the request ends with one result envelope carrying the provider's typed output, with status `succeeded` when its outcome is `completed`, `ready` or `delivered`

See [single boundary](requirements.md#req.admission.single-boundary),
[one envelope](requirements.md#req.admission.one-envelope) and
[distinct outcomes](requirements.md#req.admission.distinct-outcomes).

### scenario.harness.typed-reject — Refuse a malformed request before anything runs

- GIVEN a capability request whose envelope or typed request has an unknown type or version, a missing or unknown field, a wrong value type, duplicate JSON keys, a non-finite number or an unsafe path
- WHEN the host reads or admits it
- THEN it refuses the request with a stable code, such as `invalid_json`, `unknown_type`, `unsupported_version`, `invalid_field` or `unsafe_path`, and a JSON-pointer `field`
- AND the envelope keeps the admitted mode when the envelope itself was valid
- BUT no provider runs and no default value replaces the rejected one

### scenario.harness.execute-blocked-launch — A stale build or a refused grant blocks the launch

- GIVEN a model-backed capability whose build is stale, or whose worker grant is refused when it is compiled or checked
- WHEN the host would otherwise prepare or launch the worker
- THEN the request is refused with `stale_build` or the grant's error before any worker process starts
- AND the change status and run records are left unchanged

See [fresh build](requirements.md#req.admission.fresh-build).

### scenario.harness.describe-policy — Preview a capability without running it

- GIVEN a capability request with `mode: describe-policy`
- WHEN the host processes it
- THEN it returns status `described` with the provider's description of what would run
- AND no worker is launched and no project file changes
- BUT `concorde-init` and `concorde-configure` refuse the preview with `use_proposal`, because their own proposals are the preview

### scenario.harness.host-tools-direct — Deterministic capabilities run without a Graph or a model

- GIVEN a request for initialization, configuration, validation, delivery or Issue bookkeeping
- WHEN the host runs it
- THEN the same request, workspace, target, configuration and finalization checks apply
- AND the provider runs directly, without compiling a LangGraph Graph or starting a model
- AND a failed check stops every later step and still returns the versioned failure envelope

## Where a request runs

### scenario.harness.invocation-worktree-binding — A request binds to the worktree it was started in

- GIVEN the Pi tool starts the launcher from some working directory
- WHEN the host admits the request
- THEN the project root is exactly that directory, without searching parent directories
- AND the registry, Specs and implementation files come from that worktree alone, while change status and run records come from the primary worktree
- AND a Git worktree root gives workspace kind `primary` or `change`, and a directory outside any Git repository gives kind `unversioned`
- BUT a directory inside a Git worktree that is not its root is refused with `workspace_mismatch`, and no worker is launched

See [the project is the entry directory](requirements.md#req.admission.project-root).

### scenario.harness.worktree-relay — A mutating request from the primary runs in a candidate

- GIVEN an admitted mutating request started in the primary worktree of a consumer project
- WHEN the host binds its workspace
- THEN it creates a candidate from the committed `HEAD`, records the change in primary status, installs the invoking package into the candidate, and runs the same request through the candidate's launcher with the candidate's change ID
- AND it returns that launcher's complete envelope, whose workspace names the candidate, and forwards its standard error
- AND a later request from the primary naming that change ID runs in the same candidate, while a change ID no live candidate records is refused with `missing_change`
- AND uncommitted primary edits are not copied, and the originating session never moves
- BUT in Concorde's source checkout a mutating request from the primary is refused with `fresh_session_required`, even when it names a change

See [relay result](requirements.md#req.admission.relay-result).

### scenario.harness.local-installation — A candidate runs its own complete installation

- GIVEN a consumer primary whose installed Concorde package and runtime are ignored by Git
- WHEN the host creates a candidate for an admitted request
- THEN the installer gives the candidate its own Pi entry, Concorde package, dependencies, interpreter and receipt before the relayed launcher runs
- AND a later relay into the same candidate verifies and reuses that installation without reinstalling or rewriting its receipt
- AND change status and run records stay in the primary
- BUT a source candidate is never given an installation; it must already have its own build and environment

See [local execution](requirements.md#req.admission.local-execution).

### scenario.harness.local-installation-failure — A failed installation keeps the candidate recoverable

- GIVEN a missing, stale, conflicting or failed candidate installation, a foreign executing interpreter, or an installed entry that belongs to another project
- WHEN relay or installed admission tries to run the request
- THEN it stops with `local_installation_required` before any worker, without falling back to the primary's or a global installation
- AND a newly created candidate is kept, with status `blocked` and its original owner and task recorded in primary status
- AND after the developer runs the installer for that candidate, retrying the request continues the same change

## Reporting failures

### scenario.harness.execution-feedback — Failures keep their causes through every caller

- GIVEN a native proposal, a workflow child, a Host step or an optional Graph service fails with a known lower-level cause
- WHEN each caller above it reports the failure
- THEN the reported error keeps that cause's code, sanitized message and known attempt identity, and adds its own layer as context
- AND no-submission, schema rejection, Host refusal, capture, exit, cancellation, timeout, transport and observation failures remain distinguishable, and an unknown cause stays unknown
- AND a record too large for display is exported whole to a private temporary file whose reference is shown, and a failed export is reported as incomplete rather than silently clipped
- BUT feedback never turns a failure into completion, never retries, and never includes credential values, request bodies or transcripts

See [feedback keeps causes](requirements.md#req.admission.feedback-keeps-causes).
