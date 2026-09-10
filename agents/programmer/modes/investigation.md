# Mode: investigation

When `stage_inputs` contains `concorde-reflection-selection`, this is a read-only investigation.
Use the complete Module contract and granted code. Return `reflection_findings` for exactly the
selected IDs in order, with `verified_commit` equal to its head. Supply `observed_state`,
`verification`, `analysis`, `resolution`, `intervention_rationale`, `human_intervention`, `route`,
`effort`, `files`, `steps`, `validation`, `risks` and `protocol_change`. `resolution` describes
intended behavior only; keep code details in `verification`/`analysis`. Only small work may route
to dev-loop with `specify:false`. Keep `documents`, `plan` and `tasks` empty and make no mutations
in an investigation. Do not include raw code or logs in downstream results.

Use granted implementation contents read-only. A non-reproduced problem requires route dismiss and human_intervention required. Never implement or return tasks in this mode.
