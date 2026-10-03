# Decision log: parts-review

Goal: Review the code of every Module the parts refactor changed against its Specs with Module reviews run in this task's built worktree, verify each finding, record the verified ones as Issues, and change no Spec or code

## Brief (main agent, 2026-10-03)

### Context

The developer decided (2026-10-03) to split Concorde into independently installable parts. The
whole refactor is done on the integration branch `parts-split` (the primary worktree is on it;
`main` is untouched, 158 commits behind): parts-spec, parts-layout, parts-kernel, parts-issues,
parts-worker-harness, parts-coordination, parts-execution, parts-workflow, parts-registrations,
parts-guidance, parts-install (decision logs in `.concorde/decisions/`). Before merging it into
`main`, the developer chose an overall review: **find the problems and record them as Issues; fix
nothing in this task.** The developer decides on fixes afterwards.

An unbound change review the main agent ran first from the primary worktree
(`r-20261003T031022-code_review-4bd7e4f8`, `.concorde/unbound/` of the primary worktree) failed:
one worker had to review all 33 Modules' change at once, the unbound checkout has no build so the
configured checks failed in their fixtures (`no build found`), and the worker stopped claiming that
the `concorde_result` schema required `earlier` (it does not: the transcript shows `earlier`
optional). It did report one concrete defect worth verifying: in `src/concorde/distribution/install.py`
(~833-892) `concorde update` computes the left-out d2 / Python dependencies with `_left_out(previous,
chosen)` where `chosen` already contains the newly requested `--parts`, so an update adding a part
that needs d2 or `langgraph` may keep them left out, against Distribution's module text (~609-612).
A spec_panel of the parts' top Modules runs in parallel from the primary worktree; you do not
review Specs as such.

### What this task does

1. Prepare the worktree as usual (references, `uv sync`, `npm ci`, build), so the configured checks
   run for real.
2. Run Module reviews (`concorde run code_review --scope module --modules ...`) over every Module
   whose code the refactor changed, in batches you choose (e.g. by part), one run at a time in this
   workspace: module.spec, module.spec-mcp, module.views, module.spec-tooling, module.kernel,
   module.tracing, module.worker-harness, module.harness, module.workers, module.execution,
   module.operations, module.commands, module.checks, module.workflows, module.issues,
   module.tasks, module.task-session, module.main-session, module.method, module.understanding,
   module.specification, module.implementation, module.code-review, module.spec-review,
   module.adoption, module.validation, module.delivery, module.scaffold, module.distribution,
   module.dogfooding, module.e2e, module.dogfood-scenarios, module.concorde.
3. Verify every finding the reviews report (they record Issues themselves): read the code and Spec
   it cites; close with `not-actionable` (and a note) or `duplicate` what does not hold, append to
   an existing Issue rather than duplicating, and keep tier and severity honest. Verify the
   installer defect above and record it as an Issue if it holds.
4. Change no Spec or code. Record every non-ok run and every judgement in the decision log. When
   done, report a summary: per part, the Issues that stand with severity and tier, and anything
   systemic (e.g. a coupling the parts directions should forbid but the dependency test misses).
   The main agent will close this task as completed (no delivery needed).

Model spend needs no permission. Do not change the worker configuration.

## Task session (2026-10-03)

- Worktree prepared (init-references, uv sync, npm ci, build): ok.
- Verified the installer defect from the brief: `update()` passes `chosen` (receipt parts plus
  `--parts`) to `_left_out`, so an update adding a part that needs d2 or a Python dependency to an
  install without such a part keeps them left out, against Distribution's module text (Updating,
  step 1). Recorded as I-0a32055284805ea685b1f4bd0d909059 (module.distribution, obvious-fix,
  medium: an added part fails at run time, reinstall is the workaround).
- Batches (one `code_review --scope module` run at a time; module scope launches one reviewer per
  Module, so batch size only groups the runs): spec (spec, spec-mcp, views, spec-tooling); kernel
  (kernel, tracing); worker-harness (worker-harness, harness, workers); execution (execution,
  operations, commands, checks); workflows+issues; coordination (tasks, task-session,
  main-session); method A (method, understanding, specification, implementation, code-review);
  method B (spec-review, adoption, validation, delivery, scaffold); distribution and the rest
  (distribution, dogfooding, e2e, dogfood-scenarios, concorde).
