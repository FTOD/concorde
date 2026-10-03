# Decision log: fix-spec-root

Goal: Fix the parts refactor's regressions in the spec part and the root's Specs and checks found by the overall review, and the root wording findings of the spec panel

## Brief (main agent, 2026-10-03)

### Context

The developer split Concorde into independently installable parts on the integration branch
`parts-split` (primary worktree on it; `main` untouched; decision logs of parts-spec ...
parts-install in `.concorde/decisions/`). Before fast-forwarding `main` to it, the developer had the
whole change reviewed: task `parts-review` (`.concorde/decisions/parts-review.md`) Module-reviewed
every changed Module, verified every finding against code, Spec and `main`, and classified 49 Issues
as regressions of the refactor (11 medium, none high or critical) and about 211 as pre-existing. The
developer decided (2026-10-03): **fix every regression on `parts-split`, plus the two defects that
make reviews unreliable, then merge**; pre-existing Issues wait until after the merge. Four fix
tasks run in parallel, one per group of parts: `fix-spec-root`, `fix-kernel-execution`,
`fix-workflow-method-issues`, `fix-coordination-distribution`.

### Rules

- The Issues this task resolves are on it (`--resolves`); the merge closes them. Read each with
  `concorde issues show` (its latest report is the verified one; parts-review corrected tiers and
  severities). Fix each in the Specs, code and tests as its report says, unless the decision below
  says otherwise. If one turns out not to hold, close it yourself with `not-actionable` and the
  reason, and record why; if fixing one needs a decision with major impact, escalate it.
- Stay in your group's files as far as the fix allows; another task may meet you in a shared file
  (registrations, guidance composition, `tests/concorde/development/`), so keep such edits small. If
  the merge conflicts, the main agent will ask you to merge `parts-split` in.
- Introduce no new regression: every part must still work installed with only its dependencies
  (`tests/concorde/acceptance/test_parts.py`), the part-dependency test must pass, and guidance
  must read correctly whichever parts are installed. Rapid-iteration rule: no shims or dual paths.
- Verify with `build --check`, `spec-validation`, the full suite and smoke runs of what you touched,
  then `task-validation` and `delivery`, and report.

### Your group: spec part and root

Decided by the main agent:
- I-e193e36a: keep Spec core's exemption of the build outputs, and state in Validation's text that
  reading Distribution's build manifest, when present, is the one other-part format the spec part
  reads (optional: without a manifest nothing is exempted by it). A bare `generated/` prefix would
  exempt a user project's own `generated/` code.
- I-b7c3bd94 and I-961a20c8 carry the main agent's settlement in their latest report (no
  optional-integration imports; the merge-time build is this checkout's caller policy).
- The other root Issues are wording and scenario findings of the spec panel on the new root text;
  fix them in the root's Specs, and I-18abf5eb / I-afc4732c in the acceptance and part-dependency
  tests (the dependency test should also cover the scripts the parts ship and `concorde.json`'s
  `develop.check`).

## Task session decisions (2026-10-03)

- **I-e193e36a (build manifest).** Carried out the main agent's settlement in validation.md, but stated
  *two* of Distribution's formats, not one: Spec core also reads the installation record
  `.concorde/install.json` (`installed_files()` for `CHK.binds.installed` and the grant's read-only
  installed files), so "the one other-part format" would have been false. Both are read only when
  present, and their absence is no finding. Spec core's "Validation" rationale was aligned likewise.
- **I-efdb6346 (Spec core imports Views and the Spec MCP server).** Took the report's first repair:
  `src/concorde/spec/commands.py`, `installation.py` and `registration.json` move from Spec core's
  realizations (`realization.spec.commands` removed, `installation.py` dropped from
  `realization.spec.initializer`) into a new `realization.spec-tooling.part` ("Part entries") of
  module.spec-tooling, the spec part's parent, which `contains` all three children. No code moves.
  Why: the adapters call all three children; the parent's `contains` already gives it their Specs,
  and req.spec.no-owner-imports stays true of Spec core's code.
