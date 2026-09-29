# Decision log: review-leftovers

Goal: Remove the remaining Spec text in Issues and Spec tooling that lets the main agent work inside a task worktree

## Brief (main agent, 2026-09-30)

A follow-up to the spec review the developer asked for after `project-model-names` merged
(unbound run r-20260929T203136-spec_review-a3b63738). The developer said to fix small problems
without asking them. The task `review-root` found two statements outside its Modules that
contradict the developer's decided rule: every task is delegated to a task session, and the main
agent never works inside a task worktree, running only unbound Operations from the primary worktree.

1. specs/concorde/issues/module.md, "Branch-local records and repair" (module.issues), says the main
   agent resolves an Issue record conflict in the task worktree. Say instead that the task session
   resolves it there, while merging the primary branch into the task branch at the main agent's
   request, and that the main agent decides competing dispositions or escalates them to the
   developer. This matches the Issues section of the main-session guidance.
2. specs/concorde/spec-tooling/module.md, "A Spec change through Spec tooling" (module.spec-tooling),
   lists "the developer, the main agent or a specify worker" as those who change Specs on a task
   branch, and its diagram has no task session. Name the task session, and a specify worker it
   launches, as those who change Specs on a task branch. Remove the main agent, except for a small
   change the developer approved in the primary worktree. Update the diagram to match.

Keep every promise otherwise unchanged. Split no requirements unless a sentence you touch needs it.
Process: `uv sync --locked --group dev`, `npm --prefix docsite ci`, `build`; then `build --check`,
`spec-validation` and the relevant tests. The full suite is not needed for a text-only change
unless you touch code or tests. No spec_review is needed. Then task-validation and delivery, and
report with SendMessage.

## Task session (2026-09-30)

- Issues module.md, "Branch-local records and repair": the task session resolves an Issue record
  conflict in the task worktree while merging the primary branch into the task branch at the main
  agent's request; the main agent decides between competing dispositions or escalates the choice to
  the developer. Wording follows the main-session guidance's Issues section.
- Issues module.md also carried the same leftover in two nearby sentences, fixed within the goal:
  "Around it" named the main agent's hand edit of a conflicted record (now a task session's) and
  said the main agent adds reports and dispositions on the task branch (now: added by the task
  session working the task, in its worktree); "The main agent and Issues" now says every Issue
  write in a task worktree is run by that task's task session. The actor `main-agent`, the
  requirements and scenarios are unchanged (they name no worktree).
- Spec tooling module.md: those who change Specs on a task branch are the task session, a specify
  worker it launches, or the developer. Decision: kept the developer, since the brief only asked to
  remove the main agent and the guidance constrains nothing the developer does. Added that the main
  agent changes a Spec only in a small change the developer approved, in the primary worktree. The
  diagram's change box names the same three; the diagram stays about the task branch only.
- Left unchanged: Spec tooling's "the main agent can ask the Spec MCP server…" (asking is not
  working in a task worktree).
- Verified: build, build --check, spec-validation (0 findings), task-validation ready with no
  blocking findings or warnings; delivered as 37628d8e61845244fdedd5c240fef9439bb73cec.

## Closed: merged, 2026-09-29T21:30:18Z
