# Decision log: worker-git-isolation

Goal: Make workers' no-Git guarantee hold everywhere: deny every Git administrative path of the repository through every tool, require every worktree workers run in to live under the primary worktree's .claude/worktrees, move the unbound checkout and test projects there

## Brief (main agent, 2026-10-01)

Resolves I-1006c65677e95160b734824fd2a5c570 (high, decision-needed: Harness does not establish
Workers' universal no-Git guarantee). Read it with
`python3 scripts/concorde.py issues show I-1006c65677e95160b734824fd2a5c570` first.

The developer's decisions (2026-10-01), all to be carried out:
1. Complete the deny rules: every Git administrative path of the repository a worker works in
   (the common Git directory of the primary repository with its `worktrees/` and `modules/`, the
   worktree's own `.git` file or directory, submodules' Git directories) is denied to the worker
   through every tool, on both backends (Claude Code deny rules and Bash sandbox; pi permission
   extension and sandbox), wherever the repository lies, inside or outside the user's home.
2. Every worktree a worker runs in must live under the primary worktree's `.claude/worktrees/`;
   a worker launch in any other placement is refused with a clear refusal naming the rule.
3. The unbound checkout moves from `/tmp/concorde-unbound-…/<run-id>` to
   `.claude/worktrees/unbound-<run-id>` of the origin's primary worktree, and is still removed
   before the result is written.
4. Test projects (end-to-end, SWE-bench cases, dogfood scenarios, scratch clones) are created as
   `.claude/worktrees/test-<name>` of the Concorde checkout and deleted when the test is done:
   the end-to-end tool's default root changes accordingly (today `/tmp/concorde-e2e`).
5. Add a scenario with a primary repository outside the user's home, and test it.

`.claude/worktrees/` is Git-ignored in this checkout; check what installed projects need for it.
The runtime directory of a worker run stays under `/tmp`: it is not a worktree.

Left to the task session (record each choice here): the exact path set denied and how each
backend expresses it, the refusal code for a wrong placement, how the unbound checkout's name
avoids clashing with task names, and the scenarios and tests. Do not change Tasks: restricting
`task open --path` to `.claude/worktrees/` is I-6adb5521ad3a5c55a39350c714193f22, a later task,
since task workflow-lock-before-records is changing module.tasks now. The root Module and
module.concorde's development.md may mention `/tmp` placements: escalate a change there or in
any other Module outside this task's.

## Task session decisions (2026-10-01/02)

- **Git administrative paths denied, and how.** Workers (new `src/concorde/harness/placement.py`,
  realization.workers.runtime) computes, after checking the placement: `git rev-parse
  --git-common-dir` and `--git-dir`; every `.git` entry found by walking the worktree (not entering
  `.git`, symbolic links or runtime paths); for each `.git` file the `gitdir:` target and its
  `commondir`. It hands these with the primary worktree to the Harness. Claude Code: `Read`/`Edit`
  deny rules on each path, plus the home rule ("deny every entry that does not lead to the
  worktree, the run's directories or a runtime path") now applied to the primary worktree too, so a
  primary outside the home is hidden like one inside it; sandbox `denyRead` adds the primary
  worktree and every Git path (a narrower denyRead wins inside a wider allowRead, so a nested
  `.git` in a granted directory stays hidden). pi: the policy gains `git` and `primary`; the read
  table denies Git paths first and the primary worktree like the home; the write hook and pi write
  table deny a `.git` segment at any depth (was: only the root `.git`). Reason: one generator for
  both backends; hiding the primary worktree outside home also fulfils the Harness's existing
  promise that "the primary worktree" is denied, which held only inside home.
- **Refusal code** `worktree_misplaced`, reason `environment` (Workers cannot move a worktree),
  raised before any settings/extension is generated; the run record is still written. The rule:
  the worktree must lie *directly* in `<primary>/.claude/worktrees/`, the primary being the first
  entry of `git worktree list --porcelain`; the primary worktree itself is refused too.
- **Unbound checkout name**: `.claude/worktrees/unbound-<run-id>`. A run id always contains an
  upper-case `T` (`r-YYYYMMDDTHHMMSS-…`), which Tasks' `TASK_ID` pattern `^[a-z0-9][a-z0-9-]{0,47}$`
  never admits, so it cannot clash with a task worktree. The runner refuses with
  `checkout_unavailable` when the primary worktree's Git does not ignore that path (as Tasks does
  with `worktree_not_ignored`) or the path is taken. It removes only the checkout directory, never
  `.claude/worktrees/`. A SIGKILLed runner now leaves the checkout behind (it was in /tmp); the
  runner Spec says `git worktree remove --force` removes it. `req.execution.unbound-origin-untouched`
  amended to allow the checkout in the primary worktree's `.claude/worktrees/` while the run lasts.
- **Installed projects**: the installer already adds `.claude/worktrees/` to `.gitignore`
  (`src/concorde/distribution/install.py` IGNORED), so nothing changes there.
- **Test projects**: the e2e default root is now this checkout's `.claude/worktrees/`, each project
  `test-<name>` (also under `CONCORDE_E2E_ROOT` when set); dogfood scenario directories likewise
  `test-<name>`; the dogfood evaluation's throwaway Concorde clone is
  `.claude/worktrees/test-intake-…`, removed afterwards. Not changed: `cases.py`'s grading tree
  (`concorde-grade-…` in /tmp, a worktree of the test project in which no worker runs), since
  module.swe-bench-cases is not this task's Module.
- **Tests**: the worker fixture `WorkerProject` gained `linked=True`, putting the worker's worktree
  at `<primary>/.claude/worktrees/w` (default stays the primary, which OperationProject, owned
  outside this task, uses for tasks). New scenarios `scenario.workers.misplaced-worktree-refused`,
  `scenario.workers.git-hidden-outside-home` (primary under /tmp, home elsewhere, nested `.git`
  in a rw directory pointing outside), `scenario.execution.unbound-not-ignored`; pi policy tests
  extended; a live Claude Code test of the same scenario added to `test_live.py`.

## Escalated to the main agent, 2026-10-01T16:12:29Z

- **task-session** task session (task worker-git-isolation): `test_projects_load_concorde_instructions`
  Decision 4 places test projects at .claude/worktrees/test-<name> of the Concorde checkout, which this task implemented (e2e default root, dogfood scenario directories, dogfood intake clone). But Claude Code loads every CLAUDE.md and CLAUDE.local.md of every directory above a session's working directory. I verified it: a `claude -p` session in a fresh git repository at <checkout>/.claude/worktrees/test-probe reported being given /home/zhenyu/concorde/CLAUDE.md (and the task worktree's CLAUDE.md). So every headless main session the end-to-end tool starts in a test project, and every task session the test project's own Concorde starts there, receives Concorde's own development instructions ("This is Concorde's own source checkout... load concorde-development", the Concorde glossary import), contaminating exactly the sessions the end-to-end and dogfood tests judge. Skills are not affected (searched only up to the repository root), and the test project likely inherits the checkout's Claude Code trust, so scenario.e2e.headless's "untrusted test project" can no longer be produced under the default root. The no-Git guarantee no longer depends on where a test project lies: a test project is its own primary worktree, its workers run in its own .claude/worktrees/, and the Harness now hides its Git paths inside or outside the home.
  Not handled here (decision): Where test projects live is the developer's decision 4 for this task, and the fixes reach module.headless-sessions and module.task-session, which are outside this task's Modules; the task delivers decision 4 as given.
  Options: A. Keep test projects in <checkout>/.claude/worktrees/test-<name>, and in a follow-up task have the end-to-end tool's headless sessions pass --settings with claudeMdExcludes for every CLAUDE.md/CLAUDE.local.md/.claude/rules above the test project; task sessions the test project's Concorde starts would still load them unless Task sessions also excluded instructions above the primary worktree, a user-facing change.; B. Keep test projects out of the checkout: default end-to-end root back outside any directory with a CLAUDE.md, e.g. /tmp/concorde-e2e/test-<name> (still test-<name>, still deleted when done); the Git guarantee holds there too after this task. A one-line change of DEFAULT_ROOT plus its Spec and scenario.; C. Accept that test-project sessions see Concorde's own CLAUDE.md.
  Recommendation: B: it keeps end-to-end and dogfood sessions identical to a user's, needs no change outside End-to-end testing, and loses nothing of the no-Git guarantee, which no longer depends on where a test project lies.