- **I-6ea5c965 (shorthand / package vs Spec independence).** Fixed the root wording (children
  section: Spec tooling depends on no part and imports no part's code, implementing the Kernel's
  formats in its own copy), defined the two halves once in "Two halves, one seam" (lower half =
  Execution, Workflows, Method and the worker harness), relabelled the seam diagram, retitled
  req.concorde.halves-apart "The lower half knows no task" and replaced "state of the task store"
  with "any other record Coordination keeps of a task". Did **not** add a `uses` of module.kernel to
  Spec core: the chair called it an advisory follow-up for Spec core's own review, and it widens
  every Spec core worker's context (no Kernel contract node exists for relies_on to narrow it).
  Recorded it as suggestion Issue I-a1a9a21a32105781bbdb8f449545bb78 so it outlives this merge.
- **I-28f9a76b (report 2) / req split.** req.concorde.part-dependencies keeps the import obligation
  (now stating "no exception": optional integrations import nothing, per I-b7c3bd94's settlement);
  new req.concorde.part-installation carries the installation obligation, linking
  req.distribution.parts-installable.
- **I-28f9a76b (report 1) fingerprint encoding.** Specified the encoding the plugin already uses
  (Python `json.dumps(value, sort_keys=True)`: sorted keys, ", " and ": ", ASCII escapes, UTF-8,
  lowercase hex SHA-256) with a table of each digest's JSON value and one fixed example, which
  test_pytest_timing now asserts. No behaviour change.
- **I-71f4a1de / I-b41c7883 (prior run).** `--prior` names a report written by `--json`; it must
  be a JSON object with a string `run_id` and a `fingerprint` object holding a string `digest`,
  otherwise usage error (exit 4) before any test. This tightens the plugin (before, a missing
  run_id gave `prior_run_id: null` and a missing digest gave `false`); tests cover both new
  refusals. req.concorde.test-prior (naming) and new req.concorde.test-prior-compare (comparison
  and its null conditions) are now separate.
- **I-4d84ba09.** Prior-run scenarios now require complete input, known runtime facts and the same
  Python/pytest/OS/machine; spec-alone now includes init propose/apply. Did not add an
  incomplete-measurement scenario (the report called it optional).
- **I-18abf5eb.** SpecAloneTests now calls the installed copy's `concorde spec-mcp` (`modules` tool)
  and applies the docsite proposal; the npm docsite build stays out, as the main agent allowed.
- **I-afc4732c.** The dependency test also scans the `.py` files each registration ships under
  `install.files` (scripts/concorde.py, install-concorde.py, issues.py, available_models.py),
  checks `concorde.json`'s `develop.check` names Dogfooding code that Distribution's `uses`
  declares, removes OPTIONAL_INTEGRATIONS and fixes the NOT_PARTS comment. A mutation (shipped
  script importing another part) was confirmed to fail the check.
- **I-aeb43288.** spec guidance "Project terms" and "Specs" now say what to do without the
  coordination part (glossary changed as any other file once the developer agreed; Spec tooling's
  error record given to the developer whole). task-session.md unchanged (only composed with
  Coordination, as the verifier found).
- **I-961a20c8, I-e4136547, I-ce80c729, I-eb17fd14, I-efe98f69, I-5d5e574d, I-e9a40f5c, I-48fb0384:**
  fixed as their reports say (root merge-check wording links req.tasks.merge-default-check; root
  small-change wording aligned with req.main-session.tasks-own-changes, added to the root's
  relies_on; development "concorde" skill wording + Dogfooding rule links; Kernel wording;
  coordination-without-method GIVEN names the absent parts; Spec MCP `module` description; stale
  validation claim and docstring).

## Report 1 to the main agent (项目架构分离建议), 2026-10-03T06:31:01Z

fix-spec-root delivered: delivery commit bbf22d4f (run r-20261003T062413-delivery-93a65815) on concorde/fix-spec-root, over the work commit 06b835f5. task-validation r-20261003T061809-task_validation-a52fadf6 ready; build --check ok; spec-validation 0 errors (2 pre-existing CHK.term.unlinked warnings in distribution/contracts.md and scenarios.md, not this task's); full suite 1026 passed, 5 skipped.

Resolves all 19 Issues on the task (merge closes them). Decisions taken without the developer (full list in the decision log):
1. I-e193e36a: your settlement carried out, but validation.md names TWO Distribution formats the spec part reads, each only when present: the build manifest (CHK.binds.unbound exemption) AND the installation record .concorde/install.json (CHK.binds.installed and read-only installed files in grants). "The one other-part format" would have been false.
2. I-efdb6346 (preferred-fix, chosen fix): commands.py, installation.py and registration.json move from Spec core into a new realization.spec-tooling.part ("Part entries") of module.spec-tooling, the parent that contains Spec core, Views and the Spec MCP server. No code moved; Spec core now imports neither Views nor the MCP server.
3. I-6ea5c965: root wording fixed (Spec tooling depends on no part and imports no part's code, implementing the Kernel's formats in its own copy); halves defined once in "Two halves, one seam" (lower half = Execution, Workflows, Method, worker harness); req.concorde.halves-apart retitled "The lower half knows no task", "task store" replaced by "any other record Coordination keeps of a task". I did NOT add a Spec core `uses` of module.kernel (the chair's advisory follow-up; it widens every Spec core worker's context, since no Kernel contract node exists for relies_on); filed as suggestion Issue I-a1a9a21a32105781bbdb8f449545bb78 so it outlives the merge.
4. req.concorde.part-dependencies now holds only the import obligation, "with no exception" (optional integrations import nothing, per your I-b7c3bd94 settlement); new req.concorde.part-installation holds the installation obligation.
5. I-71f4a1de: the pytest evidence plugin now REFUSES (exit 4, before any test) a --prior report without a string run_id or a fingerprint.digest; before, these gave null/false silently. Tests cover both. req.concorde.test-prior split into test-prior (naming) and new test-prior-compare (comparison) for I-b41c7883.
6. I-28f9a76b: the canonical fingerprint encoding the plugin already uses is now specified, with one fixed example digest the test asserts. No behaviour change.
7. I-18abf5eb: SpecAloneTests now calls the installed copy's `concorde spec-mcp` and applies the docsite proposal; the npm docsite build stays out, as you allowed.
8. I-afc4732c: the dependency test also scans the .py files each registration ships under install.files, checks concorde.json's develop.check names Dogfooding code that Distribution's uses declares, and drops OPTIONAL_INTEGRATIONS. A mutation check (a shipped script importing another part) fails it as it should.
9. I-aeb43288: only skill.md gained the absent-coordination cases. I reworded the Specs section so that the main-session guidance test's exact phrase still holds.
The rest (I-961a20c8, I-e4136547, I-ce80c729, I-eb17fd14, I-efe98f69, I-5d5e574d, I-4d84ba09, I-e9a40f5c, I-48fb0384) are fixed as their reports say. The root now also relies_on req.main-session.tasks-own-changes (registry refreshed).

Not ok during the work: one full-suite run failed tests/concorde/execution/test_runner.py::test_a_detached_run_is_announced_and_finishes_on_its_own (Errno 39 '.concorde' not empty during teardown). It passed alone 3/3 and in the final full run. The cause is a teardown race in Execution's test, outside this task; filed as I-b4fe5ad37c4557809f5e6d9c99e7ee4a (module.execution, obvious-fix, low), which may suit fix-kernel-execution.

Nothing open needs a decision from you.

## Closed: merged, 2026-10-03T06:31:23Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit bbf22d4f5dcd745f9d90aa533d6daba5df0abf6c into parts-split and closed it as merged. Nobody answers a report after that.
