# Decision log: fix-open-trace-producers

Goal: Make every producer report a failed trace write in its own result (run results with their workers' failures, check results, the merge attempt a close --merged finishes), and settle whether the Bash sandbox can deny writes below a writable directory

## Brief (main agent, 2026-10-04)

### Context

The developer asked (2026-10-04) to try to resolve the project's open Issues. Nine fix tasks
(fix-open-*) merged into `main` and closed 268 Issues. Six remain open; this last task takes the
four that can be fixed and leaves two advisory suggestions (I-a3522268, I-efaedb06) alone.

fix-open-kernel made Tracing record every failed trace write in `Node.failures` and
`req.tracing.written-at-start` say producers report it (tracing stays best-effort: a failed write
never changes the work's outcome). Workers already reports them (`trace_failures` in the worker run
record and its trace content, `trace-write` evidence on a failed run), and Tasks reports them for
task deliver, open and merge (fix-open-coordination).

### What this task does

- **I-b6bc48da (module.execution)**: the run result reports a failed write of the run's trace node,
  and the trace write failures of the worker runs it launched (Method's steps carry the workers'
  `trace_failures` into the run's evidence; Workers left that to Method), in the run result
  contract and code, with a scenario and test.
- **I-da4a0cab (module.checks)**: a check result reports a failed write of the check's trace node.
- **I-386c167f (module.tasks)**: a close that finishes a merged task (`task close --merged`) also
  ends the latest unfinished merge attempt node with the merge's outcome.
- **I-ce303462 (module.harness, suggestion)**: find out from the pinned Claude Code documentation
  under `references/` (and pi's sandbox engine) whether a write-deny list inside an allowed directory
  is supported. If it is, add the ro entries below rw directories to it on both backends, with tests,
  and resolve the Issue; if it is not, close it `not-actionable` citing the documentation, and keep
  the known limit in harness/module.md.
- After fixing each Issue, add it with `concorde task resolve`; add none you did not fix.

Rules: every part still works installed with only its dependencies, the part-dependency and
guidance checks pass, no shims. Verify with `build --check`, `spec-validation`, the full suite, then
`task-validation` and `delivery`, and report. Nothing else runs in parallel.

## Task session decisions (2026-10-04)

1. **Execution (I-b6bc48da).** The runner adds every refused write of the run's `trace.json` to the
   result's host evidence as `trace-write` (ref: the run identity, detail: node file, moment,
   error), before the result is composed; when the final write, which follows the result, is
   refused, the runner publishes the result again with that evidence before releasing its locks,
   and prints that result. Status and exit status never change for it. Run result contract
   `contract.execution.run-result` 3 -> 4; new `req.execution.trace-write-reported` and
   `scenario.execution.trace-write-reported`.
   - Execution's Specs still said a failed first or final `trace.json` refuses the run
     (`run_unrecorded`) or loses it (`result_unsaved`), while `Node` (since fix-open-kernel) no
     longer raises an operating-system error, as `req.tracing.written-at-start` and the brief's
     "a failed write never changes the work's outcome" require. I aligned Execution's Specs with
     that: only the folder, the run lock and the first progress file refuse a run, and only a
     `trace.json` breaking the node contract (`TraceError`, a producer defect) still refuses or
     loses it. Reason: carrying out the developer's decision; the code already behaved so.
2. **Method.** `absorb` adds each `trace_failures` entry of the worker run record, and of each
   round's check results, to the run's own evidence (`ctx.evidence`) as `trace-write`, so a step
   that drops its outcome's evidence cannot lose them; `run_module_checks(report=ctx.evidence)`
   does the same for the checks implement's host checks, code_review and task-validation run.
   New `req.method.trace-writes-reported`, `scenario.method.trace-write-reported`.
3. **Checks (I-da4a0cab).** A check result gains `trace_failures` (empty when every write
   succeeded); a `CheckError` that ends a call carries the trace failures of every check the call
   ran, which `service_error` names as `trace-write` evidence. A call ended by an error that is not
   Check execution's (interrupt, cancellation) carries none: it has no result and its error goes on
   unchanged, as the service already promises. Glossary definition of Check result extended.
4. **Tasks (I-386c167f).** `close --merged` ends the task's latest merge attempt node still
   `running`: `ok` with `merged` (`contained` when after == before) when its content records a merge
   commit, otherwise `failed`/`interrupted`; a refused write of it is a warning of the close. An
   attempt the merge itself ended (e.g. `failed`/`refused` after a close refusal) is left as it is.
   New `req.tasks.close-ends-merge-attempt`, `scenario.tasks.close-merged-ends-attempt`.
5. **Harness (I-ce303462).** Supported: Claude Code's `sandbox.filesystem.denyWrite` ("including
   paths inside a directory that is otherwise writable", references/claude-code/settings-reference.md)
   and sandbox-runtime's (`denyWrite` wins over `allowWrite`, references/sandbox-runtime/README.md).
   Verified on this host with the installed sandbox-runtime 0.0.77 + bwrap: a denyWrite file in an
   allowWrite directory cannot be written, removed or replaced; siblings stay writable. So the
   shared sandbox lists now carry `denyWrite`: every grant entry at `ro` or `names` strictly below
   an `rw` directory entry; pi's extension stops forcing `denyWrite: []`. The known limit in
   harness/module.md is replaced by the remaining one: a `rw` path listed below such a `ro`/`names`
   directory is not Bash-writable (file tools still write it). Resolving the Issue (fixed, not
   closed not-actionable).
6. **New Issue I-babfa1cb (module.harness, obvious-fix, low)**, not fixed here (outside the goal):
   pi's Bash reads a `names` path listed apart below a readable directory; verified by probe.

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T03:45:47Z

fix-open-trace-producers delivered: delivery commit b7237a7fb8c643c53d0059eccceea2bdf6d14ca9 on concorde/fix-open-trace-producers (3 commits before it). Verified: build --check, spec-validation (no findings), full suite 1248 passed / 5 skipped, task-validation ready with nothing blocking.

The task resolves 4 Issues (added with task resolve): I-b6bc48da, I-da4a0cab, I-386c167f, I-ce303462.

- I-b6bc48da (Execution): the run result now names each refused write of the run's trace.json as `trace-write` host evidence. A refused final write, which comes after the result, is added by publishing the result again before the locks are released. Status and exit status never change for it. The run result contract went from version 3 to 4. New req/scenario execution.trace-write-reported.
- Workers' failures (Method): absorb adds the worker run's `trace_failures`, and those of each round's checks, straight to the run's evidence. `run_module_checks(report=ctx.evidence)` does the same for host checks (implement, code_review, task-validation). New req.method.trace-writes-reported and scenario.method.trace-write-reported.
- I-da4a0cab (Checks): a check result has a new field `trace_failures`. A CheckError that ends a call carries the failures of every check the call ran, and service_error turns them into `trace-write` evidence. The glossary definition of Check result now mentions this. New req/scenario checks.(service-)trace-write.
- I-386c167f (Tasks): `close --merged` now ends the latest merge attempt node that still says running. It ends `ok` with `merged` (or `contained`) when its merge commit was made, otherwise `failed` with `interrupted`. If the write of that node is refused, the close gives a warning. New req.tasks.close-ends-merge-attempt and scenario.tasks.close-merged-ends-attempt.
- I-ce303462 (Harness): resolved by a fix, not closed as not-actionable. Both Claude Code's `sandbox.filesystem.denyWrite` and sandbox-runtime's `denyWrite` take precedence inside an allowed directory: Claude Code's settings reference says so, and so does sandbox-runtime's README. I confirmed it on this host with sandbox-runtime 0.0.77 and bwrap: the file could not be written, removed or replaced, and the files beside it stayed writable. The sandbox lists both backends share now put in denyWrite every `ro` or `names` grant entry that lies below a `rw` directory entry. pi's extension no longer forces `denyWrite: []`. harness/module.md drops the old known limit and states the remaining one: a `rw` path listed below such a `ro`/`names` directory can be written by the file tools but not by Bash.

Decisions I made on my own (details in the decision log):
1. Execution's Specs still said that a failed first or final trace.json write refuses the run (run_unrecorded) or loses it (result_unsaved). Since fix-open-kernel, Node no longer raises on those operating-system failures, which matches the brief's "a failed write never changes the work's outcome". I aligned runner.md and requirements.md with that. A run is still refused for its folder, its run lock or its first progress file, and still refused or lost for a trace.json that breaks the node contract (TraceError), which is a producer defect.
2. A check call ended by an interrupt or cancellation reports no trace failures: it has no result, and its error goes on unchanged, as the service already promises.
3. A merge attempt that the merge itself already ended (for example failed/refused after its close was refused) is left as it is. Only a node still `running` is ended.

New Issue, not fixed because it is outside the goal: I-babfa1cb (module.harness, obvious-fix, low). On pi, Bash can read a `names` path listed below a readable directory. Claude Code adds its Read deny rules to the sandbox's denyRead, but pi receives only the sandbox lists. I confirmed this by probe. The fix is to add those entries to denyRead.

Nothing is open for the developer, and there was no workflow and no escalation.

## Closed: merged, 2026-10-04T03:46:05Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b7237a7fb8c643c53d0059eccceea2bdf6d14ca9 into main and closed it as merged. Nobody answers a report after that.
