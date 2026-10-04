# Decision log: fix-open-root-distribution

Goal: Fix the open Issues of the root, the distribution part and Dogfooding

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

### Your 27 Issues

- I-4db33d4f8ffd5d459f12b1faa653dcbe (medium, preferred-fix, module.dogfooding): Develop source checking crashes on repository paths containing spaces
- I-6388252db5445452bfee2e5602df9581 (medium, preferred-fix, module.concorde): Interrupted response bodies bypass documentation fetch failure reporting
- I-8f9eb3e6cdfd5456bfab5b13b97440da (medium, obvious-fix, module.dogfooding): Develop guidance omits execution-command runs
- I-a795173059fc56939a022baec2ec88ee (medium, obvious-fix, module.concorde): Documentation page paths can escape the staging directory
- I-8eb5420c3362588cab01206276416eb3 (medium, obvious-fix, module.concorde): Failed snapshot restoration still deletes the backup
- I-b2bdc1c293b6563daa070d840b8aac0a (medium, obvious-fix, module.distribution): Installer preflight accepts a falsy non-object `permissions` in .claude/settings.json and crashes after writing
- I-ad4e637525145de0a514119c2c0e5dca (low, preferred-fix, module.dogfooding): Linked-worktree refusal can name the wrong primary worktree
- I-3ed36f3722c55a99932e3d9f24991246 (low, preferred-fix, module.concorde): Early-stopped test runs lose collected units from their totals
- I-5e2d019798e059b8a90dd36de9ee4c84 (low, preferred-fix, module.concorde): Test evidence CLI value restrictions have no stated contract
- I-fde7a6ca2fa45c0eae2c6352d480b6fc (low, preferred-fix, module.distribution): protocol-manifest's precondition and write table live only in module reading
- I-22cc42fcd0e5506a81192bb1048b44ef (low, obvious-fix, module.concorde): Input fingerprints silently omit declared files
- I-0abb70ff27e45b9e8077937755265d4c (low, obvious-fix, module.concorde): Environment fingerprints misreport effective bytecode settings
- I-1dc56c17ae915a4d9e77ab6832153fe1 (low, obvious-fix, module.concorde): The user guide omits the command error-format exceptions
- I-91aabdcdb8a95028ac1da98a7afae33d (low, obvious-fix, module.concorde): The README understates the number of task types
- I-1de97e8b1bf253c28c05b0ebb42a72a7 (low, obvious-fix, module.distribution): Replacing the CLAUDE.md block strips blank lines that follow its end marker
- I-7417545a15615f13861ba6cd8a7c2680 (low, obvious-fix, module.distribution): Installer and `concorde update` refuse malformed arguments with argparse usage text and exit 2, not an error link
- I-33a1c97a70a256c0a4a1c350fd988dc1 (low, obvious-fix, module.distribution): Project MCP call_failed links drop what the call's process printed on timeout and in long work
- I-031366c07f45523b82d9a5a2f759a39b (low, obvious-fix, module.distribution): `concorde protocol-manifest` crashes without an envelope on a structurally malformed tracked manifest
- I-b26defe9ab94506c9bdd94a0178e223c (low, obvious-fix, module.concorde): The Main agent definition says it asks the developer every question a task needs
- I-684059ec01e95fe38da894bda8209759 (low, obvious-fix, module.concorde): req.concorde.test-prior-compare's SHALL omits the null outcomes its explanation gives
- I-d8b60e4393565e3a9ce516ce1bfcedaf (low, obvious-fix, module.distribution): req.distribution.installer-fresh-guidance says 'older than its sources' and covers only guidance
- I-d31fff343618550eb1b3532898d296c3 (low, obvious-fix, module.distribution): The update's rebinding step does not say what happens in a project that is not initialized
- I-1100d67b7d965a809dab1c0d09e7e259 (low, obvious-fix, module.distribution): install-later-files-bound states the binding more broadly than the requirement
- I-157f6deea1895d47af953309630ece99 (low, suggestion, module.concorde): Task context's standalone definition leaves 'task' ambiguous
- I-a3522268b2175ec69277cd0c5e40b3a4 (low, suggestion, module.concorde): Root requirements restate grant provenance, Git isolation and claim separation of children
- I-efaedb0611a756b48277b7e0088a5985 (low, suggestion, module.distribution): The build renderer's include grammar and uv invocations sit in the Module entry
- I-b1cbff3a9acb57d18e1ea7eecbb43b39 (low, suggestion, module.concorde): Nothing checks that a part's Module declares its use of Distribution's registration contract

## Task session decisions (2026-10-04)

