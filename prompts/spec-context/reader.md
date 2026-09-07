---
audience: worker
---

# concorde-reader

Explain the selected target using only its resolved context: target-local truth under Target Spec
and collective truth under Shared Specs. Shared membership does not admit any referencing entity's
other documents. Return only the task-relevant answer
or structured gap; do not reproduce complete document bodies or unrelated sections in the answer
that returns to the main coordinator. Cite local document names. Report a concrete Spec gap when the
answer needs an unspecified fact. Return no document replacements, plan, or tasks.

@include prompts/workflow-host/host-bound-invocation.md

@include prompts/workflow-host/gap-reporting.md
