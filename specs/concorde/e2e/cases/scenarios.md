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
- AND after a change that makes every listed test pass and edits the same test file itself, grading reports it resolved, the test file graded as the case's test patch writes it
- AND the project has neither the test patch's files nor an extra worktree afterwards

### scenario.swe-bench-cases.repair-specs — An adopted case's Specs are repaired before its issue

- GIVEN an adopted case whose Spec review requires changes
- WHEN the developer runs `repair-specs` for it
- THEN a task over the named Modules runs `spec_review`, then `specify` with that review as input and an intent to change the Specs and never the code, then `spec_review` once more, `validate` and `delivery`, and is merged
- AND a review that accepts the Specs is followed by `validate` and `delivery` with no repair
- BUT a step that does not end `ok` stops the repair with its result, and the task stays open
