# Decision log: fix-workers

Goal: Resolve the open Issues of module.workers, carrying out the main agent's decisions

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-c45e5bd967ca5ac8ac2f2e2bf56816ff (module.workers, high, preferred-fix): The shared brief blocks Spec reviewers on reportable gaps
- I-1be01905aee65e14a405635e6091cec5 (module.workers, high, preferred-fix): The launch interface cannot express the promised project interpreter
- I-9c0126964e99564b940173c1c460ecc3 (module.workers, high, preferred-fix): The launch interface does not define promised check-log access
- I-88e8ba4c962e51db9b8dfa9fdbd52e61 (module.workers, medium, decision-needed): Whole-configuration map checking has no defined invocation policy
- I-6a51557fc91b5e40bfcbfc78a09ecdda (module.workers, medium, decision-needed): The canonical audit evidence record lacks a defined structure
- I-f496abcfc8df5f95a0760c1039a38c49 (module.workers, medium, decision-needed): The returned run record has no contract for round contents
- I-d3c5b5cd7fbd5609a8cb8773543cc573 (module.workers, medium, decision-needed): Deletion finalization leaves repeat and failure outcomes undefined
- I-6cdee229fa545e5cbae8a1339b06176d (module.workers, medium, decision-needed): The read-denial promise conflicts with Harness runtime exceptions
- I-d6cb5b62ea545caba030578b7cc3afb5 (module.workers, medium, preferred-fix): Pre-launch configuration refusals lack a canonical error-link contract
- I-6b763384dd885f03bebc8885d4337de5 (module.workers, medium, preferred-fix): Deletion-path semantics conflict with the result-path instruction
- I-a01565a2bfd85564969709018440a4ea (module.workers, medium, obvious-fix): Workers omits the Check execution service contract from its context
- I-27866df5cd2854e3a61091a1fc402bfd (module.workers, medium, obvious-fix): Task-type admission and refusal are combined into one obligation
- I-58c4ec4acb7c5b7fa51a95b2585c3d30 (module.workers, medium, obvious-fix): Pi limit failures inherit a Claude-only error cause
- I-c890cec529065206b89ab3cb1830d43d (module.workers, medium, obvious-fix): The launch command requires a budget whose default is unset
- I-5db71f50cfef5254a1bb90c83e5c2f0d (module.workers, medium, obvious-fix): Model-map remediation is incorrectly required for every refusal
- I-8d00867d727a53578107e9d6d5254a28 (module.workers, medium, obvious-fix): Audit violations require a worker error even for valid ok results
- I-46edf1ef313b5b3192e91744fba572b9 (module.workers, low, decision-needed): The live test of a worker's detailed error fails: the worker gives the reason input
- I-3399acceb2d3530d956c24df76173ee9 (module.workers, low, obvious-fix): The path-format requirement combines two briefing obligations
- I-41e92fbe45455ae5836146048883ba0b (module.workers, low, obvious-fix): Several requirements bundle independent controls and lifecycle actions
- I-0543ca13f809577f8508098d747e1fed (module.workers, low, suggestion): The limits explanation points outside Workers' selected context
- I-30817099f87a59b9bc599e29f1a12d9e (module.workers, low, suggestion): The collaborator diagram omits Tracing
- I-6c3713337e3754e38e8a94ed7ce227a9 (module.workers, low, suggestion): The mechanics leave outside-run launches unexplained
- I-45c4418a24fd5fa486eae1132e3c69f8 (module.workers, low, suggestion): Clarify which default makes backend_source null

Decisions (main agent, ordinary scope):
- I-88e8ba4c962e51db9b8dfa9fdbd52e61: check every worker of the Operation against the model map at
  admission, before the first worker launches, with one model_unmapped refusal listing every gap.
- I-6a51557fc91b5e40bfcbfc78a09ecdda: define the item shapes of a completed audit's `changed` and
  `violations` from the current audit code (a path with its kind: changed, deleted or Git state;
  a glossary item with its owners before and after) and add a nonempty example.
- I-f496abcfc8df5f95a0760c1039a38c49: the value returned to the Operation is the run node's
  content plus an ordered `rounds` list of round-node contents, distinct from the persisted
  trace.json.
- I-d3c5b5cd7fbd5609a8cb8773543cc573: duplicate deletion targets are removed, a missing target is
  recorded as already absent, a failed deletion does not stop the others; the run then ends
  failed with an error chain listing what was and was not deleted.
