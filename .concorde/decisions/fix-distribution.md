# Decision log: fix-distribution

Goal: Resolve the open non-decision Issues of module.distribution

## Brief (main agent, 2026-10-02)

Open Issues of this task's Modules, most severe first:

- I-32b6af7d5ce95306bcbfdafd06bcc568 (module.distribution, high, obvious-fix): The install scenario specifies obsolete workflow permissions
- I-bc6475b5dd595b84835ccc4dd67c2cf8 (module.distribution, medium, preferred-fix): Install recovery assumes stronger transactions than Spec core promises
- I-2071db60b05a5a8b85261ffb220d9c92 (module.distribution, medium, obvious-fix): Distribution relies on undeclared command and runtime providers
- I-fff7d5cfbb1556e79fe386bcf07f7165 (module.distribution, medium, obvious-fix): The configuration write restriction is narrower than the entry's promise
- I-c6a715f0026e57569c9e512d95f5520d (module.distribution, medium, obvious-fix): The command-routing description omits its validation exception
- I-ab80b2580b4551a0a93bb92430c7b651 (module.distribution, low, obvious-fix): The sole-workflow assertion lacks its input precondition
- I-fe1b32de932657b986ded6dcee104ef5 (module.distribution, low, obvious-fix): Command-launch scenarios omit the empty-task-list precondition
- I-bf910bc0c2545086b07dc6c8f091d840 (module.distribution, low, obvious-fix): Update's active-run refusal does not name the progress file of a run in the lobby
- I-df16c7b012825c598f6a0d947b1c6b05 (module.distribution, low, suggestion): Make the settings preflight description explicit
- I-0f25b826bc555c6ba9c388bad2bb83f6 (module.distribution, low, suggestion): Connect the project MCP server to the Main session collaboration
- I-c5ceba30ffa158eaa14181298dca3e47 (module.distribution, low, suggestion): Collect installer refusals in one reference
- I-b936d5204bfa516ea165578a50955700 (module.distribution, low, suggestion): Limit the overview's unchanged-project guarantee to preflight

The developer asked the main agent (2026-10-02) to resolve every Issue that does not need the
developer. This task takes the open Issues listed above, none of them decision-needed (the main
agent triages those separately). For each Issue:

1. Read it with `python3 scripts/concorde.py issues show <id>` and check that it still stands at
   your HEAD: several tasks merged on 2026-10-01/02 (issue-write-recovery, mcp-fresh-code,
   run-lock-before-records, workflow-lock-before-records, lock-recovery-followups). One already
   fixed is closed with `concorde issues close <id> --reason resolved --note … --evidence <commit>`;
   a duplicate with `--reason duplicate --duplicate-of <id>`.
2. Fix it by its tier: `obvious-fix` alone; `preferred-fix` with the fix you judge best, which
   you report; `suggestion` only when it clearly improves the Specs or code at small cost,
   otherwise leave it open and say why in your report.
3. Add every Issue you fixed to this task with `python3 scripts/concorde.py task resolve <task>
   <id>…`, so the merge closes it. Never add one you did not fix.

Rules: change only the Modules this task binds. A fix another Module needs, or a fix that turns
out to need a decision (it would change what a Module promises its users, contradict an earlier
decision of the developer, discard work, or loosen a boundary), is escalated, all together at the
end, after everything else is done; a problem you find in another Module is recorded as an Issue
of that Module. Do not touch module.workers, module.harness, module.execution, module.e2e or
module.dogfood-scenarios: task worker-git-isolation is changing them. Other tasks run in
parallel on module.issues, module.main-session, module.distribution, module.concorde and a group
of small Modules; each keeps to its own. Verify with build --check, spec-validation and the full
suite, then task-validation and delivery, and report: what you fixed (with the fix chosen for
each preferred-fix), what you closed as already resolved or duplicate, the suggestions you left
open and why, and the escalations.

## Addendum (main agent, 2026-10-02): decision-needed Issues decided by the main agent

The main agent triaged the decision-needed Issues and decided these within its authority (ordinary scope: each qualifies or documents a promise following existing decisions). Fix each with the decision given, then add it with `task resolve` like the others:

- I-64711110724957a0b8e5dbd8daa8b26c (installer and update output contract): add a contract from the current output: fields, nulls when nothing was installed before, update-only fields, exit 0 and its relation to the receipt.
- I-29d63aa9d81558cfaafc2deaa3154be0 (protocol-manifest flag modes): specify all four flag combinations as implemented, linking Spec core's manifest contract.
- I-f758e1cc77915514a0f465a1d41df5fc (update with an existing mark): keep the old mark until the new update succeeds; a success replaces it while keeping the oldest unvalidated before-state; limit 'no mark' in the recovery text to initially unmarked projects.
- I-b78db462211f5578a62aaa8e68397870 (repeated parameterized includes): refuse, naming both include chains, as prompt_resolver.py already does; text plus a diamond scenario.
- I-558aded6b7b35a7a98ae5cdbbdc4a949 (glossary import after init): Distribution's adapter adds the CLAUDE.md import after a successful init --apply; a failure reports guidance_failed with recovery by concorde update or re-running guidance, never by re-running init.
Not yours: I-086f89ee787d54bb9140c65360058345 needs a Tasks change and goes to a later task.

## Task session (2026-10-02): decisions taken without the developer

- Every listed Issue still stood at the task's base (none closed as already resolved or duplicate).
- `init-references.py` failed once (exit 1) while other worktrees prepared in parallel; it
  succeeded on a second run. Not a defect of this task.
