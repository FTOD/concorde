---
id: module.concorde.reflections
kind: module
parent: module.concorde
modules: []
features:
  - feature.reflections.record-and-triage
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-reflections-system-overview.html
---

# Architecture: Reflections

## Responsibility

Record one tracked problem per file during workflow phases and triage it through the conditional
permission-bounded reflection Operation until maintainer disposition closes it.

## Boundary

Reflections owns the Reflection Document v2 grammar and template, the per-file collection under
`.concorde/reflections/` with its `pending/`, `planned/`, `needs-comments/` buckets and metadata-only
allocation index, the deterministic reflection queue Tool (allocate-id, validate-entry, relocate,
remove-merged/remove-closed with plan cleanup, plan/merged-small state), the reflection parsing/validation rules, the paired
`concorde-reflections-triage` Operation with its status/investigate/implement/merge/close branches,
and the internal investigator/implementer agent roles and their Codex/Claude projections. It does not
own the lifecycle phases that record reflections (`module.concorde.lifecycle`), the Operation
runtime/policy enforcement (`module.concorde.capabilities`), or Protocol 13
(`module.concorde.understanding`). It may investigate a Concorde Protocol problem read-only, but it
never implements, merges, or closes a normative Protocol semantic change through reflection routes;
the root `feature.concorde.evolve-protocol` owns that cutover.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.reflections.template` | document | Complete per-file Reflection Document v2 grammar: required front matter, Context/Expected/Observed/Impact/Evidence problem sections, Triage Analysis/Proposed Resolution/Intervention Rationale triage sections, a retained User Comments section, and optional Occurrences. | `templates/reflections-template.md` |
| `entity.reflections.collection` | directory | Per-file process memory holding one open `R-NNN.md` prose authority per problem, filed into `pending/`, `planned/`, or `needs-comments/` by triage state. | `.concorde/reflections` |
| `entity.reflections.index` | configuration | Metadata-only allocation record holding schema version and the monotonic, never-reused ID high-water mark. | `.concorde/reflections/index.json` |
| `entity.reflections.worktrees` | directory | One committed-base linked checkout established before a mutating triage action, shared by its investigation/plan/implementation sequence and never bootstrapped from primary dirty state. | `concept:.concorde/reflections/worktrees` |
| `entity.reflections.document-model` | package | Parses Reflection Document v2 front matter/sections and derives each document's canonical path, bucket, and occurrences. | `src/concorde/reflections/reflections.py` |
| `entity.reflections.collection-rules` | program | Adds project-wide shape, duplicate, vocabulary, and placement rules for every reflection document during validation. | `src/concorde/reflections/validation.py` |
| `entity.reflections.queue` | program | Deterministic per-file queue Tool: atomic ID allocation, bounded per-entry validation, front-matter-driven relocation, derived plan verification state, plan/merged-small state transitions, and merged/closed document removal that deletes the reflection's plan with it. | `scripts/reflections_queue.py` |
| `entity.reflections.triage-operation` | program | Action/route-conditional investigation, fast-loop/nested-plan implementation, and validation LangGraph that selects only the capabilities reachable for one explicit status/investigate/implement/merge/close request. | `operations/concorde-reflections-triage/operation.py` |
| `entity.reflections.triage-skill` | document | Installed `reflection-triage/v5` action/route/bucket/policy contract paired with its graph. | `operations/concorde-reflections-triage/SKILL.md` |
| `entity.reflections.assets` | directory | Internal reflection investigator/implementer roles, default triage configuration, and Claude/Codex projection templates. | `agent-assets/reflections` |
| `entity.reflections.investigator-role` | document | Read-only investigation prompt: establishes root cause, proposes a resolution, chooses exactly one route, and decides human intervention without writing. | `agent-assets/reflections/roles/investigator.md` |
| `entity.reflections.implementer-role` | document | Worktree-scoped implementation prompt: carries out only validated `fast-loop` plans and never edits maintainer-owned fields. | `agent-assets/reflections/roles/implementer.md` |
| `entity.reflections.asset-projector` | program | Renders canonical role bodies through integration templates into owned, digest-tracked Claude/Codex subagent projections. | `src/concorde/reflections/agent_assets.py` |
| `entity.reflections.claude-agents` | directory | Generated Claude investigator/implementer subagent files bound to `reflection-triage/v5`. | `.claude/agents` |
| `entity.reflections.codex-agents` | directory | Generated Codex investigator/implementer subagent profiles bound to `reflection-triage/v5`. | `.codex/agents` |
| `entity.reflections.tests` | test | Parser, rule, queue, operation-branch, and installed-asset evidence for reflection semantics. | `tests/concorde/reflections` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.reflections.triage-skill` | `documents` | `entity.reflections.triage-operation` | Supplies the installed `reflection-triage/v5` action/route/bucket/policy contract paired with the graph. |
| `entity.reflections.triage-operation` | `composes` | `module.concorde.lifecycle` | Uses the public analyze, fast-loop, plan, tasks, implement, and validate direct capabilities for the investigate, route, implement, and validate stages without taking ownership of their internals. |
| `entity.reflections.triage-operation` | `calls` | `entity.reflections.queue` | Invokes the deterministic queue Tool for status, relocation, merged-removal, and closed-removal actions outside the graph. |
| `entity.reflections.queue` | `reads_from` | `entity.reflections.collection` | Loads every tracked document before validating bucket placement or allocating an identifier. |
| `entity.reflections.queue` | `writes_to` | `entity.reflections.collection` | Creates, relocates, and removes exactly the reflection documents its explicit action selects, deleting each removed document's plan with it. |
| `entity.reflections.queue` | `reads_from` | `entity.reflections.index` | Reads the current allocation high-water mark before minting a new identifier. |
| `entity.reflections.queue` | `writes_to` | `entity.reflections.index` | Atomically raises the high-water mark and never lowers or reuses an identifier. |
| `entity.reflections.document-model` | `validates` | `entity.reflections.collection` | Parses front matter/sections and rejects a malformed, duplicate, or misplaced document. |
| `entity.reflections.collection-rules` | `validates` | `entity.reflections.collection` | Runs project-wide `CONCORDE-REFLECT` shape, duplicate, vocabulary, and placement checks over every entry. |
| `entity.reflections.assets` | `contains` | `entity.reflections.investigator-role` | Bundles the read-only investigator prompt among the internal reflection support assets. |
| `entity.reflections.assets` | `contains` | `entity.reflections.implementer-role` | Bundles the worktree-implementer prompt among the internal reflection support assets. |
| `entity.reflections.asset-projector` | `reads_from` | `entity.reflections.assets` | Loads the manifest and projection templates that bind each role body to its target surface. |
| `entity.reflections.asset-projector` | `transforms` | `entity.reflections.claude-agents` | Renders the investigator and implementer role bodies through Claude Markdown templates into generated subagent files. |
| `entity.reflections.asset-projector` | `transforms` | `entity.reflections.codex-agents` | Renders the investigator and implementer role bodies through Codex TOML templates into generated subagent profiles. |
| `module.concorde.lifecycle` | `writes_to` | `entity.reflections.collection` | Plan and task phases record one problem-only document per concern before triage ever runs. |
| `entity.reflections.triage-operation` | `depends_on` | `module.concorde.capabilities` | Requires per-leaf policy compilation and enforced launch for every direct capability occurrence it selects. |
| `entity.concorde.coding-agent` | `implements` | `entity.reflections.investigator-role` | Follows the read-only investigation prompt within its zero-write policy. |
| `entity.concorde.coding-agent` | `implements` | `entity.reflections.implementer-role` | Follows the worktree-implementation prompt within its narrowed write policy. |
| `entity.reflections.triage-operation` | `generates` | `entity.reflections.worktrees` | Before investigation persistence or implementation, creates or enters one linked worktree at committed primary `HEAD`; all later stages stay there and never import primary dirty state. |
| `entity.reflections.triage-operation` | `tested_by` | `entity.reflections.tests` | Branch tests prove status/investigate/implement/merge/close exclusivity and worktree scope. |
| `entity.reflections.queue` | `tested_by` | `entity.reflections.tests` | Allocation, relocation, and removal cases establish bucket and index invariants. |
| `entity.reflections.document-model` | `tested_by` | `entity.reflections.tests` | Parser cases establish shape, vocabulary, and occurrence-append evidence. |
| `entity.reflections.collection-rules` | `tested_by` | `entity.reflections.tests` | Rule cases establish duplicate, vocabulary, and placement diagnostics. |

