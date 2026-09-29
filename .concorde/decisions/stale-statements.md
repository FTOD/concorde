# Decision log: stale-statements

Goal: Repair stale Spec statements: evidence-bundle leftovers and 'delivery cites runs' in Workers, Execution and Commands, and the 'as a channel' contradiction in Task sessions

## Brief (main agent, 2026-09-30)

The restructuring tasks (which were not allowed to change meaning) found statements that
contradict decisions already taken or other Modules' own Specs. Repair them so the Specs agree; no
new design. Decided by the main agent (ordinary scope: aligning text with existing decisions).

1. **Evidence-bundle leftovers** (the developer dropped the committed evidence bundle on
   2026-09-30; see `.concorde/decisions/` of the tasks around `decision-logs-in-git`):
   - `specs/concorde/execution/workers/module.md` says twice that "Delivery later lists these
     records' identities in a workspace's evidence", and says Delivery uses Workers although
     Delivery declares no such `uses`.
   - `specs/concorde/execution/module.md` (Runs concept and `contains-commands`) and
     `specs/concorde/execution/commands/module.md` (`contains-delivery`) say delivery commits
     "with its/their evidence".
2. **"Delivery cites runs"**: `commands/module.md` ("Delivery cites the runs that led to it") and
   `execution/module.md` ("delivery must cite the run that decided the readiness it committed")
   contradict Delivery's own Spec (`execution/commands/delivery/`), which decides readiness itself
   and cites no earlier run. Delivery's Spec is authoritative; do not change Delivery.
3. **Task sessions channel**: `specs/concorde/coordination/task-session/module.md` line ~375
   (uses-main-session) says the project MCP server is configured for every task session "as a
   channel", contradicting the same entry ("without a channel … CONCORDE_CHANNEL=0") and Main
   session's Channels paragraph. Check the code (`src/concorde/…` session starter) to confirm
   which is true and make the Spec say that.

Also grep `specs/` and `prompts/` for other "evidence bundle"/"evidence" leftovers of the same kind
in these four Modules; fix those, and only report (do not fix) any found in other Modules. Check
requirements, scenarios and contracts of these Modules too, and the code when a statement is
about behaviour (if code disagrees with the decided design, report it instead of changing code).
Run build, spec-validation, task-validation and delivery; report per statement what changed.

### Addition (main agent, 2026-09-30)
4. **Task session guidance**: task `restructure-spec-tooling` left a background sandboxed polling
   loop running (its `pgrep -f "docusaurus build"` matched its own command line, so it never
   ended). While any background sandboxed command of a session lives, Claude Code's sandbox keeps
   its placeholder files in the task worktree and holds `/home/zhenyu/concorde/.git/config.lock`,
   which blocked that task's task-validation and the preparation of other tasks. Add to the task
   session's guidance (its first prompt / skill text owned by `module.task-session`, and its Spec
   where it describes the session's duties) that a task session stops every background command it
   started before `task-validation` and `delivery`, and never waits by polling. Keep it short.

## Task session (2026-09-30)

- **Workers** (`execution/workers/module.md`): removed both "Delivery later lists these records'
  identities in a workspace's evidence" sentences and dropped Delivery from "The Operation
  providers, Spec review and Delivery use this Module" (no Module but Operations' providers, Spec
  review and others declaring `uses` of `module.workers` includes Delivery). Kept "the Operation's
  evidence" (line ~193): it names the run result's own evidence, not the bundle.
- **Execution** (`execution/module.md`): the Runs concept now says `delivery` "decides that
  readiness again and commits the workspace"; `contains-commands` drops "with their evidence";
  "Why commands are runs" drops "delivery must cite the run that decided the readiness it
  committed"; "taken and cited as a step" became "taken and recorded as a step". Also fixed
  `scenario.execution.command-run` in `execution/scenarios.md`, whose AND said "a later `delivery`
  ... can find it"; it now says "a later workflow step or the task level can find it".
- **Commands** (`execution/commands/module.md`): "must be taken, cited and awaited ... Delivery
  cites the runs that led to it" became "taken, recorded and awaited ... and the task level waits
  for each command and reads its evidence and error chain"; "a later run can cite it" became "the
  task level can read it later"; `contains-delivery` drops "with their evidence".
- **Task sessions** (`coordination/task-session/module.md`, uses-main-session): "as a channel"
  became "without a channel (`CONCORDE_CHANNEL=0`)". Code confirms it: `src/concorde/tasks/session.py`
  writes `"env": {"CONCORDE_CHANNEL": "0"}` into the session's MCP configuration.
- **Addition 4**: added the rule to the task-session guidance `prompts/main-session/task-session.md`
  and to Task sessions' "The session boundary" section. Decision: that prompt file is owned by
  `module.main-session` (its entities list `prompts/main-session/`), not `module.task-session` as
  the brief said; I changed it anyway because the brief asks for exactly this change and it is
  wording only. The existing sentence "Never wait for anything with `sleep` loops." is kept
  verbatim because `tests/concorde/main_session/test_guidance.py:266` asserts it; the new sentence
  follows it.
- Verified: `build`, `build --check`, `spec-validation` (0 findings), pytest
  `tests/concorde/main_session tests/concorde/tasks` passed. Commit `2a1f3b3b`.
- **Found in other Modules, not fixed (report only)**:
  - `specs/concorde/requirements.md:143` (module.concorde): "the `delivery` execution command, which
    commits them together with their evidence".
  - `specs/concorde/execution/commands/validation/module.md:142` (module.validation): "yet delivery
    must cite the run that decided a readiness".
  - `specs/concorde/execution/operations/understanding/contracts.md:134` (module.understanding):
    example step purpose "commit the change with its evidence".
  - `src/concorde/validation/command.py:3` (Validation's code docstring): "and delivery cites its run".
- `task-validation`: ok, ready. `delivery`: ok, delivery commit `4512ee65` on
  `concorde/stale-statements`. No background command of this session was left running.

## Main agent on the session's report (2026-09-30)

Accepted, including the edit of `prompts/main-session/task-session.md` (owned by
module.main-session; the brief misnamed its owner, no other task held that Module). The four
leftovers found in module.concorde, module.validation and module.understanding go to a follow-up
task once `validation-sandbox-paths` (which holds module.validation) has merged. Merging.

## Closed: merged, 2026-09-29T18:50:19Z
