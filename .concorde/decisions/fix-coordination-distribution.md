# Decision log: fix-coordination-distribution

Goal: Fix the parts refactor's regressions in the coordination and distribution parts and the develop install found by the overall review, and check that composed guidance stands without the parts it mentions

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

### Your group: coordination, distribution, develop install, guidance composition

Decided by the main agent:
- I-dfe59128: `task_escalate`'s `by` defaults to the calling session's level, as the Session
  contract says (task-session in a bound task worktree, main-agent in the primary worktree); an
  explicit `by` still wins.
- Systemic finding of parts-review: seven parts' guidance sections assumed Coordination, and the
  tests check only which sections are composed. The other fix tasks fix their own parts' sections;
  you add a check, as far as it can be made mechanical, that a section composed for a subset of
  parts names no command or tool of an absent part without saying what happens when that part is
  absent, and fix the develop guidance (I-f063ef64).

## Task session decisions (2026-10-03)

- I-7b509b56 (deliver admission): `task deliver` takes the workspace lock with `retake=False` (a lock
  file a close removed while it waited is refused as `task_closed`) and runs its admission
  (`_bound_task`) again under the lock, acting on the record read there. Contract and
  `scenario.tasks.deliver-refused` say so; a test holds the lock in another process and switches
  the branch, then removes the lock file, while deliver waits.
- I-89564ab0 (preferred-fix): chose to narrow `req.tasks.merge-own-sources` to the steps the merge
  runs in its own process (closing the task and its sessions); the Issues bookkeeping command, like
  the checks, is a process of the primary worktree's `concorde` and runs the merged code, since the
  parts are independent. Rejected alternative: importing the Issues code into the merge process,
  which would make Coordination depend on Issues.
- I-034996be: dropped the outer `minItems` of `merging.checks` and said it is empty for a merge
  that runs no check.