## Relationship Types

| Predicate | Direction and meaning |
|---|---|
| `composes` | From a controlling Operation to a direct canonical Skill or public Operation whose identity/result it sequences without taking ownership or flattening internals. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.reflections.record` | A lifecycle phase meets a new or repeated concrete problem. | Allocate a never-used ID with the queue Tool; create the returned `pending/` document with only Context, Expected, Observed, Impact, and Evidence and a retained blank User Comments section, or append an Occurrences item to an existing document instead of allocating another identity; immediately run `--validate-entry` and correct only that new entry until it reports valid. | One problem-only document or occurrence exists under `pending/` with an unmoved, un-lowered allocation index. | `interface.concorde.reflections` |
| `interaction.reflections.triage` | A maintainer or the triage Operation selects `status`, `investigate`, `implement`, or `merge` for one or more reflections. | `status` remains read-only; before any persistence, create or enter one linked worktree at committed primary `HEAD` and exclude all primary dirty state; describe only reachable capabilities and require policy; run investigation, parent-authored plan/relocation, and the selected implementation route in that same worktree without nested stash-based bootstrap; reject Protocol-semantic implementation/merge/close in favor of the root cutover; validate before explicit integration. | Exactly one eligible route's capabilities executes in one owned worktree, the document lands in its required bucket, an eligible merged small fix is removed with its plan, or Protocol evolution stops before lifecycle mutation. | `interface.concorde.reflections`, `contract.capabilities.permission-bounded-execution`, `contract.lifecycle.plan` |
| `interaction.reflections.close` | A maintainer records `status: resolved` or `dismissed` plus a `resolution_note` on a `needs-comments/` document. | Run the `close` action's deterministic removal on the named identifiers or every closed document when none are named; validate every requested ID before mutation; remove exactly those documents and their plans atomically with rollback on any ineligible or missing entry; commit the removal with each resolution note in the message. | The collection retains only open documents while every disposition reason survives in Git history. | `interface.concorde.reflections` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.reflections.record-and-triage` | Record one detailed per-file reflection document per problem and triage it through explicit status/investigate/implement/merge/close actions until a merged small fix or maintainer disposition removes it. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the
  principal entities and directed relationships in this architecture.
