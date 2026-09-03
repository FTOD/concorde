---
id: feature.concorde.record-workflow-reflections
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.skills.project-workflow
  - feature.operations.standard-development-loop
  - feature.operations.permission-bounded-planning
interfaces:
  provided:
    - interface.concorde.reflections
  required:
    - contract.concorde.workflow
evidence_status: partial
---

# Feature Design: Record and Triage Workflow Reflections

## Outcome and Scope

Every retained workflow problem has one detailed, tracked
`.concorde/reflections/<bucket>/R-NNN.md` document. Planning and task generation normally record
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

Maintainers can explicitly choose status/investigate/implement/merge. The paired Operation launches
only the chosen branch under per-leaf policies. A validated merge of a small `fast-loop` fix removes
only its matching reflection file automatically; every other route retains the document for explicit
maintainer disposition.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.operations` | Supplies the conditional permission-bounded triage graph and nested public planner. |
| `entity.concorde.agent-assets` | Supplies Reflection Document v2 grammar and internal investigator/implementer roles. |
| `entity.concorde.runtime` | Supplies deterministic queue, allocation-index, plan-state, and merged-removal Tools. |
| `entity.concorde.coding-agent` | Records problem-only documents during workflow phases and performs explicitly assigned triage. |
| `entity.concorde.control-state` | Holds the tracked per-file reflection collection in its `pending/`, `planned/`, and `needs-comments/` buckets, the metadata-only index, and triage configuration/scratch state. |

## Interfaces

### `interface.concorde.reflections` — Record and triage project reflections

- **Consumer**: Workflow phases, maintainer, and supported reflection investigator/implementer agents.
- **Direction**: Encountered problem to problem-only document; explicit triage to completed analysis,
  proposed resolution, human-intervention decision, plans/worktree commits/merge, deterministic
  removal for merged small fixes, or maintainer disposition for other routes.
- **Entry points**: Plan/task Skill reflection rules, installed `concorde-reflections-triage`
  Operation Skill and paired graph, and `reflections_queue.py --allocate-id` / `--relocate` /
  `--remove-merged` Tools.
- **Inputs**: At recording, selected feature ID, phase/date/kind, stable concern path/ID, detailed
  context, expected and observed behavior, impact, and evidence. At triage, one selected reflection
  and explicit triage action.
- **Outputs**: Atomically allocated never-used ID and exact `pending/` document path; one
  problem-only document or occurrence; triage analysis, proposed resolution, intervention
  decision/rationale, preserved User Comments; an exact relocation manifest moving the completed
  document into `planned/` or `needs-comments/`; validated plan/worktree state; implementer commit;
  merge result; and exact removed file manifest for eligible small fixes.
- **Obligations**: Keep one prose authority per reflection and a metadata-only allocation index;
  never reuse removed IDs; avoid secrets; make status model-free and investigators read-only; keep
  recording separate from analysis; retain User Comments; keep every document in the bucket its
  `triage`/`human_intervention` state requires and move it only through the relocation Tool without
  changing its text; select exactly one route; keep nested planning public/opaque; isolate
  worktrees; preserve maintainer disposition; remove a document only when its `small` `fast-loop`
  plan is `merged`, `recorded_under` matches the reflection feature, its commit is present in
  current history, and automated merge validation passed; never treat a reflection as behavioral
  intent.
- **Failures**: Malformed/unresolved documents or index, recording-time triage content, incomplete
  triage, a document filed in a bucket its front matter does not require, invalid
  action/route/policy, unavailable enforcement, duplicate identity, stale or non-ancestor commit,
  ineligible route/effort/status, unsafe worktree/removal/relocation, or verification failure
  preserves retained reflection files and sources.
- **Compatibility**: Reflection Document v2 replaces the single-file Reflection Log v1. A legacy
  `.concorde/reflections/log.md` is diagnosed rather than accepted in a dual-layout mode.
  `reflection-triage/v5` reserves `tool` for queue helpers and exposes the conditional
  mixed-capability workflow as an exact Python/Markdown Operation pair.
- **Implementing entities**: `module.concorde.operations`, `entity.concorde.agent-assets`,
  `entity.concorde.runtime`, `entity.concorde.coding-agent`, and `entity.concorde.control-state`.

## Usage Scenarios

1. Planning meets a new concrete problem, atomically allocates an ID, and creates the returned
   `pending/R-NNN.md` with complete Context/Expected/Observed/Impact/Evidence, `triage: pending`,
   blank triage sections, no `human_intervention`, and a retained blank User Comments section.
2. Task generation meets the same problem and appends one evidence-bearing occurrence to the
   existing file, in whichever bucket it is filed, without allocating another ID.
3. `status` runs no model and reports per-bucket counts. `investigate` launches one zero-write
   investigator; the parent persists only its validated analysis, proposed resolution, intervention
   decision/rationale, and plan, then runs the relocation Tool so the document leaves `pending/`.
4. When intervention is required, the document moves to `needs-comments/` and triage leaves User
   Comments untouched for the maintainer. When it is not required, the document moves to `planned/`
   and triage records why automation can proceed. After a maintainer comments, a repeated
   `investigate` may flip the decision and the same Tool moves the document to `planned/`.
5. `implement` chooses exactly fast-loop or public nested plan; implementers write only isolated
   owned worktrees/authorized reflection references and only validated commits merge.
6. After a `small` `fast-loop` merge, the parent marks the plan `merged` and invokes deterministic
   removal of exactly the matching reflection file without changing the allocation index.

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
  MUST NOT remove their reflection documents automatically.
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

## Edge Cases

- A path is renamed while the reflection meaning, ID, User Comments, and triage decision stay unchanged.
- A resolved/dismissed reflection recurs; an occurrence is recorded without reversing maintainer disposition.
- A removed small problem recurs after closure; it receives the next never-used ID.
- Several merged IDs are requested together and one is ineligible; every reflection file remains.
- The index high-water is below a current document or retained plan ID; allocation and removal stop.
- A recorder has a suspected fix or believes a maintainer is needed; it still records only problem
  facts and leaves both judgments for triage.
- A triage completion is persisted but the parent stops before relocation; the document is
  diagnosed as misplaced and `--relocate` with no IDs repairs the layout without editing text.
- A maintainer resolves or dismisses a `needs-comments/` reflection; it stays in that bucket.
