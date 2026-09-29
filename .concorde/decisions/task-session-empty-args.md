# Decision log: task-session-empty-args

Goal: The concorde_task_session pi tool treats an empty-string optional argument (answer, model, …) as absent instead of passing it on as an empty flag value

## Brief (main agent `claude session stuck debug`, 2026-09-29)

Origin: the main session `clear-conversation-state` (transcript
`~/.claude/projects/-home-zhenyu-concorde/5de1665c-db47-4727-8c85-4283bc290b4f.jsonl`) ran a live
headless pi verification in `/tmp/concorde-e2e/verify-pi` and found this defect; the developer
approved fixing it at 2026-09-29T06:34Z ("开吧，第4点也一起处理"). The task was deferred while the
overlapping tasks `owner-only-wake` and `tracing` were open (a first attempt was opened as
`task-session-tool-args` and closed failed); both have merged, so it is opened now.

Defect: the pi model filled optional fields of the `concorde_task_session` tool with empty strings
(`answer: ""`, `model: ""`). `src/concorde/main_session/pi_extension.ts` (around line 649) passes
any defined value on, e.g. `--answer ""`, and `concorde task session` (`src/concorde/tasks/cli.py`,
`arguments.answer is not None`) then treats it as an answer and refuses the call with
`invalid_input`. The main session failed three times and fell back to bash.

Decided: the tool treats an empty (or whitespace-only) string of any optional argument as absent.
The fix belongs in the tool (module.main-session); do not change `concorde task session` in
module.tasks. Cover it with a deterministic test, and say it in the Main session Spec if the tool's
arguments are described there.

Left to the session: the exact code shape, whether other tools of the extension share the pattern
(fix them the same way within module.main-session), and test placement.

## Task session (2026-09-29)

- Code shape: the argument list of `concorde task session` is built by a new pure function
  `taskSessionArgs` in `src/concorde/main_session/pi_runs.ts`, which reads `answer` and `model`
  through a new `givenText` (absent when missing, empty or whitespace-only; a non-empty value is
  passed on unchanged, not trimmed). Reason: `pi_runs.ts` is the part the tests run under Node;
  the extension itself needs a pi session. An empty `answer` with no `stop` is therefore a start
  and names the session with `--main`, like any start.
- Other tools: `concorde_run`'s optional `task` had the same pattern for whitespace-only values
  (an empty string was already falsy); it now goes through `givenText` too. Its `arguments` array
  is left as is: an empty element there may be a meant value (e.g. an empty `--goal`).
- Spec: added `scenario.main-session.pi-tool-empty-argument` to the Main session scenarios and a
  sentence to the `concorde_task_session` paragraph of `module.md`.
- Test: `OwnerTests.test_an_empty_optional_argument_is_absent` in
  `tests/concorde/main_session/test_pi_run_view.py` runs `taskSessionArgs`/`givenText` under Node;
  the round-owner test now checks the `--main` rule through `taskSessionArgs` instead of source
  strings.
- Verified: `tests/concorde/main_session` 43 passed, `build --check` and `spec-validation`
  success. Commit 44bab5bc.
- Delivered: `task-validation` ready, no blockers; `delivery` ok, delivery commit 7f09fefb (bundle `.concorde/evidence/task-session-empty-args/1.json`).

## Closed: merged, 2026-09-29T11:42:40Z
