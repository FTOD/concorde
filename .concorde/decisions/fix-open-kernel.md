# Decision log: fix-open-kernel

Goal: Fix the open Issues of the kernel part (Kernel, Tracing)

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

- I-335b9728 (swallowed trace write failure): tracing stays best-effort for the work (a failed write never changes the work it records), but the failure is never silent: every producer reports a trace write failure in its own result (evidence or warning), and req.tracing.written-at-start says so.
- I-96b5d8ca (synthetic workspace node status): `running` when any child runs (or is lost while its runner lives), otherwise the status of its most recently started child, and `unknown` with no child; the contracts say so.

### Your 22 Issues

- I-335b97282d9a5858a04e987d80710f4e (medium, decision-needed, module.tracing): A failed trace.json write is swallowed and never reported
- I-6e58eaae0d7a50faa546e02238572341 (medium, preferred-fix, module.tracing): Prune omits traces stored outside the primary worktree
- I-3cb1625c4747588fb061f7216cc15d65 (medium, preferred-fix, module.tracing): Direct worker views fail to report a lost parent run
- I-f2e66c2ac70f5ead9a30e2515ed27152 (medium, preferred-fix, module.tracing): Exception links drop stdout when stderr is present and keep only 2000 characters
- I-fa2b91a7054158edbb9715d1096af0cd (medium, obvious-fix, module.kernel): KeyboardInterrupt or SystemExit during a file transaction skips restoration
- I-96b5d8caa8ae56d8850698a0b6e31091 (low, decision-needed, module.tracing): The synthetic workspace node's status has no defined meaning
- I-c2cb9cca8bd55804ad670b3cbb620511 (low, preferred-fix, module.tracing): Tree format is a summary, while the reading contract says it prints the same
- I-8fa5ad7ed5e95181940704dc3114ab4c (low, preferred-fix, module.kernel): Binding write checks only the schema, and read compares roots by realpath
- I-3731c71fd2d35c65bfc2d0f768ff2aff (low, preferred-fix, module.kernel): Schema comparisons do not consistently use JSON equality
- I-faff92960b7e59ff88f8e556768266f5 (low, preferred-fix, module.kernel): Some Kernel operations let raw OSError escape instead of a coded refusal
- I-01d71c9cf21f5c338a7337eec0e25b61 (low, obvious-fix, module.tracing): Prune reports a folder removed even when its removal failed
- I-52104b73064251d4ae7aea2a9fdba7b2 (low, obvious-fix, module.tracing): trace list orders by .concorde directory before root category
- I-545905c87555562db23f494d042ba572 (low, obvious-fix, module.kernel): Delivery recognition strips whitespace around the subject
- I-2b3b0790b71b5f03940c3d26b285051d (low, obvious-fix, module.kernel): Type registration rejects top-level boolean schemas
- I-c08a92435eac51be84f39b5a190537c1 (low, obvious-fix, module.kernel): Malformed transaction digests are refused as stale instead of invalid
- I-981da1f44c5d598da86cca6655ea952d (low, obvious-fix, module.kernel): Huge JSON integers crash schema checking with OverflowError
- I-dc2796da51de50a9b39fed95d8435b7f (low, obvious-fix, module.kernel): minLength 0 skips the promised nonblank rule
- I-99583038d2f2533cb82336af6aafa769 (low, obvious-fix, module.kernel): Artifact arrays get undocumented id and path uniqueness
- I-69b58414a26d56cf94263f719d7d7c51 (low, obvious-fix, module.kernel): Strict JSON decoding accepts numbers that overflow to infinity
- I-bbd853669a465515be855406f0b4c04b (low, obvious-fix, module.kernel): req.kernel.transaction-restored promises restoration unconditionally next to the refused-restoration exception
- I-b3f4d61ea46554a9b34ad1a549691dee (low, suggestion, module.kernel): State that a typed-value $ref stands alone
- I-5d5394ccd2f95553bd33800a0357e2b4 (low, suggestion, module.kernel): A workflow would clarify transaction recovery outcomes

## Task session decisions (fix-open-kernel, 2026-10-04)