```json
{
  "level": "task-session",
  "actor": "task session (task worker-git-isolation)",
  "code": "test_projects_load_concorde_instructions",
  "detail": "Decision 4 places test projects at .claude/worktrees/test-<name> of the Concorde checkout, which this task implemented (e2e default root, dogfood scenario directories, dogfood intake clone). But Claude Code loads every CLAUDE.md and CLAUDE.local.md of every directory above a session's working directory. I verified it: a `claude -p` session in a fresh git repository at <checkout>/.claude/worktrees/test-probe reported being given /home/zhenyu/concorde/CLAUDE.md (and the task worktree's CLAUDE.md). So every headless main session the end-to-end tool starts in a test project, and every task session the test project's own Concorde starts there, receives Concorde's own development instructions (\"This is Concorde's own source checkout... load concorde-development\", the Concorde glossary import), contaminating exactly the sessions the end-to-end and dogfood tests judge. Skills are not affected (searched only up to the repository root), and the test project likely inherits the checkout's Claude Code trust, so scenario.e2e.headless's \"untrusted test project\" can no longer be produced under the default root. The no-Git guarantee no longer depends on where a test project lies: a test project is its own primary worktree, its workers run in its own .claude/worktrees/, and the Harness now hides its Git paths inside or outside the home.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Where test projects live is the developer's decision 4 for this task, and the fixes reach module.headless-sessions and module.task-session, which are outside this task's Modules; the task delivers decision 4 as given."
  },
  "options": [
    "A. Keep test projects in <checkout>/.claude/worktrees/test-<name>, and in a follow-up task have the end-to-end tool's headless sessions pass --settings with claudeMdExcludes for every CLAUDE.md/CLAUDE.local.md/.claude/rules above the test project; task sessions the test project's Concorde starts would still load them unless Task sessions also excluded instructions above the primary worktree, a user-facing change.",
    "B. Keep test projects out of the checkout: default end-to-end root back outside any directory with a CLAUDE.md, e.g. /tmp/concorde-e2e/test-<name> (still test-<name>, still deleted when done); the Git guarantee holds there too after this task. A one-line change of DEFAULT_ROOT plus its Spec and scenario.",
    "C. Accept that test-project sessions see Concorde's own CLAUDE.md."
  ],
  "recommendation": "B: it keeps end-to-end and dogfood sessions identical to a user's, needs no change outside End-to-end testing, and loses nothing of the no-Git guarantee, which no longer depends on where a test project lies.",
  "causes": []
}
```
- **Live tests** (CONCORDE_LIVE_CLAUDE=1, Haiku, a few cents): the new
  `test_a_real_worker_sees_no_git_metadata_outside_home` passed on the first run: a real Claude
  Code worker in `<primary under /tmp>/.claude/worktrees/w` read nothing of the primary's `.git`,
  its own `.git` file or the primary's sources through Read, Bash or Grep. The older
  `test_a_real_worker_is_fenced` failed (not `ok`): it still assumed `src/bmod/secret.py` is
  ungranted, but an `implement` grant now makes the project's whole code `ro`. Repaired within the
  task by probing the ungranted `checks/a_check.py` instead, and by judging every Grep result,
  since the model's first Grep call may be rejected for an extra parameter.
