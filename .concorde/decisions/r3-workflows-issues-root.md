# Decision log: r3-workflows-issues-root

Goal: Fix the remaining open Issues of Workflows, Issues and the root Module (medium and low) found by the complete project_review

## Task brief (main agent, 2026-10-13)

Round 3. Rounds 1 and 2 fixed every critical and high Issue. The developer decided (2026-10-13)
that the main agent now resolves everything it can settle itself: this task resolves **every open
Issue owned by its Modules** (30, listed in `resolves`; 10 of them decision-needed), all medium or
low, found by project_review r-20261008T063808-project_review-9851e69f or reported since. Read each
with `concorde issues show`.

By tier:
- **decision-needed**: read them all first and escalate them **together in one report, early**,
  each with what you found, the options and your recommendation (say which options change a
  promise users rely on or an earlier developer decision). The main agent settles those within its
  authority and takes the rest to the developer in one batch. Continue with the rest meanwhile.
  An Issue the developer is asked about may stay open: you may deliver without it; the main agent
  reopens it after the merge if needed.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- **suggestion**: apply unless it is wrong or costs more than it is worth; then say why in the
  log and your report, and the main agent closes it as not-actionable.
- An Issue that no longer holds (many Modules changed in rounds 1-2), is a duplicate or is already
  fixed: say so with evidence; it stays in `resolves` and the merge closes it.
- Medium first, then low. A fix needing a change outside the task's Modules: escalate, unless it is
  a small mechanical follow-on (a link, a fixture, a registry refresh).

