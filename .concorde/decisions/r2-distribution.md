# Decision log: r2-distribution

Goal: Fix the critical, high and obvious-fix open Issues of Distribution found by the complete project_review

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 16 Issues in its `resolves`,
owned by its Modules, found by the complete project_review
r-20261008T063808-project_review-9851e69f (unbound; reports under
`.concorde/unbound/r-20261008T063808-project_review-9851e69f/` of the primary worktree) or
earlier. Read each with `concorde issues show`. Other open Issues of these Modules are out of
scope: do not fix them, even when nearby, unless a fix in scope needs it.

By tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest
  meanwhile. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- Work critical first, then high.
- An Issue that does not hold, is a duplicate or is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix needing a change outside the task's Modules: escalate, unless it is a small mechanical
  follow-on (a link, a fixture, a registry refresh).

Eleven other round-2 tasks run in parallel, each on other Modules (r2-*). If a merge conflict
comes back, the main agent asks you to merge the primary branch in. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Task session (2026-10-08)

None of the 16 Issues is `decision-needed`, so nothing was escalated. Every Issue held at the head;
none was a duplicate or already fixed. Decisions taken without the developer:

- **I-9cce391d** (obvious-fix): the core paragraph of "The project MCP server" now says the call's
  process takes the locks of long work and becomes the command, and the server never holds a lock;
  the "Serving a call" bullet list follows.
- **I-5f789675** (obvious-fix): a worker's progress file is placed in its run directory
  `workers/<worker run id>/` inside the Operation run's trace node, linking Workers.
- **I-6c9c8624** (preferred-fix): chose to rewrite the requirement statements rather than move the
  conditions into prose: `parts-installable` now covers a first install (selected parts,
  Distribution, transitive dependencies; every part without `--parts`) and defers to the update
  rule; `update-installed-parts` names the empty-receipt fallback, additions, Distribution and the
  transitive closure, and defines "names no part" as no `parts` or an empty one; the update-result
  contract semantics say the same; `locked-python-dependencies` carries the
  `--without-dependencies` opt-out and its preservation on update; `installer-keeps-installation-bound`
  lists its three outcomes (bound, unreadable Specs, Spec core refusal under `binding_error`), none
  failing the installer.
- **I-06346c8c** (preferred-fix): `skills-rendered`'s explanation now says the installer composes
  the skill again for the installed parts, with the main-agent description only with Coordination,
  so only an all-parts, non-develop install loads the checkout's exact text.
- **I-afa019c8** (obvious-fix): split into `req.distribution.composed-from-registrations` (kept id,
  the command) and the new `req.distribution.mcp-tools-from-registrations` (the server, with the
  required-parts filter). The kept id keeps existing links valid.
- **I-b0ebead0** (preferred-fix): the installer asks the parts installed until now through the
  installation it would replace: a small script run by that installation's own interpreter with its
  own Framework copy calls each of its parts' idle checks, so a part the incoming package no longer
  builds is asked too. Only when that copy cannot be run (no interpreter, no answer) does it fall
  back to the incoming package's registrations, which keeps a half-failed install re-runnable as
  module.md promises. A check of the installed copy that fails is `part_failed`, with the
  exception as its cause. Parts the install adds are asked through the incoming registrations.
  Rejected: refusing whenever the old copy cannot run (would block repairing a broken install).
  Spec: module.md's busy-check paragraph and the new scenario
  `install-busy-dropped-part`.
- **I-ca3436c4** (obvious-fix): `installed_names` and `_previous_parts` treat `"parts": {}` like no
  `parts`; the scenario's GIVEN names both forms.
- **I-f74da74c** (preferred-fix): `verify_fresh` checks every recorded output's existence and
  digest as well as the sources, so the installer, the Protocol copy writer and `protocol-manifest`
  all refuse a changed or missing render (`no-stale-copy` names the output case). New scenario
  `install-stale-build`.
- **I-74a058a4** (preferred-fix): `recompute_protocol_manifest` validates the whole manifest
  shape of Spec core's contract (exact fields, schema_version 1, non-empty version, integer
  profiles, non-empty assets of exactly path and `sha256:<64 hex>` digest, safe unique paths under
  `generated/protocol/`) and requires each asset to be a recorded build output, before anything is
  compared or written; the test covers every flag combination.
- **I-5d22dd8b** (preferred-fix): an envelope command's loading and run sit behind an exception
  boundary answering `failed`/`unexpected_error`; Distribution's step after it (update mark
  removal, glossary import) sits behind another that keeps the command's result and findings and
  answers `failed`/`distribution_step_failed` with the OS error as cause. Documented in module.md;
  new scenario `step-failed-envelope`.
