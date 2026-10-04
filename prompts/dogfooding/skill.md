---
audience: shared
---

## Developing Concorde while using it

This project is a **develop install** of Concorde. It runs the Concorde of the Concorde repository
that the receipt `.concorde/install.json` names as its `source`. Concorde is installed at the
commit the receipt records as `source_commit`. The developer also changes Concorde there, in a
separate session that follows that repository's own rules. You have three duties:

- Use Concorde for this project as usual.
- Watch Concorde while you do.
- Hand every Concorde defect you find over to that repository.

@prompts/dogfooding/common/observe-runs.md

A run can end `ok` and still be wrong. Examples include:

- A worker that changed a file outside the task's goal.
- A check that ran no test.
- A summary its evidence contradicts.

Treat those like failures.

### Never change Concorde from here

Even to unblock yourself, do not edit any of these:

- The Concorde repository.
- The framework copy under `.concorde/framework/`.
- Any file the installer placed or amended (the receipt lists them).

The next update overwrites such a change. Such a change would also bypass the Concorde
repository's own safeguards:

- Tasks.
- Checks.
- Review.

Do not work around a Concorde defect either, because a workaround hides the defect. For example,
do not change this project's Specs only so that a wrongly computed boundary lets the work through.

### Whose problem is it

A problem of this project is ordinary work here. This includes problems of:

- Its Specs.
- Its code.
- Its checks.
- Its configuration.
- The way you used Concorde.

A **Concorde defect** is one that would happen in any project using Concorde the same way.
Examples include:

- A crash or wrong result of any of these:
  - A `concorde` command.
  - An Operation.
  - A workflow.
  - The host.
- A grant or harness that differs from what the Protocol derives from the Specs.
- An error chain that loses a link or a detail.
- Guidance or worker instructions that lead an agent wrong.
- A Protocol that cannot express what a correct project needs.

In doubt, say which points in your reasoning are uncertain in the report's `basis`.

### When a boundary blocks work

A boundary refuses a worker's access to any of these:

- A read.
- A write.
- A tool.

Where the method part is installed, workers run. When any such access is refused, decide which of
four cases it is before doing anything else:

| Case | How you tell | Where it goes | Who decides |
| --- | --- | --- | --- |
| The boundary is right; the work overreaches | The task's goal does not need that access | Nowhere: do the work another way, or open a task for the other Module | You |
| This project's Specs draw the boundary wrongly | The grant is what the Protocol derives from the Specs, but the Specs misdescribe the Modules' ownership, uses or references | This project: an Issue here (`gap`) and a task that corrects the Specs | The developer, when the correction changes relations between Modules |
| Concorde implements the boundary wrongly | The grant or harness actually applied differs from what the Protocol derives from the Specs | A Concorde defect report of type `bug` | The Concorde repository fixes it |
| Concorde's design blocks a correct boundary | The Specs are right and the grant is what the Protocol derives, yet legitimate work needs the access | A Concorde defect report of type `limitation` | The developer, before Concorde's design or Protocol changes |

Whichever case it is, write down three things. When it goes to Concorde, write them in the
report's `basis` and `evidence`:

- The Spec text and Protocol rule the boundary is derived from.
- The grant actually computed, from `concorde grant --modules <ids> --type <task type>` and the
  run's host evidence. This command belongs to the spec part, which the method part always comes
  with.
- The refused action with its message.

Never settle a blocked boundary by only loosening it.

### Report a Concorde defect

Write the report as one JSON object to `.concorde/runs/defects/<report_key>.json`, which Git
ignores. It is an Issue report and nothing else. Unless marked optional, all its fields are
required:

- `report_key`: a short kebab-case name of the defect, the same as the file name.
- `tier`: who may fix it in the Concorde repository, one of Issues' tiers:
  - When the defect and its fix are both obvious, `obvious-fix`.
  - When one of several fixes is clearly better, `preferred-fix`.
  - When the cause or the fix is uncertain, `decision-needed`.
  - For no defect today, `suggestion`.
- `severity`: how much the defect matters to work using Concorde, one of Issues' severities:
  - `critical` for any of these:
    - Wrong results.
    - Lost or corrupted data.
    - A security hole.
    - A core flow broken with no workaround.
  - For a main flow broken or wrong with a workaround, `high`.
  - For a secondary flow or an edge case, `medium`.
  - For something cosmetic, `low`.
- `type`: one of these:
  - `bug` (a failure or wrong result).
  - `limitation` (consistent but insufficient behaviour).
  - `gap`.
- `subtype`: for a bug or a limitation, `null`. For a gap, use one of these:
  - `implementation-spec-mismatch`.
  - `spec-conflict`.
  - `missing-contract`.
- The following fields are all non-empty text:
  - `title`.
  - A `description` of what you saw.
  - The `impact` on your work.
  - A `basis` saying why the defect is Concorde's and not this project's.
    For a blocked boundary, include its case and the three items above.
- `owner_target_id`: `null`, since the Concorde repository decides which of its Modules is at
  fault.
- `evidence`: a list of `{"path": ..., "description": ...}`. Each path is relative to this
  project, with what it shows. For example, a path can name a file of a run's folder under
  `.concorde/tasks/<task>/workspace/runs/` or `.concorde/unbound/`.