Eleven other round-3 tasks (r3-*) run in parallel on other Modules. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Escalated to the main agent, 2026-10-13T11:37:09Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_canonical_json`
  I-037a6f83a1b15934b18fe0a102d04ec2 (module.issues, medium): Issues' 'canonical JSON' (interface.md Report, line 25) says only 'keys sorted, no whitespace' and links Kernel typed values, which define no byte rule. Found: the store uses Kernel schema.canonical = json.dumps(sort_keys=True, separators=(',',':'), allow_nan=False) with Python's default ensure_ascii, so every non-ASCII character is written as a lowercase \uXXXX escape (UTF-16 surrogate pairs above U+FFFF) and the text is pure ASCII; identities (UUIDv5 of [invocation_id, report_key]), report ids and the 64 KiB limit all use it.
  Not handled here (decision): Choosing the canonical bytes of durable identities fixes a durable-format promise; the Issue is tiered decision-needed.
  Options: A: state the bytes the store already uses in Issues' own interface (sorted keys, ',' and ':' separators, no NaN/Infinity, non-ASCII and control characters as \uXXXX escapes, ASCII bytes), with a non-ASCII test vector; no existing identity changes; B: define canonical JSON bytes once in the Kernel's typed-values contract and link it (Kernel belongs to the parallel r3-kernel-tracing task); C: switch to UTF-8 literal non-ASCII (changes identities/digests of existing records with non-ASCII report keys)
  Recommendation: A: it documents what every existing record already used, changes no promise users rely on, stays in module.issues; B can follow later in a Kernel task.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_canonical_json",
  "detail": "I-037a6f83a1b15934b18fe0a102d04ec2 (module.issues, medium): Issues' 'canonical JSON' (interface.md Report, line 25) says only 'keys sorted, no whitespace' and links Kernel typed values, which define no byte rule. Found: the store uses Kernel schema.canonical = json.dumps(sort_keys=True, separators=(',',':'), allow_nan=False) with Python's default ensure_ascii, so every non-ASCII character is written as a lowercase \\uXXXX escape (UTF-16 surrogate pairs above U+FFFF) and the text is pure ASCII; identities (UUIDv5 of [invocation_id, report_key]), report ids and the 64 KiB limit all use it.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing the canonical bytes of durable identities fixes a durable-format promise; the Issue is tiered decision-needed."
  },
  "options": [
    "A: state the bytes the store already uses in Issues' own interface (sorted keys, ',' and ':' separators, no NaN/Infinity, non-ASCII and control characters as \\uXXXX escapes, ASCII bytes), with a non-ASCII test vector; no existing identity changes",
    "B: define canonical JSON bytes once in the Kernel's typed-values contract and link it (Kernel belongs to the parallel r3-kernel-tracing task)",
    "C: switch to UTF-8 literal non-ASCII (changes identities/digests of existing records with non-ASCII report keys)"
  ],
  "recommendation": "A: it documents what every existing record already used, changes no promise users rely on, stays in module.issues; B can follow later in a Kernel task.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:37:10Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_answers_digest_bytes`
  I-5215f7a570825262a633f8ea392dcb5e (module.workflows, medium): req.workflows.answers-new-key hashes 'the answers list in canonical JSON' (sorted keys, no whitespace) without fixing escaping or encoding. Found: step.answers_digest uses json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False) encoded as UTF-8, i.e. non-ASCII characters literal, unlike the Kernel/Issues canonical form which escapes them.
  Not handled here (decision): Fixing the bytes behind step keys is a compatibility choice; the Issue is tiered decision-needed.
  Options: A: state the bytes the code already hashes (sorted keys, ',' and ':' separators, non-ASCII literal, only JSON's mandatory escapes, UTF-8) with a non-ASCII example digest; no step key changes; B: switch to the Kernel/Issues escaped-ASCII canonical form (changes the step key of every answered step with non-ASCII answers, so such steps of workflows in progress would rerun)
  Recommendation: A: no recorded step key changes and it stays within module.workflows.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_answers_digest_bytes",
  "detail": "I-5215f7a570825262a633f8ea392dcb5e (module.workflows, medium): req.workflows.answers-new-key hashes 'the answers list in canonical JSON' (sorted keys, no whitespace) without fixing escaping or encoding. Found: step.answers_digest uses json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False) encoded as UTF-8, i.e. non-ASCII characters literal, unlike the Kernel/Issues canonical form which escapes them.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Fixing the bytes behind step keys is a compatibility choice; the Issue is tiered decision-needed."
  },
  "options": [
    "A: state the bytes the code already hashes (sorted keys, ',' and ':' separators, non-ASCII literal, only JSON's mandatory escapes, UTF-8) with a non-ASCII example digest; no step key changes",
    "B: switch to the Kernel/Issues escaped-ASCII canonical form (changes the step key of every answered step with non-ASCII answers, so such steps of workflows in progress would rerun)"
  ],
  "recommendation": "A: no recorded step key changes and it stays within module.workflows.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:37:10Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_refresh_rollback_limit`
  I-205b34410cb150bca924930bb4bfc52e (module.concorde, medium): req.concorde.docs-refresh-whole promises the snapshot unchanged on failure and its explanation says temporary directories are removed either way, yet the same explanation admits that when both the swap and moving the previous snapshot back fail the directory is left changed and the previous snapshot is kept; scenario docs-refresh-failed-unchanged promises unchanged and no leftover. Found: scripts/development/fetch-claude-code-docs.py publish() does exactly the admitted exception (RestoreError, keeps the .old snapshot and names it).
  Not handled here (decision): The Issue is tiered decision-needed: reconciling it chooses the promised limit of restoration.
  Options: A: admit the double failure as the one exception in the requirement, qualify the cleanup sentence and the ordinary failure scenario, add a scenario for the retained previous snapshot and its named location (matches the code); B: promise unconditional restoration and change the script (not achievable when the filesystem refuses both renames)
  Recommendation: A: it matches the code and only a development script in this checkout relies on it.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_refresh_rollback_limit",
  "detail": "I-205b34410cb150bca924930bb4bfc52e (module.concorde, medium): req.concorde.docs-refresh-whole promises the snapshot unchanged on failure and its explanation says temporary directories are removed either way, yet the same explanation admits that when both the swap and moving the previous snapshot back fail the directory is left changed and the previous snapshot is kept; scenario docs-refresh-failed-unchanged promises unchanged and no leftover. Found: scripts/development/fetch-claude-code-docs.py publish() does exactly the admitted exception (RestoreError, keeps the .old snapshot and names it).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The Issue is tiered decision-needed: reconciling it chooses the promised limit of restoration."
  },
  "options": [
    "A: admit the double failure as the one exception in the requirement, qualify the cleanup sentence and the ordinary failure scenario, add a scenario for the retained previous snapshot and its named location (matches the code)",
    "B: promise unconditional restoration and change the script (not achievable when the filesystem refuses both renames)"
  ],
  "recommendation": "A: it matches the code and only a development script in this checkout relies on it.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:37:43Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_report_failure_result`
  I-206d6719d2c25757b85c92712f9cc464 (module.workflows, medium): contracts.md 'The script's result' says every path returns what report() resolved to, with reported = {status, summary} of the saved workflow result. Found: the adapter (src/concorde/workflows/scripts/claude.js report()) relays 'concorde workflow report' through a haiku agent whose schema requires status and summary; when the report command refuses with {"error": <link>} (report_failed, workspace_retired, ...) there is no saved result and no admitted shape, so the relay must invent fields and the refusal and any rejected step outcome can be lost.
  Not handled here (decision): The missing observable result of a failure path must be chosen; the Issue is tiered decision-needed.
  Options: A: let the report relay return either {status, summary} or {error: <link>} unchanged; the script's result then carries reported = {status, summary} or report_refused = <link> (no saved result), keeps relayed and rejected beside it, and a relay that brings neither is reported as report_refused with a component link naming the missing answer; contract, adapter and a build-render test change (additive shape); B: make the procedure throw when report refuses, so Claude Code shows a workflow error (loses the rejected step outcome)
  Recommendation: A: additive, keeps every chain in sight, all within module.workflows.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_report_failure_result",
  "detail": "I-206d6719d2c25757b85c92712f9cc464 (module.workflows, medium): contracts.md 'The script's result' says every path returns what report() resolved to, with reported = {status, summary} of the saved workflow result. Found: the adapter (src/concorde/workflows/scripts/claude.js report()) relays 'concorde workflow report' through a haiku agent whose schema requires status and summary; when the report command refuses with {\"error\": <link>} (report_failed, workspace_retired, ...) there is no saved result and no admitted shape, so the relay must invent fields and the refusal and any rejected step outcome can be lost.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The missing observable result of a failure path must be chosen; the Issue is tiered decision-needed."
  },
  "options": [
    "A: let the report relay return either {status, summary} or {error: <link>} unchanged; the script's result then carries reported = {status, summary} or report_refused = <link> (no saved result), keeps relayed and rejected beside it, and a relay that brings neither is reported as report_refused with a component link naming the missing answer; contract, adapter and a build-render test change (additive shape)",
    "B: make the procedure throw when report refuses, so Claude Code shows a workflow error (loses the rejected step outcome)"
  ],
  "recommendation": "A: additive, keeps every chain in sight, all within module.workflows.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:37:43Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_step_deadlines`
  I-34b45c804cca5f7ab6d2a283db86ed25 (module.workflows, medium; module.distribution and module.execution concerned): the step command may take --wait + 90 s (req.workflows.bounded-wait; code LAUNCH_WAIT = 90), but the workflow_step tool gives it only wait + 60 s (contracts 'Starting a workflow step'; code tools.STEP_GRACE = 60), so with wait 100 the tool can refuse step_failed at 160 s while a conforming command still launches until 190 s. Workflows' contract also says the server allows wait + 120 s, but Distribution's contract and code (calls.CALL_LIMIT = 300) give every ordinary call 300 s. The entry, req.workflows.script-repeats and scenario.workflows.step-waits say each call 'waits at most 100 seconds' / 'at most --wait', omitting the launch allowance. A tool timeout is safe: the detached run lives on and the next call with the same key adopts or waits for it (except I-6f8e's lobby case).
  Not handled here (decision): Choosing the time budgets changes public timing guarantees; the Issue is tiered decision-needed.
  Options: A: raise the tool's grace to 120 s (wait + 120 = 220 s, covering the 90 s launch allowance with 30 s margin, within Distribution's 300 s call limit); replace Workflows' 'wait plus 120 seconds' server sentence by a link to Distribution's 300 s limit; say in the entry, req.workflows.script-repeats and scenario.workflows.step-waits that 100 s is the run wait, to which a call that starts a run adds at most the 90 s launch allowance; code change in tools.py only; B: keep 60 s and lower LAUNCH_WAIT below 60 s (Execution waits up to 60 s for the announcement itself, so launches would be refused early)
  Recommendation: A: outer deadlines then contain inner ones, only Workflows' text and one constant change, Distribution and Execution stay as they are.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_step_deadlines",
  "detail": "I-34b45c804cca5f7ab6d2a283db86ed25 (module.workflows, medium; module.distribution and module.execution concerned): the step command may take --wait + 90 s (req.workflows.bounded-wait; code LAUNCH_WAIT = 90), but the workflow_step tool gives it only wait + 60 s (contracts 'Starting a workflow step'; code tools.STEP_GRACE = 60), so with wait 100 the tool can refuse step_failed at 160 s while a conforming command still launches until 190 s. Workflows' contract also says the server allows wait + 120 s, but Distribution's contract and code (calls.CALL_LIMIT = 300) give every ordinary call 300 s. The entry, req.workflows.script-repeats and scenario.workflows.step-waits say each call 'waits at most 100 seconds' / 'at most --wait', omitting the launch allowance. A tool timeout is safe: the detached run lives on and the next call with the same key adopts or waits for it (except I-6f8e's lobby case).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing the time budgets changes public timing guarantees; the Issue is tiered decision-needed."
  },
  "options": [
    "A: raise the tool's grace to 120 s (wait + 120 = 220 s, covering the 90 s launch allowance with 30 s margin, within Distribution's 300 s call limit); replace Workflows' 'wait plus 120 seconds' server sentence by a link to Distribution's 300 s limit; say in the entry, req.workflows.script-repeats and scenario.workflows.step-waits that 100 s is the run wait, to which a call that starts a run adds at most the 90 s launch allowance; code change in tools.py only",
    "B: keep 60 s and lower LAUNCH_WAIT below 60 s (Execution waits up to 60 s for the announcement itself, so launches would be refused early)"
  ],
  "recommendation": "A: outer deadlines then contain inner ones, only Workflows' text and one constant change, Distribution and Execution stay as they are.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:37:44Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_divergent_duplicate_records`
  I-693b8b3bc8d05f2ca9d32c03bf6bc8db (module.issues, medium): for an Issue committed in both open and closed folders, 'concorde issues check' prescribes 'keep the record whose reports and dispositions begin with the other's, remove the other with git rm' (interface.md Bookkeeping command line 641; command.py:311-316). When the two copies diverge from a common prefix, neither extends the other and the text gives no instruction; reads already refuse the doubled Issue and archive leaves it.
  Not handled here (decision): Who reconciles divergent histories and what history results is not settled by the Specs; the Issue is tiered decision-needed.
  Options: A: check compares the copies: when one extends the other it prescribes the current repair; otherwise it names both paths, says the histories diverge, says to remove neither and that the main agent (or developer) reconciles them by hand into one record holding every report of both and dispositions consistent with its final status, committed with the other's removal alone; spec + check code + test; B: add an automatic reconciliation command (merge reports by id ordered by created_at, decide dispositions) — more code for a case that only a hand edit or Git merge creates
  Recommendation: A: no accepted observation can be lost, little code, within module.issues.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_divergent_duplicate_records",
  "detail": "I-693b8b3bc8d05f2ca9d32c03bf6bc8db (module.issues, medium): for an Issue committed in both open and closed folders, 'concorde issues check' prescribes 'keep the record whose reports and dispositions begin with the other's, remove the other with git rm' (interface.md Bookkeeping command line 641; command.py:311-316). When the two copies diverge from a common prefix, neither extends the other and the text gives no instruction; reads already refuse the doubled Issue and archive leaves it.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Who reconciles divergent histories and what history results is not settled by the Specs; the Issue is tiered decision-needed."
  },
  "options": [
    "A: check compares the copies: when one extends the other it prescribes the current repair; otherwise it names both paths, says the histories diverge, says to remove neither and that the main agent (or developer) reconciles them by hand into one record holding every report of both and dispositions consistent with its final status, committed with the other's removal alone; spec + check code + test",
    "B: add an automatic reconciliation command (merge reports by id ordered by created_at, decide dispositions) — more code for a case that only a hand edit or Git merge creates"
  ],
  "recommendation": "A: no accepted observation can be lost, little code, within module.issues.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:37:44Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_lobby_refused_step`
  I-6f8e31a79f295bc189ff1ff819f22e31 (module.workflows, medium; module.execution concerned): a step still 'starting' is relaunched under the same key when no run lies in its node and no run of the workspace holds the workspace lock or waits in the lobby. A run that was refused in the lobby (e.g. workspace_busy) before taking the lock keeps its result in the lobby for good, so if the step command died after the launch but before writing the run id, recovery cannot see that run. Found: Execution strips --trace-at from the recorded command line (runner._argv), so nothing in a lobby node ties it to the step node; correlating would need Execution to record the requested trace location.
  Not handled here (decision): Choosing between a new Execution promise and a narrowed Workflows recovery guarantee is tiered decision-needed and one option touches another Module.
  Options: A: narrow the promise in Workflows: state that a run refused before taking the workspace lock whose identity the step command could not record is not adopted; such a run did no work and changed nothing, its result stays in the lobby, and the relaunch under the same key supersedes the starting step, so the step history omits that refusal; add a scenario; B: have Execution record the requested trace location in the lobby node and Workflows scan finished lobby runs for one aimed at the step node before relaunching (needs a module.execution change, owned by the parallel r3-execution task)
  Recommendation: A: the omitted run did nothing, so relaunching is safe; no cross-Module change.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_lobby_refused_step",
  "detail": "I-6f8e31a79f295bc189ff1ff819f22e31 (module.workflows, medium; module.execution concerned): a step still 'starting' is relaunched under the same key when no run lies in its node and no run of the workspace holds the workspace lock or waits in the lobby. A run that was refused in the lobby (e.g. workspace_busy) before taking the lock keeps its result in the lobby for good, so if the step command died after the launch but before writing the run id, recovery cannot see that run. Found: Execution strips --trace-at from the recorded command line (runner._argv), so nothing in a lobby node ties it to the step node; correlating would need Execution to record the requested trace location.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Choosing between a new Execution promise and a narrowed Workflows recovery guarantee is tiered decision-needed and one option touches another Module."
  },
  "options": [
    "A: narrow the promise in Workflows: state that a run refused before taking the workspace lock whose identity the step command could not record is not adopted; such a run did no work and changed nothing, its result stays in the lobby, and the relaunch under the same key supersedes the starting step, so the step history omits that refusal; add a scenario",
    "B: have Execution record the requested trace location in the lobby node and Workflows scan finished lobby runs for one aimed at the step node before relaunching (needs a module.execution change, owned by the parallel r3-execution task)"
  ],
  "recommendation": "A: the omitted run did nothing, so relaunching is safe; no cross-Module change.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:37:44Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_missing_adapter_build`
  I-93e1317cebcb54818c287c2d029ffe61 (module.workflows, medium): catalog.build_renders returns {"files": {}} as soon as the root holds no step adapter src/concorde/workflows/scripts/claude.js, before looking at registered workflows; the contribution contract gives invalid_workflow for a missing procedure script but no rule for a missing adapter. No caller besides the workflow part's registration (renders) uses it.
  Not handled here (decision): Whether a missing adapter is a valid optional build or a broken source tree is unspecified; the Issue is tiered decision-needed.
  Options: A: refuse with invalid_workflow naming the adapter when any workflow is registered; a catalog with no registered workflow renders nothing whatever the adapter; spec + code + test; B: specify the current silent empty render as intended
  Recommendation: A: a build that silently drops /concorde-brownfield is a broken install nobody notices; behaviour changes only for a broken source tree.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_missing_adapter_build",
  "detail": "I-93e1317cebcb54818c287c2d029ffe61 (module.workflows, medium): catalog.build_renders returns {\"files\": {}} as soon as the root holds no step adapter src/concorde/workflows/scripts/claude.js, before looking at registered workflows; the contribution contract gives invalid_workflow for a missing procedure script but no rule for a missing adapter. No caller besides the workflow part's registration (renders) uses it.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Whether a missing adapter is a valid optional build or a broken source tree is unspecified; the Issue is tiered decision-needed."
  },
  "options": [
    "A: refuse with invalid_workflow naming the adapter when any workflow is registered; a catalog with no registered workflow renders nothing whatever the adapter; spec + code + test",
    "B: specify the current silent empty render as intended"
  ],
  "recommendation": "A: a build that silently drops /concorde-brownfield is a broken install nobody notices; behaviour changes only for a broken source tree.",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-13T11:37:44Z

