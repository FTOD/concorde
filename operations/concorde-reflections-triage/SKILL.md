---
name: concorde-reflections-triage
description: Investigate and route project reflections through a controlled LangGraph Operation.
exposure: public
operation: operation.py
capabilities:
  - concorde-analyze
  - concorde-fast-loop
  - concorde-plan
  - concorde-tasks
  - concorde-implement
  - concorde-validate
---

# Concorde Reflection Triage

Protocol: `reflection-triage/v5`.

Use the paired graph at `{OPERATION}` as the stage topology authority. The graph composes direct leaf
Skills and the public nested planner; specialized investigator and implementer agents remain internal
execution support.

Shared configuration is `.concorde/reflections/config.json`; plans are under
`.concorde/reflections/plans/`; worktrees are under `.concorde/reflections/worktrees/`. Use the
installed deterministic Tool at `.concorde/framework/scripts/reflections_queue.py`; in a source
checkout use `scripts/reflections_queue.py`. The tracked allocation high-water is
`.concorde/reflections/index.json`; each `.concorde/reflections/R-NNN.md` is the sole persisted prose
record for one reflection. Never edit maintainer-owned `status`, `resolution_note`, or `User
Comments` while triaging.

## Actions

- `status`: run the helper with `--json`, report open, pending-triage, and plan counts, and stop.
- `investigate [N | R-NNN ...]`: use the Operation's investigate stage and one investigator per
  reflection. For each result, the parent validates and writes the returned triage completion to that
  reflection document and writes its route plan.
- `implement`: follow the route and implement stages; only validated `fast-loop` plans are eligible.
- `merge`: require clean tracked state, merge one branch at a time, validate, and remove only a
  matching merged small fast-loop entry through the helper.

Before work, run `{OPERATION} "$ARGUMENTS" --framework-prefix {FRAMEWORK} --describe-policy` and
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
maintainer when intervention is required.

The parent remains the only plan-file and triage-completion writer. Never run parallel implementers in the main checkout,
never change maintainer disposition, and never maintain a second integration-specific queue.
