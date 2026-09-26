# End-to-end testing scenarios

Concrete situations that show the [requirements](requirements.md) of
[End-to-end testing](module.md).

### scenario.e2e.repositories — Only SWE-bench's projects are prepared

- GIVEN a checkout with `references/swe-bench/` checked out
- WHEN the developer lists the repositories
- THEN the list names SWE-bench's Python repositories, among them `psf/requests` and `pallets/flask`
- BUT preparing a repository not on the list is refused with `unknown_repository` naming the known ones
- AND without `CONCORDE_E2E_ROOT` the end-to-end root is `concorde-e2e` in the system's temporary directory, outside the developer's home

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