- **task-session** task session (task r3-workflows-issues-root): `issue_decision_read_root_scope`
  I-c1b032f19ae551fc99f535a051ad2d34 (module.issues, medium): req.issues.committed-visible says the store's reads return only the records the primary worktree's last commit holds, but interface.md says library reads take the committed records of the supplied root's HEAD and read_record_file returns the file as on disk; the entry and scenario.issues.project-level speak of the primary worktree. Found: store.py reads the supplied root's HEAD; the command and the MCP tools resolve the primary worktree first (command.issues_root via project_root).
  Not handled here (decision): Reconciling opposing library-root promises chooses which behaviour the Module guarantees; the Issue is tiered decision-needed.
  Options: A: keep the library reading the supplied root's HEAD and say so; scope req.issues.committed-visible and the project-level wording to the command and tools, which resolve the primary worktree; exclude read_record_file and check from committed-only visibility explicitly (matches code; Spec text only); B: make every library read resolve the primary worktree itself (code change; a caller could no longer read a branch snapshot)
  Recommendation: A: matches the code and every caller; Spec text only.

```json
{
  "level": "task-session",
  "actor": "task session (task r3-workflows-issues-root)",
  "code": "issue_decision_read_root_scope",
  "detail": "I-c1b032f19ae551fc99f535a051ad2d34 (module.issues, medium): req.issues.committed-visible says the store's reads return only the records the primary worktree's last commit holds, but interface.md says library reads take the committed records of the supplied root's HEAD and read_record_file returns the file as on disk; the entry and scenario.issues.project-level speak of the primary worktree. Found: store.py reads the supplied root's HEAD; the command and the MCP tools resolve the primary worktree first (command.issues_root via project_root).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "Reconciling opposing library-root promises chooses which behaviour the Module guarantees; the Issue is tiered decision-needed."
  },
  "options": [
    "A: keep the library reading the supplied root's HEAD and say so; scope req.issues.committed-visible and the project-level wording to the command and tools, which resolve the primary worktree; exclude read_record_file and check from committed-only visibility explicitly (matches code; Spec text only)",
    "B: make every library read resolve the primary worktree itself (code change; a caller could no longer read a branch snapshot)"
  ],
  "recommendation": "A: matches the code and every caller; Spec text only.",
  "causes": []
}
```