- **Full suite**: 891 passed; `test_pytest_timing::test_runner_fingerprints_and_default_cli` failed
  once under xdist and passes alone (unrelated to this task).
- **Live rerun**: `test_a_real_worker_is_fenced` and `test_a_real_worker_sees_no_git_metadata_outside_home`
  passed. `test_a_real_worker_reports_a_detailed_error` failed: the Haiku worker blocked correctly
  but gave the reason `input` where the test accepts `permission` or `scope`. It concerns a
  model's error classification, not this task's goal, so it is left as is and reported.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T16:35:46Z

Task worker-git-isolation delivered: delivery commit d3a45df44037488e9ed11cc37c5283728021b5bd (on top of 91ac0078 and facd0690). Resolves I-1006c65677e95160b734824fd2a5c570 (added with task resolve).

Done, per the developer's five decisions:
1. Git paths denied through every tool on both backends. Workers (new src/concorde/harness/placement.py) finds the common Git dir (worktrees/, modules/), the worktree's own Git dir, every .git entry in the worktree and the gitdir/commondir those .git files name, and hands them with the primary worktree to the Harness. Claude Code: Read/Edit deny rules on each path, the home rule now also applied to the primary worktree, sandbox denyRead of the primary and every Git path. pi: read table denies Git paths first and the primary like the home. The write hook and pi write table deny a .git segment at any depth.
2. A worker whose worktree is not directly in <primary>/.claude/worktrees/ is refused before anything is generated: code worktree_misplaced, reason environment. The primary worktree itself is refused too.
3. The unbound checkout is now .claude/worktrees/unbound-<run-id> of the primary worktree and is removed before the result. It is refused with checkout_unavailable if Git does not ignore that path or the path is taken.
4. The e2e default root is <checkout>/.claude/worktrees; test projects and dogfood scenario directories are test-<name>; the dogfood intake clone is test-intake-…, removed afterwards.
5. New scenarios scenario.workers.git-hidden-outside-home (primary under /tmp, home elsewhere, nested .git in a rw dir pointing outside) and scenario.workers.misplaced-worktree-refused, plus scenario.execution.unbound-not-ignored, all tested. pi policy tests extended. A new live Claude Code test (Haiku) passed: a real worker read nothing of the primary's .git, its .git file or the primary's sources.

