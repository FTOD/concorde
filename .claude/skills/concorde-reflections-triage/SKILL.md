---
name: concorde-reflections-triage
description: "Investigate and route project reflections through a controlled LangGraph Operation."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-reflections-triage/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-reflections-triage/operation.py"
user-invocable: true
disable-model-invocation: false
---
# Concorde Reflection Triage

Protocol: `reflection-triage/v5`.

Use the paired graph at `python3 operations/concorde-reflections-triage/operation.py` as the stage topology authority. The graph composes direct leaf
Skills and the public nested planner; specialized investigator and implementer agents remain internal
execution support.

Shared configuration is `.concorde/reflections/config.json`; plans are under
`.concorde/reflections/plans/`; worktrees are under `.concorde/reflections/worktrees/`. Use the
installed deterministic Tool at `.concorde/framework/scripts/reflections_queue.py`; in a source
checkout use `scripts/reflections_queue.py`. The tracked allocation high-water is
`.concorde/reflections/index.json`; each `.concorde/reflections/<bucket>/R-NNN.md` is the sole
persisted prose record for one reflection. Never edit maintainer-owned `status`, `resolution_note`,
or `User Comments` while triaging.

## Bucket layout

Every reflection document lives in exactly one tracked bucket folder, and the folder is a pure
function of its triage front matter:

| Folder | Meaning | Front matter |
|---|---|---|
| `pending/` | recorded; triage has not investigated it | `triage: pending` |
| `planned/` | triaged; its plan may proceed without a maintainer | `triage: complete`, `human_intervention: not-required` |
| `needs-comments/` | triaged; waiting for maintainer input in `User Comments` | `triage: complete`, `human_intervention: required` |

Recording phases always create a document under `pending/` at the exact `reflection_path` returned
by `--allocate-id`. Only the deterministic helper moves files: after the parent persists a validated
triage completion it must run `reflections_queue.py --relocate R-NNN`, which moves the document into
the folder its new front matter requires without changing a byte of its text. Maintainer-owned
`status` never moves a file; a resolved or dismissed reflection stays in its triage bucket. No agent
moves, copies, or renames a reflection by hand. A document whose folder disagrees with its front
matter is a placement breach (`CONCORDE-REFLECT-005`); every helper action except `--relocate`
refuses such a collection, so run `--relocate` with no IDs to repair drift before continuing.

## Actions

- `status`: run the helper with `--json`, report open, pending-triage, plan, and per-bucket counts,
  and stop.
- `investigate [N | R-NNN ...]`: use the Operation's investigate stage and one investigator per
  reflection. For each result, the parent validates and writes the returned triage completion to that
  reflection document in place, writes its route plan, and then runs `--relocate R-NNN` so the
  document leaves `pending/` for `planned/` or `needs-comments/`. The step is complete only when the
  relocation result reports the document under its new bucket. When a `needs-comments/` document has
  gained maintainer input, `investigate R-NNN` may run again; if the new decision is `not-required`,
  the same relocation moves it to `planned/`.
- `implement`: follow the route and implement stages; only validated `fast-loop` plans are eligible.
- `merge`: require clean tracked state, merge one branch at a time, validate, and remove only a
  matching merged small fast-loop entry through the helper.

Before work, run `python3 operations/concorde-reflections-triage/operation.py "$ARGUMENTS" --framework-prefix . --describe-policy` and
require only the capabilities reachable for the explicit action/route:

- `status`: no model capability; run/report the queue Tool and stop;
- `investigate`: `concorde-analyze` only, under a zero-write policy;
- `implement --route fast-loop`: analyze, isolated-worktree fast-loop, then validate;
- `implement --route plan`: analyze, public nested `concorde-plan`, tasks, isolated-worktree
  implement, then validate; and
- `merge`: validate the parent state before the deterministic merge/removal Tool actions.

Never invoke both route alternatives. Never reference the planner's private leaves from this outer
graph. Execute each direct leaf/internal role within its own immutable authority; investigators are
read-only, the parent alone persists their validated triage result, and implementers can write only
beneath the declared reflection worktree plus the owning reflection document. A failed or blocked
capability prevents every downstream node.

## Triage completion boundary

Recording phases deliberately leave `triage: pending`, omit `human_intervention`, and leave Triage
Analysis, Proposed Resolution, and Intervention Rationale empty. Triage is the only workflow that may
complete them. Investigation must establish root cause with concrete evidence, propose the smallest
appropriate resolution, choose exactly one route, decide `human_intervention: required |
not-required`, and explain that decision. Set `triage: complete` only when all of those details are
present and the plan agrees with them. Preserve the original Context, Expected, Observed, Impact,
Evidence, and all Occurrences. Never fill or remove `User Comments`; it remains available for the
maintainer when intervention is required. Relocation is the final step of completion: a reflection
that keeps `triage: pending` stays under `pending/`, and a completed one is moved by the helper,
never by hand.

The parent remains the only plan-file and triage-completion writer and the only caller of
`--relocate`. Never run parallel implementers in the main checkout, never change maintainer
disposition, and never maintain a second integration-specific queue.
