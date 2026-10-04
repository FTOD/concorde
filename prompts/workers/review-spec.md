---
audience: worker
---

@prompts/workers/spec-review/checklist.md

## Your result

As a `reviewer`, judge the Module quality of the reviewed Module. End with status `ok`. Set `output`
to `{"findings": [...], "resolved": [...]}`. `findings` holds every new finding and every earlier
Issue that changed. For the latter, set `earlier` to its identity. `resolved` holds
`{"issue": ..., "reason": ...}` for each earlier Issue the Specs no longer have. When an earlier Issue
still stands as recorded, it appears in neither. It stays open. Empty lists mean that you found
nothing new and resolved nothing.

As a `checker`, you receive the reviewer's numbered findings. Check each one against the same Specs,
independently of how confident it sounds. End with status `ok`. Set `output` to `{"checks": [...]}`.
Return one `{"finding": <number>, "status": "confirmed" | "disputed", "reason": "..."}` per finding.
When the Spec text supports the finding as stated, use `confirmed`. When it does not, use `disputed`,
for example in these cases:

- The quoted evidence is not in the Spec.
- Another passage already states what the finding says is missing.
- The tier or severity is wrong.

The reason says which. A disputed finding is recorded nowhere.

Return `blocked` only when you cannot review at all, for example because the reviewed Module's own
documents cannot be read. A missing provider document is a
`context` finding. It is not a reason to stop. In `output`, still return `{"findings": []}` or
`{"checks": []}`.

@prompts/workers/common/errors.md
