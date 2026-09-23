# Request admission requirements

These are the Module-wide obligations of [Request admission](module.md). The
[scenarios](scenarios.md) show them in concrete situations; the envelopes are defined in
[contracts](contracts.md).

## The boundary

### req.admission.single-boundary — Every capability request passes admission

Every public capability request SHALL pass the admission sequence before any provider behaviour runs.

This holds for the launcher and for every Host step of a native preparation, which calls the same
sequence.

### req.admission.no-worker-callers — Workers cannot call capabilities

The host SHALL refuse with `permission_denied` a capability request made from a process that runs
under a worker policy.

### req.admission.project-root — The project is the entry directory

The host SHALL bind a request's project root to the working directory of its entry process, exactly
as resolved and without searching parent directories.

The registry, Specs and implementation files a request reads are therefore those of that worktree.
A directory inside a Git worktree that is not its root is refused with `workspace_mismatch`.

### req.admission.configuration-match — Requests run with the stored configuration

The host SHALL refuse with `configuration_mismatch` a request, other than `concorde-init`, whose
configuration differs from the project's stored operation configuration.

### req.admission.fresh-build — Model-backed requests need a fresh build

The host SHALL refuse with `stale_build` a top-level request for a model-backed capability when the
Concorde build is not fresh.

### req.admission.local-execution — Installed projects run only their own installation

In an installed project the host SHALL execute a request only with that worktree's own verified
local installation, its interpreter and its dependencies.

Failure is `local_installation_required`; there is no fallback to another worktree's or a global
installation.

## The result

### req.admission.one-envelope — Every request ends in one envelope

Every capability request SHALL end with exactly one result envelope on standard output, including
requests refused before admission and requests interrupted by the host.

### req.admission.distinct-outcomes — Refusals, outcomes and failures stay distinct

A result envelope SHALL distinguish an admission refusal, a provider's business outcome and an
execution failure by its status, output and error codes.

### req.admission.feedback-keeps-causes — Reported failures keep their causes

An error reported through a higher layer SHALL keep the lower-level cause's code, sanitized message
and known attempt identity in its causal feedback.

## Relay

### req.admission.primary-opt-in — Only an explicit opt-in applies in the primary

The host SHALL apply `concorde-configure` or an initialization `apply` in the primary worktree only
when the request sets `run_in_primary: true`.

Without the field such a request is relayed like every other mutation. The field is part of those
two request types only, and a request that sets it outside the primary worktree is refused with
`workspace_mismatch`.

### req.admission.relay-result — A relay returns the candidate's envelope

A relayed request SHALL return the candidate launcher's complete result envelope, or fail with
`relay_failed` when that launcher returns none.