- **I-4db33d4f (preferred-fix)**: chose the suggested fix. `develop_source` asks Git for
  `--git-dir` and `--git-common-dir` in two calls and keeps each output whole; a failed call is
  refused as `develop_source_unreadable` (already a code; now named in Dogfooding's module.md).
  Tested with a source and a linked worktree under paths containing spaces.
- **I-ad4e6375 (preferred-fix)**: the suggested repair (first entry of `git worktree list
  --porcelain`) does not hold: Git 2.43 lists the separate Git directory itself as the primary
  worktree there (reproduced). Git records the primary worktree only as the parent of a common
  directory named `.git` or as `core.worktree`; otherwise the refusal now names the Git directory
  and says Git records no path for the primary worktree. Restated req.dogfooding.refusal-names-reason
  accordingly ("or, where Git records no such path, the repository's Git directory").
- **I-6388252d (preferred-fix)**: `fetch` turns every `OSError` (URLError, timeouts, connection
  resets) and `http.client.HTTPException` (IncompleteRead) into the page's RuntimeError, so all
  failed pages are aggregated; requirement text names a body cut short.
- **I-8eb5420c**: the backup is removed only after the swap or the restoration succeeded; a failed
  restoration raises `RestoreError`, keeps the backup and the refusal names it instead of saying
  "unchanged". Requirement explanation states this one exception.
- **I-7417545a**: new refusal code `invalid_arguments` (input, before any write) for the
  installer's and `concorde update`'s malformed command lines, through a shared `ArgumentParser` in
  install.py; added to the refusal table and scenario.distribution.install-refusal-link.
- **I-33a1c97a**: a `call_failed` detail now gives the end of both streams, timeouts included;
  added scenario.distribution.mcp-call-failed (no scenario illustrated the requirement before).
- **I-fde7a6ca (preferred-fix)**: chose the suggested fix: new
  req.distribution.protocol-manifest-precondition and scenario.distribution.protocol-manifest-refused;
  the flag table stays explanatory in module.md. The precondition now covers a manifest not of the
  manifest's shape (I-031366c0).
- **I-3ed36f37 (preferred-fix)**: chose the Spec restatement over synthesizing units for tests that
  never ran (they have no times or outcome; fake units would distort spans and totals):
  req.concorde.test-counting now counts the tests that ran beside `collected`.
- **I-22cc42fc**: Spec already excludes non-regular files and symlinks; made explicit that a listed
  deleted path is no input (its absence changes the digest). No code change.
- **I-5e2d0197 (preferred-fix)**: listed the accepted values in req.concorde.test-evidence.
- **I-b26defe9, I-157f6dee**: glossary definitions restated (main agent decides ordinary questions
  and asks those its decision policy reserves; task context is material for one worker's job).
- **I-b1cbff3a (suggestion)**: fixed: new test in test_part_dependencies.py requires the Module
  binding each part's registration.json to rely on contract.distribution.part-registration. It found
  two gaps, fixed by small edits in other groups' Modules: `module.workers` gained a `uses` of
  Distribution (with a short #uses-distribution paragraph) and `module.tasks`'s existing `uses` of
  Distribution gained the two relies_on items; registry mirror refreshed.
- **Left open (suggestions, not cheap or clearly better)**: I-a3522268 (root requirements restating
  children: the duplication is the root requirements' stated design; reducing them changes the root's
  requirement set) and I-efaedb06 (moving the include grammar and uv invocations out of
  Distribution's module entry is a restructuring of the entry, readability only).

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:33:38Z

fix-open-root-distribution delivered: delivery commit e16bb4cb on concorde/fix-open-root-distribution. Checks: build --check ok, spec-validation success, full suite 1091 passed / 5 skipped, task-validation ready.

Resolved (25, added with task resolve; the merge closes them):
- Dogfooding: I-4db33d4f (develop source paths with spaces read whole), I-ad4e6375, I-8f9eb3e6 (develop guidance and its tests now cover execution-command runs).
- Root/development: I-6388252d, I-a7951730, I-8eb5420c (docs fetcher), I-0abb70ff, I-22cc42fc, I-5e2d0197, I-3ed36f37, I-684059ec (test-evidence plugin and requirements), I-1dc56c17 (user guide), I-91aabdcd (README), I-b26defe9 and I-157f6dee (glossary definitions), I-b1cbff3a (new part-registration uses check).
- Distribution: I-b2bdc1c2, I-1de97e8b, I-7417545a (new refusal code invalid_arguments), I-33a1c97a (new scenario.distribution.mcp-call-failed), I-031366c0, I-fde7a6ca (new req.distribution.protocol-manifest-precondition and scenario), I-d8b60e43, I-d31fff34, I-1100d67b.

Decisions I took (details in the decision log):
- I-ad4e6375 (preferred-fix): the suggested repair does not hold. Git 2.43 lists the separate Git directory itself as the primary worktree (reproduced). In that layout Git keeps no path for the primary worktree. The refusal now names the primary worktree when Git records it (`.git` parent or core.worktree), and otherwise names the Git directory and says so. req.dogfooding.refusal-names-reason restated to match.
- I-3ed36f37 (preferred-fix): restated req.concorde.test-counting (units count the tests that ran, beside `collected`) rather than inventing units with no times or outcome.
- I-22cc42fc: the Spec already excluded non-regular files and symlinks; I made explicit that a deleted listed path is no input. There is no code change.
- I-8eb5420c: a failed restoration keeps the backup and the refusal names it; the requirement explanation states this one exception.
- I-b1cbff3a: the new test found two gaps in other groups' Modules, which I fixed with small edits. module.workers gained a `uses` of module.distribution (and a short #uses-distribution paragraph). module.tasks' existing `uses` gained concept.part-registration and contract.distribution.part-registration. I also refreshed the registry mirror. This may conflict with fix-open-worker-harness or fix-open-coordination on merge.

Left open (suggestions, not cheap or clearly better):
- I-a3522268: the duplication is the stated design of the root requirements.
- I-efaedb06: moving the include grammar out of Distribution's entry is a restructuring for readability only.

Nothing escalated; nothing else is open.

## Closed: merged, 2026-10-04T02:33:59Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit e16bb4cbb7adc171389557a653e0b8484d7b0edf into main and closed it as merged. Nobody answers a report after that.
