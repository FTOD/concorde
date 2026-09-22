# Task subagents and the user session

Source authoring and independent testing use Task subagents, sibling Pi Agents with explicit task grants. This is not a product planning stage or a new scheduler.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Task subagent](../module.md#terminology) | Defined in Concorde Framework. |
| [User session](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |

## Fresh source-maintenance selection

Source maintenance starts a new Concorde-catalog-free writer in a candidate, never a fork carrying
old instructions. The user session may directly author profiles, prompts, tools, workflows and process repairs in its own exclusive
tree within task authority; it never mutates an active sibling's tree or frozen launch governance. After the writer checks,
commits and stops, the user session chooses independent testing as none, targeted or full with scope and reason.
When selected, the user session starts a separate fresh sibling tester in the same candidate. Both
disable inherited/discovered Concorde catalogs; only the tester explicitly loads the candidate Pi
entry. Failed tests within a coherent stage return to its author, then a fresh tester when selected.
Neither child delegates tasks. Ordinary milestones preserve continuity; after a completed stage
with changed goals/context, the user session may select a fresh author after a durable handoff and exact
stop/release/bind. Independent components may run in separate worktrees before a combination gate.

### Source user session discussion and task collection

The source user session can answer questions, inspect relevant sources and clarify changes without starting
maintenance. It can retain a sufficiently discussed actionable change as a lightweight TODO note
when the user requests or approves recording. Maturity concerns the goal, scope and expected
behavior, not a detailed plan or verified Spec. An underspecified TODO request leads to a choice
between more clarification and saving an issue, not an automatic record. This keeps open questions
out of the actionable list without losing the user's option to retain an immature concern.

The notes preserve the discussion's rationale and decisions for later work rather than replacing
planning or implementation artifacts. The user session updates the same change instead of duplicating it.
Promotion of a mature issue transfers its relevant background before removing its source, with
consent, write verification and unresolved-content safeguards. Ordinary Issue dispositions still
retain observations under the [Issues storage contract](../issues/execution-reference.md#issues-disposition-boundary);
record transfer does not claim a verified resolution or change that runtime API. Unsafe deletion
or associated-record ownership conflicts preserve the source instead of widening authority.

Collection is always available, not another mode, Operation or delegated task. Recording alone
creates no maintenance candidate or child ownership record and changes no implementation or Spec.
Explicit implementation requests still use maintenance; an accumulated list never triggers work
without a user request. The [collection scenarios](scenarios.md#scenario.distribution.user-session-todo-collection)
define the source user session instruction contract, not a promise of deterministic model decisions.
These instructions use the existing user-session-only projection boundary and never ship to consumers.

### Coordination and validation

The user session owns a lightweight high-level decomposition of work packages, dependencies, file/contract
ownership, worktrees, native workflow steps, component acceptance and integration/testing gates.
This is NOT Concorde product plan/tasks and requires neither a planner Operation nor a coordinator
LLM. The user session can author an ad-hoc native workflow or select a predeclared one; its steps are terminal Pi
workers, not additional orchestrators. The user session owns continuation and integration authorization. Source user session instructions make primary status registration a launch
prerequisite: each candidate has a verified stable task identity before its maintenance child starts,
then the user session binds the actual launched child rather than a workflow container. Before transferring
ownership to a tester or resumed author, the user session verifies the previous child stopped, releases that
exact owner and verifies the new binding. Failed registration or handoff stops dependent work;
run evidence and mission notes cannot replace status. Terminal records remain available, and
integration and separately authorized cleanup stay distinct. These are host-coordination duties,
not a new runtime or child grant; the [Task subagent scenario](scenarios.md#scenario.distribution.task-subagents)
defines the instruction obligation. Already-running sessions retain their loaded instructions.
Maintenance directly edits and self-checks, never delegates or
integrates. Tester starts fresh, keeps governing artifacts read-only and returns failures rather
than repairing. Its command tool uses the existing OS read-only check executor with disposable
external fixtures and the trusted tester-only scratch-backed private `/tmp` profile; unavailable
isolation fails closed. Real host `/tmp` inputs use the explicit read-only `CONCORDE_TEST_HOST_TMP`
view, except governing/runtime locations preserved at their canonical names. This permits normal
nested terminal preparation without staging runtime assets or making host `/tmp` writable.
The command schema admits command/timeout and explicit relative report names, never mounts or
export destinations. The [Host evidence handoff](../harness/execution-reference.md#execution-tester-evidence)
preserves selected nonsecret reports and bounded output in canonical primary run evidence before
scratch cleanup, with digest/completeness/truncation facts and compact references. A failed export
or scratch path alone is not retained evidence. This narrow service grants no tester status writes
or arbitrary primary writes; it does not weaken the read-only execution policy.
Explicit extension lists disable ambient
catalogs without granting additional tools. Effective discovery/preflight remains host-owned.

Local edits need format/static/targeted checks, coherent changes affected integration, final
stable input one full Python suite and applicable gates. Stage handoff alone adds no full suite;
a same-tree commit only needs HEAD/bootstrap checks. Changed relevant input/environment invalidates
corresponding evidence. Same-input reruns state their reason; self-tests never become independent.
Same-session complete unchanged Specs need no repeated bundle read; new seams/readers do.
Resource handoff requests distinguish observed capacity/current input/cache/reserve/compaction
from cumulative usage, document size or missing tools. Unknown metrics remain unknown and the user session
verifies handoff need; quality concerns are separately labelled.
