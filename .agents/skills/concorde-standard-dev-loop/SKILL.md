---
name: concorde-standard-dev-loop
description: "Run the standard Concorde development loop as a controlled LangGraph Operation."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-standard-dev-loop/SKILL.md"
  kind: "operation"
  entrypoint: "operations/concorde-standard-dev-loop/operation.py"
---
# Concorde Standard Development Loop

Treat `$ARGUMENTS` as the complete development request. Use the paired graph at `python3 operations/concorde-standard-dev-loop/operation.py` as the
topology authority for exactly four stages: specify, plan, tasks, and deliver.

Before executing leaf Skills, run:

```bash
python3 operations/concorde-standard-dev-loop/operation.py "$ARGUMENTS" --framework-prefix .
```

Require the graph to report these ordered Skill bundles:

1. `specify`: `concorde-specify`
2. `plan`: `concorde-plan`
3. `tasks`: `concorde-tasks`, then `concorde-implement`
4. `deliver`: `concorde-validate`, then `concorde-deliver`

Execute each named leaf Skill faithfully in graph order, carrying forward its explicit result. Stop
the Operation immediately when a Skill fails, blocks, or requests missing authority. Never treat the
graph's deterministic recording output as evidence that a leaf Skill itself completed.
