---
id: feature.concorde.record-workflow-reflections
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.commands.project-workflow
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
project-control reflection log. Maintainers can explicitly investigate and route it; a validated merge
of a small `fast-loop` fix removes its matching open entry automatically, while every other route
retains explicit maintainer disposition without duplicating identity or silently changing status.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.agent-assets` | Supplies canonical reflection grammar, orchestrator, and roles. |
| `entity.concorde.runtime` | Supplies deterministic queue, allocation, plan-state, and merged-removal behavior. |
| `entity.concorde.coding-agent` | Records entries/occurrences during work and performs explicitly assigned triage. |
| `entity.concorde.control-state` | Holds the sole tracked `.concorde/reflections/log.md` authority beside triage configuration/scratch state. |

## Interfaces

### `interface.concorde.reflections` — Record and triage project reflections

- **Consumer**: Workflow phases, maintainer, and supported reflection investigator/implementer agents.
- **Direction**: Encountered problem/choice to append-only record; explicit triage to plans/worktree
  commits/merge, deterministic removal for merged small fixes, or maintainer disposition for other routes.
- **Entry points**: Phase reflection rules, `reflections-triage` skill, and installed
  `reflections_queue.py --allocate-id` / `--remove-merged` helper operations.
- **Inputs**: Selected feature ID, phase/date/kind, stable concern path/ID, expected/observed/effect/action/improvement, and explicit triage request.
- **Outputs**: Atomically allocated never-used ID, unique project-log entry/occurrence, validated queue/plan/worktree state, implementer
  commit, merge result, exact removed-entry manifest for eligible small fixes, and maintainer-owned
  status/note for retained entries.
- **Obligations**: Keep one identity/prose authority; never reuse removed IDs; avoid secrets; isolate
  worktrees; preserve status/note for retained entries; remove an entry only when its `small`
  `fast-loop` plan is `merged`, `recorded_under` matches the entry feature, its commit is present in
  current history, and automated merge validation passed; allocate every new ID from a tracked log
  high-water marker rather than the current entries; never treat reflection as behavioral intent.
- **Failures**: Malformed/unresolved entries, duplicate identity, stale or non-ancestor commit,
  ineligible route/effort/status, unsafe worktree/merge, or verification failure preserves the complete
  log and sources.
- **Compatibility**: Profile 7 control paths and Reflection Log v1 grammar remain stable;
  reflection-triage/v3 adds durable ID allocation and removes eligible merged-small entries instead
  of requiring maintainer closure.
- **Implementing entities**: `entity.concorde.agent-assets`, `entity.concorde.runtime`, `entity.concorde.coding-agent`, `entity.concorde.control-state`.

## Usage Scenarios

1. A phase encounters a new difficult choice/problem, allocates the next ID atomically from the
   tracked log high-water marker, appends a valid entry, and continues safe work; a repeated retained
   problem appends an occurrence.
2. A maintainer invokes triage; investigators produce evidence-backed routes/plans without changing the log's decision state.
3. Implementers work in isolated owned worktrees; only validated commits merge.
4. After a `small` `fast-loop` merge, the parent marks the plan `merged` and invokes deterministic
   removal of exactly that matching open entry without a maintainer status/note step.
5. `specify`, `dismiss`, `blocked`, failed, and non-small work remains in the log until explicit
   maintainer disposition.

## Requirements

- **FR-001**: `.concorde/reflections/log.md` MUST remain the sole tracked identity/prose/status/occurrence authority for entries that remain active or await disposition.
- **FR-002**: Entry IDs MUST be unique and never reused, required fields/path references MUST validate,
  and maintainer status/note MUST be preserved for retained entries.
- **FR-003**: Repeated problems MUST append occurrences rather than duplicate entries.
- **FR-004**: Triage plans/worktrees/agents MUST be explicit, isolated, ownership-bounded, and validated before merge.
- **FR-005**: Reflection content MUST NOT be copied into architecture, feature designs, attempts, code, tests, diagrams, or generated releases.
- **FR-006**: After validation and merge, a plan with `route: fast-loop`, `effort: small`,
  `status: merged`, a recorded commit reachable from current `HEAD`, and a matching open entry MUST be
  eligible for one deterministic atomic log-removal operation without maintainer approval.
- **FR-007**: The removal operation MUST validate every requested ID before mutation, remove only exact
  eligible entry blocks, report removed IDs, and preserve the complete log on any ineligible, missing,
  malformed, stale, or write failure.
- **FR-008**: Plans on `specify`, `dismiss`, or `blocked` routes and failed/unmerged/non-small plans
  MUST NOT remove their entries automatically.
- **FR-009**: The tracked Reflection Log v1 preamble MUST persist a monotonic high-water ID greater
  than or equal to every current or previously used reflection ID; every new entry MUST obtain its ID
  through one atomic `--allocate-id` operation, and removal MUST never lower or reuse that value.
- **FR-010**: Allocation/removal MUST reject a missing, malformed, stale, or inconsistent high-water
  marker before mutation and preserve log bytes on failure.

## Edge Cases

- A path is renamed by the source-profile migration while the reflection meaning and ID stay unchanged.
- A resolved/dismissed entry recurs; occurrence is recorded without reversing the maintainer decision.
- A removed small problem recurs after closure; it receives the next never-used ID rather than reusing
  the removed identity.
- Several merged IDs are requested together and one is ineligible; the complete log remains unchanged.
- The high-water marker is below a current or retained-plan ID; allocation and removal stop without
  mutation until the tracked marker is reconciled.
