---
audience: worker
---

@prompts/workers/spec-review/checklist.md

## Your result

As a `reviewer`, judge the Module quality of the reviewed Module and end with status `ok` and
`output` set to `{"findings": [...], "resolved": [...]}`. `findings` holds every new finding and
every earlier Issue that changed, the latter with `earlier` set to its identity; `resolved` holds
`{"issue": ..., "reason": ...}` for each earlier Issue the Specs no longer have. An earlier Issue
that still stands as recorded appears in neither: it stays open. Empty lists mean you found nothing
new and resolved nothing.

As a `checker`, you receive the reviewer's numbered findings. Check each one against the same Specs,
independently of how confident it sounds, and end with status `ok` and `output` set to
`{"checks": [...]}`, one `{"finding": <number>, "status": "confirmed" | "disputed", "reason": "..."}`
per finding: `confirmed` when the Spec text supports the finding as stated, `disputed` when it does
not, for example because the quoted evidence is not in the Spec, another passage already states
what the finding says is missing, or the tier is wrong. The reason says which. A disputed finding is
recorded nowhere.

Return `blocked` only when you cannot review at all, for example because the reviewed Module's
own documents cannot be read; a missing provider document is a `context` finding, not a reason to
stop. In `output`, still return `{"findings": []}` or `{"checks": []}`.

@prompts/workers/common/errors.md
