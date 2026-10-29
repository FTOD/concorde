# Decision log: checks-execution-high

Goal: Fix the high Issues of Checks and Execution (refuse input directories that cannot be fully enumerated; verify preparation changes inside submodules independently) and their other obvious-fix Issues

## Task brief (main agent, 2026-10-29)

**Origin.** Project review r-20261029T060905-project_review-fa4731e2 (unbound, commit 8a5ed4245, verdict changes_required) left 2 critical and 10 high Issues open. The developer chose to fix every critical and high Issue first, in five parallel tasks split by Module, each also fixing the obvious-fix Issues of its own Modules. Read the review's findings for your Modules in `.concorde/unbound/r-20261029T060905-project_review-fa4731e2/result.json` (`output.modules[]`, the panel and code_review reviews) when an Issue's text is not enough.

**Issues this task resolves (26, all in the task's resolves):**

- I-40b793b793de5f04b75d5565a7e18cdc (module.checks, high, preferred-fix): Refuse input directories that cannot be fully enumerated
- I-e72fc9c3727b5b0196cc6b90817f9385 (module.execution, high, preferred-fix): Verify preparation changes inside submodules independently
- I-082c7c119cfd5623889071f71efc303d (module.checks, medium, obvious-fix): Refuse non-list measured file collections
- I-11a5ac6a7d3f54c9b03bebda22bb4c56 (module.checks, medium, obvious-fix): Trace-write scenario combines incompatible outcomes and an undefined second check
- I-26ff2c52ddd05cf48c6081c9daed0485 (module.checks, medium, obvious-fix): Linked checks-file refusal is absent from the format contract
- I-2c2faa435f1952e8a7e86604810c81ea (module.checks, medium, obvious-fix): Selection and freshness scenarios omit required caller inputs
- I-48510dc5bbca54b58b28b16009a45869 (module.checks, medium, obvious-fix): Output scenario lacks fixtures for signal termination and large output
- I-527a7be0523855a2865f13cd0a4e44c2 (module.checks, medium, obvious-fix): Finalize interrupted check nodes even when saving output fails
- I-c5d4e3e82e225650aa422ec287307853 (module.checks, medium, obvious-fix): Validate checks filenames as Module identities
- I-df3dd3873c6953b5a2a63eebb1ab188a (module.checks, medium, obvious-fix): Record asyncio cancellation as cancelled rather than error
- I-265464795b8059e7a2c10b45b9c1ac2e (module.execution, medium, obvious-fix): Make trace-location conditions mutually exclusive
- I-444a38370587586893b48541b29af0f7 (module.execution, medium, obvious-fix): Exclude lock files from the every-file-in-node obligation
- I-550df5881ed55e11a2028baf520b01ff (module.execution, medium, obvious-fix): Record preparation evidence on cancellation and sandbox failure
- I-641b1e5544ab5764b5253559e61b2fa4 (module.execution, medium, obvious-fix): State the exceptions to workspace-lock and result-availability guarantees
- I-66369dc978975717988da53547e31193 (module.execution, medium, obvious-fix): The worked example incorrectly makes admission a step
- I-78ad2e9499e15ba79bccb9ebba25581b (module.execution, medium, obvious-fix): Remove the duplicated .concorde component from the lobby path
- I-7f746b6a18a7514484d4c7a908e0b573 (module.execution, medium, obvious-fix): Restrict foreground result printing to accepted run invocations
- I-8fbcb097f0d05a42a6334099229650f9 (module.execution, medium, obvious-fix): Assign worker-start notification consistently to the step
- I-956bbd21c93d5a92bbfe8e316b6b37de (module.execution, medium, obvious-fix): Limit the RunContext promise to admission and step callbacks
- I-9b7c0d9465485626bbf41184b3e67836 (module.execution, medium, obvious-fix): Call the context's worker claims a worker result, not a run record
- I-a7d3a59bc07b5eaa8d18c1f38e47451b (module.execution, medium, obvious-fix): Include the failed-publication exception in the lock obligation
- I-b8724ff562105ffe863d335add6a0f78 (module.execution, medium, obvious-fix): Split the additional scenarios that append independent invocations
- I-baa45e7bb96a5297a479f5e5d6ed5459 (module.execution, medium, obvious-fix): Execution leaves its reliance on Workers' placement rule undeclared
- I-bb0d43be23345b219c5793625454e399 (module.execution, medium, obvious-fix): Keep a run running until its run lock is released
- I-bd3903fabba858489020f9dee53e45fe (module.execution, medium, obvious-fix): Forbid untracked nonignored files, not committed files, after preparation
- I-d632e2c202a75cf1b7ecd7130b71be21 (module.execution, medium, obvious-fix): Validate contradictory successful step errors instead of discarding them

**How to handle them (the main agent's decisions).**
- Critical and high first. Show each with a test that fails on the old code.
- Fix obvious-fix Issues directly. For a preferred-fix Issue, take the clearly better fix and report it. None of these Issues is decision-needed. If one turns out to need a decision beyond your Modules or beyond the Issue's evident intent, escalate it rather than guess.
- An Issue that turns out to be already fixed, not a real problem, or a duplicate of another open Issue: say so with your evidence in your report. Do not close it yourself. The main agent closes it, or the merge closes it as resolved.
- Leave the other open Issues of your Modules (preferred-fix and decision-needed medium or low) alone, unless a fix here resolves one as a side effect: then name it in your report.
- Add or change Specs first where a fix changes a promise. Keep within your Modules. Escalate a change any other Module would have to make.

**Parallel tasks.** Four other tasks run at the same time. Do not touch their Modules:
- swe-cases-critical: module.swe-bench-cases
- coordination-high: module.tasks, module.task-session
- worker-harness-high: module.harness, module.workers
- specmcp-workflows-high: module.spec-mcp, module.workflows

**Specific to this task.** Checks changed recently in task checks-bwrap-compat (merged bba57093a): bubblewrap 0.4.0 support, the pidfd system call fallback and the gate cleanup. Keep all of it, and keep bubblewrap 0.4.0 and the latest release working. Issue I-d79ac840 (UV_CACHE_DIR, preferred-fix) is not in this task.

**Verification.** Run Concorde's full suite, `build --check` and `spec-validation`. Then run `task-validation` and `delivery` from the task worktree, and report.

**Environment notes.**
- uv, node/npm (Node 24, npm 11), pi, rg, fd and d2 are under `/home/scratch.zbai_gpu/opt`.
- The system bubblewrap is 0.4.0 and works.
- Every worker runs on pi: claude-opus-5-5 and gpt-6.1-sol.
- Keep large files off `$HOME` (5 GB quota).

**Left to the session.** The mechanisms, internal structure, test design and Spec wording.

## Task session decisions (2026-10-29)

- **I-40b793 (high, preferred-fix), fix chosen.** Directory inputs are now walked with `os.walk`, whose `onerror` refuses a directory that cannot be listed (the input itself or any directory below it, and a directory whose entries cannot be stat'ed) with the existing code `check_input_missing`, naming the check, its Module and the directory as `path`. I kept the existing code rather than adding a new one: the Errors list already says an input must be measurable, consumers need no new code, and the remediation is the same kind (correct the worktree or the check's inputs). The refusal happens before any command, since the pre-run loop now enumerates every input fully; `validate_checks` refuses it too. File order and `__pycache__` exclusion are unchanged (sorted `Path` order), so existing digests stay the same; `__pycache__` is now judged on the path relative to the worktree instead of the absolute path. New `req.checks.input-measured-whole` and `scenario.checks.input-unreadable`. Test failed on the old code (CheckError not raised).
- **I-e72fc9 (high, preferred-fix), fix chosen.** Before the first command the runner now finds the checkout's repositories: the checkout and every submodule whose directory holds a `.git` (recursively), each with its Git directory read then (and checked to be its own top level). Each repository is read on its own with its pinned Git directory against a fresh index of its own `HEAD`, its new `.gitignore` files counted and its `.git` bytes recorded; the superproject's status now uses `--ignore-submodules=all` so it never reaches a submodule through its (rewritable) `.git` file. A submodule that is not checked out must stay empty. A sparse submodule's absent files show identically in both readings, so they are no change. Cost measured on this worktree: about 1 s added for the 6 sparse reference submodules (superproject reading 3 s as before). The test failed on the old code for 3 of 5 cases (hidden `.gitignore` at the submodule root and nested, write into a submodule not checked out) and gave a vague `M references/lib` or `preparation_unverified` for the others. Contract version of `contract.execution.preparation` kept at 2: runner.md already promised the reading included the submodules' files, so this is the code reaching the existing promise, and the contract text was only clarified. New `scenario.execution.unbound-preparation-submodule`.
- **I-bd3903** fixed in the same step: `req.execution.preparation-keeps-commit` now forbids changed or removed tracked files and untracked files the commit's Git does not ignore, in the checkout or a submodule; module.md and the contract semantics aligned.
- **I-082c7c (obvious-fix), one deviation from its suggested repair.** `measured` values are now refused with `invalid_check` unless they are a list or a tuple of strings; mappings, sets and iterators are refused (the Issue's impact: a mapping's keys deciding what is measured). I accept tuples as well as lists because Method's `measured_files` (module.method, outside this task) passes tuples; refusing tuples would break Method and need a change in another Module. The Spec now says a tuple is accepted as such a list. Test failed on the old code (mapping, set, iterator accepted).
- **I-527a7b (obvious-fix).** Saving the log and finishing the node are now separate suppression blocks; new `scenario.checks.service-interrupted` (existing test) and `scenario.checks.service-interrupted-unlogged` (new test, failed on the old code: node left `running`).
- **I-c5d4e3 (obvious-fix).** Checks file names must match the Kernel's Module identity pattern `^module\.[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)*$` (the one the workspace binding contract uses); the pattern is written out in service.md rather than linked, so Checks takes on no new reliance on the binding contract. Test (foo.json, check.a.json, module.json) failed on the old code.
- **I-df3dd3 (obvious-fix).** `Span.__exit__` counts `asyncio.CancelledError` as cancellation; timing.md now lists what ends a span's work by cancellation. Test failed on the old code (`error`).
- **Checks Spec Issues (I-11a5ac, I-26ff2c, I-2c2faa, I-48510d), all obvious-fix.** Scenarios split into single situations as suggested: `service-trace-write` (completed result), `service-trace-write-failed` (stale call), `service-trace-write-interrupted` (two checks, error during the second); the empty `trace_failures` case moved into `service-run` with an assertion. `command-output` split into `command-output`, `command-signal` (new test; 143 for SIGTERM verified against bubblewrap), `command-large-output` and `command-environment` (the env case was a separate test already). The selective and freshness scenarios now pass `tests` and `measured` explicitly and the prose says the service reads no Spec to find tests; Python test identities are `path::name` or `path::Class::name`.
- **I-550df5 (obvious-fix).** `preparation` evidence is now recorded with elapsed time and log also when the boundary cannot be set up and when a cancellation, interrupt or unexpected error ends the command (then the error goes on unchanged; a failed log write no longer replaces it). New scenarios `unbound-preparation-evidence` and `unbound-preparation-unbounded`; the test failed on the old code.
- **I-bb0d43 (obvious-fix).** `run_state` answers `running` whenever the run lock is held, then reads the result. Callers in module.workflows (`workflows/step.py`, `report.py`) keep working: they just see `running` for the short time between publication and the lock's release. New `scenario.execution.run-lock-result`; the test failed on the old code.
- **I-d632e2 (obvious-fix).** Composition keeps the stopping step's error whatever the status, so `validate_result` replaces an `ok` stop carrying an error with `invalid_result` that keeps the error as cause. New `scenario.execution.ok-with-error`; the test failed on the old code (the error vanished, status `ok`).
- **Execution Spec Issues (I-265464, I-444a38, I-641b1e, I-66369d, I-78ad2e, I-7f746b, I-8fbcb0, I-956bbd, I-a7d3a5), all obvious-fix**, fixed as their suggested repairs say, in requirements.md, runner.md and module.md. For I-641b1e and I-a7d3a5 the runner.md lock list and the module.md/runner.md availability sentences now name the failed-publication exception.
- **I-9b7c0d (obvious-fix), fix differs from the suggestion.** The inventory line "the run record of the latest worker launch" was not a misnamed `worker`: `RunContext.last_record` really holds that run record (Method's steps read it), but the Spec never listed the field. I kept the run-record mention, tied it to `last_record`, added `last_record` to the field table, and named `worker` separately as the worker result with the worker's claims. This removes the ambiguity the Issue describes without deleting a true statement.
- **I-b8724f (obvious-fix).** Split into single situations, each verified by the test that already exercised it: unbound-submodule-absent, unbound-runtime-not-linked, unbound-checkout-left (covers both the removed and setup-failed leftovers), bound-run-unprepared, unbound-preparation-unignored, unbound-preparation-invalid, command-not-operation, workspace-next-run, workspace-rebound, modules-from-binding, modules-removed-named, detach-unstartable, run-unrecorded-detached, final-trace-invalid, cancelled-late, inputs-refused. The BUT "a command that writes only what Git ignores leaves the run ok" was dropped from unbound-preparation-changed, since unbound-prepared states it; my own new unbound-preparation-submodule was split the same way (unbound-preparation-sparse).
- **I-baa45e (obvious-fix).** `module.execution` now `uses` `module.workers` relying on `req.workers.placement`, explained in module.md#uses-workers as a convention with no import and no part dependency. The existing include of `document.workers.launch` became redundant (CHK.includes.redundant) and was removed. `registry --write` refreshed `.concorde/specs.json`; that derived file may conflict with another task that also refreshes it, and regenerating it resolves such a conflict.

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T09:28:07Z

checks-execution-high delivered: delivery commit af764539315483ce1954521384cba2080b923550 on concorde/checks-execution-high (delivery run r-20261029T091911-delivery-edbb6e52; task-validation r-20261029T090958-task_validation-b345ea38 ready, no blocking finding). Full suite 1669 passed, 6 skipped; build --check and spec-validation clean (0 errors; the 5 warnings are pre-existing, in spec-tooling/spec/scenarios.md).

All 26 Issues in the task's resolves are fixed. None was already fixed, a duplicate or not real.

High, each shown by a test that failed on the old code:
- I-40b793 (Checks, preferred-fix). Fix chosen: directory inputs are walked with os.walk, and an input directory, or a directory below it, that cannot be listed is refused with the existing check_input_missing, naming the check, its Module and the directory, before any command; validate_checks refuses it too. I kept the existing code rather than adding a new one. File order is unchanged, so existing digests stay the same. New req.checks.input-measured-whole and scenario.checks.input-unreadable.
- I-e72fc9 (Execution, preferred-fix). Fix chosen: before the first preparation command, the runner finds every checked-out submodule (recursively) and its Git directory. Each repository is read on its own, with its pinned Git directory, against a fresh index of its own HEAD, counting new .gitignore files and its .git bytes. The superproject's status no longer reaches a submodule through its rewritable .git file (--ignore-submodules=all). A submodule that is not checked out must stay empty. Old code missed a hidden .gitignore at the submodule root and nested, and writes into an unpopulated submodule. Cost: about 1 s more on Concorde's 6 sparse references. contract.execution.preparation stays at version 2, since runner.md already promised the submodules' files were covered.

Decisions that differ from an Issue's suggested repair (my call, within the Issue's intent):
- I-082c7c: measured values must be a list or a tuple of strings; mappings, sets and iterators are refused. I accept tuples because Method's measured_files (module.method, outside this task) passes tuples. Accepting only lists would have needed a change in Method.
- I-9b7c0d: "the run record of the latest worker launch" was true. RunContext.last_record holds that run record, and Method reads it, but the Spec never listed it. I named both fields: worker holds the worker result (the worker's claims) and last_record holds the run record, and I added last_record to the field table, rather than deleting the run-record mention.
- I-baa45e: module.execution now uses module.workers, relying on req.workers.placement. The existing include of document.workers.launch became redundant (CHK.includes.redundant) and was removed. registry --write refreshed .concorde/specs.json. If another task also refreshes it, a merge conflict there is resolved by regenerating it.
- I-c5d4e3: checks file names must match the Kernel's Module identity pattern ^module\.[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)*$, written out in service.md.

Other obvious-fixes, as their Issues suggest: I-527a7b (an interrupted node ends even if its log cannot be saved), I-df3dd3 (asyncio.CancelledError counts as cancelled), I-550df5 (preparation evidence with elapsed time and log on cancellation and sandbox failure), I-bb0d43 (run_state is running while the run lock is held, even after the result is published; the callers in module.workflows keep working), I-d632e2 (an ok Stop with an error becomes invalid_result, keeping the error as its cause), I-bd3903, and the Spec-only fixes I-11a5ac, I-26ff2c, I-2c2faa, I-48510d, I-265464, I-444a38, I-641b1e, I-66369d, I-78ad2e, I-7f746b, I-8fbcb0, I-956bbd, I-a7d3a5 and I-b8724f. For I-b8724f I split 16 scenarios into single situations, each verified by the test that already exercised it.

No side effect resolves another open Issue that I know of. No escalation; nothing open for the developer. bubblewrap 0.4.0 and the checks-bwrap-compat work are untouched; the signal-ending test passed on this host's bubblewrap 0.4.0. Details are in the decision log.

## Closed: merged, 2026-10-29T09:28:36Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit af764539315483ce1954521384cba2080b923550 into main and closed it as merged. Nobody answers a report after that.
