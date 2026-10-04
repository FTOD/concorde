# Decision log: fix-open-worker-harness

Goal: Fix the open Issues of the worker harness part (Harness, Workers)

## Brief (main agent, 2026-10-04)

### Context

The developer asked (2026-10-04) to try to resolve the project's open Issues, after the parts
refactor merged into `main` (decision logs of parts-*, fix-* and parts-review* in
`.concorde/decisions/`). Every open Issue was reviewed and classified then; none is high or
critical. Nine tasks run in parallel, one per part or group of parts: fix-open-spec,
fix-open-method, fix-open-execution, fix-open-coordination, fix-open-worker-harness,
fix-open-kernel, fix-open-workflows, fix-open-root-distribution, fix-open-issues-e2e.

### How to work

- Your Issues are listed below with severity and tier; read each with `concorde issues show`
  (the latest report is the verified one). Work on them most severe first.
- **obvious-fix and preferred-fix**: fix them (preferred-fix: record which fix you chose and why).
  **decision-needed**: the main agent's decisions are below; carry them out. **suggestion**: fix it
  when it is cheap and clearly improves the Spec or code; otherwise leave it open.
- After fixing an Issue, add it to this task with `concorde task resolve <task> <issue>`: the
  merge closes exactly the Issues the task resolves, so add none you did not fix. Close an Issue
  that does not hold yourself (`not-actionable`, with the reason) or as `duplicate`. If a fix needs
  a decision with major impact, or another group's files beyond a small edit, escalate it with any
  others together rather than deciding it.
- Work directly in the Specs, code and tests; no Operation or review is needed. Keep edits of files
  other groups may touch small (glossary, registry mirror, shared tests, guidance composition); on a
  merge conflict the main agent asks you to merge `main` in.
- Introduce no regression: every part still works installed with only its dependencies
  (`tests/concorde/acceptance/test_parts.py`), the part-dependency check passes, guidance reads
  correctly whichever parts are installed (`tests/concorde/distribution/test_guidance_parts.py`).
  Rapid-iteration rule: no shims or compatibility paths.
- Verify with `build --check`, `spec-validation` and the full suite, then `task-validation` and
  `delivery`, and report: resolved, closed as not holding, left open (and why).

### Decisions of the main agent for your decision-needed Issues

- I-ff5160fb (final symlink at rw): make the code keep the existing promise that `rw` is the exact write allowlist: a write is judged by its real path with the final link resolved too, so a link listed at `rw` lets a write through only when its real target is writable; the write table, the write hook and pi's policy say so, with tests on both backends. This tightens the boundary; record it plainly.
- I-b471742c (deletions after a failed validation): follow launch.md: the host performs the proposed deletions after the last round whenever its audit was clean, except when the run ended with a violation; state that exception in the Spec.

### Your 25 Issues

