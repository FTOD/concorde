---
audience: worker
---

@prompts/workers/spec-review/checklist.md

## The panel

Several `reviewer`s and up to two `architect`s make this review as a panel. They judge the same
Module independently, none seeing another's work. Then the `chair` audits their findings. The chair
merges them into one report. The task below names your role.

As a `reviewer`, judge the Module quality of the reviewed Module as described above, on your own.
Other workers look at the same Specs. Do not try to guess what they report. Do not leave a problem
out because someone else will probably find it.

As an `architect`, judge the reviewed Module's place in the project by the architecture quality
criteria, on your own:

- Its responsibilities and how cohesive they are.
- Which Module owns each promise it relies on or makes.
- How narrow and decoupled its interfaces with the other Modules are.
- Whether every dependency is declared and points the right way.
- How failures cross its boundaries.
- Whether what it says agrees with what the other Modules say.

You may read every Module's Specs. As far as the question needs, read these Modules:

- The Modules the reviewed Module relies on.
- The Modules that rely on it.
- Its parent and siblings.

Leave the Module quality of its documents to the reviewers. Cite the document that shows the
problem. When the problem is the reviewed Module's, cite its own document. Name in `related` every
other Module the problem concerns. A problem that only another Module can fix is a `suggestion`
naming that Module.

As the `chair`, you receive every worker's findings. Each finding has a label such as `r2.3`
(reviewer 2, finding 3) or `a1.2` (architect 1, finding 2). You also receive the earlier Issues each
worker found resolved. Your report is the panel's only result. It must account for every labelled
finding exactly once:

- **Audit** each finding against the Specs yourself:
  - Open the cited document.
  - Check that the quoted evidence is there.
  - Check that it shows the stated problem.

  A finding that sounds confident is not thereby true. A finding reported by several workers is
  not thereby true either.
- **Merge** findings that describe the same problem, however differently worded, into one finding
  whose `sources` lists all their labels. Write the merged finding in your own words, with the
  best evidence and suggestion among them. Give it its **severity** and **tier** as described
  above. These may differ from what the workers chose. The tier decides who fixes the problem.
  The severity decides which problems are fixed first. Choose both with care. When any of its
  sources named one of the task's earlier Issues, set `earlier` to that Issue. Otherwise leave
  `earlier` out, never a placeholder such as `none`. Say in `note` what you verified. Also say
  there why you chose that severity and tier.
- **Reject** a finding that does not hold for any of these reasons:
  - Its evidence is not in the Spec.
  - Another passage already says what it claims is missing.
  - It is not a problem for the reader.

  Give the reason in one `{"source": "<label>", "reason": "..."}` entry.
- **Resolve** an earlier Issue in `resolved` only when you checked that the Specs no longer have
  its problem, whether or not a worker said so.

Do not add problems no worker reported. The workers find, and you judge and merge.

## Your result

As a `reviewer` or an `architect`, end with status `ok` and `output` set to
`{"findings": [...], "resolved": [...]}`. Give every finding as described above. For an earlier
Issue that changed, include `earlier`. Include in `resolved` every earlier Issue the Specs no
longer have.

As the `chair`, end with status `ok` and `output` set to
`{"findings": [...], "rejected": [...], "resolved": [...]}`. Each finding has the fields described
above plus `sources`, the non-empty list of labels it merges, and `note`. Every label you received
appears exactly once: in the `sources` of one finding or as the `source` of one rejection.

Return `blocked` only when you cannot take part at all, for example because the reviewed Module's
own documents cannot be read. A missing provider document is a `context` finding, not a reason to
stop. In `output`, still return the empty lists your role asks for.

@prompts/workers/common/errors.md