## Report 1 to the main agent (Review流程), 2026-10-13T11:37:57Z

Report 1 (early decision batch) of r3-workflows-issues-root. Of the 10 decision-needed Issues, 9 are escalated (escalations 1-9); every recommendation (A each time) matches the current code, stays inside the task's Modules and changes no promise users rely on, except where noted:
1 I-037a6f83 Issues canonical JSON bytes -> A: document the store's existing escaped-ASCII canonical form in Issues' interface (no identity changes).
2 I-5215f7a5 Workflows answers digest bytes -> A: document the UTF-8 literal form the code hashes (no step key changes).
3 I-205b3441 docs refresh rollback limit -> A: admit the double-failure exception in requirement and scenarios (matches the dev script).
4 I-206d6719 script result when report fails -> A: additive report_refused field carrying the report's error link; adapter relay accepts {error}. Adds a field to the script's result shape.
5 I-34b45c80 step/tool/server deadlines -> A: tool grace 60 s -> 120 s; link Distribution's 300 s call limit; say the 90 s launch allowance in entry/req/scenario. Changes a timing figure the tool contract states.
6 I-693b8b3b divergent duplicate Issue records -> A: check detects divergence and says to keep both and reconcile by hand (main agent/developer).
7 I-6f8e31a7 lobby-refused run during starting-step recovery -> A: narrow Workflows' recovery promise (that run did no work; relaunch supersedes it) instead of an Execution change. Narrows a recovery promise.
8 I-93e1317c missing step adapter in build -> A: invalid_workflow when any workflow is registered.
9 I-c1b032f1 Issue read root scope -> A: Spec text only: library reads the supplied root's HEAD; committed-visible scoped to command/tools; read_record_file/check excluded.
I-91b18fb8 (overview vs reporting Module) no longer holds: specs/concorde/issues/module.md:111-119 now gives the owner rule and the root Module only for a null owner, as the interface and code do; it stays in resolves.
I continue meanwhile with the 20 preferred-fix, obvious-fix and suggestion Issues.