- I-dfe59128 (main agent's decision carried out): `task_escalate` without `by` derives the level from
  the calling session's worktree (`task-session` in a bound task worktree, `main-agent` otherwise),
  as the Issue tools do; an explicit `by` wins. The command's `--by` default stays `main-agent`.
- I-3b761687: `register_wait` for a `run` calls the command's `require_execution` first.
- I-ac11047a: `task_resolve`'s registration requires `issues`; the partial-install test asserts it
  is not listed.
- I-0a320552: `update` computes what was left out from the earlier receipt's parts only.
- I-5c8b3e81 (preferred-fix): chose to record the Concorde-owned defaults in the receipt
  (`defaults`, contract.distribution.install-result version 3). An install keeps as owned, and never
  removes, every default an earlier receipt named (or, for a receipt written before `defaults`,
  one the package declares) that is still in place. Rejected: deriving defaults from the current
  package only, which is the defect.
- I-0ad54807 (preferred-fix): chose a reroute check over fetching the listing before every call
  (which doubles each call's processes): the server passes how it routed the call (`served`); the
  call's process, the current code, compares it with its own registration and, when they differ,
  answers `reroute` with how it serves every tool, running nothing; the server updates its cache
  and routes the call again once (twice is `call_failed`); a call that now belongs on a thread is
  handed to one (`Rethread`). New `req.distribution.mcp-current-serving`.
- I-6aa3735e: `Calls.refresh()` learns how tools are served without touching `listed`; only
  `tools()` (a listing given to the session) sets it; the session's `initialize` instructions use
  `refresh()` too.
- I-fbfbeb0b: long work runs with the routed worktree's `concorde`, in that worktree.
- I-0d859a80: `PART_NAME` now matches the contract; the contract's `install.gitignore` and
  `install.permissions` declare `uniqueItems` as the validator always enforced
  (contract.distribution.part-registration version 5) — chose tightening the contract over loosening
  the validator, since a repeated rule is meaningless and every other list is unique.
- I-a85a34de: `req.distribution.build-owned-outputs` names `generated/parts.json`.
- I-8220276e: Distribution's module text and new `req.distribution.mcp-channel-override` /
  `scenario.distribution.mcp-channel-override` state `CONCORDE_CHANNEL`; the main-session scenario
  stays where it is.
- I-f063ef64: the installer composes the develop section only where coordination and issues are
  installed; the source check and receipt mode hold for every develop install. The develop skill
  now names the spec and method parts where it names `concorde grant`, `concorde spec-validation`
  and worker boundaries.
- Guidance check (brief): `tests/concorde/distribution/test_guidance_parts.py` checks, per
  paragraph of every registered guidance section and the develop section, that a `concorde <cmd>`,
  a backticked command or a backticked MCP tool of a part the section may be composed without (not
  in its part's dependency closure plus Distribution; plus Coordination's for task-session
  sections; coordination+issues for the develop section; a tool's `requires` counting) is
  accompanied by the paragraph naming that part ("the X part", "the X, Y and Z parts"). Backed by
  new `req.distribution.guidance-absent-parts` and its scenario. It found two Coordination
  paragraphs (fixed), the develop section (fixed), and one paragraph each of the issues and
  workflow parts' skill sections, which task fix-workflow-method-issues rewrites on its branch: I
  made a minimal edit of the same sentences here so this branch passes on its own; on a merge
  conflict in `prompts/guidance/issues/skill.md` or `prompts/guidance/workflows/skill.md`, take
  fix-workflow-method-issues's text (an overlay of its, fix-spec-root's and fix-kernel-execution's
  prompt changes on this branch passes the check).

## Report 1 to the main agent (项目架构分离建议), 2026-10-03T06:28:34Z

fix-coordination-distribution delivered: c8926406 (delivery run r-20261003T062628-delivery-565c51c5; task-validation r-20261003T062442-task_validation-356b0cb0 ready). Full suite 1035 passed / 5 skipped; build --check and spec-validation clean (0 warnings).

Resolves all 15 Issues on the task (already in `resolves`), each fixed in Spec, code and tests:
- Tasks: I-7b509b56 deliver re-admits under the lock (retake=False -> task_closed; branch switch -> wrong_branch); I-89564ab0 (preferred-fix) narrowed req.tasks.merge-own-sources: the Issues command, like the checks, is a process of the primary's concorde running merged code; I-034996be merging.checks may be empty.
- Main session: I-dfe59128 task_escalate without `by` takes the calling session's level (your decision; explicit `by` wins, the command's default stays main-agent); I-3b761687 register_wait for a run refuses part_missing like the command; I-ac11047a task_resolve requires issues.
- Distribution: I-0a320552 update's left-out d2/deps judged on the earlier receipt's parts; I-5c8b3e81 (preferred-fix) receipt records `defaults` (install-result v3), never dropped or removed later; I-0ad54807 (preferred-fix) reroute check: the server passes how it routed a call, the call's process (current code) answers `reroute` on mismatch and the server routes again once / moves it to a thread (new req.distribution.mcp-current-serving) — chosen over a listing per call, which doubles processes; I-6aa3735e internal refresh no longer counts as listed; I-fbfbeb0b long work runs in its routed worktree; I-0d859a80 PART_NAME fixed, contract tightened with uniqueItems for install.gitignore/permissions (part-registration v5); I-a85a34de build-owned-outputs names generated/parts.json; I-8220276e CONCORDE_CHANNEL override specified in Distribution (new requirement + scenario).
- Dogfooding: I-f063ef64 develop section composed only with coordination+issues (source check and receipt mode unchanged); develop skill now names the spec/method parts for `concorde grant`, `spec-validation` and worker boundaries.

Guidance check (brief): tests/concorde/distribution/test_guidance_parts.py + req/scenario distribution.guidance-absent-parts: per paragraph of every registered section and the develop section, a `concorde <cmd>`, backticked command or MCP tool of a part the section may be composed without must come with the paragraph naming that part ("the X part" / "the X, Y and Z parts"). It found 2 Coordination paragraphs and the develop section (fixed), and one paragraph each in the issues and workflow parts' skill sections, which fix-workflow-method-issues is rewriting: I made minimal edits to those sentences so this branch passes alone. MERGE NOTE: on a conflict in prompts/guidance/issues/skill.md or prompts/guidance/workflows/skill.md take fix-workflow-method-issues's text; I checked that this branch overlaid with its, fix-spec-root's and fix-kernel-execution's prompt changes passes the check.

All decisions are in the decision log. Nothing open; no escalations.

## Closed: merged, 2026-10-03T06:28:55Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit c8926406e36e8e29c960cf44eaeb217700aa6df8 into parts-split and closed it as merged. Nobody answers a report after that.