Decisions taken (in the decision log): the path set and how each backend expresses it, as above. The refusal code is worktree_misplaced. The unbound name cannot clash with a task, because a run id always holds an upper-case T, which TASK_ID never admits. Hiding the whole primary worktree outside home also fulfils the Harness's existing promise that the primary worktree is denied. A SIGKILLed runner now leaves its checkout behind; the Spec says git worktree remove --force removes it. req.execution.unbound-origin-untouched was amended for the checkout in .claude/worktrees/. Installed projects need nothing: the installer already ignores .claude/worktrees/. The test fixture WorkerProject gained linked=True; OperationProject, outside this task, is unchanged. Not changed: cases.py's grading tree in /tmp (module.swe-bench-cases, no worker runs there).

Non-ok results: the full suite had 891 passed and 1 failure, test_pytest_timing fingerprints, which failed under xdist and passes alone. Live test_a_real_worker_is_fenced was stale (an implement grant now makes src/bmod readable); I repaired it and it now passes. Live test_a_real_worker_reports_a_detailed_error still fails: the model gave reason `input` instead of permission/scope. It is unrelated and left as is.

Open — escalation 1 (decision): test projects under the checkout load Concorde's own CLAUDE.md. Claude Code loads every ancestor CLAUDE.md, and I verified this with a claude -p probe in <checkout>/.claude/worktrees/test-probe. So the test projects' main and task sessions get Concorde's development instructions, and they likely inherit the checkout's trust. Options:
A. Keep the placement and add claudeMdExcludes in headless sessions, plus possibly in Task sessions.
B. Default root outside the checkout, e.g. /tmp/concorde-e2e/test-<name>.
C. Accept it.
I recommend B. The Git guarantee no longer depends on where a test project lies.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-01T16:49:21Z

