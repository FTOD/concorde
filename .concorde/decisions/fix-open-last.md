# Decision log: fix-open-last

Goal: Close the last open Issues: deny pi's Bash reads of names paths below readable directories, and settle the two remaining Spec suggestions

## Brief (main agent, 2026-10-04)

The developer asked (2026-10-04) to try to resolve the project's open Issues; ten fix tasks
(fix-open-*) have merged and closed 272. Three remain; this task settles them.

- **I-babfa1cb (module.harness, obvious-fix)**: on pi, Bash can read a `names` path listed below a
  readable directory, because Claude Code adds its Read deny rules to the sandbox's denyRead while
  pi receives only the shared sandbox lists. Put those entries into the shared denyRead (as
  fix-open-trace-producers did for denyWrite with `ro`/`names` entries below `rw` directories), with
  tests on both backends; then `task resolve`.
- **I-efaedb06 (module.distribution, suggestion)**: the build renderer's include grammar and uv
  invocations sit in Distribution's Module entry. Move them to a topic document of Distribution (or
  its contracts) if that clearly makes the entry easier to read without losing any promise; then
  `task resolve`. If you judge it does not, close it `not-actionable` with the reason.
- **I-a3522268 (module.concorde, suggestion)**: the root's requirements restate grant provenance,
  Git isolation and claim separation of its children. The root's requirements document says it
  promises what the Modules achieve together. If the restatements are that by design, close it
  `not-actionable` citing that; if some of them duplicate a child's obligation without adding the
  framework-wide promise, trim those and `task resolve`.

Rules as before: every part still works installed with only its dependencies, the part-dependency
and guidance checks pass, no shims. Verify with `build --check`, `spec-validation`, the full suite,
then `task-validation` and `delivery`, and report.

## Task session (2026-10-04)

- **I-babfa1cb (harness)**: added `GrantView.names_below_readable()` and put its paths into the
  shared `denyRead` of `sandbox_filesystem`, mirroring `held_below_rw()` for `denyWrite`. Probed
  with the real sandbox-runtime 0.0.77 + bwrap on the generated lists: a `names` file below a `ro`
  directory reads "Permission denied", a `names` directory below it is empty, a `ro` file listed
  below that `names` directory stays readable, other files of the `ro` directory stay readable.
  Tests: `test_workers.py` (shared lists and Claude Code settings) and `test_pi.py` (pi policy),
  both failing before the fix. Harness Specs (module.md table and known limits, pi.md,
  claude-code.md) updated. Tests tag the existing Workers scenarios `bash-confined` and
  `pi-commands-sandboxed` (a names file is ungranted for reading); no scenario changed, since
  Workers' scenarios are outside this task's Modules.
- **I-efaedb06 (distribution)**: judged the move clearly helps: the entry's build-renderer paragraph
  stated five precise refusal rules in its design section that no requirement held. Moved them to
  new requirements `req.distribution.prompt-includes`, `safe-includes`, `include-audience`,
  `include-once` and `locked-python-dependencies` (the uv export / `--require-hashes` step); the
  entry keeps the reasons and links them. While moving, corrected the audience rule to what
  `prompt_resolver._check_audience` enforces (an included prompt is `shared` or of the root's own
  audience; the old text said "worker or shared", wrong for a `shared` root). No promise dropped.
  `task resolve` added it.
- **I-a3522268 (concorde root)**: compared each pair. All three root statements had the same actor
  and scope as the child's (grant: "every grant Method computes" = Method's step; Git: "a worker"
  = Workers; claims: "every run result" = Execution's runner and steps), so none added a promise
  about how the parts work together; the "what the Modules achieve together" intro does not cover
  a plain restatement. Trimmed all three to explanations at the head of the Boundaries and Results
  sections linking req.method.workspace-specs, req.workers.no-git and req.execution.claims-apart,
  keeping the account of where Git belongs. Nothing referenced the removed identities (grep over
  specs, src, tests, prompts, docs). `task resolve` added it.

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T04:09:19Z

fix-open-last delivered: delivery commit 1b40749a701588614afd448624962594c6937609 on concorde/fix-open-last (task-validation ready, full suite 1250 passed / 5 skipped, build --check and spec-validation clean). The task resolves all three Issues (task resolve done; the merge closes them).

1. I-babfa1cb (harness, obvious-fix), commit b0035bd8: sandbox_filesystem now also puts every names entry strictly below a ro or rw directory entry into the shared denyRead (new GrantView.names_below_readable, the counterpart of held_below_rw). Probed with the real sandbox-runtime 0.0.77 + bwrap on the generated lists: a names file below a ro directory gives Permission denied, a names directory below it shows empty, and a ro file listed below that names directory plus the rest of the ro directory stay readable. New tests in test_workers.py (shared lists and Claude Code settings) and test_pi.py (pi policy) both fail without the fix. Harness Specs updated (module.md table and known limits, pi.md, claude-code.md).

2. I-efaedb06 (distribution, suggestion), commit c03922a5: I judged the move clearly helps. The entry's build-renderer paragraph held five refusal rules that no requirement stated. They are now the requirements req.distribution.prompt-includes, safe-includes, include-audience and include-once, plus locked-python-dependencies for the uv export / --require-hashes step. The entry keeps the design reasons and links to them. While moving it I corrected the audience rule to what prompt_resolver enforces: an included prompt is shared or has the root's own audience. The old text said "worker or shared", which was wrong for a shared root.

3. I-a3522268 (root, suggestion), commit b36687ff: all three root requirements had the same actor and scope as their child's requirement and added no promise about how the parts work together. I trimmed req.concorde.grant-from-task-worktree, workers-no-git and claims-apart into explanations at the head of the Boundaries and Results sections, linking req.method.workspace-specs, req.workers.no-git and req.execution.claims-apart. The account of where Git belongs is kept. Nothing referenced the removed identities.

Decisions taken without the developer: the three judgements above, recorded in the decision log. Nothing is open and nothing is escalated.

## Closed: merged, 2026-10-04T04:09:34Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 1b40749a701588614afd448624962594c6937609 into main and closed it as merged. Nobody answers a report after that.
