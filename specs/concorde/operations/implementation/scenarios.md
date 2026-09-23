# Implementation scenarios

Concrete situations that show the [requirements](requirements.md) at work. The shapes of the code
change and the test report are in the [contracts](contracts.md).

## Implement

### scenario.implementation.implement-pass — A change passes its checks

- GIVEN a task worktree whose bound Module has configured checks
- WHEN the main agent runs `implement` for that Module with a goal the worker can meet in its grant
- THEN the host audits the change and runs the Module's configured checks outside the worker
- AND the result has status `ok` with the changed files and the passing check results

### scenario.implementation.resume — A failed check is repaired in a resume round

- GIVEN an implement run whose configured checks fail after the first round
- WHEN the host resumes the same worker session with the failed check results
- AND the worker's next round makes the checks pass
- THEN the result has status `ok` and records two rounds
- AND the host keeps the newest session identity of the worker

### scenario.implementation.rounds-exhausted — Checks still failing after the last round

- GIVEN an implement run whose configured checks still fail after the last allowed resume round
- WHEN the host evaluates the last check results
- THEN the result has status `failed` with the failing check results as host evidence
- AND the worker's edits stay uncommitted in the task worktree

### scenario.implementation.spec-gap — A Spec gap stops the run

- GIVEN a goal whose code needs a promise the bound Module's Spec does not state
- WHEN the worker returns `blocked` naming the Spec gap
- THEN the result has status `blocked` with the worker's escalation
- BUT the host neither resumes the worker nor changes any Spec document

### scenario.implementation.out-of-grant — A write outside the grant fails the run

- GIVEN an implement run whose write audit finds a changed file outside the grant's writable paths
- WHEN the host evaluates the audit
- THEN the result has status `failed` with that path as host evidence
- BUT no checks run and the worker is not resumed

### scenario.implementation.pending-file — A declared file is created and its marker cleared

- GIVEN a bound Module with a pending entry for a file that does not exist
- WHEN the main agent runs `implement` and the worker writes that file
- THEN the host created the file empty before launch
- AND after the last round the entry is no longer marked pending

### scenario.implementation.unused-pending — An unused declaration stays pending

- GIVEN a bound Module with a pending entry the worker does not need for its goal
- WHEN the worker leaves the pre-created file empty
- THEN the host removes the empty file
- AND the entry stays pending

### scenario.implementation.deletion — A proposed deletion is performed by the host

- GIVEN a worker whose result proposes deleting one file inside its writable paths and one outside
- WHEN the host processes the result after the audit
- THEN it deletes the file inside the writable paths
- BUT it refuses the other deletion and reports it as host evidence

## Test

### scenario.implementation.test-pass — Passing checks are reported

- GIVEN a task worktree whose bound Module's configured checks pass
- WHEN the main agent runs `test` for that Module
- THEN the host runs the checks before launching the worker
- AND the result has status `ok` with a test report marking every check passed

### scenario.implementation.test-fail — A failing check is interpreted

- GIVEN a task worktree whose bound Module has a failing configured check
- WHEN the main agent runs `test` for that Module
- THEN the worker reads the check log, the Spec and the code without running a command
- AND the test report keeps the host's failing check result
- AND it names the scenario or requirement concerned, the likely cause and whether the code, a test, the Spec or the environment is at fault
- BUT the result status is `ok`, because the run itself succeeded

### scenario.implementation.test-change — A change during a test run fails it

- GIVEN a test run whose write audit finds any changed or new file in the task worktree
- WHEN the host evaluates the audit
- THEN the result has status `failed` with the changed paths as host evidence
