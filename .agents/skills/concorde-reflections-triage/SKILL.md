---
name: concorde-reflections-triage
description: "Investigate and route project reflections through a controlled LangGraph Operation."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-reflections-triage/SKILL.md"
  kind: "operation"
  entrypoint: "operations/concorde-reflections-triage/operation.py"
---
# Concorde Reflection Triage

Protocol: `reflection-triage/v4`.

Use the paired graph at `python3 operations/concorde-reflections-triage/operation.py` as the stage topology authority. The graph composes leaf Skills;
specialized investigator and implementer agents remain internal execution support.

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

Before work, run `python3 operations/concorde-reflections-triage/operation.py "$ARGUMENTS" --framework-prefix .` and require its
ordered investigate, route, implement, and validate stages. Execute each leaf Skill and internal role
within the existing authority boundaries. A failed or blocked stage prevents every downstream stage.

The parent remains the only plan-file writer. Never run parallel implementers in the main checkout,
never change maintainer disposition, and never maintain a second integration-specific queue.