- Run r-20261003T032159-code_review-6dd40e26 (spec part) ended `failed` / verdict `incomplete`:
  module.spec's reviewer returned 29 findings, none reported because one location
  (`tests/concorde/spec/test_initialize.py:545-602`) lies beyond the file's end
  (`unresolved_evidence`); spec-mcp (5), views (17) and spec-tooling (1) findings were reported as
  Issues. Decision: rather than rerun module.spec's review, verify its 29 findings from the run
  result and record the verified ones as Issues myself; verification is delegated to subagents per
  Module, which close what does not hold.
- Verified spec-mcp/spec-tooling findings (run r-20261003T032159-...): standing I-5108bf68 (preferred-fix/medium,
  malformed tools/call kills the stdio session), I-6e8a2240 (obvious-fix/low, corrected from medium),
  I-c7bbcafb (obvious-fix/low, corrected), I-e9a40f5c (obvious-fix/low), I-aeb43288 (obvious-fix/low,
  corrected: only the skill's "Project terms" sentence lacks the coordination-absent case; task-session.md
  is composed only with Coordination). Closed not-actionable: I-607e69e5 (non-file root is no directory, as
  the Session contract says).
- Verified module.views findings (17): 16 hold, 12 of them with tier/severity corrected downward (the reviewer
  inflated "failed instead of invalid" diagnostics and a microsecond scaffold race, I-34e0959e, from critical to
  low). Standing at medium: I-c18683973 (linked task worktrees never find the origin repository),
  I-2a6a5560 (collection id `user` collides with the user-docs plugin id); the rest low. Closed not-actionable:
  I-2b40a24c (route rule binds extension authors, not the pipeline). Root cause shared by 4 scaffold Issues:
  propose and apply run different admission subsets.
- Verified module.spec's 29 unreported findings and recorded all 29 as new Issues (each holds at least in part;
  report_key spec-review-<slug>), severities lowered where inflated: medium I-44d15d2f (init apply flattens the
  proposal without validate_typed), I-926dc4e0 (malformed metadata aborts validation), I-69ef9269 (fatal load
  errors not fatal), I-6a01a131 (grant directory entry as raw prefix widens rw), I-4d613f5d (.concorde/ and
  generated/ entries grantable); 4 Spec conflicts (I-618d6b0e, I-93a63840, I-79689f15, I-e193e36a, the last
  decision-needed); the rest low. Systemic: Spec core's own copies of Kernel utilities have drifted
  (schema anyOf, JSON decode); grant computation trusts declarations only validation refuses.
- Main agent's note (session now "项目架构分离建议"): I-85a1e885 (blank `earlier` loses spec_review findings);
  gateway_concurrency_limit seen in its spec_panel. Observed here: code_review's reviewers also write
  placeholders (`earlier: "none"`/`"new"`), which code_review accepts as any string and lists under
  `earlier_issues.ignored`, so no finding is lost in these runs.
- Run r-20261003T035159-code_review-dc0efdcc (kernel + worker-harness parts) ended `failed` / `incomplete`:
  module.kernel's pi reviewer failed with `gateway_concurrency_limit` (pi_failed), probably from my three
  verification subagents plus the main agent's spec_panel running at once. tracing (13), worker-harness (1),
  harness (9), workers (16) findings were reported as Issues. Decision: rerun module.kernel in the next batch
  and keep at most two verification subagents running while a review runs.
- Main agent asked (2026-10-03) to classify every standing Issue as regression of the parts refactor or
  pre-existing on main; verifiers now check `git show main:<old path>`; the spec-part Issues get a separate
  classification pass.
- Verified tracing (13) + worker-harness (1): 11 hold (9 corrected down), 3 closed not-actionable
  (I-6ff4f9e5, I-74580afa, I-53a2ff0b). Regressions: I-f8772d79 (TraceRoot.place unchecked, suggestion/low),
  I-941300cf (node kinds hard-coded in the Kernel although the contract now says parts register them,
  preferred-fix/low), I-0542bfbf (worker-harness guidance names absent parts, obvious-fix/low); the rest
  pre-existing (medium: I-6e58eaae, I-3cb1625c, I-f2e66c2a, I-335b9728). Installer I-0a320552: regression
  (main has no parts). Systemic: the Kernel's tracing still hard-codes every part's node kinds.
