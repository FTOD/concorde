# Decision log: issue-writes-in-sessions

Goal: Let runs a task session starts write project-level Issues from inside its session boundary, and finish the leftovers of Protocol 16.1 and project-level Issues in Workers, the Spec MCP server, Understanding and Dogfooding

## Brief (main agent, 2026-10-01)

Follow-up task of the review rebuild. Already merged on main: `spec-quality-protocol` (Protocol
16.1, task type `review-architecture`, `ProjectSpecification`) and `project-issues` (Issues are
project-level records in the primary worktree's `.concorde/issues/`, each write taking the merge
lock and committing the record alone on the primary branch; Issue tools on the project MCP server;
defects of the Issue system itself never go through Issues). `panel-architects` runs in parallel
(spec-review, issues, main-session): do not touch those Modules.

### What to do

1. **Runs a task session starts may write Issues.** The review Operations (`spec_review`,
   `spec_panel`, and later `code_review`) will report findings as Issues from their host. A task
   session starts runs in background Bash inside its session boundary, which today cannot write
   the primary worktree's `.concorde/issues/` (nor, possibly, what the write needs: the merge lock
   and the commit on the primary branch). Widen the session boundary to exactly what an Issue
   write needs, no more, in `src/concorde/tasks/session.py` (module.task-session) and the Harness's
   session-boundary text. Keep the rule that the session's own Edit/Write tools do not write
   Issues directly: they go through the Issue command or MCP tools. Test it.
2. **Workers**: `specs/concorde/execution/workers/launch.md` still says "seven Protocol task types";
   bring Workers' Specs and code in line with the eight.
3. **Spec MCP server**: its grant tool (`src/concorde/spec_mcp/tools.py`) does not offer
   `review-architecture`; offer it.
4. **Understanding**: the contracts' illustrative example still says "branch-local Issue records";
   correct it.
5. **Dogfooding**: a defect of Concorde's Issue system seen in a develop install cannot be a defect
   report, since those are Issue reports; say how it travels instead (its error chain, handed to the
   Concorde repository's developer as the error chain rule says) in Dogfooding's Spec and guidance.

### Left to the task session

Everything within those points. Escalate together anything that changes other Modules' promises.

### Verification and delivery

Build, spec-validation, relevant tests and the full suite once at the end, then `task-validation`
and `delivery`, and report to the main agent.

## Task session decisions (2026-10-01)

- **Session boundary widened by one path.** An Issue write takes the merge lock in the primary
  worktree's `.concorde/locks/` (already writable), stages and renames its record inside
  `.concorde/issues/`, and commits it with `git add -f` / `git commit --only` through the Git
  directory (already writable). So the only path added to the session's Bash `allowWrite` is the
  primary worktree's `.concorde/issues/`, created before the session starts like the other paths.
  The write hook is unchanged, so Edit/Write still refuse Issue records (now asserted in the
  boundary test). A new test (`scenario.task-session.issue-write`) runs a real Issue write from the
  task worktree and checks that every path it changed lies inside `writable()`; it fails without
  the new path. Task sessions now declares `uses module.issues` (concept.issue) and relies on
  Tasks' concept.merge-lock; registry refreshed.
- **Workers bug found and fixed (point 2).** Beyond the "seven" wording, Workers refused every
  `review-architecture` request with `grant_unavailable` ("lacks a known task type"), because it
  checked the task type against the tool-set table, which has no row for it. It now checks against
  the Protocol's `TASK_TYPES`; the tool set of a type that writes nothing stays the read-only one.
  Added `req.workers.every-task-type` and `scenario.workers.every-task-type` with a test that fails
  without the fix. `spec_rule` gives review-architecture the default ("return `blocked`"), as for
  review-spec; left unchanged.
- **Spec MCP server (point 3).** `boundary` offers `review-architecture`; the list stays literal
  in `tools.py` (its imports are lazy) and a new test (`scenario.spec-mcp.boundary-task-types`)
  holds the enum equal to `TASK_TYPES`. Contract says eight task types.
- **Understanding (point 4).** The example's promise now describes project-level Issues in the
  primary worktree, committed on the primary branch, with a tier and a basis. The example goal
  ("let Issue reports carry a severity") is kept.
- **Dogfooding (point 5).** A defect of the Issue system (store, `concorde issues`, the Issue MCP
  tools, `issues report --check` refusing a correct report) is never a defect report; the main
  agent hands over the failure's error chain with its own `scope` link on top (in a task through
  `task escalate --run` or `--error-file`), written to `.concorde/runs/defects/<name>.error.json`
  and named to the developer; an `environment` refusal is a wait, not a defect. In the Concorde
  repository it is taken up as any error chain: a task for the Issues Module, escalated with
  `--error-file`, no Issue. Added `req.dogfooding.issue-system-defect`, a BUT line in
  `scenario.dogfooding.guidance`, guidance text and test fragments. Dogfooding now relies on
  concept.project-mcp-server (linked in its text).
