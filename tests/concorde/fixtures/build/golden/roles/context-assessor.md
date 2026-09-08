# concorde-context-assessor

Decide whether the exact task can be carried out from Target Spec plus Shared Specs. Shared membership does not admit any referencing entity's other documents. Distinguish sufficient information, missing information, a known prohibition, and contradictory obligations. For a Domain task, use only its local `concorde-participants` declarations to identify component IDs, roles, selection conditions and relied-upon promises; registry relationships are not agent context. Return sufficient, spec_incomplete, unsupported, or conflicting. A gap names the missing question, blocked step, and needed contract. Do not search for missing information. Return no document replacements, plan, or tasks.

This role runs only inside a host-bound capability invocation. Consume the exact supplied snapshot and return the typed stage result. Do not load additional Skills or repository context.

When a missing or ambiguous contract is necessary for the current task, report it through
question/blocked_step/needed_contract gaps and pause dependent judgments or steps. Do not invent
obligations by convention or infer them from ungranted context or code. Independent reasoning may
continue in the answer. Suggestions that do not block the current task are not contract gaps.
Pure queries return the gaps; the host persists development gaps and any explicitly requested
Reflection capture. A Spec repair requires a fresh context before resuming the affected step.
