# End-to-end testing scenarios

Concrete situations that show the [requirements](requirements.md) of
[End-to-end testing](module.md).

### scenario.e2e.repositories — Only SWE-bench's projects are prepared

- GIVEN a checkout with `references/swe-bench/` checked out
- WHEN the developer lists the repositories
- THEN the list names SWE-bench's Python repositories, among them `psf/requests` and `pallets/flask`
- BUT preparing a repository not on the list is refused with `unknown_repository` naming the known ones

### scenario.e2e.case — A case is prepared at its base commit

- GIVEN a repository whose branch has moved past a case's base commit
- WHEN the developer prepares the case with `--rev` set to that commit and `--name` set to the case
- THEN the project directory carries the case's name and its `main` branch holds the files of the base commit

### scenario.e2e.grade — A merged change is graded with the case's tests

- GIVEN a project whose `main` branch does not yet resolve a case, and the case's test patch, FAIL_TO_PASS and PASS_TO_PASS tests
- WHEN the developer grades the project
- THEN the result names each FAIL_TO_PASS test that did not pass and reports the case unresolved
- AND after a change that makes every listed test pass, grading reports it resolved
- AND the project has neither the test patch's files nor an extra worktree afterwards

### scenario.e2e.trust — Trusting a test project

- GIVEN a test project whose repository root Claude Code does not trust, and a configuration with other settings
- WHEN the developer runs `trust` for a directory inside it
- THEN the configuration marks that repository root trusted, keeps every other setting, and a backup of the file exists
- AND running `trust` again changes nothing

### scenario.e2e.headless — A headless run waits for its workflow without trust

- GIVEN an untrusted test project with an open task
- WHEN the developer starts a headless run of the brownfield workflow
- THEN the `claude -p` session has `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` set to `0`
- AND its command line grants the workflow and its step and report commands
- AND the workflow's arguments, restart labels included, reach the session's prompt
