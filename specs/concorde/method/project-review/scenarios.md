# Project review scenarios

Concrete situations that show the [requirements](requirements.md) at work. The result's and the
record's shapes are in the [contracts](contracts.md).

## Reviewing a project

### scenario.project-review.whole-project — A first review runs every part

- GIVEN a project of two [Modules](../../glossary.json#concept.module) that no `project_review` judged before
- WHEN the [main agent](../../glossary.json#concept.main-agent) runs `project_review` unbound in the primary worktree
- THEN each Module's [Spec](../../glossary.json#concept.spec) panel and code review run, and the architecture review runs once, every worker under its own [worker id](../../glossary.json#concept.worker-id)
- AND every finding is an [Issue](../../glossary.json#concept.issue) of the Module it concerns, whose report names the part that made it as its `phase`
- AND the review record is committed alone on the primary branch, and the primary worktree holds no other change

### scenario.project-review.skips-unchanged — A repeated review skips what is unchanged

- GIVEN a project that a `project_review` judged, and that has not changed since
- WHEN the main agent runs `project_review` again
- THEN no worker runs, and every Spec panel, code review and the architecture review is skipped
- AND each Module's outcome comes from the Issues that stand for it
- AND the configured checks still run, and the unchanged deterministic problems are carried with no new report

### scenario.project-review.code-change — A code change reviews only that Module's code

- GIVEN a judged project, then a commit that changes only the code of one Module
- WHEN the main agent runs `project_review` again
- THEN only that Module's code review runs
- AND an earlier Issue the code reviewer finds resolved no longer stands, but stays open for a task to close
- AND the record's entry of that code review names the new run, and its Spec panel's entry still names the first

### scenario.project-review.full — --full reviews everything

- GIVEN a judged project that has not changed since
- WHEN the main agent runs `project_review --full`
- THEN every Spec panel, code review and the architecture review runs again

### scenario.project-review.failed-check — A failed check is an Issue until it passes

- GIVEN a Module whose [configured check](../../glossary.json#concept.configured-check) fails on the examined commit
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
- THEN no worker reviews that Module, its outcome is `incomplete` and the record gets no entry for it
- AND the other Modules are reviewed, and the run ends `blocked` with the Module's structural errors in its [error chain](../../glossary.json#concept.error-chain)

### scenario.project-review.bound — A bound run reviews the whole workspace

- GIVEN a task worktree whose binding names one Module
- WHEN the [task session](../../glossary.json#concept.task-session) runs `project_review` there without `--modules`
- THEN the run covers every Module the workspace registers
- AND the record is committed on the primary branch, not on the task branch

## Issues and the record

### scenario.project-review.shared-earlier — spec_panel builds on project_review's Issues

- GIVEN an open Issue that a `project_review` Spec panel reported for a Module
- WHEN a task runs `spec_panel` for that Module
- THEN its workers receive that Issue as an earlier Issue, and the panel carries it when no finding names or resolves it

### scenario.project-review.without-issues — Without the issues part nothing is skipped

- GIVEN a project without the issues part, which a `project_review` judged
- WHEN the main agent runs `project_review` again
- THEN every part runs again, no Issue is written and no record is committed
- AND each finding stays in the result, and each Module's outcome follows from this run's findings

### scenario.project-review.record-refused — A record with an uncommitted change is refused

- GIVEN a primary worktree whose review record file holds a change no commit holds
- WHEN the main agent runs `project_review`
- THEN the reviews complete and their Issues are written
- BUT the record is not written, and the run ends `failed` with `record_unpublished` naming the uncommitted change, its verdict still in the output
