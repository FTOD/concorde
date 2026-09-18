# Concorde source-checkout rule sources

This file is a navigation index, not a second rule bundle or a separate specification language.
The current checkout accepts Spec Protocol **10.0.0**, Framework **Profile 15** and registry schema
**5**. Workspace Protocol **16** and Delivery Proposal **10** remain separate compatibility gates.
The exact accepted Protocol version and manifest digest are recorded in `.concorde/config.json`.

## Canonical authorities

- Read `.concorde/protocol/principles.md` for the complete accepted Spec Protocol and Framework
  execution profile, including P10 session handoffs. The tracked installed copy and its asset
  digests are refreshed from authoring sources, never edited independently.
- `protocol/` authors the independent specification standard: principles, Module specifications,
  management, exact context selection, required format and canonical templates.
- `prompts/protocol/framework-profile.md` authors Concorde's execution profile. It governs complete
  Operations, bounded contexts, permission ceilings, trusted execution services, review evidence
  and worktree handoffs. It does not turn Framework execution policy into a consumer language rule.
- `AGENTS.md` supplies this source checkout's direct-maintenance, worktree ownership, build,
  formatting and English-Spec conventions. It does not authorize starting a Concorde graph without
  the developer's explicit request.

After changing Protocol authoring sources, build and explicitly refresh the accepted binding with
`python3 scripts/concorde.py protocol-manifest --write --bind-project`. Validate the resulting
sources and projections; installation and ordinary execution never silently accept another binding.

## Project specification and execution

`.concorde/specs.json` registers `module.concorde` as the entry Module. Its reading entry and
`specs/concorde/concepts.md` introduce complete Operations and distinguish Module responsibility
ownership, Operation composition and explicit context references. The Operations hierarchy includes
composed development and specification providers without making called providers their children.

Module Specs explain purpose, terminology, usage, design and relationships. Implementation Specs
hold precise requirements, scenarios and canonical contracts. Both roles and both source members
belong to complete Spec context; neither publication nor a prose link changes that context or
execution authority. The canonical bundle defines the exact obligations. Deterministic checks and
coverage declarations are evidence, not proof of semantic completeness.

## Retired index content

At baseline `7af5a831220091693695fa92b71079d9f10c5bd7`, this file still advertised Protocol 6,
Profile 13 and an obsolete two-part reading structure, despite the checkout's accepted Protocol 9 /
Profile 14 binding. Those stale claims are retired, not an alternate compatibility policy. Their
original bytes remain in Git history. The Operations migration and explicit compatibility policy
are recorded in `docs/changes/operations-graphs.md`; current authority remains the accepted bundle.
