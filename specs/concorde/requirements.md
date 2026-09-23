# Framework requirements

These obligations hold across the whole Framework. Each is one that no single Module can keep
alone: every Module named in its explanation has to keep its part. A Module's own obligations are
in that Module's requirements, and are linked from here rather than restated.

## Boundaries

### req.concorde.routing-no-access — Selection grants no access

Selecting a Module or a scenario for a request SHALL NOT by itself widen what the Host grants an
Agent call beyond the boundary sets of the Modules the call is bound to.

Spec tooling computes the sets, Task context composes the call's context from them, and Agent
execution launches the call with that context. A scenario focus, a link, a registry entry or a
Module named in a request's text adds nothing. How far the grant is enforced on a running worker is
stated honestly in the [Harness](harness/module.md).

### req.concorde.read-no-mutate — Read-only capabilities change nothing

A read or preview capability SHALL NOT modify project Specs, implementation files or the registry.

Reporting an Issue while doing read-only work is the one permitted side effect: it adds an Issue
record and gives the reporting Agent no other write access. A preview is any call that the
capability declares as describing its effect instead of performing it.

### req.concorde.dependency-layering — Dependencies follow the layering rules

Every `uses` declared by a Concorde Module SHALL target a provider that the [dependency layering
rules](module.md#dependency-layering) permit for that Module.

The rules are decidable from the registry alone. They keep the foundations free of the Modules
built on them, which is what keeps each Module's Spec context small.

## Results

### req.concorde.versioned-result — Every call returns a versioned result

Every capability call SHALL return a versioned result that keeps an admission failure, an execution
failure and the provider's domain outcome distinct.

Request admission defines the result envelope; each provider must map its own outcomes into the
domain part and never report an execution failure as a domain outcome, or the reverse.

### req.concorde.no-stale-replay — Repeated mutations use current state

A repeated mutating request SHALL be admitted against the current saved state, or require a fresh
proposal, instead of replaying an effect computed from stale inputs.

Every provider re-reads its inputs and compares them with what the earlier attempt recorded; a
proposal-based capability such as `concorde-init` or `concorde-configure` refuses a proposal whose
recorded inputs have changed.

## Change control

### req.concorde.spec-gaps-stop — Automatic loops never repair Specs

An automatic revision loop SHALL NOT change a Spec document to resolve a gap or finding it
produced.

A workflow or Graph may repeat Agent calls to repair code after a failed check or a blocking code
review, but a missing or contradictory promise stops the work and is reported for the developer.
Spec documents change only through the user session or a Task subagent acting for it. An Issue solver may still close an Issue as a duplicate or as not actionable
on its own; that changes an Issue record, not a Spec.

### req.concorde.delivery-separate — Delivery needs its own request

Delivering a candidate SHALL require its own explicit request after the candidate is ready.

No other capability delivers. Validation marks a candidate ready and stops there; Delivery
publishes it on its own branch; updating the primary branch is a further request that states the
developer's explicit merge authorization.
