# Agents scenarios

These scenarios specify discovery, Agent admission and Task subagent collaboration without duplicating business acceptance.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Agent](../module.md#terminology) | Defined in Concorde Framework. |
| [Task subagent](../module.md#terminology) | Defined in Concorde Framework. |
| [User session](../module.md#terminology) | Defined in Concorde Framework. |
| [Registration](module.md#terminology) | Defined in Agents. |

### scenario.agents.inventory — One authority for all callable Agents

- GIVEN the canonical seven Domain Agents and two Task subagents
- WHEN source build and consumer rendering discover and project those Agents
- THEN domain admission resolves the same canonical definitions and source discovery supplies both Task subagents
- AND consumer registration supplies tester but excludes source maintenance/coordinator instructions
- AND an unknown Agent, missing source or metadata drift fails rather than admitting a second definition
- AND the user session remains an external session, not a registered tenth Agent

### scenario.distribution.task-subagents — Discoverable Task subagents with separate distribution

- GIVEN a source build or a full local consumer installation and supported pi-subagents in the user session
- WHEN the user session resolves project agents by the exact names maintenance-worker and tester
- THEN source discovery supplies both canonical fresh-context Task subagents while consumers receive only generic tester
- AND source-only coordinator/maintenance prompts never enter the installed package
- AND actual Pi resource loading supplies coordinator instructions only to the source user session, not to fresh/resumed maintenance-worker, tester or terminal node prompts
- AND migration retires only the exact previously build-owned unconditional append, refuses edited owned bytes before writing, and preserves unrelated user append content during consumer install/update
- AND explicit child extensions disable ambient catalogs, delegation tools are absent and tester commands enforce read-only governing artifacts with external scratch
- AND user-owned agent-file collisions and modified owned definitions block replacement, while unchanged owned updates retain receipt verification
- AND the user session chooses check/test scope and continuation, maintenance performs self-checks without independent claims, and tester returns failures without self-repair
- AND source user session instructions require verified primary status registration before maintenance launch, reuse/reconciliation of the actual stable change identity and immediate binding of the actual launched child rather than a workflow container
- AND those instructions require a verified stopped child and release of its exact existing ownership before a tester or resumed-author handoff, with failed registration, launch or binding stopping dependent work without claiming success or overwriting another coordinator's status
- AND run evidence, coordinator notes and mission records cannot replace canonical status; terminal history remains while integration and separately authorized cleanup stay distinct
- BUT rebuilding source user session instructions does not retroactively update already-running peer sessions

### scenario.distribution.user-session-todo-collection — Collect mature notes in the source user session only

- GIVEN a source user session discussing an actionable change whose key goal, scope and expected behavior are settled
- WHEN build projects its canonical coordinator instructions
- THEN those instructions permit recording only on explicit user request or approval, with discussion alone producing no record and an offer to record appropriate only after a concrete actionable conclusion rather than every message
- AND they require one Markdown task per file under `.concorde/todos/`, the directory serving as the list without a redundant index, and updating an existing task for the same change instead of duplicating it
- AND each note preserves substantive context, motivation, agreed behavior, important decisions, alternatives and reasons, boundaries, non-goals, necessary examples and source issue references rather than a bare title or transcript
- AND recording requires durable writing and rereading to verify complete content before success, preserving prior records on failure and refusing unsafe paths or concurrent overwrites
- AND notes are not planner outputs or paired Spec units and need no detailed implementation plan, Spec verification, metadata companion, registry entry or heavyweight collection pipeline
- AND recording changes only TODOs and authorized issue records, with no implementation or Spec edits, candidate creation, maintenance launch, status registration or child binding
- AND explicit implementation requests retain the maintenance flow, unclear intent is clarified, and batching never starts from task count without an explicit user request
- AND the capability is always available without a new mode, tool, agent or Operation and appears only in source user session instructions, absent from maintenance-worker, tester, terminal workers and installed consumer assets

This is an instruction and projection contract; deterministic text checks do not establish live
model compliance with consent or maturity judgments.

### scenario.distribution.user-session-todo-unsettled — Ask before retaining immature or non-actionable discussion

- GIVEN an explicit TODO request with unsettled goal, scope or expected behavior, or a settled discussion with no remaining action
- WHEN source user session instructions describe how to respond
- THEN an underspecified request requires asking whether to continue clarification or save an issue and waiting for the user's choice, with neither an immature TODO nor an issue saved automatically
- AND an issue may retain an immature concern under existing project conventions
- AND a conclusion requiring no further action produces no TODO, with any issue closure or deletion requiring separate confirmation

### scenario.distribution.user-session-todo-promotion — Preserve issue background before authorized transfer

- GIVEN user confirmation to move a mature issue into TODO
- WHEN source user session instructions describe promotion
- THEN that confirmation also authorizes deletion of the corresponding issue without redundant approval, but only after reading the whole issue and associated records, durably writing all relevant background, observations, decisions and reasons with source references, and rereading to verify the task
- AND failed task writing or verification preserves the source, while failed deletion retains both copies and reports a partial transfer whose retry updates the same task
- AND partial resolution of a multi-part issue preserves still-unresolved source content and records only the mature actionable part
- AND actual issue storage, associated metadata, live references, permissions and ownership/concurrency rules remain binding, with unsafe deletion preserving the source and reporting the blocker rather than orphaning records or widening authority
- AND promotion is record transfer rather than a solver disposition or verified resolution, leaving immutable report semantics and ordinary retained disposition history unchanged

### scenario.distribution.stage-continuity — The user session owns stages and integration

- GIVEN authorized source maintenance with independent work packages
- WHEN source coordination instructions are rendered
- THEN the user session owns high-level decomposition, file/contract ownership, native workflow steps and component/integration/testing gates without invoking product plan/tasks
- AND the user session may directly repair profiles, prompts, tool configuration and workflows within its own exclusive tree and task authority without changing active siblings' frozen grants
- AND unfinished coherent stages reuse their author through feedback while completed stages with changed goals/context may use a fresh author after durable handoff and exact stop/release/bind
- AND separate component worktrees do not imply combination success, automatic merge, cleanup or child task delegation