- Every reflection has exactly one tracked `R-NNN.md` prose authority; no file holds more than one
  problem and no problem spans more than one file.
- A document's bucket folder is a pure function of its `triage`/`human_intervention` front matter and
  mirrors triage state and nothing else; only the deterministic relocation Tool may move it.
- `index.json` holds only the schema version and the monotonic allocation high-water mark; it never
  becomes a second prose log and never lowers or reuses an identifier.
- A closed reflection (`status: resolved | dismissed` plus a `resolution_note`) is deleted by the
  `close` action rather than retained; Git history keeps the record.
- The investigator and implementer roles are internal support for the paired Operation, not
  additional user-facing capabilities; only the Operation and its Skill project publicly.
- Investigation may analyze a Concorde Protocol problem, but every implementation/merge/close route
  that would change normative Protocol semantics stops before mutation and delegates to the root
  Protocol-evolution feature.
- Plans under `.concorde/reflections/plans/` and checkouts under `.concorde/reflections/worktrees/`
  are ignored scratch state, never a specification or implementation authority. A plan never
  outlives its reflection: merged-small and closed removal delete the plan with the document in one
  atomic action, and `status` reports any plan left without a document as an orphan.
- Mutating triage establishes its linked worktree before investigation or plan authorship and keeps
  every later stage there. It never snapshots, stashes, copies, or otherwise materializes dirty
  primary-worktree files; a missing committed concern/feature/plan input stops the route.
- A reflection's status is re-verified by the acting agent at the start of every investigation and
  implementation attempt; a plan carries only the last verification (`verified`, `verified_commit`)
  as scratch coordination state, the queue derives `current | stale | unverified` from it on every
  read, and no stored field is ever the problem's status.
