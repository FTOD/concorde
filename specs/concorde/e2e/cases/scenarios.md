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

### scenario.swe-bench-cases.grade-statuses — Statuses follow complete identities and SWE-bench's rules

- GIVEN a case whose FAIL_TO_PASS lists a passing parametrized test under its complete identity, which holds a space
- AND its FAIL_TO_PASS lists the same test's identity cut at that space
- AND its FAIL_TO_PASS lists an expected failure
- AND its PASS_TO_PASS lists a skipped test
- WHEN the developer grades the project
- THEN grading reports the case resolved, every listed test counted as passed

### scenario.swe-bench-cases.grade-unresolved-statuses — A skipped or never-reported FAIL_TO_PASS test resolves nothing

- GIVEN a case whose FAIL_TO_PASS lists a skipped test
- AND its FAIL_TO_PASS lists a test pytest never reports
- WHEN the developer grades the project
- THEN grading reports the case unresolved
- AND it names the skipped test with its status `SKIPPED` and the other with `not run`

### scenario.swe-bench-cases.grade-cut-pass-to-pass — A cut PASS_TO_PASS identity agrees by its own list's rule

- GIVEN a case whose PASS_TO_PASS lists three parametrized tests, each by an identity cut at its first space that begins two reported identities
- AND the first test's two identities pass and are skipped
- AND the second test's two identities are skipped and then fail
- AND the third test's two identities fail and then are skipped
- WHEN the developer grades the project
- THEN the first cut identity counts as passed, since a skipped PASS_TO_PASS test is no regression
- AND the second and the third are named with `not run`, since a skipped and a failed test disagree on passing for PASS_TO_PASS
- BUT the order in which pytest reports their identities changes neither outcome

For FAIL_TO_PASS, the first test's identities would disagree instead, since a skipped FAIL_TO_PASS
test resolves nothing.

### scenario.swe-bench-cases.grade-listed-twice — A test listed twice counts twice

- GIVEN a case whose FAIL_TO_PASS lists one passing test twice
- AND its PASS_TO_PASS lists another passing test twice
- WHEN the developer grades the project
- THEN grading reports the case resolved
- AND each list counts 2 of its 2 listed tests as passed

### scenario.swe-bench-cases.repair-specs — An adopted case's Specs are repaired before its issue

- GIVEN an adopted case whose Spec review requires changes
- WHEN the developer runs `repair-specs` for it
- THEN a task over the named [Modules](../../glossary.json#concept.module) runs, in its worktree, `spec_panel`, then `specify` with that review as input and an intent to change the [Specs](../../glossary.json#concept.spec) and never the code
- AND the task then runs `spec_panel` once more, `task-validation` and `delivery`, and is merged
- AND no run names the task: each works on the worktree's [workspace binding](../../glossary.json#concept.workspace-binding)

### scenario.swe-bench-cases.repair-accepted — An accepted review needs no repair

- GIVEN an adopted case whose Spec review accepts its Specs
- WHEN the developer runs `repair-specs` for it
- THEN the task runs `spec_panel` alone
- AND the task is closed as completed, its note naming the accepting review
- BUT it runs no `specify`, no second review, no `task-validation` and no `delivery`, and it is not merged
- AND the command prints the task's end as `closed` and no step it stopped at

### scenario.swe-bench-cases.repair-stopped — A step that does not end ok stops the repair

- GIVEN an adopted case whose Spec review requires changes and whose `specify` run ends `blocked`
- WHEN the developer runs `repair-specs` for it
- THEN the repair stops at `specify` with that step's result
- BUT the task is not merged and stays open

### scenario.swe-bench-cases.grade-reset-paths — Files with special paths are reset before the patch

- GIVEN a case whose test patch changes a file whose path holds a space, a file whose path Git quotes and a renamed file, and removes a line beginning with `--`
- AND a change that edits each of them
- WHEN the developer grades the project
- THEN each file the patch touches, the renamed file's source included, is restored to the base commit before the patch applies
- AND the patch applies

### scenario.swe-bench-cases.grade-creation-failed — A grading worktree that cannot be made leaves nothing

- GIVEN a ref the project does not have
- WHEN the developer grades the project at that ref
- THEN grading fails with `command_failed`, naming `git worktree add`
- AND no scratch directory and no worktree of the grading is left

### scenario.swe-bench-cases.grade-cleanup-failed — A grading worktree that cannot be removed fails grading

- GIVEN a grading whose worktree Git cannot remove
- WHEN grading ends
- THEN it fails with `cleanup_failed`, naming the worktree and listing its registration and its scratch directory as left
- AND when the case's tests ran, the log the developer named holds their whole output in place of an earlier grading's
- AND when grading had failed before, `cleanup_failed` names that earlier error