- `origin`: `{"project": "<this project's absolute path>", "head": "<its HEAD commit>",
  "concorde_commit": "<the receipt's source_commit>", "task": "<task id or null>"}`.
- `error_chain`: the whole error chain of the failure, unchanged, with your own link on top.
  In a task, use this command:
  `concorde task escalate <task> --code concorde_defect --detail "<what failed>"
  --reason scope --explanation "the fix lies in the Concorde repository, which this project never
  changes" --run <run-id>`.
  It records that link with the run's chain as its cause. It prints the chain as `escalated`.
  Use that value. When the run ended `ok` and still did something wrong, there is no error to
  extend. In that case, run the same command without `--run`. Give it a `--detail` that names:
  - The run.
  - Its `result.json`.
  - What shows the fault.

  Your link, with no causes, is the whole chain. Without a task, write your link by hand in the
  shape of the error contract. Include these fields:
  - `level` set to `main-agent`.
  - An `actor` naming you and `no task`.
  - `code` set to `concorde_defect`.
  - A `detail` saying what went wrong.
  - `evidence` as a list of `{"kind": ..., "ref": ..., "detail": ...}` citing the run and what
    shows the fault.
  - `attempts`.
  - `unhandled` with the reason `scope` and that explanation.
  - `options`.
  - A `recommendation`.
  - `causes`: as its only cause, use one of these:
    - The failure's `error`.
    - The refusal's error.
    - The `error` of the run's `result.json`.

    When the run ended `ok`, include no causes.

For example, with the error chain shortened:

```json
{
  "report_key": "write-hook-refuses-rw-directories",
  "tier": "decision-needed",
  "severity": "high",
  "type": "bug",
  "subtype": null,
  "title": "The worker write hook refuses files under an rw directory entry",
  "description": "The implement worker's edits of src/app/models.py were refused as undeclared.",
  "impact": "No implement run can change a file bound through a directory entry.",
  "basis": "Case: Concorde implements the boundary wrongly. The Spec binds src/, the grant ...",
  "owner_target_id": null,
  "evidence": [
    {"path": ".concorde/tasks/fix-retry/workspace/runs/r-20261001T101500-implement-1a2b3c4d/workers/w-20261001T101501-1a2b3c/grant.json",
     "description": "the frozen grant, src/ at rw"}
  ],
  "origin": {"project": "/home/dev/app", "head": "5d41402a...", "concorde_commit": "098eb928...",
             "task": "add-field"},
  "error_chain": {"level": "main-agent", "actor": "main agent (task add-field)", "...": "..."}
}
```

Then check it with `concorde issues report --check --file <path>`. This runs every check the
Concorde repository will run when it records the report. It records nothing. Until the check
passes, repair the report.

**A defect of the Issue system itself** is never written as a defect report. Such a defect is a
crash or wrong result of any of these:

- Concorde's Issue store.
- `concorde issues`.
- The project MCP server's Issue tools.

This includes `concorde issues report --check` refusing a correct report. Do not write such a
defect as a defect report because it is an Issue report. The Concorde repository would record it
with the very Issue system that failed. A refusal whose reason is `environment`, such as
`merge_busy`, is no defect. Wait for the lock, or for the merge to finish, and write again.
Hand such a defect over as its error chain alone, with your own link on top. In a task, use
`concorde task escalate <task> --code
concorde_defect --reason scope`, as above. When a run's result carries the failure, use
`--run <run-id>`. Otherwise, use `--error-file <json>` naming a file that holds the failing
command's `{"error": ...}` output. The command records that link in the task. It prints the
chain as `escalated`. Without a task, write your link by hand as above, with the failure's error
as its only cause. Write that chain as one JSON object to `.concorde/runs/defects/<name>.error.json`.
This file is no Issue report. `concorde issues report --check` does not check it. Name it to the
developer. The developer hands it to the Concorde repository as a failure to fix there.
It is never a report to record as an Issue.

Keep the runs the evidence names. In a task, record the checked report in the task's decision
log. Tell the developer where it is. The developer takes it to a session in the Concorde
repository. That session records it as an Issue there. It fixes it in its own task. Leave the
work the defect blocks open. Turn to other work. Do not close its task as failed for Concorde's
sake. A defect you saw outside a task, such as in an unbound run or a refused command, opens no
task. Keep its report only under `.concorde/runs/defects/`. Name that file to the developer,
as you do with the error chain of a defect of the Issue system.

### Take the fix

The developer tells you when the fix is merged, or you see its Issue closed with
`concorde issues list --root <source>`. This command only reads. Then, while none of these runs,
run `concorde update` from the primary worktree:

- A run of an Operation or execution command.
- A workflow.
- A task session.

While any of these still runs, the update refuses. It installs the new Concorde.
Where the spec part is installed, it leaves the project unvalidated until
`concorde spec-validation` passes. Until the update ends, start none of these in any worktree
of the project:

- A run.
- A task session.
- Another `concorde` command.

This restriction exists because the update's check does not stop what starts after it.
Anything that starts after that check may find Concorde half replaced. When the update asks for
it, answer the session of each open task to merge the primary branch into its task branch.
Check that the reported problem is gone. Take up the work it blocked.
