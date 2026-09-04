---
id: feature.reflections.record-and-triage
kind: feature
module: module.concorde.reflections
related_features:
  - id: feature.concorde.workflow
    relation: composed_by
  - id: feature.lifecycle.plan-attempt
    relation: depends_on
  - id: feature.lifecycle.fast-loop
    relation: composes
  - id: feature.lifecycle.standard-development-loop
    relation: relates_to
  - id: feature.capabilities.permission-bounded-execution
    relation: depends_on
  - id: feature.concorde.evolve-protocol
    relation: relates_to
interfaces:
  provided:
    - interface.concorde.reflections
  required:
    - contract.capabilities.permission-bounded-execution
    - contract.lifecycle.plan
---

# Feature Design: Record and Triage Reflections

## Outcome and Scope

Every retained workflow problem has one detailed, tracked
`.concorde/reflections/<bucket>/R-NNN.md` document. Lifecycle plan and task phases normally record
only the problem facts and leave triage-owned sections empty. Reflection triage later establishes
root cause, proposes a resolution, and decides whether human intervention is required while
preserving a `User Comments` section for maintainer input. A separate JSON index stores only the
never-reused ID high-water mark; it never becomes another prose log.

The collection is filed into three tracked bucket folders that mirror triage state and nothing
else: `pending/` holds recorded documents triage has not investigated; `planned/` holds completed
triage whose plan may proceed without a maintainer (`human_intervention: not-required`); and
`needs-comments/` holds completed triage waiting for maintainer input in `User Comments`
(`human_intervention: required`). Recording always creates a document under `pending/`, and only the
deterministic relocation Tool moves a document after the parent persists its triage completion.

No stored field records whether a reflection's problem still exists. Every attempt to resolve one,
whether investigation or implementation, begins by re-verifying the recorded Observed behavior
against the current checkout, and the plan carries only that last verification (`verified`,
`verified_commit`, and a `Verification` section) as scratch coordination state. A problem that no
longer reproduces is routed to dismissal, never implemented.

Read-only status may run in the primary worktree. Every triage action that will persist analysis,
author a plan, implement, relocate, merge, or close first creates or enters one linked worktree at
the primary worktree's exact committed `HEAD`. Investigation, planning, and implementation remain in
that worktree; no stage imports staged, unstaged, untracked, or ignored primary state through a stash
or copy. A required input absent from the commit stops the route.

Maintainers can explicitly choose status/investigate/implement/merge/close. The paired
`concorde-reflections-triage` Operation launches only the chosen branch, composing the direct
capabilities `module.concorde.lifecycle` provides under per-leaf policies that
`module.concorde.capabilities` compiles and enforces. A validated merge of a small `fast-loop` fix
removes only its matching reflection file automatically; every other route waits for explicit
maintainer disposition. Once the maintainer records that disposition — `status: resolved` or
`dismissed` plus a `resolution_note` — the deterministic removal Tool deletes the document through
the `close` action, so the collection only ever holds open work and Git history keeps the closed
record.

