# Decision log: issue-list-filters

Goal: Let a session read only the Issues it needs: give `concorde issues list` and the project MCP server's `issue_list` filters (at least status, owner Module and tier) so the duplicate check the guidance asks for fits a tool result, update the guidance to use them, and drop the Issues Spec's stale sandbox reason for task sessions using the Issue tools.

## Brief (main agent, 2026-10-01)

The developer asked the main agent to look at the Issue store and fix the more important Issues;
the main agent chose this one because it breaks a step every session takes: the main agent's own
`issue_list` call in this conversation overflowed the tool result too (157 open of 170 Issues).

Issues this task resolves, with their tiers:

- I-15b1c594bcb156bab9d5e762a96cd35a, `preferred-fix`: `issues list` / `issue_list` take no filter
  and overflow a session's tool result. Fix it yourself and report the fix you chose. Direction
  from the main agent: add filters to both the command and the MCP tool, at least `status`
  (open/closed), the owner Module (`owner_target_id`, and consider `target_id`) and `tier`,
  combinable; keep the unfiltered call returning everything as today, so no caller breaks. Then
  change the main-session and task-session guidance (prompts and the Main session Spec) so the
  duplicate check before a report reads the open Issues of the Module concerned rather than the
  whole list. Whether to also add a text/title search, a compact row form or a count is yours to
  decide; keep it small.
- I-71f6993f0e9b59fa96d22123e5f57b82, `obvious-fix`: the Issues entry still says a task session
  uses the Issue tools because its Bash sandbox cannot write the primary worktree. Replace the
  reason with the one that holds (the tools record the calling session).

Left to the session: the filter flag names and shapes, the Spec wording, scenario and test
updates. Escalate only if the fix would change what an existing caller receives.

## Task session decisions (2026-10-01)

- **Filter shape (I-15b1c594…, preferred-fix).** `concorde issues list` takes `--status open|closed`,
  `--module <module>` and `--tier <tier>` (repeatable); `issue_list` takes `status`, `module` and
  `tier` (a nonempty list). They combine as AND; with none, every Issue is listed as before, so no
  existing caller's answer changes. `--module` keeps an Issue whose latest report has the Module as
  owner *or* reporting Module: this is the store's existing `target_id` filter, already used by
  `spec_review` and `code_review` to find a Module's earlier Issues, so the command and the reviews
  agree on what "the Issues of a Module" are; a separate owner-only filter was judged unnecessary
  (the reporting Module is normally the owner). Tier is repeatable/a list so "the blocking tiers"
  is one call, mirroring `task_list`'s `state`.
- **Not added:** a text search, a compact row form or a count. With `--module X --status open` the
  largest Module (`module.issues`) lists 17 rows (~7 KB), well inside a tool result; keep it small.
- **Validation.** An unknown status or tier is `usage` (exit 2) on the command (argparse choices),
  `invalid_input` on the tool (its input schema), and `invalid_issue` in the store.
- **Guidance and Specs.** The main-session skill, task-session guidance, Main session entry,
  requirement `req.main-session.issues-recording` and scenario `record-issue` now tell a session to
  read the open (and, when it may have been fixed before, closed) Issues of the Module concerned
  through the filters, never the whole list. Issues gains `req.issues.list-filtered` and
  `scenario.issues.command-list-filtered`; its interface documents the options and `tiers`.
  `docs/using-concorde.md`'s example uses the filters.
- **I-71f6993f… (obvious-fix).** The Issues entry now says sessions use the tools because they
  record the calling session, which the command cannot know, matching
  `req.main-session.issues-through-server`; the sandbox reason is gone.
- **Full suite: 1 failure, not this task's.** `tests/concorde/workflows/test_workflows.py::SandboxTests::test_a_run_detached_inside_a_pid_namespace_dies_with_it`
  fails (`'running' != 'finished'`: the step finishes inside its 2-second wait) in this worktree and
  identically in a copy of base commit d857acc2; 870 other tests pass. It is already tracked as
  open Issue I-fc326b9c1f095e6bac9723e4bcf9de65 (found with `issues list --module module.workflows
  --status open`), so no new Issue was reported.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T12:47:04Z

issue-list-filters delivered: delivery commit b6372c3e on concorde/issue-list-filters, on top of 7073ba53. task-validation ready and delivery ok. The task resolves I-15b1c594bcb156bab9d5e762a96cd35a and I-71f6993f0e9b59fa96d22123e5f57b82, both recorded with `task resolve`.

What changed:
- I-15b1c594 (preferred-fix): `concorde issues list` now takes `--status open|closed`, `--module <module>` and `--tier <tier>`, which may be repeated. `issue_list` takes the same filters as `status`, `module` and `tier`, where `tier` is a nonempty list. Filters combine, and an Issue must pass each one. With no filter the list returns every Issue exactly as before, so no existing caller gets a different answer.
- Fix chosen: `--module` keeps an Issue when its latest report has that Module as owner or as reporting Module. This is the store's existing `target_id` filter, which spec_review and code_review already use to find a Module's earlier Issues, so the command and the reviews agree on what "a Module's Issues" means. I judged an owner-only filter unnecessary. `tier` is a list so the blocking tiers take one call, like task_list's `state`.
- I did not add text search, a compact row form or a count. The open Issues of the largest Module, module.issues, come to 17 rows (about 7 KB), well within a tool result.
- An unknown status or tier is refused as `usage` (exit 2) by the command, `invalid_input` by the tool and `invalid_issue` by the store.
- Guidance: the main-session skill, the task-session guidance, the Main session entry, req.main-session.issues-recording and scenario record-issue now tell a session to read the open Issues of the Module concerned through the filters before recording, plus the closed ones when the problem may have been fixed before, and never the whole list. Issues gains req.issues.list-filtered and scenario.issues.command-list-filtered, and its interface documents the new options. I also changed the `issues list` example in docs/using-concorde.md to use the filters.
- I-71f6993f (obvious-fix): the Issues entry no longer gives the sandbox reason. It now says sessions use the tools because they record the calling session, which the command cannot know, in line with req.main-session.issues-through-server.

Verification: build --check and spec-validation pass. Tests were added for the store, command, MCP tool and guidance. In the full suite 870 pass and 1 fails: tests/concorde/workflows/test_workflows.py::SandboxTests::test_a_run_detached_inside_a_pid_namespace_dies_with_it fails with 'running' != 'finished' because the step finishes inside its 2-second wait. It fails the same way in a copy of base d857acc2, so this task did not cause it. It is already tracked as open Issue I-fc326b9c1f095e6bac9723e4bcf9de65, which I found with the new `--module module.workflows --status open` filter, so I reported no new Issue.

Nothing is open and there are no escalations. All my decisions are in the decision log.

## Closed: merged, 2026-10-01T12:46:58Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b6372c3e1a27fa281db786ce0baeeca8ee8b2356 into main and closed it as merged. Nobody answers a report after that.
