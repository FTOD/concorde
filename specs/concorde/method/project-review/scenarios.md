# Project review scenarios

Concrete situations that show the [requirements](requirements.md) at work. The result's and the
record's shapes are in the [contracts](contracts.md).

## Reviewing a project

### scenario.project-review.whole-project — A first review runs every part

- GIVEN a project with the issues part, of two structurally valid [Modules](../../glossary.json#concept.module) that no `project_review` judged before, whose workers are configured
- WHEN the [main agent](../../glossary.json#concept.main-agent) runs `project_review` unbound in the primary worktree
- THEN each Module's [Spec](../../glossary.json#concept.spec) panel and code review run, and the architecture review runs once, every worker under its own [worker id](../../glossary.json#concept.worker-id)
- AND every finding is an [Issue](../../glossary.json#concept.issue) of the Module it concerns, whose report names the part that made it as its `phase`
- AND the review record is committed alone on the primary branch, and the primary worktree holds no other change

### scenario.project-review.skips-unchanged — A repeated review skips what is unchanged

- GIVEN a project with the issues part and two Modules, whose every part a `project_review` completed and recorded, then a commit that changes only the code of the second Module
- WHEN the main agent runs `project_review` again
- THEN only the second Module's code review runs, and the first Module's Spec panel and code review, the second Module's Spec panel and the architecture review are skipped
- AND the first Module's outcome comes from the Issues that stand for it
- AND the configured checks still run, and the unchanged deterministic problems are carried with no new report

### scenario.project-review.nothing-to-review — A review with nothing to review is refused

- GIVEN a project with the issues part, whose every part a `project_review` completed and recorded, and that has not changed since
- WHEN the main agent runs `project_review` again, with or without `--architects 0`
- THEN before any step, the run is refused with `nothing_to_review`, and no worker runs
- AND no check runs, and no Issue and no review record is written
- AND its error names `--full` as the way to review the parts anyway

### scenario.project-review.code-change — A code change reviews only that Module's code

- GIVEN a project with the issues part, whose every part a `project_review` completed and recorded, then a commit that changes only the code of one Module
- WHEN the main agent runs `project_review` again
- THEN only that Module's code review runs
- AND an earlier Issue the code reviewer finds resolved no longer stands, but stays open for a task to close
- AND the record's entry of that code review names the new run, and its Spec panel's entry still names the first

### scenario.project-review.spec-change — A Spec change of any Module reviews the architecture again

- GIVEN a project with the issues part, whose every part a `project_review` completed and recorded, then a commit that changes only a document of the second Module
- WHEN the main agent runs `project_review` again
- THEN the second Module's Spec panel and the architecture review run
- AND the architecture review judges another [context identity](../../glossary.json#concept.context-identity) than the first run, and the record's architecture entry names the new run

### scenario.project-review.full — --full reviews everything

- GIVEN a project with configured workers whose every part a `project_review` completed and recorded, and that has not changed since
- WHEN the main agent runs `project_review --full`
- THEN every Spec panel, code review and the architecture review runs again

### scenario.project-review.failed-check — A failed check is an Issue until it passes

- GIVEN a project with the issues part and configured workers, and a structurally valid Module whose [configured check](../../glossary.json#concept.configured-check) fails on the examined commit, and whose code review is not skipped
- WHEN the main agent runs `project_review`
- THEN the check's failure is an Issue of that Module, `obvious-fix` and `high`, of phase `check`
- AND the Module's code reviewer receives the failed check's result and log

### scenario.project-review.check-repaired — A repaired check's Issue no longer stands

- GIVEN an open Issue of phase `check` that a `project_review` reported for a failed check
- WHEN the check passes again and the main agent runs `project_review`
- THEN that Issue is listed resolved and no longer stands
- BUT it stays open until a task closes it

### scenario.project-review.structural-error — A structurally invalid Module is incomplete alone

- GIVEN a Module whose Specs fail structural validation
- WHEN the main agent runs `project_review`
- THEN neither a Spec panel nor a code review runs for that Module, its outcome is `incomplete`, and the record gets no Spec panel or code review entry for it
- AND the architecture review still reads its Specs as they are written, when the architecture grant can be computed
- AND the other Modules' Spec panels and code reviews run unless skipped, and the run ends `blocked` with the Module's structural errors in its [error chain](../../glossary.json#concept.error-chain)

### scenario.project-review.bound — A bound run reviews the whole workspace

- GIVEN a project with the issues part, configured workers and structurally valid Modules, and a task worktree whose binding names one Module
- WHEN the [task session](../../glossary.json#concept.task-session) runs `project_review` there without `--modules`
- THEN the run covers every Module the workspace registers
- AND when its parts complete and change the record, the record is committed on the primary branch, not on the task branch

### scenario.project-review.narrowed — --modules narrows what the verdict counts

- GIVEN a project whose Module A has Issues that stand
- WHEN the main agent runs `project_review --modules` naming Module B alone
- THEN the result covers Module B alone, and the Issues that stand are counted for Module B alone
- AND when `--modules` names both Modules in the reverse of the registry's order, the result lists them in the registry's order

## Issues and the record

### scenario.project-review.skipped-resolutions — A skipped part keeps what it found resolved

- GIVEN a code review of `project_review` that found an earlier Issue resolved, which no task closed yet
- WHEN a later `project_review` skips that code review, since its Module is unchanged
- THEN that Issue does not stand for the Module, while its revision is unchanged
- BUT it stays open until a task closes it

### scenario.project-review.record-leftover — An interrupted write's record is put back

- GIVEN a primary worktree whose review record file holds a valid record no commit holds, as a write interrupted before its commit leaves it
- WHEN `project_review` publishes its record
- THEN the file is put back to its committed version first, and the new record is committed

### scenario.project-review.shared-earlier — spec_panel builds on project_review's Issues

- GIVEN an open Issue that a `project_review` Spec panel reported for a Module
- WHEN a task runs `spec_panel` for that Module
- THEN its workers receive that Issue as an earlier Issue, and the panel carries it when no finding names or resolves it

### scenario.project-review.architecture-earlier — The architecture review builds on spec_panel's architects

- GIVEN an open Issue that `spec_panel`'s architects reported for Module A, with the provenance phase `architecture`
- WHEN `project_review` runs its architecture review
- THEN its architects receive that Issue as an earlier Issue, and the review carries it when no finding names or resolves it
- AND no new Issue states the same problem again
- BUT A's Spec panel in that run is not offered the Issue, which still stands for A

### scenario.project-review.without-issues — Without the issues part nothing is skipped

- GIVEN a project without the issues part, which a `project_review` judged
- WHEN the main agent runs `project_review` again
- THEN every part runs again, no Issue is written and no record is committed
- AND each finding stays in the result, and each Module's outcome follows from this run's findings

### scenario.project-review.record-refused — A record with an uncommitted change is refused

- GIVEN a primary worktree whose review record file holds a change no commit holds, which is not a valid record
- WHEN the main agent runs `project_review`
- THEN the reviews complete and their Issues are written
- BUT the record is not written, and the run ends `failed` with `record_unpublished` naming the uncommitted change, its verdict still in the output
