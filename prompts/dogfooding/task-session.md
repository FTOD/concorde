---
audience: shared
---

## Concorde defects in a develop install

This project is a **develop install** of Concorde. The developer also changes this Concorde, in the
Concorde repository that the receipt `.concorde/install.json` names as its `source`. You start and
observe the runs of your task, so you are the first to see a Concorde defect in them.

@prompts/dogfooding/common/observe-runs.md

A run can end `ok` and still be wrong. Treat such a run like a failure.

A **Concorde defect** is one that would happen in any project using Concorde the same way. A
problem of this project's Specs, code, checks or configuration is ordinary work of your task. A
refused read, write or tool can be either. When the task's goal does not need that access, the
work overreaches: do it another way. Otherwise, escalate the refusal as below. The main agent
places it in its boundary case.

When you suspect a Concorde defect, do these things:

- Keep the evidence. Do not delete, re-run over or clean up the run's folder, its run record or
  its error chain.
- Do not work around the defect. For example, do not change this project's Specs only so that a
  wrongly computed boundary lets the work through.
- Never change the Concorde repository, the framework copy under `.concorde/framework/` or a file
  the installer placed.
- Escalate the defect to the main agent with `concorde task escalate`, as "Decide within the task,
  escalate the rest" says. Name the run with `--run`, so that its whole error chain is the cause of
  your link. In `--detail`, say what you saw, why you think the defect is Concorde's and not this
  project's and, for a refused access, the Spec text, the grant actually computed and the refused
  action.
- Go on with every part of the task that does not depend on the defect.

Do not write a defect report yourself. The main agent places the defect in its case, writes the
defect report and hands it to the Concorde repository.