- I-ff5160fbe27757c1a2f6150806e67957 (medium, decision-needed, module.harness): Final-symlink write rules conflict with the exact write allowlist
- I-2d7bb84c42845b0296df52f9e1262149 (medium, preferred-fix, module.harness): Pi read-table precedence contradicts runtime-path access
- I-657d8b78fbee5eef9a0f8441f27c3fbc (medium, preferred-fix, module.workers): Proposed deletions can escape the grant through directory symlinks
- I-6b51b73939f55ad9a6a35a27b7e100a2 (medium, preferred-fix, module.workers): Deleting a pre-existing untracked writable file passes the audit
- I-d17905845d845ef9b74416f3b4481120 (medium, preferred-fix, module.workers): Interrupting an active round discards its transcript
- I-db8baa0a921b5cb7be2c18130390e795 (medium, obvious-fix, module.harness): Read-only directory optimization denies nested writable directories
- I-2d4dfa0aaba456a5b5a6f5a4e7d4c1ea (medium, obvious-fix, module.harness): Write-hook command does not quote filesystem paths
- I-b471742cba8957319fcb2c52f4610751 (low, decision-needed, module.workers): Validation failure skips deletions promised after a clean final audit
- I-56a3f48b69ec5bd797234d05d47de05c (low, preferred-fix, module.harness): Pi filename fallbacks bypass the checked read path
- I-9be09b40f1c95d439e599b51aec76704 (low, preferred-fix, module.workers): Runtime removal failures are hidden from the run result
- I-2b2a3a71942356cdbfb9c9fb26680240 (low, obvious-fix, module.harness): Unhashable grant levels bypass the promised validation error
- I-4d2c267952c75805840de935e51f107c (low, obvious-fix, module.workers): The write audit does not detect branch-only changes
- I-89cf63759bd75b9da532af97359ce595 (low, obvious-fix, module.workers): Mode changes to already-dirty files evade the write audit
- I-72f9a7f14a0859bf9b954518a75fabcb (low, obvious-fix, module.workers): Early startup failures bypass final records and runtime cleanup
- I-f34350c156265a42b3e1810ebf0c1951 (low, obvious-fix, module.workers): Transcript copy errors silently destroy the retained evidence
- I-8a146024733f54c89c4e1f493581c6cb (low, obvious-fix, module.workers): Final run records contain a stale progress-file digest
- I-4836928d23f2583db5714777487c964f (low, obvious-fix, module.workers): Refused launches incorrectly record a prepared tool set
- I-0dd198f0bda65d7a8c27efd2c9cd8c2b (low, obvious-fix, module.workers): Timeout and process failures discard an already-returned worker result
- I-57ea640bf6645ebca7c1de4c52f90e53 (low, obvious-fix, module.workers): Pi runtime lookup uses the wrong root with separate Git metadata
- I-b73b0eb85ba65989a79fb75db4803da5 (low, obvious-fix, module.workers): Live pi tests no longer pass their selected model to pi
- I-bf1e33bfa33250f781151971efaa3d42 (low, suggestion, module.worker-harness): Explain the kernel collaboration behind the dependency
- I-2dcebe156e1f5ffa9f2473278b5a4294 (low, suggestion, module.worker-harness): Clarify optional validation and its outcome choices
- I-bb6d2f7dbf2256b89407f390cf2c0431 (low, suggestion, module.harness): Accepted relative path spellings produce inconsistent grants
- I-d786edaac61d59aa96be9a899bc700a5 (low, suggestion, module.harness): Pi budget enforcement has no behavioral test
- I-9a1efb3f43d9516fab12a6c3e137f5ae (low, suggestion, module.harness): Invalid pi results and valid retry are untested

## Task session decisions (2026-10-04)

- **I-ff5160fb (final symlink at rw), main agent's decision carried out.** The write hook and pi's
  `writeDecision` now judge a write by its real path, every symbolic link resolved, the final one
  included, also a dangling one (followed to the file it would create). This tightens the boundary:
  a link at a `rw` path now lets a write through only when its target is `rw`; before, its own name
  decided and pi's/Claude Code's write then followed it to an unauthorized target. A link outside
  `rw` whose target is `rw` is now allowed (the write changes only the `rw` file). Denials through a
  final link name the target judged and the link. Spec: claude-code.md#write-hook, pi.md#write-table,
  harness/module.md, launch.md req.workers.write-allowlist; tests on both backends.
- **I-b471742c (deletions after a failed validation), main agent's decision carried out.** Deletions
  now happen when the run ends, after a last round whose audit was clean and whose worker returned a
  valid result, whatever the outcome (ok, worker blocked/failed, timeout or process failure after the
  result, failed or unavailable validation), except a round-validation violation and an interrupted
  run (my addition: an interruption leaves the worktree as found). New req.workers.deletions-whatever-outcome.
  A `deletion_failed` link now carries the link the run would otherwise have ended with as its cause.
- **I-2d7bb84c (preferred-fix):** chose the fix the Issue names as clearly better: the runtime-path
  row moved above the worktree rows in pi.md's read table and in `readOne`; `searchDecision` also
  allows a search rooted at or containing a runtime path. The `.git` row stays first.
