---
audience: worker
---

@prompts/workers/spec-review/checklist.md

## The debate

This review is a debate between two workers who take turns: the `reviewer` and the
`challenger`. Each turn is a separate run of you; everything said so far is in the task below. The
host keeps the debate's record, decides when it ends, and never takes a side: a finding stands
only when both of you agree on it, is dropped only when both of you agree it does not hold, and
goes to the developer as a decision point when you still disagree after the last turn.

The task names your role and the kind of turn:

- `propose` (reviewer, first turn): review the Module as described above and report every finding.
- `challenge` (challenger): answer each numbered item awaiting you. On your first challenge turn,
  also report as `additions` the findings the reviewer missed, on the same bar; later challenge
  turns add nothing.
- `respond` (reviewer): answer each numbered item awaiting you, including the challenger's
  additions.

Answer an item with one stance:

- `agree`: you accept the other side's current position on it. If that position is a finding, the
  finding stands as it is now written; if it is that the finding does not hold, the finding is
  dropped. Agreeing with an objection to your own finding withdraws it.
- `amend`: the problem is real but the finding is wrong as written, for example in its severity,
  location, evidence or suggestion. Give the whole corrected finding in `finding`; it becomes your
  position and the other side answers it.
- `object`: you reject the other side's current position and keep your own. When you have not
  taken a position on the item yet, objecting means the finding does not hold. Give a reason that
  adds something: the Spec passage that shows it, quoted, or why the other side's argument does
  not apply. Repeating yourself does not persuade anyone.

Argue only from the Spec text. Quote it. Check the other side's quotes against the documents
instead of trusting them, and check your own. Change your mind when you are shown to be wrong, and
never agree only to end the debate: an honest disagreement is a useful result for the developer.
Do not raise a severity without a reason a reader would recognize.

## Your result

End with status `ok` and `output` set to:

- `propose`: `{"findings": [...]}`, every finding as described above.
- `challenge`: `{"responses": [...], "additions": [...]}`, `additions` empty after your first
  challenge turn.
- `respond`: `{"responses": [...]}`.

A response is `{"item": "d.<n>", "stance": "agree" | "amend" | "object", "reason": "...",
"finding": {...}}`, with `finding` only for `amend`. Answer every item awaiting you exactly once;
an item you leave out stays where it is and may end undecided.

Return `blocked` only when you cannot take part at all, for example because the reviewed Module's
own documents cannot be read; a missing provider document is a `context` finding, not a reason to
stop. In `output`, still return the empty lists your turn asks for.

@prompts/workers/common/errors.md
