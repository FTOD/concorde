---
audience: shared
---

## Developing Concorde while using it

This project is a **develop install** of Concorde: it runs the Concorde of the Concorde repository
that the receipt `.concorde/install.json` names as its `source`, installed at the commit it records
as `source_commit`. The developer also changes Concorde there, in a separate session that follows
that repository's own rules. Your part is to use Concorde for this project as usual, to watch
Concorde while you do, and to hand every Concorde defect you find over to that repository.

@prompts/dogfooding/common/observe-runs.md

A run can end `ok` and still be wrong: a worker that changed a file outside the task's goal, a
check that ran no test, a summary its evidence contradicts. Treat those like failures.

### Never change Concorde from here

Do not edit the Concorde repository, the framework copy under `.concorde/framework/`, or any file
the installer placed or amended (the receipt lists them), even to unblock yourself. The next update
overwrites such a change, and it would bypass the Concorde repository's own tasks, checks and
review. Do not work around a Concorde defect either, for example by changing this project's Specs
only so that a wrongly computed boundary lets the work through: a workaround hides the defect.

### Whose problem is it

A problem of this project, its Specs, code, checks or configuration or the way you used Concorde,
is ordinary work here. A **Concorde defect** is one that would happen in any project using Concorde
the same way: a crash or wrong result of a `concorde` command, an Operation, a workflow or the
host; a grant or harness that differs from what the Protocol derives from the Specs; an error
chain that loses a link or a detail; guidance or worker instructions that lead an agent wrong; or
a Protocol that cannot express what a correct project needs. In doubt, say which parts of your
reasoning are uncertain in the report's `basis`.

### When a boundary blocks work

When a read, a write or a tool is refused, decide which of four cases it is before doing anything
else:

| Case | How you tell | Where it goes | Who decides |
| --- | --- | --- | --- |
| The boundary is right; the work overreaches | The task's goal does not need that access | Nowhere: do the work another way, or open a task for the other Module | You |
| This project's Specs draw the boundary wrongly | The grant is what the Protocol derives from the Specs, but the Specs misdescribe the Modules' ownership, uses or references | This project: an Issue here (`gap`) and a task that corrects the Specs | The developer, when the correction changes relations between Modules |
| Concorde implements the boundary wrongly | The grant or harness actually applied differs from what the Protocol derives from the Specs | A Concorde defect report of type `bug` | The Concorde repository fixes it |
| Concorde's design blocks a correct boundary | The Specs are right and the grant is what the Protocol derives, yet legitimate work needs the access | A Concorde defect report of type `limitation` | The developer, before Concorde's design or Protocol changes |

Whichever case it is, write down three things, in the report's `basis` and `evidence` when it goes
to Concorde: the Spec text and Protocol rule the boundary is derived from; the grant actually
computed (`concorde grant --modules <ids> --type <task type>` and the run's host evidence); and
the refused action with its message. Never settle a blocked boundary by only loosening it.

### Report a Concorde defect

Write the report as one JSON object to `.concorde/runs/defects/<report_key>.json`, which Git
ignores. It is an Issue report, whose fields are all required unless marked optional, and nothing
else:

- `report_key`: a short kebab-case name of the defect, the same as the file name;
- `type`: `bug` (a failure or wrong result), `limitation` (consistent but insufficient behaviour)
  or `gap`; `subtype`: `null` for a bug or a limitation, and for a gap one of
  `implementation-spec-mismatch`, `spec-conflict` or `missing-contract`;
- `title`, a `description` of what you saw, the `impact` on your work, and a `basis` saying why
  the defect is Concorde's and not this project's (for a blocked boundary: its case and the three
  items above), all non-empty text;
- `owner_target_id`: `null`, since the Concorde repository decides which of its Modules is at
  fault;
- `evidence`: a list of `{"path": ..., "description": ...}`, each path relative to this project,
  such as a file under a run directory in `.concorde/runs/`, with what it shows;
- `origin`: `{"project": "<this project's absolute path>", "head": "<its HEAD commit>",
  "concorde_commit": "<the receipt's source_commit>", "task": "<task id or null>"}`;
- `error_chain`: the whole error chain of the failure, unchanged, with your own link on top. In a
  task, `concorde task escalate <task> --code concorde_defect --detail "<what failed>"
  --reason scope --explanation "the fix lies in the Concorde repository, which this project never
  changes" --run <run-id>` records that link with the run's chain as its cause and prints it as
  `escalated`; use that value. Without a task, write your link in the same shape by hand, with the
  refusal's `error` as its only cause.

For example, with the error chain shortened:

```json
{
  "report_key": "write-hook-refuses-rw-directories",
  "type": "bug",
  "subtype": null,
  "title": "The worker write hook refuses files under an rw directory entry",
  "description": "The implement worker's edits of src/app/models.py were refused as undeclared.",
  "impact": "No implement run can change a file bound through a directory entry.",
  "basis": "Case: Concorde implements the boundary wrongly. The Spec binds src/, the grant ...",
  "owner_target_id": null,
  "evidence": [
    {"path": ".concorde/runs/w-20261001T101500-1a2b3c/control/grant.json",
     "description": "the frozen grant, src/ at rw"}
  ],
  "origin": {"project": "/home/dev/app", "head": "5d41402a...", "concorde_commit": "098eb928...",
             "task": "add-field"},
  "error_chain": {"level": "main-agent", "actor": "main agent (task add-field)", "...": "..."}
}
```

Then check it with `concorde issues report --check --file <path>`, which runs every check the
Concorde repository will run when it records the report and records nothing; repair the report
until the check passes.

Keep the runs the evidence names. Record the checked report in the task's decision log and
tell the developer where it is: the developer takes it to a session in the Concorde repository, which
records it as an Issue there and fixes it in its own task. Leave the work the defect blocks open
and turn to other work; do not close its task as failed for Concorde's sake.

### Take the fix

The developer tells you when the fix is merged, or you see its Issue closed with
`concorde issues list --root <source>`, which only reads. Then, from the primary worktree and
while no Operation, workflow or task session is running, run `concorde update`: it refuses while an
Operation run or a pi task-session round is still running, installs the new Concorde and leaves
the project unvalidated until `concorde validate` passes. Merge the primary branch into the open
tasks when the update asks for it, check that the reported problem is gone, and take up the work it
blocked.