- **I-657d8b78 (preferred-fix):** proposed deletions are judged with their directories' symbolic
  links resolved (the Issue's suggested repair), keeping the final entry's name so a final link is
  removed itself, never its target.
- **I-6b51b739 (preferred-fix):** a snapshot path Git no longer lists is measured on disk instead of
  assumed equal to HEAD: gone means deleted (violation), present means changed.
- **I-d1790584 (preferred-fix):** chose discovery during streaming: ClaudeStream now records the
  session id from any stream record (the init record), the run keeps the latest session named, and
  `finish` locates that session's transcript, so an interrupted round keeps it.
- **I-56a3f48b (preferred-fix):** chose pi's ReadOperations over a shared resolver: the extension
  gives pi's `read` its own `access`/`readFile`/`detectImageMimeType`, each checking the exact path
  pi opens; the pre-check on the given path stays. Relies on pi exporting
  `detectSupportedImageMimeTypeFromFile` and `ReadOperations` (both in pinned 0.87.1 and installed 0.99.1).
- **I-9be09b40 + I-f34350c1 (preferred-fix / obvious-fix):** chose to surface cleanup failures in
  the run's error rather than a new record field nobody reads: a transcript that cannot be kept or a
  runtime directory that cannot be removed ends the run `failed` with the new code `cleanup_failed`
  (reason `environment`), naming what remains, with the link the run would otherwise have ended with
  as its cause. `remove_runtime` removes `config/` (credential copies) first, opens up directories
  the worker made unwritable/unreadable and retries once, and checks the directory is gone. A
  transcript that could not be kept is recorded as null. New req.workers.cleanup-reported.
- **I-72f9a7f1:** startup is guarded: a non-string context identity no longer reaches the node's
  metadata (the grant check refuses it with grant_malformed), the `started` callback runs inside the
  guarded run (a raising one ends the run `interrupted`), and a run whose node could not be started
  still has its runtime directory removed.
- **I-bb6d2f7d (suggestion), fixed:** chose to refuse rather than normalise non-canonical grant paths
  (`./x`, `a//b`): grant_malformed names it. The grant-input contract gained a path pattern and went
  to version 2.
- **Contract versions:** grant-input 1→2, worker-run-trace 4→5 (transcript null when not kept,
  transcript of an interrupted round, worker_result kept whatever ended its round), worker-run-record
  2→3. Rapid-iteration rule: no compatibility path.
- **I-d786edaa, I-9a1efb3f (suggestions), fixed with tests:** a new `PiExtensionTests` loads the
  generated permission extension under Node with the installed pi's own tool definitions and
  `validateToolArguments` and a recording stand-in for pi's extension API (skipped without Node or
  pi): it covers the budget limit, an invalid then valid `concorde_result`, and the read fallback.
- **I-bf1e33bf, I-2dcebe15 (suggestions), fixed:** the part entry now explains the kernel
  collaboration (Tracing nodes and error links) and marks the round validation optional with its
  unavailable outcome and the caller's choice at exhausted rounds.

## Task session decisions, after merging main (2026-10-04)

- Merged `main` (with fix-open-kernel and fix-open-root-distribution) into the task branch as the
  main agent asked; the merge had no conflict.