It carries escalation(s) 1, 2, 3, 4, 5, 6, 7, 8, 9.

## Answer to report(s) 1 of the task session, 2026-10-13T11:38:32Z

Escalations 1-9 (main agent), each your recommendation A: 1 document the Issue store's escaped-ASCII canonical form (no identity changes). 2 document the UTF-8 literal form the answers digest hashes (no step key changes). 3 admit the double-failure exception of the docs refresh. 4 additive report_refused field carrying the report's error link. 5 workflow_step grace 60 s -> 120 s, link Distribution's 300 s call limit, state the 90 s launch allowance. 6 issues check detects divergent duplicates and says to reconcile by hand into one record holding every report. 7 narrow the recovery promise: an unrecorded run refused in the lobby is not adopted; the relaunch supersedes it. 8 invalid_workflow when a workflow is registered without the step adapter. 9 Spec text only: library reads take the supplied root's HEAD; req.issues.committed-visible scoped to the command and tools. I-91b18fb8: no longer holds, fine.

## Task session, 2026-10-13: how the work is split

- Decision: the Issues-Module and Workflows-Module fixes are done by two Claude Code subagents of this
  session working in this task worktree on disjoint files (specs/concorde/issues + src/tests of
  issues; specs/concorde/workflows + src/tests of workflows); the root Module's are done by the
  session itself. Only the session runs the build and commits, so the index and generated/ have one
  writer. Reason: 29 Issues over three Modules with no shared files; parallel work shortens the task.

