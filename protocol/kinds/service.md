# Service

A Service is a self-contained capability with an explicit boundary contract. Its complete Markdown
collection explains its consumer-facing features, representative uses, prerequisites, obligations,
configuration, runtime inputs, outputs, state/effects, failures, compatibility, and applicable retries
and idempotency. A boundary may be an executable, file exchange, HTTP, or a specified standard format;
standalone deployment is not required. Configuration, runtime data, and host-derived authority are
separate. Every custom wire field has local semantics, a type/version, and a conforming example.

The Service can participate in several Domain scopes and compose Services or Modules. Its own Spec
contains necessary business rules and required collaborator contracts; scope and component parents
and provider Specs are not implicit context. Features may have stable IDs anywhere in the registered
Markdown collection. Selecting a Feature does not reduce that complete collection.