- Classified the 50 standing spec-part Issues: regressions I-efdb6346, I-48fb0384, I-e193e36a (decision-needed),
  I-e9a40f5c, I-aeb43288 (all low); the other 45 pre-existing on main (code moved or unchanged), medium ones
  I-44d15d2f, I-926dc4e0, I-69ef9269, I-6a01a131, I-4d613f5d, I-c1868397, I-2a6a5560, I-5108bf68.
- Verified harness (9) + workers (16): 24 hold, 23 corrected (reviewer rated mistake-only/fail-closed cases as
  critical security holes against Harness's own "mistakes, not malice"), I-709191e5 closed not-actionable. All
  pre-existing (worker_harness code identical to main's harness/), except I-5b2ba600 mixed (extra-field part
  from the new grant-input contract, low). Medium: I-ff5160fb (decision-needed), I-db8baa0a, I-2d7bb84c,
  I-2d4dfa0a, I-657d8b78, I-6b51b739, I-d1790584.
- Run r-20261003T041234-code_review-72e86ad6 (kernel rerun + execution part): ok, changes_required; kernel 17,
  execution 12, operations 2, commands 2, checks 15 findings reported as Issues.
- Verified kernel (17) + operations (2) + commands (2): 19 hold (most lowered), I-2ae7302d closed not-actionable,
  I-f7f9877d closed duplicate of I-3f709b30; new I-69b58414 (Kernel decode('1e999') -> inf, pre-existing, twin
  of I-455cef95). Regressions (all low): I-97dec858, I-529eee55, I-39a101dd, I-f16be8b2, I-b7008b86 (Kernel
  contract written fresh and dropped Spec core's symlink and depth promises), I-e4ba7e37, I-3f709b30
  (decision-needed), I-c5588827 (Commands Spec still says the catalog routes the CLI; fix the Spec).
- Verified execution (12) + checks (15): 24 hold, 3 closed not-actionable (I-c6748520, I-2818ddb7, I-bf7eb0a3).
  Regressions (low): I-b0e467d3, I-d2dec046, I-078aae79 (rewritten checks.py). Execution's medium Issues are
  all pre-existing.
- Recorded I-e6240816 (module.checks, preferred-fix/low, regression): validate_checks has no caller though
  service.md says task-validation calls it; main's project-wide check-input preflight in spec-validation was
  removed with nothing in its place.
- Run r-20261003T043108-code_review-b638d3d3 (workflow, issues, coordination) ended `failed` / `incomplete`:
  module.issues (9 findings) and module.tasks (18) lost all findings to `unresolved_evidence` (line ranges a few
  lines past a file's end); workflows (13), task-session (4), main-session (9) reported. Decision: as for
  module.spec, verify the lost findings from the run result and record the verified ones myself. Recorded the
  pattern as I-82b9bb29 (module.code-review, decision-needed/medium, limitation, pre-existing on main).
- Verified workflows (13): all hold, 11 corrected. Regressions: I-c66d7124 (medium: a superseded malformed
  workflow object fails every later report), I-60bd5fea (medium: step-output contract text says the answers file
  is a JSON list, code and Adoption use {"answers": [...]}), I-cfb021e5 (low: guidance assumes Coordination);
  10 pre-existing (6 medium).
- Verified module.tasks' 18 unreported findings: 16 hold and were recorded as new Issues (most lowered from
  high/critical), 2 do not hold (unreachable ended-task worktree; open_tasks already specified). Regressions
  (low): I-7b509b56, I-89564ab0 (Issue closure now runs the merged `concorde` process, against
  req.tasks.merge-own-sources), I-034996be. Pre-existing medium: I-a01870e9, I-fea06249.
- Verified task-session (4) + main-session (9): all hold, all corrected down. Regressions (low): I-3b761687,
  I-ac11047a, I-dfe59128 (decision-needed). Recorded module.issues' 9 unreported findings: 8 hold (new Issues),
  1 does not. Regressions: I-3ad5326c (medium: KernelError is no ValueError, so a symlinked record aborts
  `issues check`), I-01f76edf (low), I-1b9c2a57 (mixed, low). Pre-existing medium: I-e189786a, I-688f5308,
  I-dbf1b166.
- Run r-20261003T045929-code_review-a21d3726 (method A): ok, changes_required; method 4, understanding 2,
  specification 4, implementation 4, code-review 3 findings reported.
- KernelError-vs-ValueError sweep (AST scans of all handlers, current and main): no case beyond I-3ad5326c and
  I-1b9c2a57; the parts catch KernelError at their boundaries. Noted, not recorded (low, generic
  unexpected_error on a malformed checks file): method/scaffold/command.py:168 calls configured_checks unguarded
  (new code).
- Verified method A (17): 14 hold, 2 closed not-actionable (I-75e78afb, I-c4c32a97), I-996d2683 duplicate of
  I-b471742c. Regressions: I-f95c7f1a (medium, implement's round loses earlier checks), I-31e529e2 (medium,
  Method skill assumes Coordination), I-5c805131 (decision-needed, low), I-815fbe1b (suggestion).
- Run r-20261003T051303-code_review-a6648158 (method B) ended `failed` / `incomplete`: module.scaffold's 3
  findings dropped for one out-of-range location (4th reviewer, see I-82b9bb29); spec-review 4, adoption 10,
  validation 8, delivery 6 reported. Scaffold's findings verified and recorded by hand as before.
- Verified spec-review (4) + adoption (10): 12 hold (10 lowered), 2 closed not-actionable (I-b3d5e5d6,
  I-59651ac8). One regression: I-13e0c56b (medium: spec_panel without the issues part falls back to the chair's
  unchecked `earlier` claims). Adoption code is byte-identical to main.
- Verified validation (8) + delivery (6): 13 hold (12 lowered), I-e0ad8e96 closed not-actionable (dropping
  removed Modules is specified). Recorded module.scaffold's 3 unreported findings as new Issues (I-d9eae20f,
  I-8e90b58a, I-11571521). All pre-existing on main.
- Run r-20261003T053126-code_review-bd94cc7c (distribution, dogfooding, e2e, dogfood-scenarios, concorde) ended
  `failed` / `incomplete`: distribution (16 findings) and dogfood-scenarios (4) dropped for out-of-range
  locations (5th and 6th reviewers, I-82b9bb29); dogfooding 4, e2e 7, concorde 10 reported. Verified and
  recorded by hand as before. All 33 Modules now reviewed (kernel on its rerun).
- Recorded module.distribution's 16 unreported findings: 13 hold (two merged → 12 new Issues; finding 1 is
  I-0a320552), 2 do not hold. Regressions: I-0a320552, I-5c8b3e81, I-0ad54807, I-6aa3735e (medium);
  I-fbfbeb0b, I-0d859a80, I-a85a34de, I-8220276e (low). Pre-existing medium: I-b2bdc1c2. Systemic: the project
  MCP server moved to Distribution but its server-level scenarios stayed in main-session's scenarios.
