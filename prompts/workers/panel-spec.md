---
audience: worker
---

@prompts/workers/spec-review/checklist.md

## The panel

This review is made by a panel: several `reviewer`s review the same Module independently, none
seeing another's work, and then the `chair` audits their reviews and merges them into one report.
The task below names your role.

As a `reviewer`, review the Module as described above, on your own. Other reviewers are looking
at the same Specs; do not try to guess what they report, and do not leave a problem out because
someone else will probably find it.

As the `chair`, you receive every reviewer's findings, each with a label such as `r2.3` (reviewer
2, finding 3). Your report is the panel's only result, so it must account for every labelled
finding exactly once:

- **Audit** each finding against the Specs yourself: open the cited document, check that the
  quoted evidence is there and that it shows the stated problem. A finding that sounds confident is
  not thereby true, and a finding reported by several reviewers is not thereby true either.
- **Merge** findings that describe the same problem, however differently worded, into one finding
  whose `sources` lists all their labels. Write the merged finding in your own words, with the
  best evidence and suggestion among them, and the severity the checklist gives it, which may
  differ from what a reviewer chose. Say in `note` what you verified and why you chose that
  severity.
- **Reject** a finding that does not hold: its evidence is not in the Spec, another passage already
  says what it claims is missing, or it is not a problem for the reader. Give the reason in one
  `{"source": "<label>", "reason": "..."}` entry.

Do not add problems no reviewer reported; the reviewers find, you judge and merge.

## Your result

As a `reviewer`, end with status `ok` and `output` set to `{"findings": [...]}`, every finding as
described above.

As the `chair`, end with status `ok` and `output` set to `{"findings": [...], "rejected": [...]}`.
Each finding has the fields described above plus `sources`, the non-empty list of labels it
merges, and `note`. Every label you received appears exactly once: in the `sources` of one finding
or as the `source` of one rejection.

Return `blocked` only when you cannot take part at all, for example because the reviewed Module's
own documents cannot be read; a missing provider document is a `context` finding, not a reason to
stop. In `output`, still return the empty lists your role asks for.

@prompts/workers/common/errors.md
