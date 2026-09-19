# Project initialization

This document defines `concorde-init`'s propose/apply behavior. [module](module.md) introduces the Module; [registry](registry.md) and [values](values.md) define the general query and value records this operation builds on.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Initialization | Creating the project's own configuration, registry and first honest specification after the Framework is installed. |
| Initial proposal | The exact new files offered for inspection before initialization is applied. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Registry](../module.md#terminology) | Defined in Concorde Framework. |
| [Protocol binding](values.md#terminology) | Defined in Identities and versions. |
| [Document role](values.md#terminology) | Defined in Identities and versions. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Installation](../distribution/installation.md#terminology) | Defined in Installing and updating Concorde. |

## Propose, inspect and apply

Initialization separates describing a possible project from accepting filesystem changes. Start with
an installed Framework and provide the project name and explicit worker configuration. The proposal
contains the configuration, registry and a paired Module entry with absent-file preconditions;
review those exact bytes before applying. A changed destination or incompatible binding rejects the
proposal rather than overwriting existing project content.

The entry models only known authoring participants. Business purpose, behavior and design remain
explicit gaps until the developer supplies them. It declares role module and explains that future
requirements, scenarios and interface contracts belong in registered implementation-role companions.
It creates no invented acceptance cases to satisfy a template. Existing projects use explicit
maintenance or topology changes, not reinitialization, to migrate their document collections.

`concorde-init` makes no model call. It runs as the host's
[project Graph](contracts.md#graphs-project-graph-project-graph): a
deterministic `select_action` node sends `propose` to the node that builds the proposal and `apply`
to the node that applies an unchanged proposal atomically. Each is a single deterministic node. A
describe-policy request is refused with `use_proposal`, because the proposal already is the preview.

### Protocol compatibility and initialization

New registries use schema 5 with explicit empty `references` on the initial Module; the stub's
schema-2 document metadata names its single `owner` and explicit `role: module`. Initialization pins Protocol 10.0.0/Profile 15 and
the exact manifest digest of the Protocol copy the [Distribution Module](../distribution/module.md) installer placed under `.concorde/protocol/`;
it creates no Protocol file itself and fails with `not_installed` when that copy is absent. Later
installations update the copy but never the binding, which the developer moves explicitly with
`concorde-configure` and `accept_protocol`. A draft identifies missing behavior without inventing external
definitions. Existing projects require an explicit atomic ownership/reference/metadata migration;
an installer must not silently relabel old shared memberships or interpret them as references.
The initializer emits this schema and metadata and validates the proposed overlay before application.

## Precise specifications

The Spec Module owns the exact obligations and interface details in [contracts](contracts.md), [requirements](requirements.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
