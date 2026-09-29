# Decision log: trim-shared-vocabulary

Goal: Keep shared vocabulary concise, remove duplicated workflows, and make root reading independent of reading vocabulary first

## Editorial scope

The developer approved keeping shared terminology, removing duplicated workflow explanations,
and removing the requirement to read vocabulary before the Framework entry. Only the two root
Module reading files change. All 15 canonical definitions, concept identities, anchors, metadata
and context selections are preserved. Actor lifecycle and escalation details stay in the existing
responsible Modules; brief explanations keep the vocabulary useful within a consumer's context.

No EnterWorktree tool is available in this session. All task commands use an explicit task-worktree
working directory and all source edits use its absolute paths. The primary sources stay untouched
until the task merge.

## Verification

Build freshness and structural validation passed without findings. The validate Operation
r-20260926T170946-validate-f4cfe00e reported ready, with check.concorde.tests passing.
A direct comparison confirmed all defining rows and all concept anchors are unchanged.

The first full-suite invocation stopped at argument parsing because its free-form --reason value
was not one of the pytest evidence plugin's allowed values; no tests ran. Restarted the full suite
with the repository's standard `.venv/bin/python -m pytest` command.

The full suite passed: 567 passed, 4 skipped. Reviewed the staged diff and confirmed whitespace
checks on two passes. Committed the editorial step as 813c9a50. Delivery
r-20260926T171107-delivery-617e8dfb passed its readiness and configured check, then committed the
evidence bundle as 5d6326ca. Vocabulary shrank from 1,700 to 1,211 whitespace-delimited words.

## Closed: merged, 2026-09-26T17:11:42Z