- Verified dogfooding (4) + e2e (7): 10 hold, I-38f5c545 closed not-actionable; recorded dogfood-scenarios' 4
  unreported findings: 2 hold (I-16245513, I-0a52f8cd), 2 do not. One regression: I-f063ef64 (medium: develop
  guidance added whatever parts are installed). Note: scripts/e2e/e2e.py now imports concorde.method.workers.
- Verified module.concorde (10): all hold, 8 lowered (two "critical" docs-fetch/backup findings → medium);
  regression I-18abf5eb (spec-alone acceptance test incomplete, low). Coupling question: no undeclared, unguarded
  cross-part coupling; every subprocess/file-format reliance is a declared, guarded optional integration or
  already recorded. Recorded I-afc4732c (module.concorde, suggestion/low): the dependency test does not scan the
  scripts parts ship (scripts/*.py) nor concorde.json's develop.check, and its NOT_PARTS comment is wrong.
- Done: all 33 Modules reviewed in 7 runs; no Spec or code changed; worktree clean; no run left running. No open
  Issue of this task stands above medium.

## Report 1 to the main agent (项目架构分离建议), 2026-10-03T06:02:30Z

parts-review: done, no delivery (review only, no Spec or code changed, worktree clean). All 33 Modules reviewed with `code_review --scope module` in 7 runs (module.kernel rerun after `gateway_concurrency_limit`). Every finding was verified against code, Spec and `main` (merge-base 5df929ef). Six reviewers lost all their findings to `unresolved_evidence` (module.spec, issues, tasks, scaffold, distribution, dogfood-scenarios: 79 findings); I verified those from the run results and recorded the ones that hold. About 20 findings were closed as not-actionable or duplicate. Reviewers inflated severity throughout: no Issue of this task stands above medium after verification.

REGRESSIONS of the parts refactor (49; 11 medium, the rest low; none high/critical)
- spec (5, all low): I-efdb6346 Spec core's new adapters (spec/commands.py, installation.py) import Views and the Spec MCP server; I-48fb0384 validation still claims configured-check inputs; I-e193e36a (decision-needed) validation.md newly says the spec part reads no other part's format, yet it reads build-manifest.json; I-e9a40f5c spec-mcp `module` tool advertises removed checks; I-aeb43288 spec guidance lacks the coordination-absent case.
- kernel (7, all low): I-97dec858 nested $defs; I-529eee55 pointer ~1 escaping; I-39a101dd guidance; I-f16be8b2, I-b7008b86 the Kernel contract, written afresh, dropped Spec core's symlink-refusal and value-depth promises; tracing I-f8772d79 TraceRoot.place never checked; I-941300cf node kinds still hard-coded in the Kernel although the contract says parts register them.
- worker harness (low): I-0542bfbf guidance names absent parts; I-5b2ba600 mixed (extra grant-input fields accepted).
- execution (7, all low): I-e4ba7e37 Operation with no workers registrable; I-3f709b30 (decision-needed) catalog "providing Module" vs part, read by nothing; I-c5588827 Commands Spec still says the catalog routes the CLI (fix the Spec); checks I-b0e467d3 check input escapes via a symlinked parent (main's preflight refused it); I-078aae79 checks files accept NaN/Infinity (json.loads replaced decode); I-d2dec046 (suggestion, latent); I-e6240816 validate_checks has no caller though service.md says task-validation calls it, so main's project-wide check-input preflight is gone with nothing in its place.
- workflow: I-c66d7124 MEDIUM a superseded malformed workflow object makes every later report fail; I-60bd5fea MEDIUM the step-output contract newly says the answers file is a JSON list, while code and Adoption use {"answers": [...]}; I-cfb021e5 low guidance assumes Coordination.
- issues: I-3ad5326c MEDIUM KernelError is no ValueError, so a symlinked record aborts `issues check` (a sweep of all handlers found no other such case); I-01f76edf low guidance; I-1b9c2a57 low mixed (recovery failure loses structured causes).
- coordination (6, all low): I-7b509b56 `task deliver` checks admission only before the lock wait; I-89564ab0 merge closes Issues via the merged `concorde` process, against req.tasks.merge-own-sources; I-034996be merging.checks minItems 1 contradicts the no-check merge; I-3b761687 run wait skips part_missing; I-ac11047a task_resolve registered without requiring issues; I-dfe59128 (decision-needed) escalation attribution text vs `by` default.
- method: I-f95c7f1a MEDIUM implement's round validation now records evidence=[] and drops the earlier round's checks; I-31e529e2 MEDIUM Method skill assumes task sessions (Coordination) without saying so; I-13e0c56b MEDIUM spec_panel without the issues part falls back to the chair's unchecked `earlier` claims; I-5c805131 (decision-needed, low); I-815fbe1b (suggestion).
- distribution (8): I-0a320552 MEDIUM `concorde update --parts` keeps d2/langgraph left out for an added part (the defect from your brief, confirmed); I-5c8b3e81 MEDIUM the receipt records no defaults, so an update keeps a dropped part's default owned and deletes an undeclared one; I-0ad54807 MEDIUM the project MCP server keeps cached serving fields, and the tools digest leaves out serving; I-6aa3735e MEDIUM an unknown-tool refresh overwrites `listed`, so list_changed is never sent; low: I-fbfbeb0b, I-0d859a80, I-a85a34de, I-8220276e (CONCORDE_CHANNEL is specified only in Coordination's scenarios).
- dogfooding (not a part): I-f063ef64 MEDIUM a develop install adds the develop guidance whatever parts are installed (fix in Distribution's install.py).
- root: I-18abf5eb low spec-alone acceptance test incomplete; I-afc4732c suggestion (see below).

PRE-EXISTING on main (~211 standing)
- MEDIUM (59): spec I-44d15d2f I-926dc4e0 I-69ef9269 I-6a01a131 I-4d613f5d, views I-c1868397 I-2a6a5560, spec-mcp I-5108bf68; tracing I-6e58eaae I-3cb1625c I-f2e66c2a I-335b9728(d-n); harness/workers I-ff5160fb(d-n) I-db8baa0a I-2d7bb84c I-2d4dfa0a I-657d8b78 I-6b51b739 I-d1790584; kernel I-fa2b91a7; execution I-517f519d I-c5823f43 I-2f6e27e8 I-3fd2e54f I-54b3c9fd I-89532385 I-e1bff8bc I-39a2cd04, checks I-eef9c7aa; workflows I-c9732ed8 I-56b26ba3 I-4ce236ae I-f3ffb788(d-n) I-1e74d6d7 I-bf7b23f6; tasks I-a01870e9 I-fea06249, task-session I-688f5308 I-dbf1b166; issues I-e189786a; method I-614b95e6 I-285bb261 I-65081f1f I-49b0c360 I-c8b66520 I-3285d6a2(d-n) I-01bf6276 I-cbf52cdd I-d9eae20f I-11571521; distribution I-b2bdc1c2; dogfooding/e2e I-4db33d4f I-8f9eb3e6 I-e430ad4f I-994b99ee; root I-a7951730 I-8eb5420c I-6388252d; code-review I-82b9bb29(d-n, limitation: one out-of-range location drops all of a reviewer's findings; it cost 6 of 33 reviews here).
- LOW/suggestion (~152): spread over every Module; listed in the decision log.

SYSTEMIC
1. Guidance assumes Coordination in 7 parts (spec, kernel, worker harness, workflow, issues, method, dogfooding develop sections). The tests check only which sections are composed, not whether their text stands alone without the parts it mentions.
2. The Kernel still knows the other parts: tracing hard-codes every part's node kinds (I-941300cf), and registration fields such as TraceRoot.place and `requires` are not enforced (I-f8772d79, I-ac11047a).
3. The Spec core copies of Kernel utilities duplicate defects, and every fix must be made twice: I-455cef95/I-69b58414 (decode 1e999), I-2734c5c8/I-3731c71f (JSON equality). The Kernel contracts, written afresh, also dropped promises Spec core's contract had.
4. Moving configured checks out of Spec core lost the project-wide input preflight (I-e6240816, I-b0e467d3). Moving round validation into Method lost earlier-round checks (I-f95c7f1a).
5. The project MCP server moved to Distribution, but its server-level scenarios stayed in main-session's scenarios (I-8220276e). Its serving metadata now comes from registrations, which is where 3 of Distribution's medium regressions come from.
6. Coupling question: no undeclared, unguarded cross-part coupling. Every `concorde <command>` subprocess call and file-format read is a declared optional integration guarded by part_missing or by the file's absence. The dependency test checks only Python imports by design. Gap recorded as I-afc4732c (suggestion): the test skips the scripts the parts ship (scripts/*.py) and concorde.json's develop.check, and its NOT_PARTS comment is wrong. A smaller duplication: the "call the worktree's concorde" helper is copied in coordination, workflows and method.
7. Reviewer quality: substance was mostly right, but severity was inflated almost everywhere. Reviewers sometimes report a callee's defect (e.g. Workers') against the calling Module. Six reviewers lost all findings to slightly-wrong line ranges (I-82b9bb29).

Issues this task resolves: none. Escalations: none. Decisions: all in the decision log.

## Closed: completed, 2026-10-03T06:03:09Z

Overall review of parts-split against main: all 33 changed Modules Module-reviewed in a built worktree, every finding verified; 49 regressions of the parts refactor (11 medium, none high or critical) and ~211 pre-existing standing Issues recorded, classified in the decision log; no Spec or code changed.

The close answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task close --completed` closed it as completed: Overall review of parts-split against main: all 33 changed Modules Module-reviewed in a built worktree, every finding verified; 49 regressions of the parts refactor (11 medium, none high or critical) and ~211 pre-existing standing Issues recorded, classified in the decision log; no Spec or code changed.. Nobody answers a report after that.