- **I-3add2a71, I-c01faf54, I-cf9767a9** (obvious-fix): `last_answer` scans past non-answer lines;
  the wait watcher tells a decoded JSON null from unparsable output; a failed listing records the
  digest of the empty list the session was given (new scenario
  `mcp-tools-changed-after-failed-listing`).
- **I-b314b281** (obvious-fix): `parts.TABLE` holds the parts table's order and
  `parts.in_table_order` presents MCP tools and instructions in it; `guidance.ORDER` derives from
  it (Coordination first). A test checks `parts.TABLE` against module.md's table.
- **I-355e9b48** (obvious-fix): the root's own audience is passed to the include check; new
  scenario `build-refuses-foreign-audience`.
- **I-89763796** (obvious-fix): the first `CLAUDE.md` block keeps the project's text as an exact
  prefix and adds only the missing separator.

- Full suite on the final input: 1381 passed, 5 skipped. task-validation
  r-20261008T135335-task_validation-3d02c3b7: ready, 28 checks passed.
- **Non-ok result:** delivery r-20261008T140441-delivery-5821b502 was blocked because
  check.execution.tests failed once: `test_a_run_waiting_behind_a_merge_names_the_merge` hit
  `OSError: Directory not empty: '.concorde'` in its temporary-directory cleanup. It is a teardown
  race in Execution's test, outside this task's code: the detached runner still writes after its
  result file appears. It passed in the full suite, in task-validation and in 6 isolated reruns.
  Recorded as Issue I-5df335beaacb58178eeab2f6a387f41d (module.execution, obvious-fix, medium)
  for later work, not fixed here. Decision: run delivery again on the same input.

## Report 1 to the main agent (Review流程), 2026-10-08T14:25:56Z

r2-distribution delivered: delivery commit 790fb45c4 on concorde/r2-distribution (4 verified steps before it: 6b4eb0b64, b6ac4b9bd, f49af501a, e325b5615). Full suite 1381 passed / 5 skipped; task-validation ready (28 checks).

The task resolves all 16 Issues in its resolves. None was decision-needed, a duplicate or already fixed, so there was no escalation. Choices on preferred-fix Issues (details in the decision log):
- I-b0ebead0: the installer asks the parts installed until now through the installation it replaces, running that copy's own interpreter and code. So a part the new package dropped is still asked. Only when that copy cannot run does it fall back to the new package's registrations, which keeps a half-failed install re-runnable. A failing check there is part_failed with its cause. New scenario install-busy-dropped-part.
- I-f74da74c: verify_fresh now checks every recorded output's digest and existence too. The installer, the Protocol copy writer and protocol-manifest all refuse a changed or missing render. New scenario install-stale-build.
- I-74a058a4: protocol-manifest validates the full manifest shape of Spec core's contract and requires each asset to be a recorded build output before comparing or writing anything (all flag combinations tested).
- I-5d22dd8b: envelope commands have an exception boundary. A failure while loading or running gives failed/unexpected_error. A failure of Distribution's own step afterwards (update-mark removal) keeps the command's result and findings and gives failed/distribution_step_failed. New scenario step-failed-envelope.
- I-6c9c8624: the installation requirement statements were rewritten: first-install selection, the update set (empty-receipt fallback, additions, Distribution, transitive closure), the --without-dependencies opt-out, and the three binding outcomes. The update-result contract is aligned.
- I-06346c8c: skills-rendered now says the installer composes the skill again for the installed parts.
Obvious-fix Issues fixed as suggested: I-9cce391d, I-5f789675, I-afa019c8 (split; kept composed-from-registrations for the command, new req.distribution.mcp-tools-from-registrations), I-ca3436c4, I-3add2a71, I-c01faf54, I-cf9767a9, I-b314b281 (parts.TABLE / in_table_order), I-355e9b48, I-89763796.

Non-ok result: the first delivery (r-20261008T140441-delivery-5821b502) was blocked by a flaky Execution test, test_a_run_waiting_behind_a_merge_names_the_merge, which hit a cleanup race (Directory not empty: .concorde) while the detached runner was still writing. It passed everywhere else and in 6 reruns. Recorded as Issue I-5df335beaacb58178eeab2f6a387f41d (module.execution, obvious-fix, medium), not fixed here; the second delivery passed.

Open: nothing for the developer. Ready to merge.

## Closed: merged, 2026-10-12T14:30:57Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 790fb45c4f2e005234f421a1b964f35016030a4f into main and closed it as merged. Nobody answers a report after that.
