---
name: concorde-reflections-triage
description: "Investigate and route project reflections through a controlled LangGraph Operation."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-reflections-triage/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-reflections-triage/operation.py"
---
# Concorde Reflection Triage

Protocol: `reflection-triage/v4`.

Use the paired graph at `python3 operations/concorde-reflections-triage/operation.py` as the stage topology authority. The graph composes direct leaf
Skills and the public nested planner; specialized investigator and implementer agents remain internal
execution support.

Shared configuration is `.concorde/reflections/config.json`; plans are under
`.concorde/reflections/plans/`; worktrees are under `.concorde/reflections/worktrees/`. Use the
installed deterministic Tool at `.concorde/framework/scripts/reflections_queue.py`; in a source
checkout use `scripts/reflections_queue.py`. Never edit reflection `Status` or `Note`.
`.concorde/reflections/log.md` remains the sole persisted reflection record.

## Actions

- `status`: run the helper with `--json`, report the ordered open queue and plan counts, and stop.
- `investigate [N | R-NNN ...]`: use the Operation's investigate stage and one investigator per entry.
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
read-only and implementers can write only beneath the declared reflection worktree plus the central
reflection record. A failed or blocked capability prevents every downstream node.

The parent remains the only plan-file writer. Never run parallel implementers in the main checkout,
never change maintainer disposition, and never maintain a second integration-specific queue.
