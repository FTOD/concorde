---
id: feature.concorde.record-workflow-reflections
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.skills.compose-workflow
interfaces:
  provided:
    - interface.concorde.reflections
  required:
    - contract.concorde.workflow
evidence_status: partial
---

# Feature Design: Record and Triage Workflow Reflections

## Outcome and Scope

Every planning/implementation difficulty or provisional design choice is appended to the one tracked
project-control reflection log, and maintainers can explicitly investigate, route, implement, merge, and decide it
without duplicating identity or silently changing status.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.extension-package` | Distributes canonical reflection grammar, orchestrator, roles, and queue helper. |
| `entity.concorde.coding-agent` | Records entries/occurrences during work and performs explicitly assigned triage. |
| `entity.concorde.control-state` | Holds the sole tracked `.concorde/reflections/log.md` authority beside triage configuration/scratch state. |

## Interfaces

### `interface.concorde.reflections` — Record and triage project reflections

- **Consumer**: Workflow phases, maintainer, and supported reflection investigator/implementer agents.
- **Direction**: Encountered problem/choice to append-only record; explicit maintainer triage to plans/worktree commits/merge/status decision.
- **Entry points**: Phase reflection rules, `reflections-triage` skill, and installed `reflections_queue.py` helper.
- **Inputs**: Selected feature ID, phase/date/kind, stable concern path/ID, expected/observed/effect/action/improvement, and explicit triage request.
- **Outputs**: Unique project-log entry/occurrence, validated queue/plan/worktree state, implementer commit, merge result, and maintainer-owned status/note.
- **Obligations**: Keep one identity/prose authority, preserve existing status/note, avoid secrets, isolate worktrees, and never treat reflection as behavioral intent.
- **Failures**: Malformed/unresolved entries, duplicate identity, stale plan, unsafe worktree/merge, or verification failure preserves open state and sources.
- **Compatibility**: Profile 7 moves the log and reflection-triage/v2 locator while Reflection Log v1 IDs/status/meaning remain stable.
- **Implementing entities**: `entity.concorde.extension-package`, `entity.concorde.coding-agent`, `entity.concorde.control-state`.

## Usage Scenarios

1. A phase encounters a difficult choice/problem, appends a valid entry or occurrence, and continues safe work.
2. A maintainer invokes triage; investigators produce evidence-backed routes/plans without changing the log's decision state.
3. Implementers work in isolated owned worktrees; only validated commits merge, then the maintainer chooses status/note.

## Requirements

- **FR-001**: `.concorde/reflections/log.md` MUST remain the sole tracked identity/prose/status/occurrence authority.
- **FR-002**: Entry IDs MUST be unique/never reused, required fields/path references MUST validate, and maintainer status/note MUST be preserved.
- **FR-003**: Repeated problems MUST append occurrences rather than duplicate entries.
- **FR-004**: Triage plans/worktrees/agents MUST be explicit, isolated, ownership-bounded, and validated before merge.
- **FR-005**: Reflection content MUST NOT be copied into architecture, feature designs, attempts, code, tests, diagrams, or generated releases.

## Edge Cases

- A path is renamed by the source-profile migration while the reflection meaning and ID stay unchanged.
- A resolved/dismissed entry recurs; occurrence is recorded without reversing the maintainer decision.