- I-bc6475b5 (preferred-fix): chose to align the recovery text with Spec core's file-transaction
  limits (a killed installer or a refused restore can leave the root metadata naming the
  installation realization without the entry's explaining paragraph; a repeated install does not
  write that paragraph; repair by removing the realization record and installing again) AND to
  stop discarding the binding failure: the installer now returns Spec core's error record as
  `binding_error` in its printed result (never in the receipt file), with a scenario and test.
  Rejected: changing `bind_installation` to repair the paragraph, which is module.spec's code.
- I-2071db60: declared `uses` of module.tasks (concept.task, concept.task-record,
  contract.tasks.record), module.issues (concept.issue, contract.issues.receipt), module.spec-mcp
  (req.spec-mcp.one-root, req.spec-mcp.stdio-only) and module.workers (worker-backend,
  worker-configuration, model-map, progress-file, req.workers.pi-sandbox), each with its prose
  section; module.spec gained concept.file-transaction and contract.spec.error. Only
  Distribution's own metadata changed; Workers' files are untouched.
- Suggestions: all four fixed, each small: I-df16c7b0 (settings preflight wording), I-0f25b826
  (project MCP server in the Main session collaboration, relies_on concept.project-mcp-server),
  I-c5ceba30 (one refusal table in module.md#refusals, with a test that checks it against every
  code the installer, its tools, update and Dogfooding's source check raise, and each code's
  reason), I-b936d520 (overview guarantee limited to the checks and the download).
- Found while building the refusal table: `mcp_config_invalid` was classified `environment`
  although only a different project corrects it, like `settings_invalid`; added it to
  INPUT_CODES (obvious fix inside the Module, no Issue filed).
- I-bf910bc0: `_run_progress` also reads the lobby; the busy test adds a lobby run, and the
  Spec and scenario name the lobby.
- I-64711110 (main agent's decision): new document specs/concorde/distribution/contracts.md with
  contract.distribution.install-result and contract.distribution.update-result, from the current
  output (binding_error included); a test validates real install-concorde.py and `concorde update`
  output against them.
- I-29d63aa9: specified the four flag combinations as implemented, including that
  `--bind-project` alone with differing digests writes the binding and then fails with
  `protocol_mismatch` while refreshing the copy (left unchanged, as implemented); scenario
  protocol-manifest-single-flag and test.
- I-f758e1cc: an update of a still-marked project keeps the earlier mark's from-version,
  from-commit and Protocol binding before; the mark is now written via `.partial` + rename (and
  the partial removed on failure) so a failure leaves the earlier mark intact. New requirement
  req.distribution.update-mark-kept and scenario update-marked-again.
- I-b78db462: Spec text and diamond scenario for the existing CONCORDE-PROMPT-DIAMOND-001 refusal.
- I-558aded6: the `init` entry point now catches a failed CLAUDE.md amendment after Spec core's
  initialization and returns `failed` with `guidance_failed` (reason/remediation given explicitly,
  since the code is Distribution's and not in Spec core's registry), keeping init's result, the OS
  error as cause; recovery `concorde update` or the installer again. Command table and
  realization.distribution.command now name both exceptions (spec-validation, init --apply).

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T17:17:49Z

fix-distribution delivered: delivery commit 7e18212d on concorde/fix-distribution (steps 6670023b, aa1176df). build --check, spec-validation (no findings), full suite (901 passed, 4 skipped) and task-validation (ready, nothing blocking) all pass.

Resolved, all 17 added with task resolve (none was already fixed or a duplicate):
- obvious-fix: I-32b6af7d (install scenario now names Workflow(concorde-brownfield), mcp__concorde__workflow_step and Bash(... workflow report:*)), I-2071db60 (declared uses of Tasks, Issues, Spec MCP server and Workers, each with its prose section and relies_on; only Distribution's metadata changed), I-fff7d5cf (installer-no-specs protects the whole project configuration except the binding in update mode), I-c6a715f0 (spec-validation exception stated in the command table and the entry points), I-ab80b258 and I-fe1b32de (scenario preconditions), I-bf910bc0 (the busy refusal now reads the lobby; test and Spec updated).
- preferred-fix I-bc6475b5: chose a Spec plus code fix. The recovery text now follows Spec core's file-transaction limits (a killed installer or a refused restore can leave the root metadata naming the installation realization without its paragraph, and a repeated install does not repair that; the developer removes the realization and installs again). The installer also stops discarding a refused binding: its printed result carries Spec core's error record as binding_error (never in the receipt file). I did not change bind_installation itself, because it is module.spec's code.
- suggestions, all four fixed because each was small: I-df16c7b0, I-0f25b826 (project MCP server in the Main session collaboration), I-c5ceba30 (one refusal table, with a test checking it against every code raised and each code's reason), I-b936d520.
- your decisions: I-64711110 (new specs/concorde/distribution/contracts.md with contract.distribution.install-result and update-result, tested against real output), I-29d63aa9 (four flag modes as implemented; note that --bind-project alone with differing digests writes the binding and then fails with protocol_mismatch, leaving the copy unchanged, which is documented as implemented), I-f758e1cc (new req.distribution.update-mark-kept: the earlier mark's before-state is kept and the mark is now replaced atomically), I-b78db462 (text plus a diamond scenario and test), I-558aded6 (init adapter returns failed/guidance_failed and keeps init's result; recovery is concorde update or the installer again).

Extra fix inside the Module: mcp_config_invalid was classified as reason environment; it is now input, like settings_invalid.

Open: nothing from this task. No escalations. I-086f89ee was left alone as instructed. All decisions are in the decision log.

## Closed: merged, 2026-10-02T02:16:31Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 7e18212d415eeab5f4f997b6e7f9901fe5c1e409 into main and closed it as merged. Nobody answers a report after that.