## Task session, 2026-10-13: root Module Issues (commit 923964690)

- I-205b3441 (decision-needed, answered A): requirement and scenario admit the double-failure
  exception; new scenario.concorde.docs-refresh-restore-failed verified by the existing restoration test.
- I-3d6932d0 (preferred-fix): chose to qualify the two passages (file tools bounded, shell kept in
  the task by guidance, merge audits some trees) rather than promise new enforcement, as the Issue's
  own preferred repair says; matches the permission table.
- I-4777efd6 (suggestion, applied): actors named; worker configuration phrased as "No agent SHALL
  change ... except on an explicit request of the developer", which assigns no new responsibility.
- I-9ba327d7 (preferred-fix): the plugin records xdist's crash report (`when == "???"`) as one failed
  unit with null process and times and incomplete telemetry; chose null over invented values, as the
  Issue suggests. Unit.process_id is now nullable. New scenario.concorde.test-counting-crashed; the
  regression test fails against the old plugin (KeyError) and passes now.
- I-57137c51 (suggestion, applied in bounded form): Overview moved before Core concepts (Purpose is the
  compact introduction; every concept anchor kept); each part's dependency reason now lives once in
  The children; Parts that install apart points there. Not done: merging the Overview parts table
  into The children, since the table is the compact map the Issue asks to keep.

