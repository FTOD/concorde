# Decision log: claude-read-denial-limit

Goal: State in Workers that a Claude Code worker's read denials cover only paths that exist when its deny rules are generated, as the Harness already documents

## Brief (main agent, 2026-09-30)

The developer's decision (2026-09-30), answering review-workers' question Q1 on spec review finding
module.workers f.6 (bound review f.1): **option A, narrow the promise**. No read-side hook.

req.workers.read-denials promises that on the Claude Code backend the deny rules forbid Read, Glob
and Grep on every worktree path whose level is neither `ro` nor `rw`. Harness's claude-code.md
("Known limits") says a file created after the rules were generated has no rule of its own, and
unless a directory rule hides it, the file tools can read it.

Do:
- Narrow req.workers.read-denials, and any scenario or prose that states the same, to paths that
  exist when the deny rules are generated. Link Harness's known limit rather than restating its
  mechanism.
- State plainly, in Workers' own words, what remains. A worker's own writes outside `rw` are
  refused, and other non-ignored files that appear outside `rw` fail the run through the write
  audit. So the gap left is Git-ignored files another process creates in the worktree during the
  run, which the worker may read without anything failing. Keep the pi guarantee distinct: its
  permission extension checks every call against the grant.
- No code change. Keep scenario ids that tests declare, or update the tests' declarations.

Process: `uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`; format, `build --check`,
`spec-validation`, the relevant tests; task-validation and delivery; report with SendMessage.

## Task session (2026-09-30)

- Narrowed req.workers.read-denials to "every worktree path that exists when the host generates
  them and whose level is neither `ro` nor `rw`", and retitled it to match ("File tools cannot read
  what the grant withheld when the rules were generated"). Id kept.
- Narrowed scenario.workers.read-denied's GIVEN to files "both existing when its deny rules were
  generated". Id kept, so the two tests in tests/concorde/harness/workers/test_workers.py and
  test_live.py that declare it need no change; they already generate the rules from existing files.
- Stated what remains in module.md, "Why the run is built this way", in Workers' own words, linking
  the Harness's deny-rules section (harness/claude-code.md#deny-rules; the limit lives there, not in
  a section titled "Known limits") instead of restating its mechanism: the worker's own writes
  outside `rw` are refused, other non-ignored files outside `rw` fail the run through the write
  audit, so the gap is Git-ignored files another process creates during the run. The pi guarantee
  is kept distinct: checked against the Harness's pi read table and sandbox lists (the whole worktree
  denied, only `ro`/`rw` allowed) before saying pi has no such gap.
- Left Harness's module.md link to req.workers.read-denials unchanged: it only links, and Harness
  is outside the task's Modules.
- No code change. Verified: build --check, spec-validation (0 findings), tests/concorde/harness/workers
  (76 passed, 4 skipped).

- task-validation: ready (3 changed paths, 11 checks, 0 warnings). delivery: ok, delivery commit 22525a48.

## Closed: merged, 2026-09-30T07:32:37Z
