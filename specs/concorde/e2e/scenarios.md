# End-to-end testing scenarios

Concrete situations that show the [requirements](requirements.md) of
[End-to-end testing](module.md).

### scenario.e2e.repositories — SWE-bench's repositories are listed

- GIVEN a checkout with `references/swe-bench/` checked out
- WHEN the developer lists the repositories
- THEN the list names SWE-bench's Python repositories, among them `psf/requests` and `pallets/flask`

### scenario.e2e.unknown-repository — A repository SWE-bench does not name is refused

- GIVEN a checkout with `references/swe-bench/` checked out
- WHEN the developer prepares a repository not on the list without `--any`
- THEN preparation is refused with `unknown_repository` naming the known ones

### scenario.e2e.default-root — Test projects live in the temporary directory

- GIVEN an environment without `CONCORDE_E2E_ROOT`
- WHEN the tool resolves the [end-to-end root](../glossary.json#concept.end-to-end-root)
- THEN it is `concorde-e2e` in the system's temporary directory, outside the developer's home

### scenario.e2e.trust — Trusting a test project

- GIVEN a [test project](../glossary.json#concept.test-project) whose repository root Claude Code does not trust, and a configuration with other settings
- WHEN the developer runs `trust` for a directory inside it
- THEN the configuration marks that repository root trusted, keeps every other setting, and a backup of the file exists
- AND running `trust` again changes nothing

### scenario.e2e.headless — A headless run waits for its workflow without trust

- GIVEN an untrusted test project with an open task
- WHEN the developer starts a [headless run](../glossary.json#concept.headless-run) of the [brownfield workflow](../glossary.json#concept.brownfield-workflow) with `--restart scaffold=2`
- THEN the `claude -p` session has `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` set to `0`
- AND its command line grants the workflow and its step and report commands
- AND the workflow's arguments, the restart label `2` of `scaffold` included, reach the session's prompt
- AND the prompt places the session in the task's worktree and has it report with `concorde workflow report`
- BUT the workflow's arguments name no task