## Task session, 2026-10-13: Workflows Issues (commit 04c684fdc)

- The five decision-needed Issues follow the main agent's answers (A each).
- I-5215f7a5: example answer "oui, un Module à part" -> digest 88f81e9b (checked with the function
  and sha256sum).
- I-206d6719: adapter-built link for a relay that brings neither answer: code report_unanswered,
  actor "Workflows (Claude Code step adapter)", reason environment.
- I-34b45c80: STEP_GRACE 120; the step agent prompt no longer says "within two minutes". Follow-on
  outside the task's Modules, judged a small mechanical one: one sentence of
  specs/concorde/distribution/contracts.md now says a workflow_step call's process takes at most
  220 s and links Workflows (it said "waits at most 100 seconds").
- I-9c638fd9 (preferred-fix): chose to refuse (step_refused over a run_not_started cause; the tool
  step_failed) instead of falling back, as the Issue suggests. tests/concorde/support/brownfield_project.py
  (bound to module.workflows) now commits an executable .concorde/bin/concorde launcher.
  step.concorde_command is kept as a wrapper with the old fallback only because
  src/concorde/method/review_issues.py (module.method) imports it; recorded as Issue
  I-4aa68b8b2b5e5eaaaa5a0dd333103eb1 (module.method, suggestion, low).
- I-bf656af2, I-e37bcee5 (preferred-fix): chose to include document.method.brownfield and
  document.tasks.requirements in module.workflows' includes (with reasons) and cite them, rather than
  restating others' promises; registry --write refreshed .concorde/specs.json for module.workflows.
- I-8631e35a (suggestion, applied in part): walkthrough first, judged-step and recovery details in a
  new "Reading the result", layout in "The record's layout"; no fact dropped.
- I-a4f4ad44 (suggestion, applied).

## Task session, 2026-10-13: Issues Issues (commit 6906d6247)

- The three decision-needed Issues follow the main agent's answers (A each). For I-037a6f83 the
  documented bytes correct one detail of the escalation's wording: Python writes \b \f \n \r \t as
  short escapes, other control and non-ASCII characters as lowercase \uXXXX.
- I-378b5120: normalized at the shared action boundary (decorator wrapping every action in
  guarded); tools.answer maps any unforeseen exception to the command's `unexpected` link.
- I-4b50e6b4: store.check_report_target shares the target checks with record_report (which still
  repeats them under the lock); skipped for a report with an origin, whose Issue is the recording
  project's.
- I-596886c3, I-c19e464b: recovery and the post-publication check now collect/put back as promised.
- I-620ede9b, I-fcd75f18: Spec only; the code already behaved as the suggested repair says.
- I-c4cc816f: new tool refusal invalid_binding (environment, Kernel refusal as cause) and
  req.issues.tools-binding-trusted; a session outside any worktree stays the main agent.
- I-693b8b3b: also admits this one hand edit in req.issues.store-writes and the entry, which said
  nobody edits a record by hand.
- I-5ae2abf5, I-83b6b191, I-a999246c (suggestions, applied). I-91b18fb8: no longer holds.

## Report 2 to the main agent (Review流程), 2026-10-13T12:22:40Z

