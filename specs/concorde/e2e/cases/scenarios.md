# SWE-bench cases scenarios

Concrete situations that show the [requirements](requirements.md) of
[SWE-bench cases](module.md).

### scenario.swe-bench-cases.prepared — A case is prepared at its base commit

- GIVEN a repository whose branch has moved past a case's base commit
- WHEN the developer prepares the case with `--rev` set to that commit and `--name` set to the case
- THEN the project directory carries the case's name and its `main` branch holds the files of the base commit

### scenario.swe-bench-cases.grade — A merged change is graded with the case's tests

- GIVEN a project whose `main` branch does not yet resolve a case, and the case's test patch, FAIL_TO_PASS and PASS_TO_PASS tests
- WHEN the developer grades the project
- THEN the result names each FAIL_TO_PASS test that did not pass and reports the case unresolved

### scenario.swe-bench-cases.grade-resolved — A change that resolves the case is graded resolved

- GIVEN a project whose `main` branch holds a change that makes every listed test of a case pass and edits a test file the case's test patch also touches
- WHEN the developer grades the project
- THEN grading reports the case resolved, the test file graded as the case's test patch writes it
- AND afterwards the project's files are as its `main` branch holds them, the change's own edit of the test file included, and the project has no extra worktree

### scenario.swe-bench-cases.repair-specs — An adopted case's Specs are repaired before its issue

- GIVEN an adopted case whose Spec review requires changes
- WHEN the developer runs `repair-specs` for it
- THEN a task over the named [Modules](../../glossary.json#concept.module) runs, in its worktree, `spec_panel`, then `specify` with that review as input and an intent to change the [Specs](../../glossary.json#concept.spec) and never the code
- AND the task then runs `spec_panel` once more, `task-validation` and `delivery`, and is merged
- AND no run names the task: each works on the worktree's [workspace binding](../../glossary.json#concept.workspace-binding)

### scenario.swe-bench-cases.repair-accepted — An accepted review needs no repair

- GIVEN an adopted case whose Spec review accepts its Specs
- WHEN the developer runs `repair-specs` for it
- THEN the task runs `spec_panel`, `task-validation` and `delivery`
- BUT it runs no `specify` and no second review

### scenario.swe-bench-cases.repair-stopped — A step that does not end ok stops the repair

- GIVEN an adopted case whose Spec review requires changes and whose `specify` run ends `blocked`
- WHEN the developer runs `repair-specs` for it
- THEN the repair stops at `specify` with that step's result
- BUT the task is not merged and stays open