- I-6cdee229fa545e5cbae8a1339b06176d: qualify req.workers.read-denials: paths under the runtime
  paths of the tracked workers.json stay readable, and changing that list is a reviewed change of
  the worker configuration. (The developer narrowed the root's access promise the same day, I-09f5bed3.)
- I-46edf1ef313b5b3192e91744fba572b9: sharpen prompts/workers/common/errors.md so that a refused
  write is reason `permission`; keep the test; accept `input` in the test only if the sharpened
  guidance still fails, and say so.

The developer asked the main agent (2026-10-02) to resolve every Issue that does not need the
developer. This task takes the open Issues listed above. The decision-needed ones among them are
already decided: their decisions are under "Decisions" below, and you carry them out as given.

Start with the full suite on your fresh worktree as a baseline: six tasks merged into main just
before this task opened, and only build and spec-validation ran on the merged result. Record any
failure in the decision log; fix it here when it lies in your Modules, otherwise record it as an
Issue of its Module.

For each Issue:
1. Read it with `python3 scripts/concorde.py issues show <id>` and check that it still stands at
   your HEAD. One already fixed is closed with `concorde issues close <id> --reason resolved
   --note … --evidence <commit>`; a duplicate with `--reason duplicate --duplicate-of <id>`.
2. Fix it by its tier: `obvious-fix` alone; `preferred-fix` with the fix you judge best, which you
   report; `suggestion` only when it clearly improves the Specs or code at small cost, otherwise
   leave it open and say why; `decision-needed` as decided below.
3. Add every Issue you fixed with `python3 scripts/concorde.py task resolve <task> <id>…`, so the
   merge closes it. Never add one you did not fix.

Rules: change only the Modules this task binds. A fix another Module needs, or a fix that turns
out to need a further decision (it would change what a Module promises its users beyond the
decisions below, contradict an earlier decision of the developer, discard work, or loosen a
boundary), is escalated, all together at the end, after everything else is done; a problem you
find in another Module is recorded as an Issue of that Module. Four other tasks run in parallel,
each on its own Modules: fix-execution-root (execution, concorde), fix-workers (workers), fix-e2e
(e2e), merge-update-followups (main-session, tasks, tracing, distribution, task-session,
coordination), fix-delivery-and-small (delivery, adoption, spec-mcp, code-review, spec-review,
operations). module.harness is bound by none: record Harness changes as Issues. Verify with build
--check, spec-validation and the full suite, then task-validation and delivery, and report: what
you fixed (with the fix chosen for each preferred-fix), what you closed as already resolved or
duplicate, the suggestions you left open and why, the baseline result and the escalations.

## Task session (2026-10-02)

- Baseline at 84994940 (fresh worktree, prepared with init-references, uv sync, npm ci, build):
  full suite `.venv/bin/python -m pytest` 922 passed, 5 skipped, 0 failed. Build succeeded.
- Preferred-fix choices:
  - I-c45e5bd9 (brief blocks Spec reviewers): the brief's Spec rule gets a case of its own for
    `review-spec` and `review-architecture`: report a missing promise or a missing document as a
    finding and go on, `blocked` only when the worker cannot review at all (workers.py spec_rule,
    module.md "The brief", scenario.workers.brief-review-gaps). Chosen over moving the rule into
    Spec review's prompts because the shared brief must not contradict them, and only Spec review
    launches these two task types.
  - I-1be01905 (project interpreter): the code already prepends the interpreter's directory to the
    worker's PATH on both backends; the Spec now has a `project interpreter` input, the PATH rows
    of both environments, "Reading beside the grant", two requirements and a scenario. The caller
    (Execution's step) resolves the interpreter and lists its read roots among the runtime paths;
    Workers never resolves it. Process-wide PATH is never changed.
  - I-9c012609 (check-log access): chose the "explicit existing-input rule" over a new task-artifact
    input: the runtime paths input is defined as every read-only path beside the grant, exactly as
    the caller lists them, including host material it admits for one run (the folder of its own
    check logs, never the surrounding trace); the Harness already enforces them on both backends.
    Recorded through the settings digest, no new trace field. req.workers.runtime-paths-exact.
  - I-d6cb5b62 (resolver refusals): new launch.md section "Refusals before a run" with every code,
    what its message names and its reason (matching models.HANDLING), no run or record, and the
    caller's component link with actor `Workers (worker configuration)`; req.workers.refusal-reason.
  - I-6b763384 (deletion paths): relative is the canonical producer form; absolute stays accepted
    as host compatibility, normalized and refused when outside the worktree (launch.md "Proposed
    deletions", worker-result semantics).
- Decided Issues carried out:
  - I-88e8ba4c: models.check_mapped gained `operation`; Spec says the Operation's run asks for it
    at admission. The call itself lies outside this task's Modules: recorded as
    I-815328180f205b579a0af51869e10731 (module.operations, code in src/concorde/execution/context.py).
  - I-6a51557f: audit item shapes defined from the code (verdict, changed paths, violation strings
    HEAD/index, path, `<path> (deleted)`, glossary entry with owners); the only code change is the
    ` (deleted)` suffix, so the kind is visible. Kept strings rather than objects because
    Execution's evidence joins them as strings. Round trace contract v3; nonempty example in the
    returned run record contract.
  - I-f496abcf: DEVIATION to report. A new contract.workers.worker-run-record defines the returned
    value, distinct from trace.json, holding the run node's content and the ordered rounds. Its
    round items keep today's returned shape (agent report under `claude`/`pi` at top level, a key
    absent when that step did not happen, absolute check logs, duration and usage), and `tools`
    stays the comma list, instead of literal round-node contents: Implementation, Understanding,
    Specification, Code review and Adoption code and tests read `.get("checks") is None`, absolute
    logs and the comma `tools`; changing them is outside this task's Modules.
  - I-d3c5b5cd: repeated targets dropped, absent ones in new `deletions_absent`, failures in new
    `deletions_failed`, the others still attempted, run ends `failed` with `deletion_failed`
    (worker's link as cause when it has one). Run trace contract v4.
  - I-6cdee229: req.workers.read-denials excludes paths below the runtime paths; prose says the
    tracked workers.json `runtime` list decides them and changing it is a reviewed change.
  - I-46edf1ef: sharpened prompts/workers/common/errors.md (a refused read or write is always
    `permission`; `input` only for a self-contradictory task). Test unchanged; live run
    (CONCORDE_LIVE_CLAUDE=1, claude-haiku-4-5) passed 3 of 3.
- Suggestions: fixed all four (I-0543ca13 link to own contract, I-30817099 Tracing in diagram,
  I-6c3713337 direct host calls explained, I-45c4418a backend_source wording), each a few lines.
- Recorded I-cdea0b0e8dc858abab58cec25d37c2f4 (module.harness, low): Harness's runtime-path wording
  is narrower than Workers' input.

## Escalated to the main agent, 2026-10-02T02:42:19Z

- **task-session** task session (task fix-workers): `cross_module_followups`
  Two points of this task lie outside module.workers. (1) I-88e8ba4c: Workers now offers models.check_mapped(config, environ, operation=...) and its Spec says the Operation's run asks for it at admission, but the call belongs to the Operation's run (Operations' workers.md, code in src/concorde/execution/context.py); recorded as I-815328180f205b579a0af51869e10731 (module.operations, obvious-fix, medium). Until it is fixed, the whole-Operation check exists but nothing runs it. (2) I-f496abcf deviation: contract.workers.worker-run-record defines the returned value distinct from trace.json, the run node's content plus the ordered rounds, but each round keeps today's returned shape (agent report under claude/pi, absent keys when a step did not happen, absolute check logs, duration and usage) and tools stays the comma list, rather than literal round-node contents, because Implementation, Understanding, Specification, Code review and Adoption code and tests rely on that shape. Also recorded: I-cdea0b0e8dc858abab58cec25d37c2f4 (module.harness, low), runtime-path wording narrower than Workers' input.
  Not handled here (scope): The admission call and any change of the returned round shape touch module.operations, module.execution and the Operation providers, which this task does not bind.
  Options: Open a task for module.operations (and module.execution) to fix I-815328180f205b579a0af51869e10731; Accept the I-f496 returned-record shape as delivered; Ask for literal round-node contents, which needs a task over the Operation providers
  Recommendation: Accept the delivered returned-record shape, and fix I-81532818 in a later Operations/Execution task; neither blocks merging fix-workers.

```json
{
  "level": "task-session",
  "actor": "task session (task fix-workers)",
  "code": "cross_module_followups",
  "detail": "Two points of this task lie outside module.workers. (1) I-88e8ba4c: Workers now offers models.check_mapped(config, environ, operation=...) and its Spec says the Operation's run asks for it at admission, but the call belongs to the Operation's run (Operations' workers.md, code in src/concorde/execution/context.py); recorded as I-815328180f205b579a0af51869e10731 (module.operations, obvious-fix, medium). Until it is fixed, the whole-Operation check exists but nothing runs it. (2) I-f496abcf deviation: contract.workers.worker-run-record defines the returned value distinct from trace.json, the run node's content plus the ordered rounds, but each round keeps today's returned shape (agent report under claude/pi, absent keys when a step did not happen, absolute check logs, duration and usage) and tools stays the comma list, rather than literal round-node contents, because Implementation, Understanding, Specification, Code review and Adoption code and tests rely on that shape. Also recorded: I-cdea0b0e8dc858abab58cec25d37c2f4 (module.harness, low), runtime-path wording narrower than Workers' input.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "The admission call and any change of the returned round shape touch module.operations, module.execution and the Operation providers, which this task does not bind."
  },
  "options": [
    "Open a task for module.operations (and module.execution) to fix I-815328180f205b579a0af51869e10731",
    "Accept the I-f496 returned-record shape as delivered",
    "Ask for literal round-node contents, which needs a task over the Operation providers"
  ],
  "recommendation": "Accept the delivered returned-record shape, and fix I-81532818 in a later Operations/Execution task; neither blocks merging fix-workers.",
  "causes": []
}
```

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T02:42:32Z

fix-workers delivered: delivery commit 6122514c on concorde/fix-workers (work commit 2b99235a). Baseline at 84994940: full suite 922 passed, 5 skipped, no failures. Final: build --check and spec-validation pass (0 errors; the one warning is concept.task-brief, Main session's, which was already there), full suite 933 passed, 5 skipped, task-validation ready.

Resolves all 23 open Workers Issues (added with task resolve). None was already fixed or a duplicate.
Preferred-fix choices:
- I-c45e5bd9: the brief has its own rule for review-spec and review-architecture workers: report a missing promise or a missing document as a finding and go on, and end blocked only when they cannot review at all (code and entry).
- I-1be01905: the code already put the interpreter first on PATH. The Spec now has a project-interpreter input, a PATH row in both backends, two requirements and scenarios. The caller resolves the interpreter and lists its read roots.
- I-9c012609: I defined the existing runtime-paths input as every read-only path beside the grant, exactly as the caller lists them, including host material admitted for one run such as the folder of its check logs. I did not add a new artifact input; the Harness already enforces these paths on both backends.
- I-d6cb5b62: new section "Refusals before a run" listing the 8 codes, what each message names and each reason; no run or record exists for them; the caller wraps them in a component link "Workers (worker configuration)".
- I-6b763384: relative paths are the canonical form; absolute paths are still accepted, normalized, and refused when outside the worktree.

Decided Issues, carried out as you decided:
- I-88e8 (check_mapped now takes the Operation).
- I-6a51 (audit record defined: verdict, changed, and violation strings, with the new suffix " (deleted)").
- I-d3c5 (deletions_absent, deletions_failed, deletion_failed; run-trace contract v4).
- I-6cde (read denials exclude the runtime paths; the tracked runtime list decides them).
- I-46ed (sharpened errors.md: a refused read or write is permission. The test is unchanged, and the live run with Haiku passed 3 of 3).
- I-f496: carried out with a deviation, see escalation 1.

All 4 suggestions fixed at small cost (I-0543, I-3081, I-6c37, I-45c4).

New Issues recorded:
- I-815328180f205b579a0af51869e10731 (module.operations, medium): no code calls the admission-time map check yet.
- I-cdea0b0e8dc858abab58cec25d37c2f4 (module.harness, low): the Harness's runtime-path wording is narrower than Workers' input.

Escalation 1 (recommend accepting; neither point blocks the merge):
- task-session task session (task fix-workers): cross_module_followups. (1) The I-88e8 call site belongs to Operations/Execution (I-81532818). (2) For I-f496, the returned run record's rounds keep today's returned shape and tools stays a comma list, rather than literal round-node contents, because other Modules' code and tests rely on that shape. Options: open an Operations/Execution task for I-81532818; accept the shape; or ask for literal contents, which needs a task over the Operation providers.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-02T02:42:54Z

Escalation 1 (cross_module_followups), decided by the main agent: (1) I-815328180f205b579a0af51869e10731 goes to a later task on module.operations/module.execution; (2) the returned run record keeps today's round shape and the comma-list tools, as you chose; the deviation from the I-f496abcf decision is accepted. Merging now.

## Closed: merged, 2026-10-02T02:42:54Z