- Kernel Issues fixed in one step (schema, files, binding, delivery, locking, contracts,
  requirements, module entry):
  - I-dc2796da (minLength 0): kept the Spec sentence shared with Spec core's copy and fixed the code
    to test the keyword's presence; chose to keep `minLength: 0` admitting `""` (only a nonempty
    whitespace-only string is refused), and said so in the contract, since refusing `""` would
    contradict the bound itself.
  - I-3731c71f (preferred-fix): one recursive JSON equality for const, enum, uniqueItems and the
    repeated-registration comparison, as the Issue's suggested fix; contract text says so.
  - I-8fa5ad7e (preferred-fix): one semantic check shared by `load` and `write`: `root` must be an
    absolute real path (an alias or `/.` is `binding_invalid`), equal to the worktree's real path
    (`binding_misplaced` when read, `binding_invalid` when written, as the Library table names only
    `binding_invalid` for writing), absolute folders and an existing workspace folder.
  - I-faff9296 (preferred-fix): the library's own I/O failures in binding write, artifact reading and
    lock acquisition are `system_error` naming the path with the OS error as cause; the lock wrappers
    translate only acquisition (ExitStack), so the caller's own exceptions inside the block pass
    unchanged. Contract Library gets one general sentence plus `system_error` in the rows.
  - I-fa2b91a7: restoration on BaseException; an interruption with a refused restoration ends in
    `system_error` like any other failure (the contract's outcome list), otherwise it is re-raised
    unchanged.
  - I-5d5394cc (suggestion, cheap): added an illustrative D2 diagram of the transaction outcomes in
    the Kernel module entry, with a killed process stated outside it.
- Tracing Issues fixed in one step (errors, reader, retention, command, node, contracts,
  requirements, module entry, scenarios):
  - I-f2e66c2a (preferred-fix): an exception link's detail names both streams of a failed command;
    each stream is quoted whole up to 20,000 characters, beyond that from its end with the count
    left out, and the whole streams go into the traceback file when the component keeps one. The
    rule is prose beside contract.tracing.error, whose semantics already ask for the exact output.
  - I-6e58eaae (preferred-fix): `trace prune` prunes every `.concorde` directory `show` searches
    (own worktree, binding's, primary's), each with the roots placed there, by the primary
    worktree's configuration, as the Issue suggested.
  - I-01d71c9c: prune output is `{"removed", "failed", "dry_run"}`, exit status still 0 (a partly
    failed prune is no refusal); a top folder's `trace.json` is removed last so a folder not removed
    wholly is found and retried by the next prune, as the contract now says.
  - I-3cb1625c (preferred-fix): `view` looks for a lost run above a directly addressed node (up to
    the `.concorde`, or the worktree root outside it), as the Issue suggested.
  - I-96b5d8ca (main agent's decision): read "running when any child runs (or is lost while its
    runner lives)" as: running when any child's status is `running`; a `lost` child, whose runner
    has ended by definition, does not count as running, and is the workspace's status only when it
    is the most recently started child. contract.tracing.view raised to version 2 for this.
  - I-c2cb9cca (preferred-fix): the contract now calls `--format tree` a summary and the tree line
    names the error's code; the JSON output alone carries every field.
  - I-52104b73: `reader.listing` takes several `.concorde` directories and orders by root category
    first, directories second.
  - I-335b9728 (main agent's decision): Tracing side done — `Node.failures` keeps an account of every
    failed write (file, moment, error); req.tracing.written-at-start and "Writing a node" state
    best-effort but never silent, the producer reporting each failure in its own result. The
    producers themselves (Execution runner and checks, Workers, Tasks) are not changed: escalated.

## Escalated to the main agent, 2026-10-04T02:17:26Z

- **task-session** task session (task fix-open-kernel): `producer_reporting_scope`
  I-335b9728 (swallowed trace write failure): the main agent decided that every producer reports a failed trace.json write in its own result. This task delivered the Tracing side (commit 61c64c2e): Node.failures keeps an account of every failed write (file, moment start/update/end, OS error), and req.tracing.written-at-start and contracts 'Writing a node' now say tracing is best-effort but never silent, the producer reporting each failure as evidence or a warning. The producers are in other parts, and only some results have a place for it: Execution's runner (run result host_evidence: small), Check execution's check node (check result has no such field), Workers' worker-run and worker-round nodes (run record: needs a field), Tasks' deliver, open and session nodes (task deliver/open outputs have no warnings; merge and close do). Workflows writes with trace.write directly, which raises, so it is not silent. Doing it means contract and code changes in module.execution, module.checks, module.workers and module.tasks, each being edited by a parallel task (fix-open-execution, fix-open-worker-harness, fix-open-coordination). Until the producers report, the new requirement text is not yet met by them.
  Not handled here (scope): the remaining changes are other Modules' result contracts and code, edited by parallel tasks; the brief says to escalate a fix needing another group's files beyond a small edit
  Options: 1. This task also changes every producer and its result contract (Execution, Check execution, Workers, Tasks); 2. This task delivers only the Tracing side; the main agent asks the parallel tasks of those parts to report Node.failures in their producers; I-335b stays open until the last producer does; 3. As 2, but this task records one obvious-fix Issue per producer Module (execution, checks, workers, tasks) naming Node.failures, and resolves I-335b with the Tracing side
  Recommendation: 3: each part decides how its own result shows the failure, nothing conflicts with the parallel tasks, and the remaining gap is tracked per Module

```json
{
  "level": "task-session",
  "actor": "task session (task fix-open-kernel)",
  "code": "producer_reporting_scope",
  "detail": "I-335b9728 (swallowed trace write failure): the main agent decided that every producer reports a failed trace.json write in its own result. This task delivered the Tracing side (commit 61c64c2e): Node.failures keeps an account of every failed write (file, moment start/update/end, OS error), and req.tracing.written-at-start and contracts 'Writing a node' now say tracing is best-effort but never silent, the producer reporting each failure as evidence or a warning. The producers are in other parts, and only some results have a place for it: Execution's runner (run result host_evidence: small), Check execution's check node (check result has no such field), Workers' worker-run and worker-round nodes (run record: needs a field), Tasks' deliver, open and session nodes (task deliver/open outputs have no warnings; merge and close do). Workflows writes with trace.write directly, which raises, so it is not silent. Doing it means contract and code changes in module.execution, module.checks, module.workers and module.tasks, each being edited by a parallel task (fix-open-execution, fix-open-worker-harness, fix-open-coordination). Until the producers report, the new requirement text is not yet met by them.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "the remaining changes are other Modules' result contracts and code, edited by parallel tasks; the brief says to escalate a fix needing another group's files beyond a small edit"
  },
  "options": [
    "1. This task also changes every producer and its result contract (Execution, Check execution, Workers, Tasks)",
    "2. This task delivers only the Tracing side; the main agent asks the parallel tasks of those parts to report Node.failures in their producers; I-335b stays open until the last producer does",
    "3. As 2, but this task records one obvious-fix Issue per producer Module (execution, checks, workers, tasks) naming Node.failures, and resolves I-335b with the Tracing side"
  ],
  "recommendation": "3: each part decides how its own result shows the failure, nothing conflicts with the parallel tasks, and the remaining gap is tracked per Module",
  "causes": []
}
```

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:25:08Z

fix-open-kernel: 21 of 22 Issues fixed and resolved on the task branch; 1 escalation needs your answer before delivery. Not delivered yet.

Commits on concorde/fix-open-kernel: 4241aff7 (Kernel), 61c64c2e (Tracing). build --check, spec-validation and the full suite pass (1098 passed, 5 skipped). task-validation: ready.

Resolved (added with task resolve):
- Kernel (14): I-fa2b91a7, I-8fa5ad7e, I-3731c71f, I-faff9296, I-545905c8, I-2b3b0790, I-c08a9243, I-981da1f4, I-dc2796da, I-99583038, I-69b58414, I-bbd85366, I-b3f4d61e (suggestion: done), I-5d5394cc (suggestion: D2 diagram added)
- Tracing (7): I-f2e66c2a, I-6e58eaae, I-3cb1625c, I-01d71c9c, I-52104b73, I-c2cb9cca, I-96b5d8ca

Decisions I made (also in the decision log):
- preferred-fix choices: one recursive JSON equality for const/enum/uniqueItems/registration; one binding check shared by read and write (root must be an absolute real path); coded system_error for the library's own I/O, with lock wrappers translating only acquisition; exception links quote stdout and stderr, each up to 20,000 chars from the end with the omitted count, and the traceback file holds the whole streams; prune covers every .concorde dir `show` searches, using the primary's configuration; a node addressed directly is lost when a run above it is lost; the tree format is called a summary and shows the error code.
- minLength 0 still admits "" (only nonempty whitespace is refused).
- prune prints {removed, failed, dry_run}, exit status 0, and removes trace.json last so a folder it could not remove is retried.
- I-96b5 as decided, with `lost` children not counted as running (a lost child's runner has ended). The workspace shows the latest child's status, lost included. contract.tracing.view is now version 2.
- An interruption (KeyboardInterrupt/SystemExit) in a file transaction restores files like any other failure.

Escalation 1 (producer_reporting_scope), still open: I-335b9728 is not resolved.
- Done here: the Tracing side. Node.failures records every failed trace write, and req.tracing.written-at-start says producers report it.
- Not done: the producers themselves (Execution runner and checks, Workers, Tasks). Their result contracts and code belong to parallel tasks. Until they report, the new requirement text is not met by them.
- Options: 1. this task changes every producer and its contract; 2. Tracing side only, you ask the parallel tasks to do theirs, and I-335b stays open; 3. as 2, but I record one obvious-fix Issue per producer Module and resolve I-335b.
- My recommendation: 3.

Rendered chain:
- **task-session** task session (task fix-open-kernel): `producer_reporting_scope` — see escalation 1 in the decision log; options 1–3 as above, recommendation 3.

Nothing else is open. Once you answer, I'll carry it out and deliver.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-04T02:25:35Z

Escalation 1 (producer_reporting_scope): option 3. Keep the Tracing side in this task, record one obvious-fix Issue per producing Module whose result must report a failed trace write (Execution's runner, Check execution, Workers, Tasks, and Workflows if it writes nodes), each naming Node.failures and req.tracing.written-at-start, and resolve I-335b9728 here. The producers are fixed after this wave merges, since they need Node.failures on main. Then deliver and report.
- Carried out the main agent's answer to escalation 1 (option 3): I-335b9728 is resolved by this
  task's Tracing side. One obvious-fix Issue was recorded per producer, each naming Node.failures
  and req.tracing.written-at-start, severity medium as I-335b had: I-b6bc48da (module.execution,
  runner), I-da4a0cab (module.checks), I-b5522be8 (module.workers), I-265f20b9 (module.tasks).
  None for Workflows: it writes its nodes with trace.write directly, whose OSError propagates, so
  a failed write is not swallowed there.

## Report 2 to the main agent (项目架构分离建议), 2026-10-04T02:34:34Z

fix-open-kernel delivered: delivery commit e0f076db92c6d42f67759188b3effb22b87b472c on concorde/fix-open-kernel. Answers report 1; I followed option 3.

Resolves all 22 of the task's Issues: the 21 listed in report 1, plus I-335b9728. The Tracing side for I-335b is in commit 61c64c2e.

New Issues for the producers (obvious-fix, severity medium, as I-335b had). Each names Node.failures and req.tracing.written-at-start, and each is to be fixed after this task merges:
- I-b6bc48da61c35080803bc2e9c0113353 (module.execution): the run result
- I-da4a0cab7f395a6ba0dc48f5a464a9d5 (module.checks): the check result
- I-b5522be8a239584fba10cf454cbeb6c0 (module.workers): the worker run record
- I-265f20b95b9258f19244d124e8f3c7be (module.tasks): the outputs of task deliver, open and merge

No Issue for Workflows: it writes its nodes with trace.write directly, and that raises the OSError instead of swallowing it.

delivery validated the whole workspace again before committing. build --check, spec-validation and the full suite passed before delivery (1098 passed, 5 skipped). The decision log has every decision. Nothing is open. Merge with: task merge fix-open-kernel --check "python3 scripts/concorde.py build" --check "python3 scripts/concorde.py spec-validation".

## Closed: merged, 2026-10-04T02:34:47Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit e0f076db92c6d42f67759188b3effb22b87b472c into main and closed it as merged. Nobody answers a report after that.