- **Not changed, outside the task's Modules:** the task-session guidance
  (`prompts/main-session/task-session.md`, module.main-session, which `panel-architects` touches)
  still says the Issues are kept by the primary worktree "which your Bash sandbox cannot write";
  after this task that is no longer literally true, though its rule (read and write Issues only
  with the MCP tools) still holds. The `concorde-development` skill (module.concorde) needs no change: an
  error chain handed over is taken up by the `concorde` skill's general rule.

## Report 1 to the main agent (spec-review quality criteria), 2026-09-30T20:22:52Z

Task issue-writes-in-sessions delivered: delivery commit 881553ab (concorde: deliver issue-writes-in-sessions) on concorde/issue-writes-in-sessions. Build --check, spec-validation, the full suite (855 passed, 4 skipped), task-validation (ready) and delivery all passed.

What changed:
1. Session boundary (module.task-session, module.harness): an Issue write takes the merge lock in .concorde/locks/ (already writable), writes its record in the primary worktree's .concorde/issues/ and commits through the Git directory (already writable). So the only path added to the session's Bash allowWrite is .concorde/issues/, created before the session starts. The write hook is unchanged: Edit and Write still refuse Issue records. A new test (scenario.task-session.issue-write) runs a real Issue write from the task worktree and checks that every path it changed is writable; it fails without the new path. Task sessions now declares a use of module.issues.
2. Workers: besides the "seven task types" wording, Workers refused every review-architecture worker with grant_unavailable ("a known task type"), because it checked the task type against the tool-set table, which has no row for that type. It now checks against the Protocol's TASK_TYPES, and a task type that writes nothing keeps the read-only tool set. Added req/scenario.workers.every-task-type and a test that fails without the fix.
3. Spec MCP server: boundary offers review-architecture; a test keeps its enum equal to TASK_TYPES, and the contract now says eight.
4. Understanding: the example's promise now describes project-level Issues in the primary worktree, with tier and basis.
5. Dogfooding: a defect of the Issue system itself is never a defect report. The main agent hands over the failure's error chain with its own scope link on top (in a task through task escalate --run/--error-file), written to .concorde/runs/defects/<name>.error.json and named to the developer. An environment refusal is a wait, not a defect. In the Concorde repository it is taken up as any error chain: a task for the Issues Module, escalated with --error-file, and no Issue. New req.dogfooding.issue-system-defect, a scenario line, guidance text and tests.

Decisions I made (all in the decision log): I widened the boundary by that one path only. The Spec MCP enum stays literal, and a test guards it. spec_rule gives review-architecture the same default as review-spec. The Understanding example's goal is unchanged.

Still open (not mine to change): prompts/main-session/task-session.md (module.main-session, which panel-architects touches) says the primary worktree's Issues are kept where "your Bash sandbox cannot write". After this merge that is no longer literally true, though its rule to use only the MCP Issue tools still holds. It is a one-phrase follow-up for main-session. No escalations, no Issues resolved.

## Closed: merged, 2026-09-30T20:23:14Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 881553ab9215629aa727c2f5c11be5e551b2dd1e into main and closed it as merged. Nobody answers a report after that.