Report 2: r3-workflows-issues-root is delivered. Delivery commit 92447948ad09e8f39c7f92ac6618b1d8e3c32181 (run r-20261013T121316-delivery-3c3ba475). task-validation: ready, 0 blocking. Full suite on the final input: 1485 passed, 5 skipped. build --check and spec-validation clean (10 warnings, none in this task's files).

All 30 Issues in resolves are handled: 29 fixed, plus I-91b18fb8, which no longer holds. Commits: 923964690 (root), 04c684fdc (Workflows), 6906d6247 (Issues).
- The 9 decision-needed Issues follow your answers (A each). One correction to escalation 1: Python writes \b \f \n \r \t as short escapes, so Issues' canonical bytes state that. All other control characters and every non-ASCII character are lowercase \uXXXX.
- Preferred-fix choices:
  - I-3d6932d0: qualified the confinement claims. No new enforcement.
  - I-9ba327d7: a crashed xdist test is one failed unit with null process and times.
  - I-9c638fd9: a step without the workspace's own concorde is refused, with no fallback. The brownfield fixture commits a launcher.
  - I-bf656af2 and I-e37bcee5: module.workflows includes Method's brownfield document and Tasks' requirements. Registry refreshed.
  - I-378b5120: one decorator normalizes OSError into io_error for both the command and the tools.
  - I-4b50e6b4: report --check also checks the target Issue, revision and status. Skipped for reports with an origin.
  - I-c4cc816f: new tool refusal invalid_binding.
  - I-620ede9b and I-fcd75f18: Spec only. The code already did this.
  - I-596886c3, I-c19e464b and I-b06aca60: as the Issues suggested.
- Suggestions applied: I-4777efd6, I-a4f4ad44, I-5ae2abf5, I-83b6b191, I-a999246c. I-57137c51 and I-8631e35a were applied in bounded form, as the decision log explains. No suggestion is left as not-actionable.
- Small follow-on outside the task's Modules: one sentence of specs/concorde/distribution/contracts.md (workflow_step fits in the 300 s limit: at most 220 s now). It may touch the line r3-distribution edits.
- New Issue I-4aa68b8b2b5e5eaaaa5a0dd333103eb1 (module.method, suggestion, low): Method's Issue calls still use workflows.step.concorde_command, which keeps the old fallback only for them.
- Decisions taken without the developer: the work was split among two subagents of this session on disjoint files, and the session made every commit. Everything else is in the decision log.
- Open: nothing for this task. No Issue was escalated to the developer.

## Main agent, 2026-10-13: merge conflict

`task merge` refused with merge_conflict in specs/concorde/distribution/contracts.md (the
workflow_step 300 s sentence, which r3-distribution also changed; it is merged). Merge the primary
branch (main) into concorde/r3-workflows-issues-root, resolve keeping both tasks' intent
(r3-distribution's text plus your "at most 220 s" fact), verify (build, spec-validation, the
relevant tests), deliver again and report.

## Task session, 2026-10-13: merge of main after merge_conflict (commit 75f55b9b1)

- Merged main into the task branch as the main agent asked. Only conflict:
  specs/concorde/distribution/contracts.md. Resolution: kept r3-distribution's text (the
  `tools/list_changed` notification against both digests) and replaced its "waits at most 100
  seconds" sentence with this task's fact (a `workflow_step` call's process takes at most 220 s,
  linking Workflows), so both tasks' intent stands. Auto-merged .concorde/specs.json and
  tests/concorde/support/pytest_timing.py without conflict.
- build: success; spec-validation: 0 errors, 5 warnings (all in spec-tooling/spec/scenarios.md,
  none in this task's files).
- task-validation r-20261013T144958-task_validation-e0d065bf on 75f55b9b1: ok, ready. Full suite:
  1558 passed, 5 skipped.
- delivery r-20261013T145933-delivery-5b77a60d: blocked (not_ready), one blocking finding:
  check.views.publication-types failed because its fresh `npm ci` in a scratch copy did not install
  esbuild's optional `@esbuild/linux-x64` ("could not be found, and is needed by esbuild"). The same
  check on the same inputs passed in the task-validation run just before, and the worktree's own
  docsite/node_modules holds the package, so I judged it an npm install flake (other round-3
  deliveries ran npm ci concurrently) and ran delivery again unchanged.

## Report 3 to the main agent (Review流程), 2026-10-13T15:19:09Z

Report 3: r3-workflows-issues-root is delivered again after the merge of main. Delivery commit da36e92dcc4b9ebbac68aa1d90bb5ff77ddf7269 (run r-20261013T150925-delivery-3ac42c21) on merge commit 75f55b9b1.
- Conflict in specs/concorde/distribution/contracts.md resolved keeping both intents: r3-distribution's text (tools/list_changed sent when tools differs from both digests) stands; only its 'waits at most 100 seconds' sentence now says a workflow_step call's process takes at most 220 seconds, linking Workflows, so it fits in the 300 s limit. No other conflict.
- Verified on the merge: build ok; spec-validation 0 errors, 5 warnings (all in spec-tooling/spec/scenarios.md); full suite 1558 passed, 5 skipped; task-validation ready.
- The first delivery run (r-20261013T145933-delivery-5b77a60d) was blocked by check.views.publication-types: its fresh npm ci in a scratch copy did not install esbuild's optional @esbuild/linux-x64. The same check passed on the same inputs in the task-validation just before, so I judged it an npm install flake and reran delivery unchanged; it passed. If it recurs, the check's npm ci may be worth an Issue of module.views.
- Open: nothing for this task.

## Closed: merged, 2026-10-13T15:19:21Z

The merge answered report(s) 2, 3 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit da36e92dcc4b9ebbac68aa1d90bb5ff77ddf7269 into main and closed it as merged. Nobody answers a report after that.
