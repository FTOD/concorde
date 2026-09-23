# Request admission requirements

The Module-wide obligations of [Request admission](module.md). The [scenarios](scenarios.md) show
them in concrete situations; the envelopes, declarations and codes are defined in
[contracts](contracts.md).

## The boundary

### req.admission.single-boundary — Every capability request passes admission

Every capability request SHALL pass the admission sequence before any provider behaviour runs.

This holds for requests from the launcher and for capability requests a provider makes on behalf
of another. The Host steps of a running Agent call or Workflow are not capability requests; Agent
execution checks them against the call it prepared.

### req.admission.declarations-only — Admission decides from declarations alone

Admission SHALL decide a request's mutation, workspace, target selection, default task,
configuration handling and build check only from the capability declaration of the capability it
names.

No capability name is special-cased inside admission, and admission imports no provider; a
provider's own selection logic runs only through the hook its declaration names.

### req.admission.project-root — The project is the entry directory

The Host SHALL bind a request's project root to the working directory of its entry process, exactly
as resolved and without searching parent directories.

The registry, Specs and implementation files a request reads are therefore those of that worktree.
A directory inside a Git worktree that is not its root is refused with `workspace_mismatch`.

### req.admission.committed-worktree — Mutations need a Git worktree

The Host SHALL refuse with `workspace_mismatch` a mutating request started outside any Git
worktree.

A candidate can only start from committed history, and change status and run records need a
primary worktree to live in. Only an embedding Host created with an explicit in-place allowance
applies mutations without a Git worktree.

### req.admission.explicit-target — No substituted target

Admission SHALL refuse a Module-bound request whose target or focus does not resolve in the registry instead of choosing another Module.

### req.admission.configuration-match — Requests run with the stored configuration

The Host SHALL refuse with `configuration_mismatch` a request of a capability that declares stored
configuration when the request's configuration differs from the project's stored operation
configuration or none is stored.

### req.admission.fresh-build — Model-backed requests need a fresh build

The Host SHALL refuse with `stale_build` a top-level request of a model-backed capability when the
build is not fresh as the build manifest contract defines it.

## The result

### req.admission.one-envelope — Every request ends in one envelope

Every capability request SHALL end with exactly one result envelope on standard output, including
requests refused before admission and requests interrupted by the Host.

### req.admission.distinct-outcomes — Refusals, outcomes and failures stay distinct

A result envelope SHALL distinguish an admission refusal, a provider's business outcome and an
execution failure by its status, output and error codes.

### req.admission.run-record — Every executed request has a run record

Every request admitted in `execute` mode SHALL have one run record in the primary worktree, opened
before its provider runs and finished with its result envelope.

A relaying request's record names the candidate's run. A failure to finish the record is reported
beside the output as `state_persistence_failed` and turns a `succeeded` status into `blocked`.

### req.admission.feedback-keeps-causes — Reported failures keep their causes

An error reported through a higher layer SHALL keep the lower-level cause's code, sanitized message
and known attempt identity in its causal feedback.

## Relay

### req.admission.primary-opt-in — Only an explicit opt-in applies in the primary

The Host SHALL apply a request of a capability that declares the `primary-opt-in` workspace in the
primary worktree only when the request sets `run_in_primary: true`.

Without the field such a request is relayed like every other mutation. A request that sets it
outside the primary worktree is refused with `workspace_mismatch`.

### req.admission.relay-result — A relay returns the candidate's envelope

A relayed request SHALL return the candidate launcher's complete result envelope, including its
invocation identity, or fail with `relay_failed` when that launcher returns none.

### req.admission.relay-own-installation — A relay runs the candidate's own installation

A relay SHALL run the candidate's own launcher with the candidate's own verified installation, never
the relaying worktree's or a global one.

A candidate without one is refused with `local_installation_required` and kept for a retry after
installation.

## Configuration

### req.admission.configure-digest-bound — Only the reviewed proposal is applied

`concorde-configure` SHALL apply a configuration proposal only when the request names that exact
proposal's digest and the configuration file still has the digest the proposal was computed from.

### req.admission.configure-atomic — Configuration changes are all or nothing

`concorde-configure` SHALL leave `.concorde/config.json` unchanged when the request is invalid, the
project cannot be loaded after the change or the write fails.