When a reflection's resolution changes normative Concorde Protocol semantics in the Concorde
repository, status/investigation may remain read-only but implement/merge/close stops before any
lifecycle or reflection-worktree mutation. The maintainer uses
`feature.concorde.evolve-protocol`; its one cutover commit records and closes the disposition in Git
history without a reflection-owned attempt.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.reflections.template` | Defines the Reflection Document v2 grammar every recorded and triaged document must satisfy. |
| `entity.reflections.collection` | Holds one open `R-NNN.md` document per problem, filed by triage state into `pending/`, `planned/`, or `needs-comments/`. |
| `entity.reflections.index` | Tracks only the monotonic allocation high-water mark that the queue Tool advances. |
| `entity.reflections.worktrees` | Isolates a complete mutating triage action from the primary checkout, beginning before investigation/plan persistence and continuing through implementation/validation. |
| `entity.reflections.document-model` | Parses front matter/sections and derives the canonical path and bucket for every document. |
| `entity.reflections.collection-rules` | Adds project-wide shape, duplicate, vocabulary, and placement checks during `concorde validate`. |
| `entity.reflections.queue` | Allocates IDs, validates entries, relocates documents, and removes merged-small or closed documents. |
| `entity.reflections.triage-operation` | Selects and runs only the capabilities reachable for the explicit status/investigate/implement/merge/close request. |
| `entity.reflections.triage-skill` | Documents the installed action/route/bucket contract maintainers and agents follow. |
| `entity.reflections.assets` | Bundles the internal investigator/implementer roles, default configuration, and projection templates. |
| `entity.reflections.investigator-role` | Establishes root cause, a proposed resolution, a route, and the human-intervention decision without writing. |
| `entity.reflections.implementer-role` | Carries out only validated `fast-loop` plans inside an isolated worktree. |
| `entity.reflections.asset-projector` | Renders both roles through integration templates into the installed Claude/Codex subagents. |
| `entity.reflections.claude-agents` | Hosts the generated Claude investigator/implementer subagents. |
| `entity.reflections.codex-agents` | Hosts the generated Codex investigator/implementer subagent profiles. |
| `module.concorde.lifecycle` | Records problem-only documents during its plan/task/analyze/fast-loop phases and supplies the fast-loop, plan, tasks, implement, and validate capabilities triage composes. |
| `module.concorde.capabilities` | Compiles per-leaf policy and enforces the launch boundary for every direct capability occurrence the triage graph selects. |
| `entity.concorde.coding-agent` | Records problem-only documents during workflow phases and performs explicitly assigned investigation or implementation. |
| `entity.concorde.control-state` | Hosts `.concorde/reflections` alongside project configuration, selection, and other control/scratch state. |

## Interfaces

### `interface.concorde.reflections` — Record and triage project reflections

- **Consumer**: Lifecycle plan/task phases, maintainer, and supported reflection investigator/implementer agents.
- **Direction**: Encountered problem to problem-only document; explicit triage action to completed analysis,
  proposed resolution, human-intervention decision, plans/worktree commits/merge, deterministic
  removal for merged small fixes, or maintainer disposition for other routes.
- **Entry points**: Lifecycle plan and task phases' reflection-recording rules, the installed
  `concorde-reflections-triage` Operation Skill and paired graph, and `reflections_queue.py
  --allocate-id` / `--relocate` / `--remove-merged` / `--remove-closed` / `--validate-entry` Tools.
- **Inputs**: For mutating triage, exact committed base plus linked-worktree identity (or explicit
  primary override), with primary dirty bytes excluded. At recording, selected feature ID, phase/date/kind, stable concern path/ID, detailed
  context, expected and observed behavior, impact, and evidence. At triage, one selected reflection,
  an explicit status/investigate/implement/merge/close action, and, for investigate/implement, a
  fresh verification of the problem at the current HEAD.
- **Outputs**: Atomically allocated never-used ID and exact `pending/` document path; one
  problem-only document or occurrence; triage analysis, proposed resolution, intervention
  decision/rationale, preserved User Comments; an exact relocation manifest moving the completed
  document into `planned/` or `needs-comments/`; validated plan/worktree state including the plan's
  verification record and its derived `current | stale | unverified` state; implementer commit;
  merge result; exact removed file manifest for eligible small fixes; exact removed manifest with
  resolution notes for closed documents; and a bounded validation result for one requested entry with
  attributable findings and separately counted unrelated findings.
- **Obligations**: Keep one prose authority per reflection and a metadata-only allocation index;
  never reuse removed IDs; avoid secrets; make status model-free and investigators read-only; keep
  recording separate from analysis; retain User Comments; keep every document in the bucket its
  `triage`/`human_intervention` state requires and move it only through the relocation Tool without
  changing its text; select exactly one route; re-verify the recorded problem at the current HEAD
  before every investigation and implementation attempt, persist that verification on the plan,
  never implement a plan whose problem does not reproduce or whose `verified_commit` is not the
  current HEAD, and never treat any stored field as the problem's status; keep nested planning
  public/opaque; establish isolation before investigation/plan persistence and keep later stages in
  that same worktree; remove a document only when (a) its `small` `fast-loop` plan is `merged`,
  `recorded_under` matches the reflection feature, its commit is present in current history, and
  automated merge validation passed, or (b) a maintainer closed it with `status: resolved |
  dismissed` and a `resolution_note`; never treat a reflection as behavioral intent.
- **Failures**: Primary-worktree mutation without explicit authorization, required input present only
  in primary dirty state, malformed/unresolved documents or index, recording-time triage content, incomplete
  triage, a document filed in a bucket its front matter does not require, invalid
  action/route/policy, unavailable enforcement, duplicate identity, stale or non-ancestor commit,
  ineligible route/effort/status, unsafe worktree/removal/relocation, a missing, stale, or failed
  verification, normative Concorde Protocol evolution, or removing an open document preserves
  retained reflection files and sources. Protocol evolution additionally names its root cutover
  feature before mutation.
- **Compatibility**: Reflection Document v2 replaces the single-file Reflection Log v1. A legacy
  `.concorde/reflections/log.md` is diagnosed rather than accepted in a dual-layout mode.
  `reflection-triage/v5` reserves `tool` for queue helpers and exposes the conditional
  mixed-capability workflow as an exact Python/Markdown Operation pair.
- **Implementing entities**: `entity.reflections.triage-operation`, `entity.reflections.queue`,
  `entity.reflections.document-model`, `entity.reflections.assets`, `entity.concorde.coding-agent`,
  and `entity.concorde.control-state`.

## Related Features

- `feature.concorde.workflow` composes this feature as the reflection-recording and triage stage of
  the end-to-end project workflow.
- `feature.lifecycle.plan-attempt` provides `contract.lifecycle.plan`, the public nested planner
  reflection triage reuses unchanged on its `plan` route.
- `feature.lifecycle.fast-loop` supplies the direct `concorde-fast-loop` capability triage composes
  on its bounded `fast-loop` route.
- `feature.lifecycle.standard-development-loop` is the outer per-feature loop whose plan, tasks,
  analyze, and implement phases are the normal reflection-recording points.
- `feature.capabilities.permission-bounded-execution` supplies `contract.capabilities.permission-bounded-execution`,
  the per-leaf policy compilation and enforced launch every direct capability occurrence requires.
- `feature.concorde.evolve-protocol` owns any normative Concorde Protocol semantic change discovered
  through a reflection; triage investigation remains read-only and no implement/merge/close route
  substitutes for the root cutover.

## Usage Scenarios

1. Planning meets a new concrete problem, atomically allocates an ID, and creates the returned
   `pending/R-NNN.md` with complete Context/Expected/Observed/Impact/Evidence, `triage: pending`,
   blank triage sections, no `human_intervention`, and a retained blank User Comments section, then
   immediately runs `--validate-entry` on it and corrects only that new entry until the result is
   `valid`.
2. Task generation meets the same problem and appends one evidence-bearing occurrence to the
   existing file, in whichever bucket it is filed, without allocating another ID.
3. `status` runs no model and reports per-bucket counts. `investigate` launches one zero-write
   investigator; the parent persists only its validated analysis, proposed resolution, intervention
   decision/rationale, and plan, then runs the relocation Tool so the document leaves `pending/`.
4. When intervention is required, the document moves to `needs-comments/` and triage leaves User
   Comments untouched for the maintainer. When it is not required, the document moves to `planned/`
   and triage records why automation can proceed. After a maintainer comments, a repeated
   `investigate` may flip the decision and the same Tool moves the document to `planned/`.
5. Before persisted investigation or implementation, triage enters one linked worktree at committed
   primary `HEAD`; `implement` chooses exactly fast-loop or public nested plan in that same worktree,
   and only validated commits merge.
6. After a `small` `fast-loop` merge, the parent marks the plan `merged` and invokes deterministic
   removal of exactly the matching reflection file without changing the allocation index.
7. A maintainer records `status: dismissed` with a `resolution_note` on a `needs-comments/`
   document. `close` runs `--remove-closed` on exactly that ID, removing exactly that file, and the
   parent commits the removal with the resolution note in the commit message so the reason survives
   in Git history.
8. `implement` runs on a plan whose problem was verified at an earlier commit. The investigate stage
   re-verifies at the current HEAD: if the behavior still reproduces, the parent records the new
   `verified`/`verified_commit` and implementation proceeds; if it does not, the parent sets the plan
   `stale`, no implementer runs, and re-investigation routes the reflection to `dismiss` with the
   verification as evidence.

## Requirements

- **FR-001**: Every reflection MUST have exactly one tracked
  `.concorde/reflections/<bucket>/R-NNN.md` prose/status/occurrence authority whose filename and
  metadata ID match; no file may contain multiple reflections.
- **FR-002**: Planning and task generation MUST be the normal reflection-recording phases. A new
  document MUST describe the problem with non-empty Context, Expected, Observed, Impact, and Evidence,
  use `status: open` and `triage: pending`, omit `human_intervention`, and leave all triage-owned
  sections empty.
- **FR-003**: Recording MUST NOT analyze root cause, propose a resolution, or decide whether human
  intervention is needed. Those responsibilities belong exclusively to reflection triage.
- **FR-004**: Every reflection document MUST retain a `User Comments` section. Triage and automated
  implementation MUST preserve its content byte-for-byte unless the maintainer edits it.
- **FR-005**: Completed triage MUST set `triage: complete`, fill Triage Analysis, Proposed Resolution,
  and Intervention Rationale, choose `human_intervention: required | not-required`, produce a
  consistent route plan, and preserve all recorded problem facts and occurrences.
- **FR-006**: Repeated problems MUST append occurrences to the existing reflection document rather
  than allocate or duplicate an identity.
- **FR-007**: Reflection content MUST NOT be copied into architecture, feature designs, attempts,
  code, tests, diagrams, or generated outputs; a triage plan may refer to the ID and contain
  independently established implementation evidence.
- **FR-008**: Triage actions/routes, plans/worktrees/agents, and per-leaf policies MUST be explicit,
  conditional, isolated, ownership-bounded, and validated before merge.
- **FR-009**: After validation and merge, a plan with `route: fast-loop`, `effort: small`, `status:
  merged`, a recorded commit reachable from current `HEAD`, and a matching open document MUST be
  eligible for deterministic removal of exactly that file without maintainer approval.
- **FR-010**: Removal MUST validate every requested ID before mutation, report exact removed paths,
  preserve every non-selected document and `index.json`, and roll back on any ineligible, missing,
  malformed, stale, or write failure.
- **FR-011**: Plans on `specify`, `dismiss`, or `blocked` routes and failed/unmerged/non-small plans
  MUST NOT remove their reflection documents automatically; they wait for maintainer disposition.
- **FR-012**: `.concorde/reflections/index.json` MUST contain only schema version and a monotonic
  high-water ID greater than or equal to every current or previously used reflection ID. Allocation
  MUST update it atomically; recording/removal MUST never lower or reuse it.
- **FR-013**: Reflection triage MUST be installed as the associated Markdown skill for its paired
  LangGraph; its Python graph MUST compose only action/route-reachable direct capabilities, reference
  public `concorde-plan` rather than private leaves, and retain specialist agents as support.
- **FR-014**: Status MUST launch no model, investigation agents MUST have zero writes, route
  alternatives MUST never both execute, the parent alone MUST persist validated triage completion,
  and implementer policies MUST narrow writes to reflection worktrees/authorized reflection paths.
- **FR-015**: The bucket folder of a reflection MUST be a pure function of its triage front matter:
  `pending/` for `triage: pending`, `planned/` for `triage: complete` with
  `human_intervention: not-required`, and `needs-comments/` for `triage: complete` with
  `human_intervention: required`. Maintainer `status` MUST NOT affect the bucket. Allocation MUST
  return a `pending/` path, and a document filed elsewhere than its state requires MUST be reported
  as a placement breach.
- **FR-016**: Only the deterministic relocation Tool MAY move a reflection between buckets. It MUST
  derive the target from front matter, leave the document text byte-identical, refuse symlinked
  buckets and existing targets, roll back every completed move on failure, and report the exact
  moved paths. The triage parent MUST invoke it immediately after persisting a triage completion,
  and every other queue action MUST refuse a collection that contains a misplaced document.
- **FR-017**: Every recording phase MUST run the bounded validation immediately after creating a
  document or appending an occurrence. It MUST correct only its own new entry when attributable
  findings exist, and MUST NOT edit other entries or maintainer-owned fields because of that result.
  An allocated-but-unused ID MUST stay retired; the high-water mark MUST NOT be lowered.
- **FR-018**: A reflection with `status: resolved | dismissed` and a `resolution_note` MUST be
  removed through the deterministic `--remove-closed` action, which MUST validate every requested ID
  before mutation, refuse open documents, remove exactly the selected files atomically with
  rollback, preserve every other document and `index.json`, never lower the high-water, and report
  each removed ID with its resolution note for the removal commit. Buckets MUST only hold open
  documents once `close` has run.
- **FR-019**: Every investigation and every implementation attempt MUST begin by re-verifying the
  recorded Observed behavior against the current checkout HEAD, and MUST persist that verification
  (`verified` date, full `verified_commit`, and a `Verification` section with method and outcome) on
  the plan. No stored field, earlier plan, or reflection prose MAY substitute for it.
- **FR-020**: A plan MUST NOT become `approved` or `implemented` without a recorded verification,
  MUST be marked `stale` when its problem no longer reproduces or its `verified_commit` is not the
  current HEAD, and a `stale` plan MUST return to investigation or maintainer rejection before any
  further attempt; a problem that does not reproduce MUST route to `dismiss`, never to
  implementation. The queue Tool MUST derive and report each plan's verification state as `current`,
  `stale`, `unverified`, or `unknown` on every read rather than storing it.
- **FR-021**: A reflection resolution that changes normative Concorde Protocol semantics MUST be
  rejected before implement/merge/close mutation and routed to `feature.concorde.evolve-protocol`;
  read-only status/investigation MAY establish the problem and decision without authorizing a
  lifecycle attempt or reflection implementation worktree.
- **FR-022**: Read-only status MAY run in the primary checkout, but any triage persistence or
  implementation MUST begin in one linked worktree created from exact committed primary `HEAD` and
  remain there through validation. Primary staged, unstaged, untracked, and ignored content MUST NOT
  be stashed, copied, materialized, or altered; missing committed input MUST stop the route unless the
  maintainer explicitly authorizes primary-worktree mutation.

## Edge Cases

- A path is renamed while the reflection meaning, ID, User Comments, and triage decision stay unchanged.
- A closed and removed reflection recurs; it receives the next never-used ID and may cite the removed
  ID in Evidence.
- A removed small problem recurs after closure; it receives the next never-used ID.
- Several merged IDs are requested together and one is ineligible; every reflection file remains.
- The index high-water is below a current document or retained plan ID; allocation and removal stop.
- A recorder has a suspected fix or believes a maintainer is needed; it still records only problem
  facts and leaves both judgments for triage.
- A triage completion is persisted but the parent stops before relocation; the document is
  diagnosed as misplaced and `--relocate` with no IDs repairs the layout without editing text.
- A maintainer resolves or dismisses a `needs-comments/` reflection; it stays in that bucket.
- A plan was verified before an unrelated merge moved HEAD; its `verification` reports `stale` and
  the next attempt re-verifies before touching any file.
- The Observed behavior no longer reproduces at HEAD because another change fixed it; the
  investigator routes to `dismiss` with the verification as evidence and nothing is implemented.
- A verified reflection proposes a normative Concorde Protocol change; triage reports the root
  Protocol-evolution route and performs no implementation, merge, or close mutation itself.
- The primary worktree contains another programmer's untracked feature/attempt files; triage ignores
  them, starts from committed `HEAD`, and reports any required absent path instead of constructing a
  stash snapshot or cherry-picking an untracked-files parent.
