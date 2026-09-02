# Framework overview

Concorde makes architecture navigable at the same scale as the work being done. A maintainer can
enter at one module, see its immediate structure and interfaces, then open one feature file without
loading the entire repository.

## What Concorde provides

- a recursive module hierarchy with one structural authority per level;
- typed architecture entities and directed relationships rather than an untyped prose inventory;
- one complete direct Markdown file per level-local feature;
- embedded feature interfaces with stable identities and usage/failure semantics;
- bounded Protocol 12 context for planning and coding agents;
- deterministic validation of layout, identity, references, safety, and freshness;
- temporary attempt workspaces with task/evidence discipline; and
- digest-bound, cleanup-only delivery.

## Standalone lifecycle boundary

Concorde owns the complete lifecycle. Root `commands/` and `templates/` are canonical human-readable
instructions/formats; `src/concorde/` and `scripts/` own deterministic operations; `concorde.json`
owns one package identity. The native installer projects those sources under `.concorde/framework/`
and into Codex or Claude, recording only generated framework/agent outputs in
`.concorde/install.json`. Project configuration, selection, constitution, attempts, reflections,
specifications, code, and tests remain project-owned.

The `speckit-*` command IDs are temporary compatibility labels. They do not delegate any phase or
template behavior to another framework.

## Authority map

| Question | Source |
|---|---|
| What does this module own and exclude? | Its `architecture.md` responsibility and boundary. |
| What significant things exist here? | The architecture entity inventory with IDs, types, definitions, and locators. |
| How do they connect and collaborate? | Directed relationships and representative interactions in architecture. |
| What can a consumer use at this level? | The module's direct feature inventory and each `features/<NNN-name>.md`. |
| What enters, leaves, can fail, and must remain compatible? | The owning feature's embedded interface definition. |
| How does this feature use module structure? | Its Architecture Zoom referencing architecture entity IDs. |
| How does it currently work in this revision? | Source code. |
| What evidence supports it? | Executable tests/checks and active attempt validation evidence. |
| What went badly or remains provisional? | `.concorde/reflections/log.md`. |
| What does the website or diagram show? | A generated projection with provenance back to architecture/feature sources. |

## Bounded reading

A module architecture shows immediate child modules as bounded entities; child internals stay in the
child architecture. A feature may reference entities visible in its providing module or permitted
ancestry. Related features are stable-ID relationships, not containment. Protocol 12 returns concise
ancestry and related-feature summaries, while another feature file is opened only for a specific
interface dependency.

This keeps context useful without pretending that generated summaries are authority.

## Workflow principle

Specification owns feature behavior and interfaces. Architecture owns entity identity and
relationships. Planning compares those sources with current code/tests and writes only temporal
artifacts. Explicit tasks may reconcile all affected authorities together. Delivery then verifies
the repository is already reconciled and removes the attempt; it does not author new durable prose.

## Prototype policy

Profile 7 is a breaking source profile. Concorde does not run a dual reader for older and current
layouts. This keeps loaders, validators, agent guidance, fixtures, publication, and packages on one
coherent ontology. Difficult tradeoffs and knowingly provisional choices are recorded in the
project reflection log so the prototype can proceed and be revised later. Reflection-triage/v3
automatically removes only validated merged-small fast-loop problems; every broader or unresolved
entry remains for maintainer disposition.
