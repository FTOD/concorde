# Decision log: coordination-high

Goal: Fix the high Issues of Tasks and Task sessions (close stops work before refusing another part's merge marker; a report can message the former main after a concurrent rebind; path normalization before symlink resolution can let a task session write outside its task) and their other obvious-fix Issues

## Task brief (main agent, 2026-10-29)

**Origin.** Project review r-20261029T060905-project_review-fa4731e2 (unbound, commit 8a5ed4245, verdict changes_required) left 2 critical and 10 high Issues open. The developer chose to fix every critical and high Issue first, in five parallel tasks split by Module, each also fixing the obvious-fix Issues of its own Modules. Read the review's findings for your Modules in `.concorde/unbound/r-20261029T060905-project_review-fa4731e2/result.json` (`output.modules[]`, the panel and code_review reviews) when an Issue's text is not enough.

**Issues this task resolves (18, all in the task's resolves):**

- I-722fd94f5b065dadab5701d853bef71a (module.task-session, high, obvious-fix): Path normalization before symlink resolution can allow writes outside the task
- I-05c59634329b5d96a6f485958b3073a1 (module.tasks, high, preferred-fix): A close stops task work before refusing another part's merge marker
- I-809baaaa00f85cddb1bab1de42e90cca (module.tasks, high, preferred-fix): A report can message the former main after a concurrent rebind
- I-04048733368c5ec893f32601c614b5eb (module.task-session, medium, obvious-fix): Place session stopping after close preflight refusals
- I-752373287b155273acb241cfcc7e1083 (module.task-session, medium, obvious-fix): The task-session start guard counts a stopped Claude Code session as still working
- I-e4a54ecb42e554af9d41cffadba2bc35 (module.task-session, medium, obvious-fix): Id-less assistant records can be incorrectly deduplicated
- I-0340037e84825d8dab3cd4b3855c6cb4 (module.tasks, medium, obvious-fix): Close summaries do not give one complete and consistent sequence
- I-295472aa08145cf091137cbfb869b35a (module.tasks, medium, obvious-fix): Following a session must not prohibit persisting its report
- I-42a3ef087b5251da9f8ac8738fb93421 (module.tasks, medium, obvious-fix): Historical task listings include a later task's lobby runs
- I-552113249f8954b69632a2d38140235d (module.tasks, medium, obvious-fix): Session following succeeds even when its transcript is missing
- I-5719977f9e065e749c3b02f22a7a14df (module.tasks, medium, obvious-fix): Separate independent persistence, cleanup and reporting obligations
- I-74451844b2c6597893465ca24fb7a7bb (module.tasks, medium, obvious-fix): Acceptance scenarios mix incompatible fixtures
- I-7e410ce761805ab0bfe3f901167035f1 (module.tasks, medium, obvious-fix): Environmental refusals default to input errors
- I-afdb22e6a2f85564b7d5a504dfd072e9 (module.tasks, medium, obvious-fix): Record locations confuse stored closure with completed archival
- I-c03affb2b6775b58934fe7cc986cf058 (module.tasks, medium, obvious-fix): The merged-close verification condition has two normative definitions
- I-e247ec3cbc2a56338937ca79bc59a481 (module.tasks, medium, obvious-fix): The common command-output promise contradicts main-hook
- I-76ae103bc5845d948eae537ec2e6c704 (module.task-session, low, obvious-fix): Give start serialization its own requirement
- I-b00a2241c1fb5766bc8e4ccd8546acf0 (module.task-session, low, obvious-fix): Separate the three MCP settings obligations

**How to handle them (the main agent's decisions).**
- Critical and high first. Show each with a test that fails on the old code.
- Fix obvious-fix Issues directly. For a preferred-fix Issue, take the clearly better fix and report it. None of these Issues is decision-needed. If one turns out to need a decision beyond your Modules or beyond the Issue's evident intent, escalate it rather than guess.
- An Issue that turns out to be already fixed, not a real problem, or a duplicate of another open Issue: say so with your evidence in your report. Do not close it yourself. The main agent closes it, or the merge closes it as resolved.
- Leave the other open Issues of your Modules (preferred-fix and decision-needed medium or low) alone, unless a fix here resolves one as a side effect: then name it in your report.
- Add or change Specs first where a fix changes a promise. Keep within your Modules. Escalate a change any other Module would have to make.

**Parallel tasks.** Four other tasks run at the same time. Do not touch their Modules:
- swe-cases-critical: module.swe-bench-cases
- worker-harness-high: module.harness, module.workers
- checks-execution-high: module.checks, module.execution
- specmcp-workflows-high: module.spec-mcp, module.workflows

**Specific to this task.** I-722fd94f is a hole in the session boundary, so treat it as security. Fix it so that a symlink can never lead a write outside the task worktree and decision log, and test it with real symlinks. I-809baaaa touches the rebind and report path that task main-bg-rename just changed (merged 146eaf554, `src/concorde/coordination/tasks/moves.py`). Read that change and its decision log `.concorde/decisions/main-bg-rename.md` first, and keep its behaviour.

**Verification.** Run Concorde's full suite, `build --check` and `spec-validation`. Then run `task-validation` and `delivery` from the task worktree, and report.

**Environment notes.**
- uv, node/npm (Node 24, npm 11), pi, rg, fd and d2 are under `/home/scratch.zbai_gpu/opt`.
- The system bubblewrap is 0.4.0 and works.
- Every worker runs on pi: claude-opus-5-5 and gpt-6.1-sol.
- Keep large files off `$HOME` (5 GB quota).

**Left to the session.** The mechanisms, internal structure, test design and Spec wording.

## Task session: decisions on the high Issues (2026-10-29)

- **I-722fd94f (session hook, symlink).** The hook now resolves the joined path directly with
  `realpath`, as the operating system walks it (each link before the `..` after it), and also
  judges the reading with `..` collapsed first, allowing the path only when both readings are
  allowed. Reason: whether Claude Code's Edit/Write normalize `..` before writing is undocumented
  (Node's `path.resolve` would collapse it), so judging both readings holds whichever file the
  tool writes; the two readings differ only for a path holding `..`. Test with real symlinks
  (`deep -> <primary>/src/a`, `deep/../a/calc.py`) fails on the old code. Commit 7c1d… see branch.
- **I-05c59634 (preferred-fix).** Chosen fix: the close's preflight, before it stops anything,
  also runs `refuse_foreign_marker` while no live process holds the merge lock, the same
  condition as the existing preflight for another task's unfinished merge; the authoritative
  check under the merge lock stays. Reason: a merge whose process still runs removes its own
  marker when it ends, so it is waited for as Tasks' own merges are; refusing it outright would
  refuse a close that would succeed after the wait. Test with a working session and a foreign
  (then unreadable) marker asserts Claude Code was never asked to stop anything; it fails on the
  old code. I-04048733 (Task sessions' lifecycle table) fixed with it.
- **I-809baaaa (preferred-fix).** Chosen fix: discard the followed answer when the record's
  `main` or `main_session` changed between the record followed and the record the report is
  appended to, rather than following again under the lock. Reason: following asks Claude Code
  (up to 20 s) and must stay outside the task's lock; a rebind meanwhile is the main agent's own,
  newer word on its session. New requirement `req.tasks.report-followed-current`. The
  main-bg-rename behaviour (follow before the lock, record unchanged, decision log names both) is
  kept. Test: a rebind inside `follow` sends the report to the new main; fails on the old code.
- **I-55211324.** `moves.follow` now returns nothing without the transcript of the record's
  `main_session`; the rename test now keeps a plain transcript, and a missing one prints the
  record's `main`.
- **I-295472aa.** `req.tasks.report-followed-shown` and the module entry now keep only the
  record's `main`, `main_session` and `mains` unchanged and state that the report is appended.

Correction to the entry above: the commits are 44503d4d0 (I-722fd94f), 6df7fcad5 (I-05c59634,
I-04048733) and 40dbe0acc (I-809baaaa, I-55211324, I-295472aa); "7c1d…" was a slip.

## Task session: decisions on the other obvious-fix Issues (2026-10-29)

- **I-75237328.** A session Claude Code lists as `stopped` now counts as replaceable, like `done`
  and `failed` (`session.REPLACEABLE`, kept apart from `STATES`, which maps a state to a node
  status and is unchanged). `blocked` still refuses: such a session waits for someone to answer it
  and works on once answered. The refusal names `claude stop <id>`, the state `stopped` it leads to
  and the states that refuse no start. Commit 7aad7be78.
- **I-e4a54ecb.** Message keys are tagged tuples: `("message", id)` for an API message and
  `("record", <full transcript path>, <record index>)` for a record without an id, so id-less
  records never collide with each other or with message ids. Test fails on the old code (24/4
  instead of 25/5). Commit 7aad7be78.
- **I-76ae103b, I-b00a2241.** New `req.task-session.starts-serialized`, and
  `req.task-session.mcp-approval` split into `mcp-replaced`, `mcp-approval` (kept for the approved
  servers, so existing links stay meaningful) and `mcp-unapproved`. Commit 7aad7be78.
- **I-42a3ef08.** `store.workspace_runs` reads the lobby only for the task's current folder; a
  folder in the history lists its own runs alone (`runs.folders(..., lobby=False)`). Test with a
  live lobby run of a reused name fails on the old code. Commit 76b673958.
- **I-7e410ce7.** `specs_unloadable` and `session_stop_failed` are `environment` in the contract
  list and in `cli.HANDLING` (both defaulted to `input` in the code too). Tests check the reason.
- **I-0340037e.** The contracts' close order is now a numbered list of all nine steps as the code
  runs them (worktree removal, record update, closing appended, trace node ended, log committed,
  transcripts kept, merge attempt ended, folder moved, sessions removed), anchored
  `#close-order`; the module's summary follows that order and links it.
- **I-5719977f.** Split: `report-answered` / new `answer-logged`; `merge-attempt-lock` / new
  `merge-attempt-lock-removed`; `merge-closes-resolved` / new `merge-close-failures-warn`;
  `main-hook-never-fails` / new `main-hook-failure-named`. The original identities keep their
  first duty, so references from main-session's requirements stay right.
- **I-74451844.** `scenario.tasks.deliver-refused` keeps the Method case; six new scenarios
  (`deliver-not-task-worktree`, `deliver-workspace-busy`, `deliver-wrong-branch`,
  `deliver-switched-while-waiting`, `deliver-check-switches-branch`,
  `deliver-retired-while-waiting`). `merge-resume-refused` keeps the head cases; new
  `merge-resume-not-merging` and `merge-resume-checks`. The existing tests verify them; no
  outcome changed.
- **I-afdb22e6, I-c03affb2, I-e247ec3c.** Locations by current or archived folder with the late
  close refusal stated; merged-close preconditions refer to `req.tasks.delivery-verified`; the
  common JSON and refusal rules exclude `main-hook`. Commit 8bb832323.

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T09:21:46Z

coordination-high delivered: delivery commit 599e887b5 (run r-20261029T091229-delivery-7a94e6a5, ok). task-validation r-20261029T090242-task_validation-1e93c09a was ready with nothing blocking. Full suite: 1665 passed, 6 skipped. build --check passed. spec-validation passed, with 5 warnings, all in other Modules' Specs.

All 18 Issues in the task's resolves are fixed. None turned out already fixed, unreal or a duplicate. None needed escalation.

High (each with a test that fails on the old code):
- I-722fd94f (security, session hook). The hook now resolves the joined path directly with realpath, as the operating system walks it. A `..` after a link therefore leaves the link's target directory. The hook also judges the path read with `..` collapsed first, and allows it only when both readings are allowed. Reason: it is undocumented whether Claude Code's Edit/Write collapse `..` before writing, so the hook holds whichever file the tool writes. Tested with real symlinks: `deep -> <primary>/src/a`, `deep/../a/calc.py` and a link to the task folder. Commit 44503d4d0.
- I-05c59634 (preferred-fix). Chosen fix: the close's preflight, before it stops anything, now also refuses a foreign or unreadable marker while no live process holds the merge lock. That is the same condition as the existing preflight for another task's unfinished merge. The check under the merge lock stays. Reason: a merge still running removes its own marker when it ends, so it is waited for instead. Test: a working session plus a foreign, then an unreadable, marker; Claude Code is never asked to stop anything. I-04048733 (Task sessions' lifecycle table) is fixed with it. Commit 6df7fcad5.
- I-809baaaa (preferred-fix). Chosen fix: drop the followed answer when the record's main or main_session changed between the record followed and the record the report is appended to. The alternative was to follow again under the lock. Reason: following asks Claude Code (up to 20 s) and must stay outside the task lock. A rebind meanwhile is the main agent's own newer word. New requirement req.tasks.report-followed-current. main-bg-rename's behaviour is kept: follow before the lock, record unchanged, decision log names both. I-55211324 (follow only with the transcript of main_session) and I-295472aa (report-followed-shown keeps only main, main_session and mains unchanged) are fixed with it. Commit 40dbe0acc.

Medium and low obvious-fix:
- I-75237328: a `stopped` session no longer refuses a start; `blocked` still does. The refusal names `claude stop <id>`, the state `stopped` and the states that refuse no start.
- I-e4a54ecb: id-less assistant records are keyed by transcript path and position, apart from message ids.
- I-76ae103b: new req.task-session.starts-serialized.
- I-b00a2241: mcp-approval is split into mcp-replaced, mcp-approval and mcp-unapproved.
- These four are in commit 7aad7be78.
- I-42a3ef08: a task in the history lists no lobby run; only the current task of a name reads the lobby. Commit 76b673958.
- I-7e410ce7: specs_unloadable and session_stop_failed are environment refusals, in the contract and in cli.HANDLING; the code also defaulted them to input.
- I-0340037e: one numbered nine-step close order, contracts.md#close-order, which the module summary follows.
- I-5719977f: four combined requirements split, with new ids answer-logged, merge-attempt-lock-removed, merge-close-failures-warn and main-hook-failure-named. The original ids keep their first duty, so main-session's links stay right.
- I-74451844: deliver-refused split into 7 scenarios and merge-resume-refused into 3. The existing tests verify them.
- I-afdb22e6: record locations by current or archived folder. I-c03affb2: merge-verified refers to delivery-verified. I-e247ec3c: main-hook is excluded from the common JSON and refusal rules.
- These are in commit 8bb832323.

Every decision is in the decision log. Nothing is open. I touched no other task's Modules, and no other open Issue of my Modules was resolved as a side effect.

## Closed: merged, 2026-10-29T09:22:15Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 599e887b5485d18278367a1dbadd9be25ee192fd into main and closed it as merged. Nobody answers a report after that.