Escalation 1 (test_projects_load_concorde_instructions): option B, decided by the developer (2026-10-02) after the main agent checked the history: no run ever failed in a sandbox because a test project lay under /tmp; the remembered problems were I-1006c656 itself (fixed by this task) and the old task-session OS sandbox making /tmp read-only (dropped 2026-10-01). So: the end-to-end default root goes back to concorde-e2e in the system temporary directory, test projects are <root>/test-<name> and are deleted when the test is done; the dogfood intake clone likewise lives outside the checkout. Also resolve I-3d6fc05a0b8f538a8a41962bb90fa9e8 (added to this task's resolves), decided by the main agent: drop the outside-home promise of the default root (the system temporary directory is used wherever it lies, no fallback), and instead refuse a root, default or CONCORDE_E2E_ROOT, that lies inside the Concorde checkout, since Claude Code would load the checkout's CLAUDE.md into the test project's sessions; state it in module.e2e with a scenario and test. Everything else of the delivery is accepted. The two non-ok tests: record each as an Issue (test_pytest_timing flaky under xdist; live test_a_real_worker_reports_a_detailed_error, model gives reason input) if no open Issue covers it. Then run task-validation and delivery again and report.

## Task session, after answer 1 (2026-10-02)

- Carried out option B: the e2e default root is `concorde-e2e` in the system temporary directory
  again (no outside-home promise, no fallback), test projects and dogfood scenario directories
  stay `<root>/test-<name>`, the dogfood intake clone is back in a plain temporary directory.
- I-3d6fc05a0b8f538a8a41962bb90fa9e8: `e2e_root()` refuses a root whose real path is the checkout
  or inside it with `root_inside_checkout`, naming the root, its source (CONCORDE_E2E_ROOT or the
  default) and the CLAUDE.md reason; `prepare` and `dogfood prepare` resolve the root first, so
  nothing is cloned. Stated as req.e2e.root-outside-checkout and scenario.e2e.root-inside-checkout,
  tested in test_e2e.py; scenario.e2e.default-root lost its outside-home clause.
- Non-ok tests recorded as Issues (no open Issue covered them): I-7c0cd43a20d6500bb52a23c54400432c
  (pytest-timing fingerprint test flaky under xdist, module.concorde, low) and
  I-46edf1ef313b5b3192e91744fba572b9 (live detailed-error test: the worker gives reason `input`,
  module.workers, low), both decision-needed since their cause is not established.

## Report 2 to the main agent (spec-review quality criteria), 2026-10-01T17:05:23Z

Task worker-git-isolation delivered again: delivery commit 9dcc75adfb982702f4e11367b9d7c602c89d00fa (on top of 1c1c8d85). It resolves I-1006c65677e95160b734824fd2a5c570 and I-3d6fc05a0b8f538a8a41962bb90fa9e8.

Answer 1 carried out:
- Option B. The end-to-end default root is concorde-e2e in the system temporary directory again, wherever that lies, with no outside-home promise and no fallback. Test projects and dogfood scenario directories are <root>/test-<name>. The dogfood intake clone is back in a plain temporary directory.
- I-3d6fc05a. e2e_root() refuses a root whose real path is the Concorde checkout or lies inside it, whether it is the default or CONCORDE_E2E_ROOT. The code is root_inside_checkout; the message names the root, its source and the CLAUDE.md reason. prepare and dogfood prepare resolve the root first, so nothing is cloned. Stated as req.e2e.root-outside-checkout and scenario.e2e.root-inside-checkout, tested in test_e2e.py. scenario.e2e.default-root no longer promises outside-home.
- The two non-ok tests are recorded as Issues, since no open Issue covered them. Both are decision-needed and low, because their cause is not established:
  - I-7c0cd43a20d6500bb52a23c54400432c, owned by module.concorde: the pytest-timing fingerprint test is flaky under xdist.
  - I-46edf1ef313b5b3192e91744fba572b9, owned by module.workers: in the live detailed-error test the worker gives reason input.

Verification: full suite 893 passed, 5 skipped. build --check and spec-validation pass. task-validation reports ready with no findings.

Nothing open. Everything is in the decision log.

## Closed: merged, 2026-10-02T02:16:03Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 9dcc75adfb982702f4e11367b9d7c602c89d00fa into main and closed it as merged. Nobody answers a report after that.
