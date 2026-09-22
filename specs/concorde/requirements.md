# Framework requirements

These obligations hold across the whole Framework. Each Module states its own precise
requirements; the ones here are the promises that no single Module can keep alone.

## Boundaries

### req.concorde.routing-no-access — Selection grants no access

Selecting a Module or a scenario for a request SHALL NOT by itself give a worker access to any file
beyond that Module's frozen context.

### req.concorde.read-no-mutate — Read-only capabilities change nothing

A read or preview capability SHALL NOT modify project Specs, implementation files or the registry.

Reporting an Issue while doing read-only work is the one permitted side effect: it adds an Issue
record and gives the reporting worker no other write access.

## Results

### req.concorde.versioned-result — Every call returns a versioned result

Every capability call SHALL return a versioned result that keeps an admission failure, an execution
failure and the domain outcome distinct.

### req.concorde.unsupported-explicit — Unsupported inputs fail explicitly

A request with an unsupported version, capability or integration SHALL fail with an explicit error
instead of being handled in a degraded way.

### req.concorde.no-stale-replay — Repeated mutations use current state

A repeated mutating request SHALL be admitted against the current saved state, or require a fresh
proposal, instead of replaying an effect computed from stale inputs.

## Developer content and delivery

### req.concorde.preserve-user-content — Developer content is preserved

Installation and configuration SHALL preserve content that the developer owns.

### req.concorde.no-overwrite-initialized — Initialization never overwrites

Initialization SHALL NOT overwrite an already initialized project.

### req.concorde.delivery-separate — Delivery needs its own request

Delivering a candidate SHALL require its own explicit request after the candidate is ready.
