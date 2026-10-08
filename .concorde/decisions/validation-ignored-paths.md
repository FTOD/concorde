# Decision log: validation-ignored-paths

Goal: Validation measures a changed path that Git neither tracks nor would add (ignored) as deleted, matching what Delivery commits, so an untracked file kept locally is no longer an unbound finding

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) to fix every known open Issue before the first full
`project_review`. This task resolves I-e8da7570 (module.validation, decision-needed, medium),
found by task bind-skill-links: `task-validation` measures a path the branch untracked
(`git rm --cached`, ignored by `.gitignore`, file left on disk) by its worktree content and blocks
it as `unbound`, although Delivery commits its deletion.

Decided by the main agent: the Issue's option (1). Validation measures a changed path that Git
neither tracks in the index nor would add (ignored) as deleted, digest and mode null, matching
what Delivery commits; readiness describes what Delivery commits. Update Validation's Spec
(requirement and a scenario), the measurement code (src/concorde/method/validation/measurement.py)
and tests, including a regression for an ignored symlink left on disk. Check that the readiness
digest and Delivery's own check agree on such a path.

Deliver with `task-validation` then `delivery`; run the full suite once on the final input.

## Task session decisions (2026-10-08)

- Detection of "Git would not commit it": a changed path from `git diff <base>` that exists on
  disk, that the index does not hold, and at which `git ls-files --others --exclude-standard`
  lists neither the path nor a path inside it. `git check-ignore` was tried first and rejected:
  it refuses literal pathspecs (a path starting with `:` fails) and fails with exit 128 on a path
  beyond a symbolic link, which would fail the whole measurement. The chosen rule is also exactly
  "`git add -A` adds nothing at it", so it covers an ignored file, a path beyond a symbolic link
  and a directory holding nothing Git would add; the contract states it as these three
  conditions.
- Helper named `ignored_paths` in measurement.py; `measure` uses one shared `_changes` pass so the
  diff and untracked listing are read once.
- Spec: new requirement `req.validation.committed-content`; `req.validation.unbound-paths` now
  excludes a path measured as deleted; contract `contract.validation.readiness` version 8 -> 9
  (behaviour change, per its own semantics) with a "measured as deleted" bullet; new scenario
  `scenario.validation.ignored-leftover` (validation then delivery of an untracked, ignored
  symlink left on disk; an index-held ignored file stays measured by content).
- Readiness vs Delivery's own check: the scenario's test delivers the workspace and asserts the
  delivery commit deletes the link, the link stays on disk, the saved readiness has the same input
  digest as task-validation's, and the worktree is clean after the commit (Delivery's
  `has_uncommitted`). The test fails on the old measurement with `unbound tools/link`.

## Report 1 to the main agent (concorde-d4), 2026-10-08T02:19:11Z

Delivered validation-ignored-paths: delivery commit 8bd3fb121a78ffbd4245a1918afbce4d13c92d92 on concorde/validation-ignored-paths (step db64dcc7). Resolves I-e8da75702b945d3ab7c83511efba298e (added with task resolve; the merge closes it).

What changed: Validation now measures a changed path as deleted (mode and digest null) when the base holds it, the index does not, and git ls-files --others --exclude-standard lists neither it nor a path inside it, i.e. git add -A adds nothing at it. That is the Issue's option (1). Spec: new req.validation.committed-content; req.validation.unbound-paths excludes a path measured as deleted; contract.validation.readiness 8 -> 9 with a 'measured as deleted' rule; new scenario.validation.ignored-leftover. Code: src/concorde/method/validation/measurement.py (ignored_paths, one shared _changes pass).

Readiness vs Delivery: the scenario test untracks an ignored symlink left on disk, then runs task-validation (ready, link recorded null/null) and delivery. The delivery commit deletes the link, the link stays on disk, the saved readiness has the same input digest, and the worktree is clean afterwards. An index-held file under an ignore rule is still measured by content. On the old code the test fails with 'unbound tools/link'.

Decisions I made (also in the decision log): I tried git check-ignore and rejected it. It refuses literal pathspecs and exits 128 on a path beyond a symbolic link, which would fail the whole measurement. The ls-files rule above is exactly 'git add -A adds nothing at it', so it also covers a path beyond a symlink and a directory holding nothing Git would add. I bumped the readiness contract version because its semantics require it for a behaviour change.

Verification: full suite 1288 passed, 5 skipped; build --check and spec-validation clean; task-validation ready with 26 checks passed.

Open: nothing.

## Closed: merged, 2026-10-08T02:19:30Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 8bd3fb121a78ffbd4245a1918afbce4d13c92d92 into main and closed it as merged. Nobody answers a report after that.