- **I-b5522be8 (obvious-fix):** no other producer reads `Node.failures` yet, so I chose the shape for
  Workers: a `trace_failures` list of strings (file, moment, error, as Node words them) in the
  worker-run trace content (failures known when it was written) and in the returned run record
  (completed with the final write's own failure), and `trace-write` evidence on the error of a run
  that does not end ok. The status never changes for a refused trace write. Both contracts gained the
  field inside the versions this task already bumped (worker-run-trace v5, worker-run-record v3);
  new req.workers.trace-failures-reported and scenario.workers.trace-failure-reported. Method does not
  yet carry `trace_failures` into its Operation's run result; that is Method's to decide.

## Task session decisions, second merge of main (2026-10-04)

- Merged `main` again (fix-open-spec); the first attempt stopped with "Unable to write index", so I
  aborted it and merged again, cleanly.
- **I-451c2b06 (preferred-fix), main agent's direction carried out:** a path's level is that of its
  most specific entry, its exact entry, else the longest directory entry above it, in the write hook,
  pi's `levelOf` (read and write), the audit (now given a `writable` predicate instead of the rw list)
  and proposed deletions. I chose "most specific entry" over replicating Spec core's exclusion rule:
  the harness stays independent of Spec core, and Spec core now lists an excluded file as its own
  entry. `GrantView.level` had the same flaw: a higher-ranked directory beat an exact entry. It now
  follows the same rule, and a directory collapses into one deny rule only when no entry below it
  gives another level.
  Decision without the developer: the Bash sandbox still writes a `rw` directory whole. I did not
  add a `denyWrite` list, since I cannot confirm here that Claude Code's sandbox settings accept one;
  a Bash write to such a file is an audit violation. Stated as a known limit in harness/module.md.
- Fixed the dogfood scenario `write-hook-rw-directories` (scripts/e2e/scenarios, module.dogfood-scenarios,
  a small edit outside the task's Modules): its fault edits targeted the old text of write_hook.py and
  pi_policy.ts; they now inject the same fault (rw directory entries ignored) into the new code.
- Main agent's small request: corrected the stale settings.py docstring and the same example in
  claude-code.md (a survey's grant with the Spec side withheld) to the read-only grant of a run that
  may not change its worktree, every rw lowered to ro.

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:57:29Z

fix-open-worker-harness delivered: delivery commit 5b5f3888 on concorde/fix-open-worker-harness (main merged in twice, both clean; build, spec-validation and the full suite pass: 1201 passed, 5 skipped).

Resolved (27, all added with task resolve): the 25 of the brief, plus I-b5522be8 and I-451c2b06 you added. None closed as not holding; none left open.

Your decisions carried out:
- I-ff5160fb: a write is judged by its real path, final link included (dangling links followed), in the write hook and pi's writeDecision. The boundary is tighter: a link at a rw path writes only when its target is rw. Denials name the target and the link. Tested on both backends.
- I-b471742c: deletions follow every last round with a clean audit and a valid result, whatever the outcome. Exceptions: a round-validation violation, and (my addition) an interrupted run. deletion_failed now carries the link the run would otherwise have ended with as its cause.
- I-451c2b06: the most specific entry decides a path's level (exact, else longest directory) in the hook, pi policy, audit, deletions and GrantView/deny rules (GrantView let a higher-ranked directory beat an exact entry).
- settings.py docstring and the same example in claude-code.md corrected (read-only grant, rw lowered to ro).

Decisions I made (details in the decision log):
- New Workers code cleanup_failed: a transcript that can't be kept or a runtime directory that can't be removed fails the run (I-9be09b40, I-f34350c1), wrapping the link it would otherwise have ended with. remove_runtime removes config/ first, opens up locked directories and retries, and checks the directory is gone.
- I-b5522be8: trace_failures in the worker-run node content and the returned record (plus the final write's own failure), and trace-write evidence on a failed run's error. Method does not yet carry trace_failures into its Operation result; that is Method's call.
- pi read checks the exact path pi opens via its ReadOperations (I-56a3f48b). The runtime-path row moved above the worktree rows in pi's read table (I-2d7bb84c).
- Non-canonical grant paths (./x, a//b) are refused as grant_malformed (I-bb6d2f7d).
- Contract versions: grant-input 2, worker-run-trace 5, worker-run-record 3.
- New PiExtensionTests load the real extension under Node with the installed pi (budget limit, invalid then valid concorde_result, read fallback); they are skipped without Node or pi.
- Small edit outside my Modules: scripts/e2e/scenarios/write-hook-rw-directories.json's fault edits now target the new code (same fault).

Still open, for you to weigh: the Bash sandbox still writes a rw directory whole, so a Bash write to a ro file listed below one is caught only by the audit (a violation that fails the run). I added no denyWrite list because I could not confirm Claude Code's sandbox settings accept one. It is stated as a known limit in harness/module.md. The live pi test change (I-b73b0eb8) was not run, since it needs CONCORDE_LIVE_PI.

## Closed: merged, 2026-10-04T02:57:49Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 5b5f3888ddefac0d0e0c711fcbee14c2708c1438 into main and closed it as merged. Nobody answers a report after that.
