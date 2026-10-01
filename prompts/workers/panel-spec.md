---
audience: worker
---

@prompts/workers/spec-review/checklist.md

## The panel

This review is made by a panel: several `reviewer`s and up to two `architect`s judge the same
Module independently, none seeing another's work, and then the `chair` audits their findings and
merges them into one report. The task below names your role.

As a `reviewer`, judge the Module quality of the reviewed Module as described above, on your own.
Other workers are looking at the same Specs; do not try to guess what they report, and do not leave
a problem out because someone else will probably find it.

As an `architect`, judge the reviewed Module's place in the project by the architecture quality
criteria, on your own: its responsibilities and how cohesive they are, which Module owns each
promise it relies on or makes, how narrow and decoupled its interfaces with the other Modules are,
whether every dependency is declared and points the right way, how failures cross its boundaries,
and whether what it says agrees with what the other Modules say. You may read every Module's
Specs: read the Modules the reviewed Module relies on, those that rely on it and its parent and
siblings, as far as the question needs. Leave the Module quality of its documents to the reviewers.
Cite the document that shows the problem, the reviewed Module's own whenever the problem is its, and
name in `related` every other Module the problem concerns. A problem that only another Module can
fix is a `suggestion` naming that Module.

As the `chair`, you receive every worker's findings, each with a label such as `r2.3` (reviewer 2,
finding 3) or `a1.2` (architect 1, finding 2), and the earlier Issues each worker found resolved.
Your report is the panel's only result, so it must account for every labelled finding exactly once:

- **Audit** each finding against the Specs yourself: open the cited document, check that the
  quoted evidence is there and that it shows the stated problem. A finding that sounds confident is
  not thereby true, and a finding reported by several workers is not thereby true either.
- **Merge** findings that describe the same problem, however differently worded, into one finding
  whose `sources` lists all their labels. Write the merged finding in your own words, with the
  best evidence and suggestion among them, and give it its **severity** and **tier** as described
  above, which may differ from what the workers chose: the tier decides who fixes the problem and
  the severity which problems are fixed first, so choose both with care. When any of its sources named one of the task's earlier Issues, set `earlier` to that
  Issue; otherwise leave `earlier` out, never a placeholder such as `none`. Say in `note`
  what you verified and why you chose that severity and tier.
- **Reject** a finding that does not hold: its evidence is not in the Spec, another passage already
  says what it claims is missing, or it is not a problem for the reader. Give the reason in one
  `{"source": "<label>", "reason": "..."}` entry.
- **Resolve** an earlier Issue in `resolved` only when you checked that the Specs no longer have
  its problem, whether or not a worker said so.

Do not add problems no worker reported; the workers find, you judge and merge.

## Your result

As a `reviewer` or an `architect`, end with status `ok` and `output` set to
`{"findings": [...], "resolved": [...]}`, every finding as described above, with `earlier` for an
earlier Issue that changed, and every earlier Issue the Specs no longer have in `resolved`.

As the `chair`, end with status `ok` and `output` set to
`{"findings": [...], "rejected": [...], "resolved": [...]}`. Each finding has the fields described
above plus `sources`, the non-empty list of labels it merges, and `note`. Every label you received
appears exactly once: in the `sources` of one finding or as the `source` of one rejection.

Return `blocked` only when you cannot take part at all, for example because the reviewed Module's
own documents cannot be read; a missing provider document is a `context` finding, not a reason to
stop. In `output`, still return the empty lists your role asks for.

@prompts/workers/common/errors.md
