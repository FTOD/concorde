# Decision log: spec-debate

Goal: Pilot a discussion-style Spec review Operation (reviewer and challenger alternate on per-finding stances, bounded rounds, unresolved disputes become decision points), with its control flow in a LangGraph StateGraph inside the Operation host and idempotent worker launches keyed by run, node and round; then run it on Concorde's own Specs and report the effect

## 2026-09-27 decisions (main agent, in the task)

- **Name `spec_debate`** instead of `double_spec_review`: the Operation is a debate between two
  roles with stances, not a review run twice; it sits beside `spec_review` in Spec review.
- **Idempotent worker keys and checkpointed resume deferred.** The goal names them, but the
  Operation host has no way to re-enter a crashed run (a new `concorde run` is a new run id and
  run directory), so a keyed launch lookup or a LangGraph checkpointer would have no caller in this
  pilot. The graph state is kept plain JSON so a checkpointer can be added together with host-level
  run resumption later.
- **Each debate turn is a fresh worker**, not a resumed session: independent, bounded turns whose
  only shared memory is the host's record; costs more tokens (each turn rereads the Specs).
- **No review memory** is read or written by the debate, so the pilot can be compared with
  `spec_review` on the same Specs without the two interfering.
- **LangGraph only in the dev dependency group.** Concorde's runtime is standard-library only and an
  installed project's `.concorde/framework/python/` venv has no LangGraph; the Operation refuses
  with `langgraph_unavailable` there. Making it a real runtime dependency is a Distribution decision
  left to the developer (Distribution's Spec still says the runtime needs only the standard library).
- The shared Spec review checklist moved to `prompts/workers/spec-review/checklist.md`; the rendered
  `review-spec` prompt changed only in its role sentence.

## 2026-09-27 live runs and delivery

- spec_debate on module.spec-review (r-20260926T195859-spec_debate-3bb8a81b): 3 turns, 4m42s,
  24 items, all agreed (21 reviewer, 3 challenger additions), 1 amendment, 0 objections.
- spec_review --check-findings --force on the same Specs (r-20260926T200412-spec_review-13c8c61f):
  2 workers, 3m22s, 20 findings, all confirmed. Its review memory was removed from the worktree
  (kept in the session scratchpad) so the task does not deliver findings about pre-fix Specs.
- The debate-Spec defects both runs found (routing only in an illustrative diagram, no debater
  result shape, unclassified stop causes, two-obligation requirements, "round" clash) were fixed;
  `--rounds` became `--challenges`. Pre-existing Spec review and Workers findings were not fixed:
  outside this pilot's goal.
- spec_debate on module.workers (r-20260926T200954-spec_debate-ee14c7d2): 3 turns, 4m43s, 23
  items, all agreed, 1 amendment, 0 objections.
- Delivered; **not merged**: merging adds a LangGraph dev dependency and a pilot Operation to main,
  which the developer asked to evaluate first.

## 2026-09-27 developer direction: panel review, LangGraph as a runtime dependency

- The developer accepted LangGraph as a Concorde dependency ("后面会有更复杂的operation") and asked to
  remove the "runtime needs only the standard library" claim, and to replace the debate with several
  independent reviewers plus a merging worker, naming left to the main agent.
- **Name `spec_panel`**, roles `reviewer` and `chair`, `--reviewers` 2–5 (default 3). `spec_debate`
  was deleted outright (rapid iteration, no compatibility).
- The chair judges and merges but may not add findings (every report finding has sources), so every
  finding traces to an independent reviewer; the host labels reviewer findings (`r<seat>.<n>`) and
  checks that the report accounts for each exactly once, giving the chair one repair attempt.
- A reviewer that does not finish stops the panel before the chair (`panel_short`), so a report never
  silently rests on fewer reviews than asked for.
- Making the dependency real, not just deleting the claim: LangGraph moved to `[project]`
  dependencies; the installer installs the exported runtime lock into Concorde's own venv with uv
  (`uv_missing` / `python_dependencies_failed` refusals, `--without-dependencies` to skip), which
  makes uv an installer prerequisite; `scripts/concorde.py` re-runs on a source checkout's `.venv`.
  Distribution and Dogfooding tests pass `dependencies=False` so they need no network.

## Closed: merged, 2026-09-27T03:53:35Z
